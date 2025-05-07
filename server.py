"""
Ponto de entrada alternativo para a aplicação.
Inicializa o MCP com dados padrão antes de iniciar o servidor Dash.
"""
import logging
import os
import sys

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Importar configurações
try:
    import config
    log.info("Configurações carregadas com sucesso")
except ImportError:
    log.critical("Não foi possível importar config.py")
    sys.exit(1)

# Configurar logging avançado
try:
    # Garantir que o diretório de logs existe
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # Configurar logging
    log_file_path = os.path.join(config.LOG_DIR, "server.log")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formatar logs
    formatter = logging.Formatter(
        fmt=config.LOGGING_FORMAT,
        datefmt=config.LOGGING_DATE_FORMAT
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configurar logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.LOGGING_LEVEL)
    
    # Remover handlers existentes e adicionar os novos
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    log.info(f"Logging configurado. Nível: {logging.getLevelName(config.LOGGING_LEVEL)}. Arquivo: {log_file_path}")
except Exception as e:
    log.error(f"Erro ao configurar logging avançado: {e}", exc_info=True)

# Inicializar MCP com dados padrão
log.info("Inicializando MCP com dados padrão...")
try:
    # Importar módulo de inicialização
    from app_core.startup import load_default_transformer_data
    
    # Carregar dados padrão
    default_data = load_default_transformer_data()
    if default_data:
        log.info("Dados padrão carregados com sucesso")
    else:
        log.warning("Não foi possível carregar dados padrão")
except ImportError as e:
    log.error(f"Erro ao importar módulo de inicialização: {e}", exc_info=True)
except Exception as e:
    log.error(f"Erro ao carregar dados padrão: {e}", exc_info=True)

# Importar aplicação Dash
try:
    from app import app, server
    log.info("Aplicação Dash importada com sucesso")
except ImportError as e:
    log.critical(f"Não foi possível importar a aplicação Dash: {e}", exc_info=True)
    sys.exit(1)

# Verificar se o MCP foi inicializado corretamente
if hasattr(app, 'mcp') and app.mcp is not None:
    log.info("MCP inicializado com sucesso")
    
    # Verificar se os dados padrão foram carregados
    transformer_data = app.mcp.get_data("transformer-inputs-store")
    if transformer_data:
        log.info(f"MCP contém dados do transformador: {len(transformer_data) if isinstance(transformer_data, dict) else 'Não é dict'} campos")
    else:
        log.warning("MCP não contém dados do transformador")
else:
    log.warning("MCP não inicializado ou não disponível")

# Ponto de entrada para WSGI
if __name__ == "__main__":
    # Iniciar servidor
    host = getattr(config, "HOST", "127.0.0.1")
    port = getattr(config, "PORT", 8050)
    debug_mode = getattr(config, "DEBUG_MODE", False)
    
    log.info(f"Iniciando servidor em http://{host}:{port}/ (Debug: {debug_mode})")
    
    try:
        # Sempre desativar debug e reloader para evitar problemas com o MCP
        app.run(
            debug=False,  # Forçar debug=False para evitar reinicialização do MCP
            host=host,
            port=port,
            use_reloader=False,  # Desativar reloader para evitar reinicialização do MCP
            threaded=True,  # Usar threading para melhor desempenho e estabilidade
        )
        log.info("Servidor encerrado normalmente")
    except Exception as e:
        log.critical(f"Erro ao iniciar servidor: {e}", exc_info=True)
        sys.exit(1)
