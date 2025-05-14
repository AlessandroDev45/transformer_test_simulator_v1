# callbacks/navigation_dcc_links.py
import logging
import traceback

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

from layouts import COLORS
from utils.routes import ROUTE_HOME, ROUTE_LABELS, VALID_ROUTES, is_valid_route, normalize_pathname

log = logging.getLogger(__name__)


# --- Funções de Fallback e Importações Seguras ---
def _create_fallback_layout(module_name):
    log.error(f"Falha ao importar layout para '{module_name}'.")
    return dbc.Alert(
        f"Erro: Layout '{module_name}' não pôde ser carregado.", color="danger", className="m-3"
    )


# Importações de todos os layouts referenciados em main_layout.py (CORRIGIDAS NOVAMENTE)
# Dados Básicos:
try:
    from layouts.transformer_inputs import create_transformer_inputs_layout
except ImportError:
    create_transformer_inputs_layout = lambda: _create_fallback_layout("transformer_inputs")
# Perdas:
try:
    from layouts.losses import create_losses_layout  # Agora em losses.py
except ImportError:
    create_losses_layout = lambda: _create_fallback_layout("losses")
# Impulso:
try:
    from layouts.impulse import create_impulse_layout  # Agora em impulse.py
except ImportError:
    create_impulse_layout = lambda: _create_fallback_layout("impulse")
# Análise Dielétrica:
try:
    from layouts.dieletric_analysis import (
        create_dielectric_layout,
    )
except ImportError:
    create_dielectric_layout = lambda: _create_fallback_layout("dieletric_analysis")
# Análise Dielétrica Completa:
try:
    from layouts.dielectric_analysis_comprehensive import create_dielectric_comprehensive_layout
except ImportError:
    create_dielectric_comprehensive_layout = lambda: _create_fallback_layout(
        "dielectric_analysis_comprehensive"
    )
# Tensão Aplicada:
try:
    from layouts.applied_voltage import create_applied_voltage_layout
except ImportError:
    create_applied_voltage_layout = lambda: _create_fallback_layout("applied_voltage")
# Tensão Induzida:
try:
    from layouts.induced_voltage import create_induced_voltage_layout
except ImportError:
    create_induced_voltage_layout = lambda: _create_fallback_layout("induced_voltage")
try:
    from layouts.short_circuit import create_short_circuit_layout
except ImportError:
    create_short_circuit_layout = lambda: _create_fallback_layout("short_circuit")
try:
    from layouts.temperature_rise import create_temperature_rise_layout
except ImportError:
    create_temperature_rise_layout = lambda: _create_fallback_layout("temperature_rise")
# Fórmulas Matemáticas removidas - documentação agora é via HTML estático
# Histórico de Sessões:
try:
    from layouts.history import create_history_layout
except ImportError:
    create_history_layout = lambda: _create_fallback_layout("history")
# Consulta de Normas:
try:
    from layouts.standards_consultation import create_standards_consultation_layout
except ImportError:
    create_standards_consultation_layout = lambda: _create_fallback_layout("standards_consultation")
# Gerenciamento de Normas:
try:
    from layouts.standards_management import create_standards_management_layout
except ImportError:
    create_standards_management_layout = lambda: _create_fallback_layout("standards_management")

log.info("\n[navigation_dcc_links.py] REGISTRANDO CALLBACK DE NAVEGAÇÃO (render_content)\n")


# Callback ajustado para IDs e paths de main_layout.py original
@dash.callback(
    Output("content", "children"),  # ID correto do container de conteúdo
    Input("url", "pathname"),  # ID do dcc.Location
    # Adicionamos os stores como State para garantir que eles existam
    [
        State("transformer-inputs-store", "data"),
        State("losses-store", "data"),
        State("impulse-store", "data"),
        State("dieletric-analysis-store", "data"),
        State("applied-voltage-store", "data"),
        State("induced-voltage-store", "data"),
        State("short-circuit-store", "data"),
        State("temperature-rise-store", "data"),
    ],
)
def navigation_dcc_links_render_content(pathname, *args):
    """
    Atualiza a área de conteúdo ('content') baseado na URL ('pathname').

    Args:
        pathname: O pathname atual da URL
        *args: Argumentos adicionais (stores) para garantir que eles existam no layout
              Não são usados diretamente, mas sua presença como State garante que
              os componentes existam no layout.
    """
    try:
        log.info(f"\n=== CALLBACK render_content ACIONADO === URL: {pathname}\n")
        print(f"--- render_content: Pathname recebido: {pathname} ---")  # <--- ADDED PRINT
        print(f"[DEBUG] Callback de navegação acionado com pathname: {pathname}")

        # Normaliza o caminho removendo barras extras e tratando o caso raiz
        if pathname is None or pathname == "/":
            clean_path = ROUTE_HOME  # Default para a página inicial/dados básicos
            log.info(f"URL é / ou None, mapeado para '{clean_path}'")
            print(f"[DEBUG] URL é / ou None, mapeado para '{clean_path}'")
        else:
            clean_path = normalize_pathname(pathname)
            log.info(f"URL normalizada: {clean_path}")
            print(f"[DEBUG] URL normalizada: {clean_path}")

        # Mapeamento baseado nas rotas definidas em utils/routes.py
        if is_valid_route(clean_path):
            print(f"[DEBUG] Rota '{clean_path}' é válida")
            # Mapeamento de rotas para funções de layout
            route_to_layout = {
                "dados": create_transformer_inputs_layout,
                "perdas": create_losses_layout,
                "impulso": create_impulse_layout,
                "analise-dieletrica": create_dielectric_layout,
                "analise-dieletrica-completa": create_dielectric_comprehensive_layout,
                "tensao-aplicada": create_applied_voltage_layout,
                "tensao-induzida": create_induced_voltage_layout,
                "curto-circuito": create_short_circuit_layout,
                "elevacao-temperatura": create_temperature_rise_layout,
                "historico": create_history_layout,  # Histórico de sessões
                "consulta-normas": create_standards_consultation_layout,  # Consulta de normas
                "gerenciar-normas": create_standards_management_layout,  # Gerenciamento de normas
            }

            layout_function = route_to_layout.get(clean_path)
            if layout_function:
                log.info(f"Carregando layout para: {clean_path} ({ROUTE_LABELS.get(clean_path)})")
                print(
                    f"--- render_content: Tentando chamar função de layout para: {clean_path} ---"
                )  # Modified print
                print(
                    f"[DEBUG] Tentando carregar layout para: {clean_path}, função: {layout_function.__name__}"
                )
                try:
                    # Verificar se estamos navegando para a página de perdas e garantir que os dados sejam propagados
                    if clean_path == "perdas":
                        # Importar o utilitário de persistência do MCP
                        try:
                            from app import app
                            from utils.mcp_persistence import ensure_mcp_data_propagation

                            # Verificar se o MCP está disponível
                            if hasattr(app, "mcp") and app.mcp is not None:
                                # Obter dados do transformer-inputs-store
                                transformer_data = app.mcp.get_data("transformer-inputs-store")

                                if transformer_data:
                                    # Propagar dados para o losses-store
                                    propagation_result = ensure_mcp_data_propagation(
                                        app, "transformer-inputs-store", ["losses-store"]
                                    )
                                    log.info(
                                        f"Propagação de dados para losses-store: {propagation_result}"
                                    )
                        except Exception as e:
                            log.error(f"Erro ao propagar dados para losses-store: {e}")

                    layout_content = layout_function()  # Call the function
                    print(
                        f"--- render_content: Função de layout '{layout_function.__name__}' retornou com sucesso. Tipo: {type(layout_content)} ---"
                    )  # Modified print
                    print(f"[DEBUG] Layout carregado com sucesso para: {clean_path}")

                    if layout_content is None:
                        log.warning(f"Layout function for {clean_path} returned None!")
                        print(f"[WARN] Layout function for {clean_path} returned None!")
                        # Return an error message instead of None to see something
                        return dbc.Alert(
                            f"Erro: Layout para '{clean_path}' retornou vazio.", color="warning"
                        )

                    return layout_content
                except Exception as layout_error:
                    log.error(
                        f"Erro ao executar a função de layout para '{clean_path}': {layout_error}",
                        exc_info=True,
                    )
                    print(
                        f"[ERROR] Erro ao executar a função de layout para '{clean_path}': {layout_error}"
                    )
                    print(traceback.format_exc())
                    return dbc.Alert(
                        f"Erro ao carregar layout para {clean_path}: {layout_error}", color="danger"
                    )  # Show error in UI
            else:
                log.warning(f"Nenhuma função de layout encontrada para a rota válida: {clean_path}")
                print(f"[WARN] Nenhuma função de layout encontrada para rota válida: {clean_path}")

        # Página 404 melhorada com botão para retornar à página inicial
        log.warning(f"URL não mapeada: '{clean_path}', exibindo página 404")
        return html.Div(
            [
                html.Div(
                    [
                        html.H1("404 - Página Não Encontrada", className="text-danger mb-4"),
                        html.P(
                            f"O caminho '{pathname}' não corresponde a nenhuma seção conhecida.",
                            className="mb-4",
                        ),
                        dbc.Button(
                            "Voltar para a Página Inicial",
                            id="return-home-button",
                            color="primary",
                            href=f"/{ROUTE_HOME}",
                            className="mt-3",
                        ),
                    ],
                    className="text-center",
                )
            ],
            style={
                "padding": "50px",
                "maxWidth": "600px",
                "margin": "0 auto",
                "marginTop": "50px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "10px",
                "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
            },
        )

    except Exception as e:
        log.error(f"ERRO CRÍTICO no callback render_content: {e}")
        log.error(traceback.format_exc())

        return html.Div(
            [
                html.H4("Erro ao carregar conteúdo da página", style={"color": "red"}),
                html.P(f"Ocorreu um erro inesperado ao tentar carregar a seção para: {pathname}"),
                html.P(f"Detalhe do erro: {str(e)}"),
                html.Pre(traceback.format_exc(), style={"fontSize": "small", "overflowX": "auto"}),
            ],
            style={"padding": "20px"},
        )


# Callback para atualizar o estilo do link ativo na sidebar
@dash.callback(
    [Output(f"nav-container-{route}", "style") for route in VALID_ROUTES], Input("url", "pathname")
)
def update_active_link_style(pathname):
    """
    Atualiza o estilo do link ativo na sidebar.

    Args:
        pathname (str): O pathname atual

    Returns:
        list: Lista de estilos para cada link na sidebar
    """
    try:
        # Normaliza o pathname
        clean_path = normalize_pathname(pathname)

        # Se o pathname for vazio ou '/', usa a rota padrão
        if not clean_path or clean_path == "/":
            clean_path = ROUTE_HOME

        # Cria uma lista de estilos para cada link
        styles = []
        for route in VALID_ROUTES:
            # Estilo padrão (link inativo)
            style = {}

            # Se o link corresponder à rota atual, aplica o estilo de link ativo
            if route == clean_path:
                style = {
                    "backgroundColor": COLORS["primary"],
                    "borderLeft": f"3px solid {COLORS['accent']}",
                    "fontWeight": "bold",
                    "color": "white",
                    "fontSize": "0.75rem",
                    "boxShadow": "0 1px 3px rgba(0,0,0,0.2)",
                }

            styles.append(style)

        return styles
    except Exception as e:
        log.error(f"Erro ao atualizar estilo do link ativo: {e}")
        # Retorna estilos vazios em caso de erro
        return [{} for _ in VALID_ROUTES]


# Callback para mostrar informações de callbacks
@dash.callback(
    Output("callback-info-panel", "children"),
    Output("callback-info-panel", "style"),
    Input("url", "pathname"),
    Input("url", "search"),
)
def show_callback_info(pathname, search):
    """
    Mostra informações sobre os callbacks do módulo atual.

    Args:
        pathname (str): O pathname atual
        search (str): A parte de consulta da URL

    Returns:
        tuple: (conteúdo do painel, estilo do painel)
    """
    try:
        # Verifica se a URL contém o parâmetro ?show_callbacks=true
        show_callbacks = "show_callbacks=true" in (search or "")

        if not show_callbacks:
            # Se não estiver mostrando callbacks, esconde o painel
            return None, {"display": "none"}

        # Importa o analisador de callbacks
        from utils.callback_analyzer import format_module_info_html, get_module_info_by_pathname

        # Obtém informações do módulo
        module_info = get_module_info_by_pathname(pathname)

        # Formata as informações como HTML
        html_content = format_module_info_html(module_info)

        # Retorna o conteúdo e o estilo do painel
        return html.Div(
            [
                html.H3("Informações de Callbacks", className="mb-3"),
                html.Div(
                    [
                        html.Div(
                            html.A("Fechar", href=pathname, className="btn btn-sm btn-danger"),
                            className="mb-3",
                        ),
                        html.Div(
                            html.Iframe(
                                srcDoc=html_content,
                                style={"border": "none", "width": "100%", "height": "70vh"},
                            )
                        ),
                    ],
                    className="p-3",
                ),
            ],
            className="bg-light text-dark p-3 rounded",
        ), {
            "display": "block",
            "position": "fixed",
            "top": "70px",
            "right": "20px",
            "width": "600px",
            "maxHeight": "80vh",
            "overflowY": "auto",
            "zIndex": "1000",
            "backgroundColor": "#f8f9fa",
            "border": "1px solid #ddd",
            "borderRadius": "5px",
            "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
        }

    except Exception as e:
        log.error(f"Erro ao mostrar informações de callbacks: {e}")
        return html.Div(f"Erro ao mostrar informações de callbacks: {str(e)}"), {
            "display": "block",
            "position": "fixed",
            "top": "70px",
            "right": "20px",
            "width": "400px",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "padding": "10px",
            "borderRadius": "5px",
            "zIndex": "1000",
        }


# A importação em app.py já deve registrar este callback.
