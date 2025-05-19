# utils/logger.py
import datetime
import json
import logging
import sys
import time
import traceback
from functools import wraps

# --- Logging Configuration ---

# Define o nome do arquivo de log com base na data atual
log_filename = f"app_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"

# Define o nível de log desejado (pode ser movido para config.py depois)
# DEBUG: Mais verboso, bom para desenvolvimento
# INFO: Informações gerais sobre o fluxo da aplicação
# WARNING: Avisos sobre situações inesperadas, mas que não impedem o funcionamento
# ERROR: Erros que impedem uma operação específica
# CRITICAL: Erros graves que podem parar a aplicação
LOG_LEVEL = logging.INFO

# Configurar loggers específicos
# Mostrar apenas logs relacionados aos stores e ao MCP
logging.getLogger('app_core.transformer_mcp').setLevel(logging.DEBUG)
logging.getLogger('utils.mcp_persistence').setLevel(logging.DEBUG)
logging.getLogger('utils.mcp_diagnostics').setLevel(logging.DEBUG)
logging.getLogger('utils.store_diagnostics').setLevel(logging.DEBUG)

# Callbacks relacionados aos stores
logging.getLogger('callbacks.transformer_inputs').setLevel(logging.DEBUG)
logging.getLogger('callbacks.global_updates').setLevel(logging.DEBUG)
logging.getLogger('callbacks.insulation_level_callbacks').setLevel(logging.INFO)
logging.getLogger('callbacks.isolation_callbacks').setLevel(logging.INFO)

# Reduzir verbosidade de outros loggers
logging.getLogger('app_core.isolation_repo').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('components.transformer_info_template').setLevel(logging.WARNING)

# Define o formato das mensagens de log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Remove handlers existentes para evitar duplicação se este módulo for recarregado
# (Importante em ambientes de desenvolvimento com recarregamento automático)
root_logger = logging.getLogger()
if root_logger.hasHandlers():
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

# Criar um filtro personalizado para destacar logs relacionados aos stores e ao MCP
class StoreAndMCPFilter(logging.Filter):
    def filter(self, record):
        # Verificar se o log está relacionado aos stores ou ao MCP
        if any(name in record.name for name in ['transformer_mcp', 'mcp_persistence', 'store_diagnostics', 'transformer_inputs']):
            # Adicionar um prefixo ao início da mensagem para destacar
            if not record.msg.startswith('[STORE/MCP]'):
                record.msg = f'[STORE/MCP] {record.msg}'
        return True

# Adicionar o filtro ao logger raiz
root_logger.addFilter(StoreAndMCPFilter())

# Configura o logging básico
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        # Handler para escrever logs em um arquivo
        logging.FileHandler(log_filename, mode="a", encoding="utf-8"),
        # Handler para exibir logs no console
        logging.StreamHandler(sys.stdout),  # Usar sys.stdout explicitamente
    ],
    # força a reconfiguração caso já tenha sido configurado em outro lugar (menos provável agora)
    force=True,
)

# Exemplo de como obter um logger em outro módulo:
# import logging
# log = logging.getLogger(__name__)
# log.info("Esta é uma mensagem de informação.")

# Adiciona uma mensagem inicial ao log para confirmar a configuração
logging.getLogger(__name__).info(
    f"Logging configurado. Nível: {logging.getLevelName(LOG_LEVEL)}. Arquivo: {log_filename}"
)

# Não há necessidade de exportar nada explicitamente daqui.
# A configuração é aplicada globalmente ao módulo logging.

# --- Funções de Log Aprimoradas ---


def log_detailed(logger, level, message, module=None, function=None, data=None, exception=None):
    """
    Função para registrar logs detalhados com informações adicionais.

    Args:
        logger: O objeto logger a ser usado
        level: Nível de log (debug, info, warning, error, critical)
        message: Mensagem principal do log
        module: Nome do módulo (opcional)
        function: Nome da função (opcional)
        data: Dados adicionais para incluir no log (opcional)
        exception: Exceção a ser registrada (opcional)
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Prepara os dados para o log
    log_data = {"timestamp": timestamp, "message": message}

    if module:
        log_data["module"] = module

    if function:
        log_data["function"] = function

    if data:
        # Tenta converter dados complexos para string
        try:
            if isinstance(data, dict):
                # Limita o tamanho dos valores para evitar logs muito grandes
                limited_data = {}
                for k, v in data.items():
                    if isinstance(v, (dict, list)) and len(str(v)) > 1000:
                        limited_data[k] = f"{str(v)[:1000]}... (truncado)"
                    else:
                        limited_data[k] = v
                log_data["data"] = limited_data
            else:
                log_data["data"] = str(data)[:2000] + "..." if len(str(data)) > 2000 else data
        except Exception as e:
            log_data["data_error"] = f"Erro ao serializar dados: {str(e)}"

    if exception:
        log_data["exception"] = str(exception)
        log_data["traceback"] = traceback.format_exc()

    # Formata a mensagem de log
    try:
        log_message = json.dumps(log_data, ensure_ascii=False, default=str)
    except Exception:
        # Fallback se a serialização JSON falhar
        log_message = f"{timestamp} - {message} - Erro ao serializar dados adicionais"

    # Registra a mensagem no nível apropriado
    if level == "debug":
        logger.debug(log_message)
    elif level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    elif level == "critical":
        logger.critical(log_message)
    else:
        logger.info(log_message)





# Função para verificar a existência de stores
def check_store_exists(store_data, store_name):
    """
    Verifica se um store existe e tem dados válidos.

    Args:
        store_data: Os dados do store
        store_name: O nome do store para mensagens de log

    Returns:
        bool: True se o store existe e tem dados válidos, False caso contrário
    """
    if store_data is None:
        logging.warning(f"Store {store_name} não existe")
        return False

    if isinstance(store_data, dict) and not store_data:
        logging.warning(f"Store {store_name} está vazio")
        return False

    return True
