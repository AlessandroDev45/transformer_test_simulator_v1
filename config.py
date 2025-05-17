# config.py
"""
Configurações centralizadas da aplicação.
Este arquivo contém configurações essenciais para a inicialização e funcionamento da aplicação.
"""
import logging
import os
from pathlib import Path

import dash_bootstrap_components as dbc

# -----------------------------------------------------------------------------
# Caminhos de Arquivos
# -----------------------------------------------------------------------------
try:
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    BASE_DIR = Path(os.getcwd())

# Diretórios principais
ASSETS_DIR = BASE_DIR / "assets"
TABLES_DIR = ASSETS_DIR / "tables"
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Arquivos de dados
PATH_NBR_DATA = TABLES_DIR / "tabelas__ABNT_NBR_5356_3.xlsx"
PATH_IEEE_DATA = TABLES_DIR / "IEEE Std C57.12.00-2000_v1.xlsx"
PATH_IEC_60060_1_DATA = TABLES_DIR / "IEC 60060_1.xlsx"
USAGE_COUNT_FILE = BASE_DIR / "usage_count.txt"
LOG_FILE = LOG_DIR / "app.log"

# -----------------------------------------------------------------------------
# Configurações da Aplicação
# -----------------------------------------------------------------------------
APP_TITLE = "Simulador de Testes de Transformadores (IEC/IEEE/ABNT) EPS 1500"
DEBUG_MODE = True  # Mantenha True para desenvolvimento
HOST = "127.0.0.1"
PORT = 8050
USAGE_LIMIT = 1000

# Configurações de tema
DEFAULT_THEME_NAME = "DARKLY"
DEFAULT_THEME_URL = getattr(dbc.themes, DEFAULT_THEME_NAME, dbc.themes.DARKLY)

# Configurações de PDF
PDF_AUTHOR = "Simulador de Testes"
PDF_CREATOR = "Transformer Test Simulation Tool"

# -----------------------------------------------------------------------------
# Configurações de Logging
# -----------------------------------------------------------------------------
LOGGING_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# -----------------------------------------------------------------------------
# Importação de Constantes Físicas
# -----------------------------------------------------------------------------
# Importar de utils/constants.py para centralizar as constantes físicas
from utils.constants import DEFAULT_FREQUENCY, EPSILON_0, MU_0, PI

# -----------------------------------------------------------------------------
# Importação de Estilos
# -----------------------------------------------------------------------------
# Importar estilos centralizados de utils/styles.py
from utils.styles import COLORS, COMPONENTS, MESSAGE_STYLES, SPACING, TABLE_STYLES, TYPOGRAPHY

# Aliases para compatibilidade com código existente
colors = COLORS
TABLE_HEADER_STYLE_SM = TABLE_STYLES["header_sm"]
TABLE_HEADER_STYLE_MD = TABLE_STYLES["header_md"]
TABLE_PARAM_STYLE_SM = TABLE_STYLES["param_sm"]
TABLE_PARAM_STYLE_MD = TABLE_STYLES["param_md"]
TABLE_VALUE_STYLE_SM = TABLE_STYLES["value_sm"]
TABLE_VALUE_STYLE_MD = TABLE_STYLES["value_md"]
TABLE_STATUS_STYLE = TABLE_STYLES["status"]
TABLE_WRAPPER_STYLE = TABLE_STYLES["wrapper"]
PLACEHOLDER_STYLE = MESSAGE_STYLES["placeholder"]
ERROR_STYLE = MESSAGE_STYLES["error"]
LABEL_STYLE = TYPOGRAPHY["label"]
INPUT_STYLE = COMPONENTS["input"]
DROPDOWN_STYLE = COMPONENTS["dropdown"]
READ_ONLY_STYLE = COMPONENTS["read_only"]
SECTION_TITLE_STYLE = TYPOGRAPHY["section_title"]
CARD_HEADER_STYLE = COMPONENTS["card_header"]
