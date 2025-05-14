#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script simplificado para processar PDFs de normas técnicas.
Este script não depende de bibliotecas externas complexas como Docling.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "standards_processing.log"),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("standards_processor")

# Obter caminho raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Importar funções do banco de dados
try:
    from utils.standards_db import (
        add_or_update_standard_metadata,
        create_safe_id,
        index_standard_content,
        update_processing_status,
    )
except ImportError as e:
    logger.error(f"Erro ao importar funções do banco de dados: {e}")
    sys.exit(1)


def process_pdf(pdf_path, metadata, output_base):
    """
    Processa um arquivo PDF de norma técnica e gera um arquivo Markdown.

    Args:
        pdf_path: Caminho do arquivo PDF
        metadata: Dicionário com metadados da norma
        output_base: Diretório base para saída

    Returns:
        Tuple[bool, str, str]: (sucesso, mensagem, caminho_markdown)
    """
    try:
        # Criar ID seguro para a norma
        standard_id = create_safe_id(metadata["standard_number"], metadata["organization"])
        logger.info(f"ID seguro criado para a norma: {standard_id}")

        # Atualizar status no banco de dados
        update_processing_status(standard_id, "processing")

        # Criar diretório de saída
        output_dir = os.path.join(output_base, standard_id)
        os.makedirs(output_dir, exist_ok=True)

        # Criar diretório para imagens
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        # Caminho para o arquivo Markdown de saída
        markdown_output_path = os.path.join(output_dir, "content.md")

        # Registrar início do processamento
        start_time = time.time()
        logger.info(f"Iniciando processamento simplificado para {pdf_path}")

        # Criar um arquivo Markdown simples com os metadados
        # Em um sistema real, aqui você usaria uma biblioteca para extrair o texto do PDF
        markdown_content = f"""# {metadata['title']}

**Norma:** {metadata['standard_number']}
**Organização:** {metadata['organization']}
**Ano:** {metadata['year']}
**Categorias:** {', '.join(metadata['categories'])}

---

## Conteúdo da Norma

Este é um conteúdo de exemplo gerado pelo processador simplificado.
Em um sistema real, aqui estaria o texto extraído do PDF.

O arquivo original está em: {pdf_path}

Processado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Nota

Este arquivo foi gerado por um processador simplificado porque o sistema
não conseguiu usar a biblioteca Docling para processar o PDF.

Para processar corretamente este PDF, é necessário instalar e configurar
a biblioteca Docling conforme a documentação em:
https://github.com/docling-project/docling

"""

        # Salvar o conteúdo Markdown
        with open(markdown_output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Registrar tempo de processamento
        elapsed_time = time.time() - start_time
        logger.info(f"Processamento concluído em {elapsed_time:.2f} segundos")

        # Caminho relativo para o banco de dados
        relative_md_path = os.path.join("standards_data", standard_id, "content.md")

        # Indexar o conteúdo para pesquisa
        index_standard_content(standard_id, markdown_content)
        logger.info(f"Conteúdo da norma {standard_id} indexado para pesquisa")

        logger.info(f"Arquivo Markdown gerado: {markdown_output_path}")
        return True, "Processamento simplificado concluído com sucesso", relative_md_path

    except Exception as e:
        logger.exception(f"Erro durante o processamento simplificado do PDF: {e}")
        return False, f"Erro: {str(e)}", None


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Processa PDF de norma técnica para Markdown (versão simplificada)."
    )
    parser.add_argument("--pdf", required=True, help="Caminho do arquivo PDF")
    parser.add_argument("--metadata", required=True, help="JSON com metadados da norma")
    parser.add_argument("--output", required=True, help="Diretório base para saída")

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

        # Atualizar status no banco de dados
        update_processing_status(standard_id, "processing")

        # Processar o PDF
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

            logger.info(f"Norma {standard_id} processada e indexada com sucesso")
        else:
            # Atualizar status de erro
            update_processing_status(standard_id, "error", message)
            logger.error(f"Falha no processamento da norma {standard_id}: {message}")

        # Remover arquivo PDF temporário se necessário
        if args.pdf.startswith(os.path.join(project_root, "temp")):
            try:
                os.remove(args.pdf)
                logger.info(f"Arquivo PDF temporário removido: {args.pdf}")
            except Exception as e:
                logger.warning(f"Não foi possível remover o arquivo PDF temporário: {e}")

    except Exception as e:
        logger.exception(f"Erro não tratado durante o processamento: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
