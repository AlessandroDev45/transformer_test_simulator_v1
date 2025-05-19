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



