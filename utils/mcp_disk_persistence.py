"""
Utilitários para persistência de dados do MCP em disco.
Permite salvar e carregar o estado do MCP entre sessões da aplicação.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.paths import get_data_dir

log = logging.getLogger(__name__)

# Diretório para armazenar os dados do MCP
MCP_DATA_DIR = get_data_dir() / "mcp_state"
# Arquivo principal para armazenar os dados do MCP
MCP_DATA_FILE = MCP_DATA_DIR / "mcp_state.json"
# Arquivo de backup para armazenar os dados do MCP
MCP_BACKUP_DIR = MCP_DATA_DIR / "backups"
# Número máximo de backups a manter
MAX_BACKUPS = 5


def ensure_mcp_dirs() -> None:
    """
    Garante que os diretórios necessários para persistência do MCP existam.
    """
    MCP_DATA_DIR.mkdir(exist_ok=True, parents=True)
    MCP_BACKUP_DIR.mkdir(exist_ok=True, parents=True)
    log.info(f"Diretórios para persistência do MCP criados: {MCP_DATA_DIR}, {MCP_BACKUP_DIR}")


def save_mcp_state_to_disk(mcp_data: Dict[str, Any], create_backup: bool = True) -> bool:
    """
    Salva o estado atual do MCP em disco.

    Args:
        mcp_data: Dicionário com os dados do MCP
        create_backup: Se True, cria um backup antes de salvar

    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    ensure_mcp_dirs()

    try:
        # Criar backup se solicitado e se o arquivo existir
        if create_backup and MCP_DATA_FILE.exists():
            create_mcp_backup()

        # Adicionar metadados
        data_with_metadata = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "stores": mcp_data,
        }

        # Salvar dados em formato JSON
        with open(MCP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2, default=str)

        log.info(f"Estado do MCP salvo em disco: {MCP_DATA_FILE}")
        return True
    except Exception as e:
        log.error(f"Erro ao salvar estado do MCP em disco: {e}", exc_info=True)
        return False


def create_mcp_backup() -> Optional[Path]:
    """
    Cria um backup do arquivo de estado do MCP.

    Returns:
        Optional[Path]: Caminho para o arquivo de backup criado, ou None se falhou
    """
    if not MCP_DATA_FILE.exists():
        log.warning(
            f"Arquivo de estado do MCP não existe, não é possível criar backup: {MCP_DATA_FILE}"
        )
        return None

    try:
        # Criar nome de arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = MCP_BACKUP_DIR / f"mcp_state_{timestamp}.json"

        # Copiar arquivo
        with open(MCP_DATA_FILE, "r", encoding="utf-8") as src:
            with open(backup_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())

        log.info(f"Backup do estado do MCP criado: {backup_file}")

        # Limpar backups antigos
        cleanup_old_backups()

        return backup_file
    except Exception as e:
        log.error(f"Erro ao criar backup do estado do MCP: {e}", exc_info=True)
        return None


def cleanup_old_backups() -> None:
    """
    Remove backups antigos, mantendo apenas os MAX_BACKUPS mais recentes.
    """
    try:
        # Listar todos os arquivos de backup
        backup_files = list(MCP_BACKUP_DIR.glob("mcp_state_*.json"))

        # Ordenar por data de modificação (mais recente primeiro)
        backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Remover arquivos excedentes
        if len(backup_files) > MAX_BACKUPS:
            for old_file in backup_files[MAX_BACKUPS:]:
                old_file.unlink()
                log.info(f"Backup antigo removido: {old_file}")
    except Exception as e:
        log.error(f"Erro ao limpar backups antigos: {e}", exc_info=True)


def load_mcp_state_from_disk() -> Tuple[Dict[str, Any], bool]:
    """
    Carrega o estado do MCP a partir do disco.

    Returns:
        Tuple[Dict[str, Any], bool]: (Dados carregados, Flag indicando sucesso)
    """
    ensure_mcp_dirs()

    if not MCP_DATA_FILE.exists():
        log.warning(f"Arquivo de estado do MCP não encontrado: {MCP_DATA_FILE}")
        return {}, False

    try:
        # Carregar dados do arquivo JSON
        with open(MCP_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verificar se os dados têm o formato esperado
        if not isinstance(data, dict) or "stores" not in data:
            log.error(f"Formato inválido no arquivo de estado do MCP: {MCP_DATA_FILE}")
            return {}, False

        # Extrair dados dos stores
        stores_data = data.get("stores", {})

        # Log de diagnóstico
        log.info(f"Estado do MCP carregado do disco: {MCP_DATA_FILE}")
        log.info(f"Timestamp dos dados: {data.get('timestamp', 'desconhecido')}")
        log.info(f"Stores carregados: {list(stores_data.keys())}")

        return stores_data, True
    except json.JSONDecodeError as e:
        log.error(f"Erro ao decodificar JSON do arquivo de estado do MCP: {e}", exc_info=True)
        return {}, False
    except Exception as e:
        log.error(f"Erro ao carregar estado do MCP do disco: {e}", exc_info=True)
        return {}, False


def get_available_backups() -> List[Dict[str, Any]]:
    """
    Obtém a lista de backups disponíveis.

    Returns:
        List[Dict[str, Any]]: Lista de backups com metadados
    """
    ensure_mcp_dirs()

    try:
        # Listar todos os arquivos de backup
        backup_files = list(MCP_BACKUP_DIR.glob("mcp_state_*.json"))

        # Criar lista de backups com metadados
        backups = []
        for file in backup_files:
            try:
                # Obter data de modificação
                mod_time = datetime.fromtimestamp(os.path.getmtime(file))

                # Obter tamanho do arquivo
                size_bytes = os.path.getsize(file)

                # Tentar extrair timestamp do nome do arquivo
                filename = file.name
                timestamp_str = filename.replace("mcp_state_", "").replace(".json", "")

                backups.append(
                    {
                        "file_path": str(file),
                        "filename": filename,
                        "timestamp": timestamp_str,
                        "modified": mod_time.isoformat(),
                        "size_bytes": size_bytes,
                        "size_kb": round(size_bytes / 1024, 1),
                    }
                )
            except Exception as e:
                log.error(f"Erro ao processar arquivo de backup {file}: {e}")

        # Ordenar por data de modificação (mais recente primeiro)
        backups.sort(key=lambda x: x["modified"], reverse=True)

        return backups
    except Exception as e:
        log.error(f"Erro ao obter lista de backups: {e}", exc_info=True)
        return []


def restore_from_backup(backup_file: str) -> Tuple[Dict[str, Any], bool]:
    """
    Restaura o estado do MCP a partir de um arquivo de backup.

    Args:
        backup_file: Caminho para o arquivo de backup

    Returns:
        Tuple[Dict[str, Any], bool]: (Dados restaurados, Flag indicando sucesso)
    """
    backup_path = Path(backup_file)
    if not backup_path.exists():
        log.error(f"Arquivo de backup não encontrado: {backup_file}")
        return {}, False

    try:
        # Criar backup do estado atual antes de restaurar
        if MCP_DATA_FILE.exists():
            create_mcp_backup()

        # Carregar dados do arquivo de backup
        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verificar se os dados têm o formato esperado
        if not isinstance(data, dict) or "stores" not in data:
            log.error(f"Formato inválido no arquivo de backup: {backup_file}")
            return {}, False

        # Extrair dados dos stores
        stores_data = data.get("stores", {})

        # Copiar arquivo de backup para o arquivo principal
        with open(MCP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        log.info(f"Estado do MCP restaurado a partir do backup: {backup_file}")
        return stores_data, True
    except json.JSONDecodeError as e:
        log.error(f"Erro ao decodificar JSON do arquivo de backup: {e}", exc_info=True)
        return {}, False
    except Exception as e:
        log.error(f"Erro ao restaurar estado do MCP a partir do backup: {e}", exc_info=True)
        return {}, False
