"""
Utilitários para garantir a persistência de dados no MCP durante a navegação entre páginas.
"""

import logging
from typing import Dict, Any, Optional

log = logging.getLogger(__name__)

def patch_mcp(app, store_name: str, data: Dict[str, Any]) -> bool:
    """
    Atualiza o MCP com os dados fornecidos, mas apenas para campos não vazios.
    Isso evita que valores None sobrescrevam dados válidos no MCP.
    
    Args:
        app: Instância da aplicação Dash
        store_name: Nome do store no MCP
        data: Dicionário com os dados a serem atualizados
        
    Returns:
        bool: True se algum dado foi atualizado, False caso contrário
    """
    if not app.mcp or not data:
        return False
    
    # Obter os dados atuais do MCP
    current_data = app.mcp.get_data(store_name) or {}
    
    # Criar uma cópia para não modificar o dicionário original
    updated_data = current_data.copy()
    
    # Contar quantos campos foram atualizados
    updated_count = 0
    
    # Atualizar apenas os campos não vazios
    for key, value in data.items():
        if value is not None and value != "":
            if key not in current_data or current_data[key] != value:
                updated_data[key] = value
                updated_count += 1
                log.debug(f"[patch_mcp] Atualizando {key}: {current_data.get(key)} -> {value}")
    
    # Atualizar o MCP apenas se houver alterações
    if updated_count > 0:
        app.mcp.set_data(store_name, updated_data)
        log.info(f"[patch_mcp] {updated_count} campos atualizados no MCP para {store_name}")
        return True
    
    log.debug(f"[patch_mcp] Nenhum campo atualizado no MCP para {store_name}")
    return False

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
