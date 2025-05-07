"""
Utilitários para garantir a persistência de dados no MCP durante a navegação entre páginas.
"""

import logging
from typing import Dict, Any, Optional
from utils.mcp_utils import patch_mcp  # Importar a função patch_mcp do módulo mcp_utils

log = logging.getLogger(__name__)

def ensure_mcp_data_propagation(app, source_store: str, target_stores: list) -> Dict[str, bool]:
    """
    Garante que os dados do store de origem sejam propagados para os stores de destino.

    Args:
        app: Instância da aplicação Dash
        source_store: Nome do store de origem
        target_stores: Lista de nomes dos stores de destino

    Returns:
        Dict[str, bool]: Dicionário com o status de atualização de cada store
    """
    if not app.mcp:
        return {store: False for store in target_stores}

    # Obter os dados do store de origem
    source_data = app.mcp.get_data(source_store)
    if not source_data:
        log.warning(f"[ensure_mcp_data_propagation] Store de origem {source_store} está vazio")
        return {store: False for store in target_stores}

    # Verificar se os dados essenciais estão presentes
    has_essential_data = (
        source_data.get('potencia_mva') is not None and
        source_data.get('tensao_at') is not None and
        source_data.get('tensao_bt') is not None
    )

    # Se não tiver dados essenciais, verificar se há dados de corrente que podemos usar
    if not has_essential_data and source_data.get('corrente_nominal_at') is not None:
        log.info(f"[ensure_mcp_data_propagation] Dados de corrente encontrados no store de origem {source_store}")
        has_essential_data = True

    # Log detalhado dos dados disponíveis para debug
    log.debug(f"[ensure_mcp_data_propagation] Dados disponíveis no store {source_store}: potencia_mva={source_data.get('potencia_mva')}, tensao_at={source_data.get('tensao_at')}, tensao_bt={source_data.get('tensao_bt')}, corrente_nominal_at={source_data.get('corrente_nominal_at')}")

    if not has_essential_data:
        log.warning(f"[ensure_mcp_data_propagation] Dados essenciais ausentes no store de origem {source_store}")
        return {store: False for store in target_stores}

    # Preparar os dados para propagação
    propagation_data = {
        'transformer_data': {
            'potencia_mva': source_data.get('potencia_mva'),
            'tensao_at': source_data.get('tensao_at'),
            'tensao_bt': source_data.get('tensao_bt'),
            'corrente_nominal_at': source_data.get('corrente_nominal_at'),
            'corrente_nominal_bt': source_data.get('corrente_nominal_bt'),
            'tipo_transformador': source_data.get('tipo_transformador'),
            'frequencia': source_data.get('frequencia'),
            'impedancia': source_data.get('impedancia')
        }
    }

    # Propagar para cada store de destino
    results = {}
    for store in target_stores:
        # Verificar se o store já tem dados
        target_data = app.mcp.get_data(store)
        if not target_data or not target_data.get('transformer_data'):
            # Store vazio, atualizar diretamente
            app.mcp.set_data(store, propagation_data)
            results[store] = True
            log.info(f"[ensure_mcp_data_propagation] Dados propagados para {store} (store vazio)")
        else:
            # Store já tem dados, fazer patch apenas dos campos essenciais
            current_transformer_data = target_data.get('transformer_data', {})
            updated = False

            for key, value in propagation_data['transformer_data'].items():
                if value is not None and (key not in current_transformer_data or current_transformer_data[key] is None):
                    current_transformer_data[key] = value
                    updated = True

            if updated:
                target_data['transformer_data'] = current_transformer_data
                app.mcp.set_data(store, target_data)
                results[store] = True
                log.info(f"[ensure_mcp_data_propagation] Dados atualizados em {store}")
            else:
                results[store] = False
                log.debug(f"[ensure_mcp_data_propagation] Nenhuma atualização necessária para {store}")

    return results
