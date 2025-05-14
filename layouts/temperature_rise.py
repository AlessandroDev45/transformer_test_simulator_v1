# layouts/temperature_rise.py
"""
Defines the layout for the Temperature Rise section as a function.
"""
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

from app import app  # Importa a instância app para acessar o cache de dados do transformador
from components.help_button import create_help_button

# Import reusable components and constants
from components.ui_elements import create_labeled_input
from utils import constants  # For material options

log = logging.getLogger(__name__)

# Importar estilos padronizados
from layouts import COLORS, COMPONENTS, SPACING, TYPOGRAPHY


# --- Layout Definition Function ---
def create_temperature_rise_layout():
    """Creates the layout component for the Temperature Rise section."""

    # Tenta obter os dados do transformador do cache da aplicação ou do MCP
    transformer_data = {}
    try:
        # Primeiro tenta obter do MCP (fonte mais confiável)
        if hasattr(app, "mcp") and app.mcp is not None:
            transformer_data = app.mcp.get_data("transformer-inputs-store")
            log.info(
                f"[Temperature Rise] Dados do transformador obtidos do MCP: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}"
            )
        # Se não conseguir do MCP, tenta do cache
        elif hasattr(app, "transformer_data_cache") and app.transformer_data_cache:
            transformer_data = app.transformer_data_cache
            log.info(
                f"[Temperature Rise] Dados do transformador obtidos do cache: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}"
            )
        else:
            log.warning(
                "[Temperature Rise] Dados do transformador não encontrados no MCP nem no cache"
            )
    except Exception as e:
        log.error(f"[Temperature Rise] Erro ao obter dados do transformador: {e}")

    return dbc.Container(
        [
            # Removemos a redefinição dos stores para evitar conflitos com os stores globais
            # Os stores já estão definidos em components/global_stores.py e incluídos no layout principal
            # Primeira seção - Informações do Transformador (sempre visível no topo)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Componente de informações do transformador
                            html.Div(
                                [
                                    # Div onde o painel será renderizado - usando ID único para evitar conflitos
                                    html.Div(
                                        id="transformer-info-temperature-rise-page",
                                        className="mb-1",
                                    ),
                                    # Div oculta para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-temperature-rise",
                                        style={"display": "none"},
                                    ),
                                    # Divs ocultos para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-losses",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-impulse",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-dieletric",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-applied",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-induced",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-short-circuit",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-comprehensive",
                                        style={"display": "none"},
                                    ),
                                ],
                                className="mb-2",
                            )
                        ],
                        width=12,
                    )
                ],
                className=SPACING["row_margin"],
            ),
            # Título principal do módulo
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H6(
                                    "ANÁLISE DE ELEVAÇÃO DE TEMPERATURA",
                                    className="text-center m-0 d-inline-block",
                                    style=TYPOGRAPHY["card_header"],
                                ),
                                # Botão de ajuda
                                create_help_button(
                                    "temperature_rise", "Ajuda sobre Elevação de Temperatura"
                                ),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=COMPONENTS["card_header"],
                    ),
                    dbc.CardBody(
                        [
                            # Layout principal com duas colunas
                            dbc.Row(
                                [
                                    # --- Coluna Esquerda: Entradas e Diagrama ---
                                    dbc.Col(
                                        [
                                            # Card para Dados de Entrada
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.H6(
                                                            "Dados de Entrada do Ensaio",
                                                            className="m-0",
                                                            style=TYPOGRAPHY["card_header"],
                                                        ),
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            # Alerta informativo
                                                            dbc.Alert(
                                                                [
                                                                    html.P(
                                                                        "Cálculos baseados na NBR 5356-2 / IEC 60076-2.",
                                                                        className="mb-0",
                                                                        style={
                                                                            "fontSize": "0.7rem"
                                                                        },
                                                                    )
                                                                ],
                                                                color="info",
                                                                className="p-2 mb-3",
                                                            ),
                                                            # Seção 1: Condições Ambientais e Material
                                                            html.Div(
                                                                "Condições Ambientais e Material",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "fontWeight": "bold",
                                                                    "marginBottom": "0.5rem",
                                                                    "color": COLORS["text_light"],
                                                                },
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    # Temperatura Ambiente
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Temp. Ambiente (Θa) (°C):",
                                                                                "temp-amb",
                                                                                placeholder="Ex: 25.0",
                                                                                label_width=7,
                                                                                input_width=5,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    # Material do Enrolamento
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Row(
                                                                                [
                                                                                    dbc.Col(
                                                                                        [
                                                                                            dbc.Label(
                                                                                                "Material Enrolamento:",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                                html_for="winding-material",
                                                                                            ),
                                                                                        ],
                                                                                        width=7,
                                                                                    ),
                                                                                    dbc.Col(
                                                                                        [
                                                                                            dcc.Dropdown(
                                                                                                id="winding-material",
                                                                                                options=constants.MATERIAL_OPTIONS,
                                                                                                value="cobre",
                                                                                                clearable=False,
                                                                                                style=COMPONENTS[
                                                                                                    "dropdown"
                                                                                                ],
                                                                                                className="dash-dropdown-dark",
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                        ],
                                                                                        width=5,
                                                                                    ),
                                                                                ]
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ],
                                                                className="mb-3",
                                                            ),
                                                            # Seção 2: Medições a Frio
                                                            html.Div(
                                                                "Medições a Frio",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "fontWeight": "bold",
                                                                    "marginBottom": "0.5rem",
                                                                    "color": COLORS["text_light"],
                                                                },
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    # Resistência Fria
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Res. Fria (Rc) (Ohm):",
                                                                                "res-cold",
                                                                                placeholder="Ohm @ Θc",
                                                                                label_width=7,
                                                                                input_width=5,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                                step="any",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    # Temperatura de Referência Fria
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Temp. Ref. Fria (Θc) (°C):",
                                                                                "temp-cold",
                                                                                placeholder="Temp. Rc",
                                                                                label_width=7,
                                                                                input_width=5,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ],
                                                                className="mb-3",
                                                            ),
                                                            # Seção 3: Medições a Quente
                                                            html.Div(
                                                                "Medições a Quente",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "fontWeight": "bold",
                                                                    "marginBottom": "0.5rem",
                                                                    "color": COLORS["text_light"],
                                                                },
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    # Resistência Quente
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Res. Quente (Rw) (Ohm):",
                                                                                "res-hot",
                                                                                placeholder="Ohm @ t=0",
                                                                                label_width=7,
                                                                                input_width=5,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                                step="any",
                                                                            ),
                                                                            dbc.Tooltip(
                                                                                "Resistência extrapolada para t=0 após desligamento (conforme NBR 5356-2)",
                                                                                target="res-hot",
                                                                                placement="bottom",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    # Temperatura do Topo do Óleo
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Temp. Topo Óleo (Θoil) (°C):",
                                                                                "temp-top-oil",
                                                                                placeholder="Final",
                                                                                label_width=7,
                                                                                input_width=5,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ],
                                                                className="mb-3",
                                                            ),
                                                            # Seção 4: Parâmetro para Constante de Tempo
                                                            html.Div(
                                                                "Parâmetro para Constante de Tempo Térmica",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "fontWeight": "bold",
                                                                    "marginBottom": "0.5rem",
                                                                    "color": COLORS["text_light"],
                                                                },
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Row(
                                                                                [
                                                                                    dbc.Col(
                                                                                        [
                                                                                            dbc.Label(
                                                                                                "Elevação Máx Óleo (ΔΘoil_max) (K):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                                html_for="delta-theta-oil-max",
                                                                                            ),
                                                                                        ],
                                                                                        width=7,
                                                                                    ),
                                                                                    dbc.Col(
                                                                                        [
                                                                                            dbc.Input(
                                                                                                type="number",
                                                                                                id="delta-theta-oil-max",
                                                                                                style=COMPONENTS[
                                                                                                    "input"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                                placeholder="Opcional p/ τ₀",
                                                                                                step=0.1,
                                                                                            ),
                                                                                        ],
                                                                                        width=5,
                                                                                    ),
                                                                                ]
                                                                            ),
                                                                            dbc.Tooltip(
                                                                                "Elevação final do óleo sobre o ambiente (da 1ª etapa do ensaio). Necessário para calcular τ₀.",
                                                                                target="delta-theta-oil-max",
                                                                                placement="bottom",
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                    ),
                                                                ],
                                                                className="mb-3",
                                                            ),
                                                            # Botão de cálculo
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Button(
                                                                            "Calcular Elevação",
                                                                            id="limpar-temp-rise",
                                                                            color="primary",
                                                                            size="md",
                                                                            className="w-100",
                                                                            style=TYPOGRAPHY[
                                                                                "button"
                                                                            ],
                                                                            n_clicks=0,
                                                                        ),
                                                                        width=12,
                                                                    ),
                                                                ],
                                                                className="mb-2",
                                                            ),
                                                            # Mensagem de erro
                                                            html.Div(
                                                                id="temp-rise-error-message",
                                                                className="mt-2",
                                                                style=TYPOGRAPHY["error_text"],
                                                            ),
                                                        ],
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                                className="mb-3",
                                            ),
                                            # Card para Diagrama Explicativo
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.H6(
                                                            "Diagrama de Elevação de Temperatura",
                                                            className="m-0",
                                                            style=TYPOGRAPHY["card_header"],
                                                        ),
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            # Diagrama explicativo
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-temperature-high fa-4x"
                                                                            ),
                                                                            html.P(
                                                                                "Diagrama de Elevação de Temperatura",
                                                                                className="mt-2",
                                                                            ),
                                                                        ],
                                                                        className="text-center p-4",
                                                                        style={
                                                                            "width": "100%",
                                                                            "maxWidth": "500px",
                                                                            "margin": "0 auto",
                                                                            "display": "block",
                                                                            "color": "#aaa",
                                                                        },
                                                                    )
                                                                ],
                                                                className="text-center",
                                                            )
                                                        ],
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                            ),
                                        ],
                                        md=6,
                                        className=SPACING["col_padding"],
                                    ),
                                    # --- Coluna Direita: Resultados e Fórmulas ---
                                    dbc.Col(
                                        [
                                            # Card para Resultados
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.H6(
                                                            "Resultados Calculados",
                                                            className="m-0",
                                                            style=TYPOGRAPHY["card_header"],
                                                        ),
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        dcc.Loading(
                                                            [
                                                                # Seção 1: Temperaturas e Elevações
                                                                html.Div(
                                                                    "Temperaturas e Elevações",
                                                                    style={
                                                                        "fontSize": "0.8rem",
                                                                        "fontWeight": "bold",
                                                                        "marginBottom": "0.5rem",
                                                                        "color": COLORS[
                                                                            "text_light"
                                                                        ],
                                                                    },
                                                                ),
                                                                dbc.Row(
                                                                    [
                                                                        # Temperatura Média do Enrolamento
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Row(
                                                                                    [
                                                                                        dbc.Col(
                                                                                            html.Label(
                                                                                                "Temp. Média Enrol. Final (Θw):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                            ),
                                                                                            width=7,
                                                                                        ),
                                                                                        dbc.Col(
                                                                                            dbc.Input(
                                                                                                id="avg-winding-temp",
                                                                                                type="number",
                                                                                                readonly=True,
                                                                                                style=COMPONENTS[
                                                                                                    "read_only"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                            width=5,
                                                                                        ),
                                                                                    ],
                                                                                    className="mb-2 align-items-center",
                                                                                ),
                                                                            ],
                                                                            width=12,
                                                                        ),
                                                                        # Elevação Média do Enrolamento
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Row(
                                                                                    [
                                                                                        dbc.Col(
                                                                                            html.Label(
                                                                                                "Elevação Média Enrol. (ΔΘw):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                            ),
                                                                                            width=7,
                                                                                        ),
                                                                                        dbc.Col(
                                                                                            dbc.Input(
                                                                                                id="avg-winding-rise",
                                                                                                type="number",
                                                                                                readonly=True,
                                                                                                style=COMPONENTS[
                                                                                                    "read_only"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                            width=5,
                                                                                        ),
                                                                                    ],
                                                                                    className="mb-2 align-items-center",
                                                                                ),
                                                                            ],
                                                                            width=12,
                                                                        ),
                                                                        # Elevação do Topo do Óleo
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Row(
                                                                                    [
                                                                                        dbc.Col(
                                                                                            html.Label(
                                                                                                "Elevação Topo Óleo (ΔΘoil):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                            ),
                                                                                            width=7,
                                                                                        ),
                                                                                        dbc.Col(
                                                                                            dbc.Input(
                                                                                                id="top-oil-rise",
                                                                                                type="number",
                                                                                                readonly=True,
                                                                                                style=COMPONENTS[
                                                                                                    "read_only"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                            width=5,
                                                                                        ),
                                                                                    ],
                                                                                    className="mb-2 align-items-center",
                                                                                ),
                                                                            ],
                                                                            width=12,
                                                                        ),
                                                                    ]
                                                                ),
                                                                # Seção 2: Parâmetros Térmicos
                                                                html.Div(
                                                                    "Parâmetros Térmicos",
                                                                    style={
                                                                        "fontSize": "0.8rem",
                                                                        "fontWeight": "bold",
                                                                        "marginTop": "1rem",
                                                                        "marginBottom": "0.5rem",
                                                                        "color": COLORS[
                                                                            "text_light"
                                                                        ],
                                                                    },
                                                                ),
                                                                dbc.Row(
                                                                    [
                                                                        # Perdas Totais Usadas
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Row(
                                                                                    [
                                                                                        dbc.Col(
                                                                                            html.Label(
                                                                                                "Perdas Totais Usadas (Ptot):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                            ),
                                                                                            width=7,
                                                                                        ),
                                                                                        dbc.Col(
                                                                                            dbc.Input(
                                                                                                id="ptot-used",
                                                                                                type="number",
                                                                                                readonly=True,
                                                                                                placeholder="kW",
                                                                                                style=COMPONENTS[
                                                                                                    "read_only"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                            width=5,
                                                                                        ),
                                                                                    ],
                                                                                    className="mb-2 align-items-center",
                                                                                ),
                                                                            ],
                                                                            width=12,
                                                                        ),
                                                                        # Constante de Tempo Térmica
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Row(
                                                                                    [
                                                                                        dbc.Col(
                                                                                            html.Label(
                                                                                                "Const. Tempo Térmica (τ₀):",
                                                                                                style=TYPOGRAPHY[
                                                                                                    "label"
                                                                                                ],
                                                                                            ),
                                                                                            width=7,
                                                                                        ),
                                                                                        dbc.Col(
                                                                                            dbc.Input(
                                                                                                id="tau0-result",
                                                                                                type="number",
                                                                                                readonly=True,
                                                                                                placeholder="horas",
                                                                                                style=COMPONENTS[
                                                                                                    "read_only"
                                                                                                ],
                                                                                                persistence=True,
                                                                                                persistence_type="local",
                                                                                            ),
                                                                                            width=5,
                                                                                        ),
                                                                                    ],
                                                                                    className="mb-2 align-items-center",
                                                                                ),
                                                                            ],
                                                                            width=12,
                                                                        ),
                                                                    ]
                                                                ),
                                                                # Seção 3: Fórmulas Utilizadas
                                                                html.Div(
                                                                    "Fórmulas Utilizadas",
                                                                    style={
                                                                        "fontSize": "0.8rem",
                                                                        "fontWeight": "bold",
                                                                        "marginTop": "1rem",
                                                                        "marginBottom": "0.5rem",
                                                                        "color": COLORS[
                                                                            "text_light"
                                                                        ],
                                                                    },
                                                                ),
                                                                dbc.Card(
                                                                    [
                                                                        dbc.CardBody(
                                                                            [
                                                                                html.P(
                                                                                    [
                                                                                        html.Span(
                                                                                            "Temperatura Média do Enrolamento:",
                                                                                            style={
                                                                                                "fontWeight": "bold"
                                                                                            },
                                                                                        ),
                                                                                        html.Br(),
                                                                                        "Θw = Θa + [(Rw/Rc) × (C + Θc) - C]",
                                                                                    ],
                                                                                    style={
                                                                                        "fontSize": "0.7rem",
                                                                                        "marginBottom": "0.5rem",
                                                                                    },
                                                                                ),
                                                                                html.P(
                                                                                    [
                                                                                        html.Span(
                                                                                            "Elevação Média do Enrolamento:",
                                                                                            style={
                                                                                                "fontWeight": "bold"
                                                                                            },
                                                                                        ),
                                                                                        html.Br(),
                                                                                        "ΔΘw = Θw - Θa",
                                                                                    ],
                                                                                    style={
                                                                                        "fontSize": "0.7rem",
                                                                                        "marginBottom": "0.5rem",
                                                                                    },
                                                                                ),
                                                                                html.P(
                                                                                    [
                                                                                        html.Span(
                                                                                            "Elevação do Topo do Óleo:",
                                                                                            style={
                                                                                                "fontWeight": "bold"
                                                                                            },
                                                                                        ),
                                                                                        html.Br(),
                                                                                        "ΔΘoil = Θoil - Θa",
                                                                                    ],
                                                                                    style={
                                                                                        "fontSize": "0.7rem",
                                                                                        "marginBottom": "0.5rem",
                                                                                    },
                                                                                ),
                                                                                html.P(
                                                                                    [
                                                                                        html.Span(
                                                                                            "Constante de Tempo Térmica:",
                                                                                            style={
                                                                                                "fontWeight": "bold"
                                                                                            },
                                                                                        ),
                                                                                        html.Br(),
                                                                                        "τ₀ = 0.132 × (mT - 0.5 × mO) × ΔΘoil_max / Ptot",
                                                                                    ],
                                                                                    style={
                                                                                        "fontSize": "0.7rem",
                                                                                        "marginBottom": "0",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "padding": "0.5rem"
                                                                            },
                                                                        )
                                                                    ],
                                                                    style={
                                                                        "backgroundColor": COLORS[
                                                                            "background_card"
                                                                        ],
                                                                        "border": f"1px solid {COLORS['border']}",
                                                                    },
                                                                ),
                                                                # Notas Explicativas
                                                                html.Hr(className="my-3"),
                                                                dbc.Alert(
                                                                    [
                                                                        html.P(
                                                                            [
                                                                                html.Strong(
                                                                                    "Nota 1:"
                                                                                ),
                                                                                " Cálculos conforme NBR 5356-2. Rw deve ser o valor extrapolado para t=0.",
                                                                                html.Br(),
                                                                                html.Strong(
                                                                                    "Nota 2:"
                                                                                ),
                                                                                " O cálculo de τ₀ requer ΔΘoil_max, Pesos (Dados Básicos) e Perdas Totais (Perdas).",
                                                                                html.Br(),
                                                                                html.Strong(
                                                                                    "Nota 3:"
                                                                                ),
                                                                                " C = 234,5 para cobre e 225 para alumínio.",
                                                                            ],
                                                                            style=TYPOGRAPHY[
                                                                                "small_text"
                                                                            ],
                                                                            className="mb-0",
                                                                        )
                                                                    ],
                                                                    color="light",
                                                                    className="py-1 px-2 mt-1",
                                                                    style={
                                                                        "borderColor": "#e9ecef",
                                                                        "borderRadius": "4px",
                                                                        "marginBottom": "0",
                                                                    },
                                                                ),
                                                            ]
                                                        ),
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                                className="h-100",
                                            )
                                        ],
                                        md=6,
                                        className=SPACING["col_padding"],
                                    ),
                                ],
                                className=SPACING["row_gutter"],
                            ),
                        ]
                    ),  # Fechamento do CardBody
                ]
            ),  # Fechamento do Card
        ],
        fluid=True,
        className="p-0",
        style={"backgroundColor": COLORS["background_main"]},
    )
