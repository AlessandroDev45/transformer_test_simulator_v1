# app.py - Versão Revisada
import logging
import os
import sys
import webbrowser

import dash
import dash_bootstrap_components as dbc

# Imports específicos de dash.exceptions são feitos nos módulos de callback

# --- 1. Load Configuration FIRST ---
try:
    import config

    # Configuração carregada
except ImportError:
    # Configurar logging básico para registrar o erro
    logging.basicConfig(
        level=logging.CRITICAL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.critical("Não foi possível importar config.py. Usando configuração de fallback.")

    # Fallback basic config if needed, or exit
    class ConfigFallback:
        LOG_DIR = "."
        LOG_FILE = "app_fallback.log"
        LOGGING_LEVEL = logging.INFO
        LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        APP_TITLE = "Simulador (Erro Config)"
        DEFAULT_THEME_URL = dbc.themes.DARKLY  # Default to a theme
        DEFAULT_THEME_NAME = "DARKLY"
        ASSETS_DIR = "assets"
        USAGE_COUNT_FILE = "usage_count.txt"
        USAGE_LIMIT = 61  # Example fallback
        HOST = "127.0.0.1"
        PORT = 8060
        DEBUG_MODE = False  # Default to False in fallback

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
            logging.FileHandler(log_file_path, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,  # Garante que a configuração seja aplicada mesmo se já houver handlers
    )
    log = logging.getLogger(__name__)
    log.info(
        f"Logging configurado. Nível: {logging.getLevelName(config.LOGGING_LEVEL)}. Arquivo: {log_file_path}"
    )
except Exception as e:
    print(f"ERRO ao configurar logging: {e}")
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger(__name__)
    log.error(f"Erro ao configurar logging: {e}")


# --- 3. Usage Limit Check Function (modificada) ---
def verificar_e_incrementar_uso(incrementar=True):
    """
    Verifica e opcionalmente incrementa o contador de uso.

    Args:
        incrementar (bool): Se True, incrementa o contador. Se False, apenas lê o valor atual.

    Returns:
        tuple: (limite_atingido, uso_atual)
    """
    try:
        # Importar o rastreador de uso
        # Criar o rastreador com o caminho do banco de dados
        from utils.paths import get_data_dir
        from utils.usage_tracker import UsageTracker

        db_path = get_data_dir() / "usage.db"
        tracker = UsageTracker(str(db_path))

        if incrementar:
            # Incrementar o contador e verificar o limite
            uso_atual, limite_atingido = tracker.increment_counter("app_usage")
            log.info(f"Contador incrementado para: {uso_atual}")
        else:
            # Apenas ler o valor atual
            uso_atual = tracker.get_counter("app_usage") or 0
            limite_atingido = uso_atual >= config.USAGE_LIMIT
            log.info(f"Contador lido sem incremento: {uso_atual}")

        log.info(
            f"Uso atual: {uso_atual}, Limite: {config.USAGE_LIMIT}, Atingido: {limite_atingido}"
        )
        return limite_atingido, uso_atual
    except Exception as e:
        log.error(f"Erro ao verificar/incrementar uso: {e}", exc_info=True)
        return False, 0


# --- 4. Initialize Dash App (sem mudanças) ---
log.info(f"Inicializando a aplicação Dash: {config.APP_TITLE}")
app = dash.Dash(
    __name__,
    external_stylesheets=[config.DEFAULT_THEME_URL],
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,  # Evita que callbacks sejam disparados na inicialização
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Simulador de Testes de Transformadores"},
        {"name": "theme-color", "content": "#4F4F4F"},
    ],
    title=config.APP_TITLE,
    assets_folder=config.ASSETS_DIR,
)
server = app.server
log.info(f"Tema Bootstrap: {config.DEFAULT_THEME_NAME}")
log.info(f"Pasta assets: {config.ASSETS_DIR}")

# --- 5. Initialize Master Control Program (MCP) ---
try:
    from app_core.transformer_mcp import TransformerMCP

    app.mcp = TransformerMCP(
        load_from_disk=True
    )  # Atribui à instância do app e carrega dados do disco
    log.info("TransformerMCP (app.mcp) inicializado com sucesso.")

    # Inicializar o MCP com dados padrão do arquivo transformer.json
    try:
        from app_core.startup import seed_mcp

        # Tentar carregar dados padrão do arquivo JSON
        seed_success = seed_mcp(app_instance=app)
        if seed_success:
            log.info("MCP inicializado com dados padrão do arquivo transformer.json")
        else:
            log.warning(
                "Não foi possível inicializar o MCP com dados padrão do arquivo transformer.json"
            )
    except ImportError as e:
        log.error(f"Erro ao importar módulo de startup: {e}", exc_info=True)
    except Exception as e:
        log.error(f"Erro ao inicializar MCP com dados padrão: {e}", exc_info=True)

    # Verificar se o MCP foi inicializado corretamente
    if app.mcp is not None:
        # Verificar se os dados padrão foram carregados
        transformer_data = app.mcp.get_data("transformer-inputs-store")
        if transformer_data:
            log.info(f"MCP inicializado com dados: {transformer_data}")

            # Calcular correntes nominais
            try:
                calculated_currents = app.mcp.calculate_nominal_currents(transformer_data)
                log.info(f"Correntes calculadas na inicialização: {calculated_currents}")

                # Atualizar os dados com as correntes calculadas
                transformer_data.update(
                    {
                        "corrente_nominal_at": calculated_currents.get("corrente_nominal_at"),
                        "corrente_nominal_at_tap_maior": calculated_currents.get(
                            "corrente_nominal_at_tap_maior"
                        ),
                        "corrente_nominal_at_tap_menor": calculated_currents.get(
                            "corrente_nominal_at_tap_menor"
                        ),
                        "corrente_nominal_bt": calculated_currents.get("corrente_nominal_bt"),
                        "corrente_nominal_terciario": calculated_currents.get(
                            "corrente_nominal_terciario"
                        ),
                    }
                )

                # Atualizar o MCP com os dados atualizados diretamente
                app.mcp.set_data("transformer-inputs-store", transformer_data)
                log.info("MCP atualizado com correntes calculadas na inicialização")

                # Propagar dados para outros stores usando o novo utilitário
                try:
                    log.info("Propagando dados do transformer-inputs-store para outros stores...")

                    # Importar o utilitário de persistência do MCP
                    from utils.mcp_persistence import ensure_mcp_data_propagation

                    # Lista de stores para os quais propagar os dados
                    target_stores = [
                        "losses-store",
                        "impulse-store",
                        "dieletric-analysis-store",
                        "applied-voltage-store",
                        "induced-voltage-store",
                        "short-circuit-store",
                        "temperature-rise-store",
                        "comprehensive-analysis-store",
                    ]

                    # Propagar dados para todos os stores
                    propagation_results = ensure_mcp_data_propagation(
                        app, "transformer-inputs-store", target_stores
                    )

                    # Registrar resultados
                    for store, success in propagation_results.items():
                        if success:
                            log.info(f"Dados propagados para {store}")
                        else:
                            log.warning(f"Não foi necessário propagar dados para {store}")

                    # Sincronizar valores de isolamento entre todos os stores
                    try:
                        from utils.mcp_persistence import sync_isolation_values
                        sync_result = sync_isolation_values(app)
                        if sync_result:
                            log.info("Valores de isolamento sincronizados com sucesso entre todos os stores")
                        else:
                            log.warning("Não foi possível sincronizar valores de isolamento entre os stores")
                    except Exception as e:
                        log.error(f"Erro ao sincronizar valores de isolamento: {e}", exc_info=True)

                except Exception as e:
                    log.error(f"Erro ao propagar dados para outros stores: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Erro ao calcular correntes na inicialização: {e}", exc_info=True)
        else:
            log.warning("MCP inicializado, mas sem dados padrão")
except ImportError as e:
    log.critical(f"FALHA CRÍTICA ao importar TransformerMCP: {e}", exc_info=True)
    app.mcp = None
except Exception as e:
    log.critical(f"FALHA CRÍTICA ao instanciar TransformerMCP: {e}", exc_info=True)
    app.mcp = None

# --- 6. Perform Usage Limit Check (modificado) ---
# Determina se deve incrementar o contador com base no modo de execução
deve_incrementar = not config.DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") != "true"
limite_atingido_inicial, uso_atual = verificar_e_incrementar_uso(incrementar=deve_incrementar)

log.info(
    f"Status final após verificação/incremento: Uso={uso_atual}, Limite={config.USAGE_LIMIT}, Atingido={limite_atingido_inicial}"
)
if limite_atingido_inicial:
    log.warning(
        f"Limite ({config.USAGE_LIMIT}) atingido ou excedido. Uso: {uso_atual}. Funcionalidades podem estar restritas."
    )

# --- 7. Create Main Application Layout FIRST ---
layout_creation_failed = False
error_layout = dbc.Container(
    [dbc.Alert("Erro Crítico na Inicialização", color="danger", className="m-5")]
)
try:
    log.info("Importando e criando layout principal...")
    from layouts.main_layout import create_main_layout

    # Cria e ATRIBUI o layout à aplicação
    app.layout = create_main_layout(
        uso_atual=uso_atual,
        limite_atingido=limite_atingido_inicial,
        app=app,  # Passa a instância do app para o layout (útil para acessar mcp/cache se necessário no layout)
    )
    log.info("Layout principal da aplicação definido e atribuído a app.layout.")
except Exception as e:
    log.critical("ERRO CRÍTICO AO CRIAR LAYOUT", exc_info=True)
    log.critical(f"Erro inesperado durante a criação do layout: {e}", exc_info=True)
    app.layout = error_layout
    layout_creation_failed = True

# --- 8. Import and Register Callbacks AFTER Layout is Set ---
if not layout_creation_failed:
    log.info("Importando e registrando callbacks (APÓS app.layout)...")
    try:
        # Modules with @callback decorators (imported for side effects)
        decorated_modules = [
            # 'transformer_inputs' removido para evitar importação com erro
            # 'short_circuit' removido para evitar importação com erro
            # 'temperature_rise' removido para usar registro explícito
            "navigation_dcc_links",
            "losses",
            "dieletric_analysis",
            "report_generation",
            "dielectric_analysis_comprehensive",
            "global_updates",
            "standards_consultation",  # Adicionado
            "standards_management",  # Adicionado
        ]
        for module_name in decorated_modules:
            try:
                module_path = f"callbacks.{module_name}"
                log.debug(f"Importando módulo de callback decorado: {module_path}")

                __import__(module_path)

                log.debug(f"Módulo importado: {module_path}")
            except ImportError as e:
                log.error(f"Erro ao importar módulo de callback {module_name}: {e}", exc_info=True)
            except Exception as e:
                log.error(
                    f"Erro inesperado ao processar módulo de callback {module_name}: {e}",
                    exc_info=True,
                )

        # Explicitly register callbacks that need app instance
        explicit_registrations = {
            "transformer_inputs": "register_transformer_inputs_callbacks",
            "short_circuit": "register_short_circuit_callbacks",
            "impulse": "register_impulse_callbacks",
            "applied_voltage": "register_applied_voltage_callbacks",
            "induced_voltage": "register_induced_voltage_callbacks",
            "history": "register_history_callbacks",
            "global_actions": "register_global_actions_callbacks",  # Adicionado
            "insulation_level_callbacks": "register_insulation_level_callbacks",  # Corrigido para o nome correto do ficheiro/função
            "temperature_rise": "register_temperature_rise_callbacks",  # Callbacks de elevação de temperatura
            # 'standards_consultation': 'register_standards_consultation_callbacks', # Já são decorados
            # 'standards_management': 'register_standards_management_callbacks' # Já são decorados
            # "client_side_callbacks": "register_client_side_callbacks",  # Client-side - Removido: arquivo não existe
        }

        # Vamos registrar os callbacks explicitamente
        for module_name, reg_func_name in explicit_registrations.items():
            try:
                module_path = f"callbacks.{module_name}"
                log.debug(f"Importando e registrando explicitamente: {module_path}")
                module = __import__(module_path, fromlist=[reg_func_name])
                registration_function = getattr(module, reg_func_name)
                registration_function(app)  # Passa a instância do app
                log.debug(f"Callbacks registrados explicitamente: {module_path}")
            except ImportError as e:
                log.error(
                    f"Erro ao importar módulo para registro explícito {module_name}: {e}",
                    exc_info=True,
                )
            except AttributeError as e:
                log.error(
                    f"Função de registro '{reg_func_name}' não encontrada em {module_name}: {e}",
                    exc_info=True,
                )
            except Exception as e:
                log.error(
                    f"Erro ao registrar callbacks de {module_name} explicitamente: {e}",
                    exc_info=True,
                )

        # Inicializar banco de dados de normas
        try:
            from utils.standards_db import create_standards_tables

            create_standards_tables()
            log.debug("Banco de dados de normas técnicas inicializado/verificado.")
        except Exception as e:
            log.error(f"Erro ao inicializar banco de dados de normas: {e}", exc_info=True)

        log.info(f"Callbacks registrados. Total: {len(app.callback_map)}")
    except Exception as e:
        log.critical("ERRO CRÍTICO AO REGISTRAR CALLBACKS", exc_info=True)
        log.critical(f"Erro inesperado durante o registro de callbacks: {e}", exc_info=True)
        layout_creation_failed = True  # Marca falha se registro der erro

# --- 9. Browser Opening Logic (modificado) ---
# Flag global para controlar a abertura do navegador
_browser_opened = False


def open_browser():
    """Abre o navegador na URL da aplicação."""
    host = getattr(config, "HOST", "127.0.0.1")
    port = getattr(config, "PORT", 8050)
    url = f"http://{host}:{port}/"
    log.info(f"Abrindo navegador na URL: {url}")
    try:
        webbrowser.open_new(url)
    except Exception as e:
        log.error(f"Falha ao abrir o navegador: {e}")


# --- 10. Run Server ---
if __name__ == "__main__":
    if layout_creation_failed:
        log.error(
            "Início do servidor abortado devido a falha na criação do layout ou registro de callbacks."
        )
    else:
        if limite_atingido_inicial:
            log.warning("LIMITE DE USO ATINGIDO - Funcionalidades podem estar restritas")

        host = getattr(config, "HOST", "127.0.0.1")
        port = getattr(config, "PORT", 8050)  # <<< Usar PORT do config
        debug_mode = getattr(config, "DEBUG_MODE", True)

        log.info(f"Iniciando servidor Dash em http://{host}:{port}/ (Debug: {debug_mode})")

        # Controle de abertura do navegador
        # Abre apenas no processo principal (sem debug) ou no processo filho do reloader (com debug)
        if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            if not _browser_opened:
                # Usa threading.Timer para abrir o navegador após um pequeno atraso
                import threading

                threading.Timer(1.5, open_browser).start()
                _browser_opened = True
                log.info("Timer para abertura do navegador iniciado")
        else:
            log.debug("Não abrindo navegador (processo principal do reloader)")

        try:
            # Sempre desativar debug e reloader para evitar problemas com o MCP
            # Register a function to save MCP state on exit
            import atexit

            def save_mcp_on_exit():
                if hasattr(app, "mcp") and app.mcp is not None:
                    log.info("Saving MCP state to disk before exit...")
                    try:
                        app.mcp.save_to_disk(force=True)
                        log.info("MCP state saved successfully on exit")
                    except Exception as e:
                        log.error(f"Error saving MCP state on exit: {e}", exc_info=True)

            atexit.register(save_mcp_on_exit)

            app.run(
                debug=False,  # Forçar debug=False para evitar reinicialização do MCP
                host=host,
                port=port,
                use_reloader=False,  # Desativar reloader para evitar reinicialização do MCP
                threaded=True,  # Usar threading para melhor desempenho e estabilidade
            )
            log.info("Servidor Dash encerrado.")
        except OSError as e:
            log.error(f"Erro ao iniciar o servidor na porta {port}: {e}")
            log.critical(
                f"ERRO FATAL: Não foi possível iniciar o servidor na porta {port}. Verifique se ela já está em uso."
            )
        except Exception as e:
            log.exception(f"Erro inesperado ao iniciar o servidor: {e}")
