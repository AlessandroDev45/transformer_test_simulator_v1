# layouts/transformer_inputs.py
""" Defines the layout for the Transformer Inputs (Dados Básicos) section. """
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging
# Importar estilos diretamente de utils.styles
from utils.styles import COLORS, TYPOGRAPHY, COMPONENTS, SPACING
# Importar componente de botão de ajuda
from components.help_button import create_help_button

log = logging.getLogger(__name__)

# Use standardized styles
LABEL_STYLE = {**TYPOGRAPHY['label'], "textAlign": "left", "whiteSpace": "nowrap", "marginBottom": "0.1rem", "display": "inline-block", "width": "100%"}
INPUT_STYLE = {**COMPONENTS['input'], "height": "28px", "fontSize": "0.7rem"} # Ensure consistent height and font
DROPDOWN_STYLE = {**COMPONENTS['dropdown'], "height": "28px", "minHeight": "28px", "fontSize": "0.7rem", "width": "100%", "display": "inline-block"}
READ_ONLY_STYLE = {**COMPONENTS['read_only'], "height": "28px", "fontSize": "0.7rem"}
SECTION_TITLE_STYLE = {**TYPOGRAPHY['section_title'], "marginTop": "0.5rem"} # Added top margin
SUBSECTION_TITLE_STYLE = {
    "backgroundColor": COLORS['secondary'],
    "color": COLORS['text_light'],
    "fontSize": "0.7rem",
    "padding": "2px 5px",
    "borderRadius": "2px",
    "textAlign": "center",
    "marginBottom": "0.4rem", # Increased margin slightly
    "marginTop": "0.4rem", # Added top margin
    "fontWeight": "bold",
}

def create_transformer_inputs_layout():
    """Creates the layout component for the Transformer Inputs section."""
    log.info("Criando layout Dados Básicos (v3 - Reintegrated)...")

    transformer_inputs_layout = html.Div([
        # Stores (references)
        dcc.Store(id='transformer-inputs-store', storage_type='local'),
        dcc.Store(id='losses-store', storage_type='local'),
        dcc.Store(id='impulse-store', storage_type='local'),
        dcc.Store(id='dieletric-analysis-store', storage_type='local'),
        dcc.Store(id='applied-voltage-store', storage_type='local'),
        dcc.Store(id='induced-voltage-store', storage_type='local'),
        dcc.Store(id='short-circuit-store', storage_type='local'),
        dcc.Store(id='temperature-rise-store', storage_type='local'),
        dcc.Store(id="front-resistor-data", storage_type="memory"),
        dcc.Store(id="tail-resistor-data", storage_type="memory"),
        dcc.Store(id="calculated-inductance", storage_type="memory"),
        dcc.Store(id="simulation-status", storage_type="memory"),

        # --- Especificações Gerais (Incluindo Pesos) ---
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("ESPECIFICAÇÕES GERAIS E PESOS", className="text-center m-0 d-inline-block"),
                    # Botão de ajuda
                    create_help_button("dados_basicos", "Ajuda sobre Dados Básicos do Transformador")
                ], className="d-flex align-items-center justify-content-center"),
                style=COMPONENTS['card_header']
            ),
            dbc.CardBody([
                dbc.Row([
                    # Primeira Linha: Potência, Frequência, Grupo, Líquido, Elev. Óleo
                    dbc.Col([
                        dbc.Label("Potência (MVA):", style=LABEL_STYLE, html_for='potencia_mva'),
                        dbc.Input(type="number", id="potencia_mva", placeholder="MVA", style=INPUT_STYLE, step=0.1, max=9999.9, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    dbc.Col([
                        dbc.Label("Frequência (Hz):", style=LABEL_STYLE, html_for='frequencia'),
                        dbc.Input(type="number", id="frequencia", placeholder="Hz", style=INPUT_STYLE, value=60, persistence=True, persistence_type='local'),
                    ], width=1, className="px-1"), # Reduzido
                    dbc.Col([
                        dbc.Label("Grupo Ligação:", style=LABEL_STYLE, html_for='grupo_ligacao'),
                        dbc.Input(type="text", id="grupo_ligacao", placeholder="Ex: Dyn1", style=INPUT_STYLE, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    dbc.Col([
                        dbc.Label("Líq. Isolante:", style=LABEL_STYLE, html_for='liquido_isolante'),
                        dbc.Input(type="text", id="liquido_isolante", value="Mineral", style=INPUT_STYLE, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                     dbc.Col([
                        dbc.Label("Elev. Óleo (°C/K):", style=LABEL_STYLE, html_for='elevacao_oleo_topo'),
                        dbc.Input(type="number", id="elevacao_oleo_topo", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                     dbc.Col([
                        dbc.Label("Tipo Trafo:", style=LABEL_STYLE, html_for='tipo_transformador'),
                        dcc.Dropdown(
                            id='tipo_transformador', options=[{'label': 'Trifásico', 'value': 'Trifásico'}, {'label': 'Monofásico', 'value': 'Monofásico'}],
                            value='Monofásico', # <<< MUDADO PARA MONOFÁSICO PARA TESTAR SE O LAYOUT ORIGINAL ERA TRIFÁSICO
                            clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type='local', className="dash-dropdown-dark"
                        ),
                    ], width=3, className="px-1"), # Aumentado
                ], className="g-2 mb-2 align-items-end"), # Added gutter g-2 and margin mb-2

                dbc.Row([
                     # Segunda Linha: Tipo Isolamento, Pesos, Botão Limpar
                    dbc.Col([
                        dbc.Label("Tipo Isolamento:", style=LABEL_STYLE, html_for='tipo_isolamento'),
                        dcc.Dropdown(
                            id='tipo_isolamento', options=[{'label': 'Uniforme', 'value': 'uniforme'}, {'label': 'Progressivo', 'value': 'progressivo'}],
                            value='uniforme', clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type='local', className="dash-dropdown-dark"
                        ),
                    ], width=2, className="px-1"),
                    # Pesos
                    dbc.Col([
                        dbc.Label("Peso Total (ton):", style=LABEL_STYLE, html_for='peso_total'),
                        dbc.Input(type="number", id="peso_total", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    dbc.Col([
                        dbc.Label("Peso P.Ativa (ton):", style=LABEL_STYLE, html_for='peso_parte_ativa'),
                        dbc.Input(type="number", id="peso_parte_ativa", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    dbc.Col([
                        dbc.Label("Peso Óleo (ton):", style=LABEL_STYLE, html_for='peso_oleo'),
                        dbc.Input(type="number", id="peso_oleo", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    dbc.Col([
                        dbc.Label("Peso Tanque (ton):", style=LABEL_STYLE, html_for='peso_tanque_acessorios'),
                        dbc.Input(type="number", id="peso_tanque_acessorios", style=INPUT_STYLE, step=0.1, max=999.9, persistence=True, persistence_type='local'),
                    ], width=2, className="px-1"),
                    # Botão Limpar
                    dbc.Col([
                         dbc.Button("Limpar", id="limpar-transformer-inputs", className="w-100", title="Limpar Campos Gerais e Pesos",
                                  style={**COMPONENTS['button_secondary'], "backgroundColor": COLORS['warning'], "color": COLORS['text_dark'],
                                         "padding": "0.2rem 0.3rem", "fontSize": "0.7rem", "height": "28px"})
                    ], width=2, className="ps-1 d-flex align-items-end") # Alinha botão na base
                ], className="g-2"),
            ], style={**COMPONENTS['card_body'], 'padding': '0.75rem'}) # Aumentado padding do body
        ], style={**COMPONENTS['card'], 'marginBottom': '0.75rem'}),

        # --- Parâmetros dos Enrolamentos ---
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H5("PARÂMETROS DOS ENROLAMENTOS E NÍVEIS DE ISOLAMENTO", className="text-center m-0 d-inline-block"),
                    # Botão de ajuda
                    create_help_button("transformer_inputs", "Ajuda sobre Parâmetros dos Enrolamentos")
                ], className="d-flex align-items-center justify-content-center"),
                style=COMPONENTS['card_header']
            ),
            dbc.CardBody([
                dbc.Row([
                    # --- Coluna Alta Tensão ---
                    dbc.Col([
                        html.Div("Alta Tensão (AT)", className="mb-2", style=SECTION_TITLE_STYLE),
                        # --- AT Nominal ---
                        # html.Div("AT Nominal", className="mb-1 mt-2", style=SUBSECTION_TITLE_STYLE), # Subtítulo Nominal Removido
                        dbc.Row([
                            dbc.Col(dbc.Label("Tensão (kV):", style=LABEL_STYLE, html_for='tensao_at'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_at", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Classe (kV):", style=LABEL_STYLE, html_for='classe_tensao_at'), width=6),
                            dbc.Col(dbc.Input(type="number", id="classe_tensao_at", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Elev. Enrol. (°C):", style=LABEL_STYLE, html_for='elevacao_enrol_at'), width=6),
                            dbc.Col(dbc.Input(type="number", id="elevacao_enrol_at", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Corrente (A):", style=LABEL_STYLE, html_for='corrente_nominal_at'), width=6),
                            dbc.Col(dbc.Input(type="number", id="corrente_nominal_at", disabled=True, style=READ_ONLY_STYLE, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Z (%):", style=LABEL_STYLE, html_for='impedancia'), width=6),
                            dbc.Col(dbc.Input(type="number", id="impedancia", style=INPUT_STYLE, step=0.01, max=99.99, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        #html.Hr(style={"margin": "0.4rem 0"}), # Divisor movido para após NBI/SIL
                        dbc.Row([
                            dbc.Col(dbc.Label("NBI (kV):", style=LABEL_STYLE, html_for='nbi_at'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_at', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row(id="sil_at_col", children=[
                            dbc.Col(dbc.Label("SIL (kV):", style=LABEL_STYLE, html_for='sil_at'), width=6),
                            dbc.Col(dcc.Dropdown(id='sil_at', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6)
                        ], className="g-1 mb-2", style={'display': 'none', 'alignItems': 'center'}), # Estilo controlado por callback

                         # --- Inputs de Conexão/Neutro AT ---
                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES da seção de Conexão/Neutro
                        dbc.Row(id='conexao_at_col', children=[ # Linha visível por padrão
                            dbc.Col(dbc.Label("Conexão:", style=LABEL_STYLE, html_for='conexao_at'), width=6),
                            dbc.Col(dcc.Dropdown(
                                id='conexao_at',
                                options=[{'label': 'Yn', 'value': 'estrela'},{'label': 'Y', 'value': 'estrela_sem_neutro'},{'label': 'D', 'value': 'triangulo'}],
                                value='triangulo', # <<< VALOR PADRÃO ATUALIZADO
                                clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type='local', className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row(id='tensao_bucha_neutro_at_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("Classe Neutro (kV):", style=LABEL_STYLE, html_for='tensao_bucha_neutro_at'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_bucha_neutro_at", style=INPUT_STYLE, persistence=True, persistence_type='local', step=0.1, max=999.9), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                        dbc.Row(id='nbi_neutro_at_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("NBI Neutro (kV):", style=LABEL_STYLE, html_for='nbi_neutro_at'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_neutro_at', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                         # --- Fim Conexão/Neutro AT ---

                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES dos Taps
                        html.Div("Taps AT", className="mb-1 mt-2", style=SUBSECTION_TITLE_STYLE),
                        dbc.Row([
                            dbc.Col(dbc.Label("Tap+ kV:", style=LABEL_STYLE, html_for='tensao_at_tap_maior'), width=3),
                            dbc.Col(dbc.Input(type="number", id="tensao_at_tap_maior", style=INPUT_STYLE, step=0.1, max=9999.9, persistence=True, persistence_type='local'), width=3),
                            dbc.Col(dbc.Label("Tap- kV:", style=LABEL_STYLE, html_for='tensao_at_tap_menor'), width=3),
                            dbc.Col(dbc.Input(type="number", id="tensao_at_tap_menor", style=INPUT_STYLE, step=0.1, max=9999.9, persistence=True, persistence_type='local'), width=3),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Tap+ A:", style=LABEL_STYLE, html_for='corrente_nominal_at_tap_maior'), width=3),
                            dbc.Col(dbc.Input(type="number", id="corrente_nominal_at_tap_maior", disabled=True, style=READ_ONLY_STYLE, persistence=True, persistence_type='local'), width=3),
                            dbc.Col(dbc.Label("Tap- A:", style=LABEL_STYLE, html_for='corrente_nominal_at_tap_menor'), width=3),
                            dbc.Col(dbc.Input(type="number", id="corrente_nominal_at_tap_menor", disabled=True, style=READ_ONLY_STYLE, persistence=True, persistence_type='local'), width=3),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Tap+ Z%:", style=LABEL_STYLE, html_for='impedancia_tap_maior'), width=3),
                            dbc.Col(dbc.Input(type="number", id="impedancia_tap_maior", style=INPUT_STYLE, step=0.01, max=99.99, persistence=True, persistence_type='local'), width=3),
                            dbc.Col(dbc.Label("Tap- Z%:", style=LABEL_STYLE, html_for='impedancia_tap_menor'), width=3),
                            dbc.Col(dbc.Input(type="number", id="impedancia_tap_menor", style=INPUT_STYLE, step=0.01, max=99.99, persistence=True, persistence_type='local'), width=3),
                        ], className="g-1 mb-2"),

                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES das Tensões de Ensaio
                        html.Div("Tensões Ensaio AT", className="mb-1 mt-2", style=SUBSECTION_TITLE_STYLE),
                        dbc.Row([
                             dbc.Col(dbc.Label("Aplicada (kV):", style=LABEL_STYLE, html_for='teste_tensao_aplicada_at'), width=6),
                             dbc.Col(dcc.Dropdown(id='teste_tensao_aplicada_at', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                             dbc.Col(dbc.Label("Induzida (kV):", style=LABEL_STYLE, html_for='teste_tensao_induzida'), width=6),
                             dbc.Col(dcc.Dropdown(id='teste_tensao_induzida', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                    ], md=4, className="pe-1", style={"borderRight": f"1px solid {COLORS['border']}"}), # Fim Coluna AT

                    # --- Coluna Baixa Tensão ---
                    dbc.Col([
                         html.Div("Baixa Tensão (BT)", className="mb-2", style=SECTION_TITLE_STYLE),
                        dbc.Row([
                            dbc.Col(dbc.Label("Tensão (kV):", style=LABEL_STYLE, html_for='tensao_bt'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_bt", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Classe (kV):", style=LABEL_STYLE, html_for='classe_tensao_bt'), width=6),
                            dbc.Col(dbc.Input(type="number", id="classe_tensao_bt", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Elev. Enrol. (°C):", style=LABEL_STYLE, html_for='elevacao_enrol_bt'), width=6),
                            dbc.Col(dbc.Input(type="number", id="elevacao_enrol_bt", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Corrente (A):", style=LABEL_STYLE, html_for='corrente_nominal_bt'), width=6),
                            dbc.Col(dbc.Input(type="number", id="corrente_nominal_bt", disabled=True, style=READ_ONLY_STYLE, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         #html.Hr(style={"margin": "0.4rem 0"}), # Divisor movido para após NBI/SIL
                        dbc.Row([
                            dbc.Col(dbc.Label("NBI (kV):", style=LABEL_STYLE, html_for='nbi_bt'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_bt', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row(id="sil_bt_col", children=[
                            dbc.Col(dbc.Label("SIL (kV):", style=LABEL_STYLE, html_for='sil_bt'), width=6),
                            dbc.Col(dcc.Dropdown(id='sil_bt', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6)
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback

                        # --- Inputs de Conexão/Neutro BT ---
                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES da seção de Conexão/Neutro
                        dbc.Row(id='conexao_bt_col', children=[ # Linha visível por padrão
                            dbc.Col(dbc.Label("Conexão:", style=LABEL_STYLE, html_for='conexao_bt'), width=6),
                            dbc.Col(dcc.Dropdown(
                                id='conexao_bt',
                                options=[{'label': 'Yn', 'value': 'estrela'},{'label': 'Y', 'value': 'estrela_sem_neutro'},{'label': 'D', 'value': 'triangulo'}],
                                value='triangulo', # <<< VALOR PADRÃO ATUALIZADO
                                clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type='local', className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row(id='tensao_bucha_neutro_bt_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("Classe Neutro (kV):", style=LABEL_STYLE, html_for='tensao_bucha_neutro_bt'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_bucha_neutro_bt", style=INPUT_STYLE, persistence=True, persistence_type='local', step=0.1, max=999.9), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                         dbc.Row(id='nbi_neutro_bt_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("NBI Neutro (kV):", style=LABEL_STYLE, html_for='nbi_neutro_bt'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_neutro_bt', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                        # --- Fim Conexão/Neutro BT ---

                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES das Tensões de Ensaio
                        html.Div("Tensões Ensaio BT", className="mb-1 mt-2", style=SUBSECTION_TITLE_STYLE),
                         dbc.Row([
                             dbc.Col(dbc.Label("Aplicada (kV):", style=LABEL_STYLE, html_for='teste_tensao_aplicada_bt'), width=6),
                             dbc.Col(dcc.Dropdown(id='teste_tensao_aplicada_bt', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                    ], md=4, className="px-1", style={"borderRight": f"1px solid {COLORS['border']}"}), # Fim Coluna BT

                    # --- Coluna Terciário ---
                    dbc.Col([
                         html.Div("Terciário", className="mb-2", style=SECTION_TITLE_STYLE),
                         dbc.Row([
                            dbc.Col(dbc.Label("Tensão (kV):", style=LABEL_STYLE, html_for='tensao_terciario'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_terciario", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Classe (kV):", style=LABEL_STYLE, html_for='classe_tensao_terciario'), width=6),
                            dbc.Col(dbc.Input(type="number", id="classe_tensao_terciario", style=INPUT_STYLE, step=0.1, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row([
                            dbc.Col(dbc.Label("Elev. Enrol. (°C):", style=LABEL_STYLE, html_for='elevacao_enrol_terciario'), width=6),
                            dbc.Col(dbc.Input(type="number", id="elevacao_enrol_terciario", style=INPUT_STYLE, step=1, max=999, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row([
                            dbc.Col(dbc.Label("Corrente (A):", style=LABEL_STYLE, html_for='corrente_nominal_terciario'), width=6),
                            dbc.Col(dbc.Input(type="number", id="corrente_nominal_terciario", disabled=True, style=READ_ONLY_STYLE, persistence=True, persistence_type='local'), width=6),
                        ], className="g-1 mb-2"),
                        #html.Hr(style={"margin": "0.4rem 0"}), # Divisor movido para após NBI/SIL
                        dbc.Row([
                            dbc.Col(dbc.Label("NBI (kV):", style=LABEL_STYLE, html_for='nbi_terciario'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_terciario', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                        dbc.Row(id="sil_terciario_col", children=[
                            dbc.Col(dbc.Label("SIL (kV):", style=LABEL_STYLE, html_for='sil_terciario'), width=6),
                            dbc.Col(dcc.Dropdown(id='sil_terciario', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6)
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback

                        # --- Inputs de Conexão/Neutro Terciário ---
                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES da seção de Conexão/Neutro
                        dbc.Row(id='conexao_terciario_col', children=[ # Linha visível por padrão
                            dbc.Col(dbc.Label("Conexão:", style=LABEL_STYLE, html_for='conexao_terciario'), width=6),
                            dbc.Col(dcc.Dropdown(
                                id='conexao_terciario',
                                options=[{'label': ' ', 'value': ' '},{'label': 'Yn', 'value': 'estrela'},{'label': 'Y', 'value': 'estrela_sem_neutro'},{'label': 'D', 'value': 'triangulo'}],
                                value=' ', # <<< VALOR PADRÃO MANTIDO (' ')
                                clearable=False, style=DROPDOWN_STYLE, persistence=True, persistence_type='local', className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                         dbc.Row(id='tensao_bucha_neutro_terciario_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("Classe Neutro (kV):", style=LABEL_STYLE, html_for='tensao_bucha_neutro_terciario'), width=6),
                            dbc.Col(dbc.Input(type="number", id="tensao_bucha_neutro_terciario", style=INPUT_STYLE, persistence=True, persistence_type='local', step=0.1, max=999.9), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                         dbc.Row(id='nbi_neutro_terciario_col', children=[ # Linha escondida por padrão
                            dbc.Col(dbc.Label("NBI Neutro (kV):", style=LABEL_STYLE, html_for='nbi_neutro_terciario'), width=6),
                            dbc.Col(dcc.Dropdown(id='nbi_neutro_terciario', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2", style={'display': 'none'}), # Estilo controlado por callback
                         # --- Fim Conexão/Neutro Terciário ---

                        html.Hr(style={"margin": "0.4rem 0"}), # Divisor ANTES das Tensões de Ensaio
                        html.Div("Tensões Ensaio Terciário", className="mb-1 mt-2", style=SUBSECTION_TITLE_STYLE),
                         dbc.Row([
                             dbc.Col(dbc.Label("Aplicada (kV):", style=LABEL_STYLE, html_for='teste_tensao_aplicada_terciario'), width=6),
                             dbc.Col(dcc.Dropdown(id='teste_tensao_aplicada_terciario', options=[], style=DROPDOWN_STYLE, persistence=False, className="dash-dropdown-dark"), width=6),
                        ], className="g-1 mb-2"),
                    ], md=4, className="ps-1"), # Fim Coluna Terciário
                ], className="g-0"), # Fim da Row dos Enrolamentos
            ], style={**COMPONENTS['card_body'], 'padding':'0.5rem'}) # Padding ajustado
        ], style={**COMPONENTS['card'], 'marginBottom': '0.75rem'}),

    ], style={"padding": "0.25rem"}) # End of main Div

    return dbc.Container(
        transformer_inputs_layout,
        fluid=True,
        style=COMPONENTS['container']
    )