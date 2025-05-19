# layouts/main_layout.py
import logging

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from components.global_stores import create_global_stores
from layouts import COLORS, COMPONENTS, SPACING, TYPOGRAPHY
from utils.routes import ROUTE_LABELS, VALID_ROUTES

log = logging.getLogger(__name__)


def create_main_layout(uso_atual=0, limite_atingido=False, app=None):
    log.debug("Creating main layout (dbc.Button, n_clicks, stores defined in global_stores)...")
    print("[DEBUG MAIN LAYOUT] Iniciando create_main_layout (dbc.Button)...")

    # --- Navbar Superior ---
    navbar = dbc.Navbar(
        # ... (código da navbar como antes) ...
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.A(
                                html.Div(
                                    [
                                        html.Img(
                                            src=dash.get_asset_url("DataLogo.jpg"),
                                            height="40px",
                                            style={
                                                "filter": "drop-shadow(0px 2px 2px rgba(0,0,0,0.3))",
                                                "marginRight": "15px",
                                                "verticalAlign": "middle",
                                                "borderRadius": "4px",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.H4(
                                                    "Simulador de Testes de Transformadores",
                                                    className="m-0",
                                                    style={
                                                        **TYPOGRAPHY["title"],
                                                        "fontSize": "1.1rem",
                                                        "letterSpacing": "0.05rem",
                                                        "textShadow": "0px 1px 2px rgba(0,0,0,0.3)",
                                                        "marginBottom": "2px !important",
                                                        "lineHeight": "1.2",
                                                        "color": COLORS["text_light"],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "IEC/IEEE/ABNT",
                                                            style={"fontWeight": "bold"},
                                                        ),
                                                        " | ",
                                                        html.Span(
                                                            "EPS 1500",
                                                            style={
                                                                "color": COLORS["accent"]
                                                                or "#ffc107"
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "fontSize": "0.7rem",
                                                        "color": "rgba(255,255,255,0.85)",
                                                        "letterSpacing": "0.03rem",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "display": "inline-block",
                                                "verticalAlign": "middle",
                                            },
                                        ),
                                    ],
                                    style={"display": "flex", "alignItems": "center"},
                                ),
                                href="/",
                                style={"textDecoration": "none"},
                            ),
                            width="auto",
                            className="d-flex align-items-center",
                        ),
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-chart-line me-1",
                                                    style={"fontSize": "0.7rem"},
                                                ),
                                                html.Span(
                                                    "Uso:",
                                                    style={"fontSize": "0.7rem", "opacity": "0.9"},
                                                ),
                                                html.Span(
                                                    f" {uso_atual}",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "fontWeight": "bold",
                                                        "marginLeft": "2px",
                                                    },
                                                ),
                                                html.Div(
                                                    html.Div(
                                                        "",
                                                        style={
                                                            "width": f"{min(100, int(uso_atual / 10))}%",
                                                            "height": "3px",
                                                            "backgroundColor": COLORS["accent"],
                                                            "borderRadius": "2px",
                                                            "transition": "width 0.5s ease-in-out",
                                                        },
                                                    ),
                                                    style={
                                                        "width": "50px",
                                                        "height": "3px",
                                                        "backgroundColor": "rgba(255,255,255,0.2)",
                                                        "borderRadius": "2px",
                                                        "marginLeft": "5px",
                                                        "display": "inline-block",
                                                        "verticalAlign": "middle",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center",
                                        )
                                    ],
                                    id="usage-counter-display",
                                    className="me-3 py-1 px-2",
                                    style={
                                        "backgroundColor": "rgba(13, 202, 240, 0.2)",
                                        "color": COLORS["text_light"],
                                        "border": "1px solid rgba(13, 202, 240, 0.3)",
                                        "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                        "borderRadius": "4px",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "height": "28px",
                                    },
                                ),
                                html.Div(
                                    dbc.Alert(
                                        [
                                            html.I(className="fas fa-exclamation-triangle me-1"),
                                            "Limite Atingido!",
                                        ],
                                        color="danger",
                                        className="d-flex align-items-center p-2 mb-0",
                                        style={
                                            "fontSize": "0.75rem",
                                            "backgroundColor": "rgba(220, 53, 69, 0.9)",
                                            "color": COLORS["text_light"],
                                            "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                            "borderRadius": "4px",
                                            "border": "1px solid rgba(220, 53, 69, 0.5)",
                                            "height": "28px",
                                        },
                                    ),
                                    id="limit-alert-div",
                                    className="me-3",
                                    style={"display": "block"}
                                    if limite_atingido
                                    else {"display": "none"},
                                ),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-file-pdf me-1"),
                                        "Gerar Relatório PDF",
                                    ],
                                    id="generate-report-btn",
                                    className="me-2",
                                    disabled=limite_atingido,
                                    size="sm",
                                    style={
                                        **COMPONENTS["button_primary"],
                                        "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                        "transition": "all 0.2s ease-in-out",
                                        "border": "1px solid rgba(255,255,255,0.1)",
                                        "backgroundColor": COLORS["primary"],
                                        "height": "28px",
                                        "fontSize": "0.75rem",
                                        "fontWeight": "500",
                                        "letterSpacing": "0.02rem",
                                    },
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-eraser me-1"), "Limpar Campos"],
                                    id="global-clear-button",
                                    className="me-2",
                                    color="warning",
                                    size="sm",
                                    style={
                                        **COMPONENTS["button_secondary"],
                                        "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                        "transition": "all 0.2s ease-in-out",
                                        "border": "1px solid rgba(255,255,255,0.1)",
                                        "height": "28px",
                                        "fontSize": "0.75rem",
                                        "fontWeight": "500",
                                        "letterSpacing": "0.02rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            [
                                                html.I(
                                                    id="theme-toggle-icon",
                                                    className="fas fa-sun me-1",
                                                    style={"fontSize": "0.8rem"},
                                                ),
                                                html.Span(
                                                    "Tema Claro",
                                                    id="theme-toggle-text",
                                                    style={"fontSize": "0.75rem"},
                                                ),
                                            ],
                                            id="theme-toggle",
                                            className="theme-toggle",
                                            style={
                                                "backgroundColor": "rgba(255, 255, 255, 0.15)",
                                                "color": COLORS["text_light"],
                                                "border": "1px solid rgba(255, 255, 255, 0.2)",
                                                "borderRadius": "4px",
                                                "padding": "4px 8px",
                                                "fontSize": "0.75rem",
                                                "cursor": "pointer",
                                                "transition": "all 0.2s ease-in-out",
                                                "display": "flex",
                                                "alignItems": "center",
                                                "height": "28px",
                                            },
                                        )
                                    ],
                                    className="me-2",
                                ),
                            ],
                            width="auto",
                            className="d-flex justify-content-end align-items-center",
                        ),
                    ],
                    className="w-100 align-items-center",
                    justify="between",
                ),
            ],
            fluid=True,
        ),
        dark=True,
        className="mb-1",
        style={
            "backgroundColor": COLORS["primary"],
            "padding": "0.3rem 1rem",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
            "borderBottom": f"1px solid {COLORS['border']}",
        },
    )

    # --- Sidebar de Navegação ---
    log.debug("Criando sidebar...")
    # ... (código da sidebar como antes) ...
    nav_items = []
    route_icons = {
        "dados": "fas fa-cogs",
        "perdas": "fas fa-bolt",
        "impulso": "fas fa-wave-square",
        "analise-dieletrica": "fas fa-microscope",
        "analise-dieletrica-completa": "fas fa-search-plus",
        "tensao-aplicada": "fas fa-plug",
        "tensao-induzida": "fas fa-charging-station",
        "curto-circuito": "fas fa-exclamation-triangle",
        "elevacao-temperatura": "fas fa-temperature-high",
        "historico": "fas fa-history",
        "consulta-normas": "fas fa-book",
        "gerenciar-normas": "fas fa-cog",
    }
    nav_link_style = {
        "cursor": "pointer",
        "background": "transparent",
        "border": "none",
        "textAlign": "left",
        "display": "block",
        "width": "100%",
        "padding": "0.5rem 0.5rem",
        "marginBottom": "3px",
        "borderLeft": f"3px solid {COLORS['background_card_header']}",
        "color": COLORS["text_light"],
        "fontWeight": "normal",
        "fontSize": "0.75rem",
        "textDecoration": "none",
        "transition": "all 0.2s ease-in-out",
        "borderRadius": "0 4px 4px 0",
    }

    for route in VALID_ROUTES:
        nav_id = f"nav-{route}"
        label = ROUTE_LABELS[route]
        icon = route_icons.get(route, "fas fa-circle")

        # Link principal para a página
        main_link = dcc.Link(
            children=[
                html.I(className=f"{icon} me-2", style={"width": "16px", "textAlign": "center"}),
                html.Span(label),
            ],
            id=nav_id,
            href=f"/{route}",
            refresh=False,
            className="nav-link d-flex align-items-center",
            style=nav_link_style,
        )

        # Link para mostrar informações de callbacks
        callback_info_link = html.A(
            html.I(
                className="fas fa-code ms-2",
                style={"fontSize": "0.7rem", "color": COLORS.get("info", "#0dcaf0")},
            ),
            href=f"/{route}?show_callbacks=true",
            title="Mostrar informações de callbacks",
            style={"marginLeft": "auto"},
        )

        # Container com os dois links
        nav_container = html.Div(
            html.Div([main_link, callback_info_link], className="d-flex align-items-center w-100"),
            id=f"nav-container-{route}",
            className="nav-item",
        )

        nav_items.append(nav_container)

    sidebar = dbc.Nav(
        nav_items,
        vertical=True,
        pills=False,
        className="border-end pe-2",
        style={
            "height": "calc(100vh - 120px)",
            "overflowY": "auto",
            "position": "sticky",
            "top": "0",
            "backgroundColor": COLORS["background_card_header"],
            "fontSize": "0.8rem",
            "padding": "0.75rem 0.5rem",
            "borderRadius": "4px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
            "marginTop": "0",
            "marginRight": "0.5rem",
            "scrollbarWidth": "thin",
            "scrollbarColor": f"{COLORS['border']} {COLORS['background_card_header']}",
        },
    )

    # --- Área de Conteúdo Principal ---
    # Adiciona divs ocultas para todos os painéis de informação que podem ser atualizados globalmente
    hidden_info_panels = [
        html.Div(id="transformer-info-losses", style={"display": "none"}),
        html.Div(id="transformer-info-impulse", style={"display": "none"}),
        html.Div(id="transformer-info-dieletric", style={"display": "none"}),
        html.Div(id="transformer-info-applied", style={"display": "none"}),
        html.Div(id="transformer-info-induced", style={"display": "none"}),
        html.Div(id="transformer-info-short-circuit", style={"display": "none"}),
        html.Div(id="transformer-info-temperature-rise", style={"display": "none"}),
        html.Div(id="transformer-info-comprehensive", style={"display": "none"}),
        # Div para exibir informações de callbacks
        html.Div(id="callback-info-panel", style={"display": "none"}),
        # Não são mais necessários elementos dummy para callbacks de insulation_level
        # Adicione outros IDs de painéis de informação aqui se existirem
    ]

    content_area = html.Div(
        id="content",
        children=[
            *hidden_info_panels,  # Inclui os painéis ocultos no layout inicial
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Selecione um módulo no menu lateral para começar.",
                ],
                color="info",
                className="m-3",
                style={
                    **COMPONENTS.get("alert", {}),
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "borderLeft": f"4px solid {COLORS.get('info','#0dcaf0')}",
                },
            ),
        ],
        style={
            "backgroundColor": COLORS["background_main"],
            "borderRadius": "4px",
            "padding": "0",
            "marginTop": "0",
            "height": "calc(100vh - 120px)",
            "overflowY": "auto",
            "scrollbarWidth": "thin",
            "scrollbarColor": f"{COLORS['border']} {COLORS['background_main']}",
        },
    )

    # --- Componentes Globais (Stores, Download, Modais) ---
    log.debug("Definindo stores e componentes globais...")
    global_stores = create_global_stores(app)
    global_components = [
        *global_stores,
        dcc.Download(id="download-pdf"),
        # CSS personalizado
        html.Link(
            rel="stylesheet",
            href="/assets/custom.css",
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    "Confirmação",
                    style={
                        "backgroundColor": COLORS["background_card_header"],
                        "color": COLORS["text_light"],
                    },
                ),
                dbc.ModalBody(
                    [
                        html.P(
                            "Tem certeza que deseja limpar todos os campos? Esta ação não pode ser desfeita.",
                            style={"color": COLORS["text_light"]},
                        )
                    ],
                    style={
                        "backgroundColor": COLORS["background_card"],
                        "color": COLORS["text_light"],
                    },
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Cancelar",
                            id="clear-cancel-button",
                            className="me-2",
                            color="secondary",
                        ),
                        dbc.Button("Confirmar", id="clear-confirm-button", color="danger"),
                    ],
                    style={
                        "backgroundColor": COLORS["background_card"],
                        "borderTop": f'1px solid {COLORS["border"]}',
                    },
                ),
            ],
            id="clear-confirm-modal",
            is_open=False,
            backdrop="static",
            centered=True,
            style={"color": COLORS["text_light"]},
        ),
    ]
    # ... (restante da função como antes) ...
    component_ids = [getattr(c, "id", "NoID") for c in global_components]
    log.debug(
        f"Componentes globais definidos (sem duplicidade de limit-status-store): {component_ids}"
    )

    # --- Layout Final Combinado ---
    log.debug("Montando layout final...")
    location = dcc.Location(id="url", refresh=False)

    layout = html.Div(
        [
            location,
            *global_components,
            navbar,
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(sidebar, width=2, className="pe-0"),
                            dbc.Col(content_area, width=10, className="ps-2"),
                        ],
                        className=SPACING["row_gutter"],
                        style={
                            "marginTop": "0",
                            "marginBottom": "0",
                            "minHeight": "calc(100vh - 60px)",
                        },
                    )
                ],
                fluid=True,
                className="flex-grow-1 px-2",
                style={"paddingTop": "0", "paddingBottom": "0"},
            ),
            html.Footer(
                dbc.Container(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Transformer Test Simulator ",
                                    className="text-muted",
                                    style={"fontSize": "0.7rem"},
                                ),
                                html.Span(
                                    "v1.0",
                                    className="text-muted",
                                    style={"fontSize": "0.7rem", "opacity": "0.7"},
                                ),

                            ],
                            className="text-center py-1",
                        )
                    ],
                    fluid=True,
                ),
                style={
                    "backgroundColor": COLORS["background_card_header"],
                    "borderTop": f"1px solid {COLORS['border']}",
                    "marginTop": "auto",
                    "fontSize": "0.7rem",
                    "color": COLORS["text_muted"],
                    "boxShadow": "0 -1px 3px rgba(0,0,0,0.1)",
                },
            ),
        ],
        style={
            "minHeight": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "backgroundColor": COLORS["background_main"],
            "overflow": "hidden",
        },
    )
    log.debug("Layout final montado.")
    print("[DEBUG MAIN LAYOUT] Layout principal montado com sucesso (dbc.Button).")
    return layout
