#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilitário para testar a funcionalidade do banco de dados.
Permite verificar se o banco de dados pode ser acessado e se os dados podem ser salvos e recuperados.
"""

import logging
import sys
import os
import json
from typing import Dict, Any

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger(__name__)

# Adicionar o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar funções do gerenciador de banco de dados
from utils.db_manager import (
    connect_db,
    save_test_session,
    get_test_session_details,
    get_all_test_sessions,
    delete_test_session,
)


def test_database_connection():
    """Testa a conexão com o banco de dados."""
    try:
        conn = connect_db()
        log.info("✓ Conexão com o banco de dados estabelecida com sucesso.")

        # Verificar o esquema atual da tabela
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_sessions)")
        columns = cursor.fetchall()

        log.info("Esquema atual da tabela test_sessions:")
        for col in columns:
            log.info(f"  - {col}")

        conn.close()
        return True
    except Exception as e:
        log.error(f"✗ Erro ao conectar ao banco de dados: {e}")
        return False


def test_save_and_retrieve():
    """Testa o salvamento e recuperação de dados no banco de dados."""
    # Dados de teste
    test_data = {
        "transformer-inputs-store": {
            "tipo_transformador": "Trifásico",
            "potencia_mva": 100,
            "tensao_at": 138,
            "tensao_bt": 13.8,
            "frequencia": 60,
        },
        "losses-store": {
            "perdas_vazio": 50,
            "perdas_carga": 500,
        },
    }

    test_session_name = "Sessão de Teste"
    test_notes = "Notas de teste para verificar a funcionalidade do banco de dados."

    try:
        # Salvar dados
        log.info("Tentando salvar dados de teste...")
        session_id = save_test_session(test_data, test_session_name, test_notes)

        if session_id <= 0:
            log.error(f"✗ Erro ao salvar dados de teste: ID inválido {session_id}")
            return False

        log.info(f"✓ Dados salvos com sucesso. ID da sessão: {session_id}")

        # Recuperar dados
        log.info(f"Tentando recuperar dados da sessão {session_id}...")
        session_details = get_test_session_details(session_id)

        if not session_details:
            log.error(f"✗ Erro ao recuperar dados da sessão {session_id}")
            return False

        log.info(f"✓ Dados recuperados com sucesso: {session_details.get('session_name')}")

        # Verificar se os dados recuperados correspondem aos dados salvos
        store_data = session_details.get("store_data", {})
        transformer_data = store_data.get("transformer-inputs-store", {})

        if transformer_data.get("potencia_mva") == test_data["transformer-inputs-store"]["potencia_mva"]:
            log.info("✓ Dados recuperados correspondem aos dados salvos.")
        else:
            log.warning("⚠ Dados recuperados não correspondem exatamente aos dados salvos.")
            log.warning(f"Original: {test_data['transformer-inputs-store']}")
            log.warning(f"Recuperado: {transformer_data}")

        # Listar todas as sessões
        log.info("Listando todas as sessões...")
        sessions = get_all_test_sessions()
        log.info(f"✓ {len(sessions)} sessões encontradas.")

        # Excluir a sessão de teste
        log.info(f"Excluindo sessão de teste {session_id}...")
        success = delete_test_session(session_id)

        if success:
            log.info(f"✓ Sessão {session_id} excluída com sucesso.")
        else:
            log.error(f"✗ Erro ao excluir sessão {session_id}")
            return False

        return True
    except Exception as e:
        log.error(f"✗ Erro durante o teste de salvamento e recuperação: {e}")
        import traceback
        log.error(f"Traceback: {traceback.format_exc()}")
        return False


def run_all_tests():
    """Executa todos os testes de banco de dados."""
    log.info("=" * 50)
    log.info("INICIANDO TESTES DE BANCO DE DADOS")
    log.info("=" * 50)

    # Teste de conexão
    log.info("\n--- Teste de Conexão ---")
    connection_result = test_database_connection()

    if not connection_result:
        log.error("✗ Teste de conexão falhou. Abortando testes subsequentes.")
        return False

    # Teste de salvamento e recuperação
    log.info("\n--- Teste de Salvamento e Recuperação ---")
    save_retrieve_result = test_save_and_retrieve()

    # Resultado final
    log.info("\n" + "=" * 50)
    if connection_result and save_retrieve_result:
        log.info("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        return True
    else:
        log.error("✗ ALGUNS TESTES FALHARAM!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
