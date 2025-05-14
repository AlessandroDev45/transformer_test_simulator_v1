# components/global_stores.py
"""
Componente para armazenar todos os stores globais da aplicação.
"""
import logging

from dash import dcc

log = logging.getLogger(__name__)


def create_global_stores(app=None):  # Aceita app como argumento opcional
    """
    Cria todos os stores globais necessários para a aplicação.

    Args:
        app: A instância da aplicação Dash (opcional)
    """
    log.info("Criando stores globais...")

    # Importar valores padrão para transformer-inputs-store
    from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS

    # Tenta obter dados iniciais do app se disponível, senão usa defaults
    transformer_initial_data = DEFAULT_TRANSFORMER_INPUTS.copy()
    losses_initial_data = {"resultados_perdas_vazio": {}, "resultados_perdas_carga": {}}

    # Removida a correção para FLASH-BACK que usava dados fixos
    # Agora usamos apenas os dados do MCP ou os valores padrão do DEFAULT_TRANSFORMER_INPUTS

    if app is not None:
        # Se o MCP estiver inicializado no app, tenta obter dados dele
        if hasattr(app, "mcp") and app.mcp is not None:
            mcp_data = app.mcp.get_data("transformer-inputs-store")

            # Usar os dados do MCP diretamente
            transformer_initial_data = mcp_data or transformer_initial_data

            losses_initial_data = app.mcp.get_data("losses-store") or losses_initial_data
            # ... Fazer o mesmo para outros stores se necessário ...
        # Se não houver MCP, tenta usar caches se existirem
        elif hasattr(app, "transformer_data_cache"):
            cache_data = app.transformer_data_cache

            # Usar os dados do cache diretamente
            transformer_initial_data = cache_data or transformer_initial_data

        if hasattr(app, "losses_store_initial"):
            losses_initial_data = app.losses_store_initial or losses_initial_data

    stores = [
        # Stores principais - 'session' para persistência entre páginas
        dcc.Store(
            id="transformer-inputs-store", storage_type="session", data=transformer_initial_data
        ),
        dcc.Store(id="losses-store", storage_type="session", data=losses_initial_data),
        dcc.Store(id="impulse-store", storage_type="session", data={}),
        dcc.Store(id="dieletric-analysis-store", storage_type="session", data={}),
        dcc.Store(id="applied-voltage-store", storage_type="session", data={}),
        dcc.Store(id="induced-voltage-store", storage_type="session", data={}),
        dcc.Store(id="short-circuit-store", storage_type="session", data={}),
        dcc.Store(id="temperature-rise-store", storage_type="session", data={}),
        dcc.Store(id="comprehensive-analysis-store", storage_type="session", data={}),
        # Stores temporários (memory)
        dcc.Store(id="history-temp-store", storage_type="memory", data={}),
        dcc.Store(id="delete-session-id-store", storage_type="memory", data={}),
        dcc.Store(id="front-resistor-data", storage_type="memory", data={}),
        dcc.Store(id="tail-resistor-data", storage_type="memory", data={}),
        dcc.Store(id="calculated-inductance", storage_type="memory", data={}),
        dcc.Store(id="simulation-status", storage_type="memory", data={"running": False}),
        dcc.Store(
            id="limit-status-store", storage_type="memory", data={"limite_atingido": False}
        ),  # Store para status do limite
        # Stores para normas
        dcc.Store(id="standards-processing-status-store", storage_type="memory", data=None),
        dcc.Store(id="standards-current-search", storage_type="memory", data=None),
        dcc.Store(id="standards-current-category", storage_type="memory", data=None),
        dcc.Store(id="standards-current-standard", storage_type="memory", data=None),
    ]

    log.info(
        f"Stores globais criados: {[f'{store.id} ({store.storage_type})' for store in stores]}"
    )
    return stores
