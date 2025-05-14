# layouts/losses.py
"""
Defines the layout for the Losses section.
"""
import logging

# import config # Assuming config might be used elsewhere, kept import
# Importações para obter dados do transformador
import dash_bootstrap_components as dbc
from dash import dcc, html

from components.help_button import create_help_button

# Attempt to import shared styles, provide fallbacks
# Importar estilos do módulo centralizado
from utils.styles import COLORS, COMPONENTS, TYPOGRAPHY

log = logging.getLogger(__name__)

# Use standardized styles (use fallbacks defined above if import failed)
SECTION_TITLE_STYLE = TYPOGRAPHY.get("section_title", {})
LABEL_STYLE = TYPOGRAPHY.get("label", {})
INPUT_STYLE = {**COMPONENTS.get("input", {}), "height": "26px", "padding": "0.15rem 0.3rem"}

# Estilo específico para dropdowns com cores legíveis
DROPDOWN_STYLE = {
    **COMPONENTS.get("dropdown", {}),
    "color": COLORS.get("text_light", "#f8f9fa"),
    "backgroundColor": COLORS.get("background_input", "#495057"),
    "height": "26px",
    "minHeight": "26px",
}

READ_ONLY_STYLE = {
    **INPUT_STYLE,
    "backgroundColor": COLORS.get("background_card_header", "#495057"),
    "color": COLORS.get("text_muted", "#6c757d"),
    "cursor": "not-allowed",
}

# Style Constants from callbacks (merged for consistency)
CARD_HEADER_STYLE = {"fontSize": "0.85rem", "fontWeight": "bold", "color": COLORS["text_light"]}
PLACEHOLDER_STYLE = {
    "fontSize": "0.75rem",
    "color": COLORS.get("text_muted", "#6c757d"),
    "textAlign": "center",
    "height": "100%", # Revertido para height: "100%"
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
}


# Helper function
def create_input_row(label, id, placeholder, input_type="number"):
    return dbc.Row(
        [
            dbc.Col(dbc.Label(label, style=LABEL_STYLE), width=9, className="text-end pe-1"),
            dbc.Col(
                dbc.Input(
                    type=input_type,
                    id=id,
                    placeholder=placeholder,
                    persistence=True,
                    persistence_type="local",
                    style={**INPUT_STYLE, "width": "75%"},  # Kept width style from original
                ),
                width=3,
            ),
        ],
        className="g-1 mb-1",
    )


# --- Render Functions ---


def render_perdas_vazio():
    """Defines the layout for the 'no-load losses' tab."""
    top_card_min_height = "310px"
    input_card_style = {
        **COMPONENTS["card"],
        "minHeight": top_card_min_height,
        "height": "100%",
        "display": "flex",
        "flexDirection": "column",
    }
    input_card_body_style = {
        **COMPONENTS["card_body"],
        "flexGrow": 1,
        "display": "flex",
        "flexDirection": "column",
    }
    results_card_body_style = { # Deve ser idêntico ao input_card_body_style para consistência
        **COMPONENTS["card_body"],
        "flexGrow": 1,
        "display": "flex",
        "flexDirection": "column",
    }
    results_card_style = { # Deve ser idêntico ao input_card_style para consistência
        **COMPONENTS["card"],
        "minHeight": top_card_min_height, 
        "height": "100%",
        "display": "flex",
        "flexDirection": "column",
    }
    sut_card_style = {**COMPONENTS["card"], "height": "100%"}

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "PARÂMETROS DE PERDAS EM VAZIO",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dbc.Label(
                                                                    "Perdas em Vazio (kW):",
                                                                    style=TYPOGRAPHY["label"],
                                                                ),
                                                                width=9,
                                                                className="text-end pe-1",
                                                            ),
                                                            dbc.Col(
                                                                dcc.Input(
                                                                    type="number",
                                                                    id="perdas-vazio-kw",
                                                                    placeholder="Perdas vazio",
                                                                    persistence=True,
                                                                    persistence_type="local",
                                                                    style={
                                                                        **COMPONENTS["input"],
                                                                        "height": "26px",
                                                                        "padding": "0.15rem 0.3rem",
                                                                        "width": "75%",
                                                                    },
                                                                ),
                                                                width=3,
                                                            ),
                                                        ],
                                                        className="g-1 mb-1",
                                                    ),
                                                    create_input_row(
                                                        "Peso do Núcleo (Ton):",
                                                        "peso-projeto-Ton",
                                                        "Peso núcleo",
                                                    ),
                                                    create_input_row(
                                                        "Corrente de Excitação (%):",
                                                        "corrente-excitacao",
                                                        "Corrente excitação",
                                                    ),
                                                    create_input_row(
                                                        "Indução do Núcleo (T):",
                                                        "inducao-nucleo",
                                                        "Ex.: 1.7",
                                                    ),
                                                    create_input_row(
                                                        "Corrente de Excitação 1.1pu (%):",
                                                        "corrente-excitacao-1-1",
                                                        "Corrente 1.1pu",
                                                    ),
                                                    create_input_row(
                                                        "Corrente de Excitação 1.2pu (%):",
                                                        "corrente-excitacao-1-2",
                                                        "Corrente 1.2pu",
                                                    ),
                                                ],
                                                style={"flexGrow": 1},
                                            ),
                                            html.Div(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Button(
                                                                        "Calcular",
                                                                        id="calcular-perdas-vazio",
                                                                        color="info",
                                                                        size="sm",
                                                                        className="w-100",
                                                                        style={
                                                                            **COMPONENTS[
                                                                                "button_primary"
                                                                            ],
                                                                            "fontSize": "0.75rem",
                                                                            "fontWeight": "bold",
                                                                        },
                                                                    )
                                                                ],
                                                                width={"size": 8, "offset": 2},
                                                            )
                                                        ],
                                                        className="g-1 mt-3 pb-2",
                                                    )
                                                ]
                                            ),
                                        ],
                                        style=input_card_body_style,
                                    ),
                                ],
                                style=input_card_style,
                            ),
                        ],
                        width=4,
                        className="pe-1 h-100", 
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "PARÂMETROS GERAIS E DE MATERIAL",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE),
                                        id="parametros-gerais-card-body",
                                        style=results_card_body_style,
                                    ),
                                ],
                                style=results_card_style,
                            ),
                        ],
                        width=4,
                        className="px-1 h-100", 
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "RESULTADOS POR NÍVEL DE TENSÃO (DUT)",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE), # Conteúdo inicial
                                        id="dut-voltage-level-results-body", # ID movido para o CardBody
                                        style=results_card_body_style,
                                    ),
                                ],
                                style=results_card_style,
                            ),
                        ],
                        width=4,
                        className="ps-1 h-100",
                    ),
                ],
                className="mb-2 g-2",
                align="stretch",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "ANÁLISE TAPS SUT / CORRENTE EPS",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE),
                                        id="sut-analysis-results-area",
                                        style=COMPONENTS["card_body"],
                                    ),
                                ],
                                style=sut_card_style,
                            ),
                        ],
                        width=12,
                    )
                ],
                className="mb-2 g-2",
            ),
            dbc.Row(
                [dbc.Col(html.Div(id="legend-observations-area"), width=12)], className="g-2 mb-2"
            ),
        ]
    )


def render_perdas_carga():
    """Defines the layout for the 'load losses' tab."""
    top_card_min_height = "200px"
    input_card_style = {
        **COMPONENTS["card"],
        "minHeight": top_card_min_height,
        "height": "100%",
        "display": "flex",
        "flexDirection": "column",
    }
    input_card_body_style = {
        **COMPONENTS["card_body"],
        "flexGrow": 1,
        "display": "flex",
        "flexDirection": "column",
    }
    results_card_style = {**COMPONENTS["card"], "minHeight": top_card_min_height, "height": "100%"}
    # Use the DROPDOWN_STYLE defined at the top of the file
    final_dropdown_style = {**DROPDOWN_STYLE, "width": "75%"}

    return html.Div(
        [
            dbc.Row(
                [
                    # Input Parameters Column
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "PARÂMETROS DE PERDAS EM CARGA",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dbc.Label(
                                                                    "Temperatura de Referência (°C):",
                                                                    style=TYPOGRAPHY["label"],
                                                                ),
                                                                width=9,
                                                                className="text-end pe-1",
                                                            ),
                                                            dbc.Col(
                                                                dcc.Dropdown(
                                                                    id="temperatura-referencia",
                                                                    options=[
                                                                        {
                                                                            "label": f"{t}°C",
                                                                            "value": t,
                                                                        }
                                                                        for t in [75, 85, 115]
                                                                    ],
                                                                    value=75,
                                                                    clearable=False,
                                                                    style=final_dropdown_style,  # Use combined style
                                                                    persistence=True,
                                                                    persistence_type="local",
                                                                    className="dark-dropdown",
                                                                ),
                                                                width=3,
                                                            ),
                                                        ],
                                                        className="g-1 mb-1",
                                                    ),
                                                    create_input_row(
                                                        "Perdas Totais Tap- (kW):",
                                                        "perdas-carga-kw_U_min",
                                                        "Perdas Tap-",
                                                    ),
                                                    create_input_row(
                                                        "Perdas Totais Tap Nominal (kW):",
                                                        "perdas-carga-kw_U_nom",
                                                        "Perdas Tap Nom",
                                                    ),
                                                    create_input_row(
                                                        "Perdas Totais Tap+ (kW):",
                                                        "perdas-carga-kw_U_max",
                                                        "Perdas Tap+",
                                                    ),
                                                ]
                                            ),
                                            html.Div(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Button(
                                                                        "Calcular",
                                                                        id="calcular-perdas-carga",
                                                                        color="danger",
                                                                        size="sm",
                                                                        className="w-100",
                                                                        style={
                                                                            **COMPONENTS[
                                                                                "button_secondary"
                                                                            ],
                                                                            "fontSize": "0.75rem",
                                                                            "fontWeight": "bold",
                                                                        },
                                                                    )
                                                                ],
                                                                width={"size": 8, "offset": 2},
                                                            )
                                                        ],
                                                        className="g-1 mt-auto pb-2",
                                                    )
                                                ],
                                                style={
                                                    "display": "flex",
                                                    "flexDirection": "column",
                                                    "justifyContent": "flex-end",
                                                    "flexGrow": 1,
                                                },
                                            ),
                                        ],
                                        style=input_card_body_style,
                                    ),
                                ],
                                style=input_card_style,
                            ),
                        ],
                        width=5,
                        className="pe-1",
                    ),  # Adjusted width to 5 (40%)
                    # Nominal Conditions Column
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "CONDIÇÕES NOMINAIS (RESULTADOS)",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        ),
                                        style=COMPONENTS["card_header"],
                                    ),
                                    dbc.CardBody(
                                        html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE),
                                        id="condicoes-nominais-card-body",
                                        style={
                                            **COMPONENTS["card_body"],
                                            "minHeight": top_card_min_height,
                                        },
                                    ),
                                ],
                                style=results_card_style,
                            ),
                        ],
                        width=7,
                        className="ps-1",
                    ),  # Adjusted width to 7 (60%)
                ],
                className="mb-2 g-2",
                align="stretch",
            ),  # Use g-2 for consistent spacing
            # Row for Detailed Load Loss Results (Tables, SUT, Legend)
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(id="resultados-perdas-carga"), width=12
                    )  # This div holds multiple cards/tables from callback
                ],
                className="g-2",
            ),
        ]
    )


# --- Main Layout Creation ---
def create_losses_layout():
    """Creates the layout component for the Losses section."""
    log.info("Creating Losses layout...")

    # Import app here to avoid circular imports
    try:
        from app import app

        # Obter dados diretamente do MCP em vez de usar o cache
        if hasattr(app, "mcp") and app.mcp is not None:
            # Primeiro, tentar obter dados do losses-store
            losses_data = app.mcp.get_data("losses-store")
            if losses_data and "transformer_data" in losses_data:
                transformer_data = losses_data["transformer_data"]
                log.info("[Losses Layout] Dados do transformador obtidos do losses-store.")
            else:
                # Se não houver dados no losses-store, obter do transformer-inputs-store
                transformer_data = app.mcp.get_data("transformer-inputs-store")
                log.info(
                    "[Losses Layout] Dados do transformador obtidos do transformer-inputs-store."
                )
        else:
            transformer_data = (
                app.transformer_data_cache
                if hasattr(app, "transformer_data_cache") and app.transformer_data_cache
                else {}
            )
            log.info("[Losses Layout] Dados do transformador obtidos do cache.")
    except (ImportError, AttributeError) as e:
        log.warning(f"[Losses Layout] Erro ao acessar MCP ou cache: {e}")
        transformer_data = {}

    if not transformer_data:
        log.warning("[Losses Layout] Dados do transformador não encontrados.")

    layout = dbc.Container(
        [
            # Stores are now defined in components/global_stores.py and included in main_layout.py
            # Transformer Info Panel
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    id="transformer-info-losses-page", className="mb-1"
                                ),  # Painel visível que será atualizado pelo callback local
                                html.Div(
                                    html.Div(),
                                    id="transformer-info-losses",
                                    style={"display": "none"},
                                ),  # Painel oculto atualizado pelo callback global
                                html.Div(
                                    html.Div(),
                                    id="transformer-info-dieletric",
                                    style={"display": "none"},
                                ),  # Compatibility
                                html.Div(
                                    html.Div(),
                                    id="transformer-info-impulse",
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
                                    id="transformer-info-short-circuit",
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
                            className="mb-1",
                        ),
                        width=12,
                    )
                ],
                className="mb-1",
            ),
            # Losses Analysis Section
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div(
                            [
                                html.H6(
                                    "ANÁLISE DE PERDAS",
                                    className="text-center m-0 d-inline-block",
                                    style=CARD_HEADER_STYLE,
                                ),
                                # Botão de ajuda
                                create_help_button("perdas", "Ajuda sobre Cálculos de Perdas"),
                            ],
                            className="d-flex align-items-center justify-content-center",
                        ),
                        style=COMPONENTS.get("card_header", {}),
                    ),
                    dbc.CardBody(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        label="Perdas em Vazio",
                                        tab_id="tab-vazio",
                                        label_style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "bold",
                                            "padding": "0.25rem 0.5rem",
                                        },
                                        active_label_style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "bold",
                                            "padding": "0.25rem 0.5rem",
                                            "backgroundColor": "#ffffff", # Alterado para branco
                                            "color": "#000000", # Texto preto para contraste com fundo branco
                                            "borderRadius": "2px 2px 0 0",
                                        },
                                    ),
                                    dbc.Tab(
                                        label="Perdas em Carga",
                                        tab_id="tab-carga",
                                        label_style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "bold",
                                            "padding": "0.25rem 0.5rem",
                                        },
                                        active_label_style={
                                            "fontSize": "0.75rem",
                                            "fontWeight": "bold",
                                            "padding": "0.25rem 0.5rem",
                                            "backgroundColor": "#ffffff", # Alterado para branco
                                            "color": "#000000", # Texto preto para contraste com fundo branco
                                            "borderRadius": "2px 2px 0 0",
                                        },
                                    ),
                                ],
                                id="tabs-perdas",
                                active_tab="tab-vazio",
                                persistence=True,
                                persistence_type="local",
                            ),
                            # Tab content will be rendered by callback
                            html.Div(
                                id="conteudo-perdas",
                                className="mt-2 p-2",
                                style={
                                    "border": f"1px solid {COLORS.get('border', '#495057')}",
                                    "borderTop": "none",
                                    "backgroundColor": COLORS.get("background_card", "#343a40"),
                                    "borderRadius": "0 0 4px 4px",
                                },
                            ),
                        ],
                        style=COMPONENTS.get("card_body", {}),
                    ),
                ],
                style=COMPONENTS.get("card", {}),
            ),
        ],
        fluid=True,
        style={
            "backgroundColor": COLORS.get("background_main", "#282c34"),
            "padding": "0.5rem",
            "color": COLORS.get("text_light", "#f8f9fa"),
        },
    )

    return layout


# Keep the function as the primary export
# losses_layout = create_losses_layout() # Don't call it here, let the main app call it.
