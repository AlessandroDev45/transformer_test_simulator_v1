# utils/mcp_utils.py
"""
Utilitários para manipulação do MCP (Master Control Program).
Fornece funções para manipular dados do MCP de forma segura.
"""
import logging
from typing import Dict, Any, Optional
import copy

log = logging.getLogger(__name__)

def patch_mcp(store_id: str, data: Dict[str, Any], app=None) -> bool:
    """
    Atualiza apenas os campos não vazios no MCP, preservando os valores existentes.
    Suporta estruturas aninhadas como dicionários dentro de dicionários.

    Args:
        store_id: ID do store no MCP
        data: Dicionário com os dados a serem atualizados
        app: Instância da aplicação Dash (opcional, usa o app global se não fornecido)

    Returns:
        bool: True se algum campo foi atualizado, False caso contrário
    """
    from app import app as global_app

    # Usar a instância global se não fornecida
    app_instance = app or global_app

    # Verificar se o MCP está disponível
    if not hasattr(app_instance, 'mcp') or app_instance.mcp is None:
        log.error(f"[patch_mcp] MCP não inicializado ou não disponível")
        return False

    # Obter os dados atuais do store
    current_data = app_instance.mcp.get_data(store_id) or {}

    # Função recursiva para filtrar campos não vazios em estruturas aninhadas
    def filter_non_empty(data_dict):
        if not isinstance(data_dict, dict):
            return data_dict

        result = {}
        for k, v in data_dict.items():
            if isinstance(v, dict):
                # Recursivamente filtrar dicionários aninhados
                filtered = filter_non_empty(v)
                if filtered:  # Adicionar apenas se o dicionário filtrado não estiver vazio
                    result[k] = filtered
            elif v not in (None, "", []):
                result[k] = v
        return result

    # Filtrar apenas os campos não vazios do novo data, incluindo estruturas aninhadas
    valid_data = filter_non_empty(data)

    if not valid_data:
        log.debug(f"[patch_mcp] Nenhum dado válido para atualizar em {store_id}")
        return False

    # Função recursiva para mesclar dicionários aninhados
    def deep_merge(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # Se o valor é um dicionário, mesclar recursivamente
                node = destination.setdefault(key, {})
                if isinstance(node, dict):
                    deep_merge(value, node)
                else:
                    # Se o destino não é um dicionário, substituir
                    destination[key] = value
            else:
                # Para valores não-dicionário, simplesmente substituir
                destination[key] = value
        return destination

    # Verificar se há mudanças efetivas
    changes = False

    # Criar uma cópia dos dados atuais
    updated_data = copy.deepcopy(current_data)

    # Mesclar os dados válidos com os dados atuais
    deep_merge(valid_data, updated_data)

    # Verificar se houve mudanças comparando os dicionários
    if updated_data != current_data:
        changes = True

    if not changes:
        log.debug(f"[patch_mcp] Nenhuma mudança efetiva em {store_id}")
        return False

    # Salvar os dados atualizados no MCP
    app_instance.mcp.set_data(store_id, updated_data)

    log.info(f"[patch_mcp] Atualizado {store_id} com dados válidos")
    return True
