# layouts/history.py
"""
Define o layout para a seção de Histórico de Sessões (VERSÃO REFEITA).
"""
import logging
import dash_bootstrap_components as dbc
from dash import dcc, html

# Importar estilos padronizados (ajuste o caminho se necessário)
from layouts import COLORS, COMPONENTS, SPACING, TYPOGRAPHY

log = logging.getLogger(__name__)

def create_history_layout():
    log.info("Criando layout de Histórico de Sessões (VERSÃO REFEITA)")

    # Estilos (pode ajustar conforme seu tema)
    stats_card_style = {**COMPONENTS["card"], "padding": "0.75rem", "textAlign": "center", "backgroundColor": COLORS["background_card_header"]}
    stats_icon_style = {"fontSize": "1.8rem", "marginBottom": "0.5rem", "color": COLORS["accent"]}
    stats_value_style = {"fontSize": "1.4rem", "fontWeight": "bold", "margin": "0", "color": COLORS["text_light"]}
    stats_label_style = {"fontSize": "0.75rem", "margin": "0", "color": COLORS["text_muted"]}

    table_header_style = {
        "backgroundColor": COLORS["background_card_header"], "color": COLORS["text_header"],
        "padding": "8px 12px", "fontWeight": "600", "textAlign": "center",
        "fontSize": "0.8rem", "border": f'1px solid {COLORS["border"]}', "borderBottomWidth": "2px"
    }

    layout = dbc.Container(
        [
            # Stores necessários para a página de histórico
            dcc.Store(id="history-page-temp-data", storage_type="memory"), # Para dados temporários na página
            dcc.Store(id="history-selected-session-id", storage_type="memory", data=None), # Para ID da sessão a ser excluída

            # Divs ocultas para compatibilidade com o callback global_updates
            # <<< ADD THESE HIDDEN DIVS >>>
            html.Div(html.Div(), id="transformer-info-losses", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-impulse", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-dieletric", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-applied", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-induced", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-short-circuit", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-temperature-rise", style={"display": "none"}),
            html.Div(html.Div(), id="transformer-info-comprehensive", style={"display": "none"}),
            # <<< END ADD THESE HIDDEN DIVS >>>


            # Título da Página
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.I(className="fas fa-history me-2", style={"fontSize": "1.8rem", "color": COLORS["accent"]}),
                            html.H4("Histórico de Sessões", className="d-inline align-middle", style=TYPOGRAPHY["title"]),
                        ], className="d-flex align-items-center"
                    ), width=12
                ), className=f"{SPACING['row_margin']} pt-2"
            ),

            # Seção de Gerenciamento de Sessões (Salvar e Buscar)
            dbc.Card(
                [
                    dbc.CardHeader(
                        [html.I(className="fas fa-tasks me-2"), "Gerenciar Sessões"],
                        style=COMPONENTS["card_header"]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.InputGroup(
                                            [
                                                dbc.InputGroupText(html.I(className="fas fa-search")),
                                                dbc.Input(id="history-search-input", placeholder="Filtrar por nome ou notas..."),
                                                dbc.Button("Buscar", id="history-search-button", color="primary", className="ms-2"),
                                            ]
                                        ), md=7, lg=8, className="mb-2 mb-md-0"
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            [html.I(className="fas fa-save me-2"), "Salvar Sessão Atual"],
                                            id="history-open-save-modal-button", # NOVO ID para abrir o modal
                                            color="success", className="w-100"
                                        ), md=5, lg=4
                                    ),
                                ], align="center"
                            )
                        ], style=COMPONENTS["card_body"]
                    ),
                ], style=COMPONENTS["card"], className=SPACING["row_margin"]
            ),

            # Estatísticas (Opcional, mas útil)
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(html.Div([
                                html.I(className="fas fa-database", style=stats_icon_style),
                                html.Div([
                                    html.H5(id="history-stats-total-sessions", children="--", style=stats_value_style),
                                    html.P("Sessões Salvas", style=stats_label_style)
                                ])
                            ]), style=stats_card_style, md=4),
                            # Adicione mais estatísticas se desejar
                        ], className="g-0"
                    )
                ), style={"backgroundColor": COLORS["background_card_header"], "marginBottom": "1rem", "padding": "0.5rem"}
            ),

            # Tabela de Sessões Armazenadas
            dbc.Card(
                [
                    dbc.CardHeader(
                        [html.I(className="fas fa-list-alt me-2"), "Sessões Armazenadas"],
                        style=COMPONENTS["card_header"]
                    ),
                    dbc.CardBody(
                        [
                            dcc.Loading(
                                id="history-loading-table", type="circle", color=COLORS["primary"],
                                children=[
                                    html.Div( # Cabeçalho Fixo
                                        dbc.Row(
                                            [
                                                dbc.Col(html.Span("Data/Hora"), width=3, style=table_header_style),
                                                dbc.Col(html.Span("Nome da Sessão"), width=4, style=table_header_style),
                                                dbc.Col(html.Span("Notas"), width=3, style=table_header_style),
                                                dbc.Col(html.Span("Ações"), width=2, style=table_header_style),
                                            ], className="g-0"
                                        ), style={"position": "sticky", "top": 0, "zIndex": 1, "backgroundColor": COLORS["background_card"]}
                                    ),
                                    html.Div( # Corpo Rolável
                                        id="history-table-body-content", # NOVO ID para o conteúdo da tabela
                                        style={"maxHeight": "45vh", "overflowY": "auto", "border": f'1px solid {COLORS["border"]}', "borderTop": "none"}
                                    )
                                ]
                            ),
                            html.Div(id="history-action-message", className="mt-3", style={"minHeight": "40px"})
                        ], style=COMPONENTS["card_body"]
                    ),
                ], style=COMPONENTS["card"]
            ),

            # Modal para Salvar Sessão
            dbc.Modal(
                [
                    dbc.ModalHeader("Salvar Sessão Atual", style={"backgroundColor": COLORS["background_card_header"], "color": COLORS["text_header"]}),
                    dbc.ModalBody(
                        [
                            dbc.Label("Nome da Sessão:", html_for="history-session-name-input", style=TYPOGRAPHY["label"]),
                            dbc.Input(id="history-session-name-input", placeholder="Identificador único", type="text", className="mb-3", style=COMPONENTS["input"]),
                            dbc.Label("Notas (Opcional):", html_for="history-session-notes-input", style=TYPOGRAPHY["label"]),
                            dbc.Textarea(id="history-session-notes-input", placeholder="Detalhes...", style={**COMPONENTS["input"], "height": "100px"}),
                            html.Div(id="history-save-modal-error", className="text-danger small mt-2") # Para erros no modal
                        ], style={"backgroundColor": COLORS["background_card"], "color": COLORS["text_light"]}
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancelar", id="history-save-modal-cancel-button", color="secondary", outline=True),
                            dbc.Button(html.Span([html.I(className="fas fa-save me-1"), "Salvar"]), id="history-save-modal-confirm-button", color="success"),
                        ], style={"backgroundColor": COLORS["background_card_header"], "borderTop": f'1px solid {COLORS["border"]}'}
                    ),
                ],
                id="history-save-session-modal",
                is_open=False,
                backdrop="static",
                centered=True,
            ),

            # Modal para Confirmar Exclusão
            dbc.Modal(
                [
                    dbc.ModalHeader("Confirmar Exclusão", style={"backgroundColor": COLORS["background_card_header"], "color": COLORS["text_header"]}),
                    dbc.ModalBody(
                        [
                            html.P("Tem certeza que deseja excluir esta sessão?"),
                            html.P("Esta ação não pode ser desfeita.", className="fw-bold", style={"color": COLORS["danger"]}),
                        ], style={"backgroundColor": COLORS["background_card"], "color": COLORS["text_light"]}
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Cancelar", id="history-delete-modal-cancel-button", color="secondary", outline=True),
                            dbc.Button(html.Span([html.I(className="fas fa-trash-alt me-1"), "Excluir"]), id="history-delete-modal-confirm-button", color="danger"),
                        ], style={"backgroundColor": COLORS["background_card_header"], "borderTop": f'1px solid {COLORS["border"]}'}
                    ),
                ],
                id="history-delete-session-modal",
                is_open=False,
                backdrop="static",
                centered=True,
            ),
        ],
        fluid=True,
        style={"backgroundColor": COLORS["background_main"], "padding": "1rem", "color": COLORS["text_light"], "minHeight": "calc(100vh - 120px)"}
    )
    return layout