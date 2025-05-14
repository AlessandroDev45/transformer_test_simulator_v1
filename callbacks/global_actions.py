# callbacks/global_actions.py
"""
Callbacks para ações globais da aplicação, como limpar todos os campos.
"""
import logging

from dash import Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate

# Importar a instância da aplicação
from app import app

log = logging.getLogger(__name__)


# --- Callback para abrir o modal de confirmação ---
def global_actions_toggle_clear_modal(n_global, n_cancel, n_confirm, is_open):
    """Abre ou fecha o modal de confirmação para limpar todos os campos."""
    print(f"[DEBUG] toggle_clear_modal acionado. Trigger: {ctx.triggered_id}")

    if ctx.triggered_id == "global-clear-button":
        print("[DEBUG] Abrindo modal de confirmação para limpar campos")
        return True
    elif ctx.triggered_id in ["clear-cancel-button", "clear-confirm-button"]:
        print(f"[DEBUG] Fechando modal de confirmação. Botão: {ctx.triggered_id}")
        return False

    print("[DEBUG] Mantendo estado atual do modal")
    return is_open


# --- Callback para limpar todos os campos ---
def global_actions_clear_all_data(n_clicks, pathname):
    """Limpa todos os dados armazenados nos stores quando o botão de confirmação é clicado."""
    print(f"[DEBUG] clear_all_data acionado. n_clicks: {n_clicks}, pathname: {pathname}")

    # Log detalhado para diagnóstico
    log.info(f"CLEAR_ALL_DATA Start - Trigger: {ctx.triggered_id}, Pathname: {pathname}")
    print(f"[DEBUG] CLEAR_ALL_DATA Start - Trigger: {ctx.triggered_id}, Pathname: {pathname}")

    if n_clicks is None or n_clicks == 0:
        print("[DEBUG] PreventUpdate em clear_all_data (n_clicks é None ou 0)")
        log.info("CLEAR_ALL_DATA Aborted - n_clicks is None or 0")
        raise PreventUpdate

    # Verificar se estamos em uma página que não deve atualizar os stores
    if pathname and pathname.strip("/") in ["consulta-normas", "gerenciar-normas"]:
        print(f"[DEBUG] Ignorando limpeza em página não relacionada: {pathname}")
        log.info(f"CLEAR_ALL_DATA Skipped - Pathname: {pathname} is not related")
        return [no_update] * 12

    log.info("Limpando todos os dados da aplicação")
    print("[DEBUG] Iniciando limpeza de todos os dados da aplicação")

    # Usar o MCP para limpar todos os dados
    try:
        if hasattr(app, "mcp") and app.mcp is not None:
            # Usar o MCP para limpar todos os dados
            log.info("Usando MCP para limpar todos os dados")
            print("[DEBUG] Usando MCP para limpar todos os dados")

            # Limpar todos os stores através do MCP
            cleared_data = app.mcp.clear_data()

            # Atualizar o cache da aplicação
            app.transformer_data_cache = cleared_data.get("transformer-inputs-store", {}).copy()
            log.info("Cache de dados do transformador limpo via MCP.")
            print("[DEBUG] Cache de dados do transformador limpo via MCP.")

            # Log de finalização
            log.info("CLEAR_ALL_DATA End - Returning cleared data via MCP")
            print("[DEBUG] CLEAR_ALL_DATA End - Returning cleared data via MCP")

            # Retornar os dados limpos do MCP
            return (
                cleared_data.get("transformer-inputs-store", {}),  # transformer-inputs-store
                cleared_data.get("losses-store", {}),  # losses-store
                cleared_data.get("impulse-store", {}),  # impulse-store
                cleared_data.get("dieletric-analysis-store", {}),  # dieletric-analysis-store
                cleared_data.get("applied-voltage-store", {}),  # applied-voltage-store
                cleared_data.get("induced-voltage-store", {}),  # induced-voltage-store
                cleared_data.get("short-circuit-store", {}),  # short-circuit-store
                cleared_data.get("temperature-rise-store", {}),  # temperature-rise-store
                cleared_data.get("front-resistor-data", {}),  # front-resistor-data
                cleared_data.get("tail-resistor-data", {}),  # tail-resistor-data
                cleared_data.get("calculated-inductance", {}),  # calculated-inductance
                cleared_data.get("simulation-status", {"running": False}),  # simulation-status
            )
        else:
            # Fallback para o método antigo se o MCP não estiver disponível
            log.warning("MCP não disponível. Usando método antigo para limpar dados.")
            print("[DEBUG] MCP não disponível. Usando método antigo para limpar dados.")

            # Valores padrão para cada store
            from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS

            transformer_inputs_default = DEFAULT_TRANSFORMER_INPUTS.copy()

            # Atualiza o cache da aplicação
            app.transformer_data_cache = transformer_inputs_default.copy()
            log.info("Cache de dados do transformador limpo.")
            print("[DEBUG] Cache de dados do transformador limpo.")

            # Log de finalização
            log.info("CLEAR_ALL_DATA End - Returning cleared data via fallback method")
            print("[DEBUG] CLEAR_ALL_DATA End - Returning cleared data via fallback method")

            # Retorna valores vazios para todos os stores
            return (
                transformer_inputs_default,  # transformer-inputs-store
                {},  # losses-store
                {},  # impulse-store
                {},  # dieletric-analysis-store
                {},  # applied-voltage-store
                {},  # induced-voltage-store
                {},  # short-circuit-store
                {},  # temperature-rise-store
                {},  # front-resistor-data
                {},  # tail-resistor-data
                {},  # calculated-inductance
                {"running": False},  # simulation-status
            )
    except Exception as e:
        log.error(f"Erro ao limpar dados: {e}")
        print(f"[DEBUG] Erro ao limpar dados: {e}")
        import traceback

        print(f"[DEBUG] Traceback: {traceback.format_exc()}")

        # Valores padrão para cada store em caso de erro
        from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS

        transformer_inputs_default = DEFAULT_TRANSFORMER_INPUTS.copy()

        # Retorna valores padrão em caso de erro
        return (
            transformer_inputs_default,  # transformer-inputs-store
            {},  # losses-store
            {},  # impulse-store
            {},  # dieletric-analysis-store
            {},  # applied-voltage-store
            {},  # induced-voltage-store
            {},  # short-circuit-store
            {},  # temperature-rise-store
            {},  # front-resistor-data
            {},  # tail-resistor-data
            {},  # calculated-inductance
            {"running": False},  # simulation-status
        )


# Registrar os callbacks com a aplicação
def register_global_actions_callbacks(app):
    """Registra os callbacks de ações globais com a aplicação."""
    app.callback(
        Output("clear-confirm-modal", "is_open"),
        [
            Input("global-clear-button", "n_clicks"),
            Input("clear-cancel-button", "n_clicks"),
            Input("clear-confirm-button", "n_clicks"),
        ],
        [State("clear-confirm-modal", "is_open")],
        prevent_initial_call=True,
    )(global_actions_toggle_clear_modal)

    app.callback(
        # Outputs para os stores (com allow_duplicate=True)
        [
            Output("transformer-inputs-store", "data", allow_duplicate=True),
            Output("losses-store", "data", allow_duplicate=True),
            Output("impulse-store", "data", allow_duplicate=True),
            Output("dieletric-analysis-store", "data", allow_duplicate=True),
            Output("applied-voltage-store", "data", allow_duplicate=True),
            Output("induced-voltage-store", "data", allow_duplicate=True),
            Output("short-circuit-store", "data", allow_duplicate=True),
            Output("temperature-rise-store", "data", allow_duplicate=True),
            Output("front-resistor-data", "data", allow_duplicate=True),
            Output("tail-resistor-data", "data", allow_duplicate=True),
            Output("calculated-inductance", "data", allow_duplicate=True),
            Output("simulation-status", "data", allow_duplicate=True),
        ],
        [Input("clear-confirm-button", "n_clicks")],
        [State("url", "pathname")],
        prevent_initial_call=True,
    )(global_actions_clear_all_data)
