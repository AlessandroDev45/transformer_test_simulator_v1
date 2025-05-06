# callbacks/history.py
"""
Callbacks para a seção de Histórico de Sessões.
"""
import dash
from dash import Input, Output, State, ctx, no_update, html, ALL
import dash_bootstrap_components as dbc
import logging
from dash.exceptions import PreventUpdate
import json

# Importar a instância da aplicação
from app import app
# Importar funções do gerenciador de banco de dados
from utils.db_manager import (
    get_all_test_sessions,
    get_test_session_details,
    save_test_session,
    update_test_session,
    delete_test_session,
    session_name_exists
)
# Importar função de preparação de dados
from utils.store_diagnostics import prepare_session_data
# Importar funções de utilidade para stores
from utils.store_utils import prepare_data_for_store, update_store_data, update_app_cache
# Importar estilos padronizados
from layouts import COLORS

log = logging.getLogger(__name__)

# --- Callback para carregar a tabela de histórico ao entrar na página ---
@app.callback(
    Output("history-table-body", "children"),
    [Input("url", "pathname"),
     Input("search-button", "n_clicks")],
    [State("search-input", "value")],
    prevent_initial_call=False
)
def load_history_table(pathname, n_clicks, search_term):
    """Carrega a tabela de histórico quando o usuário entra na página ou realiza uma busca."""
    print(f"[DEBUG] Callback load_history_table acionado. Pathname: {pathname}, Trigger: {ctx.triggered_id}")

    if pathname != "/historico" and ctx.triggered_id != "search-button":
        print(f"[DEBUG] PreventUpdate em load_history_table. Pathname: {pathname}, Trigger: {ctx.triggered_id}")
        raise PreventUpdate

    log.info(f"Carregando tabela de histórico. Busca: {search_term}")
    print(f"[DEBUG] Buscando sessões no banco de dados. Termo: {search_term}")

    try:
        # Buscar sessões do banco de dados
        sessions = get_all_test_sessions(search_term)

        # Criar linhas da tabela com botões HTML reais
        rows = []
        for session in sessions:
            session_id = session['id']
            row = html.Div([
                html.Div(session['timestamp'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div(session['session_name'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div(session['notes'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div([
                    html.Button("Carregar", id={"type": "load-btn", "index": session_id},
                               className="btn btn-sm btn-primary me-2"),
                    html.Button("Excluir", id={"type": "delete-btn", "index": session_id},
                               className="btn btn-sm btn-danger")
                ], className="col-3", style={'padding': '10px', 'textAlign': 'center'})
            ], className="row", style={
                'borderBottom': f'1px solid {COLORS["border"]}',
                'padding': '5px 0'
            })
            rows.append(row)

        return rows
    except Exception as e:
        log.error(f"Erro ao carregar tabela de histórico: {e}")
        return []

# --- Callback para abrir o modal de salvar sessão ---
@app.callback(
    Output("save-session-modal", "is_open"),
    [Input("save-current-session-button", "n_clicks"),
     Input("save-session-cancel", "n_clicks"),
     Input("save-session-confirm", "n_clicks")],
    [State("save-session-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_save_modal(n_save, n_cancel, n_confirm, is_open):
    """Abre ou fecha o modal de salvar sessão."""
    if ctx.triggered_id == "save-current-session-button":
        return True
    elif ctx.triggered_id in ["save-session-cancel", "save-session-confirm"]:
        return False
    return is_open

# --- Callback para salvar a sessão atual ---
@app.callback(
    [Output("history-message", "children"),
     Output("history-table-body", "children", allow_duplicate=True),
     Output("stats-total-sessions", "children", allow_duplicate=True),
     Output("stats-last-session", "children", allow_duplicate=True)],
    [Input("save-session-confirm", "n_clicks")],
    [State("session-name-input", "value"),
     State("session-notes-input", "value"),
     State("transformer-inputs-store", "data"),
     State("losses-store", "data"),
     State("impulse-store", "data"),
     State("dieletric-analysis-store", "data"),
     State("applied-voltage-store", "data"),
     State("induced-voltage-store", "data"),
     State("short-circuit-store", "data"),
     State("temperature-rise-store", "data")],
    prevent_initial_call=True
)
def save_current_session(n_clicks, session_name, notes, *store_data):
    """Salva a sessão atual no banco de dados."""
    print(f"\n\n{'!'*10} CALLBACK save_current_session ACIONADO {'!'*10}")
    print(f"n_clicks: {n_clicks}, session_name: '{session_name}'")
    if n_clicks is None or n_clicks == 0:
        print("[DEBUG DB] save_current_session: n_clicks é None ou 0, PreventUpdate.")
        raise PreventUpdate

    if not session_name:
        return dbc.Alert("É necessário fornecer um nome para a sessão.", color="danger"), no_update, no_update, no_update

    # Verificar se o nome da sessão já existe
    if session_name_exists(session_name):
        return dbc.Alert(f"Já existe uma sessão com o nome '{session_name}'. Por favor, escolha outro nome.", color="warning"), no_update, no_update, no_update

    try:
        # Criar dicionário com os dados dos stores
        store_names = [
            "transformer-inputs-store", "losses-store", "impulse-store",
            "dieletric-analysis-store", "applied-voltage-store", "induced-voltage-store",
            "short-circuit-store", "temperature-rise-store"
        ]

        print(f"\n\n{'='*80}")
        print(f"[DEBUG DB] SALVANDO SESSÃO: '{session_name}'")
        print(f"{'='*80}")

        log.info(f"[HISTORY SAVE] Iniciando salvamento da sessão '{session_name}'")
        log.info(f"[HISTORY SAVE] Número de stores recebidos: {len(store_data)}")
        log.info(f"[HISTORY SAVE] Número de nomes de stores: {len(store_names)}")

        # Verificar se o número de stores recebidos corresponde ao número de nomes
        if len(store_data) != len(store_names):
            log.warning(f"[HISTORY SAVE] Discrepância: {len(store_data)} stores recebidos, mas {len(store_names)} nomes definidos")
            print(f"[DEBUG DB] ALERTA: Discrepância no número de stores! Recebidos: {len(store_data)}, Esperados: {len(store_names)}")
            # Mesmo com discrepância, tenta preparar com os dados recebidos
            # prepare_session_data usará zip, que para no menor número de elementos

        # --- INÍCIO DA INSPEÇÃO ULTRA-DETALHADA ---
        print(f"\n{'='*80}")
        print(f"[DEBUG DB] INSPEÇÃO DETALHADA DOS DADOS RECEBIDOS (ANTES DA PREPARAÇÃO)")
        print(f"{'='*80}")
        log.info("--- [SAVE SESSION] INSPECIONANDO DADOS BRUTOS DETALHADAMENTE ---")

        store_data_list = list(store_data)
        any_data_found = False
        for i, store_name in enumerate(store_names):
            data = store_data_list[i] if i < len(store_data_list) else None
            print(f"\n--- Store #{i+1}: {store_name} ---")
            log.info(f"  [SAVE SESSION] Inspecionando Store: {store_name}")

            if data is None:
                print(f"  Conteúdo: None")
                log.info(f"    -> Conteúdo: None")
            elif isinstance(data, dict):
                keys = list(data.keys())
                num_keys = len(keys)
                print(f"  Tipo: dict, Chaves: {num_keys}")
                if num_keys > 0:
                    any_data_found = True # Encontrou pelo menos um dict não vazio
                    print(f"  Primeiras chaves: {keys[:5]}{'...' if num_keys > 5 else ''}")
                    log.info(f"    -> Tipo: dict, Chaves: {num_keys}")
                    # Imprime os 3 primeiros itens (chave e tipo do valor)
                    print("  Amostra (3 primeiros itens):")
                    for k, v in list(data.items())[:3]:
                        v_type = type(v).__name__
                        v_repr = repr(v)[:60] # Limita representação
                        print(f"    '{k}': (Tipo: {v_type}) {v_repr}{'...' if len(repr(v)) > 60 else ''}")
                        log.debug(f"      -> Chave '{k}': Tipo={v_type}")

                    # Verificar se há valores não-None
                    has_values = False
                    for k, v in data.items():
                        if v is not None:
                            has_values = True
                            break
                    if not has_values:
                        print(f"   ⚠ AVISO: Todos os valores são None!")
                        log.warning(f"[HISTORY SAVE] Store {store_name}: Todos os valores são None!")
                else:
                    print(f"  Conteúdo: Dicionário Vazio {{}}")
                    log.info(f"    -> Conteúdo: Dicionário Vazio {{}}")
            elif isinstance(data, list):
                 num_items = len(data)
                 print(f"  Tipo: list, Itens: {num_items}")
                 if num_items > 0:
                      any_data_found = True
                      print(f"  Amostra (3 primeiros itens):")
                      for item in data[:3]:
                           item_type = type(item).__name__
                           item_repr = repr(item)[:60]
                           print(f"    - (Tipo: {item_type}) {item_repr}{'...' if len(repr(item)) > 60 else ''}")
                           log.debug(f"      -> Item Lista: Tipo={item_type}")
                 else:
                      print(f"  Conteúdo: Lista Vazia []")
                      log.info(f"    -> Conteúdo: Lista Vazia []")
            else:
                print(f"  Tipo: {type(data).__name__}")
                print(f"  Conteúdo: {repr(data)[:100]}{'...' if len(repr(data)) > 100 else ''}")
                log.warning(f"    -> Store '{store_name}' não é dict/list/None, é {type(data).__name__}")
                # Se encontrar um tipo inesperado aqui, PODE ser a causa raiz
                any_data_found = True # Considera como dado encontrado

        print(f"\n{'='*80}")
        log.info("--- [SAVE SESSION] Fim da inspeção detalhada ---")

        # Se NENHUM dado útil foi encontrado em NENHUM store, alerta e para.
        if not any_data_found:
            print("!!! AVISO: Nenhum dado útil encontrado em nenhum dos stores no momento do salvamento! Verifique se os dados estão sendo preenchidos e salvos nos stores corretos antes.")
            log.warning("[HISTORY SAVE] Nenhum dado útil encontrado nos stores para salvar.")
            return dbc.Alert("Nenhum dado para salvar. Preencha as seções primeiro.", color="warning"), no_update
        # --- FIM DA INSPEÇÃO ULTRA-DETALHADA ---

        # Verificar dados brutos recebidos (resumo)
        print(f"\n{'='*40} RESUMO DOS DADOS BRUTOS RECEBIDOS {'='*40}")
        for i, (name, data) in enumerate(zip(store_names, store_data_list)):
            data_type = type(data).__name__
            if data is None:
                print(f"{i+1}. {name}: None")
                log.info(f"[HISTORY SAVE] Store {name}: None")
            elif isinstance(data, dict):
                keys = list(data.keys())
                print(f"{i+1}. {name}: dict com {len(keys)} chaves: {keys[:10]}{'...' if len(keys) > 10 else ''}")
                log.info(f"[HISTORY SAVE] Store {name}: dict com {len(keys)} chaves")
            else:
                print(f"{i+1}. {name}: {data_type}")
                log.info(f"[HISTORY SAVE] Store {name}: {data_type}")

        # 1. Preparar os dados usando a função de diagnóstico e correção
        log.info("[HISTORY SAVE] Preparando dados da sessão usando prepare_session_data...")
        print(f"\n{'='*40} PREPARANDO DADOS DA SESSÃO {'='*40}")
        session_data = prepare_session_data(store_data_list, store_names)
        log.info("[HISTORY SAVE] Dados preparados.")

        # Verificar dados após preparação
        print(f"\n{'='*40} DADOS APÓS PREPARAÇÃO {'='*40}")
        conversion_failures = []
        for name, data in session_data.items():
            if isinstance(data, dict):
                # Verificar se há informações de erro de conversão
                if data.get("_conversion_failed"):
                    error_msg = data.get("_error", "Erro desconhecido")
                    print(f"⚠ {name}: FALHA NA CONVERSÃO - {error_msg}")
                    log.error(f"[HISTORY SAVE] Store {name}: Falha na conversão - {error_msg}")
                    conversion_failures.append(name)

                    # Mostrar caminhos problemáticos se disponíveis
                    if "_problematic_paths" in data and data["_problematic_paths"]:
                        print(f"   Caminhos problemáticos:")
                        for path in data["_problematic_paths"][:5]:  # Limitar a 5 para não sobrecarregar o log
                            print(f"   - {path}")
                else:
                    keys = list(data.keys())
                    print(f"✓ {name}: dict com {len(keys)} chaves: {keys[:10]}{'...' if len(keys) > 10 else ''}")
                    log.info(f"[HISTORY SAVE] Store {name} preparado: dict com {len(keys)} chaves")
            else:
                print(f"? {name}: {type(data).__name__}")
                log.info(f"[HISTORY SAVE] Store {name} preparado: {type(data).__name__}")

        # 2. Salvar no banco de dados
        log.info("[HISTORY SAVE] Preparando para salvar dados no banco de dados")
        print(f"\n{'='*40} SALVANDO NO BANCO DE DADOS {'='*40}")

        # Verificar se houve falhas de conversão e alertar
        if conversion_failures:
            print(f"⚠ AVISO: {len(conversion_failures)} stores tiveram falhas de conversão:")
            for name in conversion_failures:
                print(f"  - {name}")
            print("Tentando salvar mesmo assim com as informações de diagnóstico...")
            log.warning(f"[HISTORY SAVE] {len(conversion_failures)} stores tiveram falhas de conversão: {conversion_failures}")

        try:
            # Salvar diretamente no banco de dados (sem MCP)
            log.info(f"[HISTORY SAVE] Salvando sessão diretamente no banco de dados: {session_name}")
            print(f"[DEBUG] Salvando sessão diretamente no banco de dados: {session_name}")

            # Chama save_test_session com os dados já preparados/corrigidos
            session_id = save_test_session(session_data, session_name, notes or "")

            if session_id <= 0:
                log.error(f"[HISTORY SAVE] Erro ao salvar sessão: ID inválido {session_id}")
                print(f"✗ ERRO ao salvar sessão: ID inválido {session_id}")
                raise Exception(f"Erro ao salvar sessão: ID inválido {session_id}")

            log.info(f"[HISTORY SAVE] Dados salvos com sucesso no banco de dados, ID: {session_id}")
            print(f"✓ Dados salvos com sucesso, ID: {session_id}")
        except Exception as save_error:
            # Se o salvamento falhar mesmo após a preparação, loga e propaga o erro
            log.error(f"[HISTORY SAVE] Erro CRÍTICO ao salvar no banco de dados: {save_error}")
            print(f"✗ ERRO CRÍTICO ao salvar no banco de dados: {save_error}")
            import traceback
            traceback_str = traceback.format_exc()
            log.error(f"[HISTORY SAVE] Traceback do erro crítico de salvamento: {traceback_str}")
            print(f"Traceback do erro crítico de salvamento: {traceback_str}")
            # Propaga o erro para ser capturado pelo bloco except externo
            raise save_error

        # 3. Recarregar a tabela com o novo formato
        log.info("[HISTORY SAVE] Recarregando tabela de histórico após salvamento bem-sucedido")
        print(f"\n{'='*40} ATUALIZANDO TABELA DE HISTÓRICO {'='*40}")
        try:
            sessions = get_all_test_sessions()
            rows = []
            for session in sessions:
                session_id = session['id']
                row = html.Div([
                    html.Div(session['timestamp'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                    html.Div(session['session_name'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                    html.Div(session['notes'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                    html.Div([
                        html.Button("Carregar", id={"type": "load-btn", "index": session_id},
                                className="btn btn-sm btn-primary me-2"),
                        html.Button("Excluir", id={"type": "delete-btn", "index": session_id},
                                className="btn btn-sm btn-danger")
                    ], className="col-3", style={'padding': '10px', 'textAlign': 'center'})
                ], className="row", style={
                    'borderBottom': f'1px solid {COLORS["border"]}',
                    'padding': '5px 0'
                })
                rows.append(row)
            print(f"✓ Tabela de histórico atualizada com {len(rows)} sessões")
        except Exception as table_error:
            log.error(f"[HISTORY SAVE] Erro ao atualizar tabela de histórico: {table_error}")
            print(f"✗ ERRO ao atualizar tabela de histórico: {table_error}")
            # Não retorna erro aqui, apenas loga, pois os dados já foram salvos

        # Preparar mensagem de sucesso ou aviso
        if conversion_failures:
            message = f"Sessão '{session_name}' salva com avisos. Alguns dados podem estar incompletos devido a problemas de serialização."
            color = "warning"
        else:
            message = f"Sessão '{session_name}' salva com sucesso!"
            color = "success"

        log.info(f"[HISTORY SAVE] {message}")
        print(f"\n{'='*40} CONCLUSÃO {'='*40}")
        print(message)
        print(f"{'='*80}\n\n")

        # Atualizar estatísticas
        total_sessions = len(rows)
        last_session = session_name  # A sessão que acabou de ser salva é a mais recente

        return dbc.Alert(message, color=color), rows, total_sessions, last_session
    except Exception as e:
        log.error(f"[HISTORY SAVE] Erro ao salvar sessão: {e}")
        print(f"✗ ERRO GERAL ao salvar sessão: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        log.error(f"[HISTORY SAVE] Traceback: {traceback_str}")
        print(f"Traceback: {traceback_str}")
        return dbc.Alert(f"Erro ao salvar sessão: {str(e)}", color="danger"), no_update, no_update, no_update

# --- Callback para abrir o modal de confirmação de exclusão ---
@app.callback(
    [Output("delete-session-modal", "is_open"),
     Output("delete-session-id-store", "data")],
    [Input({"type": "delete-btn", "index": ALL}, "n_clicks"),
     Input("delete-session-cancel", "n_clicks"),
     Input("delete-session-confirm", "n_clicks")],
    [State("delete-session-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open):
    """Abre ou fecha o modal de confirmação de exclusão."""
    print(f"[DEBUG] toggle_delete_modal acionado. Trigger: {ctx.triggered_id}")

    # Verificar se o callback foi acionado por um clique no botão
    if not ctx.triggered:
        print("[DEBUG] PreventUpdate em toggle_delete_modal: nenhum botão foi clicado")
        raise PreventUpdate

    # Verificar se foi um clique no botão de exclusão
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "delete-btn":
        # Verificar se o botão foi realmente clicado (não é o carregamento inicial)
        # Encontrar o índice do botão clicado na lista de delete_clicks
        button_idx = None
        for i, clicks in enumerate(delete_clicks or []):
            if clicks and clicks > 0:
                button_idx = i
                break

        if button_idx is None:
            print("[DEBUG] PreventUpdate em toggle_delete_modal: nenhum botão foi clicado")
            raise PreventUpdate

        session_id = ctx.triggered_id.get("index")
        print(f"[DEBUG] Botão de exclusão clicado para sessão ID: {session_id}")
        if session_id:
            return True, {"session_id": session_id, "session_name": ""}

    # Se foi o botão de cancelar ou confirmar, fechar o modal
    elif ctx.triggered_id in ["delete-session-cancel", "delete-session-confirm"]:
        print(f"[DEBUG] Botão {ctx.triggered_id} clicado")
        return False, no_update

    # Caso contrário, manter o estado atual
    return is_open, no_update

# --- Callback para excluir uma sessão ---
@app.callback(
    [Output("history-message", "children", allow_duplicate=True),
     Output("history-table-body", "children", allow_duplicate=True),
     Output("stats-total-sessions", "children", allow_duplicate=True),
     Output("stats-last-session", "children", allow_duplicate=True)],
    [Input("delete-session-confirm", "n_clicks")],
    [State("delete-session-id-store", "data")],
    prevent_initial_call=True
)
def delete_session(n_clicks, session_data):
    """Exclui uma sessão do banco de dados."""
    if n_clicks is None or n_clicks == 0 or not session_data:
        raise PreventUpdate

    session_id = session_data.get("session_id")
    session_name = session_data.get("session_name", "")

    if not session_id:
        return dbc.Alert("ID de sessão inválido.", color="danger"), no_update

    try:
        # Excluir a sessão
        success = delete_test_session(session_id)

        if not success:
            return dbc.Alert(f"Erro ao excluir sessão: Sessão não encontrada.", color="danger"), no_update

        # Recarregar a tabela com o novo formato
        sessions = get_all_test_sessions()
        rows = []
        for session in sessions:
            session_id = session['id']
            row = html.Div([
                html.Div(session['timestamp'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div(session['session_name'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div(session['notes'], className="col-3", style={'padding': '10px', 'textAlign': 'center'}),
                html.Div([
                    html.Button("Carregar", id={"type": "load-btn", "index": session_id},
                               className="btn btn-sm btn-primary me-2"),
                    html.Button("Excluir", id={"type": "delete-btn", "index": session_id},
                               className="btn btn-sm btn-danger")
                ], className="col-3", style={'padding': '10px', 'textAlign': 'center'})
            ], className="row", style={
                'borderBottom': f'1px solid {COLORS["border"]}',
                'padding': '5px 0'
            })
            rows.append(row)

        # Atualizar estatísticas
        total_sessions = len(rows)

        # Buscar a sessão mais recente para atualizar a estatística
        last_session = "Nenhuma"
        if rows:
            try:
                # Buscar todas as sessões novamente
                all_sessions = get_all_test_sessions()
                if all_sessions:
                    # Ordenar por timestamp (mais recente primeiro)
                    sorted_sessions = sorted(all_sessions, key=lambda x: x['timestamp'], reverse=True)
                    last_session = sorted_sessions[0]['session_name'] if sorted_sessions else "Nenhuma"
            except Exception as e:
                log.error(f"Erro ao buscar última sessão após exclusão: {e}")

        return dbc.Alert(f"Sessão '{session_name}' excluída com sucesso!", color="success"), rows, total_sessions, last_session
    except Exception as e:
        log.error(f"Erro ao excluir sessão: {e}")
        return dbc.Alert(f"Erro ao excluir sessão: {str(e)}", color="danger"), no_update, no_update, no_update

# --- Callback para carregar uma sessão ---
@app.callback(
    [Output("history-temp-store", "data"),
     Output("history-message", "children", allow_duplicate=True),
     Output("stats-current-session", "children", allow_duplicate=True)],
    [Input({"type": "load-btn", "index": ALL}, "n_clicks")],
    [State("transformer-inputs-store", "data")],
    prevent_initial_call=True
)
def load_session(load_clicks, transformer_inputs=None):
    """Carrega uma sessão do banco de dados e armazena os dados no store temporário."""
    print(f"[DEBUG] load_session acionado. Trigger: {ctx.triggered_id}, Clicks: {load_clicks}")

    # Verificar se o callback foi acionado por um clique no botão
    if not ctx.triggered:
        print("[DEBUG] PreventUpdate em load_session: nenhum botão foi clicado")
        raise PreventUpdate

    # Encontrar qual botão foi clicado
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict) or triggered_id.get("type") != "load-btn":
        print("[DEBUG] PreventUpdate em load_session: trigger_id não é do tipo load-btn")
        raise PreventUpdate

    # Verificar se o botão foi realmente clicado (não é o carregamento inicial)
    # Encontrar o índice do botão clicado na lista de load_clicks
    button_idx = None
    for i, clicks in enumerate(load_clicks or []):
        if clicks and clicks > 0:
            button_idx = i
            break

    if button_idx is None:
        print("[DEBUG] PreventUpdate em load_session: nenhum botão foi clicado")
        raise PreventUpdate

    # Obter o ID da sessão a partir do ID do botão
    session_id = triggered_id.get("index")
    print(f"[DEBUG] Botão de carregamento clicado para sessão ID: {session_id}")

    if not session_id:
        print("[DEBUG] PreventUpdate em load_session: session_id é None")
        raise PreventUpdate

    # Buscar o nome da sessão para exibir na mensagem
    sessions = get_all_test_sessions()
    session_name = next((s['session_name'] for s in sessions if s['id'] == session_id), "")

    try:
        # Carregar os detalhes da sessão diretamente do banco de dados
        log.info(f"Carregando sessão diretamente do banco de dados, ID: {session_id}")
        print(f"[DEBUG] Carregando sessão diretamente do banco de dados, ID: {session_id}")

        # Carregar os detalhes da sessão
        session_details = get_test_session_details(session_id)

        if not session_details:
            return no_update, dbc.Alert("Sessão não encontrada.", color="danger"), no_update

        # Extrair os dados dos stores
        store_data = session_details.get("store_data", {})

        # Armazenar os dados no store temporário e exibir mensagem de sucesso
        # Não atualizamos o cache aqui, isso será feito em process_loaded_data
        return {
            "session_id": session_id,
            "session_name": session_name,
            "store_data": store_data
        }, dbc.Alert(f"Sessão '{session_name}' carregada com sucesso!", color="success"), no_update
    except Exception as e:
        log.error(f"Erro ao carregar sessão: {e}")
        print(f"[DEBUG] Erro ao carregar sessão: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return no_update, dbc.Alert(f"Erro ao carregar sessão: {str(e)}", color="danger"), no_update

# --- Callback para processar os dados carregados ---
@app.callback(
    [
        # Outputs para os dados dos stores
        Output("transformer-inputs-store", "data", allow_duplicate=True),
        Output("losses-store", "data", allow_duplicate=True),
        Output("impulse-store", "data", allow_duplicate=True),
        Output("dieletric-analysis-store", "data", allow_duplicate=True),
        Output("applied-voltage-store", "data", allow_duplicate=True),
        Output("induced-voltage-store", "data", allow_duplicate=True),
        Output("short-circuit-store", "data", allow_duplicate=True),
        Output("temperature-rise-store", "data", allow_duplicate=True),
    ],
    [Input("history-temp-store", "data")],
    prevent_initial_call=True
)
def process_loaded_data(temp_store_data):
    """
    Processa os dados carregados e atualiza os stores.
    Esta função foi refatorada para separar a atualização dos stores da navegação,
    evitando problemas de timing durante as transições de página.
    """
    import time
    from utils.logger import log_detailed, check_store_exists
    from dash import ctx

    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    triggered_id = ctx.triggered_id if ctx.triggered else "N/A"

    log.info(f"PROCESS_LOADED_DATA Start - Trigger: {triggered_id}")
    print(f"[DEBUG] PROCESS_LOADED_DATA Start - Trigger: {triggered_id}")

    log_detailed(
        log,
        'info',
        f"Iniciando processamento de dados carregados",
        module="history",
        function="process_loaded_data",
        data={
            'timestamp': timestamp,
            'trigger': triggered_id,
            'temp_store_data_type': type(temp_store_data).__name__,
            'temp_store_data_keys': list(temp_store_data.keys()) if isinstance(temp_store_data, dict) else None
        }
    )

    if not temp_store_data:
        log_detailed(
            log,
            'warning',
            "Nenhum dado para processar, abortando",
            module="history",
            function="process_loaded_data"
        )
        raise PreventUpdate

    session_id = temp_store_data.get("session_id")
    session_name = temp_store_data.get("session_name")
    store_data = temp_store_data.get("store_data", {})

    log_detailed(
        log,
        'info',
        f"Dados da sessão identificados",
        module="history",
        function="process_loaded_data",
        data={
            'session_id': session_id,
            'session_name': session_name,
            'store_count': len(store_data)
        }
    )

    # Processar dados diretamente do store_data (sem MCP)
    log_detailed(
        log,
        'info',
        f"Processando dados carregados da sessão diretamente",
        module="history",
        function="process_loaded_data",
        data={'session_name': session_name}
    )

    # Atualizar o cache da aplicação para acesso rápido fora dos callbacks
    try:
        # Atualizar o cache com os dados carregados
        for store_name, data in store_data.items():
            if data and store_name == "transformer-inputs-store":  # Verificar se os dados não estão vazios
                # Preparar os dados para garantir serialização
                prepared_data = prepare_data_for_store(data, store_name)

                # Atualizar o cache da aplicação
                if update_app_cache(prepared_data):
                    log_detailed(
                        log,
                        'debug',
                        f"Cache de dados atualizado com {store_name}",
                        module="history",
                        function="process_loaded_data",
                        data={
                            'store_name': store_name,
                            'data_keys': list(prepared_data.keys()) if isinstance(prepared_data, dict) else None
                        }
                    )
    except Exception as e:
        log_detailed(
            log,
            'error',
            f"Erro ao atualizar cache de dados",
            module="history",
            function="process_loaded_data",
            data={'error_type': type(e).__name__},
            exception=e
        )

    # Preparar os dados para retorno diretamente do store_data
    transformer_inputs = store_data.get("transformer-inputs-store", {})
    losses_store = store_data.get("losses-store", {})
    impulse_store = store_data.get("impulse-store", {})
    dieletric_analysis_store = store_data.get("dieletric-analysis-store", {})
    applied_voltage_store = store_data.get("applied-voltage-store", {})
    induced_voltage_store = store_data.get("induced-voltage-store", {})
    short_circuit_store = store_data.get("short-circuit-store", {})
    temperature_rise_store = store_data.get("temperature-rise-store", {})

    # Verificar se todos os stores foram carregados corretamente
    stores_status = {
        "transformer-inputs-store": check_store_exists(transformer_inputs, "transformer-inputs-store"),
        "losses-store": check_store_exists(losses_store, "losses-store"),
        "impulse-store": check_store_exists(impulse_store, "impulse-store"),
        "dieletric-analysis-store": check_store_exists(dieletric_analysis_store, "dieletric-analysis-store"),
        "applied-voltage-store": check_store_exists(applied_voltage_store, "applied-voltage-store"),
        "induced-voltage-store": check_store_exists(induced_voltage_store, "induced-voltage-store"),
        "short-circuit-store": check_store_exists(short_circuit_store, "short-circuit-store"),
        "temperature-rise-store": check_store_exists(temperature_rise_store, "temperature-rise-store")
    }

    log_detailed(
        log,
        'info',
        "Verificação de status dos stores após carregamento",
        module="history",
        function="process_loaded_data",
        data={'stores_status': stores_status}
    )

    # Calcular o tempo de execução
    execution_time = time.time() - start_time

    log_detailed(
        log,
        'info',
        "Dados processados com sucesso",
        module="history",
        function="process_loaded_data",
        data={
            'execution_time_ms': round(execution_time * 1000, 2),
            'transformer_inputs_keys': len(transformer_inputs) if isinstance(transformer_inputs, dict) else 0,
            'losses_store_keys': len(losses_store) if isinstance(losses_store, dict) else 0,
            'impulse_store_keys': len(impulse_store) if isinstance(impulse_store, dict) else 0,
            'dieletric_analysis_store_keys': len(dieletric_analysis_store) if isinstance(dieletric_analysis_store, dict) else 0,
            'applied_voltage_store_keys': len(applied_voltage_store) if isinstance(applied_voltage_store, dict) else 0,
            'induced_voltage_store_keys': len(induced_voltage_store) if isinstance(induced_voltage_store, dict) else 0,
            'short_circuit_store_keys': len(short_circuit_store) if isinstance(short_circuit_store, dict) else 0,
            'temperature_rise_store_keys': len(temperature_rise_store) if isinstance(temperature_rise_store, dict) else 0
        }
    )

    # Retornar apenas os dados dos stores, sem navegação
    # A navegação será tratada por um callback separado
    log.info(f"PROCESS_LOADED_DATA End - Returning data for stores")
    print(f"[DEBUG] PROCESS_LOADED_DATA End - Returning data for stores")

    return (
        transformer_inputs,
        losses_store,
        impulse_store,
        dieletric_analysis_store,
        applied_voltage_store,
        induced_voltage_store,
        short_circuit_store,
        temperature_rise_store
    )

# --- Callback para atualizar as estatísticas da página de histórico ---
@app.callback(
    [Output("stats-total-sessions", "children"),
     Output("stats-last-session", "children"),
     Output("stats-current-session", "children")],
    [Input("url", "pathname")],
    prevent_initial_call=False
)
def update_history_stats(pathname):
    """Atualiza as estatísticas exibidas na página de histórico."""
    if pathname != "/historico":
        raise PreventUpdate

    try:
        # Buscar todas as sessões
        sessions = get_all_test_sessions()

        # Total de sessões
        total_sessions = len(sessions)

        # Última sessão (data/hora mais recente)
        last_session = "Nenhuma"
        if sessions:
            # Ordenar por timestamp (mais recente primeiro)
            sorted_sessions = sorted(sessions, key=lambda x: x['timestamp'], reverse=True)
            last_session = sorted_sessions[0]['session_name'] if sorted_sessions else "Nenhuma"

        # Sessão atual (nome da sessão atual ou "Nova Sessão")
        current_session = "Nova Sessão"

        return total_sessions, last_session, current_session
    except Exception as e:
        log.error(f"Erro ao atualizar estatísticas de histórico: {e}")
        return "--", "--", "Nova Sessão"

# --- Callback separado para navegação após o processamento dos dados ---
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("history-temp-store", "data"),
    prevent_initial_call=True
)
def navigate_after_load(data):
    """Navega para a página de dados básicos após o carregamento dos dados."""
    return "/dados" if data else dash.no_update

# --- Registrar os callbacks com a aplicação ---
def register_history_callbacks(app):
    """
    Registra os callbacks de histórico com a aplicação.

    Nota: Todos os callbacks foram refatorados para usar decoradores @app.callback,
    então esta função não precisa mais registrar os callbacks explicitamente.
    """
    log.info("Callbacks do módulo history já registrados via decoradores @app.callback.")
