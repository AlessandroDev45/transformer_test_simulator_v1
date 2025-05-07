# callbacks/global_updates.py
"""
Callbacks globais para atualização de componentes em múltiplas seções.
Centraliza a atualização dos painéis de informação do transformador lendo do MCP.
"""
import dash
from dash import Input, Output, callback, ctx, no_update, html
import logging
from components.transformer_info_template import create_transformer_info_panel
from app import app # Import app instance to access MCP
from utils.logger import log_detailed # Importa log detalhado
import time
import json
from datetime import datetime
from utils.mcp_diagnostics import diagnose_mcp, fix_mcp_data

log = logging.getLogger(__name__)

# Lista de todos os IDs dos painéis de informação nas diferentes seções
info_panel_outputs = [
    Output("transformer-info-losses", "children", allow_duplicate=True),
    Output("transformer-info-impulse", "children", allow_duplicate=True),
    Output("transformer-info-dieletric", "children", allow_duplicate=True),
    Output("transformer-info-applied", "children", allow_duplicate=True),
    Output("transformer-info-induced", "children", allow_duplicate=True),
    Output("transformer-info-short-circuit", "children", allow_duplicate=True),
    Output("transformer-info-temperature-rise", "children", allow_duplicate=True),
    # Adicionar outros painéis se existirem
    Output("transformer-info-comprehensive", "children", allow_duplicate=True), # Exemplo
]

# Callback para diagnosticar e corrigir o MCP quando a aplicação iniciar
@callback(
    Output("url", "search"),  # Output fictício, não usado
    Input("url", "pathname"),
    prevent_initial_call=False
)
def diagnose_and_fix_mcp(pathname):
    """
    Diagnostica e corrige o MCP quando a aplicação iniciar.
    Este callback é executado uma vez na inicialização.
    """
    log.info("[MCP Diagnostics] Iniciando diagnóstico do MCP...")

    # Executar diagnóstico
    diagnosis = diagnose_mcp(app, verbose=True)
    log.info(f"[MCP Diagnostics] Resultado do diagnóstico: {diagnosis['status']}")

    if diagnosis['status'] != 'ok':
        log.warning(f"[MCP Diagnostics] Problemas encontrados: {diagnosis['warnings']} {diagnosis['errors']}")

        # Tentar corrigir problemas
        log.info("[MCP Diagnostics] Tentando corrigir problemas...")
        fix_result = fix_mcp_data(app, verbose=True)
        log.info(f"[MCP Diagnostics] Resultado da correção: {fix_result['status']}")

        if fix_result['status'] == 'ok':
            log.info(f"[MCP Diagnostics] Ações realizadas: {fix_result['actions']}")
        else:
            log.error(f"[MCP Diagnostics] Erros na correção: {fix_result['errors']}")
    else:
        log.info("[MCP Diagnostics] MCP em bom estado. Nenhuma correção necessária.")

    # Retornar string vazia para o search da URL (não afeta a navegação)
    return ""

@callback(
    info_panel_outputs,
    Input("transformer-inputs-store", "data"), # Acionado quando o store (e portanto o MCP) muda
    prevent_initial_call='initial_duplicate' # Permite rodar na carga inicial para exibir dados padrão/carregados
)
def global_updates_all_transformer_info_panels(store_data): # Recebe dados do store como trigger
    """
    Atualiza TODOS os painéis de informação do transformador lendo do MCP.
    """
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    triggered_id = ctx.triggered_id if ctx.triggered else "Initial Load / No Trigger"
    module_name = "global_updates"
    function_name = "global_updates_all_transformer_info_panels"

    log.info(f"[{module_name}] ========== INICIANDO ATUALIZAÇÃO GLOBAL DE PAINÉIS ==========")
    log.info(f"[{module_name}] Trigger: {triggered_id}")
    log.info(f"[{module_name}] Timestamp: {timestamp}")

    # Verificar dados do store recebido como trigger
    if store_data:
        log.info(f"[{module_name}] Dados do store recebidos como trigger: {store_data}")
    else:
        log.info(f"[{module_name}] Nenhum dado recebido do store como trigger")

    if app.mcp is None:
        log.error(f"[{module_name}] MCP não disponível. Não é possível atualizar painéis.")
        error_panel = html.Div("Erro interno: MCP não inicializado.", className="alert alert-danger small")
        return [error_panel] * len(info_panel_outputs)

    # --- Obter dados do MCP ---
    transformer_data_mcp = app.mcp.get_data('transformer-inputs-store')
    log.info(f"[{module_name}] Dados obtidos do MCP para painéis")

    # Log detalhado dos dados obtidos do MCP
    if isinstance(transformer_data_mcp, dict):
        log.info(f"[{module_name}] Chaves disponíveis no MCP: {list(transformer_data_mcp.keys())}")
        # Log de valores importantes
        log.info(f"[{module_name}] Potência: {transformer_data_mcp.get('potencia_mva')}")
        log.info(f"[{module_name}] Tensão AT: {transformer_data_mcp.get('tensao_at')}")
        log.info(f"[{module_name}] Tensão BT: {transformer_data_mcp.get('tensao_bt')}")
        log.info(f"[{module_name}] Corrente AT: {transformer_data_mcp.get('corrente_nominal_at')}")
        log.info(f"[{module_name}] Corrente BT: {transformer_data_mcp.get('corrente_nominal_bt')}")
    else:
        log.warning(f"[{module_name}] Dados do MCP não são um dicionário: {transformer_data_mcp}")

    # Verificar se os dados são válidos (simples verificação se é um dict não vazio)
    if not isinstance(transformer_data_mcp, dict) or not transformer_data_mcp:
         log.warning(f"[{module_name}] Dados do MCP inválidos ou vazios. Exibindo mensagem padrão.")
         default_panel = create_transformer_info_panel({}) # Cria painel vazio/padrão
         return [default_panel] * len(info_panel_outputs)

    # NOTA: O recálculo de correntes foi removido daqui.
    # Este callback agora assume que os dados do MCP (transformer_data_mcp)
    # já contêm as correntes calculadas pelo callback de inputs.

    # Criar o painel HTML
    try:
        log.info(f"[{module_name}] Criando painel HTML com os dados do MCP: {transformer_data_mcp}")
        panel_html = create_transformer_info_panel(transformer_data_mcp)
        execution_time = time.time() - start_time
        log.info(f"[{module_name}] Painel de informações global criado em {round(execution_time * 1000, 2)}ms")

        # Retorna o mesmo painel para todas as saídas
        log.info(f"[{module_name}] ========== ATUALIZAÇÃO GLOBAL DE PAINÉIS CONCLUÍDA ==========")
        return [panel_html] * len(info_panel_outputs)
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(f"[{module_name}] Erro ao criar painel de informações global: {e}", exc_info=True)
        log.error(f"[{module_name}] Tempo de execução: {round(execution_time * 1000, 2)}ms")

        # Criar painel de erro
        error_panel = html.Div(f"Erro ao exibir informações: {str(e)}",
                              className="alert alert-danger small")
        return [error_panel] * len(info_panel_outputs)
