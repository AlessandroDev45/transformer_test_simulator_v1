# layouts/induced_voltage.py
"""
Defines the layout for the Induced Voltage section as a function.
"""
# Importações para obter dados do transformador
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

from components.help_button import create_help_button

# Import reusable components
from components.ui_elements import create_labeled_input

log = logging.getLogger(__name__)

# Importar estilos padronizados
from layouts import COLORS, COMPONENTS, SPACING, TYPOGRAPHY


# --- Layout Definition Function ---
def create_induced_voltage_layout():
    """Creates the layout component for the Induced Voltage section.

    Returns:
        dash.html.Div: O layout completo da seção de Tensão Induzida
    """
    print("--- Executando create_induced_voltage_layout ---")

    # Não obter dados do cache aqui
    transformer_data = {}
    log.info("[Induced Voltage] Usando dados vazios inicialmente, serão preenchidos via callback")
    return dbc.Container(
        [
            # <<< REMOVIDOS dcc.Store definidos aqui >>>
            # Stores ('induced-voltage-store', 'transformer-inputs-store', etc.)
            # JÁ ESTÃO definidos em components/global_stores.py e incluídos no layout principal
            # Primeira seção - Informações do Transformador (Container a ser preenchido)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    # Div onde o painel será renderizado - usando ID único para evitar conflitos
                                    html.Div(id="transformer-info-induced-page", className="mb-2"),
                                    # Div oculta para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-induced",
                                        style={"display": "none"},
                                    ),
                                    # Adicionado para compatibilidade com o callback global_updates
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
                                        id="transformer-info-short-circuit",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-temperature-rise",
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-comprehensive",
                                        style={"display": "none"},
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className=SPACING["row_margin"],
            ),
            # Título principal do módulo (como antes)
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H6(
                                    "ANÁLISE DE TENSÃO INDUZIDA",
                                    className="text-center m-0 d-inline-block",
                                    style=TYPOGRAPHY["card_header"],
                                ),
                                create_help_button(
                                    "induced_voltage", "Ajuda sobre Tensão Induzida"
                                ),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=COMPONENTS["card_header"],
                    ),
                    dbc.CardBody(
                        [
                            # Parâmetros de Entrada em uma única linha (como antes)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.H6(
                                                            "Parâmetros de Entrada do Ensaio Tensão Induzida",
                                                            className="m-0",
                                                            style=TYPOGRAPHY["card_header"],
                                                        ),
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Alert(
                                                                                "Cálculos baseados na NBR 5356-3 / IEC 60076-3 e estimativas com tabelas de aço M4.",
                                                                                color="info",
                                                                                className="small py-2 px-3 mb-0 h-75",
                                                                                style={
                                                                                    **TYPOGRAPHY[
                                                                                        "small_text"
                                                                                    ],
                                                                                    "display": "flex",
                                                                                    "alignItems": "center",
                                                                                },
                                                                            )
                                                                        ],
                                                                        md=2,
                                                                        className="d-flex align-items-center",
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Tipo:",
                                                                                style={
                                                                                    **TYPOGRAPHY[
                                                                                        "label"
                                                                                    ],
                                                                                    "textAlign": "left",
                                                                                    "marginBottom": "0",
                                                                                    "whiteSpace": "nowrap",
                                                                                },
                                                                                html_for="tipo-transformador",
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="tipo-transformador",
                                                                                options=[
                                                                                    {
                                                                                        "label": "Monofásico",
                                                                                        "value": "Monofásico",
                                                                                    },
                                                                                    {
                                                                                        "label": "Trifásico",
                                                                                        "value": "Trifásico",
                                                                                    },
                                                                                ],
                                                                                value="Trifásico",
                                                                                clearable=False,
                                                                                style={
                                                                                    **COMPONENTS[
                                                                                        "dropdown"
                                                                                    ],
                                                                                    "height": "26px",
                                                                                    "minHeight": "26px",
                                                                                    "width": "120px",
                                                                                },
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                                className="dark-dropdown",
                                                                            ),
                                                                        ],
                                                                        md=2,
                                                                        className="d-flex align-items-center",
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Teste (fp):",
                                                                                "frequencia-teste",
                                                                                placeholder="Ex: 120",
                                                                                value=120,
                                                                                label_width=5,
                                                                                input_width=7,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                                style=COMPONENTS[
                                                                                    "input"
                                                                                ],
                                                                            )
                                                                        ],
                                                                        md=2,
                                                                        className="d-flex align-items-center",
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            create_labeled_input(
                                                                                "Cap. AT-GND (pF):",
                                                                                "capacitancia",
                                                                                placeholder="Cp AT-GND",
                                                                                min=0,
                                                                                step=1,
                                                                                label_width=6,
                                                                                input_width=6,
                                                                                persistence=True,
                                                                                persistence_type="local",
                                                                                style=COMPONENTS[
                                                                                    "input"
                                                                                ],
                                                                            )
                                                                        ],
                                                                        md=3,
                                                                        className="d-flex align-items-center",
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Calcular",
                                                                                id="calc-induced-voltage-btn",
                                                                                color="primary",
                                                                                size="sm",
                                                                                className="w-100 h-75",
                                                                                style=TYPOGRAPHY[
                                                                                    "button"
                                                                                ],
                                                                            )
                                                                        ],
                                                                        md=3,
                                                                        className="d-flex align-items-center",
                                                                    ),
                                                                ],
                                                                className="g-2 align-items-center justify-content-between",
                                                            ),
                                                            html.Div(
                                                                id="induced-voltage-error-message",
                                                                className="mt-2",
                                                                style=TYPOGRAPHY["error_text"],
                                                            ),
                                                        ],
                                                        style={
                                                            **COMPONENTS["card_body"],
                                                            "padding": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                            )
                                        ],
                                        width=12,
                                        className=SPACING["col_padding"],
                                    )
                                ],
                                className=SPACING["row_gutter"],
                            ),
                            # Resultados (como antes)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
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
                                                            html.Div(
                                                                id="resultado-tensao-induzida"
                                                            ),
                                                            type="circle",
                                                            color=COLORS["primary"],
                                                        ),
                                                        style={
                                                            **COMPONENTS["card_body"],
                                                            "padding": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                            )
                                        ],
                                        width=12,
                                        className=SPACING["col_padding"],
                                    )
                                ],
                                className=SPACING["row_gutter"],
                            ),
                            # Botões para tabela de frequências (como antes)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "Gerar Tabela de Frequências (100-240Hz)",
                                                        id="generate-frequency-table-button",
                                                        color="info",
                                                        size="sm",
                                                        className="mt-3 mb-2",
                                                        style={
                                                            **TYPOGRAPHY["button"],
                                                            "width": "auto",
                                                        },
                                                    ),
                                                    dbc.Button(
                                                        "Limpar Tabela",
                                                        id="clear-frequency-table-button",
                                                        color="secondary",
                                                        size="sm",
                                                        className="mt-3 mb-2",
                                                        style={
                                                            **TYPOGRAPHY["button"],
                                                            "width": "auto",
                                                        },
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        className="d-flex justify-content-center",
                                    )
                                ],
                                className=SPACING["row_gutter"],
                            ),
                            # Contêiner para a tabela de frequências (como antes)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [html.Div(id="frequency-table-container")],
                                        width=12,
                                        className=SPACING["col_padding"],
                                    )
                                ],
                                className=SPACING["row_gutter"],
                            ),
                        ]
                    ),
                ]
            ),
        ],
        fluid=True,
        className="p-0",
        style={"backgroundColor": COLORS["background_main"]},
    )
