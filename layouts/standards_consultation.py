"""
Layout para o módulo de consulta de normas técnicas.
"""
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

# Configurar logger
log = logging.getLogger(__name__)


def create_standards_consultation_layout():
    """
    Cria o layout para a página de consulta de normas técnicas.

    Returns:
        dbc.Container: Layout completo da página
    """
    log.info("Criando layout de consulta de normas técnicas")

    # Layout principal
    layout = dbc.Container(
        [
            dbc.Row(
                [
                    # Título da página
                    dbc.Col(
                        [
                            html.H2("Consulta de Normas Técnicas", className="mb-4 mt-4"),
                            html.Hr(),
                        ],
                        width=12,
                    )
                ]
            ),
            # Armazenamento de estado
            dcc.Store(id="standards-current-search", data=None),
            dcc.Store(id="standards-current-category", data=None),
            dcc.Store(id="standards-current-standard", data=None),
            # Divs ocultas para compatibilidade com o callback global_updates
            html.Div(id="transformer-info-losses", style={"display": "none"}),
            html.Div(id="transformer-info-impulse", style={"display": "none"}),
            html.Div(id="transformer-info-dieletric", style={"display": "none"}),
            html.Div(id="transformer-info-applied", style={"display": "none"}),
            html.Div(id="transformer-info-induced", style={"display": "none"}),
            html.Div(id="transformer-info-short-circuit", style={"display": "none"}),
            html.Div(id="transformer-info-temperature-rise", style={"display": "none"}),
            html.Div(id="transformer-info-comprehensive", style={"display": "none"}),
            # Nota: Os stores globais são definidos em components/global_stores.py
            # e incluídos no layout principal em layouts/main_layout.py
            dbc.Row(
                [
                    # Sidebar (Navegação e Filtros)
                    dbc.Col(
                        [
                            # Seção de busca
                            dbc.Card(
                                [
                                    dbc.CardHeader("Busca", className="fw-bold"),
                                    dbc.CardBody(
                                        [
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="standards-search-input",
                                                        placeholder="Buscar nas normas...",
                                                        type="text",
                                                    ),
                                                    dbc.Button(
                                                        html.I(className="fas fa-search"),
                                                        id="standards-search-button",
                                                        color="primary",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(id="standards-search-info"),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Seção de categorias
                            dbc.Card(
                                [
                                    dbc.CardHeader("Categorias", className="fw-bold"),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                id="standards-categories-loading",
                                                type="circle",
                                                children=html.Div(
                                                    id="standards-categories-container"
                                                ),
                                            )
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Lista de normas
                            dbc.Card(
                                [
                                    dbc.CardHeader("Normas Disponíveis", className="fw-bold"),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                id="standards-nav-loading",
                                                type="circle",
                                                children=html.Div(id="standards-nav-sidebar"),
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=3,
                    ),
                    # Conteúdo principal
                    dbc.Col(
                        [
                            # Resultados da busca
                            html.Div(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                "Resultados da Busca", className="fw-bold"
                                            ),
                                            dbc.CardBody([html.Div(id="standards-search-results")]),
                                        ]
                                    )
                                ],
                                id="standards-search-results-container",
                                style={"display": "none"},
                                className="mb-3",
                            ),
                            # Visualizador de norma
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.Span(
                                                "Visualizador de Norma",
                                                id="standards-viewer-title",
                                                className="fw-bold",
                                            ),
                                            dbc.Button(
                                                html.I(className="fas fa-expand"),
                                                id="standards-fullscreen-button",
                                                color="link",
                                                size="sm",
                                                className="float-end",
                                                title="Expandir visualizador",
                                            ),
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                id="standards-content-loading",
                                                type="circle",
                                                children=html.Div(
                                                    [
                                                        # Metadados da norma
                                                        html.Div(
                                                            id="standards-metadata-display",
                                                            className="mb-3",
                                                        ),
                                                        # Conteúdo da norma
                                                        html.Div(
                                                            dcc.Markdown(
                                                                id="standards-content-display",
                                                                dangerously_allow_html=True,
                                                                className="standards-markdown-content",
                                                            ),
                                                            id="standards-content-container",
                                                            style={
                                                                "maxHeight": "800px",
                                                                "overflow": "auto",
                                                            },
                                                        ),
                                                    ]
                                                ),
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=9,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

    return layout
