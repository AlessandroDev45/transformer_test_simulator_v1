"""
Callbacks para o módulo de gerenciamento de normas técnicas.
"""
import base64
import datetime
import json
import logging
import multiprocessing
import os
import subprocess
import sys

import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate

# Importar funções do banco de dados
from utils.standards_db import delete_standard, get_all_standards_metadata, update_processing_status

# Configurar logger
log = logging.getLogger(__name__)


def register_standards_management_callbacks(app):
    """
    Registra os callbacks para o módulo de gerenciamento de normas técnicas.

    Args:
        app: Instância da aplicação Dash
    """
    log.info("Registrando callbacks para o módulo de gerenciamento de normas")

    # Usar um Store para comunicação entre callbacks em vez de depender do output visual
    @app.callback(
        Output("existing-standards-list", "children"),
        [Input("url", "pathname"), Input("standards-processing-status-store", "data")],
        prevent_initial_call=False,
    )
    def populate_existing_standards(pathname, processing_status):
        """Popula a lista de normas existentes."""
        if not pathname or not pathname.endswith("/gerenciar-normas"):
            raise PreventUpdate

        # O status de processamento é usado apenas para acionar o callback
        # quando uma ação é realizada

        try:
            # Obter todas as normas (incluindo as em processamento)
            standards = get_all_standards_metadata()

            if not standards:
                return html.Div("Nenhuma norma cadastrada", className="text-muted p-3")

            # Agrupar por status
            standards_by_status = {"completed": [], "processing": [], "pending": [], "error": []}

            for std in standards:
                status = std.get("processing_status", "pending")
                if status not in standards_by_status:
                    standards_by_status[status] = []
                standards_by_status[status].append(std)

            # Criar tabela de normas
            items = []

            # Normas concluídas
            if standards_by_status["completed"]:
                items.append(html.H5("Normas Disponíveis", className="mt-3 mb-2"))
                items.append(
                    dbc.Table(
                        [
                            html.Thead(
                                [
                                    html.Tr(
                                        [
                                            html.Th("Norma"),
                                            html.Th("Título"),
                                            html.Th("Ano"),
                                            html.Th("Ações"),
                                        ]
                                    )
                                ]
                            ),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(
                                                f"{std.get('organization', '')} {std.get('standard_number', 'N/A')}"
                                            ),
                                            html.Td(std.get("title", "")),
                                            html.Td(std.get("year", "")),
                                            html.Td(
                                                [
                                                    dbc.Button(
                                                        html.I(className="fas fa-trash"),
                                                        id={
                                                            "type": "delete-standard-btn",
                                                            "index": std["id"],
                                                        },
                                                        color="danger",
                                                        size="sm",
                                                        className="me-1",
                                                        title="Excluir norma",
                                                    ),
                                                    dbc.Button(
                                                        html.I(className="fas fa-eye"),
                                                        href=f"/consulta-normas?standard={std['id']}",
                                                        color="primary",
                                                        size="sm",
                                                        title="Visualizar norma",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    )
                                    for std in sorted(
                                        standards_by_status["completed"],
                                        key=lambda x: (
                                            x.get("organization", ""),
                                            x.get("standard_number", ""),
                                        ),
                                    )
                                ]
                            ),
                        ],
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size="sm",
                    )
                )

            # Normas em processamento
            if standards_by_status["processing"]:
                items.append(html.H5("Normas em Processamento", className="mt-4 mb-2"))
                items.append(
                    dbc.Table(
                        [
                            html.Thead(
                                [html.Tr([html.Th("Norma"), html.Th("Título"), html.Th("Status")])]
                            ),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(
                                                f"{std.get('organization', '')} {std.get('standard_number', 'N/A')}"
                                            ),
                                            html.Td(std.get("title", "")),
                                            html.Td(
                                                dbc.Spinner(
                                                    size="sm", color="primary", type="grow"
                                                ),
                                                className="text-primary",
                                            ),
                                        ]
                                    )
                                    for std in standards_by_status["processing"]
                                ]
                            ),
                        ],
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size="sm",
                    )
                )

            # Normas com erro
            if standards_by_status["error"]:
                items.append(html.H5("Normas com Erro", className="mt-4 mb-2"))
                items.append(
                    dbc.Table(
                        [
                            html.Thead(
                                [
                                    html.Tr(
                                        [
                                            html.Th("Norma"),
                                            html.Th("Título"),
                                            html.Th("Erro"),
                                            html.Th("Ações"),
                                        ]
                                    )
                                ]
                            ),
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td(
                                                f"{std.get('organization', '')} {std.get('standard_number', 'N/A')}"
                                            ),
                                            html.Td(std.get("title", "")),
                                            html.Td(std.get("error_message", "Erro desconhecido")),
                                            html.Td(
                                                dbc.Button(
                                                    html.I(className="fas fa-redo"),
                                                    id={
                                                        "type": "retry-standard-btn",
                                                        "index": std["id"],
                                                    },
                                                    color="warning",
                                                    size="sm",
                                                    title="Tentar novamente",
                                                )
                                            ),
                                        ]
                                    )
                                    for std in standards_by_status["error"]
                                ]
                            ),
                        ],
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size="sm",
                    )
                )

            return items

        except Exception as e:
            log.exception(f"Erro ao popular lista de normas existentes: {e}")
            return html.Div(f"Erro ao carregar normas: {str(e)}", className="text-danger p-3")

    @app.callback(
        Output("upload-standard-info", "children"),
        [Input("upload-standard-pdf", "contents")],
        [State("upload-standard-pdf", "filename")],
    )
    def display_upload_info(contents, filename):
        """Exibe informações sobre o arquivo PDF carregado."""
        if not contents or not filename:
            return ""

        if not filename.lower().endswith(".pdf"):
            return html.Div("Apenas arquivos PDF são aceitos", className="text-danger")

        # Exibir informações do arquivo
        return html.Div(
            [
                html.I(className="fas fa-file-pdf me-2"),
                html.Span(f"Arquivo selecionado: {filename}"),
            ],
            className="text-success",
        )

    # Callback unificado para atualizar tanto o display quanto o store
    @app.callback(
        [
            Output("processing-status-display", "children"),
            Output("standards-processing-status-store", "data"),
        ],
        [
            Input("process-standard-button", "n_clicks"),
            Input({"type": "delete-standard-btn", "index": ALL}, "n_clicks"),
            Input({"type": "retry-standard-btn", "index": ALL}, "n_clicks"),
        ],
        [
            State("upload-standard-pdf", "contents"),
            State("upload-standard-pdf", "filename"),
            State("standard-title-input", "value"),
            State("standard-number-input", "value"),
            State("standard-organization-input", "value"),
            State("standard-year-input", "value"),
            State("standard-categories-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def process_standard_action(
        n_clicks,
        delete_clicks,
        retry_clicks,
        contents,
        filename,
        title,
        number,
        organization,
        year,
        categories,
    ):
        """Processa ações relacionadas às normas (adicionar, excluir, reprocessar)."""
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered_id

        # Ação de exclusão
        if isinstance(trigger_id, dict) and trigger_id.get("type") == "delete-standard-btn":
            standard_id = trigger_id.get("index")
            if not standard_id:
                return dbc.Alert("ID da norma não especificado", color="danger")

            try:
                # Excluir norma
                success = delete_standard(standard_id)

                if success:
                    # Excluir arquivos
                    standard_dir = os.path.join("assets", "standards_data", standard_id)
                    if os.path.exists(standard_dir):
                        import shutil

                        shutil.rmtree(standard_dir)

                    status = dbc.Alert("Norma excluída com sucesso", color="success")
                    action_data = {
                        "action": "delete",
                        "id": standard_id,
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                    return status, action_data
                else:
                    status = dbc.Alert("Erro ao excluir norma", color="danger")
                    action_data = {
                        "action": "error",
                        "error": "delete_failed",
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                    return status, action_data

            except Exception as e:
                log.exception(f"Erro ao excluir norma {standard_id}: {e}")
                status = dbc.Alert(f"Erro ao excluir norma: {str(e)}", color="danger")
                action_data = {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

        # Ação de reprocessamento
        elif isinstance(trigger_id, dict) and trigger_id.get("type") == "retry-standard-btn":
            standard_id = trigger_id.get("index")
            if not standard_id:
                return dbc.Alert("ID da norma não especificado", color="danger")

            try:
                # Atualizar status para "pending"
                success = update_processing_status(standard_id, "pending")

                if success:
                    status = dbc.Alert(
                        "Norma marcada para reprocessamento. Faça o upload do PDF novamente.",
                        color="warning",
                    )
                    action_data = {
                        "action": "retry",
                        "id": standard_id,
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                    return status, action_data
                else:
                    status = dbc.Alert("Erro ao atualizar status da norma", color="danger")
                    action_data = {
                        "action": "error",
                        "error": "update_failed",
                        "timestamp": datetime.datetime.now().isoformat(),
                    }
                    return status, action_data

            except Exception as e:
                log.exception(f"Erro ao atualizar status da norma {standard_id}: {e}")
                status = dbc.Alert(f"Erro ao atualizar status: {str(e)}", color="danger")
                action_data = {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

        # Ação de processamento
        elif trigger_id == "process-standard-button":
            if not n_clicks:
                raise PreventUpdate

            # Validar inputs
            if not contents:
                status = dbc.Alert("Nenhum arquivo selecionado", color="danger")
                action_data = {
                    "action": "error",
                    "error": "no_file",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            if not filename or not filename.lower().endswith(".pdf"):
                status = dbc.Alert("Apenas arquivos PDF são aceitos", color="danger")
                action_data = {
                    "action": "error",
                    "error": "invalid_file",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            if not title or not title.strip():
                status = dbc.Alert("Título da norma é obrigatório", color="danger")
                action_data = {
                    "action": "error",
                    "error": "missing_title",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            if not number or not number.strip():
                status = dbc.Alert("Número da norma é obrigatório", color="danger")
                action_data = {
                    "action": "error",
                    "error": "missing_number",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            if not organization or not organization.strip():
                status = dbc.Alert("Organização é obrigatória", color="danger")
                action_data = {
                    "action": "error",
                    "error": "missing_organization",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            if not year or not str(year).isdigit():
                status = dbc.Alert("Ano de publicação inválido", color="danger")
                action_data = {
                    "action": "error",
                    "error": "invalid_year",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

            # Processar categorias
            if categories and categories.strip():
                categories_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
            else:
                categories_list = []

            try:
                # Decodificar conteúdo do PDF
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)

                # Criar ID seguro para a norma
                from utils.standards_db import create_safe_id

                standard_id = create_safe_id(number.strip(), organization.strip())

                # Verificar se a norma já está em processamento
                try:
                    import sqlite3

                    conn = sqlite3.connect(
                        os.path.join(
                            os.path.dirname(os.path.dirname(__file__)), "data", "standards.db"
                        )
                    )
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT processing_status FROM standards_metadata WHERE id = ?",
                        (standard_id,),
                    )
                    result = cursor.fetchone()
                    conn.close()

                    if result and result[0] == "processing":
                        status = dbc.Alert(
                            "Esta norma já está em processamento. Aguarde a conclusão.",
                            color="warning",
                        )
                        action_data = {
                            "action": "error",
                            "error": "already_processing",
                            "timestamp": datetime.datetime.now().isoformat(),
                        }
                        return status, action_data
                except Exception as db_err:
                    log.warning(f"Erro ao verificar status da norma no banco de dados: {db_err}")

                # Salvar PDF em pasta temporária usando tempfile para garantir nome único
                temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
                os.makedirs(temp_dir, exist_ok=True)

                # Usar nome de arquivo seguro com timestamp para evitar colisões
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                safe_filename = f"{standard_id}_{timestamp}.pdf"
                pdf_temp_path = os.path.join(temp_dir, safe_filename)

                # Criar arquivo de bloqueio para indicar que este arquivo está em uso
                lock_file = f"{pdf_temp_path}.lock"
                with open(lock_file, "w") as f:
                    f.write(f"Processing started at {datetime.datetime.now().isoformat()}")

                # Salvar o PDF
                with open(pdf_temp_path, "wb") as f:
                    f.write(decoded)

                log.info(f"Arquivo PDF salvo em: {pdf_temp_path}")

                # Preparar metadados
                metadata_dict = {
                    "title": title.strip(),
                    "standard_number": number.strip(),
                    "organization": organization.strip(),
                    "year": int(year),
                    "categories": categories_list,
                }

                # Definir caminhos
                output_base = "assets/standards_data"
                # Usar o script atualizado para Docling 2.31.0
                script_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "scripts", "process_standard.py"
                )

                # Verificar se o Docling está instalado
                try:
                    import importlib

                    docling_spec = importlib.util.find_spec("docling")
                    use_fallback = docling_spec is None
                    if use_fallback:
                        log.warning("Docling não está instalado. Usando processador simplificado.")
                except ImportError:
                    use_fallback = True
                    log.warning(
                        "Não foi possível verificar se Docling está instalado. Usando processador simplificado."
                    )

                # Preparar argumentos
                args_list = [
                    sys.executable,  # Garante que use o mesmo python
                    script_path,
                    "--pdf",
                    pdf_temp_path,
                    "--metadata",
                    json.dumps(metadata_dict),
                    "--output",
                    output_base,
                ]

                # Adicionar flag de fallback se necessário
                if use_fallback:
                    args_list.append("--fallback")
                    log.info("Adicionando flag --fallback para usar processador simplificado")

                # Iniciar processo em background
                try:
                    log.info(f"Iniciando processo background: {' '.join(args_list)}")
                    process = multiprocessing.Process(target=run_script, args=(args_list,))
                    process.start()
                    status_message = "Processamento iniciado em background..."
                    if use_fallback:
                        status_message += " (usando processador simplificado)"
                except Exception as start_err:
                    log.error(f"Erro ao iniciar processo background: {start_err}", exc_info=True)
                    status_message = f"Erro ao iniciar processamento: {start_err}"

                # Criar ID seguro para a norma
                from utils.standards_db import create_safe_id

                standard_id = create_safe_id(number.strip(), organization.strip())

                # Atualizar a lista de normas
                try:
                    # Notificar que o processamento foi iniciado
                    # Isso será feito em um callback separado
                    pass
                except Exception as notify_err:
                    log.error(f"Erro ao notificar processamento: {notify_err}")

                status = dbc.Alert(
                    [html.I(className="fas fa-cog fa-spin me-2"), html.Span(status_message)],
                    color="info",
                )

                # Criar ID seguro para a norma
                from utils.standards_db import create_safe_id

                standard_id = create_safe_id(number.strip(), organization.strip())

                action_data = {
                    "action": "process",
                    "id": standard_id,
                    "title": title.strip(),
                    "number": number.strip(),
                    "organization": organization.strip(),
                    "year": int(year),
                    "timestamp": datetime.datetime.now().isoformat(),
                }

                return status, action_data

            except Exception as e:
                log.exception(f"Erro ao processar norma: {e}")
                status = dbc.Alert(f"Erro ao processar norma: {str(e)}", color="danger")
                action_data = {
                    "action": "error",
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                return status, action_data

        # Se chegou aqui, nenhum trigger foi reconhecido
        status = dbc.Alert("Nenhuma ação reconhecida", color="warning")
        action_data = {"action": "none", "timestamp": datetime.datetime.now().isoformat()}
        return status, action_data


def run_script(args):
    """
    Função auxiliar para executar o script de processamento em background.

    Args:
        args: Lista de argumentos para o script
    """
    try:
        # Verificar se o arquivo PDF existe
        pdf_path = args[args.index("--pdf") + 1]
        if not os.path.exists(pdf_path):
            logging.error(f"Arquivo PDF não encontrado: {pdf_path}")
            return

        # Verificar se o arquivo de bloqueio existe
        lock_file = f"{pdf_path}.lock"
        if not os.path.exists(lock_file):
            # Criar arquivo de bloqueio se não existir
            with open(lock_file, "w") as f:
                f.write(f"Processing started at {datetime.datetime.now().isoformat()}")

        # Usar Popen para não esperar o término aqui
        process = subprocess.Popen(args)
        logging.info(f"Processo {args[1]} iniciado com sucesso. PID: {process.pid}")

        # Registrar o PID no arquivo de bloqueio
        with open(lock_file, "a") as f:
            f.write(f"\nPID: {process.pid}")

    except Exception as run_err:
        logging.error(f"Erro ao executar script {args[1]}: {run_err}", exc_info=True)

        # Remover arquivo de bloqueio em caso de erro
        try:
            pdf_path = args[args.index("--pdf") + 1]
            lock_file = f"{pdf_path}.lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
                logging.info(f"Arquivo de bloqueio removido: {lock_file}")
        except Exception as lock_err:
            logging.warning(f"Erro ao remover arquivo de bloqueio: {lock_err}")
