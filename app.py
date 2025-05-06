# app_fixed.py - Modified version of app.py to fix socket error
import dash
from dash import Input, html as dash_html, dcc, Output
import dash_bootstrap_components as dbc
import logging
import webbrowser
from threading import Timer
import datetime
import os
import traceback
import sys
from dash.exceptions import PreventUpdate, InvalidCallbackReturnValue

# --- 1. Load Configuration FIRST ---
try:
    import config
    # Configuração carregada
except ImportError:
    print("ERRO CRÍTICO: Não foi possível importar config.py.")
    # Fallback basic config if needed, or exit
    class ConfigFallback:
        LOG_DIR = '.'
        LOG_FILE = 'app_fallback.log'
        LOGGING_LEVEL = logging.INFO
        LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
        LOGGING_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
        APP_TITLE = "Simulador (Erro Config)"
        DEFAULT_THEME_URL = dbc.themes.DARKLY # Default to a theme
        DEFAULT_THEME_NAME = "DARKLY"
        ASSETS_DIR = "assets"
        USAGE_COUNT_FILE = "usage_count.txt"
        USAGE_LIMIT = 615 # Example fallback
        HOST = '127.0.0.1'
        PORT = 8060
        DEBUG_MODE = False # Default to False in fallback
    config = ConfigFallback()

# --- 2. Configure Logging SECOND ---
try:
    # Ensure log directory exists
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # Configure logging
    log_file_path = os.path.join(config.LOG_DIR, config.LOG_FILE)
    logging.basicConfig(
        level=config.LOGGING_LEVEL,
        format=config.LOGGING_FORMAT,
        datefmt=config.LOGGING_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    log = logging.getLogger(__name__)
    log.info(f"Logging configurado. Arquivo de log: {log_file_path}")
except Exception as e:
    print(f"ERRO ao configurar logging: {e}")
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    log = logging.getLogger(__name__)
    log.error(f"Erro ao configurar logging: {e}")

# --- 3. Usage Limit Check Function ---
def verificar_e_incrementar_uso():
    """
    Verifica e incrementa o contador de uso.

    Returns:
        tuple: (limite_atingido, uso_atual)
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(config.USAGE_COUNT_FILE):
            # Criar o arquivo se não existir
            with open(config.USAGE_COUNT_FILE, 'w') as f:
                f.write('0')
            log.info(f"Arquivo de contagem de uso criado: {config.USAGE_COUNT_FILE}")
            return False, 0

        # Ler o valor atual
        with open(config.USAGE_COUNT_FILE, 'r') as f:
            try:
                uso_atual = int(f.read().strip())
            except ValueError:
                log.warning(f"Valor inválido no arquivo de contagem. Reiniciando para 0.")
                uso_atual = 0

        # Incrementar o valor
        uso_atual += 1

        # Escrever o novo valor
        with open(config.USAGE_COUNT_FILE, 'w') as f:
            f.write(str(uso_atual))

        # Verificar se o limite foi atingido
        limite_atingido = uso_atual >= config.USAGE_LIMIT

        log.info(f"Uso atual: {uso_atual}, Limite: {config.USAGE_LIMIT}, Atingido: {limite_atingido}")
        return limite_atingido, uso_atual

    except Exception as e:
        log.error(f"Erro ao verificar/incrementar uso: {e}")
        return False, 0

# --- 4. Initialize Dash App ---
log.info(f"Inicializando a aplicação Dash: {config.APP_TITLE}")
app = dash.Dash(
    __name__,
    external_stylesheets=[config.DEFAULT_THEME_URL],
    suppress_callback_exceptions=True, # ESSENTIAL for multi-page apps and dynamically loaded content
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Simulador de Testes de Transformadores"},
        {"name": "theme-color", "content": "#4F4F4F"}
    ],
    title=config.APP_TITLE,
    assets_folder=config.ASSETS_DIR
)
server = app.server # Expose server variable for Procfile/Gunicorn
log.info(f"Tema Bootstrap: {config.DEFAULT_THEME_NAME}")
log.info(f"Pasta assets: {config.ASSETS_DIR}")

# --- Initialize Master Control Program (MCP) ---
try:
    from app_core.transformer_mcp import TransformerMCP
    app.mcp = TransformerMCP()
    log.info("TransformerMCP (app.mcp) inicializado com sucesso.")
    # Nota: O MCP centraliza a gestão de estado.
    # Os callbacks devem interagir com app.mcp para ler/escrever dados.
    # O app.transformer_data_cache foi removido/comentado.
except ImportError as e:
    log.critical(f"FALHA CRÍTICA ao importar TransformerMCP: {e}", exc_info=True)
    # A aplicação provavelmente não funcionará corretamente sem o MCP.
    # Considerar um layout de erro mais severo ou sair.
    app.mcp = None # Define como None para verificações posteriores
except Exception as e:
    log.critical(f"FALHA CRÍTICA ao instanciar TransformerMCP: {e}", exc_info=True)
    app.mcp = None

# # Initialize application-level cache (substituído pelo MCP)
# app.transformer_data_cache = {}
# log.info("Cache de dados do transformador (app.transformer_data_cache) inicializado.")
# # Nota: O MCP foi removido para simplificar o fluxo de dados.
# # Agora os dados são gerenciados diretamente pelos dcc.Store components
# # e o cache é usado apenas para acesso rápido fora dos callbacks.

# Ensure the losses-store is properly initialized
try:
    from utils.store_utils import prepare_data_for_store
    app.losses_store_initial = prepare_data_for_store({
        'resultados_perdas_vazio': {},
        'resultados_perdas_carga': {}
    }, "losses-store")
    log.info("Dados iniciais para losses-store preparados.")
except Exception as e:
    log.error(f"Erro ao preparar dados iniciais para losses-store: {e}")
    app.losses_store_initial = {
        'resultados_perdas_vazio': {},
        'resultados_perdas_carga': {}
    }

# --- 5. Perform Usage Limit Check ---
limite_atingido_inicial, uso_atual = verificar_e_incrementar_uso()
log.info(f"Status final após verificação/incremento: Uso={uso_atual}, Limite={config.USAGE_LIMIT}, Atingido={limite_atingido_inicial}")
if limite_atingido_inicial:
    log.warning(f"Limite ({config.USAGE_LIMIT}) atingido ou excedido. Uso: {uso_atual}. Funcionalidades podem estar restritas.")

# Basic error layout
error_layout = dbc.Container([
    dbc.Alert([dash_html.H4("Erro Crítico na Inicialização"), dash_html.P("Não foi possível carregar a aplicação. Verifique os logs.")], color="danger", className="m-5")
])

# --- START OF CRITICAL REORDERING ---

# --- 6. Create Main Application Layout FIRST ---
layout_creation_failed = False
try:
    log.info("Importando e criando layout principal...")
    from layouts.main_layout import create_main_layout # Import the function

    # Create the layout structure AND ASSIGN it to app.layout
    app.layout = create_main_layout(
        uso_atual=uso_atual,
        limite_atingido=limite_atingido_inicial
    )
    log.info("Layout principal da aplicação definido e atribuído a app.layout.")

except ImportError as e:
     print(f"!!!!!! [app.py] ERRO CRÍTICO DE IMPORTAÇÃO (Layout) !!!!!!")
     print(traceback.format_exc())
     log.critical(f"Erro de Importação Crítico ao criar layout: {e}.", exc_info=True)
     app.layout = error_layout # Assign error layout
     layout_creation_failed = True
     print("[app.py] Usando layout de erro devido a falha na importação do layout.")
except Exception as e:
    print(f"!!!!!! [app.py] ERRO CRÍTICO INESPERADO AO CRIAR LAYOUT !!!!!!")
    print(traceback.format_exc())
    log.critical(f"Erro inesperado durante a criação do layout: {e}", exc_info=True)
    app.layout = error_layout # Assign error layout
    layout_creation_failed = True
    print("[app.py] Usando layout de erro devido a falha inesperada na criação do layout.")

# Ensure layout is defined even after errors
if not hasattr(app, 'layout') or app.layout is None:
     print("!!!!!! [app.py] ERRO FATAL: Layout não definido após tentativas !!!!!!")
     log.critical("Falha crítica: Layout não foi definido.")
     app.layout = dash_html.Div("Erro Fatal na Aplicação") # Absolute minimum layout
     layout_creation_failed = True # Mark as failed


# --- 7. Import and Register Callbacks AFTER Layout is Set ---
# Only proceed if layout creation didn't fail critically
if not layout_creation_failed:
    try:
        log.info("Importando e registrando callbacks (APÓS app.layout)...")

        # Modules with @callback decorators (imported for side effects)
        callback_modules_decorated = [
            'navigation_dcc_links',
            # 'transformer_inputs', # Moved to explicit registration
            'losses',
            'dieletric_analysis',
            'short_circuit',
            'temperature_rise',
            'report_generation',
            'dielectric_analysis_comprehensive',
            'global_updates'
        ]

        # Import all callback modules (for side effects - they register themselves)
        for module_name in callback_modules_decorated:
            try:
                module_path = f'callbacks.{module_name}'
                log.debug(f"Importando módulo de callback: {module_path}")
                __import__(module_path)
                log.debug(f"Módulo de callback importado com sucesso: {module_path}")
            except ImportError as e:
                log.error(f"Erro ao importar módulo de callback {module_name}: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Erro inesperado ao processar módulo de callback {module_name}: {e}", exc_info=True)

        # Explicitly register callbacks that need app instance
        try:
            from callbacks.transformer_inputs import register_transformer_inputs_callbacks
            # Wrap the registration in a try-except block to catch specific callback errors
            try:
                register_transformer_inputs_callbacks(app)
                log.debug("Callbacks de transformer_inputs registrados explicitamente.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks de transformer_inputs: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks de transformer_inputs: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Erro ao importar módulo de callbacks de transformer_inputs: {e}", exc_info=True)

        try:
            from callbacks.impulse import register_impulse_callbacks
            try:
                register_impulse_callbacks(app)
                log.debug("Callbacks de impulso registrados explicitamente.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks de impulso: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks de impulso: {e}", exc_info=True)
        except Exception as e: log.error(f"Erro ao importar módulo de callbacks de impulso: {e}", exc_info=True)

        try:
            from callbacks.applied_voltage import register_applied_voltage_callbacks
            try:
                register_applied_voltage_callbacks(app)
                log.debug("Callbacks de tensão aplicada registrados explicitamente.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks de tensão aplicada: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks de tensão aplicada: {e}", exc_info=True)
        except Exception as e: log.error(f"Erro ao importar módulo de callbacks de tensão aplicada: {e}", exc_info=True)

        try:
            from callbacks.induced_voltage import register_induced_voltage_callbacks
            try:
                register_induced_voltage_callbacks(app)
                log.debug("Callbacks de tensão induzida registrados explicitamente.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks de tensão induzida: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks de tensão induzida: {e}", exc_info=True)
        except Exception as e: log.error(f"Erro ao importar módulo de callbacks de tensão induzida: {e}", exc_info=True)

        try:
            from callbacks.history import register_history_callbacks
            try:
                register_history_callbacks(app)
                log.debug("Callbacks de histórico registrados explicitamente.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks de histórico: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks de histórico: {e}", exc_info=True)
        except Exception as e: log.error(f"Erro ao importar módulo de callbacks de histórico: {e}", exc_info=True)

        try:
            # Initialize standards database
            try:
                from utils.standards_db import create_standards_tables
                create_standards_tables()
                log.debug("Banco de dados de normas técnicas inicializado.")
            except Exception as e:
                log.error(f"Erro ao inicializar banco de dados de normas: {e}", exc_info=True)

            # Register standards consultation callbacks
            try:
                from callbacks.standards_consultation import register_standards_consultation_callbacks
                try:
                    register_standards_consultation_callbacks(app)
                    log.debug("Callbacks de consulta de normas registrados.")
                except dash.exceptions.InvalidCallbackReturnValue as e:
                    log.error(f"Erro de valor de retorno inválido em callbacks de consulta de normas: {e}", exc_info=True)
                    log.warning("Tentando continuar apesar do erro de callback...")
                except Exception as e:
                    log.error(f"Erro ao registrar callbacks de consulta de normas: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Erro ao importar módulo de callbacks de consulta de normas: {e}", exc_info=True)

            # Register standards management callbacks
            try:
                from callbacks.standards_management import register_standards_management_callbacks
                try:
                    register_standards_management_callbacks(app)
                    log.debug("Callbacks de gerenciamento de normas registrados.")
                except dash.exceptions.InvalidCallbackReturnValue as e:
                    log.error(f"Erro de valor de retorno inválido em callbacks de gerenciamento de normas: {e}", exc_info=True)
                    log.warning("Tentando continuar apesar do erro de callback...")
                except Exception as e:
                    log.error(f"Erro ao registrar callbacks de gerenciamento de normas: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Erro ao importar módulo de callbacks de gerenciamento de normas: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Erro geral ao inicializar/registrar sistema de normas: {e}", exc_info=True)

        try:
            from components.client_side_callbacks import register_client_side_callbacks
            try:
                register_client_side_callbacks()
                log.debug("Callbacks do lado do cliente registrados.")
            except dash.exceptions.InvalidCallbackReturnValue as e:
                log.error(f"Erro de valor de retorno inválido em callbacks do lado do cliente: {e}", exc_info=True)
                log.warning("Tentando continuar apesar do erro de callback...")
            except Exception as e:
                log.error(f"Erro ao registrar callbacks do lado do cliente: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Erro ao importar módulo de callbacks do lado do cliente: {e}", exc_info=True)

        log.info(f"Todos os Callbacks registrados. Total: {len(app.callback_map)}")

    except Exception as e:
        print(f"!!!!!! [app.py] ERRO CRÍTICO AO REGISTRAR CALLBACKS !!!!!!")
        print(traceback.format_exc())
        log.critical(f"Erro inesperado durante o registro de callbacks: {e}", exc_info=True)
        # Optionally switch back to error layout if callback registration fails?
        # app.layout = error_layout
        # layout_creation_failed = True # Mark as failed to prevent server run?

# --- END OF CRITICAL REORDERING ---


# --- 8. Browser Opening Logic ---
def open_browser():
    """Opens the browser to the application URL."""
    global _browser_opened
    host = getattr(config, 'HOST', '127.0.0.1')
    port = getattr(config, 'PORT', 8060)
    url = f"http://{host}:{port}/"
    log.info(f"Abrindo navegador na URL: {url}")
    try:
        webbrowser.open_new(url)
    except Exception as e:
        log.error(f"Falha ao abrir o navegador: {e}")

# Flag para garantir que o navegador seja aberto apenas uma vez
_browser_opened = False

# --- 9. Run Server ---
if __name__ == '__main__':
    if layout_creation_failed:
        log.error("Início do servidor abortado devido a falha na criação do layout ou registro de callbacks.")
    else:
        # Log do status de limite
        if limite_atingido_inicial:
            log.warning("LIMITE DE USO ATINGIDO - Funcionalidades podem estar restritas")

        # Configurações do servidor
        host = getattr(config, 'HOST', '127.0.0.1')
        port = getattr(config, 'PORT', 8060)
        debug_mode = getattr(config, 'DEBUG_MODE', True) # Read debug mode from config

        log.info(f"Iniciando servidor Dash em http://{host}:{port}/ (Debug: {debug_mode})")

        # Lógica para abrir o navegador apenas uma vez
        if not debug_mode or (debug_mode and os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
             if not _browser_opened:
                Timer(1.5, open_browser).start()
                _browser_opened = True
        elif debug_mode and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            log.debug("Não abrindo navegador (processo filho do reloader)")

        # Iniciar o servidor com configurações modificadas para evitar o erro de socket
        try:
            app.run(
                debug=debug_mode,
                host=host,
                port=port,
                use_reloader=debug_mode,
                threaded=False  # Adicionado para evitar problemas de socket
            )
            log.info("Servidor Dash encerrado.")
        except OSError as e:
            log.error(f"Erro ao iniciar o servidor na porta {port}: {e}")
            print(f"\n!!! ERRO FATAL: Não foi possível iniciar o servidor na porta {port}. Verifique se ela já está em uso. !!!\n")
        except Exception as e:
            log.exception(f"Erro inesperado ao iniciar o servidor: {e}")
