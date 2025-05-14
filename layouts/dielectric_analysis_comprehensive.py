# layouts/dielectric_analysis_comprehensive.py
"""
Define o layout para a seção de Análise Dielétrica Completa.
Esta seção permite comparar detalhadamente os requisitos das normas NBR/IEC e IEEE
para os níveis de isolamento específicos selecionados na página de Análise Dielétrica.
"""
import logging

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html

# Importações para obter dados do transformador
# <<< REMOVIDO import direto de 'app' >>>
# from app import app
log = logging.getLogger(__name__)

# Importar estilos padronizados
from layouts import COLORS, COMPONENTS, SPACING, TYPOGRAPHY


def create_dielectric_comprehensive_layout():
    """
    Cria o layout da seção de Análise Dielétrica Completa.

    Returns:
        dash.html.Div: O layout completo da seção de Análise Dielétrica Completa
    """
    log.info("Creating Comprehensive Dielectric Analysis layout...")

    # Não obter dados do cache aqui
    transformer_data = {}

    # --- Verificador Initialization (como antes) ---
    verificador_instance = None
    try:
        from app_core.standards import VerificadorTransformador

        verificador_instance = VerificadorTransformador()
        if not verificador_instance.is_valid():
            log.warning(
                "VerificadorTransformador is invalid upon creation in create_dielectric_comprehensive_layout."
            )
        else:
            log.info(
                "VerificadorTransformador instantiated successfully for comprehensive analysis."
            )
    except ImportError:
        log.error(
            "Failed to import VerificadorTransformador in create_dielectric_comprehensive_layout."
        )
    except Exception as e:
        log.critical(f"CRITICAL error instantiating VerificadorTransformador: {e}", exc_info=True)
        return dbc.Alert(
            f"Erro crítico ao carregar dados das normas: {e}. Verifique a configuração e os arquivos.",
            color="danger",
            style=COMPONENTS["alert"],
        )

    # --- Layout Structure ---
    comprehensive_layout = html.Div(
        [
            # <<< REMOVIDOS dcc.Store definidos aqui (exceto o específico desta página) >>>
            dcc.Store(id="comprehensive-analysis-store", storage_type="local"),
            # Os stores globais ('dieletric-analysis-store', 'transformer-inputs-store', etc.)
            # JÁ ESTÃO definidos em components/global_stores.py e incluídos no layout principal
            # Primeira seção - Informações do Transformador (Container a ser preenchido)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    # Div onde o painel será renderizado - usando ID único para evitar conflitos
                                    html.Div(
                                        id="transformer-info-comprehensive-page", className="mb-1"
                                    ),
                                    # Div oculta para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-comprehensive",
                                        style={"display": "none"},
                                    ),
                                    # Divs ocultos para compatibilidade com o callback global_updates
                                    html.Div(
                                        html.Div(),
                                        id="transformer-info-dieletric",
                                        style={"display": "none"},
                                    ),
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
                                        id="transformer-info-temperature-rise",
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
            # Segunda seção - Parâmetros Selecionados e Título/Descrição lado a lado (como antes)
            dbc.Row(
                [
                    # Coluna 1 (3/4) - Parâmetros Selecionados
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            "Parâmetros Selecionados", className="text-center m-0"
                                        ),
                                        style={
                                            **COMPONENTS["card_header"],
                                            "backgroundColor": COLORS["primary"],
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="selected-params-display", className="px-2"
                                            )  # Conteúdo preenchido por callback
                                        ],
                                        style={**COMPONENTS["card_body"], "padding": "0.75rem"},
                                    ),
                                ],
                                style={
                                    **COMPONENTS["card"],
                                    "height": "100%",
                                    "boxShadow": "0 3px 5px rgba(0,0,0,0.2)",
                                },
                            )
                        ],
                        width=9,
                        className=SPACING["col_padding"],
                    ),
                    # Coluna 2 (1/4) - Título e Descrição (como antes)
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            "Análise Dielétrica Completa",
                                            className="text-center m-0",
                                        ),
                                        style={
                                            **COMPONENTS["card_header"],
                                            "backgroundColor": COLORS["info"],
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "Esta ferramenta compara detalhadamente os requisitos das normas NBR/IEC e IEEE para os níveis de isolamento "
                                                "selecionados na página anterior.",
                                                className="text-center mb-2",
                                                style={"fontSize": "0.8rem"},
                                            ),
                                            html.Div(
                                                [
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-search-plus me-1"
                                                            ),
                                                            "Analisar Detalhes",
                                                        ],
                                                        id="analisar-detalhes-button",
                                                        color="primary",
                                                        className="w-100 mb-2",
                                                        style={
                                                            **TYPOGRAPHY["button"],
                                                            "fontSize": "0.85rem",
                                                            "padding": "0.5rem 1rem",
                                                        },
                                                    ),
                                                    # Botão para forçar carregamento (ajustar se necessário)
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-sync-alt me-1"
                                                            ),
                                                            "Forçar Carregamento Dados",
                                                        ],
                                                        id="forcar-carregamento-button",  # Adicione este ID se ainda não existir
                                                        color="warning",
                                                        outline=True,
                                                        className="w-100 mb-2",
                                                        style={
                                                            **TYPOGRAPHY["button"],
                                                            "fontSize": "0.85rem",
                                                            "padding": "0.5rem 1rem",
                                                        },
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-arrow-left me-1"
                                                            ),
                                                            "Voltar",
                                                        ],
                                                        href="/analise-dieletrica",
                                                        color="secondary",
                                                        className="w-100",
                                                        style={
                                                            **TYPOGRAPHY["button"],
                                                            "fontSize": "0.85rem",
                                                            "padding": "0.5rem 1rem",
                                                        },
                                                    ),
                                                ],
                                                className="text-center mt-2",
                                            ),
                                        ],
                                        style={
                                            **COMPONENTS["card_body"],
                                            "height": "100%",
                                            "display": "flex",
                                            "flexDirection": "column",
                                            "justifyContent": "space-between",
                                        },
                                    ),
                                ],
                                style={
                                    **COMPONENTS["card"],
                                    "height": "100%",
                                    "boxShadow": "0 3px 5px rgba(0,0,0,0.2)",
                                },
                            )
                        ],
                        width=3,
                        className=SPACING["col_padding"],
                    ),
                ],
                className=SPACING["row_margin"],
            ),
            # Quarta seção - Área de Resultados Comparativos (Layout de 3 Colunas - como antes)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("Análise AT", className="text-center m-0"),
                                        style={
                                            **COMPONENTS["card_header"],
                                            "backgroundColor": COLORS["primary"],
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                html.Div(id="comparison-output-at"),
                                                type="circle",
                                                color=COLORS["primary"],
                                            )
                                        ],
                                        style={
                                            **COMPONENTS["card_body"],
                                            "padding": "0.75rem",
                                            "maxHeight": "calc(100vh - 350px)",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                style={
                                    **COMPONENTS["card"],
                                    "height": "100%",
                                    "boxShadow": "0 3px 5px rgba(0,0,0,0.2)",
                                },
                            )
                        ],
                        md=4,
                        className=SPACING["col_padding"],
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("Análise BT", className="text-center m-0"),
                                        style={
                                            **COMPONENTS["card_header"],
                                            "backgroundColor": COLORS["secondary"],
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                html.Div(id="comparison-output-bt"),
                                                type="circle",
                                                color=COLORS["secondary"],
                                            )
                                        ],
                                        style={
                                            **COMPONENTS["card_body"],
                                            "padding": "0.75rem",
                                            "maxHeight": "calc(100vh - 350px)",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                style={
                                    **COMPONENTS["card"],
                                    "height": "100%",
                                    "boxShadow": "0 3px 5px rgba(0,0,0,0.2)",
                                },
                            )
                        ],
                        md=4,
                        className=SPACING["col_padding"],
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("Análise Terciário", className="text-center m-0"),
                                        style={
                                            **COMPONENTS["card_header"],
                                            "backgroundColor": COLORS["info"],
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Loading(
                                                html.Div(id="comparison-output-terciario"),
                                                type="circle",
                                                color=COLORS["info"],
                                            )
                                        ],
                                        style={
                                            **COMPONENTS["card_body"],
                                            "padding": "0.75rem",
                                            "maxHeight": "calc(100vh - 350px)",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                style={
                                    **COMPONENTS["card"],
                                    "height": "100%",
                                    "boxShadow": "0 3px 5px rgba(0,0,0,0.2)",
                                },
                            )
                        ],
                        md=4,
                        className=SPACING["col_padding"],
                    ),
                ],
                className=SPACING["row_margin"],
            ),
            # Área de Mensagens/Alertas (como antes)
            html.Div(
                id="alert-container-comprehensive",
                style={
                    "position": "fixed",
                    "bottom": "20px",
                    "right": "20px",
                    "zIndex": "1000",
                    "maxWidth": "400px",
                },
            ),
        ]
    )

    return dbc.Container(comprehensive_layout, fluid=True, style=COMPONENTS["container"])


# Função create_sequence_graph (como antes - não precisa de alteração)
def create_sequence_graph(sequence_data, title):
    # ... (código da função como no original) ...
    if not sequence_data:
        return go.Figure()

    # Verificar o formato dos dados
    if "title" in sequence_data:
        title = sequence_data.get("title", title)

    x_values = []  # Tempo acumulado
    y_values = []  # Nível de tensão
    text_values = []  # Informações adicionais
    dp_markers_x = []  # Pontos onde medir DP
    dp_markers_y = []  # Valores correspondentes

    if "steps" in sequence_data:
        steps = sequence_data["steps"]
        for step in steps:
            time = step.get("time", 0)
            voltage = step.get("voltage", 0)
            label = step.get("label", "")
            medir_dp = step.get("measure_pd", False)
            x_values.append(time)
            y_values.append(voltage)
            text_values.append(f"{label}: {voltage}%")
            if medir_dp:
                dp_markers_x.append(time)
                dp_markers_y.append(voltage)
    else:
        tempo_acumulado = 0
        for step in sequence_data.get("steps_legacy", []):  # Use a different key if needed
            nivel = step.get("nivel", "")
            duracao = step.get("duracao_s", 0)
            tensao = step.get("tensao_kv", 0)
            medir_dp = step.get("medir_dp", False)
            x_values.append(tempo_acumulado)
            y_values.append(tensao)
            text_values.append(f"{nivel}: {tensao} kV")
            tempo_acumulado += duracao
            x_values.append(tempo_acumulado)
            y_values.append(tensao)
            text_values.append(f"{nivel}: {tensao} kV, {duracao}s")
            if medir_dp:
                dp_markers_x.append(tempo_acumulado - duracao / 2)
                dp_markers_y.append(tensao)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name="Sequência",
            line=dict(color=COLORS["primary"], width=2, shape="hv"),
            text=text_values,
            hoverinfo="text",
        )
    )
    if dp_markers_x:
        fig.add_trace(
            go.Scatter(
                x=dp_markers_x,
                y=dp_markers_y,
                mode="markers",
                name="Medição DP",
                marker=dict(
                    symbol="star",
                    size=10,
                    color=COLORS["warning"],
                    line=dict(width=1, color=COLORS["text_light"]),
                ),
                hoverinfo="text",
                text=["Medição de DP" for _ in dp_markers_x],
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Tempo (s)",
        yaxis_title="Tensão (kV / %)",
        template="plotly_dark",
        plot_bgcolor=COLORS["background_card"],
        paper_bgcolor=COLORS["background_card"],
        font=dict(color=COLORS["text_light"]),
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLORS["border"])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS["border"])
    return fig
