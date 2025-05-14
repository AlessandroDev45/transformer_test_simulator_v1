"""
Gerenciador de banco de dados para o módulo de consulta de normas técnicas.
Implementa funções para criar, atualizar e consultar normas técnicas no SQLite.
"""
import datetime
import json
import logging
import os
import sqlite3
from typing import Dict, List, Optional

# Configurar logger
log = logging.getLogger(__name__)


def get_db_path():
    """Retorna o caminho para o banco de dados SQLite."""
    # Usar o mesmo diretório de dados da aplicação
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "standards.db")


def get_connection():
    """Estabelece e retorna uma conexão com o banco de dados."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar colunas pelo nome
    return conn


def create_standards_tables(conn=None):
    """
    Cria as tabelas para metadados e conteúdo FTS das normas.

    Args:
        conn: Conexão SQLite opcional. Se None, cria uma nova conexão.
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Tabela de Metadados
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS standards_metadata (
            id TEXT PRIMARY KEY,  -- ID seguro da norma (ex: 'nbr_5356_3')
            title TEXT NOT NULL,
            standard_number TEXT, -- Ex: "NBR 5356-3"
            organization TEXT,    -- Ex: "ABNT"
            year INTEGER,
            categories TEXT,      -- Armazenar como JSON Text: ["Dielétrico", "Transformador"]
            md_file_path TEXT UNIQUE, -- Caminho relativo dentro de assets/
            processing_status TEXT DEFAULT 'pending', -- pending, processing, completed, error
            error_message TEXT,
            last_updated TEXT NOT NULL
        )
        """
        )

        # Tabela Virtual FTS5 para busca no conteúdo
        cursor.execute(
            """
        CREATE VIRTUAL TABLE IF NOT EXISTS standards_content_fts USING fts5(
            doc_id UNINDEXED, -- FK para standards_metadata.id (não indexado no FTS)
            content,          -- Conteúdo Markdown para indexação
            tokenize='porter unicode61'
        )
        """
        )

        # Triggers para manter FTS sincronizado
        cursor.execute(
            """
        CREATE TRIGGER IF NOT EXISTS standards_metadata_delete
        AFTER DELETE ON standards_metadata
        BEGIN
            DELETE FROM standards_content_fts WHERE doc_id = old.id;
        END;
        """
        )

        conn.commit()
        log.info("Tabelas 'standards_metadata' e 'standards_content_fts' criadas/verificadas.")
    except Exception as e:
        log.exception(f"Erro ao criar tabelas de normas: {e}")
        conn.rollback()
        raise
    finally:
        if close_conn and conn:
            conn.close()


def add_or_update_standard_metadata(
    id: str,
    title: str,
    standard_number: str,
    organization: str,
    year: int,
    categories: List[str],
    md_file_path: str,
    processing_status: str = "pending",
    error_message: str = None,
    conn=None,
) -> bool:
    """
    Insere ou atualiza metadados de uma norma técnica.

    Args:
        id: ID único da norma (ex: 'nbr_5356_3')
        title: Título da norma
        standard_number: Número da norma (ex: "NBR 5356-3")
        organization: Organização (ex: "ABNT")
        year: Ano de publicação
        categories: Lista de categorias
        md_file_path: Caminho relativo do arquivo Markdown
        processing_status: Status do processamento
        error_message: Mensagem de erro (se houver)
        conn: Conexão SQLite opcional

    Returns:
        bool: True se sucesso, False caso contrário
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Converter lista de categorias para JSON
        categories_json = json.dumps(categories, ensure_ascii=False)

        # Data atual
        now = datetime.datetime.now().isoformat()

        # Verificar se o registro já existe
        cursor.execute("SELECT id FROM standards_metadata WHERE id = ?", (id,))
        exists = cursor.fetchone() is not None

        if exists:
            # Atualizar registro existente
            cursor.execute(
                """
            UPDATE standards_metadata
            SET title = ?, standard_number = ?, organization = ?, year = ?,
                categories = ?, md_file_path = ?, processing_status = ?,
                error_message = ?, last_updated = ?
            WHERE id = ?
            """,
                (
                    title,
                    standard_number,
                    organization,
                    year,
                    categories_json,
                    md_file_path,
                    processing_status,
                    error_message,
                    now,
                    id,
                ),
            )
        else:
            # Inserir novo registro
            cursor.execute(
                """
            INSERT INTO standards_metadata
            (id, title, standard_number, organization, year, categories,
             md_file_path, processing_status, error_message, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    id,
                    title,
                    standard_number,
                    organization,
                    year,
                    categories_json,
                    md_file_path,
                    processing_status,
                    error_message,
                    now,
                ),
            )

        conn.commit()
        log.info(f"{'Atualizado' if exists else 'Inserido'} metadados para norma {id}")
        return True
    except Exception as e:
        log.exception(
            f"Erro ao {'atualizar' if exists else 'inserir'} metadados da norma {id}: {e}"
        )
        conn.rollback()
        return False
    finally:
        if close_conn and conn:
            conn.close()


def update_processing_status(id: str, status: str, error_message: str = None, conn=None) -> bool:
    """
    Atualiza o status de processamento de uma norma.

    Args:
        id: ID da norma
        status: Novo status ('pending', 'processing', 'completed', 'error')
        error_message: Mensagem de erro (se status='error')
        conn: Conexão SQLite opcional

    Returns:
        bool: True se sucesso, False caso contrário
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()

        cursor.execute(
            """
        UPDATE standards_metadata
        SET processing_status = ?, error_message = ?, last_updated = ?
        WHERE id = ?
        """,
            (status, error_message, now, id),
        )

        conn.commit()
        log.info(f"Atualizado status de processamento da norma {id} para {status}")
        return True
    except Exception as e:
        log.exception(f"Erro ao atualizar status de processamento da norma {id}: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn and conn:
            conn.close()


def index_standard_content(doc_id: str, md_content: str, conn=None) -> bool:
    """
    Indexa o conteúdo Markdown de uma norma na tabela FTS.

    Args:
        doc_id: ID da norma
        md_content: Conteúdo Markdown
        conn: Conexão SQLite opcional

    Returns:
        bool: True se sucesso, False caso contrário
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Verificar se já existe conteúdo para este doc_id
        cursor.execute("SELECT doc_id FROM standards_content_fts WHERE doc_id = ?", (doc_id,))
        exists = cursor.fetchone() is not None

        if exists:
            # Atualizar conteúdo existente
            cursor.execute(
                """
            DELETE FROM standards_content_fts WHERE doc_id = ?
            """,
                (doc_id,),
            )

        # Inserir conteúdo
        cursor.execute(
            """
        INSERT INTO standards_content_fts (doc_id, content)
        VALUES (?, ?)
        """,
            (doc_id, md_content),
        )

        conn.commit()
        log.info(f"{'Atualizado' if exists else 'Indexado'} conteúdo para norma {doc_id}")
        return True
    except Exception as e:
        log.exception(f"Erro ao indexar conteúdo da norma {doc_id}: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn and conn:
            conn.close()


def search_standards_fts(query: str, limit: int = 20, conn=None) -> List[Dict]:
    """
    Realiza busca de texto completo nas normas.

    Args:
        query: Termo de busca
        limit: Número máximo de resultados
        conn: Conexão SQLite opcional

    Returns:
        Lista de dicionários com resultados da busca
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Busca com snippet para destacar os termos encontrados
        cursor.execute(
            """
        SELECT
            m.id,
            m.title,
            m.standard_number,
            m.organization,
            snippet(standards_content_fts, 0, '<mark>', '</mark>', '...', 40) as snippet
        FROM
            standards_content_fts f
        JOIN
            standards_metadata m ON f.doc_id = m.id
        WHERE
            standards_content_fts MATCH ? AND m.processing_status = 'completed'
        ORDER BY
            rank
        LIMIT ?
        """,
            (query, limit),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "standard_number": row["standard_number"],
                    "organization": row["organization"],
                    "snippet": row["snippet"],
                }
            )

        log.info(f"Busca por '{query}' retornou {len(results)} resultados")
        return results
    except Exception as e:
        log.exception(f"Erro na busca FTS por '{query}': {e}")
        return []
    finally:
        if close_conn and conn:
            conn.close()


def get_standard_metadata_by_id(doc_id: str, conn=None) -> Optional[Dict]:
    """
    Busca metadados de uma norma pelo ID.

    Args:
        doc_id: ID da norma
        conn: Conexão SQLite opcional

    Returns:
        Dicionário com metadados ou None se não encontrado
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT * FROM standards_metadata WHERE id = ?
        """,
            (doc_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        # Converter para dicionário
        metadata = dict(row)

        # Converter categorias de JSON para lista
        if metadata.get("categories"):
            metadata["categories"] = json.loads(metadata["categories"])

        return metadata
    except Exception as e:
        log.exception(f"Erro ao buscar metadados da norma {doc_id}: {e}")
        return None
    finally:
        if close_conn and conn:
            conn.close()


def get_standard_content_path(doc_id: str, conn=None) -> Optional[str]:
    """
    Busca o caminho do arquivo Markdown de uma norma.

    Args:
        doc_id: ID da norma
        conn: Conexão SQLite opcional

    Returns:
        Caminho do arquivo ou None se não encontrado
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT md_file_path FROM standards_metadata
        WHERE id = ? AND processing_status = 'completed'
        """,
            (doc_id,),
        )

        row = cursor.fetchone()
        return row["md_file_path"] if row else None
    except Exception as e:
        log.exception(f"Erro ao buscar caminho do conteúdo da norma {doc_id}: {e}")
        return None
    finally:
        if close_conn and conn:
            conn.close()


def get_all_standards_metadata(status: str = None, conn=None) -> List[Dict]:
    """
    Lista metadados de todas as normas, opcionalmente filtradas por status.

    Args:
        status: Status de processamento para filtrar (opcional)
        conn: Conexão SQLite opcional

    Returns:
        Lista de dicionários com metadados
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
            SELECT * FROM standards_metadata
            WHERE processing_status = ?
            ORDER BY organization, standard_number
            """,
                (status,),
            )
        else:
            cursor.execute(
                """
            SELECT * FROM standards_metadata
            ORDER BY organization, standard_number
            """
            )

        results = []
        for row in cursor.fetchall():
            metadata = dict(row)

            # Converter categorias de JSON para lista
            if metadata.get("categories"):
                metadata["categories"] = json.loads(metadata["categories"])

            results.append(metadata)

        return results
    except Exception as e:
        log.exception(f"Erro ao listar metadados de normas: {e}")
        return []
    finally:
        if close_conn and conn:
            conn.close()


def delete_standard(doc_id: str, conn=None) -> bool:
    """
    Remove uma norma do banco de dados.

    Args:
        doc_id: ID da norma
        conn: Conexão SQLite opcional

    Returns:
        bool: True se sucesso, False caso contrário
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Obter caminho do arquivo antes de excluir
        cursor.execute("SELECT md_file_path FROM standards_metadata WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        if not row:
            log.warning(f"Norma {doc_id} não encontrada para exclusão")
            return False

        # Excluir da tabela de metadados (o trigger excluirá da FTS)
        cursor.execute("DELETE FROM standards_metadata WHERE id = ?", (doc_id,))

        conn.commit()
        log.info(f"Norma {doc_id} excluída do banco de dados")
        return True
    except Exception as e:
        log.exception(f"Erro ao excluir norma {doc_id}: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn and conn:
            conn.close()


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


def get_categories_list(conn=None) -> List[str]:
    """
    Retorna uma lista de todas as categorias únicas usadas nas normas.

    Args:
        conn: Conexão SQLite opcional

    Returns:
        Lista de categorias únicas
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT categories FROM standards_metadata")

        all_categories = set()
        for row in cursor.fetchall():
            if row["categories"]:
                categories = json.loads(row["categories"])
                all_categories.update(categories)

        return sorted(list(all_categories))
    except Exception as e:
        log.exception(f"Erro ao obter lista de categorias: {e}")
        return []
    finally:
        if close_conn and conn:
            conn.close()


def filter_standards_by_category(category: str, conn=None) -> List[Dict]:
    """
    Filtra normas por categoria.

    Args:
        category: Categoria para filtrar
        conn: Conexão SQLite opcional

    Returns:
        Lista de dicionários com metadados das normas na categoria
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    try:
        cursor = conn.cursor()

        # Busca normas onde a categoria está na lista JSON
        cursor.execute(
            """
        SELECT * FROM standards_metadata
        WHERE json_extract(categories, '$') LIKE ?
        ORDER BY organization, standard_number
        """,
            (f"%{category}%",),
        )

        results = []
        for row in cursor.fetchall():
            metadata = dict(row)

            # Verificar se a categoria realmente está na lista
            categories = json.loads(metadata["categories"])
            if category in categories:
                # Manter a lista de categorias como lista Python
                metadata["categories"] = categories
                results.append(metadata)

        return results
    except Exception as e:
        log.exception(f"Erro ao filtrar normas por categoria '{category}': {e}")
        return []
    finally:
        if close_conn and conn:
            conn.close()
