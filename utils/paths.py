"""
Utilitários para manipulação de caminhos de arquivos.
Fornece funções para obter caminhos de forma portável entre sistemas operacionais.
"""
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def get_app_root() -> Path:
    """
    Obtém o diretório raiz da aplicação.

    Returns:
        Path: Caminho para o diretório raiz da aplicação
    """
    # Se estamos em um pacote instalado
    if getattr(sys, "frozen", False):
        # PyInstaller cria um diretório temporário e armazena o caminho em _MEIPASS
        app_root = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    else:
        # Estamos em modo de desenvolvimento
        # Assumimos que este arquivo está em utils/ no diretório raiz
        app_root = Path(__file__).parent.parent

    log.debug(f"App root directory: {app_root}")
    return app_root


def get_assets_dir() -> Path:
    """
    Obtém o diretório de assets da aplicação.

    Returns:
        Path: Caminho para o diretório de assets
    """
    assets_dir = get_app_root() / "assets"
    if not assets_dir.exists():
        log.warning(f"Assets directory not found: {assets_dir}")
    return assets_dir


def get_tables_dir() -> Path:
    """
    Obtém o diretório de tabelas da aplicação.

    Returns:
        Path: Caminho para o diretório de tabelas
    """
    tables_dir = get_assets_dir() / "tables"
    if not tables_dir.exists():
        log.warning(f"Tables directory not found: {tables_dir}")
    return tables_dir


def get_data_dir() -> Path:
    """
    Obtém o diretório de dados da aplicação.

    Returns:
        Path: Caminho para o diretório de dados
    """
    data_dir = get_app_root() / "data"
    if not data_dir.exists():
        log.info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """
    Obtém o diretório de logs da aplicação.

    Returns:
        Path: Caminho para o diretório de logs
    """
    logs_dir = get_app_root() / "logs"
    if not logs_dir.exists():
        log.info(f"Creating logs directory: {logs_dir}")
        logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_table_path(table_name: str, extension: str = "json") -> Path:
    """
    Obtém o caminho para um arquivo de tabela.

    Args:
        table_name: Nome da tabela
        extension: Extensão do arquivo (default: json)

    Returns:
        Path: Caminho para o arquivo de tabela
    """
    table_path = get_tables_dir() / f"{table_name}.{extension}"
    if not table_path.exists():
        log.warning(f"Table file not found: {table_path}")
    return table_path
