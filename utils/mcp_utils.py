# utils/mcp_utils.py
"""
Utilitários para manipulação do MCP (Master Control Program).
Fornece funções para manipular dados do MCP de forma segura.
"""
import copy
import logging
from typing import Any, Dict



from utils.mcp_persistence import _dados_ok, ESSENTIAL

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
    if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
        log.error("[patch_mcp] MCP não inicializado ou não disponível")
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
    changed_fields = []

    # Criar uma cópia dos dados atuais
    updated_data = copy.deepcopy(current_data)

    # Mesclar os dados válidos com os dados atuais
    deep_merge(valid_data, updated_data)

    # Verificar se houve mudanças comparando os dicionários chave por chave
    # Isso evita problemas com casting (int → float, str → int)
    if updated_data.keys() != current_data.keys():
        changes = True
        changed_fields.append("keys_different")
    else:
        for key in updated_data:
            # Se o valor é um dicionário, verificar recursivamente
            if isinstance(updated_data[key], dict) and isinstance(current_data.get(key), dict):
                # Verificação simplificada: se os dicionários têm chaves diferentes, há mudanças
                if set(updated_data[key].keys()) != set(current_data[key].keys()):
                    changes = True
                    changed_fields.append(f"{key}.keys")
                    break
                # Verificar valores dentro do dicionário
                for subkey in updated_data[key]:
                    # Se um dos valores é None e o outro não, são diferentes
                    if (updated_data[key][subkey] is None and current_data[key].get(subkey) is not None) or \
                       (updated_data[key][subkey] is not None and current_data[key].get(subkey) is None):
                        changes = True
                        changed_fields.append(f"{key}.{subkey}")
                        break

                    # Se ambos não são None, converter para string para comparação mais segura
                    if updated_data[key][subkey] is not None and current_data[key].get(subkey) is not None:
                        updated_val = str(updated_data[key][subkey])
                        current_val = str(current_data[key].get(subkey))

                        if updated_val != current_val:
                            changes = True
                            changed_fields.append(f"{key}.{subkey}")
                            break
                if changes:
                    break
            # Para valores simples, comparar como strings para evitar problemas de tipo
            else:
                # Se um dos valores é None e o outro não, são diferentes
                if (updated_data[key] is None and current_data.get(key) is not None) or \
                   (updated_data[key] is not None and current_data.get(key) is None):
                    changes = True
                    changed_fields.append(key)
                    break

                # Se ambos não são None, converter para string para comparação mais segura
                if updated_data[key] is not None and current_data.get(key) is not None:
                    updated_val = str(updated_data[key])
                    current_val = str(current_data.get(key))

                    if updated_val != current_val:
                        changes = True
                        changed_fields.append(key)
                        break

    if not changes:
        log.debug(f"[patch_mcp] Nenhuma mudança efetiva em {store_id}")
        return False
    else:
        log.info(f"[patch_mcp] Detectadas mudanças em {store_id}: {changed_fields[:5]}{'...' if len(changed_fields) > 5 else ''}")

    # Removida a verificação de dados essenciais para permitir o fluxo de dados
    # mesmo quando campos obrigatórios estão ausentes
    if store_id == "transformer-inputs-store" and not _dados_ok(updated_data):
        missing_fields = [k for k in ESSENTIAL if updated_data.get(k) in (None, "", 0)]
        log.warning(f"[patch_mcp] Dados essenciais faltando: {missing_fields}, mas continuando com a gravação")

    # Importar a função de conversão de tipos numpy
    from utils.store_diagnostics import convert_numpy_types

    # Converter os dados para tipos serializáveis antes de salvar no MCP
    try:
        serializable_data = convert_numpy_types(updated_data, debug_path=f"patch_mcp.{store_id}")
        log.info(f"[patch_mcp] Dados convertidos para tipos serializáveis antes de salvar no MCP")
    except Exception as e:
        log.error(f"[patch_mcp] Erro ao converter dados para tipos serializáveis: {e}")
        serializable_data = updated_data  # Usar os dados originais se a conversão falhar

    # Salvar os dados atualizados no MCP
    app_instance.mcp.set_data(store_id, serializable_data)

    log.info(f"[patch_mcp] Atualizado {store_id} com dados válidos")
    return True
