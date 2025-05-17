# layouts/transformer_inputs.py
""" Defines the layout for the Transformer Inputs (Dados Básicos) section. """
import logging
import sys
import os
import json # Adicionado para carregar o JSON

# Configurar logging básico para execução standalone
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path quando executado diretamente
if __name__ == "__main__":
    # Adiciona o diretório pai ao path para permitir importações relativas
    sys.path.insert(0, os.path.abspath('..'))

import dash_bootstrap_components as dbc
from dash import dcc, html

# Importar estilos diretamente de utils.styles
try:
    from utils.styles import COLORS, COMPONENTS, SPACING, TYPOGRAPHY
    log.debug("Estilos importados com sucesso de utils.styles")
except ImportError as e:
    # Fallback básico se a importação falhar
    log.error(f"Falha ao importar estilos: {e}. Usando fallbacks.")
    COLORS = {
        "primary": "#007bff",
        "secondary": "#6c757d",
        "info": "#17a2b8",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "light": "#f8f9fa",
        "dark": "#343a40",
        "text_light": "#f8f9fa",
        "text_dark": "#212529",
        "text_muted": "#6c757d",
        "text_header": "#ffffff",
        "background_main": "#282c34",
        "background_card": "#343a40",
        "background_card_header": "#495057",
        "background_input": "#495057",
        "border": "#495057",
        "border_strong": "#adb5bd",
        "accent": "#17a2b8",
    }
    TYPOGRAPHY = {
        "label": {"fontSize": "0.75rem", "fontWeight": "500"},
        "section_title": {
            "fontSize": "0.9rem",
            "fontWeight": "bold",
            "marginTop": "1rem",
            "marginBottom": "0.5rem",
        },
        "card_header": {"fontSize": "1rem", "fontWeight": "bold"},
    }
    COMPONENTS = {
        "card": {},
        "card_header": {},
        "card_body": {},
        "input": {},
        "dropdown": {},
        "read_only": {"backgroundColor": "#e9ecef", "cursor": "default"},
        "button_secondary": {},
        "button_primary": {},
    }
    SPACING = {"row_margin": "mb-3", "row_gutter": "g-3", "col_padding": "px-2"}


# Importar componente de botão de ajuda
try:
    from components.help_button import create_help_button
except ImportError:
    log.warning("Help button component not found.")

    def create_help_button(module_name, tooltip_text):
        return html.Div()  # Fallback


# Estilos locais baseados nos estilos importados/fallback
LABEL_STYLE = {
    **TYPOGRAPHY.get("label", {}),
    "textAlign": "left",
    "whiteSpace": "nowrap",
    "marginBottom": "0.2rem",
    "display": "block", # Alterado para block para que o input fique abaixo
    "width": "100%",
    "color": COLORS.get("text_light", "#f0f0f0"),
    "fontSize": "0.8rem",
}
INPUT_STYLE = {
    **COMPONENTS.get("input", {}),
    "height": "32px",
    "fontSize": "0.8rem",
    "backgroundColor": COLORS.get("background_input", "#444"),
    "color": COLORS.get("text_light", "#f0f0f0"),
    "border": f"1px solid {COLORS.get('border', '#555')}",
    "padding": "0.375rem 0.75rem",
    "width": "100%", # Input ocupa 100% da coluna pai
}
DROPDOWN_STYLE = {
    **COMPONENTS.get("dropdown", {}),
    "height": "32px",
    "minHeight": "32px",
    "fontSize": "0.8rem",
    "width": "100%", # Dropdown ocupa 100% da coluna pai
    "display": "inline-block",
    "backgroundColor": COLORS.get("background_input", "#444"),
    "color": COLORS.get("text_dark", "#212529"), # Ajustar se o tema do dropdown for escuro
    "border": f"1px solid {COLORS.get('border', '#555')}",
}
READ_ONLY_STYLE = {
    **COMPONENTS.get("read_only", {}),
    "height": "32px",
    "fontSize": "0.8rem",
    "backgroundColor": COLORS.get("background_card_header", "#555"),
    "color": COLORS.get("text_muted", "#aaa"),
    "border": f"1px solid {COLORS.get('border', '#555')}",
    "padding": "0.375rem 0.75rem",
    "width": "100%",
}
SECTION_TITLE_STYLE = {
    **TYPOGRAPHY.get("section_title", {}),
    "marginTop": "0.75rem",
    "marginBottom": "0.75rem",
    "color": COLORS.get("text_light", "#f0f0f0"),
    "fontSize": "1rem",
    "fontWeight": "bold",
    "textAlign": "center",
    "backgroundColor": COLORS.get("primary", "#007bff"),
    "padding": "0.3rem",
    "borderRadius": "3px",
}
SUBSECTION_TITLE_STYLE = {
    "backgroundColor": COLORS.get("secondary", "#555"),
    "color": COLORS.get("text_header", "#fff"),
    "fontSize": "0.85rem",
    "padding": "3px 8px",
    "borderRadius": "3px",
    "textAlign": "center",
    "marginBottom": "0.6rem",
    "marginTop": "0.6rem",
    "fontWeight": "bold",
}
BUTTON_STYLE_SECONDARY = {
    **COMPONENTS.get("button_secondary", {}),
    "padding": "0.2rem 0.3rem", # Ajustar se necessário
    "fontSize": "0.75rem", # Ajustar para caber
    "height": "32px", # Mesma altura dos inputs
    "width": "100%", # Botão ocupa 100% da coluna pai
    "lineHeight": "1.5", # Para centralizar texto verticalmente
    "textAlign": "center",
    # Se o botão tiver cor de fundo diferente, ajuste as cores do texto
    # "backgroundColor": COLORS.get("secondary"),
    # "color": COLORS.get("text_header"),
    # "border": f"1px solid {COLORS.get('border_strong')}"
}
CARD_HEADER_STYLE_PRIMARY = {
    **COMPONENTS.get("card_header", {}),
    "backgroundColor": COLORS.get("primary", "#007bff"),
    "padding": "0.75rem",
    "fontSize": "1.1rem",
    "fontWeight": "bold",
}
CARD_BODY_STYLE = {
    **COMPONENTS.get("card_body", {}),
    "padding": "1rem",
    "backgroundColor": COLORS.get("background_card", "#343a40"),
}
CARD_STYLE = {
    **COMPONENTS.get("card", {}),
    "marginBottom": "1rem",
    "border": f"1px solid {COLORS.get('border_strong', '#adb5bd')}",
    "borderRadius": "5px",
    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
}


def create_transformer_inputs_layout():
    """Creates the layout component for the Transformer Inputs section."""
    log.info("Criando layout Dados Básicos (v5 - Layout Geral e Pesos em 2 linhas)...")

    # Carregar dados do JSON para as classes de tensão
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'assets', 'tabela.json'), 'r', encoding='utf-8') as f:
            insulation_data = json.load(f)

        # Extrair valores únicos de um_kv e criar opções para o dropdown
        # Usar um set para garantir valores únicos e depois ordenar
        um_kv_values = sorted(list(set([level['um_kv'] for level in insulation_data.get('insulation_levels', []) if 'um_kv' in level])))
        voltage_class_options = [{'label': str(val), 'value': val} for val in um_kv_values]
        log.info(f"Classes de tensão carregadas para dropdown: {len(voltage_class_options)} opções.")

    except FileNotFoundError:
        log.error("Arquivo assets/tabela.json não encontrado. Usando opções vazias para classes de tensão.")
        voltage_class_options = []
    except json.JSONDecodeError:
        log.error("Erro ao decodificar assets/tabela.json. Usando opções vazias para classes de tensão.")
        voltage_class_options = []
    except Exception as e:
        log.error(f"Erro inesperado ao carregar classes de tensão: {e}. Usando opções vazias.")
        voltage_class_options = []


    transformer_inputs_layout = html.Div(
        [
            # ... (stores globais e divs ocultas permanecem aqui) ...
            html.Div(html.Div(), id="transformer-info-losses", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-impulse", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-dieletric", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-applied", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-induced", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-short-circuit", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-temperature-rise", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-comprehensive", style={"display": "none"}),



            # --- Especificações Gerais e Pesos ---
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H5(
                                    "ESPECIFICAÇÕES GERAIS E PESOS",
                                    className="text-center m-0 d-inline-block",
                                ),
                                create_help_button(
                                    "dados_basicos", "Ajuda sobre Dados Básicos do Transformador"
                                ),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=CARD_HEADER_STYLE_PRIMARY,
                    ),
                    dbc.CardBody(
                        [
                            # LINHA 1: Potência, Frequência, Tipo Trafo, Grupo Ligação, Líq. Isolante, Tipo Isolamento, Norma
                            dbc.Row(
                                [
                                    dbc.Col([
                                        dbc.Label("Potência (MVA):", style=LABEL_STYLE, html_for="potencia_mva"),
                                        dbc.Input(type="number", id="potencia_mva", placeholder="MVA", style=INPUT_STYLE, step=0.1, max=9999.9, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Frequência (Hz):", style=LABEL_STYLE, html_for="frequencia"),
                                        dbc.Input(type="number", id="frequencia", placeholder="Hz", style=INPUT_STYLE, value=60, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Tipo Trafo:", style=LABEL_STYLE, html_for="tipo_transformador"),
                                        dcc.Dropdown(id="tipo_transformador", options=[{"label": "Trifásico", "value": "Trifásico"}, {"label": "Monofásico", "value": "Monofásico"}], value="Trifásico", clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type="local", className="dash-dropdown-dark")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Grupo Ligação:", style=LABEL_STYLE, html_for="grupo_ligacao"),
                                        dbc.Input(type="text", id="grupo_ligacao", placeholder="Ex: Dyn1", style=INPUT_STYLE, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Líq. Isolante:", style=LABEL_STYLE, html_for="liquido_isolante"),
                                        dbc.Input(type="text", id="liquido_isolante", value="Mineral", style=INPUT_STYLE, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Tipo Isolamento:", style=LABEL_STYLE, html_for="tipo_isolamento"),
                                        dcc.Dropdown(id="tipo_isolamento", options=[{"label": "Uniforme", "value": "Uniforme"}, {"label": "Progressivo", "value": "Progressivo"}], value="Uniforme", clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type="local", className="dash-dropdown-dark")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Norma:", style=LABEL_STYLE, html_for="norma_iso"),
                                        dcc.Dropdown(id="norma_iso", options=[{"label": "IEC NBR 5356", "value": "IEC"},{"label": "IEEE C57.12", "value": "IEEE"}], value="IEC", clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type="local", className="dash-dropdown-dark")
                                    ]),
                                ],
                                className="g-2 mb-3", # g-2 para gutter (espaçamento), mb-3 para margem inferior
                            ),
                            # LINHA 2: Elev. Óleo, Elev. Enrol., Peso P.Ativa, Peso Tanque, Peso Óleo, Peso Total, LIMPAR
                            dbc.Row(
                                [
                                    dbc.Col([
                                        dbc.Label("Elev. Óleo (°C/K):", style=LABEL_STYLE, html_for="elevacao_oleo_topo"),
                                        dbc.Input(type="number", id="elevacao_oleo_topo", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Elev. Enrol. (°C):", style=LABEL_STYLE, html_for="elevacao_enrol"),
                                        dbc.Input(type="number", id="elevacao_enrol", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Peso P.Ativa (ton):", style=LABEL_STYLE, html_for="peso_parte_ativa"),
                                        dbc.Input(type="number", id="peso_parte_ativa", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Peso Tanque (ton):", style=LABEL_STYLE, html_for="peso_tanque_acessorios"),
                                        dbc.Input(type="number", id="peso_tanque_acessorios", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Peso Óleo (ton):", style=LABEL_STYLE, html_for="peso_oleo"),
                                        dbc.Input(type="number", id="peso_oleo", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("Peso Total (ton):", style=LABEL_STYLE, html_for="peso_total"),
                                        dbc.Input(type="number", id="peso_total", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type="local")
                                    ]),
                                    dbc.Col([
                                        dbc.Label("\u00A0", style=LABEL_STYLE), # Espaço para alinhar com os labels dos inputs
                                        dbc.Button("LIMPAR", id="limpar-transformer-inputs", title="Limpar Campos Gerais e Pesos", style=BUTTON_STYLE_SECONDARY)
                                    ]),
                                ],
                                className="g-2", # g-2 para gutter (espaçamento)
                            ),
                        ],
                        style=CARD_BODY_STYLE,
                    ),
                ],
                style=CARD_STYLE,
            ),
            # --- Parâmetros dos Enrolamentos ---
            # O restante do layout permanece o mesmo
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H5(
                                    "PARÂMETROS DOS ENROLAMENTOS E NÍVEIS DE ISOLAMENTO",
                                    className="text-center m-0 d-inline-block",
                                ),
                                create_help_button(
                                    "transformer_inputs", "Ajuda sobre Parâmetros dos Enrolamentos"
                                ),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=CARD_HEADER_STYLE_PRIMARY,
                    ),
                    dbc.CardBody(
                        [
                            # Sem espaçamento adicional para compactar o layout
                            dbc.Row(
                                [
                                    # --- Coluna Alta Tensão ---
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "ALTA TENSÃO (AT)",
                                                className="mb-3",
                                                style=SECTION_TITLE_STYLE,
                                            ),
                                            # Tensão e Classe lado a lado
                                            dbc.Row(
                                                [
                                                    # Tensão (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tensão (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_at",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_at",
                                                                style=INPUT_STYLE,
                                                                step=0.1,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Classe (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Classe (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="classe_tensao_at",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="classe_tensao_at",
                                                                options=voltage_class_options,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3", # ALTERADO de g-2 mb-1 para g-3 mb-3
                                            ),
                                            # Corrente e Impedância lado a lado
                                            dbc.Row(
                                                [
                                                    # Corrente
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Corrente (A):",
                                                                style=LABEL_STYLE,
                                                                html_for="corrente_nominal_at",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="corrente_nominal_at",
                                                                disabled=True,
                                                                style=READ_ONLY_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Impedância
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Z (%):",
                                                                style=LABEL_STYLE,
                                                                html_for="impedancia",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="impedancia",
                                                                style=INPUT_STYLE,
                                                                step=0.01,
                                                                max=99.99,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI e SIL lado a lado
                                            dbc.Row(
                                                [
                                                    # NBI
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_at",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                            # Elemento dummy para callback clientside
                                                            html.Div(id="_at_dummy_output", style={"display": "none"}),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # SIL/IM
                                                    dbc.Col(
                                                        id="sil_at_col",
                                                        children=[
                                                            dbc.Label(
                                                                "SIL/IM (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_at",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            # Conexão e Classe Neutro lado a lado
                                            dbc.Row(
                                                [
                                                    # Conexão
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Conexão:",
                                                                style=LABEL_STYLE,
                                                                html_for="conexao_at",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="conexao_at",
                                                                options=[
                                                                    {
                                                                        "label": "Yn",
                                                                        "value": "estrela",
                                                                    },
                                                                    {
                                                                        "label": "Y",
                                                                        "value": "estrela_sem_neutro",
                                                                    },
                                                                    {
                                                                        "label": "D",
                                                                        "value": "triangulo",
                                                                    },
                                                                    {
                                                                        "label": "Zn",
                                                                        "value": "ziguezague",
                                                                    },
                                                                    {
                                                                        "label": "Z",
                                                                        "value": "ziguezague_sem_neutro",
                                                                    },
                                                                ],
                                                                value="estrela",  # Default AT para estrela (Yn)
                                                                clearable=False,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                        id="conexao_at_col",
                                                    ),
                                                    # Classe Neutro (agora visível por padrão)
                                                    dbc.Col(
                                                        id="tensao_bucha_neutro_at_col",
                                                        children=[
                                                            dbc.Label(
                                                                "Classe Neutro (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_bucha_neutro_at",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_bucha_neutro_at",
                                                                style=INPUT_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                step=0.1,
                                                                max=999.9,
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI/BIL Neutro e SIL/IM Neutro lado a lado
                                            dbc.Row(
                                                id="at_neutral_fields_row",
                                                children=[
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_neutro_at",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_neutro_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "SIL/IM Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_neutro_at",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_neutro_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            html.Div(
                                                "TAPS AT",
                                                className="mb-3 mt-3",
                                                style=SUBSECTION_TITLE_STYLE,
                                            ),
                                            # Tensões Tap+ e Tap- lado a lado
                                            dbc.Row(
                                                [
                                                    # Tap+ kV
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap+ kV:",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_at_tap_maior",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_at_tap_maior",
                                                                style=INPUT_STYLE,
                                                                step=0.1,
                                                                max=9999.9,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Tap- kV
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap- kV:",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_at_tap_menor",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_at_tap_menor",
                                                                style=INPUT_STYLE,
                                                                step=0.1,
                                                                max=9999.9,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # Correntes Tap+ e Tap- lado a lado
                                            dbc.Row(
                                                [
                                                    # Tap+ A
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap+ A:",
                                                                style=LABEL_STYLE,
                                                                html_for="corrente_nominal_at_tap_maior",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="corrente_nominal_at_tap_maior",
                                                                disabled=True,
                                                                style=READ_ONLY_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Tap- A
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap- A:",
                                                                style=LABEL_STYLE,
                                                                html_for="corrente_nominal_at_tap_menor",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="corrente_nominal_at_tap_menor",
                                                                disabled=True,
                                                                style=READ_ONLY_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # Impedâncias Tap+ e Tap- lado a lado
                                            dbc.Row(
                                                [
                                                    # Tap+ Z%
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap+ Z%:",
                                                                style=LABEL_STYLE,
                                                                html_for="impedancia_tap_maior",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="impedancia_tap_maior",
                                                                style=INPUT_STYLE,
                                                                step=0.01,
                                                                max=99.99,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Tap- Z%
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tap- Z%:",
                                                                style=LABEL_STYLE,
                                                                html_for="impedancia_tap_menor",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="impedancia_tap_menor",
                                                                style=INPUT_STYLE,
                                                                step=0.01,
                                                                max=99.99,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            html.Div(
                                                "TENSÕES ENSAIO AT",
                                                className="mb-3 mt-3",
                                                style=SUBSECTION_TITLE_STYLE,
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Aplicada (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="teste_tensao_aplicada_at",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="teste_tensao_aplicada_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Induzida (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="teste_tensao_induzida_at",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="teste_tensao_induzida_at",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                        ],
                                        md=4,
                                        className="pe-1",
                                        style={"borderRight": f"1px solid {COLORS['border']}"},
                                    ),
                                    # --- Coluna Baixa Tensão ---
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "BAIXA TENSÃO (BT)",
                                                className="mb-3",
                                                style=SECTION_TITLE_STYLE,
                                            ),
                                            # Tensão e Classe lado a lado
                                            dbc.Row(
                                                [
                                                    # Tensão (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tensão (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_bt",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_bt",
                                                                style=INPUT_STYLE,
                                                                step=0.1,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Classe (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Classe (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="classe_tensao_bt",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="classe_tensao_bt",
                                                                options=voltage_class_options,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # Corrente
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Corrente (A):",
                                                                style=LABEL_STYLE,
                                                                html_for="corrente_nominal_bt",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="corrente_nominal_bt",
                                                                disabled=True,
                                                                style=READ_ONLY_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6, # Ajustado
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI e SIL lado a lado
                                            dbc.Row(
                                                [
                                                    # NBI
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_bt",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_bt",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                            # Elemento dummy para callback clientside
                                                            html.Div(id="_bt_dummy_output", style={"display": "none"}),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # SIL/IM
                                                    dbc.Col(
                                                        id="sil_bt_col",
                                                        children=[
                                                            dbc.Label(
                                                                "SIL/IM (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_bt",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_bt",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            # Conexão e Classe Neutro lado a lado
                                            dbc.Row(
                                                [
                                                    # Conexão
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Conexão:",
                                                                style=LABEL_STYLE,
                                                                html_for="conexao_bt",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="conexao_bt",
                                                                options=[
                                                                    {
                                                                        "label": "Yn",
                                                                        "value": "estrela",
                                                                    },
                                                                    {
                                                                        "label": "Y",
                                                                        "value": "estrela_sem_neutro",
                                                                    },
                                                                    {
                                                                        "label": "D",
                                                                        "value": "triangulo",
                                                                    },
                                                                    {
                                                                        "label": "Zn",
                                                                        "value": "ziguezague",
                                                                    },
                                                                    {
                                                                        "label": "Z",
                                                                        "value": "ziguezague_sem_neutro",
                                                                    },
                                                                ],
                                                                value="triangulo",  # Default BT para triângulo
                                                                clearable=False,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                        id="conexao_bt_col",
                                                    ),
                                                    # Classe Neutro (agora visível por padrão)
                                                    dbc.Col(
                                                        id="tensao_bucha_neutro_bt_col",
                                                        children=[
                                                            dbc.Label(
                                                                "Classe Neutro (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_bucha_neutro_bt",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_bucha_neutro_bt",
                                                                style=INPUT_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                step=0.1,
                                                                max=999.9,
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI/BIL Neutro e SIL/IM Neutro lado a lado
                                            dbc.Row(
                                                id="bt_neutral_fields_row",
                                                children=[
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_neutro_bt",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_neutro_bt",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "SIL/IM Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_neutro_bt",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_neutro_bt",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            html.Div(
                                                "TENSÕES ENSAIO BT",
                                                className="mb-3 mt-3",
                                                style=SUBSECTION_TITLE_STYLE,
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Aplicada (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="teste_tensao_aplicada_bt",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="teste_tensao_aplicada_bt",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                        ],
                                        md=4,
                                        className="px-1",
                                        style={"borderRight": f"1px solid {COLORS['border']}"},
                                    ),
                                    # --- Coluna Terciário ---
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "TERCIÁRIO",
                                                className="mb-3",
                                                style=SECTION_TITLE_STYLE,
                                            ),
                                            # Tensão e Classe lado a lado
                                            dbc.Row(
                                                [
                                                    # Tensão (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Tensão (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_terciario",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_terciario",
                                                                style=INPUT_STYLE,
                                                                step=0.1,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # Classe (kV)
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Classe (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="classe_tensao_terciario",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="classe_tensao_terciario",
                                                                options=voltage_class_options,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # Corrente
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Corrente (A):",
                                                                style=LABEL_STYLE,
                                                                html_for="corrente_nominal_terciario",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="corrente_nominal_terciario",
                                                                disabled=True,
                                                                style=READ_ONLY_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                            ),
                                                        ],
                                                        width=6, # Ajustado
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI e SIL lado a lado
                                            dbc.Row(
                                                [
                                                    # NBI
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_terciario",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_terciario",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                            # Elemento dummy para callback clientside
                                                            html.Div(id="_terciario_dummy_output", style={"display": "none"}),
                                                        ],
                                                        width=6,
                                                    ),
                                                    # SIL/IM
                                                    dbc.Col(
                                                        id="sil_terciario_col",
                                                        children=[
                                                            dbc.Label(
                                                                "SIL/IM (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_terciario",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_terciario",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            # Conexão e Classe Neutro lado a lado
                                            dbc.Row(
                                                [
                                                    # Conexão
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Conexão:",
                                                                style=LABEL_STYLE,
                                                                html_for="conexao_terciario",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="conexao_terciario",
                                                                options=[
                                                                    {
                                                                        "label": "(Nenhum)",
                                                                        "value": " ",
                                                                    },
                                                                    {
                                                                        "label": "Yn",
                                                                        "value": "estrela",
                                                                    },
                                                                    {
                                                                        "label": "Y",
                                                                        "value": "estrela_sem_neutro",
                                                                    },
                                                                    {
                                                                        "label": "D",
                                                                        "value": "triangulo",
                                                                    },
                                                                    {
                                                                        "label": "Zn",
                                                                        "value": "ziguezague",
                                                                    },
                                                                    {
                                                                        "label": "Z",
                                                                        "value": "ziguezague_sem_neutro",
                                                                    },
                                                                ],
                                                                value=" ",  # Default Terciário como vazio
                                                                clearable=False,
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                        id="conexao_terciario_col",
                                                    ),
                                                    # Classe Neutro (agora visível por padrão)
                                                    dbc.Col(
                                                        id="tensao_bucha_neutro_terciario_col",
                                                        children=[
                                                            dbc.Label(
                                                                "Classe Neutro (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="tensao_bucha_neutro_terciario",
                                                            ),
                                                            dbc.Input(
                                                                type="number",
                                                                id="tensao_bucha_neutro_terciario",
                                                                style=INPUT_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                step=0.1,
                                                                max=999.9,
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            # NBI/BIL Neutro e SIL/IM Neutro lado a lado
                                            dbc.Row(
                                                id="terciario_neutral_fields_row",
                                                children=[
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "NBI/BIL Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="nbi_neutro_terciario",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="nbi_neutro_terciario",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "SIL/IM Neutro (kV):", # Label original
                                                                style=LABEL_STYLE,
                                                                html_for="sil_neutro_terciario",
                                                            ),
                                                            dcc.Dropdown( # REVERTIDO PARA DROPDOWN
                                                                id="sil_neutro_terciario",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                            html.Hr(
                                                style={
                                                    "margin": "0.8rem 0",
                                                    "borderTop": f"2px solid {COLORS.get('border_strong', '#adb5bd')}",
                                                }
                                            ),
                                            html.Div(
                                                "TENSÕES ENSAIO TERCIÁRIO",
                                                className="mb-3 mt-3",
                                                style=SUBSECTION_TITLE_STYLE,
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                "Aplicada (kV):",
                                                                style=LABEL_STYLE,
                                                                html_for="teste_tensao_aplicada_terciario",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="teste_tensao_aplicada_terciario",
                                                                options=[],
                                                                style=DROPDOWN_STYLE,
                                                                persistence=True,
                                                                persistence_type="local",
                                                                className="dash-dropdown-dark",
                                                            ),
                                                        ],
                                                        width=6, # Ajustado
                                                    ),
                                                ],
                                                className="g-3 mb-3",
                                            ),
                                        ],
                                        md=4,
                                        className="ps-1",
                                    ),
                                ],
                                className="g-0", # No gutter for the main winding columns row
                            ),
                            html.Div(style={"height": "15px"}),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                id="last-save-ok",
                                                className="text-center text-muted small",
                                                style={"fontSize": "0.8rem"},
                                            ),
                                        ],
                                        width={"size": 6, "offset": 3},
                                    ),
                                ],
                                className="g-2 mb-2",
                            ),
                            dcc.Store(id="dirty-flag", storage_type="memory"),
                            dcc.Interval(id="page-init-trigger", n_intervals=0, max_intervals=1),
                        ],
                        style={**CARD_BODY_STYLE, "padding": "1rem"},
                    ),
                ],
                style={**CARD_STYLE, "marginBottom": "0.75rem"},
            ),
        ],
        style={"padding": "0.25rem"},
    )

    return dbc.Container(
        transformer_inputs_layout, fluid=True, style=COMPONENTS.get("container", {})
    )
