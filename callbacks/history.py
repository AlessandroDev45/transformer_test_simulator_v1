# callbacks/history.py
import logging
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate

from app import app # Importar instância do app
from utils.db_manager import get_all_test_sessions # get_all_test_sessions ainda é útil para a lista
from layouts import COLORS # Para estilos de botões na tabela, se necessário
# Importar STORE_IDS do módulo app_core.transformer_mcp
from app_core.transformer_mcp import STORE_IDS

log = logging.getLogger(__name__)

def register_history_callbacks(app_instance):
    log.info("Registrando callbacks de Histórico (VERSÃO REFEITA - Foco no MCP)")

    # --- Callback para popular a tabela de histórico (sem grandes mudanças aqui) ---
    @app_instance.callback(
        Output("history-table-body-content", "children"),
        Output("history-stats-total-sessions", "children"),
        [Input("url", "pathname"),
         Input("history-search-button", "n_clicks"),
         Input("history-action-message", "children")],
        [State("history-search-input", "value")]
    )
    def history_populate_table(pathname, search_clicks, action_feedback, search_term):
        # ... (lógica existente para popular a tabela, sem alterações diretas na funcionalidade)
        # Certifique-se que os IDs dos botões Carregar/Excluir sejam distintos
        if (pathname and not pathname.endswith("/historico")) and not ctx.triggered_id == "history-action-message":
            raise PreventUpdate
        log.info(f"Populando tabela de histórico. Trigger: {ctx.triggered_id}, Termo Busca: {search_term}")
        try:
            sessions = get_all_test_sessions(search_term)
            rows = []
            if not sessions:
                rows.append(html.Div("Nenhuma sessão encontrada.", className="text-muted p-3 text-center"))
            else:
                for session in sessions:
                    session_id = session["id"]
                    row = dbc.Row(
                        [
                            dbc.Col(session["timestamp"], width=3, style={"padding": "8px 12px", "textAlign": "center", "fontSize": "0.75rem", "color": COLORS["text_light"]}),
                            dbc.Col(session["session_name"], width=4, style={"padding": "8px 12px", "textAlign": "left", "fontSize": "0.75rem", "color": COLORS["text_light"]}),
                            dbc.Col(session["notes"], width=3, style={"padding": "8px 12px", "textAlign": "left", "fontSize": "0.75rem", "color": COLORS["text_light"], "whiteSpace": "pre-wrap", "wordBreak": "break-word"}),
                            dbc.Col(
                                [
                                    dbc.Button("Carregar", id={"type": "history-load-session-button", "index": session_id}, color="primary", size="sm", className="me-1", style={"fontSize": "0.7rem"}),
                                    dbc.Button("Excluir", id={"type": "history-delete-session-button", "index": session_id}, color="danger", size="sm", style={"fontSize": "0.7rem"}),
                                ],
                                width=2, className="text-center"
                            ),
                        ], className="g-0", style={"borderBottom": f'1px solid {COLORS["border"]}'}
                    )
                    rows.append(row)
            return rows, str(len(sessions))
        except Exception as e:
            log.error(f"Erro ao popular tabela de histórico: {e}", exc_info=True)
            return html.Div(f"Erro ao carregar sessões: {str(e)}", className="text-danger p-3"), "Erro"


    # --- Callbacks para o Modal de Salvar Sessão (sem grandes mudanças na UI, mas na ação) ---
    @app_instance.callback(
        Output("history-save-session-modal", "is_open"),
        Output("history-session-name-input", "value", allow_duplicate=True),
        Output("history-session-notes-input", "value", allow_duplicate=True),
        Output("history-save-modal-error", "children", allow_duplicate=True),
        [Input("history-open-save-modal-button", "n_clicks"),
         Input("history-save-modal-confirm-button", "n_clicks"), # Trigger para salvar
         Input("history-save-modal-cancel-button", "n_clicks")],
        [State("history-save-session-modal", "is_open")],
        prevent_initial_call=True
    )
    def history_toggle_save_modal(open_clicks, confirm_clicks, cancel_clicks, is_open_current):
        triggered_id = ctx.triggered_id.split(".")[0] if ctx.triggered_id else None
        log.debug(f"history_toggle_save_modal: trigger={triggered_id}")

        if triggered_id == "history-open-save-modal-button":
            return True, "", "", None # Limpa campos e abre
        # Se o salvamento foi confirmado, o callback `history_handle_save_session` fechará o modal.
        # Se o cancelamento foi clicado, fecha o modal.
        if triggered_id == "history-save-modal-cancel-button":
             return False, no_update, no_update, None
        # Se foi o botão de confirmar, a lógica de fechamento estará no callback de salvar.
        # Se o modal já está aberto e o botão de abrir é clicado de novo, não faz nada.
        if triggered_id == "history-save-modal-confirm-button" and not is_open_current:
             # Evita reabrir se o salvamento fechar
             raise PreventUpdate
        return is_open_current, no_update, no_update, no_update


    @app_instance.callback(
        Output("history-action-message", "children", allow_duplicate=True),
        Output("history-save-modal-error", "children", allow_duplicate=True),
        Output("history-save-session-modal", "is_open", allow_duplicate=True),
        [Input("history-save-modal-confirm-button", "n_clicks")],
        [
            # States: Session name and notes from the modal
            State("history-session-name-input", "value"),
            State("history-session-notes-input", "value"),
            # ADD States for ALL STORES HERE
            # This is the crucial change. Get the data from all relevant stores.
            # Use the list of store IDs from app_core.transformer_mcp
            *[State(store_id, "data") for store_id in STORE_IDS] # * expands the list into separate arguments
        ],
        prevent_initial_call=True
    )
    def history_handle_save_session(confirm_clicks, session_name, session_notes, *store_data_from_states): # * captures all State values after notes
        # This callback should ONLY fire when the confirm button is clicked
        if not confirm_clicks or confirm_clicks <= 0:
            raise PreventUpdate

        log.info(f"[HISTORY UI SAVE] Tentando salvar sessão: Nome='{session_name}'")

        # Default outputs - assume failure and keep modal open unless success
        modal_error_msg = None # Default to no error message
        action_msg = no_update # Default to no external action message
        modal_is_open = True # Default to keep modal open

        # Basic validation: Name is required
        if not session_name or not session_name.strip():
            log.warning("[HISTORY UI SAVE] Nome da sessão está vazio.")
            modal_error_msg = dbc.Alert("O nome da sessão é obrigatório.", color="danger", duration=5000)
            # Return defaults - keeps modal open, shows error, no external message change
            return action_msg, modal_error_msg, modal_is_open

        # Check if MCP is available
        if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
            log.error("[HISTORY UI SAVE] MCP não disponível.")
            action_msg = dbc.Alert("Erro interno: Sistema de dados não disponível.", color="danger")
            # This is a fatal error for this operation, close modal
            modal_is_open = False
            return action_msg, modal_error_msg, modal_is_open

        try:
            # Collect data from States into a dictionary
            # The *store_data_from_states variable is a tuple of values corresponding
            # to the order of State inputs defined after session_notes.
            # Zip STORE_IDS with this tuple to create the dictionary {store_id: data}
            all_stores_latest_data = {store_id: data for store_id, data in zip(STORE_IDS, store_data_from_states)}

            log.debug(f"[HISTORY UI SAVE] Collected data from {len(all_stores_latest_data)} stores from States.")
            log.debug(f"[HISTORY UI SAVE] Stores collected (IDs): {list(all_stores_latest_data.keys())}")
            # Optional: Add some info about the data structure of collected stores for debug
            for sid, data in all_stores_latest_data.items():
                 log.debug(f"[HISTORY UI SAVE]   Collected data for '{sid}': Type={type(data).__name__}, Keys={list(data.keys()) if isinstance(data, dict) else None}")

            # Call MCP save_session, passing the collected data
            # Pass the collected dictionary as the 'stores_data' argument
            session_id = app_instance.mcp.save_session(
                session_name,
                session_notes or "",
                stores_data=all_stores_latest_data # Pass the collected data here
            )

            # Handle return codes from save_session
            if session_id == -2: # Name already exists (handled by MCP)
                log.warning(f"[HISTORY UI SAVE] Save failed: Session name '{session_name}' already exists.")
                modal_error_msg = dbc.Alert(app_instance.mcp.last_save_error or "Nome da sessão já existe.", color="warning", duration=5000)
                # Keep modal open to show the error
                modal_is_open = True
            elif session_id == -3: # Serialization error (handled by MCP)
                 log.error(f"[HISTORY UI SAVE] Save failed: Serialization error.")
                 modal_error_msg = dbc.Alert(app_instance.mcp.last_save_error or "Erro ao preparar dados para salvar (serialização).", color="danger", duration=5000)
                 # Keep modal open
                 modal_is_open = True
            elif session_id <= 0: # Other DB error (handled by MCP)
                log.error(f"[HISTORY UI SAVE] Save failed: Database error (code {session_id}).")
                error_details = app_instance.mcp.last_save_error or f"Código de erro DB: {session_id}"
                modal_error_msg = dbc.Alert(f"Erro ao salvar sessão: {error_details}", color="danger", duration=5000)
                 # Keep modal open
                modal_is_open = True
            else: # Success (session_id > 0)
                log.info(f"[HISTORY UI SAVE] Session '{session_name}' saved successfully (ID: {session_id})!")
                action_msg = dbc.Alert(f"Sessão '{session_name}' salva com sucesso (ID: {session_id})!", color="success", duration=4000)
                modal_is_open = False # Close the modal on success

            # Return the outputs
            return action_msg, modal_error_msg, modal_is_open

        except Exception as e:
            log.error(f"[HISTORY UI SAVE] EXCEPCIONAL ERROR during save process: {e}", exc_info=True)
            # This catches errors outside the specific return codes from save_session
            action_msg = dbc.Alert(f"Erro inesperado ao salvar: {str(e)}", color="danger")
            modal_error_msg = dbc.Alert(f"Erro inesperado: {str(e)}", color="danger", duration=5000)
            modal_is_open = True # Keep modal open to show the error

            return action_msg, modal_error_msg, modal_is_open


    # --- Callbacks para Excluir Sessão (sem grandes mudanças aqui, já delega) ---
    @app_instance.callback(
        Output("history-delete-session-modal", "is_open"),
        Output("history-selected-session-id", "data"),
        [Input({"type": "history-delete-session-button", "index": ALL}, "n_clicks"),
         Input("history-delete-modal-confirm-button", "n_clicks"),
         Input("history-delete-modal-cancel-button", "n_clicks")],
        [State("history-delete-session-modal", "is_open")],
        prevent_initial_call=True
    )
    def history_toggle_delete_modal(delete_btn_clicks, confirm_click, cancel_click, is_open_current):
        # ... (lógica existente, mas usando app_instance.mcp.delete_session) ...
        triggered_id_info = ctx.triggered_id
        log.debug(f"history_toggle_delete_modal: trigger={triggered_id_info}")

        if isinstance(triggered_id_info, dict) and triggered_id_info.get("type") == "history-delete-session-button":
            session_id_to_delete = triggered_id_info.get("index")
            # É importante verificar se o botão que disparou realmente foi clicado
            # (n_clicks não é None e > 0 para o botão específico)
            # Esta lógica pode ser complexa com pattern-matching. Para simplificar,
            # vamos assumir que o Dash só dispara se houve um clique real
            if session_id_to_delete is not None:
                log.info(f"Botão excluir clicado para sessão ID: {session_id_to_delete}")
                return True, session_id_to_delete # Abre modal e guarda ID
            else:
                 log.warning("ID da sessão para exclusão não encontrado no botão.")
                 raise PreventUpdate

        if triggered_id_info == "history-delete-modal-confirm-button" or triggered_id_info == "history-delete-modal-cancel-button":
            return False, no_update # Fecha modal, não mexe no ID guardado ainda

        return is_open_current, no_update


    @app_instance.callback(
        Output("history-action-message", "children", allow_duplicate=True),
        [Input("history-delete-modal-confirm-button", "n_clicks")],
        [State("history-selected-session-id", "data")],
        prevent_initial_call=True
    )
    def history_handle_delete_session(confirm_clicks, session_id_to_delete):
        if not confirm_clicks or not session_id_to_delete:
            raise PreventUpdate

        log.info(f"[HISTORY UI DELETE] Tentando excluir sessão ID: {session_id_to_delete}")
        if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
            log.error("[HISTORY UI DELETE] MCP não disponível.")
            return dbc.Alert("Erro interno: Sistema de dados não disponível.", color="danger")

        try:
            success = app_instance.mcp.delete_session(session_id_to_delete) # Usa MCP
            if success:
                msg = dbc.Alert(f"Sessão ID {session_id_to_delete} excluída com sucesso!", color="success", duration=4000)
                log.info(f"[HISTORY UI DELETE] Sessão ID {session_id_to_delete} excluída.")
            else:
                msg = dbc.Alert(f"Erro: Não foi possível excluir a sessão ID {session_id_to_delete}.", color="danger", duration=4000)
                log.warning(f"[HISTORY UI DELETE] Falha ao excluir sessão ID {session_id_to_delete} via MCP.")
            return msg
        except Exception as e:
            log.error(f"[HISTORY UI DELETE] Erro ao excluir sessão ID {session_id_to_delete}: {e}", exc_info=True)
            return dbc.Alert(f"Erro ao excluir sessão: {str(e)}", color="danger", duration=5000)

    # --- Callbacks para Carregar Sessão (Fluxo em Duas Etapas) ---
    @app_instance.callback(
        Output("history-page-temp-data", "data"), # Guarda dados carregados temporariamente
        Output("history-action-message", "children", allow_duplicate=True),
        [Input({"type": "history-load-session-button", "index": ALL}, "n_clicks")],
        prevent_initial_call=True
    )
    def history_trigger_load_session(load_clicks):
        # ... (lógica para obter session_id_to_load do botão clicado, como na versão anterior) ...
        triggered_id_info = ctx.triggered_id
        log.debug(f"history_trigger_load_session: trigger={triggered_id_info}")

        if not isinstance(triggered_id_info, dict) or triggered_id_info.get("type") != "history-load-session-button":
            raise PreventUpdate

        session_id_to_load = triggered_id_info.get("index")
        if session_id_to_load is None:
            raise PreventUpdate

        # Verifica se este botão específico foi clicado (n_clicks > 0)
        all_inputs = ctx.inputs_list[0]
        actual_click_count = 0
        for input_dict in all_inputs:
            if input_dict['id'] == triggered_id_info:
                actual_click_count = input_dict['value']
                break

        if not actual_click_count or actual_click_count == 0:
            log.debug(f"Botão carregar para sessão {session_id_to_load} não teve um clique válido (n_clicks={actual_click_count}).")
            raise PreventUpdate

        log.info(f"[HISTORY UI LOAD] Iniciando carregamento da sessão ID: {session_id_to_load}")
        if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
            log.error("[HISTORY UI LOAD] MCP não disponível.")
            return no_update, dbc.Alert("Erro interno: Sistema de dados não disponível.", color="danger")
        try:
            # `db_get_session_details` retorna o dict com `mcp_stores_raw_json`
            # Usar a função db_get_session_details diretamente, não através do MCP
            from utils.db_manager import get_test_session_details
            session_data_raw_from_db = get_test_session_details(session_id_to_load)

            if not session_data_raw_from_db:
                msg = dbc.Alert(f"Erro: Não foi possível encontrar detalhes da sessão ID {session_id_to_load}.", color="danger", duration=5000)
                log.error(f"Detalhes não encontrados para sessão ID {session_id_to_load}.")
                return no_update, msg

            # Passa os dados brutos para o store temporário. O MCP.load_session fará a desserialização.
            # Guardamos o objeto completo retornado por db_get_session_details.
            log.info(f"Sessão ID {session_id_to_load} lida do DB. Passando para history-page-temp-data.")
            return session_data_raw_from_db, dbc.Alert(f"Sessão '{session_data_raw_from_db.get('session_name', session_id_to_load)}' pronta para ser aplicada.", color="info", duration=3000)

        except Exception as e:
            log.error(f"[HISTORY UI LOAD] Erro ao ler sessão ID {session_id_to_load} do DB: {e}", exc_info=True)
            return no_update, dbc.Alert(f"Erro ao carregar sessão do banco: {str(e)}", color="danger", duration=5000)

    # STORE_IDS já importado no início do arquivo

    @app_instance.callback(
        [Output(store_id, "data", allow_duplicate=True) for store_id in STORE_IDS] +
        [Output("url", "pathname", allow_duplicate=True),
         Output("history-action-message", "children", allow_duplicate=True)],
        [Input("history-page-temp-data", "data")],
        prevent_initial_call=True
    )
    def history_apply_loaded_session_data(raw_session_data_from_temp_store):
        if not raw_session_data_from_temp_store or not isinstance(raw_session_data_from_temp_store, dict):
            raise PreventUpdate

        session_id = raw_session_data_from_temp_store.get("id")
        session_name = raw_session_data_from_temp_store.get("session_name", f"ID {session_id}")

        log.info(f"[HISTORY UI APPLY] Aplicando dados da sessão '{session_name}' (ID: {session_id}) aos stores via MCP.")

        if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
            log.error("[HISTORY UI APPLY] MCP não disponível.")
            # Número de stores + 2 (url, message)
            return [no_update] * (len(STORE_IDS) + 2)


        # O MCP.load_session agora lida com a desserialização e atualização interna.
        success = app_instance.mcp.load_session(session_id) # Passa apenas o ID

        if success:
            # Após o MCP carregar, precisamos popular os Outputs dos dcc.Store
            output_store_values = [app_instance.mcp.get_data(store_id_mcp) for store_id_mcp in STORE_IDS]

            # Salvar o estado do MCP no disco após carregar uma sessão com sucesso
            app_instance.mcp.save_to_disk(force=True)
            log.info(f"Estado do MCP salvo no disco após carregar e aplicar a sessão '{session_name}'.")

            feedback = dbc.Alert(f"Sessão '{session_name}' carregada e aplicada com sucesso!", color="success", duration=4000)
            log.info(f"Sessão '{session_name}' aplicada. Redirecionando para /dados.")
            return output_store_values + ["/dados", feedback]
        else:
            error_msg_mcp = app_instance.mcp.last_save_error or "Falha ao carregar dados da sessão no MCP."
            log.error(f"[HISTORY UI APPLY] Falha ao carregar sessão via MCP: {error_msg_mcp}")
            error_msg_alert = dbc.Alert(f"Erro ao aplicar dados da sessão: {error_msg_mcp}", color="danger")
            return [no_update] * (len(STORE_IDS) + 1) + [error_msg_alert] # Não muda URL em caso de erro

    log.info("Callbacks de Histórico (VERSÃO REFEITA - Foco no MCP) registrados.")
