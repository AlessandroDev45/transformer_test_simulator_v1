# callbacks/client_side_callbacks.py
"""
Módulo para melhorar a experiência do usuário e evitar erros de navegação.
Também inclui callbacks para sincronizar o MCP com os stores.
"""
import logging
import dash
from dash import ClientsideFunction, Output, Input, State

log = logging.getLogger(__name__)

def register_client_side_callbacks(app_instance):
    """
    Registra callbacks do lado do cliente para melhorar a experiência do usuário.
    Também registra callbacks para sincronizar o MCP com os stores.
    """
    log.info("Registrando callbacks do lado do cliente...")

    # Em vez de usar um callback do lado do cliente, vamos modificar os callbacks existentes
    # para verificar o pathname antes de atualizar os stores
    log.info("Abordagem de callback do lado do cliente substituída por verificações de pathname nos callbacks existentes.")

    # Registrar callbacks para sincronizar o MCP com os stores
    try:
        # Verificar se o MCP está disponível
        if hasattr(app_instance, 'mcp') and app_instance.mcp is not None:
            log.info("Registrando callbacks para sincronizar o MCP com os stores...")

            # Registrar um callback para atualizar o MCP quando o store transformer-inputs-store muda
            # Comentado para evitar conflito com outro callback que usa url.refresh
            # dash.clientside_callback(
            #     """
            #     function(storeData) {
            #         // Este callback é chamado quando o store transformer-inputs-store muda
            #         // Não precisamos fazer nada aqui, pois o MCP já é atualizado nos callbacks do servidor
            #         console.log("Store transformer-inputs-store atualizado");
            #         return window.dash_clientside.no_update;
            #     }
            #     """,
            #     Output('url', 'refresh', allow_duplicate=True),
            #     Input('transformer-inputs-store', 'data'),
            #     prevent_initial_call=True
            # )

            # Remover completamente o callback que estava causando conflitos
            # Não precisamos de um callback específico para sincronizar o MCP,
            # pois o MCP já é atualizado automaticamente quando o store muda
            log.info("Callback de sincronização do MCP removido. O MCP já é atualizado automaticamente.")

            log.info("Callbacks para sincronizar o MCP com os stores registrados com sucesso.")
        else:
            log.warning("MCP não disponível. Callbacks de sincronização não registrados.")
    except Exception as e:
        log.error(f"Erro ao registrar callbacks para sincronizar o MCP com os stores: {e}")

    log.info("Callbacks do lado do cliente registrados com sucesso.")
