"""
Utilitários para garantir a persistência de dados no MCP durante a navegação entre páginas.
"""

import logging
from typing import Dict

import dash
from dash.exceptions import PreventUpdate

log = logging.getLogger(__name__)

# Lista de campos essenciais que devem estar presentes para salvar dados no MCP
ESSENTIAL = ["potencia_mva", "tensao_at", "tensao_bt",
             "corrente_nominal_at", "corrente_nominal_bt"]

def _dados_ok(d: dict) -> bool:
    """
    Verifica se os dados essenciais estão presentes e são válidos.

    Garante que potência, tensões e correntes estejam preenchidos.

    Args:
        d: Dicionário de dados a ser verificado

    Returns:
        bool: True se todos os dados essenciais estiverem presentes e válidos, False caso contrário
    """
    # Verificar se o dicionário existe
    if not d or not isinstance(d, dict):
        return False

    # Verificar se todos os campos essenciais estão presentes e não são None, string vazia ou zero
    for k in ESSENTIAL:
        value = d.get(k)
        if value in (None, "", 0):
            return False

    return True


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

    # Verificar se os dados essenciais estão presentes usando a função _dados_ok
    has_essential_data = _dados_ok(source_data)

    # Log detalhado dos dados disponíveis para debug
    log.debug(
        f"[ensure_mcp_data_propagation] Dados disponíveis no store {source_store}: potencia_mva={source_data.get('potencia_mva')}, tensao_at={source_data.get('tensao_at')}, tensao_bt={source_data.get('tensao_bt')}, corrente_nominal_at={source_data.get('corrente_nominal_at')}, corrente_nominal_bt={source_data.get('corrente_nominal_bt')}"
    )

    if not has_essential_data:
        missing_fields = [k for k in ESSENTIAL if source_data.get(k) in (None, "", 0)]
        log.warning(
            f"[ensure_mcp_data_propagation] Dados essenciais ausentes no store de origem {source_store}: {missing_fields}"
        )
        return {store: False for store in target_stores}

    # Preparar os dados para propagação
    propagation_data = {
        "transformer_data": {
            "potencia_mva": source_data.get("potencia_mva"),
            "tensao_at": source_data.get("tensao_at"),
            "tensao_bt": source_data.get("tensao_bt"),
            "corrente_nominal_at": source_data.get("corrente_nominal_at"),
            "corrente_nominal_bt": source_data.get("corrente_nominal_bt"),
            "tipo_transformador": source_data.get("tipo_transformador"),
            "frequencia": source_data.get("frequencia"),
            "impedancia": source_data.get("impedancia"),
        }
    }

    # Propagar para cada store de destino
    results = {}
    for store in target_stores:
        # Verificar se o store já tem dados
        target_data = app.mcp.get_data(store)
        if not target_data or not target_data.get("transformer_data"):
            # Store vazio, atualizar diretamente
            app.mcp.set_data(store, propagation_data)
            results[store] = True
            log.info(f"[ensure_mcp_data_propagation] Dados propagados para {store} (store vazio)")
        else:
            # Store já tem dados, fazer patch apenas dos campos essenciais
            current_transformer_data = target_data.get("transformer_data", {})
            updated = False

            for key, value in propagation_data["transformer_data"].items():
                if value is not None and (
                    key not in current_transformer_data or current_transformer_data[key] is None
                ):
                    current_transformer_data[key] = value
                    updated = True

            if updated:
                target_data["transformer_data"] = current_transformer_data
                app.mcp.set_data(store, target_data)
                results[store] = True
                log.info(f"[ensure_mcp_data_propagation] Dados atualizados em {store}")
            else:
                results[store] = False
                log.debug(
                    f"[ensure_mcp_data_propagation] Nenhuma atualização necessária para {store}"
                )

    return results
