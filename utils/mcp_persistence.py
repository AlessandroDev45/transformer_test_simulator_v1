"""
Utilitários para garantir a persistência de dados no MCP durante a navegação entre páginas.
"""

import logging
from typing import Dict

log = logging.getLogger(__name__)

# Lista de campos essenciais que devem estar presentes para salvar dados no MCP
ESSENTIAL = ["potencia_mva", "tensao_at", "tensao_bt", "corrente_nominal_at", "corrente_nominal_bt"]

# Define a fonte-de-verdade (authoritative store) para os dados básicos
AUTHORITATIVE_STORE = "transformer-inputs-store"

# Define os campos básicos que só devem ser atualizados a partir da fonte-de-verdade
BASIC_FIELDS = {
    "potencia_mva",
    "tensao_at",
    "tensao_bt",
    "tensao_terciario",
    "corrente_nominal_at",
    "corrente_nominal_bt",
    "corrente_nominal_terciario",
    "corrente_nominal_at_tap_maior",
    "corrente_nominal_at_tap_menor",
    "tipo_transformador",
    "frequencia",
    "impedancia",
    "impedancia_tap_maior",
    "impedancia_tap_menor",
    "grupo_ligacao",
    "conexao_at",
    "conexao_bt",
    "conexao_terciario",
    "classe_tensao_at",
    "classe_tensao_bt",
    "classe_tensao_terciario",
}


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
    Garante que os dados do store de origem sejam propagados para os stores de destino,
    respeitando a fonte-de-verdade (authoritative store) para campos básicos.

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

    # Verificar se a origem é a fonte-de-verdade
    is_authoritative = source_store == AUTHORITATIVE_STORE
    if not is_authoritative:
        log.info(
            f"[ensure_mcp_data_propagation] Store de origem {source_store} NÃO é a fonte-de-verdade para campos básicos"
        )
    else:
        log.info(
            f"[ensure_mcp_data_propagation] Store de origem {source_store} É a fonte-de-verdade para campos básicos"
        )

    # Mesmo sem dados essenciais, continuamos com a propagação
    if not has_essential_data:
        missing_fields = [k for k in ESSENTIAL if source_data.get(k) in (None, "", 0)]
        log.warning(
            f"[ensure_mcp_data_propagation] Dados essenciais ausentes no store de origem {source_store}: {missing_fields}, mas continuando com a propagação"
        )

    # Preparar os dados para propagação
    propagation_data = {"transformer_data": {}}

    # Se a origem não é a fonte-de-verdade, não propagar campos básicos
    if not is_authoritative:
        # Copiar apenas campos que não são básicos
        for key, value in source_data.items():
            if key not in BASIC_FIELDS:
                propagation_data["transformer_data"][key] = value
        log.info(
            f"[ensure_mcp_data_propagation] Propagando apenas campos não-básicos de {source_store}"
        )
    else:
        # Se é a fonte-de-verdade, propagar todos os campos
        for key, value in source_data.items():
            propagation_data["transformer_data"][key] = value
        log.info(
            f"[ensure_mcp_data_propagation] Propagando todos os campos de {source_store} (fonte-de-verdade)"
        )

    # Propagar para cada store de destino
    results = {}
    for store in target_stores:
        # Verificar se o store já tem dados
        target_data = app.mcp.get_data(store)

        # Verificar se há dados específicos no store de origem
        specific_inputs = {}
        for key, value in source_data.items():
            if key.startswith('inputs_'):
                specific_inputs[key] = value
                log.debug(f"[ensure_mcp_data_propagation] Encontrado dado específico {key} no store de origem {source_store}")

        if not target_data or not target_data.get("transformer_data"):
            # Store vazio, atualizar diretamente
            new_data = propagation_data.copy()

            # Adicionar dados específicos, se houver
            if specific_inputs:
                for key, value in specific_inputs.items():
                    new_data[key] = value
                log.info(f"[ensure_mcp_data_propagation] Adicionando dados específicos ao store vazio {store}: {list(specific_inputs.keys())}")

            app.mcp.set_data(store, new_data)
            results[store] = True
            log.info(f"[ensure_mcp_data_propagation] Dados propagados para {store} (store vazio)")
        else:
            # Store já tem dados, fazer patch apenas dos campos essenciais
            current_transformer_data = target_data.get("transformer_data", {})
            updated = False

            # Verificar se o destino é a fonte-de-verdade
            is_dest_authoritative = store == AUTHORITATIVE_STORE

            for key, value in propagation_data["transformer_data"].items():
                # Se o destino é a fonte-de-verdade e o campo é básico, só aceitar se a origem também for a fonte-de-verdade
                if is_dest_authoritative and key in BASIC_FIELDS and not is_authoritative:
                    log.info(
                        f"[ensure_mcp_data_propagation] Ignorando atualização de {key} em {store} (fonte-de-verdade) a partir de {source_store}"
                    )
                    continue

                # Propagar se:
                # 1. O valor de origem não é None
                # 2. E (o valor de destino não existe OU é None OU é string vazia OU é zero)
                if value is not None and (
                    key not in current_transformer_data
                    or current_transformer_data[key] is None
                    or current_transformer_data[key] == ""
                    or current_transformer_data[key] == 0
                ):
                    current_transformer_data[key] = value
                    updated = True
                    log.info(f"[ensure_mcp_data_propagation] Atualizado {key}={value} em {store}")

            # Adicionar dados específicos, se houver
            if specific_inputs:
                for key, value in specific_inputs.items():
                    if key not in target_data or target_data[key] is None:
                        target_data[key] = value
                        updated = True
                        log.info(f"[ensure_mcp_data_propagation] Adicionado dado específico {key} ao store {store}")

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
