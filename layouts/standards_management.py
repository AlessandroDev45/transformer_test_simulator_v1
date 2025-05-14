"""
Layout para o módulo de gerenciamento de normas técnicas.
"""
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

# Configurar logger
log = logging.getLogger(__name__)


def create_standards_management_layout():
    """
    Cria o layout para a página de gerenciamento de normas técnicas.

    Returns:
        dbc.Container: Layout completo da página
    """
    log.info("Criando layout de gerenciamento de normas técnicas")

    # Layout principal
    layout = dbc.Container(
        [
            # Store para comunicação entre callbacks
            dcc.Store(id="standards-processing-status-store", data=None, storage_type="memory"),
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
                    # Título da página
                    dbc.Col(
                        [
                            html.H2("Gerenciamento de Normas Técnicas", className="mb-4 mt-4"),
                            html.Hr(),
                        ],
                        width=12,
                    )
                ]
            ),
            dbc.Row(
                [
                    # Formulário de upload
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Adicionar Nova Norma", className="fw-bold"),
                                    dbc.CardBody(
                                        [
                                            # Upload de PDF
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Arquivo PDF da Norma",
                                                        className="form-label",
                                                    ),
                                                    dcc.Upload(
                                                        id="upload-standard-pdf",
                                                        children=html.Div(
                                                            [
                                                                "Arraste e solte ou ",
                                                                html.A(
                                                                    "selecione um arquivo PDF",
                                                                    className="text-primary",
                                                                ),
                                                            ]
                                                        ),
                                                        style={
                                                            "width": "100%",
                                                            "height": "60px",
                                                            "lineHeight": "60px",
                                                            "borderWidth": "1px",
                                                            "borderStyle": "dashed",
                                                            "borderRadius": "5px",
                                                            "textAlign": "center",
                                                            "margin": "10px 0",
                                                        },
                                                        multiple=False,
                                                    ),
                                                    html.Div(
                                                        id="upload-standard-info", className="mt-2"
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Metadados da norma
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Título da Norma",
                                                                className="form-label",
                                                            ),
                                                            dbc.Input(
                                                                id="standard-title-input",
                                                                type="text",
                                                                placeholder="Ex: Transformadores de Potência - Parte 3: Níveis de Isolamento",
                                                            ),
                                                        ],
                                                        width=12,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Número da Norma",
                                                                className="form-label",
                                                            ),
                                                            dbc.Input(
                                                                id="standard-number-input",
                                                                type="text",
                                                                placeholder="Ex: NBR 5356-3",
                                                            ),
                                                        ],
                                                        width=6,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Organização",
                                                                className="form-label",
                                                            ),
                                                            dbc.Input(
                                                                id="standard-organization-input",
                                                                type="text",
                                                                placeholder="Ex: ABNT",
                                                            ),
                                                        ],
                                                        width=6,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Ano de Publicação",
                                                                className="form-label",
                                                            ),
                                                            dbc.Input(
                                                                id="standard-year-input",
                                                                type="number",
                                                                placeholder="Ex: 2014",
                                                                min=1900,
                                                                max=2100,
                                                            ),
                                                        ],
                                                        width=6,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Categorias (separadas por vírgula)",
                                                                className="form-label",
                                                            ),
                                                            dbc.Input(
                                                                id="standard-categories-input",
                                                                type="text",
                                                                placeholder="Ex: Dielétrico, Transformador, Ensaios",
                                                            ),
                                                        ],
                                                        width=6,
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            # Botão de processamento
                                            dbc.Button(
                                                "Processar Norma",
                                                id="process-standard-button",
                                                color="primary",
                                                className="mt-2",
                                            ),
                                            # Status do processamento
                                            html.Div(
                                                id="processing-status-display",
                                                className="mt-3",
                                                children=html.Div(
                                                    "Pronto para processar normas",
                                                    className="text-muted",
                                                ),
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            )
                        ],
                        width=6,
                    ),
                    # Lista de normas existentes
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Normas Cadastradas", className="fw-bold"),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                id="existing-standards-loading",
                                                type="circle",
                                                children=html.Div(id="existing-standards-list"),
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )

    return layout
