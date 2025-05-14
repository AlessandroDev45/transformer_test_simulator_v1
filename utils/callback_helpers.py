# utils/callback_helpers.py
"""
Funções auxiliares para padronizar os callbacks em todos os módulos.
"""
import json
import logging
import time

from dash import html, no_update

from components.transformer_info_template import create_transformer_info_panel
from utils.logger import check_store_exists, log_detailed

log = logging.getLogger(__name__)


def safe_float(value, default=None):
    """Converte valor para float de forma segura, retorna default em caso de erro."""
    if value is None or value == "":
        return default
    try:
        s_value = str(value).replace(".", "").replace(",", ".")
        return float(s_value)
    except (ValueError, TypeError):
        log.warning(f"Could not convert '{value}' to float.")
        return default


def standard_transformer_info_callback(transformer_data, module_name, function_name, app_instance):
    """
    Função padronizada para atualizar o painel de informações do transformador.

    Args:
        transformer_data: Dados do transformador do store
        module_name: Nome do módulo para logs
        function_name: Nome da função para logs
        app_instance: Instância da aplicação para acessar o MCP

    Returns:
        html.Div: Painel de informações do transformador ou mensagem de erro
    """
    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    log_detailed(
        log,
        "debug",
        f"[{module_name}] Iniciando atualização do painel de informações",
        module=module_name,
        function=function_name,
        data={
            "timestamp": timestamp,
            "data_type": type(transformer_data).__name__,
            "data_keys": list(transformer_data.keys())
            if isinstance(transformer_data, dict)
            else None,
            "data_size": len(json.dumps(transformer_data)) if transformer_data else 0,
        },
    )

    # Verificar se o MCP está disponível
    mcp_available = hasattr(app_instance, "mcp") and app_instance.mcp is not None

    # Verificar se os dados do transformador existem
    if not check_store_exists(transformer_data, "transformer-inputs-store"):
        log_detailed(
            log,
            "warning",
            f"[{module_name}] Dados do transformador não disponíveis ou inválidos",
            module=module_name,
            function=function_name,
        )

        # Tentar obter dados do MCP se disponível
        if mcp_available:
            log_detailed(
                log,
                "info",
                f"[{module_name}] Tentando obter dados do MCP",
                module=module_name,
                function=function_name,
            )

            transformer_data = app_instance.mcp.get_data("transformer-inputs-store")

            # Verificar novamente se os dados são válidos
            if not check_store_exists(transformer_data, "transformer-inputs-store"):
                log_detailed(
                    log,
                    "warning",
                    f"[{module_name}] Dados do MCP também não disponíveis ou inválidos",
                    module=module_name,
                    function=function_name,
                )
                return html.Div(
                    "Dados do transformador não disponíveis", className="alert alert-warning"
                )
        else:
            return html.Div(
                "Dados do transformador não disponíveis", className="alert alert-warning"
            )

    # Se chegamos aqui, temos dados válidos (do store ou do MCP)
    try:
        # Criar painel de informações usando o template comum
        panel_html = create_transformer_info_panel(transformer_data)

        # Calcular o tempo de execução
        execution_time = time.time() - start_time

        log_detailed(
            log,
            "debug",
            f"[{module_name}] Painel de informações criado com sucesso",
            module=module_name,
            function=function_name,
            data={
                "execution_time_ms": round(execution_time * 1000, 2),
                "panel_type": type(panel_html).__name__,
            },
        )

        return panel_html
    except Exception as e:
        # Calcular o tempo até a exceção
        execution_time = time.time() - start_time

        log_detailed(
            log,
            "error",
            f"[{module_name}] Erro ao criar painel de informações",
            module=module_name,
            function=function_name,
            data={
                "execution_time_ms": round(execution_time * 1000, 2),
                "error_type": type(e).__name__,
            },
            exception=e,
        )

        return html.Div(
            f"Erro ao criar painel de informações: {str(e)}", className="alert alert-danger"
        )


def standard_store_update_callback(
    store_data, new_data, module_name, function_name, app_instance, store_id
):
    """
    Função padronizada para atualizar um store.

    Args:
        store_data: Dados atuais do store
        new_data: Novos dados a serem adicionados ao store
        module_name: Nome do módulo para logs
        function_name: Nome da função para logs
        app_instance: Instância da aplicação para acessar o MCP
        store_id: ID do store a ser atualizado

    Returns:
        dict: Store atualizado
    """
    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    log_detailed(
        log,
        "debug",
        f"[{module_name}] Iniciando atualização do store {store_id}",
        module=module_name,
        function=function_name,
        data={
            "timestamp": timestamp,
            "store_id": store_id,
            "current_data_type": type(store_data).__name__,
            "new_data_type": type(new_data).__name__,
        },
    )

    # Inicializar store_data se for None
    if store_data is None:
        store_data = {}

    # Verificar se o MCP está disponível
    mcp_available = hasattr(app_instance, "mcp") and app_instance.mcp is not None

    try:
        # Atualizar o store com os novos dados
        updated_store = store_data.copy() if isinstance(store_data, dict) else {}

        # Se new_data for um dicionário, atualizamos o store com ele
        if isinstance(new_data, dict):
            updated_store.update(new_data)

        # Atualizar o MCP se disponível
        if mcp_available:
            log_detailed(
                log,
                "debug",
                f"[{module_name}] Atualizando store {store_id} no MCP",
                module=module_name,
                function=function_name,
            )

            app_instance.mcp.set_data(store_id, updated_store, validate=False)

        # Calcular o tempo de execução
        execution_time = time.time() - start_time

        log_detailed(
            log,
            "debug",
            f"[{module_name}] Store {store_id} atualizado com sucesso",
            module=module_name,
            function=function_name,
            data={
                "execution_time_ms": round(execution_time * 1000, 2),
                "updated_store_keys": list(updated_store.keys())
                if isinstance(updated_store, dict)
                else None,
            },
        )

        return updated_store
    except Exception as e:
        # Calcular o tempo até a exceção
        execution_time = time.time() - start_time

        log_detailed(
            log,
            "error",
            f"[{module_name}] Erro ao atualizar store {store_id}",
            module=module_name,
            function=function_name,
            data={
                "execution_time_ms": round(execution_time * 1000, 2),
                "error_type": type(e).__name__,
            },
            exception=e,
        )

        # Retornar o store original em caso de erro
        return store_data if store_data is not None else {}


def standard_load_from_store_callback(
    store_data,
    module_name,
    function_name,
    app_instance,
    store_id,
    pathname=None,
    expected_pathname=None,
):
    """
    Função padronizada para carregar dados de um store.

    Args:
        store_data: Dados do store
        module_name: Nome do módulo para logs
        function_name: Nome da função para logs
        app_instance: Instância da aplicação para acessar o MCP
        store_id: ID do store a ser carregado
        pathname: Pathname atual (opcional)
        expected_pathname: Pathname esperado para este módulo (opcional)

    Returns:
        dict: Dados do store ou dados do MCP
    """
    start_time = time.time()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Verificar se estamos na página correta (se pathname e expected_pathname foram fornecidos)
    if pathname is not None and expected_pathname is not None:
        if pathname != expected_pathname:
            log_detailed(
                log,
                "debug",
                f"[{module_name}] Ignorando carregamento em página diferente: {pathname} != {expected_pathname}",
                module=module_name,
                function=function_name,
            )
            return no_update

    log_detailed(
        log,
        "debug",
        f"[{module_name}] Iniciando carregamento do store {store_id}",
        module=module_name,
        function=function_name,
        data={
            "timestamp": timestamp,
            "store_id": store_id,
            "data_type": type(store_data).__name__,
            "data_keys": list(store_data.keys()) if isinstance(store_data, dict) else None,
        },
    )

    # Verificar se o MCP está disponível
    mcp_available = hasattr(app_instance, "mcp") and app_instance.mcp is not None

    # Verificar se os dados do store existem
    if not check_store_exists(store_data, store_id):
        log_detailed(
            log,
            "warning",
            f"[{module_name}] Dados do store {store_id} não disponíveis ou inválidos",
            module=module_name,
            function=function_name,
        )

        # Tentar obter dados do MCP se disponível
        if mcp_available:
            log_detailed(
                log,
                "info",
                f"[{module_name}] Tentando obter dados do MCP para store {store_id}",
                module=module_name,
                function=function_name,
            )

            mcp_data = app_instance.mcp.get_data(store_id)

            # Verificar se os dados do MCP são válidos
            if check_store_exists(mcp_data, store_id):
                # Calcular o tempo de execução
                execution_time = time.time() - start_time

                log_detailed(
                    log,
                    "info",
                    f"[{module_name}] Dados do store {store_id} obtidos do MCP com sucesso",
                    module=module_name,
                    function=function_name,
                    data={
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "data_keys": list(mcp_data.keys()) if isinstance(mcp_data, dict) else None,
                    },
                )

                return mcp_data
            else:
                log_detailed(
                    log,
                    "warning",
                    f"[{module_name}] Dados do MCP para store {store_id} também não disponíveis ou inválidos",
                    module=module_name,
                    function=function_name,
                )
                return {}
        else:
            return {}

    # Se chegamos aqui, os dados do store são válidos
    # Calcular o tempo de execução
    execution_time = time.time() - start_time

    log_detailed(
        log,
        "debug",
        f"[{module_name}] Dados do store {store_id} carregados com sucesso",
        module=module_name,
        function=function_name,
        data={
            "execution_time_ms": round(execution_time * 1000, 2),
            "data_keys": list(store_data.keys()) if isinstance(store_data, dict) else None,
        },
    )

    return store_data
