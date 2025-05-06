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

    log_detailed(
        log, 'debug',
        f"Iniciando atualização global de painéis",
        module=module_name, function=function_name,
        data={'trigger': triggered_id}
    )

    if app.mcp is None:
        log.error(f"[{module_name}] MCP não disponível. Não é possível atualizar painéis.")
        error_panel = html.Div("Erro interno: MCP não inicializado.", className="alert alert-danger small")
        return [error_panel] * len(info_panel_outputs)

    # --- Obter dados do MCP ---
    transformer_data_mcp = app.mcp.get_data('transformer-inputs-store')

    log_detailed(
        log, 'debug',
        f"Dados obtidos do MCP para painéis",
        module=module_name, function=function_name,
        data={'keys': list(transformer_data_mcp.keys()) if isinstance(transformer_data_mcp, dict) else None}
    )

    # Verificar se os dados são válidos (simples verificação se é um dict não vazio)
    if not isinstance(transformer_data_mcp, dict) or not transformer_data_mcp:
         log.warning(f"[{module_name}] Dados do MCP inválidos ou vazios. Exibindo mensagem padrão.")
         default_panel = create_transformer_info_panel({}) # Cria painel vazio/padrão
         return [default_panel] * len(info_panel_outputs)

    # Criar o painel HTML
    try:
        panel_html = create_transformer_info_panel(transformer_data_mcp)
        execution_time = time.time() - start_time
        log_detailed(
            log, 'debug',
            f"Painel de informações global criado",
            module=module_name, function=function_name,
            data={'execution_time_ms': round(execution_time * 1000, 2)}
        )
        # Retorna o mesmo painel para todas as saídas
        return [panel_html] * len(info_panel_outputs)
    except Exception as e:
        execution_time = time.time() - start_time
        log_detailed(
            log, 'error',
            f"Erro ao criar painel de informações global",
            module=module_name, function=function_name,
            data={'execution_time_ms': round(execution_time * 1000, 2)},
            exception=e
        )
        error_panel = html.Div(f"Erro ao carregar dados: {e}", className="alert alert-danger small")
        return [error_panel] * len(info_panel_outputs)