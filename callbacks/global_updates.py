
# callbacks/global_updates.py
"""
Callbacks globais para atualização de componentes em múltiplas seções.
Centraliza a atualização dos painéis de informação do transformador.
"""
import dash
from dash import Input, Output, callback, ctx, no_update, html
import logging
from components.transformer_info_template import create_transformer_info_panel
from app import app # Import app instance to access cache

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
]

@callback(
    info_panel_outputs,
    Input("transformer-inputs-store", "data"),
    prevent_initial_call=True # Prevent running on initial load before data exists
)
def global_updates_all_transformer_info_panels(transformer_data):
    """
    Atualiza TODOS os painéis de informação do transformador nas diferentes
    seções sempre que os dados básicos são salvos/atualizados.
    """
    import time
    import json
    from utils.logger import log_detailed
    from utils.callback_helpers import standard_transformer_info_callback

    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    triggered_id = ctx.triggered_id if ctx.triggered else "N/A"

    log_detailed(
        log,
        'info',
        f"[Global Info Panel Update] Iniciando atualização de painéis",
        module="global_updates",
        function="update_all_transformer_info_panels",
        data={
            'timestamp': timestamp,
            'trigger': triggered_id,
            'data_type': type(transformer_data).__name__,
            'data_keys': list(transformer_data.keys()) if isinstance(transformer_data, dict) else None,
            'data_size': len(json.dumps(transformer_data)) if transformer_data else 0
        }
    )

    # Verificar se o MCP está disponível
    mcp_available = hasattr(app, 'mcp') and app.mcp is not None
    if mcp_available:
        log_detailed(
            log,
            'info',
            f"[Global Info Panel Update] MCP disponível, verificando dados",
            module="global_updates",
            function="update_all_transformer_info_panels"
        )

        # Verificar se os dados no MCP são consistentes com os dados recebidos
        mcp_data = app.mcp.get_data('transformer-inputs-store')
        data_match = transformer_data == mcp_data

        log_detailed(
            log,
            'info',
            f"[Global Info Panel Update] Verificação de consistência MCP: {data_match}",
            module="global_updates",
            function="update_all_transformer_info_panels",
            data={
                'mcp_keys': list(mcp_data.keys()) if isinstance(mcp_data, dict) else None,
                'data_match': data_match
            }
        )

        # Se os dados não forem consistentes, atualizar o MCP
        if not data_match and transformer_data:
            app.mcp.set_data('transformer-inputs-store', transformer_data, validate=False)
            log_detailed(
                log,
                'info',
                f"[Global Info Panel Update] MCP atualizado com novos dados",
                module="global_updates",
                function="update_all_transformer_info_panels"
            )

    # Atualizar o cache de dados do transformador
    if hasattr(app, 'transformer_data_cache') and isinstance(transformer_data, dict):
        app.transformer_data_cache = transformer_data
        log_detailed(
            log,
            'info',
            f"[Global Info Panel Update] Cache global atualizado",
            module="global_updates",
            function="update_all_transformer_info_panels",
            data={'fields_count': len(transformer_data)}
        )

    # Criar o painel usando a função padronizada
    try:
        panel_html = standard_transformer_info_callback(
            transformer_data=transformer_data,
            module_name="global_updates",
            function_name="update_all_transformer_info_panels",
            app_instance=app
        )

        # Calcular o tempo de execução
        execution_time = time.time() - start_time

        log_detailed(
            log,
            'info',
            f"[Global Info Panel Update] Painel criado com sucesso",
            module="global_updates",
            function="update_all_transformer_info_panels",
            data={
                'execution_time_ms': round(execution_time * 1000, 2),
                'panel_type': type(panel_html).__name__
            }
        )

        # Return the same panel for all outputs
        return [panel_html] * len(info_panel_outputs)
    except Exception as e:
        # Calcular o tempo até a exceção
        execution_time = time.time() - start_time

        log_detailed(
            log,
            'error',
            "[Global Info Panel Update] Erro ao criar painel de informações",
            module="global_updates",
            function="update_all_transformer_info_panels",
            data={
                'execution_time_ms': round(execution_time * 1000, 2),
                'error_type': type(e).__name__
            },
            exception=e
        )

        error_panel = html.Div(f"Erro ao carregar dados do transformador: {e}", className="alert alert-danger")
        return [error_panel] * len(info_panel_outputs)
