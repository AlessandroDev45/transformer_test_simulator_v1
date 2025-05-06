# layouts/main_layout.py (MODIFICADO PARA dbc.Button)
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc # Precisa do dbc agora
import datetime
import logging
import config
from utils.routes import VALID_ROUTES, ROUTE_LABELS, normalize_pathname
from layouts import COLORS, TYPOGRAPHY, COMPONENTS, SPACING

log = logging.getLogger(__name__)

# --- Store IDs (como antes) ---
STORE_IDS = [
    'transformer-inputs-store', 'losses-store', 'impulse-store',
    'dieletric-analysis-store', 'applied-voltage-store', 'induced-voltage-store',
    'short-circuit-store', 'temperature-rise-store', 'limit-status-store',
    "front-resistor-data", "tail-resistor-data", "calculated-inductance",
    "simulation-status"
]

def create_main_layout(uso_atual=0, limite_atingido=False):
    """
    Cria o layout principal da aplicação Dash.
    """
    log.debug("Creating main layout (dbc.Button, n_clicks, stores defined here)...")
    # Only log to debug, not print to console
    log.debug("[main_layout.py] Iniciando create_main_layout (dbc.Button)...")

    # --- Navbar Superior ---
    navbar = dbc.Navbar(
        dbc.Container([
             dbc.Row(
                [
                    dbc.Col(
                        html.A(
                            html.Div([
                                # Logo com efeito de sombra
                                html.Img(
                                    src=dash.get_asset_url("DataLogo.jpg"),
                                    height="40px",
                                    style={
                                        "filter": "drop-shadow(0px 2px 2px rgba(0,0,0,0.3))",
                                        "marginRight": "15px",
                                        "verticalAlign": "middle",
                                        "borderRadius": "4px",
                                    }
                                ),
                                # Div para o título principal e subtítulo
                                html.Div([
                                    # Título principal
                                    html.H4(
                                        "Simulador de Testes de Transformadores",
                                        className="m-0",
                                        style={
                                            **TYPOGRAPHY['title'],
                                            "fontSize": "1.1rem",
                                            "letterSpacing": "0.05rem",
                                            "textShadow": "0px 1px 2px rgba(0,0,0,0.3)",
                                            "marginBottom": "2px !important",
                                            "lineHeight": "1.2",
                                            "color": COLORS['text_light'],
                                        }
                                    ),
                                    # Subtítulo com padrões e modelo
                                    html.Div(
                                        [
                                            html.Span("IEC/IEEE/ABNT", style={"fontWeight": "bold"}),
                                            " | ",
                                            html.Span("EPS 1500", style={"color": COLORS['accent'] or "#ffc107"})
                                        ],
                                        style={
                                            "fontSize": "0.7rem",
                                            "color": "rgba(255,255,255,0.85)",
                                            "letterSpacing": "0.03rem",
                                        }
                                    )
                                ], style={"display": "inline-block", "verticalAlign": "middle"})
                            ], style={"display": "flex", "alignItems": "center"}),
                            href="/",
                            style={"textDecoration": "none"}
                        ),
                        width="auto",
                        className="d-flex align-items-center"
                    ),
                    dbc.Col(
                        [
                            # Contador de uso com ícone e estilo aprimorado
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(className="fas fa-chart-line me-1",
                                                 style={"fontSize": "0.7rem"}),
                                            html.Span("Uso:",
                                                     style={"fontSize": "0.7rem", "opacity": "0.9"}),
                                            html.Span(
                                                f" {uso_atual}",
                                                style={
                                                    "fontSize": "0.8rem",
                                                    "fontWeight": "bold",
                                                    "marginLeft": "2px"
                                                }
                                            ),
                                            # Barra de progresso
                                            html.Div(
                                                html.Div(
                                                    "",
                                                    style={
                                                        "width": f"{min(100, int(uso_atual / 10))}%",
                                                        "height": "3px",
                                                        "backgroundColor": COLORS['accent'],
                                                        "borderRadius": "2px",
                                                        "transition": "width 0.5s ease-in-out"
                                                    }
                                                ),
                                                style={
                                                    "width": "50px",
                                                    "height": "3px",
                                                    "backgroundColor": "rgba(255,255,255,0.2)",
                                                    "borderRadius": "2px",
                                                    "marginLeft": "5px",
                                                    "display": "inline-block",
                                                    "verticalAlign": "middle"
                                                }
                                            )
                                        ],
                                        className="d-flex align-items-center"
                                    ),
                                ],
                                id='usage-counter-display',
                                className="me-3 py-1 px-2",
                                style={
                                    "backgroundColor": "rgba(13, 202, 240, 0.2)",
                                    "color": COLORS['text_light'],
                                    "border": "1px solid rgba(13, 202, 240, 0.3)",
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                    "borderRadius": "4px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "height": "28px"
                                }
                            ),

                            # Alerta de limite atingido com ícone
                            html.Div(
                                dbc.Alert(
                                    [
                                        html.I(className="fas fa-exclamation-triangle me-1"),
                                        "Limite Atingido!"
                                    ],
                                    color="danger",
                                    className="d-flex align-items-center p-2 mb-0",
                                    style={
                                        "fontSize": "0.75rem",
                                        "backgroundColor": "rgba(220, 53, 69, 0.9)",
                                        "color": COLORS['text_light'],
                                        "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                        "borderRadius": "4px",
                                        "border": "1px solid rgba(220, 53, 69, 0.5)",
                                        "height": "28px"
                                    }
                                ),
                                id='limit-alert-div',
                                className="me-3",
                                style={'display': 'block'} if limite_atingido else {'display': 'none'}
                            ),

                            # Botão de gerar relatório com efeito hover
                            dbc.Button(
                                [
                                    html.I(className="fas fa-file-pdf me-1"),
                                    "Gerar Relatório PDF"
                                ],
                                id="generate-report-btn",
                                className="me-2",
                                disabled=limite_atingido,
                                size="sm",
                                style={
                                    **COMPONENTS['button_primary'],
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                    "transition": "all 0.2s ease-in-out",
                                    "border": "1px solid rgba(255,255,255,0.1)",
                                    "backgroundColor": COLORS['primary'],
                                    "height": "28px",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "500",
                                    "letterSpacing": "0.02rem"
                                }
                            ),

                            # Botão de limpar todos os campos
                            dbc.Button(
                                [
                                    html.I(className="fas fa-eraser me-1"),
                                    "Limpar Campos"
                                ],
                                id="global-clear-button",
                                className="me-2",
                                color="warning",
                                size="sm",
                                style={
                                    **COMPONENTS['button_secondary'],
                                    "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                                    "transition": "all 0.2s ease-in-out",
                                    "border": "1px solid rgba(255,255,255,0.1)",
                                    "height": "28px",
                                    "fontSize": "0.75rem",
                                    "fontWeight": "500",
                                    "letterSpacing": "0.02rem"
                                }
                            ),

                            # Seletor de tema (claro/escuro)
                            html.Div(
                                [
                                    html.Button(
                                        [
                                            html.I(
                                                id="theme-toggle-icon",
                                                className="fas fa-sun me-1",
                                                style={"fontSize": "0.8rem"}
                                            ),
                                            html.Span(
                                                "Tema Claro",
                                                id="theme-toggle-text",
                                                style={"fontSize": "0.75rem"}
                                            )
                                        ],
                                        id="theme-toggle",
                                        className="theme-toggle",
                                        style={
                                            "backgroundColor": "rgba(255, 255, 255, 0.15)",
                                            "color": COLORS['text_light'],
                                            "border": "1px solid rgba(255, 255, 255, 0.2)",
                                            "borderRadius": "4px",
                                            "padding": "4px 8px",
                                            "fontSize": "0.75rem",
                                            "cursor": "pointer",
                                            "transition": "all 0.2s ease-in-out",
                                            "display": "flex",
                                            "alignItems": "center",
                                            "height": "28px"
                                        }
                                    )
                                ],
                                className="me-2"
                            ),
                        ],
                        width="auto",
                        className="d-flex justify-content-end align-items-center"
                    ),
                ],
                className="w-100 align-items-center",
                justify="between",
            ),
        ], fluid=True),
        dark=True,
        className="mb-1",
        style={
            "backgroundColor": COLORS['primary'],
            "padding": "0.3rem 1rem",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
            "borderBottom": f"1px solid {COLORS['border']}"
        }
    )

    # --- Sidebar de Navegação ---
    log.debug("Creating sidebar...")
    nav_items = []

    # Ícones para cada rota
    route_icons = {
        'dados': "fas fa-cogs",
        'perdas': "fas fa-bolt",
        'impulso': "fas fa-wave-square",
        'analise-dieletrica': "fas fa-microscope",
        'analise-dieletrica-completa': "fas fa-search-plus",
        'tensao-aplicada': "fas fa-plug",
        'tensao-induzida': "fas fa-charging-station",
        'curto-circuito': "fas fa-exclamation-triangle",
        'elevacao-temperatura': "fas fa-temperature-high",
        'historico': "fas fa-history",  # Histórico de sessões
        'consulta-normas': "fas fa-book",  # Consulta de normas
        'gerenciar-normas': "fas fa-cog"  # Gerenciamento de normas
    }

    # Usando as rotas definidas em utils/routes.py
    for route in VALID_ROUTES:
        nav_id = f'nav-{route}'
        label = ROUTE_LABELS[route]
        icon = route_icons.get(route, "fas fa-circle")
        log.debug(f"[main_layout.py] Criando dcc.Link ID: {nav_id}")

        # Removido print duplicado para nav-dados

        # Estilo para os links de navegação
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
            "color": COLORS['text_light'],
            "fontWeight": "normal",
            "fontSize": "0.75rem",
            "textDecoration": "none",
            "transition": "all 0.2s ease-in-out",
            "borderRadius": "0 4px 4px 0"
        }

        nav_items.append(
            html.Div(
                dcc.Link(
                    children=[
                        html.I(className=f"{icon} me-2", style={"width": "16px", "textAlign": "center"}),
                        html.Span(label)
                    ],
                    id=nav_id,
                    href=f'/{route}',  # Usar a rota correta definida em utils/routes.py
                    refresh=False,  # Importante: não recarregar a página
                    className="nav-link d-flex align-items-center",
                    style=nav_link_style
                ),
                id=f'nav-container-{route}',
                className="nav-item"
            )
        )

    # Sidebar com estilo atualizado
    sidebar = dbc.Nav(
        nav_items,
        vertical=True,
        pills=False, # Pills adiciona fundo arredondado, não queremos aqui
        className="border-end pe-2",
        style={
            "height": "calc(100vh - 120px)",
            "overflowY": "auto",
            "position": "sticky",
            "top": "0",
            "backgroundColor": COLORS['background_card_header'],
            "fontSize": "0.8rem",
            "padding": "0.75rem 0.5rem",
            "borderRadius": "4px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
            "marginTop": "0",
            "marginRight": "0.5rem",
            "scrollbarWidth": "thin",
            "scrollbarColor": f"{COLORS['border']} {COLORS['background_card_header']}"
        }
    )
    log.debug("Sidebar created.")

    # --- Área de Conteúdo Principal ---
    content_area = html.Div(
        id='content',
        children=[
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Selecione um módulo no menu lateral para começar."
                ],
                color="info",
                className="m-3",
                style={
                    **COMPONENTS['alert'],
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "borderLeft": f"4px solid {COLORS['info']}"
                }
            )
        ],
        style={
            "backgroundColor": COLORS['background_main'],
            "borderRadius": "4px",
            "padding": "0",
            "marginTop": "0",
            "height": "calc(100vh - 120px)",
            "overflowY": "auto",
            "scrollbarWidth": "thin",
            "scrollbarColor": f"{COLORS['border']} {COLORS['background_main']}"
        }
    )

    # --- Componentes Globais (Stores e Download como antes) ---
    log.debug("[main_layout.py] Definindo stores e componentes globais...")

    # Importar o componente de stores global
    from components.global_stores import create_global_stores

    # Obter a lista de stores globais
    global_stores = create_global_stores()

    global_components = [
        dcc.Store(id='limit-status-store', storage_type='memory', data={'limite_atingido': limite_atingido}),
        *global_stores,  # Desempacota a lista de stores globais
        dcc.Download(id="download-pdf"),

        # Modal de confirmação para limpar todos os campos
        dbc.Modal([
            dbc.ModalHeader("Confirmação", style={"backgroundColor": COLORS['background_card_header'], "color": COLORS['text_light']}),
            dbc.ModalBody([
                html.P("Tem certeza que deseja limpar todos os campos? Esta ação não pode ser desfeita.",
                       style={"color": COLORS['text_light']}),
            ], style={"backgroundColor": COLORS['background_card'], "color": COLORS['text_light']}),
            dbc.ModalFooter([
                dbc.Button("Cancelar", id="clear-cancel-button", className="me-2", color="secondary"),
                dbc.Button("Confirmar", id="clear-confirm-button", color="danger"),
            ], style={"backgroundColor": COLORS['background_card'], "borderTop": f"1px solid {COLORS['border']}"}),
        ], id="clear-confirm-modal", is_open=False, backdrop="static", centered=True,
           style={"color": COLORS['text_light']}),
    ]
    # Format the list of component IDs for better readability
    component_ids = [getattr(c, 'id', 'NoID') for c in global_components]
    log.debug(f"[main_layout.py] Componentes globais definidos: {component_ids}")

    # --- Layout Final Combinado ---
    log.debug("Assembling final layout (dbc.Button, n_clicks, stores defined here)...")
    log.debug("[main_layout.py] Montando layout final (dbc.Button)...")

    # Importante: Adicionar dcc.Location explicitamente no início do layout
    # para garantir que ele seja carregado corretamente
    location = dcc.Location(id='url', refresh=False)

    # Removido div oculto para callbacks clientside (não é mais necessário)

    layout = html.Div([
        location,  # Adiciona dcc.Location explicitamente
        *global_components, # Adiciona stores e download
        navbar,
        dbc.Container([
            dbc.Row([
                dbc.Col(sidebar, width=2, className="pe-0"),
                dbc.Col(content_area, width=10, className="ps-2")
            ], className=SPACING['row_gutter'], style={
                "marginTop": "0",
                "marginBottom": "0",
                "minHeight": "calc(100vh - 60px)"
            })
        ], fluid=True, className="flex-grow-1 px-2", style={
            "paddingTop": "0",
            "paddingBottom": "0"
        }),
        # Footer com informações da versão
        html.Footer(
            dbc.Container([
                html.Div([
                    html.Span("Transformer Test Simulator ", className="text-muted", style={"fontSize": "0.7rem"}),
                    html.Span("v1.0", className="text-muted", style={"fontSize": "0.7rem", "opacity": "0.7"}),
                ], className="text-center py-1")
            ], fluid=True),
            style={
                "backgroundColor": COLORS['background_card_header'],
                "borderTop": f"1px solid {COLORS['border']}",
                "marginTop": "auto",
                "fontSize": "0.7rem",
                "color": COLORS['text_muted'],
                "boxShadow": "0 -1px 3px rgba(0,0,0,0.1)"
            }
        )
    ], style={
        "minHeight": "100vh",
        "display": "flex",
        "flexDirection": "column",
        "backgroundColor": COLORS['background_main'],
        "overflow": "hidden"
    })
    log.debug("Main layout assembled (dbc.Button).")
    log.debug("[main_layout.py] Layout final montado (dbc.Button).")
    return layout
