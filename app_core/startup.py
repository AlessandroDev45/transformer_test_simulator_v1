"""
Módulo de inicialização da aplicação.
Responsável por carregar dados iniciais e configurar o MCP.
"""
import json
import logging
import pathlib
from typing import Any, Dict

# Configurar logger
log = logging.getLogger(__name__)


def load_default_transformer_data() -> Dict[str, Any]:
    """
    Carrega os dados padrão do transformador a partir do arquivo JSON.

    Returns:
        Dict[str, Any]: Dados padrão do transformador
    """
    try:
        # Caminho para o arquivo de dados padrão
        default_file = pathlib.Path("defaults/transformer.json")

        # Verificar se o arquivo existe
        if not default_file.exists():
            log.warning(f"Arquivo de dados padrão não encontrado: {default_file}")
            return {}

        # Carregar dados do arquivo JSON
        data = json.loads(default_file.read_text(encoding="utf-8"))
        log.info(f"Dados padrão do transformador carregados de {default_file}")

        return data
    except Exception as e:
        log.error(f"Erro ao carregar dados padrão do transformador: {e}", exc_info=True)
        return {}


def seed_mcp(mcp_instance=None, app_instance=None) -> bool:
    """
    Inicializa o MCP com dados padrão.

    Args:
        mcp_instance: Instância do MCP (opcional)
        app_instance: Instância da aplicação Dash (opcional)

    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    # Obter instância do MCP
    mcp = mcp_instance

    # Se não foi fornecida uma instância do MCP, tentar obter da instância da aplicação
    if mcp is None and app_instance is not None:
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            mcp = app_instance.mcp

    # Verificar se o MCP está disponível
    if mcp is None:
        log.error("Não foi possível obter uma instância do MCP para inicialização")
        return False

    try:
        # Carregar dados padrão
        default_data = load_default_transformer_data()

        if not default_data:
            log.warning("Não foi possível carregar dados padrão para inicialização do MCP")
            return False

        # Definir dados no MCP
        mcp.set_data("transformer-inputs-store", default_data)
        log.info("MCP inicializado com dados padrão")

        return True
    except Exception as e:
        log.error(f"Erro ao inicializar MCP com dados padrão: {e}", exc_info=True)
        return False


def initialize_app(app_instance) -> bool:
    """
    Inicializa a aplicação, configurando o MCP e outros componentes.

    Args:
        app_instance: Instância da aplicação Dash

    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    if app_instance is None:
        log.error("Não foi possível inicializar a aplicação: instância não fornecida")
        return False

    try:
        # Inicializar MCP
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            seed_success = seed_mcp(app_instance=app_instance)
            if seed_success:
                log.info("Aplicação inicializada com sucesso")
                return True
            else:
                log.warning("Aplicação inicializada, mas sem dados padrão no MCP")
                return False
        else:
            log.error("Não foi possível inicializar a aplicação: MCP não disponível")
            return False
    except Exception as e:
        log.error(f"Erro ao inicializar a aplicação: {e}", exc_info=True)
        return False
