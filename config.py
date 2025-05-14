# config.py
import logging
import math
import os

import dash_bootstrap_components as dbc

# --- File Paths ---
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TABLES_DIR = os.path.join(ASSETS_DIR, "tables")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
PATH_NBR_DATA = os.path.join(TABLES_DIR, "tabelas__ABNT_NBR_5356_3.xlsx")
PATH_IEEE_DATA = os.path.join(TABLES_DIR, "IEEE Std C57.12.00-2000_v1.xlsx")
PATH_IEC_60060_1_DATA = os.path.join(TABLES_DIR, "IEC 60060_1.xlsx")
USAGE_COUNT_FILE = os.path.join(BASE_DIR, "usage_count.txt")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# --- Application Settings ---
APP_TITLE = "Simulador de Testes de Transformadores (IEC/IEEE/ABNT) EPS 1500"
DEBUG_MODE = True  # Mantenha True para desenvolvimento
HOST = "127.0.0.1"
PORT = 8050
DEFAULT_THEME_NAME = "DARKLY"  # Mudado para um tema escuro do dbc
DEFAULT_THEME_URL = getattr(dbc.themes, DEFAULT_THEME_NAME, dbc.themes.DARKLY)

# --- Usage Limit ---
USAGE_LIMIT = 1000

# --- PDF Generation Settings ---
PDF_AUTHOR = "Simulador de Testes"
PDF_CREATOR = "Transformer Test Simulation Tool"

# --- Default Values ---
DEFAULT_FREQUENCY = 60.0

# --- Logging Configuration ---
LOGGING_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- Importação Centralizada de Estilos ---
# Importar diretamente do módulo centralizado
try:
    from utils.styles import COLORS, COMPONENTS, MESSAGE_STYLES, SPACING, TABLE_STYLES, TYPOGRAPHY

    # Manter aliases para compatibilidade, mas apontando para os dicionários corretos
    colors = COLORS  # Alias ainda útil
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

except ImportError as e:
    logging.error(f"Erro ao importar estilos de utils.styles em config.py: {e}")
    # Definir fallbacks básicos para evitar que a aplicação quebre completamente
    COLORS = {}
    TYPOGRAPHY = {}
    COMPONENTS = {
        "card": {},
        "card_header": {},
        "card_body": {},
        "input": {},
        "dropdown": {},
        "read_only": {},
    }
    SPACING = {"row_margin": "", "row_gutter": "", "col_padding": ""}
    TABLE_STYLES = {
        "header_sm": {},
        "header_md": {},
        "param_sm": {},
        "param_md": {},
        "value_sm": {},
        "value_md": {},
        "status": {},
        "wrapper": {},
    }
    MESSAGE_STYLES = {"placeholder": {}, "error": {}}
    # Recriar os aliases com fallbacks
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
    LABEL_STYLE = TYPOGRAPHY.get("label", {})
    INPUT_STYLE = COMPONENTS["input"]
    DROPDOWN_STYLE = COMPONENTS["dropdown"]
    READ_ONLY_STYLE = COMPONENTS["read_only"]
    SECTION_TITLE_STYLE = TYPOGRAPHY.get("section_title", {})
    CARD_HEADER_STYLE = COMPONENTS["card_header"]

# --- Constantes Físicas (movidas para utils/styles) ---
try:
    from utils.styles import EPSILON_0, MU_0, PI
except ImportError:
    PI = math.pi
    EPSILON_0 = 8.854187817e-12
    MU_0 = 4 * PI * 1e-7
