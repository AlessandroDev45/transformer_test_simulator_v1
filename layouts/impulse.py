# layouts/impulse.py
""" Define o layout para a seção de Simulação de Ensaios de Impulso. """
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging # Adicionado para log
import plotly.graph_objects as go # Importação para criar gráficos
from layouts import COLORS, TYPOGRAPHY, COMPONENTS, SPACING

# Importar componentes reutilizáveis e constantes
# Certifique-se que os imports abaixo estão corretos e os módulos/constantes existem
try:
    from components.ui_elements import create_labeled_input # Exemplo, ajuste se necessário
    from utils.constants import GENERATOR_CONFIGURATIONS, SHUNT_OPTIONS, INDUCTORS_OPTIONS
    from components.transformer_info_template import create_transformer_info_panel
    from components.help_button import create_help_button
    import config # Importar config para usar as constantes de configuração
    from app import app # Para acessar o cache da aplicação
except ImportError as e:
    log = logging.getLogger(__name__)
    log.error(f"Erro ao importar dependências em layouts/impulse.py: {e}")
    # Pode ser útil definir valores padrão ou retornar um layout de erro aqui
    GENERATOR_CONFIGURATIONS = [{"label": "Padrão", "value": "12S-1P"}] # Exemplo de fallback
    SHUNT_OPTIONS = [{"label": "0.01 Ω", "value": 0.01}] # Exemplo de fallback
    INDUCTORS_OPTIONS = [{"label": "Nenhum", "value": 0}] # Exemplo de fallback
    # A importação de 'config' geralmente é crucial, pode lançar um erro se falhar


# Estilos locais usando os estilos padronizados
section_title_style = TYPOGRAPHY['section_title']
graph_container_style = {
    "marginTop": "10px",
    "borderRadius": "5px",
    "overflow": "hidden",
    "border": f"1px solid {COLORS['border']}",
    "backgroundColor": COLORS['background_card'],
    "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
}
tab_label_style = {
    "fontSize": "0.75rem",
    "fontWeight": "bold",
    "padding": "0.25rem 0.5rem",
    "color": COLORS['text_light']
}

# Estilo para os headers dos cards
card_header_style = COMPONENTS['card_header']

def create_impulse_layout():
    """Creates the layout component for the Impulse Simulation section.

    Esta função cria o layout da seção de Simulação de Ensaios de Impulso e inclui
    o painel de informações do transformador diretamente no layout, obtendo
    os dados do cache da aplicação.

    Returns:
        dash.html.Div: O layout completo da seção de Simulação de Ensaios de Impulso
    """
    log = logging.getLogger(__name__)
    log.info("Criando layout de impulso...")

    # Tenta obter os dados do transformador do cache da aplicação ou do MCP
    transformer_data = {}
    try:
        # Primeiro tenta obter do MCP (fonte mais confiável)
        if hasattr(app, 'mcp') and app.mcp is not None:
            transformer_data = app.mcp.get_data('transformer-inputs-store')
            log.info(f"[Impulse] Dados do transformador obtidos do MCP: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}")
        # Se não conseguir do MCP, tenta do cache
        elif hasattr(app, 'transformer_data_cache') and app.transformer_data_cache:
            transformer_data = app.transformer_data_cache
            log.info(f"[Impulse] Dados do transformador obtidos do cache: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'}")
        else:
            log.warning("[Impulse] Dados do transformador não encontrados no MCP nem no cache")
    except Exception as e:
        log.error(f"[Impulse] Erro ao obter dados do transformador: {e}")

    # --- Layout Principal ---
    return dbc.Container([
        # Location específico para esta seção para acionar o callback
        dcc.Location(id='url-impulse-section', refresh=False), # Mantido para trigger de pathname

                # Stores are now defined in components/global_stores.py and included in main_layout.py


        # Primeira seção - Informações do Transformador (sempre visível no topo)
        dbc.Row([
            dbc.Col(
                html.Div(
                    [
                        html.Div(
                            id="transformer-info-impulse-page", className="mb-1"
                        ),  # Painel visível que será atualizado pelo callback local
                        html.Div(
                            html.Div(),
                            id="transformer-info-impulse",
                            style={"display": "none"},
                        ),  # Painel oculto atualizado pelo callback global
                        html.Div(
                            html.Div(),
                            id="transformer-info-losses",
                            style={"display": "none"},
                        ),  # Compatibility
                        html.Div(
                            html.Div(),
                            id="transformer-info-dieletric",
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
        ], className="mb-1"), # Reduzida a margem inferior da linha de info

        # Título principal do módulo
        dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.H6("ANÁLISE DE IMPULSO", className="text-center m-0 d-inline-block", style=TYPOGRAPHY['card_header']),
                    # Botão de ajuda
                    create_help_button("impulse", "Ajuda sobre Simulação de Impulso")
                ], className="d-flex align-items-center justify-content-center"),
                style=COMPONENTS['card_header']
            ),
            dbc.CardBody([
                # Linha 1: Cabeçalho com título centralizado
                dbc.Row([
                    # Coluna vazia para empurrar o título para o centro (ajustar width se necessário)
                    dbc.Col(width=2),
                    # Coluna do Título Centralizado
                    dbc.Col(html.H6("Simulação de Ensaios de Impulso CDYH-2400kV/360kJ Impulse Voltage Test System",
                           className="text-primary m-0 text-center",
                           style={"whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}),
                           width=8),
                    # Coluna vazia à direita para manter o título centralizado
                    dbc.Col(width=2)
                ], className="mb-1 border-bottom align-items-center"), # Reduzido mb, alinhado itens verticalmente

        # Linha 2: Layout principal em 3 colunas (mantido)
        dbc.Row([
            # Coluna 1: Parâmetros de entrada (25%)
            dbc.Col([
                # Card para parâmetros básicos
                dbc.Card([
                    dbc.CardHeader("Parâmetros Básicos", className="p-1 text-center fw-bold fs-6", style=card_header_style),
                    dbc.CardBody([
                        # Tipo de impulso
                        dbc.Row([
                            dbc.Col([
                                html.Label("Tipo:", style={"fontSize": "0.75rem", "fontWeight": "bold", "color": COLORS['text_light']}),
                                dbc.RadioItems(
                                    id="impulse-type",
                                    options=[
                                        {"label": "Atmosférico (LI)", "value": "lightning"},
                                        {"label": "Manobra (SI)", "value": "switching"},
                                        {"label": "Cortado (LIC)", "value": "chopped"}
                                    ],
                                    value="lightning",
                                    inline=True,
                                    inputClassName="me-1",
                                    style={"fontSize": "0.75rem", "color": COLORS['text_light']},
                                    persistence=True,
                                    persistence_type='local'
                                )
                            ], width=12),
                        ], className="mb-0"),

                        # Tensão e Configuração
                        dbc.Row([
                            dbc.Col([
                                html.Label("Tensão (kV):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="test-voltage",
                                        type="number",
                                        value=1200,
                                        min=0,
                                        step=10,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="voltage-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="voltage-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=6),
                            dbc.Col([
                                html.Label("Config.:", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dcc.Dropdown(
                                    id="generator-config",
                                    options=[{"label": cfg["label"], "value": cfg["value"]} for cfg in GENERATOR_CONFIGURATIONS], # Usando cfg em vez de config
                                    value="6S-1P",
                                    clearable=False,
                                    style={
                                        "fontSize": "0.75rem",
                                        "height": "28px",
                                        "backgroundColor": COLORS['background_input'],
                                        "color": COLORS['text_light']
                                    },
                                    className="dash-dropdown-dark",
                                    persistence=True,
                                    persistence_type='local'
                                )
                            ], width=6)
                        ], className="mb-0"),

                        # Modelo e Capacitâncias
                        dbc.Row([
                            dbc.Col([
                                html.Label("Modelo:", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dcc.Dropdown(
                                    id="simulation-model-type",
                                    options=[
                                        {"label": "RLC+K", "value": "hybrid"},
                                        {"label": "RLC", "value": "rlc"},
                                    ],
                                    value="hybrid",
                                    clearable=False,
                                    style={
                                        "fontSize": "0.75rem",
                                        "height": "28px",
                                        "backgroundColor": COLORS['background_input'],
                                        "color": COLORS['text_light']
                                    },
                                    className="dash-dropdown-dark",
                                    persistence=True,
                                    persistence_type='local'
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Cap. DUT (pF):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="test-object-capacitance",
                                        type="number",
                                        value=3000,
                                        min=0,
                                        step=100,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="dut-cap-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="dut-cap-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=6)
                        ], className="mb-0"),

                        # Shunt e Capacitância parasita
                        dbc.Row([
                            dbc.Col([
                                html.Label("Shunt (Ω):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dcc.Dropdown(
                                    id="shunt-resistor",
                                    options=[{"label": option["label"], "value": option["value"]} for option in SHUNT_OPTIONS],
                                    value=0.01,
                                    clearable=False,
                                    style={
                                        "fontSize": "0.75rem",
                                        "height": "28px",
                                        "backgroundColor": COLORS['background_input'],
                                        "color": COLORS['text_light']
                                    },
                                    className="dash-dropdown-dark",
                                    persistence=True,
                                    persistence_type='local'
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Cap. Parasita (pF):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}), # Adicionado (pF)
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="stray-capacitance",
                                        type="number",
                                        value=400,
                                        min=0,
                                        step=50,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="stray-cap-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="stray-cap-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=6)
                        ], className="mb-1"), # Mantém espaçamento no final
                    ], style={**COMPONENTS['card_body'], "padding": "0.3rem"})
                ], style=COMPONENTS['card'], className="mb-1"), # Reduzido margin bottom ainda mais

                # Card para Resistores e Ajustes
                dbc.Card([
                    dbc.CardHeader("Resistores e Ajustes", className="p-1 text-center fw-bold fs-6", style=card_header_style),
                    dbc.CardBody([
                        # Resistores
                        dbc.Row([
                            dbc.Col([
                                html.Label("Rf (por coluna):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}), # Ajustado label
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="front-resistor-expression",
                                        type="text",
                                        value="15", # Valor inicial padrão
                                        placeholder="Ex: 15 ou 30||30",
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="rf-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="rf-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm"),
                                html.Small(id="front-resistor-help", className="text-muted", style={"fontSize": "0.65rem", "color": COLORS['text_muted']})
                            ], width=6),
                            dbc.Col([
                                html.Label("Rt (por coluna):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}), # Ajustado label
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="tail-resistor-expression",
                                        type="text",
                                        value="100", # Valor inicial padrão
                                        placeholder="Ex: 100 ou 50+50",
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="rt-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="rt-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm"),
                                html.Small(id="tail-resistor-help", className="text-muted", style={"fontSize": "0.65rem", "color": COLORS['text_muted']})
                            ], width=6)
                        ], className="mb-1"),

                        # Ajustes
                        dbc.Row([
                            dbc.Col([
                                html.Label("Aj. L (fator):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}), # Ajustado label
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="inductance-adjustment-factor",
                                        type="number",
                                        value=1.0,
                                        min=0.1, max=5.0, # Limites razoáveis
                                        step=0.1,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="ajl-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="ajl-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=6),
                            dbc.Col([
                                html.Label("Aj. Rt (fator):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}), # Ajustado label
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="tail-resistance-adjustment-factor",
                                        type="number",
                                        value=1.0,
                                        min=0.1, max=5.0, # Limites razoáveis
                                        step=0.1,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                        persistence=True,
                                        persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="ajrt-up",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="ajrt-down",
                                               style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=6)
                        ], className="mb-1"),

                        # Botão de Sugestão
                        dbc.Row([
                            dbc.Col(
                                dbc.Button("Sugerir Resistores", id="suggest-resistors-btn", color="info", outline=True, size="sm", className="w-100"),
                                width=12
                            )
                        ], className="mb-1"),

                        # Área de sugestões
                        dbc.Row([
                            dbc.Col([
                                html.Div(id="suggested-resistors-output",
                                       style={"fontSize": "0.7rem", "maxHeight": "60px", "overflowY": "auto", "border": f"1px solid {COLORS['border']}", "padding": "3px", "marginTop": "3px", "backgroundColor": COLORS['background_card'], "color": COLORS['text_light']}) # Estilo melhorado
                            ], width=12)
                        ], className="mb-1"),
                    ], style=COMPONENTS['card_body'])
                ], style=COMPONENTS['card'], className="mb-1"), # Reduzido margin bottom ainda mais

            ], width=3, className="pe-1"),  # Fim da coluna de parâmetros

            # Coluna 2: Gráficos e Indutâncias (50%)
            dbc.Col([
                # Título da Forma de Onda e Botão Simular
                dbc.Row([
                    dbc.Col([
                        html.H6(id="waveform-title-display", children="Forma de Onda de Tensão e Corrente",
                               className="m-0 text-center",
                               style={"fontSize": "0.9rem", "color": COLORS['text_light']})
                    ], width=9),
                    dbc.Col([
                        dbc.Button(
                            [
                                html.Span("Simular Forma de Onda", id="simulate-button-text"),
                                dbc.Spinner(size="sm", color="light", id="simulate-spinner", spinner_class_name="ms-2 d-none")
                            ],
                            id="simulate-button",
                            color="primary",
                            size="sm",
                            className="float-end",
                            style={"backgroundColor": COLORS['primary'], "borderColor": COLORS['primary']}
                        )
                    ], width=3, className="d-flex align-items-center justify-content-end")
                ], className="mb-1"), # Removido margin bottom

                # Alertas de Status
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            # Alerta de Conformidade Geral
                            dbc.Alert("Não Conforme", id="compliance-overall-alert", color="danger", className="py-1 px-2 m-0 me-1 d-none", style={"fontSize": "0.75rem"}), # d-none por padrão
                            # Alerta de Oscilação
                            dbc.Alert(html.Span([html.I(className="fas fa-wave-square me-1"), "Oscilatório"]), id="oscillation-warning-alert", color="warning", className="py-1 px-2 m-0 me-1 d-none", style={"fontSize": "0.75rem"}), # d-none por padrão
                            # Alerta de Energia
                            dbc.Alert("Energia OK", id="energy-compliance-alert", color="success", className="py-1 px-2 m-0 me-1 d-none", style={"fontSize": "0.75rem"}), # d-none por padrão
                            # Alerta de Tensão no Shunt
                            dbc.Alert(html.Span([html.I(className="fas fa-exclamation-triangle me-1"), "V Shunt > 5V!"]), id="shunt-voltage-alert", color="danger", className="py-1 px-2 m-0 d-none", style={"fontSize": "0.75rem"}), # d-none por padrão
                        ], className="d-flex justify-content-center flex-wrap") # flex-wrap para quebrar linha se necessário
                    ], width=12)
                ], className="mb-1"), # Mantido mb-1 para espaço mínimo

                # Gráficos com Loading
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-graph",
                            type="default",
                            children=[
                                # Gráfico de Tensão
                                dcc.Graph(
                                    id="impulse-waveform",
                                    figure=go.Figure(layout={
                                        "height": 300,
                                        "margin": dict(t=10, b=30, l=40, r=10),
                                        "xaxis_title": "Tempo (µs)",
                                        "yaxis_title": "Tensão (kV)",
                                        "paper_bgcolor": "rgba(0,0,0,0)",
                                        "plot_bgcolor": COLORS['background_card'],
                                        "font": {"size": 10, "color": COLORS['text_light']},
                                        "xaxis": {"gridcolor": COLORS['border']},
                                        "yaxis": {"gridcolor": COLORS['border']}
                                    }), # Altura aumentada para aproveitar o espaço
                                    config={"displayModeBar": False, "staticPlot": False},
                                    style={"height": "300px", "border": f"1px solid {COLORS['border']}", "borderRadius": "3px", "marginBottom": "5px", "backgroundColor": COLORS['background_card']} # Altura aumentada
                                ),
                                # Gráfico de Corrente
                                dcc.Graph(
                                    id="impulse-current",
                                    figure=go.Figure(layout={
                                        "height": 250,
                                        "margin": dict(t=10, b=30, l=40, r=10),
                                        "xaxis_title": "Tempo (µs)",
                                        "yaxis_title": "Corrente (A)",
                                        "paper_bgcolor": "rgba(0,0,0,0)",
                                        "plot_bgcolor": COLORS['background_card'],
                                        "font": {"size": 10, "color": COLORS['text_light']},
                                        "xaxis": {"gridcolor": COLORS['border']},
                                        "yaxis": {"gridcolor": COLORS['border']}
                                    }), # Altura aumentada para aproveitar o espaço
                                    config={"displayModeBar": False, "staticPlot": False},
                                    style={"height": "250px", "border": f"1px solid {COLORS['border']}", "borderRadius": "3px", "backgroundColor": COLORS['background_card']} # Altura aumentada
                                )
                            ]
                        )
                    ], width=12)
                ], className="mb-1") # Reduzido margin bottom
            ], width=5, className="px-1"),  # Fim da coluna de gráficos - reduzida para 5

            # Coluna 3: Resultados (25%)
            dbc.Col([
                # Card para Indutâncias (Movido para cima do card de análise)
                dbc.Card([
                    dbc.CardHeader("Indutâncias e Componentes Adicionais", className="p-1 text-center fw-bold fs-6", style=card_header_style),
                    dbc.CardBody([
                        # Linha 1: L Extra, Indutor Extra, L Carga/Trafo, Botão Calcular
                        dbc.Row([
                            # Coluna L Extra
                            dbc.Col([
                                html.Label("L Extra (μH):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="external-inductance", type="number", value=10, min=0, step=1,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']}, persistence=True, persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="lext-up", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="lext-down", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=3),

                            # Coluna Indutor Extra
                            dbc.Col([
                                html.Div([
                                    html.Label("Indutor Extra:", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                    dcc.Dropdown(
                                        id="inductor", options=[{"label": option["label"], "value": option["value"]} for option in INDUCTORS_OPTIONS],
                                        value=0,
                                        clearable=False,
                                        style={
                                            "fontSize": "0.75rem",
                                            "height": "28px",
                                            "backgroundColor": COLORS['background_input'],
                                            "color": COLORS['text_light']
                                        },
                                        className="dash-dropdown-dark",
                                        persistence=True,
                                        persistence_type='local'
                                    )
                                ], id="inductor-container", style={"display": "block"})
                            ], width=3),

                            # Coluna L Carga/Trafo (Input)
                            dbc.Col([
                                html.Label("L Carga/Trafo (H):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="transformer-inductance", type="number", value=0.05, min=0, step=0.01,
                                        style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']}, persistence=True, persistence_type='local'
                                    ),
                                    dbc.InputGroupText([
                                        html.I(className="fas fa-chevron-up", id="ltrafo-up", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        html.I(className="fas fa-chevron-down", id="ltrafo-down", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                    ], style={"padding": "0 5px"})
                                ], size="sm")
                            ], width=3),

                            # Coluna Botão Calcular L Trafo (Ajustada)
                            dbc.Col(
                                # Botão diretamente na coluna, alinhado ao final se necessário com mb-auto ou similar
                                dbc.Button(
                                    html.Span([html.I(className="fas fa-calculator me-1"), " Calcular L Trafo"]),
                                    id="show-transformer-calc",
                                    color="info",
                                    outline=True, # Garante contorno
                                    size="sm",
                                    className="w-100 mt-auto" # Usa mt-auto para empurrar para baixo se a linha tiver altura
                                ),
                                width=3,
                                className="d-flex align-items-end" # Tenta alinhar o conteúdo da coluna ao final
                            ),

                        ], className="g-2 mb-1"), # Fim da Linha 1 - Reduzido espaçamento

                        # Linha 2: Gap/Capacitor (condicional)
                        dbc.Row([
                            dbc.Col([
                                # Container para Gap (Impulso Cortado)
                                html.Div([
                                    html.Label("Gap Corte (cm):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id="gap-distance", type="number", value=4.0, min=0.1, step=0.5,
                                            style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']}, persistence=True, persistence_type='local'
                                        ),
                                        dbc.InputGroupText([
                                            html.I(className="fas fa-chevron-up", id="gap-up", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                            html.I(className="fas fa-chevron-down", id="gap-down", style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        ], style={"padding": "0 5px"})
                                    ], size="sm"),
                                    # Botão para calcular gap automaticamente
                                    dbc.Button(
                                        html.Span([html.I(className="fas fa-calculator me-1"), "Calcular Gap"]),
                                        id="calculate-gap-btn",
                                        color="info",
                                        outline=True,
                                        size="sm",
                                        className="w-100 mt-1",
                                        style={"fontSize": "0.7rem"}
                                    ),
                                    # Texto de ajuda para o gap
                                    html.Small(
                                        "Gap calculado para corte entre 2-6 μs",
                                        className="text-muted",
                                        style={"fontSize": "0.65rem", "color": COLORS['text_muted']}
                                    )
                                ], id="gap-distance-container", style={"display": "none"}),
                                # Container para Capacitor SI (Impulso de Manobra)
                                html.Div([
                                    html.Label("Cap. Acopl. (pF):", style={"fontSize": "0.75rem", "color": COLORS['text_light']}),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id="si-capacitor-value",
                                            type="number",
                                            value=600,
                                            min=0,
                                            step=100,
                                            style={"fontSize": "0.75rem", "height": "28px", "backgroundColor": COLORS['background_input'], "color": COLORS['text_light']},
                                            persistence=True,
                                            persistence_type='local'
                                        ),
                                        dbc.InputGroupText([
                                            html.I(className="fas fa-chevron-up", id="si-cap-up",
                                                   style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                            html.I(className="fas fa-chevron-down", id="si-cap-down",
                                                   style={"cursor": "pointer", "fontSize": "0.7rem"}),
                                        ], style={"padding": "0 5px"})
                                    ], size="sm"),
                                    html.Small("(em paralelo com Rf)", className="text-muted", style={"fontSize": "0.65rem", "color": COLORS['text_muted']})
                                ], id="capacitor-si-container", style={"display": "none"})
                            ], width=3) # Ocupa apenas o espaço necessário
                        ], className="g-2 mb-1"), # Fim da Linha 2 - Reduzido espaçamento

                        # Linha 3: Calculadora de Indutância (Collapse)
                        dbc.Row([
                            dbc.Col([
                                dbc.Collapse([
                                    html.Div([
                                        dbc.Row([
                                            dbc.Col(create_labeled_input("Tensão (kV)", "transformer-voltage", input_type="number", value=138, min=0, step=1, persistence=True, persistence_type='local'), width=6),
                                            dbc.Col(create_labeled_input("Potência (MVA)", "transformer-power", input_type="number", value=50, min=0, step=1, persistence=True, persistence_type='local'), width=6)
                                        ], className="mb-1 gx-2"),
                                        dbc.Row([
                                            dbc.Col(create_labeled_input("Z (%)", "transformer-impedance", input_type="number", value=12, min=0, step=0.1, persistence=True, persistence_type='local'), width=6),
                                            dbc.Col(create_labeled_input("Freq. (Hz)", "transformer-frequency", input_type="number", value=60, min=50, step=10, persistence=True, persistence_type='local'), width=6)
                                        ], className="mb-1 gx-2"),
                                        dbc.Row([
                                            dbc.Col(dbc.Button("Calcular L", id="calculate-inductance", color="info", size="sm", className="w-100"), width=6),
                                            dbc.Col(dbc.Button("Usar Dados Trafo", id="use-transformer-data", color="info", size="sm", className="w-100"), width=6)
                                        ], className="mb-1 gx-2"),
                                        dbc.Row([
                                            dbc.Col(html.Div(id="calculated-inductance-display", className="text-center text-muted", style={"fontSize": "0.7rem", "minHeight": "1.2rem", "color": COLORS['text_light']}), width=12)
                                        ])
                                    ], style={"border": f"1px solid {COLORS['border']}", "padding": "8px", "marginTop": "5px", "borderRadius": "4px", "backgroundColor": COLORS['background_card_header'], "color": COLORS['text_light'], "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"})
                                ], id="transformer-calc-collapse", is_open=False)
                            ], width=12) # Collapse ocupa a linha inteira
                        ], className="mb-1"), # Linha apenas para o Collapse

                        # Alerta SI (mantido)
                        dbc.Alert(
                            "Atenção: Modelo SI é experimental e pode não refletir todos os efeitos.",
                            id="si-model-warning-alert", color="warning", className="py-1 px-2 m-0 mt-2",
                            style={"fontSize": "0.7rem", "display": "none"}
                        ),
                    ], style=COMPONENTS['card_body'])
                ], style=COMPONENTS['card'], className="mb-1"), # Adicionado margin bottom

                # Tabs para resultados (Análise, Circuito, Energia)
                dbc.Tabs([
                    # Estilo personalizado para as abas
                    dbc.Tab(
                        html.Div( # Container para a tabela
                            id="waveform-analysis-table",
                            children=[dbc.Alert("Simule para ver a análise.", color="info", className="m-2", style={"fontSize": "0.7rem", "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"})], # Mensagem inicial
                            style={
                                "overflowY": "auto",
                                "fontSize": "0.7rem",
                                "padding": "8px",
                                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
                                "borderRadius": "0 0 3px 3px",
                                "border": f"1px solid {COLORS['border']}",
                                "borderTop": "none",
                                "backgroundColor": COLORS['background_card'],
                                "color": "#000000", # Alterado para preto para melhor legibilidade
                                "minHeight": "300px",
                                "maxHeight": "400px"
                            } # Estilo melhorado com altura mínima
                        ),
                        label="Análise",
                        tab_id="tab-analysis",
                        labelClassName="px-3 py-1 me-1", # Estilo label com margem à direita
                        activeLabelClassName="fw-bold" # Estilo label ativo
                    ),
                    dbc.Tab(
                        html.Div( # Container para a tabela
                            id="circuit-parameters-display",
                            children=[dbc.Alert("Simule para ver os parâmetros.", color="info", className="m-2", style={"fontSize": "0.7rem", "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"})], # Mensagem inicial
                            style={
                                "overflowY": "auto",
                                "fontSize": "0.7rem",
                                "padding": "8px",
                                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
                                "borderRadius": "0 0 3px 3px",
                                "border": f"1px solid {COLORS['border']}",
                                "borderTop": "none",
                                "backgroundColor": COLORS['background_card'],
                                "color": "#000000", # Alterado para preto para melhor legibilidade
                                "minHeight": "300px",
                                "maxHeight": "400px"
                            } # Estilo melhorado com altura mínima
                        ),
                        label="Circuito",
                        tab_id="tab-circuit",
                        labelClassName="px-3 py-1 me-1", # Estilo label com margem à direita
                        activeLabelClassName="fw-bold" # Estilo label ativo
                    ),
                    dbc.Tab(
                        html.Div( # Container para a tabela
                            id="energy-details-table",
                            children=[dbc.Alert("Simule para ver detalhes de energia.", color="info", className="m-2", style={"fontSize": "0.7rem", "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"})], # Mensagem inicial
                            style={
                                "overflowY": "auto",
                                "fontSize": "0.7rem",
                                "padding": "8px",
                                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
                                "borderRadius": "0 0 3px 3px",
                                "border": f"1px solid {COLORS['border']}",
                                "borderTop": "none",
                                "backgroundColor": COLORS['background_card'],
                                "color": "#000000", # Alterado para preto para melhor legibilidade
                                "minHeight": "300px",
                                "maxHeight": "400px"
                            } # Estilo melhorado com altura mínima
                        ),
                        label="Energia",
                        tab_id="tab-energy",
                        labelClassName="px-3 py-1 me-1", # Estilo label com margem à direita
                        activeLabelClassName="fw-bold" # Estilo label ativo
                    ),
                ],
                active_tab="tab-analysis",
                className="mb-0 custom-tabs",
                style={
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "width": "100%"
                }) # Estilo melhorado para separar as abas
            ], width=4, className="ps-1"),  # Fim da coluna de resultados - aumentada para 4
        ]),

                # Stores are now defined in components/global_stores.py and included in main_layout.py


        # Elementos para integração JavaScript (mantido)
        html.Div(id="spinner-dummy-output", style={"display": "none"}),

        # Intervalo para auto-simulação (mantido)
        dcc.Interval(id='auto-simulate-interval', interval=1*1000, n_intervals=0, disabled=True), # Intervalo ajustado para 1s
            ]), # Fechamento do CardBody
        ]), # Fechamento do Card

        # Script JS para spinners e collapse (mantido e revisado)
        html.Script("""
document.addEventListener('DOMContentLoaded', function() {
    // Função para manipular os cliques nos spinners e collapse
    function setupInteractiveElements() {
        const spinners = {
            'voltage-up': {id: 'test-voltage', step: 10, min: 0},
            'voltage-down': {id: 'test-voltage', step: -10, min: 0},
            'dut-cap-up': {id: 'test-object-capacitance', step: 100, min: 0},
            'dut-cap-down': {id: 'test-object-capacitance', step: -100, min: 0},
            'stray-cap-up': {id: 'stray-capacitance', step: 50, min: 0},
            'stray-cap-down': {id: 'stray-capacitance', step: -50, min: 0},
            'si-cap-up': {id: 'si-capacitor-value', step: 100, min: 0},
            'si-cap-down': {id: 'si-capacitor-value', step: -100, min: 0},
            'rf-up': {id: 'front-resistor-expression', isText: true, step: 1, min: 1},
            'rf-down': {id: 'front-resistor-expression', isText: true, step: -1, min: 1},
            'rt-up': {id: 'tail-resistor-expression', isText: true, step: 10, min: 1},
            'rt-down': {id: 'tail-resistor-expression', isText: true, step: -10, min: 1},
            'ajl-up': {id: 'inductance-adjustment-factor', step: 0.1, min: 0.1},
            'ajl-down': {id: 'inductance-adjustment-factor', step: -0.1, min: 0.1},
            'ajrt-up': {id: 'tail-resistance-adjustment-factor', step: 0.1, min: 0.1},
            'ajrt-down': {id: 'tail-resistance-adjustment-factor', step: -0.1, min: 0.1},
            'gap-up': {id: 'gap-distance', step: 0.5, min: 0.1},
            'gap-down': {id: 'gap-distance', step: -0.5, min: 0.1},
            'lext-up': {id: 'external-inductance', step: 1, min: 0},
            'lext-down': {id: 'external-inductance', step: -1, min: 0},
            'ltrafo-up': {id: 'transformer-inductance', step: 0.01, min: 0},
            'ltrafo-down': {id: 'transformer-inductance', step: -0.01, min: 0}
        };

        Object.keys(spinners).forEach(function(spinnerId) {
            var spinner = document.getElementById(spinnerId);
            // Remove listener antigo antes de adicionar novo, se existir
            if (spinner && spinner._clickListener) {
                spinner.removeEventListener('click', spinner._clickListener);
                spinner._clickListener = null;
                spinner.removeAttribute('data-listener-added');
            }
            if (spinner && !spinner.hasAttribute('data-listener-added')) {
                spinner.setAttribute('data-listener-added', 'true');
                const listener = function(e) { // Define a função listener para poder remover depois
                    e.preventDefault();
                    var config = spinners[spinnerId];
                    var input = document.getElementById(config.id);
                    if (!input) return;

                    var currentValue = input.value;
                    var newValue;
                    var precision = config.step.toString().includes('.') ? config.step.toString().split('.')[1].length : 0;

                    if (config.isText) {
                        // Tenta extrair número da expressão (simplificado, pega o primeiro número)
                        const match = currentValue.match(/\\d+/);
                        var baseVal = match ? parseInt(match[0]) : 0;
                        newValue = Math.max(config.min || 1, baseVal + config.step);
                        // Atualiza apenas o número na string, mantendo o resto (se houver) - CUIDADO!
                        // Isso pode não ser ideal para expressões complexas. Talvez o callback Python seja melhor.
                        if (match) {
                           input.value = currentValue.replace(match[0], String(newValue));
                        } else {
                           input.value = String(newValue);
                        }
                    } else {
                        var val = parseFloat(currentValue) || 0;
                        var minVal = config.min !== undefined ? config.min : parseFloat(input.min) || 0;
                        newValue = Math.max(minVal, val + config.step);
                        newValue = parseFloat(newValue.toFixed(precision)); // Arredonda para precisão do step
                    }

                    if (input.value !== String(newValue)) {
                        input.value = String(newValue);
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                };
                spinner.addEventListener('click', listener);
                spinner._clickListener = listener; // Armazena a referência para poder remover
            }
        });

        // Configurar o botão collapse do transformador
        var toggleBtn = document.getElementById('show-transformer-calc');
         if (toggleBtn && toggleBtn._clickListener) {
             toggleBtn.removeEventListener('click', toggleBtn._clickListener);
             toggleBtn._clickListener = null;
             toggleBtn.removeAttribute('data-listener-added');
         }
        if (toggleBtn && !toggleBtn.hasAttribute('data-listener-added')) {
             toggleBtn.setAttribute('data-listener-added', 'true');
             const listener = function() {
                var collapseElement = document.getElementById('transformer-calc-collapse');
                if (collapseElement) {
                    var bsCollapse = bootstrap.Collapse.getInstance(collapseElement);
                    if (!bsCollapse) {
                        // Inicializa se não existir, mas não alterna aqui
                        bsCollapse = new bootstrap.Collapse(collapseElement, { toggle: false });
                    }
                     // Alterna o estado
                    bsCollapse.toggle();
                }
            };
             toggleBtn.addEventListener('click', listener);
             toggleBtn._clickListener = listener;
        }
    }

    // Executar imediatamente
    setupInteractiveElements();

    // Usar MutationObserver para garantir que os listeners sejam reanexados após atualizações do Dash
    const observer = new MutationObserver(function(mutations) {
        let needsSetup = false;
        for (const mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                 // Verifica se algum nó adicionado ou seus filhos são elementos interativos
                 mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.matches('.fa-chevron-up, .fa-chevron-down, #show-transformer-calc') || node.querySelector('.fa-chevron-up, .fa-chevron-down, #show-transformer-calc')) {
                             needsSetup = true;
                        }
                    }
                 });
            }
            if (needsSetup) break; // Otimização: Sai cedo se já encontrou um
        }

        if (needsSetup) {
           // console.log("Relevant DOM change detected, re-running setupInteractiveElements");
           setupInteractiveElements();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Limpeza: Desconectar o observer quando não for mais necessário (ex: ao sair da página)
    // window.addEventListener('beforeunload', () => {
    //     observer.disconnect();
    // });

});
""", type="text/javascript")


    ], fluid=True, className="p-0", style={
        "backgroundColor": COLORS['background_main'],
        "color": COLORS['text_light'],
        "padding": "0.25rem",
        "borderRadius": "4px",
        "marginTop": "0",
        "marginBottom": "0",
        "height": "100%",
        "maxHeight": "calc(100vh - 120px)"
    })
