"""
Utilitário para rastrear o uso da aplicação.
Usa SQLite para armazenar contadores de uso de forma eficiente.
"""
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

log = logging.getLogger(__name__)


class UsageTracker:
    """
    Classe para rastrear o uso da aplicação usando SQLite.
    """

    def __init__(self, db_path: str = "usage.db"):
        """
        Inicializa o rastreador de uso.

        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """
        Garante que o banco de dados existe e tem a estrutura correta.
        """
        try:
            # Criar diretório pai se não existir
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Conectar ao banco de dados e criar tabela se não existir
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Criar tabela de contadores
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_counters (
                    id INTEGER PRIMARY KEY,
                    counter_name TEXT UNIQUE,
                    value INTEGER,
                    last_updated TEXT
                )
            """
            )

            # Criar tabela de histórico
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_history (
                    id INTEGER PRIMARY KEY,
                    counter_name TEXT,
                    timestamp TEXT,
                    action TEXT,
                    value INTEGER
                )
            """
            )

            conn.commit()
            conn.close()
            log.debug(f"Banco de dados de uso inicializado: {self.db_path}")
        except Exception as e:
            log.error(f"Erro ao inicializar banco de dados de uso: {e}", exc_info=True)

    def increment_counter(self, counter_name: str = "app_usage") -> Tuple[int, bool]:
        """
        Incrementa um contador e verifica se atingiu o limite.

        Args:
            counter_name: Nome do contador

        Returns:
            Tuple[int, bool]: (valor atual, True se atingiu o limite)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obter valor atual
            cursor.execute(
                "SELECT value FROM usage_counters WHERE counter_name = ?", (counter_name,)
            )
            result = cursor.fetchone()

            # Se o contador não existe, criar com valor 1
            if result is None:
                current_value = 1
                cursor.execute(
                    "INSERT INTO usage_counters (counter_name, value, last_updated) VALUES (?, ?, ?)",
                    (counter_name, current_value, datetime.now().isoformat()),
                )
            else:
                current_value = result[0] + 1
                cursor.execute(
                    "UPDATE usage_counters SET value = ?, last_updated = ? WHERE counter_name = ?",
                    (current_value, datetime.now().isoformat(), counter_name),
                )

            # Registrar no histórico
            cursor.execute(
                "INSERT INTO usage_history (counter_name, timestamp, action, value) VALUES (?, ?, ?, ?)",
                (counter_name, datetime.now().isoformat(), "increment", current_value),
            )

            conn.commit()
            conn.close()

            # Verificar se atingiu o limite (configurado externamente)
            import config

            usage_limit = getattr(config, "USAGE_LIMIT", 1000)
            reached_limit = current_value >= usage_limit

            if reached_limit:
                log.warning(f"Limite de uso atingido: {current_value}/{usage_limit}")
            else:
                log.info(f"Uso incrementado: {current_value}/{usage_limit}")

            return current_value, reached_limit

        except Exception as e:
            log.error(f"Erro ao incrementar contador de uso: {e}", exc_info=True)
            return 0, False

    def get_counter(self, counter_name: str = "app_usage") -> Optional[int]:
        """
        Obtém o valor atual de um contador.

        Args:
            counter_name: Nome do contador

        Returns:
            Optional[int]: Valor atual ou None se não existir
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT value FROM usage_counters WHERE counter_name = ?", (counter_name,)
            )
            result = cursor.fetchone()

            conn.close()
            return result[0] if result else None

        except Exception as e:
            log.error(f"Erro ao obter contador de uso: {e}", exc_info=True)
            return None


