"""
Callbacks para o módulo de consulta de normas técnicas.
"""
import logging
import os

import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate

# Importar funções do banco de dados
from utils.standards_db import (
    filter_standards_by_category,
    get_all_standards_metadata,
    get_categories_list,
    get_standard_metadata_by_id,
    search_standards_fts,
)

# Configurar logger
log = logging.getLogger(__name__)


def register_standards_consultation_callbacks(app):
    """
    Registra os callbacks para o módulo de consulta de normas técnicas.

    Args:
        app: Instância da aplicação Dash
    """
    log.info("Registrando callbacks para o módulo de consulta de normas")

    @app.callback(
        Output("standards-nav-sidebar", "children"),
        [Input("url", "pathname"), Input("standards-current-category", "data")],
    )
    def populate_standards_sidebar(pathname, current_category):
        """Popula a barra lateral com a lista de normas disponíveis."""
        if not pathname or not pathname.endswith("/consulta-normas"):
            raise PreventUpdate

        try:
            # Obter metadados das normas
            if current_category:
                standards = filter_standards_by_category(current_category)
                header = f"Normas na categoria: {current_category}"
            else:
                standards = get_all_standards_metadata(status="completed")
                header = "Todas as normas"

            if not standards:
                return html.Div("Nenhuma norma disponível", className="text-muted p-3")

            # Agrupar por organização
            standards_by_org = {}
            for std in standards:
                org = std.get("organization", "Outra")
                if org not in standards_by_org:
                    standards_by_org[org] = []
                standards_by_org[org].append(std)

            # Criar lista de normas agrupadas
            items = []

            # Adicionar cabeçalho com contagem
            items.append(html.Div(f"{header} ({len(standards)})", className="fw-bold mb-2"))

            # Adicionar normas agrupadas por organização
            for org, org_standards in sorted(standards_by_org.items()):
                # Adicionar cabeçalho da organização
                items.append(html.Div(org, className="fw-bold mt-3 mb-2 text-primary"))

                # Adicionar normas desta organização
                for std in sorted(org_standards, key=lambda x: x.get("standard_number", "")):
                    items.append(
                        dbc.Button(
                            f"{std.get('standard_number', 'N/A')}",
                            id={"type": "select-standard-btn", "index": std["id"]},
                            color="link",
                            className="text-start p-1 d-block w-100 text-truncate",
                            title=std.get("title", ""),
                            style={"textDecoration": "none"},
                        )
                    )

            return items

        except Exception as e:
            log.exception(f"Erro ao popular barra lateral de normas: {e}")
            return html.Div(f"Erro ao carregar normas: {str(e)}", className="text-danger p-3")

    @app.callback(Output("standards-categories-container", "children"), [Input("url", "pathname")])
    def populate_categories_list(pathname):
        """Popula a lista de categorias disponíveis."""
        if not pathname or not pathname.endswith("/consulta-normas"):
            raise PreventUpdate

        try:
            # Obter lista de categorias
            categories = get_categories_list()

            if not categories:
                return html.Div("Nenhuma categoria disponível", className="text-muted p-2")

            # Criar lista de categorias
            items = []
            for category in categories:
                items.append(
                    dbc.Button(
                        category,
                        id={"type": "select-category-btn", "index": category},
                        color="light",
                        outline=True,
                        size="sm",
                        className="m-1",
                    )
                )

            # Adicionar botão para limpar filtro
            items.append(
                dbc.Button(
                    "Todas",
                    id="clear-category-filter",
                    color="secondary",
                    outline=True,
                    size="sm",
                    className="m-1",
                )
            )

            return items

        except Exception as e:
            log.exception(f"Erro ao popular lista de categorias: {e}")
            return html.Div(f"Erro ao carregar categorias: {str(e)}", className="text-danger p-2")

    @app.callback(
        Output("standards-current-category", "data"),
        [
            Input({"type": "select-category-btn", "index": ALL}, "n_clicks"),
            Input("clear-category-filter", "n_clicks"),
        ],
    )
    def update_selected_category(category_clicks, clear_clicks):
        """Atualiza a categoria selecionada."""
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered_id

        # Se o botão "Todas" foi clicado
        if trigger_id == "clear-category-filter":
            return None

        # Se um botão de categoria foi clicado
        if isinstance(trigger_id, dict) and trigger_id.get("type") == "select-category-btn":
            return trigger_id.get("index")

        raise PreventUpdate

    @app.callback(
        [
            Output("standards-metadata-display", "children"),
            Output("standards-content-display", "children"),
            Output("standards-viewer-title", "children"),
            Output("standards-current-standard", "data"),
        ],
        [
            Input({"type": "select-standard-btn", "index": ALL}, "n_clicks"),
            Input({"type": "search-result-btn", "index": ALL}, "n_clicks"),
        ],
        [State("standards-current-search", "data"), State("standards-current-standard", "data")],
    )
    def display_standard_content(
        std_clicks, search_result_clicks, current_search, current_standard
    ):
        """Exibe o conteúdo da norma selecionada."""
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered_id

        # Determinar o ID da norma a ser exibida
        standard_id = None

        if isinstance(trigger_id, dict):
            if trigger_id.get("type") == "select-standard-btn":
                standard_id = trigger_id.get("index")
            elif trigger_id.get("type") == "search-result-btn":
                standard_id = trigger_id.get("index")

        if not standard_id:
            raise PreventUpdate

        try:
            # Obter metadados da norma
            metadata = get_standard_metadata_by_id(standard_id)
            if not metadata:
                return (
                    html.Div("Norma não encontrada", className="text-danger"),
                    "Norma não encontrada ou não processada corretamente.",
                    "Erro",
                    None,
                )

            # Obter caminho do arquivo Markdown
            md_path = metadata.get("md_file_path")
            if not md_path:
                return (
                    html.Div("Arquivo Markdown não encontrado", className="text-danger"),
                    "Conteúdo da norma não disponível.",
                    "Erro",
                    None,
                )

            # Caminho completo do arquivo
            full_path = os.path.join("assets", md_path)
            if not os.path.exists(full_path):
                return (
                    html.Div(f"Arquivo não encontrado: {md_path}", className="text-danger"),
                    "Arquivo da norma não encontrado no servidor.",
                    "Erro",
                    None,
                )

            # Ler conteúdo do arquivo
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Se houver um termo de busca ativo, destacar no conteúdo
            if current_search:
                search_term = current_search.lower()
                # Substituir o termo de busca por uma versão destacada
                # Isso é simplificado e pode não funcionar perfeitamente para todos os casos
                content = content.replace(
                    search_term, f'<span class="search-highlight">{search_term}</span>'
                )

            # Criar exibição de metadados
            metadata_display = dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(metadata.get("title", "Sem título"), className="card-title"),
                            html.Div(
                                [
                                    html.Span(
                                        f"{metadata.get('organization', 'N/A')} ",
                                        className="fw-bold",
                                    ),
                                    html.Span(
                                        f"{metadata.get('standard_number', 'N/A')} ",
                                        className="text-primary",
                                    ),
                                    html.Span(f"({metadata.get('year', 'N/A')})"),
                                ]
                            ),
                            html.Div(
                                [
                                    html.Span("Categorias: ", className="fw-bold"),
                                    html.Span(", ".join(metadata.get("categories", []))),
                                ],
                                className="mt-2",
                            ),
                        ]
                    )
                ],
                className="mb-3",
            )

            # Título para o visualizador
            viewer_title = f"Visualizador: {metadata.get('standard_number', 'Norma')}"

            return metadata_display, content, viewer_title, standard_id

        except Exception as e:
            log.exception(f"Erro ao exibir conteúdo da norma {standard_id}: {e}")
            return (
                html.Div(f"Erro ao carregar norma: {str(e)}", className="text-danger"),
                f"Ocorreu um erro ao carregar o conteúdo da norma: {str(e)}",
                "Erro",
                None,
            )

    @app.callback(
        [
            Output("standards-search-results", "children"),
            Output("standards-search-results-container", "style"),
            Output("standards-current-search", "data"),
            Output("standards-search-info", "children"),
        ],
        [Input("standards-search-button", "n_clicks")],
        [State("standards-search-input", "value")],
    )
    def search_standards(n_clicks, search_term):
        """Realiza busca nas normas técnicas."""
        if not n_clicks or not search_term or len(search_term.strip()) < 3:
            return [], {"display": "none"}, None, ""

        search_term = search_term.strip()

        try:
            # Realizar busca
            results = search_standards_fts(search_term)

            if not results:
                return (
                    html.Div("Nenhum resultado encontrado", className="text-muted p-3"),
                    {"display": "block"},
                    search_term,
                    html.Span(f"Nenhum resultado para '{search_term}'", className="text-danger"),
                )

            # Criar lista de resultados
            items = []
            for result in results:
                items.append(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H5(
                                        [
                                            html.Span(
                                                f"{result.get('organization', '')} ",
                                                className="text-muted",
                                            ),
                                            html.Span(
                                                result.get("standard_number", "N/A"),
                                                className="text-primary",
                                            ),
                                        ],
                                        className="card-title",
                                    ),
                                    html.P(result.get("title", ""), className="card-subtitle mb-2"),
                                    html.Div(
                                        [
                                            html.P(
                                                html.Span(
                                                    [html.Raw(result.get("snippet", ""))],
                                                    className="search-snippet",
                                                ),
                                                className="mb-2",
                                            ),
                                            dbc.Button(
                                                "Ver Norma",
                                                id={
                                                    "type": "search-result-btn",
                                                    "index": result.get("id"),
                                                },
                                                color="primary",
                                                size="sm",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        className="mb-3",
                    )
                )

            return (
                items,
                {"display": "block"},
                search_term,
                html.Span(
                    f"{len(results)} resultados para '{search_term}'", className="text-success"
                ),
            )

        except Exception as e:
            log.exception(f"Erro na busca por '{search_term}': {e}")
            return (
                html.Div(f"Erro na busca: {str(e)}", className="text-danger p-3"),
                {"display": "block"},
                search_term,
                html.Span(f"Erro na busca: {str(e)}", className="text-danger"),
            )

    @app.callback(
        Output("standards-fullscreen-button", "n_clicks"),
        [Input("standards-fullscreen-button", "n_clicks")],
        [State("standards-content-container", "style")],
    )
    def toggle_fullscreen(n_clicks, current_style):
        """Alterna o modo de tela cheia do visualizador."""
        if not n_clicks:
            raise PreventUpdate

        # Esta função apenas dispara o evento de clique
        # O JavaScript no cliente lidará com a alternância de tela cheia
        return n_clicks
