# utils/db_manager.py
import datetime
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "history.db") # Padronizando para history.db

os.makedirs(DB_DIR, exist_ok=True)

def connect_db() -> sqlite3.Connection:
    # ... (sem alterações, mas garanta que está criando a tabela test_sessions
    # com as colunas: timestamp, session_name, notes,
    # transformer_inputs TEXT, losses_data TEXT, impulse_data TEXT,
    # dieletric_data TEXT, applied_voltage_data TEXT, induced_voltage_data TEXT,
    # short_circuit_data TEXT, temperature_rise_data TEXT
    # )
    # ... (seu código connect_db existente, verificando se a tabela existe)
    log.info(f"[DB CONNECT] Tentando conectar ao banco de dados: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # <<< ADICIONE/GARANTA ESTA LINHA AQUI
    log.info("[DB CONNECT] Conexão estabelecida com sucesso e row_factory definida.")
    conn.execute("PRAGMA foreign_keys = ON")
    log.info("[DB CONNECT] Suporte a chaves estrangeiras habilitado")

    # Mapeamento de nomes de store para colunas do DB
    # Esta ordem DEVE corresponder à ordem na query INSERT e na leitura
    # Estes são os STORE_IDS do MCP
    STORE_COLUMNS_MAP = {
        "transformer-inputs-store": "transformer_inputs",
        "losses-store": "losses_data",
        "impulse-store": "impulse_data",
        "dieletric-analysis-store": "dieletric_data", # Corrigido para 'dieletric_data'
        "applied-voltage-store": "applied_voltage_data",
        "induced-voltage-store": "induced_voltage_data",
        "short-circuit-store": "short_circuit_data",
        "temperature-rise-store": "temperature_rise_data",
        "comprehensive-analysis-store": "comprehensive_analysis_data", # Adicionando os que faltavam
        "front-resistor-data": "front_resistor_data",
        "tail-resistor-data": "tail_resistor_data",
        "calculated-inductance": "calculated_inductance_data", # Nome da coluna ligeiramente diferente
        "simulation-status": "simulation_status_data" # Nome da coluna ligeiramente diferente
    }

    # Construir a string das colunas dinamicamente
    column_definitions = ",\n                ".join([f"{col_name} TEXT" for col_name in STORE_COLUMNS_MAP.values()])

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS test_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        session_name TEXT NOT NULL UNIQUE, -- Adicionado UNIQUE para nome da sessão
        notes TEXT,
        {column_definitions}
    )
    """
    # Adicionar mais colunas se novos stores forem criados
    # Exemplo: comprehensive_analysis_data TEXT, ...

    try:
        conn.execute(create_table_sql)
        log.info("[DB CONNECT] Tabela test_sessions criada/verificada com sucesso")
        conn.commit()
    except sqlite3.Error as sql_error:
        log.error(f"[DB CONNECT] Erro ao criar/verificar tabela test_sessions: {sql_error}")
        raise
    return conn


def save_test_session(all_mcp_stores_data: Dict[str, Any], session_name: str, notes: str = "") -> int:
    """
    Salva uma sessão de teste no banco de dados.
    `all_mcp_stores_data` é um dicionário onde as chaves são os STORE_IDs e os
    valores são os DADOS JÁ PREPARADOS (serializáveis) para cada store.
    """
    log.info(f"[DB MANAGER - SAVE] Iniciando salvamento da sessão: '{session_name}'")
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()

        # Mapeamento de STORE_IDs para nomes de colunas no banco de dados
        # Certifique-se que STORE_COLUMNS_MAP esteja definido consistentemente
        # (talvez no topo do módulo ou importado)

        # O ideal é que STORE_COLUMNS_MAP seja definido em um local central ou aqui
        # e que corresponda às colunas da sua tabela.
        STORE_COLUMNS_MAP = {
            "transformer-inputs-store": "transformer_inputs",
            "losses-store": "losses_data",
            "impulse-store": "impulse_data",
            "dieletric-analysis-store": "dieletric_data",
            "applied-voltage-store": "applied_voltage_data",
            "induced-voltage-store": "induced_voltage_data",
            "short-circuit-store": "short_circuit_data",
            "temperature-rise-store": "temperature_rise_data",
            "comprehensive-analysis-store": "comprehensive_analysis_data",
            "front-resistor-data": "front_resistor_data",
            "tail-resistor-data": "tail_resistor_data",
            "calculated-inductance": "calculated_inductance_data",
            "simulation-status": "simulation_status_data"
        }
        # Garantir que todas as colunas esperadas pela tabela (exceto id, timestamp, etc.) estejam no map
        # E que todos os STORE_IDS estejam no map.

        db_column_names = []
        json_values_for_db = []

        # Iterar sobre todos os stores recebidos, não apenas os que estão em STORE_IDS
        for store_id, store_content in all_mcp_stores_data.items():
            db_column_name = STORE_COLUMNS_MAP.get(store_id)
            if not db_column_name:
                log.warning(f"[DB MANAGER - SAVE] Store ID '{store_id}' não mapeado para coluna do DB. Ignorando.")
                continue

            db_column_names.append(db_column_name)

            # O MCP já deve ter garantido que store_content é serializável
            # ou é um dict de diagnóstico.
            try:
                json_str = json.dumps(store_content, default=str, ensure_ascii=False)
                json_values_for_db.append(json_str)
                log.debug(f"[DB MANAGER - SAVE] Serializado '{store_id}' para '{db_column_name}': {len(json_str)} bytes.")
            except Exception as e_ser:
                log.error(f"[DB MANAGER - SAVE] ERRO ao serializar store '{store_id}' para DB: {e_ser}", exc_info=True)
                json_values_for_db.append(json.dumps({"_serialization_error_in_db_manager": str(e_ser)}))


        if not db_column_names:
            log.error("[DB MANAGER - SAVE] Nenhuma coluna de store para salvar. Abortando.")
            return -2 # Código de erro específico

        cols_str = ", ".join(db_column_names)
        placeholders_str = ", ".join(["?"] * len(db_column_names))

        sql_query = f"""
            INSERT INTO test_sessions (timestamp, session_name, notes, {cols_str})
            VALUES (?, ?, ?, {placeholders_str})
        """
        sql_values = (timestamp, session_name, notes, *json_values_for_db)

        log.debug(f"[DB MANAGER - SAVE] Executando SQL: {sql_query} com {len(sql_values)} valores.")
        cursor.execute(sql_query, sql_values)
        session_id = cursor.lastrowid
        conn.commit()
        log.info(f"[DB MANAGER - SAVE] Sessão '{session_name}' salva com ID: {session_id}")
        return session_id

    except sqlite3.IntegrityError as e_int:
        # Isso provavelmente significa que o session_name já existe se você adicionou UNIQUE
        log.error(f"[DB MANAGER - SAVE] Erro de integridade ao salvar sessão '{session_name}': {e_int}", exc_info=True)
        if conn: conn.rollback()
        return -3 # Código de erro para nome duplicado ou outra violação de integridade
    except Exception as e:
        log.error(f"[DB MANAGER - SAVE] Erro geral ao salvar sessão '{session_name}': {e}", exc_info=True)
        if conn: conn.rollback()
        return -1 # Erro genérico
    finally:
        if conn: conn.close()

def get_test_session_details(session_id: int) -> Optional[Dict[str, Any]]:
    """
    Recupera os detalhes COMPLETOS de uma sessão específica, retornando os dados
    dos stores como strings JSON para serem desserializados pelo MCP.
    """
    log.info(f"[DB MANAGER - LOAD] Carregando detalhes da sessão ID: {session_id}")
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Obter TODOS os nomes de colunas da tabela para buscar dinamicamente
        cursor.execute("PRAGMA table_info(test_sessions)")
        columns_info = cursor.fetchall()
        column_names_from_db = [col_info['name'] for col_info in columns_info]

        if not column_names_from_db:
            log.error("[DB MANAGER - LOAD] Não foi possível obter nomes de colunas da tabela test_sessions.")
            return None

        select_cols_str = ", ".join(column_names_from_db)

        cursor.execute(f"SELECT {select_cols_str} FROM test_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            log.warning(f"[DB MANAGER - LOAD] Sessão ID {session_id} não encontrada.")
            return None

        # Monta o dicionário de resultado.
        # Os dados dos stores são mantidos como strings JSON.
        session_details_raw = dict(row)

        # Mapeamento de STORE_IDs para nomes de colunas no banco de dados
        # (Deve ser o mesmo usado em save_test_session)
        STORE_COLUMNS_MAP = {
            "transformer-inputs-store": "transformer_inputs",
            "losses-store": "losses_data",
            "impulse-store": "impulse_data",
            "dieletric-analysis-store": "dieletric_data",
            "applied-voltage-store": "applied_voltage_data",
            "induced-voltage-store": "induced_voltage_data",
            "short-circuit-store": "short_circuit_data",
            "temperature-rise-store": "temperature_rise_data",
            "comprehensive-analysis-store": "comprehensive_analysis_data",
            "front-resistor-data": "front_resistor_data",
            "tail-resistor-data": "tail_resistor_data",
            "calculated-inductance": "calculated_inductance_data",
            "simulation-status": "simulation_status_data"
        }

        # Estrutura para o MCP: {'store_id': json_string_data, ...}
        mcp_formatted_store_data = {}
        for store_id, db_col_name in STORE_COLUMNS_MAP.items():
            if db_col_name in session_details_raw:
                mcp_formatted_store_data[store_id] = session_details_raw.get(db_col_name)
            else:
                log.warning(f"[DB MANAGER - LOAD] Coluna '{db_col_name}' (para store '{store_id}') não encontrada nos dados recuperados para sessão {session_id}.")
                mcp_formatted_store_data[store_id] = "{}" # JSON string vazia como fallback

        result = {
            "id": session_details_raw.get("id"),
            "timestamp": session_details_raw.get("timestamp"),
            "session_name": session_details_raw.get("session_name"),
            "notes": session_details_raw.get("notes"),
            "mcp_stores_raw_json": mcp_formatted_store_data # Contém strings JSON
        }
        log.info(f"[DB MANAGER - LOAD] Detalhes da sessão ID {session_id} recuperados.")
        return result

    except Exception as e:
        log.error(f"[DB MANAGER - LOAD] Erro ao carregar detalhes da sessão {session_id}: {e}", exc_info=True)
        return None
    finally:
        if conn: conn.close()

# Manter get_all_test_sessions, session_name_exists, delete_test_session como estão,
# pois parecem funcionar bem para listar e gerenciar as sessões.

# ... (seu código existente para get_all_test_sessions, session_name_exists, delete_test_session) ...
# Adicionei a verificação de tabela no connect_db para garantir que todas as colunas existam.
# Se as colunas comprehensive_analysis_data, etc., não existirem, você precisará
# de um script de migração ou recriar a tabela.
# Para simplificar, a create_table_sql agora é mais dinâmica.

# Função session_name_exists (sem alterações)
def session_name_exists(session_name: str) -> bool:
    log.info(f"[DB CHECK] Verificando se o nome de sessão '{session_name}' já existe")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM test_sessions WHERE LOWER(session_name) = LOWER(?)",
            (session_name,),
        )
        count = cursor.fetchone()[0]
        conn.close()
        exists = count > 0
        log.info(f"[DB CHECK] Nome de sessão '{session_name}' existe? {exists}")
        return exists
    except Exception as e:
        log.error(f"[DB CHECK] Erro ao verificar nome de sessão '{session_name}': {e}")
        return False # Default para não bloquear em caso de erro de DB

# Função delete_test_session (sem alterações)
def delete_test_session(session_id: int) -> bool:
    log.info(f"[DB DELETE] Iniciando exclusão da sessão ID {session_id}")
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT session_name FROM test_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            log.warning(f"[DB DELETE] Sessão com ID {session_id} não encontrada para exclusão")
            return False
        session_name = row[0]
        cursor.execute("DELETE FROM test_sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        log.info(f"[DB DELETE] Sessão com ID {session_id} ('{session_name}') excluída com sucesso")
        return True
    except Exception as e:
        log.error(f"[DB DELETE] Erro ao excluir sessão {session_id}: {e}", exc_info=True)
        return False

# Função get_all_test_sessions (sem alterações, apenas para referência de formato)
def get_all_test_sessions(search_term: Optional[str] = None) -> List[Dict[str, Any]]:
    log.info(f"[DB GET ALL] Buscando sessões. Termo: '{search_term}'")
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        if search_term:
            query = """
            SELECT id, timestamp, session_name, notes FROM test_sessions
            WHERE session_name LIKE ? OR notes LIKE ?
            ORDER BY timestamp DESC
            """
            cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
        else:
            query = "SELECT id, timestamp, session_name, notes FROM test_sessions ORDER BY timestamp DESC"
            cursor.execute(query)

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "timestamp": datetime.datetime.fromisoformat(row["timestamp"]).strftime("%d/%m/%Y %H:%M") if row["timestamp"] else "N/A",
                "session_name": row["session_name"],
                "notes": row["notes"]
            })
        log.info(f"[DB GET ALL] Encontradas {len(sessions)} sessões.")
        return sessions
    except Exception as e:
        log.error(f"[DB GET ALL] Erro ao buscar sessões: {e}", exc_info=True)
        return []
    finally:
        if conn: conn.close()
