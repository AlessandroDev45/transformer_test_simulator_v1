#!/usr/bin/env python
"""
Script para processamento de PDFs de normas técnicas em segundo plano.
Converte PDFs para Markdown usando Docling, preservando imagens e tabelas.
Baseado na documentação oficial: https://github.com/docling-project/docling
"""

# Versão do script para depuração
SCRIPT_VERSION = "1.3 - Implementação oficial Docling 2.31.0"
import argparse
import json
import logging
import os
import shutil
import sys
import threading
import time

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "standards_processing.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("standards_processor")

# Adicionar o diretório raiz ao path para importar módulos do projeto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Diretório temporário para arquivos
temp_dir = os.path.join(project_root, "temp")
os.makedirs(temp_dir, exist_ok=True)

# Timeout para processamento (em segundos)
PROCESSING_TIMEOUT = 300  # 5 minutos


class TimeoutError(Exception):
    """Exceção para timeout."""

    pass


class ProcessTimeout:
    """Classe para gerenciar timeout de processamento."""

    def __init__(self, seconds, error_message="Timeout excedido"):
        self.seconds = seconds
        self.error_message = error_message
        self.timer = None

    def handle_timeout(self):
        """Manipulador de timeout."""
        raise TimeoutError(self.error_message)

    def __enter__(self):
        """Inicia o timer quando o contexto é iniciado."""
        self.timer = threading.Timer(self.seconds, self.handle_timeout)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cancela o timer quando o contexto é finalizado."""
        if self.timer:
            self.timer.cancel()


def cleanup_temp_files(standard_id, current_pdf=None):
    """
    Limpa arquivos temporários relacionados a uma norma.

    Args:
        standard_id: ID da norma
        current_pdf: Caminho do arquivo PDF atual que não deve ser removido
    """
    try:
        # Limpar arquivos temporários no diretório temp
        for file in os.listdir(temp_dir):
            if standard_id.lower() in file.lower():
                file_path = os.path.join(temp_dir, file)

                # Verificar se é um arquivo de bloqueio
                if file_path.endswith(".lock"):
                    # Não remover arquivos de bloqueio de arquivos em uso
                    if os.path.exists(file_path[:-5]):  # Caminho do PDF sem o .lock
                        logger.debug(
                            f"Ignorando arquivo de bloqueio para arquivo em uso: {file_path}"
                        )
                        continue
                    else:
                        # Se o PDF não existe mais, podemos remover o arquivo de bloqueio
                        try:
                            os.remove(file_path)
                            logger.info(f"Arquivo de bloqueio órfão removido: {file_path}")
                        except Exception as e:
                            logger.warning(
                                f"Não foi possível remover arquivo de bloqueio: {file_path}: {e}"
                            )
                        continue

                # Não remover o arquivo que está sendo processado atualmente
                if current_pdf and os.path.normpath(file_path) == os.path.normpath(current_pdf):
                    logger.debug(f"Ignorando arquivo atual em processamento: {file_path}")
                    continue

                # Verificar se existe um arquivo de bloqueio para este arquivo
                lock_file = f"{file_path}.lock"
                if os.path.exists(lock_file):
                    logger.debug(f"Ignorando arquivo com bloqueio ativo: {file_path}")
                    continue

                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Arquivo temporário removido: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        logger.info(f"Diretório temporário removido: {file_path}")
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo temporário {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Erro ao limpar arquivos temporários: {e}")


# Importar funções do banco de dados
try:
    from utils.standards_db import (
        add_or_update_standard_metadata,
        index_standard_content,
        update_processing_status,
    )
except ImportError as e:
    logger.error(f"Erro ao importar módulos do projeto: {e}")
    sys.exit(1)


def create_safe_id(standard_number, organization):
    """
    Cria um ID seguro para a norma a partir do número e organização.

    Args:
        standard_number: Número da norma (ex: "NBR 5356-3")
        organization: Organização (ex: "ABNT")

    Returns:
        ID seguro para uso em nomes de arquivos e URLs
    """
    # Remover caracteres especiais e espaços
    safe_id = f"{organization}_{standard_number}".lower()
    safe_id = safe_id.replace(" ", "_")
    safe_id = safe_id.replace("/", "_")
    safe_id = safe_id.replace("\\", "_")
    safe_id = safe_id.replace(":", "_")
    safe_id = safe_id.replace(";", "_")
    safe_id = safe_id.replace(".", "_")
    safe_id = safe_id.replace("-", "_")
    safe_id = safe_id.replace(",", "_")
    safe_id = safe_id.replace("(", "")
    safe_id = safe_id.replace(")", "")

    # Remover underscores duplicados
    while "__" in safe_id:
        safe_id = safe_id.replace("__", "_")

    return safe_id


def process_pdf(pdf_path, metadata, output_base):
    """
    Processa um PDF de norma técnica usando Docling.

    Args:
        pdf_path: Caminho do arquivo PDF
        metadata: Dicionário com metadados da norma
        output_base: Diretório base para saída

    Returns:
        Tuple[bool, str, str]: (sucesso, mensagem, caminho_markdown)
    """
    try:
        # Log da versão do script para depuração
        logger.info(f"Executando script versão: {SCRIPT_VERSION}")

        # Verificar se o Docling está instalado
        try:
            # Tentativa de importar docling para verificar se está instalado
            import importlib

            importlib.import_module("docling")
            logger.info("Biblioteca Docling está instalada")
        except ImportError:
            logger.error("Biblioteca Docling não está instalada. Instale com: pip install docling")
            return False, "Biblioteca Docling não está instalada", None

        # Criar ID seguro para a norma
        standard_id = create_safe_id(metadata["standard_number"], metadata["organization"])
        logger.info(f"ID seguro criado para a norma: {standard_id}")

        # Definir caminhos de saída
        norma_output_dir = os.path.join(output_base, standard_id)
        images_output_dir = os.path.join(norma_output_dir, "images")
        markdown_output_path = os.path.join(norma_output_dir, "content.md")

        # Criar diretórios de saída
        os.makedirs(norma_output_dir, exist_ok=True)
        os.makedirs(images_output_dir, exist_ok=True)

        # Atualizar status no banco de dados
        update_processing_status(standard_id, "processing")

        # Configurar Docling
        logger.info(f"Iniciando processamento do PDF: {pdf_path}")

        # Verificar se GPU está disponível
        use_gpu = False
        try:
            import torch

            use_gpu = torch.cuda.is_available()
            logger.info(f"GPU disponível: {use_gpu}")
        except ImportError:
            logger.warning("PyTorch não está instalado. Usando CPU.")

        # Verificar se pytesseract está instalado
        try:
            import pytesseract

            # Definir caminho do Tesseract (ajuste conforme a localização na sua máquina)
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                logger.info(f"Caminho do Tesseract definido: {tesseract_path}")
            else:
                logger.warning(f"Caminho do Tesseract não encontrado: {tesseract_path}")
                # Tentar caminhos alternativos
                alt_paths = [
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    r"C:\Users\Administrator\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
                    r"C:\Users\Administrator\AppData\Local\Tesseract-OCR\tesseract.exe",
                ]
                for path in alt_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Caminho alternativo do Tesseract definido: {path}")
                        break
        except ImportError:
            logger.warning("pytesseract não está instalado. Instale com: pip install pytesseract")

        # Processar o PDF com Docling
        # Seguindo a documentação oficial: https://github.com/docling-project/docling
        try:
            # Verificar se o Docling está instalado
            try:
                from docling.document_converter import DocumentConverter

                logger.info("Biblioteca Docling encontrada")
            except ImportError:
                logger.error(
                    "Biblioteca Docling não está instalada. Instale com: pip install docling"
                )
                return False, "Biblioteca Docling não está instalada", None

            # Criar o conversor com configurações padrão conforme documentação oficial
            parser = DocumentConverter()
            logger.info("DocumentConverter inicializado com sucesso")

        except Exception as e:
            logger.error(f"Não foi possível inicializar o Docling: {e}")
            return False, f"Não foi possível inicializar o Docling: {e}", None

        # Registrar início do processamento
        start_time = time.time()
        logger.info(f"Iniciando processamento Docling para {pdf_path}")

        # Processar o PDF seguindo a documentação oficial
        try:
            # Usar timeout para evitar processamento infinito
            with ProcessTimeout(PROCESSING_TIMEOUT, f"Timeout excedido ao processar {pdf_path}"):
                # Converter o PDF para um documento Docling
                logger.info("Convertendo PDF para Docling Document")
                result = parser.convert(pdf_path)

                if not result or not result.document:
                    raise ValueError("A conversão não retornou um documento válido")

                # Exportar para Markdown conforme documentação oficial
                logger.info("Exportando para Markdown")
                markdown_content = result.document.export_to_markdown()

                # Salvar o conteúdo Markdown
                with open(markdown_output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                # Tentar exportar imagens se disponíveis
                try:
                    logger.info("Verificando imagens no documento")
                    has_figures = False

                    # Verificar se o documento tem páginas com figuras
                    if hasattr(result.document, "pages"):
                        for page in result.document.pages:
                            if hasattr(page, "figures") and page.figures:
                                has_figures = True
                                break

                    if has_figures:
                        logger.info(f"Exportando imagens para {images_output_dir}")
                        # Usar o método export_figures se disponível
                        if hasattr(result.document, "export_figures"):
                            result.document.export_figures(images_output_dir)
                        # Tentar método alternativo se o primeiro não estiver disponível
                        elif hasattr(result.document, "export_images"):
                            result.document.export_images(images_output_dir)
                        else:
                            logger.warning("Métodos de exportação de imagens não disponíveis")
                    else:
                        logger.info("Nenhuma imagem encontrada no documento")
                except Exception as img_err:
                    logger.warning(f"Erro ao exportar imagens: {img_err}")

                logger.info("Conversão e exportação concluídas com sucesso")
        except TimeoutError as timeout_err:
            logger.error(f"Timeout excedido durante o processamento: {timeout_err}")
            # Criar um arquivo Markdown mínimo para evitar falhas
            minimal_content = f"""# {metadata['title']}

**Norma:** {metadata['standard_number']}
**Organização:** {metadata['organization']}
**Ano:** {metadata['year']}
**Categorias:** {', '.join(metadata['categories'])}

---

O processamento desta norma foi interrompido devido a um timeout.
Por favor, tente novamente ou contate o administrador do sistema.
"""
            with open(markdown_output_path, "w", encoding="utf-8") as f:
                f.write(minimal_content)
            markdown_content = minimal_content

            # Continuar o processamento com o conteúdo mínimo
            logger.warning("Continuando com conteúdo mínimo devido ao timeout")
        except Exception as e:
            logger.error(f"Erro ao processar o PDF com Docling: {e}")
            return False, f"Erro ao processar o PDF: {e}", None

        # Registrar tempo de processamento
        elapsed_time = time.time() - start_time
        logger.info(f"Processamento concluído em {elapsed_time:.2f} segundos")

        # Verificar se o arquivo Markdown foi criado
        if not os.path.exists(markdown_output_path):
            logger.error(f"Arquivo Markdown não foi criado: {markdown_output_path}")
            return False, "Falha ao gerar arquivo Markdown", None

        # Ler o conteúdo Markdown gerado (se ainda não tivermos o conteúdo)
        if "markdown_content" not in locals():
            with open(markdown_output_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()

        # Adicionar cabeçalho com metadados ao Markdown
        header = f"""# {metadata['title']}

**Norma:** {metadata['standard_number']}
**Organização:** {metadata['organization']}
**Ano:** {metadata['year']}
**Categorias:** {', '.join(metadata['categories'])}

---

"""

        # Atualizar o arquivo com o cabeçalho
        with open(markdown_output_path, "w", encoding="utf-8") as f:
            f.write(header + markdown_content)

        # Caminho relativo para o banco de dados
        relative_md_path = os.path.join("standards_data", standard_id, "content.md")

        # Copiar o arquivo para o diretório assets/standards_data/
        assets_dir = os.path.join(project_root, "assets", "standards_data", standard_id)
        assets_md_path = os.path.join(assets_dir, "content.md")

        try:
            # Criar diretório se não existir
            os.makedirs(assets_dir, exist_ok=True)

            # Copiar arquivo
            shutil.copy2(markdown_output_path, assets_md_path)
            logger.info(f"Arquivo Markdown copiado para: {assets_md_path}")
        except Exception as copy_err:
            logger.warning(f"Erro ao copiar arquivo para assets: {copy_err}")

        logger.info(f"Arquivo Markdown gerado: {markdown_output_path}")
        return True, "Processamento concluído com sucesso", relative_md_path

    except Exception as e:
        logger.exception(f"Erro durante o processamento do PDF: {e}")
        return False, f"Erro: {str(e)}", None


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Processa PDF de norma técnica para Markdown.")
    parser.add_argument("--pdf", required=True, help="Caminho do arquivo PDF")
    parser.add_argument("--metadata", required=True, help="JSON com metadados da norma")
    parser.add_argument("--output", required=True, help="Diretório base para saída")
    parser.add_argument("--db", help="Caminho do banco de dados (opcional)")
    parser.add_argument(
        "--fallback", action="store_true", help="Usar processador simplificado em vez de Docling"
    )

    args = parser.parse_args()

    try:
        # Verificar se o arquivo PDF existe
        if not os.path.exists(args.pdf):
            logger.error(f"Arquivo PDF não encontrado: {args.pdf}")
            sys.exit(1)

        # Verificar se o diretório de saída existe
        output_base = os.path.join(project_root, args.output)
        os.makedirs(output_base, exist_ok=True)

        # Carregar metadados
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar JSON de metadados: {args.metadata}")
            sys.exit(1)

        # Validar metadados
        required_fields = ["title", "standard_number", "organization", "year", "categories"]
        for field in required_fields:
            if field not in metadata:
                logger.error(f"Campo obrigatório ausente nos metadados: {field}")
                sys.exit(1)

        # Criar ID seguro para a norma
        standard_id = create_safe_id(metadata["standard_number"], metadata["organization"])

        # Verificar se já existe uma norma com o mesmo ID em processamento
        try:
            import sqlite3

            conn = sqlite3.connect(os.path.join(project_root, "data", "standards.db"))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT processing_status FROM standards_metadata WHERE id = ?", (standard_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "processing":
                logger.warning(
                    f"Norma {standard_id} já está em processamento. Limpando arquivos temporários."
                )
                cleanup_temp_files(standard_id, args.pdf)
        except Exception as db_err:
            logger.warning(f"Erro ao verificar status da norma no banco de dados: {db_err}")

        # Limpar arquivos temporários antes de iniciar, exceto o arquivo atual
        cleanup_temp_files(standard_id, args.pdf)

        # Atualizar status no banco de dados
        update_processing_status(standard_id, "processing")

        # Verificar se devemos usar o processador simplificado
        if args.fallback:
            logger.info("Usando processador simplificado conforme solicitado")
            # Importar o processador simplificado
            try:
                simple_processor_path = os.path.join(
                    os.path.dirname(__file__), "simple_pdf_processor.py"
                )
                if not os.path.exists(simple_processor_path):
                    logger.error(
                        f"Processador simplificado não encontrado: {simple_processor_path}"
                    )
                    sys.exit(1)

                # Executar o processador simplificado como um processo separado
                import subprocess

                cmd = [
                    sys.executable,
                    simple_processor_path,
                    "--pdf",
                    args.pdf,
                    "--metadata",
                    args.metadata,
                    "--output",
                    args.output,
                ]
                logger.info(f"Executando processador simplificado: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("Processador simplificado concluído com sucesso")
                    sys.exit(0)
                else:
                    logger.error(f"Erro ao executar processador simplificado: {result.stderr}")
                    sys.exit(1)
            except Exception as e:
                logger.exception(f"Erro ao executar processador simplificado: {e}")
                sys.exit(1)

        # Processar o PDF com Docling
        success, message, md_path = process_pdf(args.pdf, metadata, output_base)

        if success:
            # Atualizar metadados no banco de dados
            add_or_update_standard_metadata(
                id=standard_id,
                title=metadata["title"],
                standard_number=metadata["standard_number"],
                organization=metadata["organization"],
                year=metadata["year"],
                categories=metadata["categories"],
                md_file_path=md_path,
                processing_status="completed",
            )

            # Indexar conteúdo para busca
            try:
                # Primeiro, tentar abrir o arquivo no caminho relativo à raiz do projeto
                full_path = os.path.join(project_root, "assets", md_path)
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        markdown_content = f.read()
                else:
                    # Se não existir, tentar abrir o arquivo no caminho absoluto
                    absolute_path = os.path.join(output_base, standard_id, "content.md")
                    if os.path.exists(absolute_path):
                        with open(absolute_path, "r", encoding="utf-8") as f:
                            markdown_content = f.read()
                    else:
                        # Se ainda não existir, usar o conteúdo que já temos em memória
                        logger.warning(
                            f"Arquivo não encontrado em {full_path} nem em {absolute_path}. Usando conteúdo em memória."
                        )
                        if "markdown_content" not in locals():
                            logger.error("Conteúdo Markdown não disponível em memória")
                            markdown_content = f"# {metadata['title']}\n\nConteúdo não disponível"
            except Exception as read_err:
                logger.warning(
                    f"Erro ao ler arquivo Markdown: {read_err}. Usando conteúdo em memória."
                )
                if "markdown_content" not in locals():
                    logger.error("Conteúdo Markdown não disponível em memória")
                    markdown_content = f"# {metadata['title']}\n\nConteúdo não disponível"

            # Indexar o conteúdo
            index_standard_content(standard_id, markdown_content)

            logger.info(f"Norma {standard_id} processada e indexada com sucesso")
        else:
            # Atualizar status de erro
            update_processing_status(standard_id, "error", message)
            logger.error(f"Falha no processamento da norma {standard_id}: {message}")

        # Remover arquivo de bloqueio se existir
        lock_file = f"{args.pdf}.lock"
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                logger.info(f"Arquivo de bloqueio removido: {lock_file}")
            except Exception as e:
                logger.warning(f"Não foi possível remover o arquivo de bloqueio: {e}")

        # Remover arquivo PDF temporário se necessário
        if args.pdf.startswith(os.path.join(project_root, "temp")):
            try:
                os.remove(args.pdf)
                logger.info(f"Arquivo PDF temporário removido: {args.pdf}")
            except Exception as e:
                logger.warning(f"Não foi possível remover o arquivo PDF temporário: {e}")

        # Limpar outros arquivos temporários (agora é seguro remover o arquivo PDF também)
        cleanup_temp_files(standard_id)

    except Exception as e:
        logger.exception(f"Erro não tratado durante o processamento: {e}")

        # Tentar remover o arquivo de bloqueio em caso de erro
        try:
            if "args" in locals() and isinstance(args, argparse.Namespace) and hasattr(args, "pdf"):
                lock_file = f"{args.pdf}.lock"
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    logger.info(f"Arquivo de bloqueio removido após erro: {lock_file}")
        except Exception as lock_err:
            logger.warning(f"Erro ao remover arquivo de bloqueio após falha: {lock_err}")

        # Tentar limpar arquivos temporários mesmo em caso de erro
        try:
            if "standard_id" in locals():
                # Agora é seguro remover todos os arquivos, incluindo o PDF
                cleanup_temp_files(standard_id)
                # Atualizar status para erro
                update_processing_status(standard_id, "error", str(e))
        except Exception as cleanup_err:
            logger.warning(f"Erro ao limpar arquivos temporários após falha: {cleanup_err}")

        sys.exit(1)


if __name__ == "__main__":
    main()
