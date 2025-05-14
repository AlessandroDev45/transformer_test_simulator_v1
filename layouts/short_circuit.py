# layouts/short_circuit.py
"""
Defines the layout for the Short-Circuit Withstand section as a function.
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.express as px # For the initial empty graph

# Import reusable components and constants
from components.ui_elements import create_labeled_input
from components.transformer_info_template import create_transformer_info_panel
from components.help_button import create_help_button
from utils import constants # For category options

# Importações para obter dados do transformador
from app import app # Para acessar o cache da aplicação
import logging
log = logging.getLogger(__name__)

# Importar estilos padronizados
from layouts import COLORS, TYPOGRAPHY, COMPONENTS, SPACING
from config import colors  # Importar cores para estilos de status

# Initial Empty Graph (created within the function now)
def create_empty_sc_figure():
    """ Creates an empty placeholder figure for the impedance variation graph. """
    fig = px.bar(title="Variação da Impedância (%)")
    fig.update_layout(
        template="plotly_white",
        yaxis_title="ΔZ (%)",
        xaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=f"rgba({int(COLORS['background_card'][1:3], 16)},{int(COLORS['background_card'][3:5], 16)},{int(COLORS['background_card'][5:7], 16)},0.5)",
        font={"size": 10, "color": COLORS['text_light']},
        xaxis={"gridcolor": COLORS['border']},
        yaxis={"gridcolor": COLORS['border']},
        margin=dict(t=30, b=10, l=10, r=10),
        title_font_size=12,
        font_size=10
    )
    return fig

# --- Layout Definition Function ---
def create_short_circuit_layout():
    """Creates the layout component for the Short-Circuit section.

    Esta função cria o layout da seção de Curto-Circuito e inclui
    o painel de informações do transformador diretamente no layout, obtendo
    os dados do cache da aplicação.

    Returns:
        dash.html.Div: O layout completo da seção de Curto-Circuito
    """

    # Tenta obter os dados do transformador do cache da aplicação ou do MCP
    transformer_data = {}
    try:
        # Primeiro tenta obter do MCP (fonte mais confiável)
        if hasattr(app, 'mcp') and app.mcp is not None:
            transformer_data = app.mcp.get_data('transformer-inputs-store')
            log.info(f"[Short Circuit] Dados do transformador obtidos do MCP: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}")
        # Se não conseguir do MCP, tenta do cache
        elif hasattr(app, 'transformer_data_cache') and app.transformer_data_cache:
            transformer_data = app.transformer_data_cache
            log.info(f"[Short Circuit] Dados do transformador obtidos do cache: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}")
        else:
            log.warning("[Short Circuit] Dados do transformador não encontrados no MCP nem no cache")
    except Exception as e:
        log.error(f"[Short Circuit] Erro ao obter dados do transformador: {e}")

    return dbc.Container([
        # Removemos a redefinição dos stores para evitar conflitos com os stores globais
        # Os stores já estão definidos em components/global_stores.py e incluídos no layout principal

        # Primeira seção - Informações do Transformador (sempre visível no topo)
        dbc.Row([
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            id="transformer-info-short-circuit-page", className="mb-1"
                        ),  # Painel visível que será atualizado pelo callback local
                        html.Div(
                            html.Div(),
                            id="transformer-info-short-circuit",
                            style={"display": "none"},
                        ),  # Painel oculto atualizado pelo callback global
                        html.Div(
                            html.Div(),
                            id="transformer-info-losses",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-impulse",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-dieletric",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-applied",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-induced",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-temperature-rise",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-comprehensive",
                            style={"display": "none"},
                        ),  # Compatibility
                    ],
                    className="mb-2",
                ),
                width=12,
            )
        ], className=SPACING['row_margin']),

        # Título principal do módulo
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H6("ANÁLISE DE CURTO-CIRCUITO", className="text-center m-0 d-inline-block", style=TYPOGRAPHY['card_header']),
                    # Botão de ajuda
                    create_help_button("short_circuit", "Ajuda sobre Curto-Circuito")
                ], className="d-flex align-items-center justify-content-center"),
                style=COMPONENTS['card_header']
            ),
            dbc.CardBody([

        # Layout principal com duas colunas
        dbc.Row([
            # --- Coluna Esquerda: Dados de Entrada e Resultados ---
            dbc.Col([
                # Card para Dados de Entrada
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Dados de Entrada do Ensaio", className="m-0", style=TYPOGRAPHY['card_header']),
                        style=COMPONENTS['card_header']
                    ),
                    dbc.CardBody([
                        # Alerta informativo
                        dbc.Alert([
                            html.P("Cálculos e verificações baseados na NBR 5356-5 / IEC 60076-5.",
                                  className="mb-0", style={"fontSize": "0.7rem"})
                        ], color="info", className="p-2 mb-3"),

                        # Seção de Impedâncias
                        html.Div("Impedâncias Medidas (%)",
                                style={"fontSize": "0.8rem", "fontWeight": "bold", "marginBottom": "0.5rem", "color": COLORS['text_light']}),
                        dbc.Row([
                            dbc.Col([
                                create_labeled_input(
                                    "Pré-Ensaio (Z_antes):", "impedance-before", placeholder="Z% antes",
                                    label_width=6, input_width=6, persistence=True, persistence_type='local', step=0.01
                                ),
                            ], width=6),
                            dbc.Col([
                                create_labeled_input(
                                    "Pós-Ensaio (Z_depois):", "impedance-after", placeholder="Z% depois",
                                    label_width=6, input_width=6, persistence=True, persistence_type='local', step=0.01
                                ),
                            ], width=6),
                        ], className="mb-3"),

                        # Seção de Parâmetros Adicionais
                        html.Div("Parâmetros Adicionais",
                                style={"fontSize": "0.8rem", "fontWeight": "bold", "marginBottom": "0.5rem", "color": COLORS['text_light']}),
                        dbc.Row([
                            # Fator de Pico
                            dbc.Col([
                                create_labeled_input(
                                    "Fator Pico (k√2):", "peak-factor", placeholder="Ex: 2.55", value=2.55,
                                    label_width=6, input_width=6, persistence=True, persistence_type='local', step=0.01
                                ),
                            ], width=6),

                            # Lado de Cálculo
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Lado Cálculo Isc:", style=TYPOGRAPHY['label'], html_for='isc-side'),
                                    ], width=6),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id='isc-side',
                                            options=[
                                                {'label': 'AT', 'value': 'AT'},
                                                {'label': 'BT', 'value': 'BT'},
                                                {'label': 'Terciário', 'value': 'TERCIARIO'}
                                            ],
                                            value='AT', # Default
                                            clearable=False,
                                            style=COMPONENTS['dropdown'],
                                            className="dash-dropdown-dark",
                                            persistence=True, persistence_type='local'
                                        ),
                                    ], width=6),
                                ]),
                            ], width=6),
                        ], className="mb-3"),

                        # Categoria de Potência
                        dbc.Row([
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Categoria (Potência):", style=TYPOGRAPHY['label'], html_for='power-category'),
                                    ], width=6),
                                    dbc.Col([
                                        dcc.Dropdown(
                                            id='power-category',
                                            options=constants.POWER_CATEGORY_OPTIONS, # From utils.constants
                                            placeholder="Selecione...",
                                            style=COMPONENTS['dropdown'],
                                            className="dash-dropdown-dark",
                                            persistence=True, persistence_type='local'
                                        ),
                                    ], width=6),
                                ]),
                            ], width=6),

                            # Botão de Cálculo
                            dbc.Col([
                                dbc.Button("Calcular / Verificar", id="calc-short-circuit-btn", color="primary",
                                          size="md", className="w-100 mt-1", style=TYPOGRAPHY['button']),
                            ], width=6, className="d-flex align-items-center"),
                        ], className="mb-2"),

                        # Mensagem de erro
                        html.Div(id='short-circuit-error-message', className="mt-2", style=TYPOGRAPHY['error_text'])
                    ], style=COMPONENTS['card_body'])
                ], style=COMPONENTS['card'], className="mb-3"),

                # Card para Resultados
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Resultados do Cálculo", className="m-0", style=TYPOGRAPHY['card_header']),
                        style=COMPONENTS['card_header']
                    ),
                    dbc.CardBody([
                        dbc.Row([
                            # Coluna de resultados numéricos
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col(html.Label("Isc Simétrica (kA):", style=TYPOGRAPHY['label']), width=6),
                                    dbc.Col(dbc.Input(id="isc-sym-result", type="number", readonly=True, style=COMPONENTS['read_only'], persistence=True, persistence_type='local'), width=6)
                                ], className="mb-2 align-items-center"),
                                dbc.Row([
                                    dbc.Col(html.Label("Ip Pico (kA):", style=TYPOGRAPHY['label']), width=6),
                                    dbc.Col(dbc.Input(id="isc-peak-result", type="number", readonly=True, style=COMPONENTS['read_only'], persistence=True, persistence_type='local'), width=6)
                                ], className="mb-2 align-items-center"),
                                dbc.Row([
                                    dbc.Col(html.Label("Variação ΔZ (%):", style=TYPOGRAPHY['label']), width=6),
                                    dbc.Col(dbc.Input(id="delta-impedance-result", type="text", readonly=True, style=COMPONENTS['read_only'], persistence=True, persistence_type='local'), width=6)
                                ], className="mb-2 align-items-center"),
                            ], width=12),

                            # Status de verificação (destacado)
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col(html.Label("Status Verificação:", style=TYPOGRAPHY['label']), width=6),
                                    dbc.Col(html.Div(id="impedance-check-status", children="-",
                                                    style={"paddingTop": "2px", "fontSize": "0.75rem"}), width=6)
                                ], className="mb-2 align-items-center"),
                            ], width=12),

                            # Notas explicativas
                            dbc.Col([
                                dbc.Alert([
                                    html.P([
                                        html.Strong("Nota 1:"), " Cálculos de Isc e ip são simplificados.", html.Br(),
                                        html.Strong("Nota 2:"), " Limites de ΔZ% conforme NBR 5356-5 Tabela 2."
                                    ], style=TYPOGRAPHY['small_text'], className="mb-0")
                                ], color="light", className="py-1 px-2 mt-1", style={"borderColor": "#e9ecef", "borderRadius":"4px", "marginBottom": "0"})
                            ], width=12),
                        ]),

                        # Hidden notes div for compatibility
                        html.Div(id='short-circuit-notes', style={"display": "none"})
                    ], style=COMPONENTS['card_body'])
                ], style=COMPONENTS['card'])
            ], md=5, className=SPACING['col_padding']),

            # --- Coluna Direita: Gráfico de Variação de Impedância (mais espaço) ---
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Variação da Impedância", className="m-0", style=TYPOGRAPHY['card_header']),
                        style=COMPONENTS['card_header']
                    ),
                    dbc.CardBody([
                        # Descrição do gráfico
                        html.P([
                            "O gráfico abaixo mostra a variação percentual da impedância (ΔZ) medida antes e após o ensaio, ",
                            "comparada com os limites estabelecidos pela norma NBR 5356-5 / IEC 60076-5 para a categoria selecionada."
                        ], style={"fontSize": "0.75rem", "color": COLORS['text_light'], "marginBottom": "0.5rem"}),

                        # Gráfico com altura aumentada
                        dcc.Loading(
                            html.Div(
                                dcc.Graph(id='impedance-variation-graph', figure=create_empty_sc_figure(),
                                         config={'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToRemove': ['select2d', 'lasso2d']},
                                         style={"height": "400px"}) # Altura aumentada para melhor visualização
                            )
                        ),

                        # Legenda explicativa
                        html.Div([
                            html.Span("■ ", style={"color": colors.get('primary', 'royalblue'), "fontSize": "1rem"}),
                            html.Span("Variação Medida (ΔZ)", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                            html.Span(" | ", style={"margin": "0 0.5rem", "color": COLORS['text_light']}),
                            html.Span("■ ", style={"color": colors.get('fail', 'firebrick'), "fontSize": "1rem"}),
                            html.Span("Limites Normativos", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                        ], className="mt-2 text-center")
                    ], style=COMPONENTS['card_body'])
                ], style=COMPONENTS['card'], className="h-100")
            ], md=7, className=SPACING['col_padding']),
        ], className=SPACING['row_gutter'])
            ]), # Fechamento do CardBody
        ]), # Fechamento do Card

    ], fluid=True, className="p-0", style={"backgroundColor": COLORS['background_main']})
