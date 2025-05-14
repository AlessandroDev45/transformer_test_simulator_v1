# layouts/applied_voltage.py
"""
Define o layout para a seção de Tensão Aplicada.
"""
# Importações para obter dados do transformador
# <<< REMOVIDO import direto de 'app' - Obter dados via callback >>>
# from app import app
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

from components.help_button import create_help_button

# Importar componentes reutilizáveis

log = logging.getLogger(__name__)

# Importar estilos padronizados
from layouts import COLORS, COMPONENTS, TYPOGRAPHY


def create_input_row(label, id, placeholder, input_type="number"):
    """Função auxiliar para criar linhas de input com estilo consistente"""
    # Importar estilos padronizados

    # Definir estilos locais para evitar duplicação
    label_style = {
        "fontSize": "0.7rem",
        "marginBottom": "0",
        "fontWeight": "bold",
        "color": COLORS["text_light"],
    }

    input_style = {"fontSize": "0.7rem", "height": "22px", "padding": "0 0.3rem"}

    return dbc.Row(
        [
            dbc.Col(
                dbc.Label(
                    label,
                    style=label_style,
                ),
                width=7,
                className="text-end",
            ),
            dbc.Col(
                dbc.Input(
                    type=input_type,
                    id=id,
                    placeholder=placeholder,
                    persistence=True,
                    persistence_type="local",
                    style=input_style,
                ),
                width=5,
            ),
        ],
        className="g-1 mb-1",
    )


# --- Layout ---
def create_applied_voltage_layout():
    """Creates the layout component for the Applied Voltage section.

    Esta função cria o layout da seção de Tensão Aplicada.
    O painel de informações do transformador será preenchido via callback.

    Returns:
        dash.html.Div: O layout completo da seção de Tensão Aplicada
    """
    log.info("[Applied Voltage Layout] Creating layout...")  # Log criação layout

    # Não obter dados do cache aqui, será feito por callback
    transformer_data = {}

    return dbc.Container(
        [
            # <<< REMOVIDOS dcc.Store definidos aqui >>>
            # dcc.Store(id='applied-voltage-store', storage_type='local'),
            # dcc.Store(id='transformer-inputs-store', storage_type='local'), # Exemplo de store global
            # Primeira seção - Informações do Transformador (Container que será preenchido via callback)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    # Div onde o painel será renderizado - usando ID único para evitar conflitos
                                    html.Div(id="transformer-info-applied-page", className="mb-1"),
                                    # Div oculta para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-applied",
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
                className="mb-1",
            ),
            # Título principal do módulo
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H6(
                                    "ANÁLISE DE TENSÃO APLICADA",
                                    className="text-center m-0 d-inline-block",
                                    style=TYPOGRAPHY["card_header"],
                                ),
                                create_help_button(
                                    "applied_voltage", "Ajuda sobre Tensão Aplicada"
                                ),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=COMPONENTS["card_header"],
                    ),
                    dbc.CardBody(
                        [
                            # Linha principal para dividir Entradas e Sistema Ressonante
                            dbc.Row(
                                [
                                    # --- Coluna Esquerda: Entradas (1/4 da largura) ---
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.Span(
                                                            "Parâmetros de Entrada",
                                                            className="p-1 fw-bold fs-6",
                                                        ),
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            html.Div(
                                                                "Capacitâncias",
                                                                className="text-center mb-1",
                                                                style=TYPOGRAPHY["section_title"],
                                                            ),
                                                            create_input_row(
                                                                "Capacitância AT - GND (pF):",
                                                                "cap-at",
                                                                "Cap. AT",
                                                            ),
                                                            create_input_row(
                                                                "Capacitância BT - GND (pF):",
                                                                "cap-bt",
                                                                "Cap. BT",
                                                            ),
                                                            create_input_row(
                                                                "Capacitância Ter. - GND (pF):",
                                                                "cap-ter",
                                                                "Cap. Terciário",
                                                            ),
                                                            html.Div(
                                                                "Tensões de Ensaio",
                                                                className="text-center my-1",
                                                                style=TYPOGRAPHY["section_title"],
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Label(
                                                                            "Tensão de ensaio AT (kV):",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "marginBottom": "0",
                                                                                "fontWeight": "bold",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=7,
                                                                        className="text-end",
                                                                    ),
                                                                    dbc.Col(
                                                                        html.Div(
                                                                            id="tensao-at-display",
                                                                            children="-",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "padding": "0.2rem 0",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=5,
                                                                    ),
                                                                ],
                                                                className="g-1 mb-1",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Label(
                                                                            "Tensão de ensaio BT (kV):",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "marginBottom": "0",
                                                                                "fontWeight": "bold",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=7,
                                                                        className="text-end",
                                                                    ),
                                                                    dbc.Col(
                                                                        html.Div(
                                                                            id="tensao-bt-display",
                                                                            children="-",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "padding": "0.2rem 0",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=5,
                                                                    ),
                                                                ],
                                                                className="g-1 mb-1",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Label(
                                                                            "Tensão de ensaio Ter. (kV):",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "marginBottom": "0",
                                                                                "fontWeight": "bold",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=7,
                                                                        className="text-end",
                                                                    ),
                                                                    dbc.Col(
                                                                        html.Div(
                                                                            id="tensao-terciario-display",
                                                                            children="-",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "padding": "0.2rem 0",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=5,
                                                                    ),
                                                                ],
                                                                className="g-1 mb-1",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Label(
                                                                            "Frequência de ensaio (Hz):",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "marginBottom": "0",
                                                                                "fontWeight": "bold",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=7,
                                                                        className="text-end",
                                                                    ),
                                                                    dbc.Col(
                                                                        html.Div(
                                                                            id="frequencia-display",
                                                                            children="60 Hz",
                                                                            style={
                                                                                "fontSize": "0.7rem",
                                                                                "padding": "0.2rem 0",
                                                                                "color": COLORS[
                                                                                    "text_light"
                                                                                ],
                                                                            },
                                                                        ),
                                                                        width=5,
                                                                    ),
                                                                ],
                                                                className="g-1 mb-1",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Calcular",
                                                                                id="calc-applied-voltage-btn",
                                                                                color="primary",
                                                                                size="sm",
                                                                                className="w-100 mt-3",
                                                                                style=TYPOGRAPHY[
                                                                                    "button"
                                                                                ],
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                    )
                                                                ],
                                                                className="g-2 justify-content-center",
                                                            ),
                                                            html.Div(
                                                                id="applied-voltage-error-message",
                                                                className="mt-2",
                                                                style=TYPOGRAPHY["error_text"],
                                                            ),
                                                        ],
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                                className="h-100",
                                            )
                                        ],
                                        width=3,
                                        className="pe-1",
                                    ),
                                    # --- Coluna Direita: Sistema Ressonante (3/4 da largura) ---
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        " Sistema Ressonante High Volt WRM 1800/1350-900-450",  # Texto ajustado
                                                        className="p-1 text-center fw-bold fs-6",
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            # Tabela de Configurações (como antes)
                                                                            html.Div(
                                                                                "Configurações disponíveis:",
                                                                                style={
                                                                                    "fontSize": "0.7rem",
                                                                                    "fontWeight": "bold",
                                                                                    "marginBottom": "0.3rem",
                                                                                    "color": COLORS[
                                                                                        "text_light"
                                                                                    ],
                                                                                },
                                                                            ),
                                                                            html.P(
                                                                                [
                                                                                    "Nota: Para Módulos 1||2||3 (3 Par.), a tensão máxima varia conforme a capacitância: ",
                                                                                    "270 kV para 2,0-39,3 nF e 450 kV para 2,0-23,6 nF.",
                                                                                ],
                                                                                style={
                                                                                    "fontSize": "0.6rem",
                                                                                    "marginBottom": "0.3rem",
                                                                                    "color": COLORS[
                                                                                        "text_light"
                                                                                    ],
                                                                                    "fontStyle": "italic",
                                                                                },
                                                                            ),
                                                                            dbc.Table(
                                                                                [
                                                                                    html.Thead(
                                                                                        [
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Th(
                                                                                                        "Configuração",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "backgroundColor": COLORS[
                                                                                                                "background_card_header"
                                                                                                            ],
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Th(
                                                                                                        "Tensão Máx (kV)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "backgroundColor": COLORS[
                                                                                                                "background_card_header"
                                                                                                            ],
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Th(
                                                                                                        "Capacitância (nF)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "backgroundColor": COLORS[
                                                                                                                "background_card_header"
                                                                                                            ],
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Th(
                                                                                                        "Corrente (A)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "backgroundColor": COLORS[
                                                                                                                "background_card_header"
                                                                                                            ],
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Th(
                                                                                                        "Potência (kVA)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "backgroundColor": COLORS[
                                                                                                                "background_card_header"
                                                                                                            ],
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            )
                                                                                        ]
                                                                                    ),
                                                                                    html.Tbody(
                                                                                        [
                                                                                            # Linhas da tabela (como antes)
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Td(
                                                                                                        "Módulos 1+2+3 (Série)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1350",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "0,22 - 2,6",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1,33",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1800",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Td(
                                                                                                        "Módulos 1+2 (Série)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "900",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "0,3 - 6,5",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1,33",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1200",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Td(
                                                                                                        "Módulo 1 (1 em Par.)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "450",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "0,7 - 13,1",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1,33",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "600",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Td(
                                                                                                        "Módulos 1||2||3 (3 Par.)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "450",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "2,0 - 23,6",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "4,0",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1800",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#3D3D3D",
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                            html.Tr(
                                                                                                [
                                                                                                    html.Td(
                                                                                                        "Módulos 1||2||3 (3 Par.)",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "270",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "2.0 - 39,3",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "4,0",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                    html.Td(
                                                                                                        "1800",
                                                                                                        style={
                                                                                                            "fontSize": "0.7rem",
                                                                                                            "padding": "0.2rem",
                                                                                                            "color": COLORS[
                                                                                                                "text_light"
                                                                                                            ],
                                                                                                            "backgroundColor": "#4F4F4F",
                                                                                                        },
                                                                                                    ),
                                                                                                ]
                                                                                            ),
                                                                                        ]
                                                                                    ),
                                                                                ],
                                                                                bordered=True,
                                                                                hover=True,
                                                                                size="sm",
                                                                                className="mb-3",
                                                                                style={
                                                                                    "backgroundColor": "#3D3D3D"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            html.Div(
                                                                                "Recomendação do Sistema:",
                                                                                style={
                                                                                    "fontSize": "0.7rem",
                                                                                    "fontWeight": "bold",
                                                                                    "marginBottom": "0.3rem",
                                                                                    "color": COLORS[
                                                                                        "text_light"
                                                                                    ],
                                                                                    "textAlign": "center",
                                                                                },
                                                                            ),
                                                                            html.Div(
                                                                                id="resonant-system-recommendation",
                                                                                style={
                                                                                    "fontSize": "0.7rem",
                                                                                    "color": COLORS[
                                                                                        "text_light"
                                                                                    ],
                                                                                },
                                                                            ),
                                                                        ],
                                                                        width=12,
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                                className="h-100",
                                            )
                                        ],
                                        width=9,
                                        className="ps-1",
                                    ),
                                ],
                                className="mb-2",
                            ),
                            # Linha para Resultados
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        "Resultados",
                                                        className="p-1 text-center fw-bold fs-6",
                                                        style=COMPONENTS["card_header"],
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            dbc.Spinner(
                                                                html.Div(
                                                                    id="applied-voltage-results",
                                                                    style={
                                                                        "fontSize": "0.7rem",
                                                                        "color": COLORS[
                                                                            "text_light"
                                                                        ],
                                                                    },
                                                                )
                                                            )
                                                        ],
                                                        style=COMPONENTS["card_body"],
                                                    ),
                                                ],
                                                style=COMPONENTS["card"],
                                            )
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            # Componente oculto para tipo de transformador (se necessário para outros callbacks)
                            html.Div(
                                dcc.Input(
                                    id="tipo_transformador",
                                    type="hidden",
                                    value=transformer_data.get("tipo_transformador", "Trifásico"),
                                ),
                                style={"display": "none"},
                            ),
                        ]
                    ),  # Fechamento do CardBody Principal
                ]
            ),  # Fechamento do Card Principal
        ],
        fluid=True,
        style=COMPONENTS["container"],
    )
