# components/global_stores.py
"""
Componente para armazenar todos os stores globais da aplicação.

IMPORTANTE: Os stores principais usam storage_type='local' para garantir que os dados
persistam entre navegações de páginas. Isso é essencial para que os dados inseridos
nas diferentes seções estejam disponíveis quando o usuário navega para a página de
Histórico e tenta salvar a sessão.

- storage_type='local': Dados persistem entre páginas e sessões do navegador
- storage_type='session': Dados persistem entre páginas, mas são perdidos ao fechar o navegador
- storage_type='memory': Dados são perdidos ao navegar entre páginas (NÃO USE para stores principais)
"""
from dash import dcc
import logging
from app import app

log = logging.getLogger(__name__)

def create_global_stores():
    """
    Cria todos os stores globais necessários para a aplicação.
    """
    log.info("Criando stores globais...")

    # Importar valores padrão para transformer-inputs-store
    from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS

    # Retorna uma lista de stores em vez de um container
    stores = [
        # Stores principais da aplicação - usando 'local' para persistir dados entre páginas
        dcc.Store(id='transformer-inputs-store', storage_type='local', data=DEFAULT_TRANSFORMER_INPUTS.copy()),
        dcc.Store(id='losses-store', storage_type='local', data=getattr(app, 'losses_store_initial', {'resultados_perdas_vazio': {}, 'resultados_perdas_carga': {}})),
        dcc.Store(id='impulse-store', storage_type='local', data={}),
        dcc.Store(id='dieletric-analysis-store', storage_type='local', data={}),
        dcc.Store(id='applied-voltage-store', storage_type='local', data={}),
        dcc.Store(id='induced-voltage-store', storage_type='local', data={}),
        dcc.Store(id='short-circuit-store', storage_type='local', data={}),
        dcc.Store(id='temperature-rise-store', storage_type='local', data={}),
        dcc.Store(id='comprehensive-analysis-store', storage_type='local', data={}),

        # Stores temporários (memory)
        dcc.Store(id='history-temp-store', storage_type='memory', data={}),
        dcc.Store(id='delete-session-id-store', storage_type='memory', data={}),
        dcc.Store(id="front-resistor-data", storage_type="memory", data={}),
        dcc.Store(id="tail-resistor-data", storage_type="memory", data={}),
        dcc.Store(id="calculated-inductance", storage_type="memory", data={}),
        dcc.Store(id="simulation-status", storage_type="memory", data={"running": False}),

        # Stores para o módulo de normas
        dcc.Store(id="standards-processing-status-store", storage_type="memory", data=None),
        dcc.Store(id="standards-current-search", storage_type="memory", data=None),
        dcc.Store(id="standards-current-category", storage_type="memory", data=None),
        dcc.Store(id="standards-current-standard", storage_type="memory", data=None),
    ]

    log.info(f"Stores globais criados: {[f'{store.id} ({store.storage_type})' for store in stores]}")
    return stores
