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
# Estes campos são considerados parte da "fonte única da verdade" e não devem ser duplicados
# em outros stores. Outros stores devem referenciar estes campos do transformer-inputs-store.
BASIC_FIELDS = {
    # Dados básicos do transformador
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

    # Níveis de isolamento (também são dados básicos)
    "nbi_at",
    "sil_at",
    "nbi_bt",
    "sil_bt",
    "nbi_terciario",
    "sil_terciario",
    "nbi_neutro_at",
    "sil_neutro_at",
    "nbi_neutro_bt",
    "sil_neutro_bt",
    "nbi_neutro_terciario",
    "sil_neutro_terciario",
    "teste_tensao_aplicada_at",
    "teste_tensao_induzida_at",
    "teste_tensao_aplicada_bt",
    "teste_tensao_aplicada_terciario",
    "teste_tensao_induzida",
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
    Propaga dados entre stores seguindo o padrão de "fonte única da verdade".

    Quando o source_store é o AUTHORITATIVE_STORE (transformer-inputs-store):
    - Todos os dados são propagados para os stores de destino
    - Os dados básicos são colocados em transformer_data

    Quando o source_store NÃO é o AUTHORITATIVE_STORE:
    - Apenas dados específicos do módulo são propagados
    - Dados básicos não são propagados (devem ser referenciados do AUTHORITATIVE_STORE)

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

    # Verificar se a origem é a fonte-de-verdade
    is_authoritative = source_store == AUTHORITATIVE_STORE

    # Log informativo sobre a fonte dos dados
    log.info(
        f"[ensure_mcp_data_propagation] Store de origem {source_store} {'É' if is_authoritative else 'NÃO é'} a fonte-de-verdade para campos básicos"
    )

    # Preparar os dados para propagação
    results = {}

    # Processar cada store de destino
    for store in target_stores:
        # Verificar se o store já tem dados
        target_data = app.mcp.get_data(store)

        # Inicializar ou obter transformer_data
        if not target_data:
            target_data = {}

        if "transformer_data" not in target_data:
            target_data["transformer_data"] = {}

        # Determinar quais dados propagar com base na fonte
        if is_authoritative:
            # Se a origem é a fonte-de-verdade, propagar todos os campos básicos
            updated = False

            # Propagar campos básicos para transformer_data
            for key, value in source_data.items():
                if key in BASIC_FIELDS and value is not None:
                    target_data["transformer_data"][key] = value
                    updated = True

            # Propagar campos específicos (inputs_*)
            for key, value in source_data.items():
                if key.startswith('inputs_') and value is not None:
                    target_data[key] = value
                    updated = True

            if updated:
                app.mcp.set_data(store, target_data)
                results[store] = True
                log.info(f"[ensure_mcp_data_propagation] Dados básicos propagados para {store}")
            else:
                results[store] = False
                log.debug(f"[ensure_mcp_data_propagation] Nenhuma atualização necessária para {store}")

        else:
            # Se a origem NÃO é a fonte-de-verdade, propagar apenas dados específicos do módulo
            # (não propagar campos básicos, que devem vir apenas da fonte-de-verdade)
            updated = False

            # Propagar apenas campos não-básicos para transformer_data
            for key, value in source_data.items():
                if key not in BASIC_FIELDS and not key.startswith('inputs_') and value is not None:
                    target_data["transformer_data"][key] = value
                    updated = True

            # Propagar campos específicos (inputs_*)
            for key, value in source_data.items():
                if key.startswith('inputs_') and value is not None:
                    target_data[key] = value
                    updated = True

            if updated:
                app.mcp.set_data(store, target_data)
                results[store] = True
                log.info(f"[ensure_mcp_data_propagation] Dados específicos propagados para {store}")
            else:
                results[store] = False
                log.debug(f"[ensure_mcp_data_propagation] Nenhuma atualização necessária para {store}")

    return results
