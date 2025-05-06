# utils/db_manager.py
"""
Módulo para gerenciar a persistência de dados da aplicação em um banco de dados SQLite.
"""
import os
import json
import sqlite3
import datetime
import logging
from typing import Dict, List, Optional, Any, Union

log = logging.getLogger(__name__)

# Caminho para o banco de dados
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'test_sessions.db')

# Garantir que o diretório de dados existe
os.makedirs(DB_DIR, exist_ok=True)

def connect_db() -> sqlite3.Connection:
    """
    Estabelece conexão com o banco de dados SQLite.
    Cria o banco e a tabela se não existirem.

    Returns:
        sqlite3.Connection: Conexão com o banco de dados
    """
    log.info(f"[DB CONNECT] Tentando conectar ao banco de dados: {DB_PATH}")
    log.info(f"[DB CONNECT] Diretório existe? {os.path.exists(DB_DIR)}")
    log.info(f"[DB CONNECT] Arquivo existe? {os.path.exists(DB_PATH)}")

    print(f"[DEBUG DB] Tentando conectar ao banco de dados: {DB_PATH}")
    print(f"[DEBUG DB] Diretório existe? {os.path.exists(DB_DIR)}")
    # Verificar permissões de escrita no diretório
    write_permission = os.access(DB_DIR, os.W_OK)
    print(f"[DEBUG DB] Permissão de escrita no diretório '{DB_DIR}'? {write_permission}") # <-- NOVO PRINT
    log.info(f"[DB CONNECT] Permissão de escrita no diretório '{DB_DIR}'? {write_permission}")
    print(f"[DEBUG DB] Arquivo existe? {os.path.exists(DB_PATH)}")
    if os.path.exists(DB_PATH):
        file_write_permission = os.access(DB_PATH, os.W_OK)
        print(f"[DEBUG DB] Permissão de escrita no arquivo '{DB_PATH}'? {file_write_permission}") # <-- NOVO PRINT
        log.info(f"[DB CONNECT] Permissão de escrita no arquivo '{DB_PATH}'? {file_write_permission}")

    try:
        print("[DEBUG DB] Tentando sqlite3.connect...") # <-- NOVO PRINT
        # Criar conexão
        conn = sqlite3.connect(DB_PATH)
        log.info("[DB CONNECT] Conexão estabelecida com sucesso")
        print("[DEBUG DB] Conexão estabelecida com sucesso")

        # Habilitar suporte a chaves estrangeiras
        conn.execute("PRAGMA foreign_keys = ON")
        log.info("[DB CONNECT] Suporte a chaves estrangeiras habilitado")
        print("[DEBUG DB] Suporte a chaves estrangeiras habilitado")

        # Criar tabela de sessões se não existir
        log.info("[DB CONNECT] Criando tabela test_sessions se não existir")
        print("[DEBUG DB] Criando tabela test_sessions se não existir")
        try:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_name TEXT NOT NULL,
                transformer_inputs TEXT,
                losses_data TEXT,
                impulse_data TEXT,
                dieletric_data TEXT,
                applied_voltage_data TEXT,
                induced_voltage_data TEXT,
                short_circuit_data TEXT,
                temperature_rise_data TEXT,
                notes TEXT
            )
            ''')
            log.info("[DB CONNECT] Tabela test_sessions criada/verificada com sucesso")
            print("[DEBUG DB] Tabela test_sessions criada/verificada com sucesso")

            conn.commit()
            log.info("[DB CONNECT] Commit realizado com sucesso")
            print("[DEBUG DB] Commit realizado com sucesso")
            return conn
        except sqlite3.Error as sql_error:
            log.error(f"[DB CONNECT] Erro ao criar tabela: {sql_error}")
            print(f"[DEBUG DB] Erro ao criar tabela: {sql_error}")
            raise
    except Exception as e:
        log.error(f"[DB CONNECT] Erro ao conectar ao banco de dados: {e}")
        print(f"[DEBUG DB] Erro ao conectar ao banco de dados: {e}")
        raise

def save_test_session(session_data: Dict[str, Any], session_name: str, notes: str = "") -> int:
    """
    Salva uma sessão de teste no banco de dados.
    Assume que session_data já foi preparado/corrigido por prepare_session_data.
    """
    print(f"\n\n{'!'*10} FUNÇÃO save_test_session INICIADA {'!'*10}") # <-- NOVO PRINT (com destaque)
    print(f"Nome da sessão: '{session_name}'")
    print(f"Notas: '{notes}'")
    print(f"Dados recebidos (chaves): {list(session_data.keys())}")
    print(f"{'='*80}")

    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        print("[DB SAVE] Conexão e cursor criados.")

        timestamp = datetime.datetime.now().isoformat()
        print(f"[DB SAVE] Timestamp: {timestamp}")

        # Mapeamento de Nomes de Store para Colunas do DB
        store_to_column_map = {
            'transformer-inputs-store': 'transformer_inputs',
            'losses-store': 'losses_data',
            'impulse-store': 'impulse_data',
            'dieletric-analysis-store': 'dieletric_data',
            'applied-voltage-store': 'applied_voltage_data',
            'induced-voltage-store': 'induced_voltage_data',
            'short-circuit-store': 'short_circuit_data',
            'temperature-rise-store': 'temperature_rise_data'
        }
        # Lista de colunas na ordem da query INSERT
        db_columns_in_order = [
            'transformer_inputs', 'losses_data', 'impulse_data', 'dieletric_data',
            'applied_voltage_data', 'induced_voltage_data', 'short_circuit_data',
            'temperature_rise_data'
        ]

        # --- REMOVIDO: A chamada a prepare_session_data não deve estar aqui ---
        # prepared_data = prepare_session_data(session_data) # <-- REMOVER ESTA LINHA

        print(f"\n{'='*40} SERIALIZANDO DADOS PREPARADOS PARA INSERT {'='*40}")
        json_values = []
        stores_saved_as_empty = [] # Lista para rastrear stores salvos como {}

        for store_name, db_col_name in store_to_column_map.items():
            data_to_serialize = session_data.get(store_name, {}) # Pega do dict passado
            print(f"\n--- Serializando '{store_name}' para coluna '{db_col_name}' ---")
            print(f"Tipo dos dados a serializar: {type(data_to_serialize).__name__}")

            # Verificar se já contém informações de erro de conversão
            has_conversion_error = False
            if isinstance(data_to_serialize, dict) and data_to_serialize.get("_conversion_failed"):
                has_conversion_error = True
                error_msg = data_to_serialize.get("_error", "Erro desconhecido")
                print(f"⚠ Dados contêm informações de erro de conversão: {error_msg}")
                log.warning(f"[DB SAVE] '{store_name}' contém informações de erro de conversão: {error_msg}")

            json_str = "{}" # Default para JSON vazio
            serialization_ok = False
            try:
                # Tenta serializar com default=str para segurança
                json_str = json.dumps(data_to_serialize, default=str, ensure_ascii=False, indent=2) # Indent para facilitar leitura no log/print
                serialization_ok = True

                # Verifica se o resultado é apenas um dicionário vazio "{}" ou similar
                # e se o dado original *não* era realmente vazio
                is_effectively_empty_json = json_str.strip() in ["{}", "null", "[]"]
                original_was_meaningful = data_to_serialize and data_to_serialize != {"_empty_marker": True} and not (isinstance(data_to_serialize, dict) and data_to_serialize.get("_conversion_failed"))

                if is_effectively_empty_json and original_was_meaningful:
                     print(f"  ⚠ AVISO: Dados originais para '{store_name}' existiam, mas JSON final é vazio/null/[]! Verifique a função de conversão.")
                     log.warning(f"[DB SAVE] Dados originais para '{store_name}' parecem perdidos na serialização final (JSON: {json_str})")
                     stores_saved_as_empty.append(store_name) # Rastreia o problema
                elif is_effectively_empty_json:
                     print(f"  Informação: Store '{store_name}' resultou em JSON vazio/null/[] (original era vazio ou erro).")
                     log.info(f"[DB SAVE] Store '{store_name}' serializado como vazio/null/[] (era vazio ou erro).")
                     if original_was_meaningful: stores_saved_as_empty.append(store_name) # Também rastreia se era erro
                else:
                     print(f"  ✓ Serializado com sucesso: {len(json_str)} bytes.")
                     # Opcional: Imprimir JSON curto para debug
                     if len(json_str) < 200:
                         print(f"    JSON: {json_str}")
                     else:
                         print(f"    JSON (início): {json_str[:150]}...")
                     log.info(f"[DB SAVE] '{store_name}' serializado: {len(json_str)} bytes.")

                json_values.append(json_str)

                if has_conversion_error:
                    print(f"✓ Informações de diagnóstico serializadas com sucesso: {len(json_str)} bytes")
                    log.info(f"[DB SAVE] '{store_name}' (com informações de diagnóstico) serializado para '{db_col_name}': {len(json_str)} bytes")

            except (TypeError, OverflowError) as e:
                print(f"  ✗ ERRO CRÍTICO DE SERIALIZAÇÃO para '{store_name}': {e}")
                log.error(f"[DB SAVE] Erro CRÍTICO de serialização para {store_name}: {e}", exc_info=True)
                # Cria um JSON de erro
                error_info = {"_serialization_failed": True, "_error": f"Erro json.dumps: {str(e)}"}
                json_str = json.dumps(error_info)
                json_values.append(json_str)
                print(f"  ✓ Informações de erro serializadas como fallback.")
                stores_saved_as_empty.append(f"{store_name} (ERRO)") # Rastreia o erro

        # Garante que temos o número correto de valores JSON
        if len(json_values) != len(db_columns_in_order):
             log.error(f"Erro interno: Discrepância entre colunas DB ({len(db_columns_in_order)}) e valores JSON ({len(json_values)})")
             raise ValueError("Erro interno ao preparar dados para o banco.")

        # Log dos dados JSON preparados
        print(f"\n{'='*40} DADOS JSON PREPARADOS PARA INSERT {'='*40}")
        for i, col_name in enumerate(db_columns_in_order):
             print(f"{col_name}: {len(json_values[i])} bytes")

        # Montar a query SQL
        cols_str = ", ".join(db_columns_in_order)
        placeholders_str = ", ".join(["?"] * len(db_columns_in_order))
        sql_query = f'''
            INSERT INTO test_sessions (
                timestamp, session_name, notes, {cols_str}
            ) VALUES (?, ?, ?, {placeholders_str})
        '''
        # Montar os valores na ordem correta da query
        sql_values = (timestamp, session_name, notes, *json_values)

        # --- DEBUG ANTES DO EXECUTE ---
        print(f"\n{'='*40} DADOS FINAIS PARA INSERT SQL (Bytes e Início do JSON) {'='*40}")
        print(f"  - timestamp: {timestamp}")
        print(f"  - session_name: {session_name}")
        print(f"  - notes: {notes}")
        for i, col_name in enumerate(db_columns_in_order):
            val_index = i + 3  # +3 para pular timestamp, session_name, notes
            val_json = sql_values[val_index]
            print(f"  - {col_name}: {type(val_json).__name__} ({len(val_json)} bytes)")
            print(f"    JSON (início): {val_json[:150]}{'...' if len(val_json) > 150 else ''}")  # Imprime início do JSON
        print(f"{'-'*60}")

        # Adiciona aviso se algum store foi salvo como vazio
        if stores_saved_as_empty:
            print(f"\n⚠ AVISO: Os seguintes stores foram salvos como JSON vazio ou com erro:")
            for store_name in stores_saved_as_empty:
                print(f"  - {store_name}")
            log.warning(f"[DB SAVE] Os seguintes stores foram salvos como JSON vazio ou com erro: {', '.join(stores_saved_as_empty)}")

        print(f"\n{'='*40} EXECUTANDO INSERT SQL {'='*40}")
        print(f"Query: {sql_query}")
        print(f"Valores (início): ({timestamp}, {session_name}, {notes}, ...)")

        # Executar INSERT
        try:
            cursor.execute(sql_query, sql_values)
            print(f"[DB SAVE] INSERT executado. Linhas afetadas: {cursor.rowcount}")
            log.info(f"[DB SAVE] INSERT executado. Linhas afetadas: {cursor.rowcount}")
        except sqlite3.Error as e_sql:
             print(f"!!! ERRO SQL durante INSERT: {e_sql} !!!")
             log.error(f"[DB SAVE] Erro SQL durante INSERT: {e_sql}", exc_info=True)
             raise # Re-levanta o erro

        session_id = cursor.lastrowid
        print(f"[DB SAVE] ID da linha inserida: {session_id}")

        # Commit
        print(f"\n{'='*40} EXECUTANDO COMMIT {'='*40}")
        conn.commit()
        print("[DB SAVE] Commit realizado com sucesso.")
        log.info("[DB SAVE] Commit realizado.")

        print(f"{'!'*10} FUNÇÃO save_test_session FINALIZADA COM SUCESSO (ID={session_id}) {'!'*10}") # <-- NOVO PRINT (com destaque)
        return session_id

    except Exception as e:
        print(f"***** ERRO NA FUNÇÃO save_test_session *****")
        print(f"Erro: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        log.exception(f"[DB SAVE] Erro geral ao salvar sessão: {e}")
        if conn:
            try:
                conn.rollback()
                print("[DB SAVE] Rollback realizado devido a erro.")
            except Exception as rb_err:
                print(f"[DB SAVE] Erro durante rollback: {rb_err}")
        raise # Re-levanta a exceção

    finally:
        if conn:
            try:
                conn.close()
                print("[DB SAVE] Conexão com DB fechada.")
                log.info("[DB SAVE] Conexão com DB fechada.")
            except Exception as cl_err:
                 print(f"[DB SAVE] Erro ao fechar conexão: {cl_err}")
                 log.error(f"[DB SAVE] Erro ao fechar conexão: {cl_err}")
        print(f"{'='*80}\n\n")

def get_all_test_sessions(search_term: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recupera todas as sessões de teste ou filtra por termo de busca.

    Args:
        search_term: Termo opcional para filtrar sessões por nome

    Returns:
        List[Dict]: Lista de sessões com informações básicas
    """
    log.info(f"[DB GET] get_all_test_sessions chamado com search_term: {search_term}")
    print(f"[DEBUG DB] get_all_test_sessions chamado com search_term: {search_term}")
    try:
        log.info(f"[DB GET] Tentando conectar ao banco de dados em: {DB_PATH}")
        print(f"[DEBUG DB] Tentando conectar ao banco de dados em: {DB_PATH}")
        conn = connect_db()
        cursor = conn.cursor()
        log.info("[DB GET] Conexão com banco de dados estabelecida")
        print("[DEBUG DB] Conexão com banco de dados estabelecida")

        if search_term:
            # Busca por nome de sessão contendo o termo
            log.info(f"[DB GET] Buscando sessões com termo: '{search_term}'")
            cursor.execute('''
            SELECT id, timestamp, session_name, notes
            FROM test_sessions
            WHERE session_name LIKE ? OR notes LIKE ?
            ORDER BY timestamp DESC
            ''', (f'%{search_term}%', f'%{search_term}%'))
        else:
            # Busca todas as sessões
            log.info("[DB GET] Buscando todas as sessões")
            cursor.execute('''
            SELECT id, timestamp, session_name, notes
            FROM test_sessions
            ORDER BY timestamp DESC
            ''')

        # Formatar resultados
        sessions = []
        rows = cursor.fetchall()
        log.info(f"[DB GET] Encontradas {len(rows)} sessões")

        for row in rows:
            session_id, timestamp_str, session_name, notes = row

            # Converter timestamp para formato legível
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp_str)
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M")
            except Exception as timestamp_error:
                log.warning(f"[DB GET] Erro ao formatar timestamp '{timestamp_str}': {timestamp_error}")
                formatted_date = timestamp_str

            sessions.append({
                'id': session_id,
                'timestamp': formatted_date,
                'session_name': session_name,
                'notes': notes
            })

        conn.close()
        log.info(f"[DB GET] Retornando {len(sessions)} sessões formatadas")
        return sessions
    except Exception as e:
        log.error(f"[DB GET] Erro ao recuperar sessões: {e}")
        print(f"[DEBUG DB] Erro ao recuperar sessões: {e}")
        return []

def get_test_session_details(session_id: int) -> Dict[str, Any]:
    """
    Recupera os detalhes completos de uma sessão específica.

    Args:
        session_id: ID da sessão a ser recuperada

    Returns:
        Dict: Dados completos da sessão
    """
    print(f"\n\n{'='*80}")
    print(f"CARREGANDO SESSÃO ID: {session_id}")
    print(f"{'='*80}")

    log.info(f"[DB DETAILS] Recuperando detalhes da sessão com ID {session_id}")
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        log.info(f"[DB DETAILS] Executando consulta para sessão ID {session_id}")
        try:
            cursor.execute('''
            SELECT * FROM test_sessions WHERE id = ?
            ''', (session_id,))
        except sqlite3.Error as sql_error:
            log.error(f"[DB DETAILS] Erro SQL ao consultar sessão {session_id}: {sql_error}")
            print(f"ERRO SQL: {sql_error}")
            return {}

        row = cursor.fetchone()
        if not row:
            log.warning(f"[DB DETAILS] Sessão com ID {session_id} não encontrada")
            print(f"Sessão com ID {session_id} não encontrada")
            return {}

        # Obter nomes das colunas
        column_names = [description[0] for description in cursor.description]
        log.info(f"[DB DETAILS] Colunas encontradas: {column_names}")

        # Criar dicionário com os dados
        session_data = dict(zip(column_names, row))
        log.info(f"[DB DETAILS] Dados brutos recuperados para sessão ID {session_id}")

        print(f"\n{'='*40} DADOS BRUTOS RECUPERADOS {'='*40}")
        for key in ['transformer_inputs', 'losses_data', 'impulse_data',
                   'dieletric_data', 'applied_voltage_data', 'induced_voltage_data',
                   'short_circuit_data', 'temperature_rise_data']:
            value = session_data.get(key, '')
            print(f"{key}: {len(value)} bytes")
            if len(value) < 100:
                print(f"  Conteúdo: {value}")
            else:
                print(f"  Conteúdo (primeiros 100 bytes): {value[:100]}...")

        # Converter strings JSON para dicionários Python
        print(f"\n{'='*40} PROCESSANDO DADOS {'='*40}")
        for key in ['transformer_inputs', 'losses_data', 'impulse_data',
                   'dieletric_data', 'applied_voltage_data', 'induced_voltage_data',
                   'short_circuit_data', 'temperature_rise_data']:
            print(f"\n{'-'*30} PROCESSANDO: {key} {'-'*30}")
            if session_data.get(key):
                try:
                    log.info(f"[DB DETAILS] Convertendo JSON para {key}")
                    print(f"Convertendo JSON para dicionário...")

                    # Carrega o JSON
                    json_str = session_data[key]
                    print(f"JSON lido do DB para '{key}': {json_str[:150]}{'...' if len(json_str) > 150 else ''}")
                    loaded_data = json.loads(json_str)

                    # Verificar marcadores especiais
                    if isinstance(loaded_data, dict):
                        # Verificar marcador de dados vazios
                        if loaded_data.get("_empty_marker") is True:
                            log.info(f"[DB DETAILS] Marcador '_empty_marker' encontrado em {key}. Substituindo por {{}}.")
                            print(f"Marcador '_empty_marker' encontrado em {key}. Substituindo por {{}}.")
                            session_data[key] = {}
                        # Verificar marcador de falha de conversão
                        elif loaded_data.get("_conversion_failed") is True:
                            error_msg = loaded_data.get("_error", "Erro desconhecido")
                            log.warning(f"[DB DETAILS] Dados de {key} contêm informações de erro de conversão: {error_msg}")
                            print(f"⚠ Dados contêm informações de erro de conversão: {error_msg}")

                            # Manter as informações de diagnóstico para referência
                            session_data[key] = loaded_data
                            print(f"Mantendo informações de diagnóstico para referência")
                        # Verificar marcador de falha de serialização
                        elif loaded_data.get("_serialization_failed") is True:
                            error_msg = loaded_data.get("_error", "Erro desconhecido")
                            log.warning(f"[DB DETAILS] Dados de {key} contêm informações de erro de serialização: {error_msg}")
                            print(f"⚠ Dados contêm informações de erro de serialização: {error_msg}")

                            # Manter as informações de diagnóstico para referência
                            session_data[key] = loaded_data
                            print(f"Mantendo informações de diagnóstico para referência")
                        else:
                            # Dados normais
                            session_data[key] = loaded_data
                    else:
                        # Não é um dicionário
                        session_data[key] = loaded_data

                    # Continua com a lógica de log/diagnóstico
                    if isinstance(session_data[key], dict):
                        log.info(f"[DB DETAILS] {key} contém {len(session_data[key])} chaves")
                        print(f"Convertido com sucesso: dict com {len(session_data[key])} chaves")

                        # Log das chaves principais para diagnóstico
                        if len(session_data[key]) > 0:
                            keys = list(session_data[key].keys())
                            log.info(f"[DB DETAILS] {key} chaves principais: {keys}")
                            print(f"Chaves: {keys}")
                    else:
                        log.info(f"[DB DETAILS] {key} não é um dicionário, tipo: {type(session_data[key])}")
                        print(f"Não é um dicionário, tipo: {type(session_data[key]).__name__}")
                except json.JSONDecodeError as json_error:
                    log.warning(f"[DB DETAILS] Erro ao decodificar JSON para {key}: {json_error}")
                    print(f"ERRO ao decodificar JSON: {json_error}")

                    # Tentar recuperar parte do JSON se possível
                    try:
                        # Verificar se é um erro de formato ou se há dados parciais
                        json_str = session_data[key]
                        if json_str.startswith('{') and json_str.endswith('}'):
                            log.info(f"[DB DETAILS] Tentando recuperar dados parciais de {key}")
                            print("Tentando recuperar dados parciais...")

                            # Tentar extrair pares chave-valor válidos
                            import re
                            pairs = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|[0-9.]+|true|false|null|\{[^}]*\}|\[[^\]]*\])', json_str)
                            if pairs:
                                partial_data = {k: eval(v) for k, v in pairs}
                                session_data[key] = partial_data
                                log.info(f"[DB DETAILS] Recuperados {len(partial_data)} pares chave-valor de {key}")
                                print(f"Recuperados {len(partial_data)} pares chave-valor")
                            else:
                                session_data[key] = {}
                                print("Não foi possível recuperar dados parciais, usando dicionário vazio")
                        else:
                            session_data[key] = {}
                            print("Formato JSON inválido, usando dicionário vazio")
                    except Exception as recovery_error:
                        session_data[key] = {}
                        print(f"ERRO ao tentar recuperar dados parciais: {recovery_error}")
                except Exception as other_error:
                    log.warning(f"[DB DETAILS] Outro erro ao processar {key}: {other_error}")
                    print(f"ERRO ao processar dados: {other_error}")
                    session_data[key] = {}
            else:
                log.info(f"[DB DETAILS] {key} está vazio ou é None")
                print("Dados vazios ou None, usando dicionário vazio")
                session_data[key] = {}

        # Mapear para os nomes dos stores
        store_data = {
            'transformer-inputs-store': session_data.get('transformer_inputs', {}),
            'losses-store': session_data.get('losses_data', {}),
            'impulse-store': session_data.get('impulse_data', {}),
            'dieletric-analysis-store': session_data.get('dieletric_data', {}),
            'applied-voltage-store': session_data.get('applied_voltage_data', {}),
            'induced-voltage-store': session_data.get('induced_voltage_data', {}),
            'short-circuit-store': session_data.get('short_circuit_data', {}),
            'temperature-rise-store': session_data.get('temperature_rise_data', {})
        }
        log.info("[DB DETAILS] Dados mapeados para os nomes dos stores")
        print("\nDados mapeados para os nomes dos stores")

        # Verificar se todos os stores estão presentes
        print(f"\n{'='*40} RESUMO DOS DADOS CARREGADOS {'='*40}")
        for store_name in store_data:
            data = store_data[store_name]
            if not data:
                log.warning(f"[DB DETAILS] Store {store_name} está vazio")
                print(f"{store_name}: VAZIO")
            else:
                if isinstance(data, dict):
                    print(f"{store_name}: dict com {len(data)} chaves: {list(data.keys())}")
                else:
                    print(f"{store_name}: {type(data).__name__}")

        # Adicionar metadados
        result = {
            'id': session_data.get('id'),
            'timestamp': session_data.get('timestamp'),
            'session_name': session_data.get('session_name'),
            'notes': session_data.get('notes'),
            'store_data': store_data
        }

        log.info(f"[DB DETAILS] Detalhes da sessão ID {session_id} recuperados com sucesso")
        print(f"\n{'='*40} RESULTADO {'='*40}")
        print(f"Sessão ID {session_id} carregada com sucesso!")
        print(f"Nome: {result['session_name']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"{'='*80}\n\n")
        return result
    except Exception as e:
        log.error(f"[DB DETAILS] Erro ao recuperar detalhes da sessão {session_id}: {e}")
        print(f"\n{'='*40} ERRO {'='*40}")
        print(f"ERRO ao recuperar detalhes da sessão {session_id}: {e}")
        import traceback
        traceback_str = traceback.format_exc()
        log.error(f"[DB DETAILS] Traceback: {traceback_str}")
        print(f"Traceback: {traceback_str}")
        print(f"{'='*80}\n\n")
        return {}
    finally:
        if conn:
            try:
                conn.close()
                log.info("[DB DETAILS] Conexão fechada")
            except Exception as close_error:
                log.error(f"[DB DETAILS] Erro ao fechar conexão: {close_error}")

def update_test_session(session_id: int, updated_data: Dict[str, Any]) -> bool:
    """
    Atualiza uma sessão existente.

    Args:
        session_id: ID da sessão a ser atualizada
        updated_data: Dados atualizados da sessão

    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    log.info(f"[DB UPDATE] Iniciando atualização da sessão ID {session_id}")
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Verificar se a sessão existe
        log.info(f"[DB UPDATE] Verificando se a sessão ID {session_id} existe")
        cursor.execute('SELECT id FROM test_sessions WHERE id = ?', (session_id,))
        if not cursor.fetchone():
            conn.close()
            log.warning(f"[DB UPDATE] Sessão com ID {session_id} não encontrada para atualização")
            return False

        # Extrair dados dos stores
        store_data = updated_data.get('store_data', {})
        log.info(f"[DB UPDATE] Dados dos stores extraídos: {len(store_data)} stores")

        # Preparar dados para atualização
        update_data = {
            'session_name': updated_data.get('session_name'),
            'notes': updated_data.get('notes'),
            'transformer_inputs': json.dumps(store_data.get('transformer-inputs-store', {})),
            'losses_data': json.dumps(store_data.get('losses-store', {})),
            'impulse_data': json.dumps(store_data.get('impulse-store', {})),
            'dieletric_data': json.dumps(store_data.get('dieletric-analysis-store', {})),
            'applied_voltage_data': json.dumps(store_data.get('applied-voltage-store', {})),
            'induced_voltage_data': json.dumps(store_data.get('induced-voltage-store', {})),
            'short_circuit_data': json.dumps(store_data.get('short-circuit-store', {})),
            'temperature_rise_data': json.dumps(store_data.get('temperature-rise-store', {}))
        }

        # Log detalhado do que está sendo atualizado para cada módulo
        log.info(f"[DB UPDATE] Preparando dados para atualização da sessão ID {session_id}")
        log.info(f"[DB UPDATE] Transformer Inputs: {len(update_data['transformer_inputs'])} bytes")
        log.info(f"[DB UPDATE] Losses Data: {len(update_data['losses_data'])} bytes")
        log.info(f"[DB UPDATE] Impulse Data: {len(update_data['impulse_data'])} bytes")
        log.info(f"[DB UPDATE] Dieletric Data: {len(update_data['dieletric_data'])} bytes")
        log.info(f"[DB UPDATE] Applied Voltage Data: {len(update_data['applied_voltage_data'])} bytes")
        log.info(f"[DB UPDATE] Induced Voltage Data: {len(update_data['induced_voltage_data'])} bytes")
        log.info(f"[DB UPDATE] Short Circuit Data: {len(update_data['short_circuit_data'])} bytes")
        log.info(f"[DB UPDATE] Temperature Rise Data: {len(update_data['temperature_rise_data'])} bytes")

        # Construir a query de atualização
        set_clauses = []
        values = []

        for key, value in update_data.items():
            if value is not None:  # Só atualiza campos que foram fornecidos
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            conn.close()
            log.warning("[DB UPDATE] Nenhum dado fornecido para atualização")
            return False

        # Adicionar ID à lista de valores
        values.append(session_id)

        log.info(f"[DB UPDATE] Query construída com {len(set_clauses)} campos para atualizar")

        # Executar a atualização
        log.info(f"[DB UPDATE] Executando atualização para sessão ID {session_id}")
        cursor.execute(f'''
        UPDATE test_sessions
        SET {', '.join(set_clauses)}
        WHERE id = ?
        ''', values)

        conn.commit()
        conn.close()

        log.info(f"[DB UPDATE] Sessão com ID {session_id} atualizada com sucesso")
        return True
    except Exception as e:
        log.error(f"[DB UPDATE] Erro ao atualizar sessão {session_id}: {e}")
        return False

def session_name_exists(session_name: str) -> bool:
    """
    Verifica se já existe uma sessão com o nome especificado.

    Args:
        session_name: Nome da sessão a ser verificado

    Returns:
        bool: True se o nome já existe, False caso contrário
    """
    log.info(f"[DB CHECK] Verificando se o nome de sessão '{session_name}' já existe")
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Buscar sessões com o nome exato (case insensitive)
        cursor.execute('''
        SELECT COUNT(*) FROM test_sessions WHERE LOWER(session_name) = LOWER(?)
        ''', (session_name,))

        count = cursor.fetchone()[0]
        conn.close()

        exists = count > 0
        log.info(f"[DB CHECK] Nome de sessão '{session_name}' existe? {exists}")
        return exists
    except Exception as e:
        log.error(f"[DB CHECK] Erro ao verificar nome de sessão '{session_name}': {e}")
        return False

def delete_test_session(session_id: int) -> bool:
    """
    Exclui uma sessão do banco de dados.

    Args:
        session_id: ID da sessão a ser excluída

    Returns:
        bool: True se a exclusão foi bem-sucedida, False caso contrário
    """
    log.info(f"[DB DELETE] Iniciando exclusão da sessão ID {session_id}")
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Verificar se a sessão existe
        log.info(f"[DB DELETE] Verificando se a sessão ID {session_id} existe")
        cursor.execute('SELECT id, session_name FROM test_sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            log.warning(f"[DB DELETE] Sessão com ID {session_id} não encontrada para exclusão")
            return False

        session_name = row[1] if len(row) > 1 else "Desconhecido"
        log.info(f"[DB DELETE] Sessão encontrada: ID {session_id}, Nome '{session_name}'")

        # Excluir a sessão
        log.info(f"[DB DELETE] Executando exclusão da sessão ID {session_id}")
        cursor.execute('DELETE FROM test_sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()

        log.info(f"[DB DELETE] Sessão com ID {session_id} ('{session_name}') excluída com sucesso")
        return True
    except Exception as e:
        log.error(f"[DB DELETE] Erro ao excluir sessão {session_id}: {e}")
        return False