# callbacks/temperature_rise.py
""" Callbacks para a seção de Elevação de Temperatura. """
import dash
from dash import dcc, html, Input, Output, State, callback, callback_context, no_update
import dash_bootstrap_components as dbc
import math
import logging
import datetime
from dash.exceptions import PreventUpdate

# Importações da aplicação
from app import app
from config import colors # Para estilos
from utils import constants # Para constantes de material
from utils.routes import normalize_pathname, ROUTE_TEMPERATURE_RISE # Para normalização de pathname
# <<< IMPORTANTE: Verifique a assinatura e unidades esperadas destas funções >>>
from app_core.calculations import (
    calculate_winding_temps,
    calculate_top_oil_rise,
    calculate_thermal_time_constant # Assume que espera pesos em KG
)
# <<< FIM IMPORTANTE >>>
from components.validators import validate_dict_inputs # Para validação
from components.transformer_info_template import create_transformer_info_panel
from components.formatters import formatar_elevacao_temperatura, format_parameter_value # Formatadores

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# --- Callback para atualizar o painel de info removido ---
# Este callback foi removido pois a atualização é feita pelo callback global em global_updates.py

# --- Funções Auxiliares (mantida) ---
def safe_float(value, default=None):
    if value is None or value == '':
        return default
    try:
        s_value = str(value).replace('.', '').replace(',', '.')
        return float(s_value)
    except (ValueError, TypeError):
        log.warning(f"Could not convert '{value}' to float.")
        return default

# --- Callbacks ---

# Callback para CARREGAR dados (RESTAURADO com triggers corretos)
@app.callback(
    [
        Output("temp-amb", "value"),
        Output("winding-material", "value"),
        Output("res-cold", "value"),
        Output("temp-cold", "value"),
        Output("res-hot", "value"),
        Output("temp-top-oil", "value"),
        Output("delta-theta-oil-max", "value"),
        Output("avg-winding-temp", "value"),
        Output("avg-winding-rise", "value"),
        Output("top-oil-rise", "value"),
        Output("ptot-used", "value"),
        Output("tau0-result", "value"),
        Output("temp-rise-error-message", "children")
    ],
    [
        Input("url", "pathname"),                    # <<< Trigger pela URL
        Input("transformer-inputs-store", "data"),   # <<< Trigger pelos Dados Básicos
        Input("temperature-rise-store", "data")     # <<< Trigger pelo store local
    ],
    prevent_initial_call=False # <<< Permite rodar na carga inicial
)
def temperature_rise_load_data(pathname, transformer_data, stored_temp_rise_data):
    """
    Carrega os dados da aba Elevação de Temperatura para a UI.
    - Prioriza 'elevacao_oleo_topo' do transformer-inputs-store.
    - Carrega outros inputs e resultados do temperature-rise-store.
    """
    triggered_id = callback_context.triggered_id
    log.debug(f"[LOAD TempRise] Callback triggered by: {triggered_id}")
    print(f"\n\n***** [LOAD TempRise] CALLBACK INICIADO *****")
    print(f"[LOAD TempRise] Trigger: {triggered_id}")
    print(f"[LOAD TempRise] Pathname: {pathname}")
    print(f"[LOAD TempRise] Stored data: {stored_temp_rise_data}")

    # Adicionar logs para debug
    print(f"\n\n***** [LOAD TempRise] CALLBACK DETALHES *****")
    print(f"[LOAD TempRise] callback_context.triggered: {callback_context.triggered}")
    print(f"[LOAD TempRise] callback_context.inputs: {callback_context.inputs}")

    normalized_path = normalize_pathname(pathname)
    # Só executa a lógica principal se o trigger for a URL E estiver na página correta,
    # OU se o trigger for a atualização do store global (para pegar delta_theta)
    # OU se o trigger for o store local (para carregar dados salvos)
    should_process = False

    # Caso 1: Estamos na página correta (independente do trigger)
    if normalized_path == ROUTE_TEMPERATURE_RISE:
        should_process = True
        log.info(f"[LOAD TempRise] Estamos na página de Elevação de Temperatura. Processando.")
    # Caso 2: Trigger é o store global (para pegar delta_theta)
    elif triggered_id == "transformer-inputs-store":
        should_process = True
        log.info(f"[LOAD TempRise] Processando atualização de transformer-inputs-store.")
    # Caso 3: Estamos em outra página e o trigger é a URL
    elif triggered_id == "url" and normalized_path != ROUTE_TEMPERATURE_RISE:
         log.debug(f"[LOAD TempRise] Pathname '{pathname}' não é '{ROUTE_TEMPERATURE_RISE}'. Abortando trigger de URL.")
         raise PreventUpdate
    # Caso 4: Outros triggers não relevantes
    else:
        log.debug(f"[LOAD TempRise] Trigger não relevante ({triggered_id}). Abortando.")
        raise PreventUpdate

    if not should_process: # Segurança extra
        raise PreventUpdate

    # Lê dados dos stores, tratando None/inválido
    local_data = stored_temp_rise_data if stored_temp_rise_data and isinstance(stored_temp_rise_data, dict) else {}
    global_data = transformer_data if transformer_data and isinstance(transformer_data, dict) else {}

    inputs_local = local_data.get('inputs_temp_rise', {})
    results_local = local_data.get('resultados_temp_rise', {})

    log.debug(f"[LOAD TempRise] Dados lidos do local store: Inputs={inputs_local}, Resultados={results_local}")
    log.debug(f"[LOAD TempRise] Dados lidos do global store: {global_data}")

    # Determina delta_theta_oil_max (prioridade global)
    delta_theta_oil_max_final = None
    delta_theta_oil_max_global_raw = global_data.get('elevacao_oleo_topo')
    if delta_theta_oil_max_global_raw is not None:
        delta_theta_oil_max_final = safe_float(delta_theta_oil_max_global_raw)
        log.info(f"[LOAD TempRise] Usando 'elevacao_oleo_topo' ({delta_theta_oil_max_final}) do global store.")
        if delta_theta_oil_max_final is None:
             log.warning(f"[LOAD TempRise] Falha ao converter 'elevacao_oleo_topo' ({delta_theta_oil_max_global_raw}). Fallback para local.")
             delta_theta_oil_max_final = inputs_local.get('input_delta_theta_oil_max') # Já deve ser float
    else:
        delta_theta_oil_max_final = inputs_local.get('input_delta_theta_oil_max')
        log.info(f"[LOAD TempRise] Global 'elevacao_oleo_topo' não disponível. Usando local: {delta_theta_oil_max_final}")

    # Tenta carregar a mensagem salva
    message_str = results_local.get('message', "")
    display_message = ""
    if message_str:
         is_warning = "Aviso" in message_str
         display_message = html.Div(message_str,
                                    style={"color": colors.get('warning', 'orange') if is_warning else colors.get('fail', 'red'),
                                           "fontSize": "0.7rem"})

    # Retorna valores para UI
    values_to_return = (
        inputs_local.get('input_ta'), inputs_local.get('input_material', 'cobre'),
        inputs_local.get('input_rc'), inputs_local.get('input_tc'),
        inputs_local.get('input_rw'), inputs_local.get('input_t_oil'),
        delta_theta_oil_max_final, # Valor numérico
        results_local.get('avg_winding_temp'), results_local.get('avg_winding_rise'),
        results_local.get('top_oil_rise'), results_local.get('ptot_used_kw'),
        results_local.get('tau0_h'), display_message
    )

    log.debug(f"[LOAD TempRise] Valores finais retornados para UI: {values_to_return}")
    return values_to_return


# Callback de debug para o botão alternativo
@app.callback(
    Output("temp-rise-error-message", "children", allow_duplicate=True),
    [Input("calc-temp-rise-debug", "n_clicks")],
    prevent_initial_call=True
)
def debug_calc_button(n_clicks):
    log.info(f"***** [DEBUG] Botão TESTE Calcular clicado: n_clicks = {n_clicks} *****")
    print(f"\n\n***** [DEBUG] Botão TESTE Calcular clicado: n_clicks = {n_clicks} *****\n\n")

    # Criar um arquivo de log específico para debug
    with open('logs/debug_calcular_button.log', 'a') as f:
        f.write(f"\n\n***** [DEBUG] Botão TESTE Calcular clicado *****\n")
        f.write(f"[DEBUG] n_clicks = {n_clicks}\n")
        f.write(f"[DEBUG] Trigger: {callback_context.triggered_id}\n")
        f.write(f"[DEBUG] Triggered: {callback_context.triggered}\n")
        f.write(f"[DEBUG] Timestamp: {datetime.datetime.now().isoformat()}\n")

    return html.Div(f"Botão TESTE clicado: {n_clicks} vezes", style={"color": "red", "fontSize": "0.8rem"})

# Callback principal para cálculo (RESTAURADO e CORRIGIDO)
@app.callback(
    [
        Output("avg-winding-temp", "value", allow_duplicate=True),
        Output("avg-winding-rise", "value", allow_duplicate=True),
        Output("top-oil-rise", "value", allow_duplicate=True),
        Output("ptot-used", "value", allow_duplicate=True),
        Output("tau0-result", "value", allow_duplicate=True),
        Output("temp-rise-error-message", "children", allow_duplicate=True),
        Output("temperature-rise-store", "data", allow_duplicate=True)
    ],
    [Input("calc-temp-rise-btn", "n_clicks")], # Trigger: Botão Calcular
    [
        State("temp-amb", "value"), State("winding-material", "value"),
        State("res-cold", "value"), State("temp-cold", "value"),
        State("res-hot", "value"), State("temp-top-oil", "value"),
        State("delta-theta-oil-max", "value"),
        State("transformer-inputs-store", "data"),
        State("losses-store", "data"), # Removido State("temperature-rise-store", "data")
        State("url", "pathname") # Adicionado pathname para verificação
    ],
    prevent_initial_call=True
)
def temperature_rise_calculate(
    n_clicks, temp_amb_str, winding_material, res_cold_str, temp_cold_str, res_hot_str, temp_top_oil_str, delta_theta_oil_max_str, # Inputs locais
    transformer_data, losses_data, pathname): # Dados globais e pathname
    """
    Calcula elevação de temperatura, Ptot usada e τ₀.
    Busca dados globais, realiza cálculos e salva inputs/resultados no store local.
    """
    # Verificar se estamos na página correta
    if pathname != "/elevacao-temperatura":
        log.info(f"Ignorando callback temperature_rise_calculate em página diferente: {pathname}")
        raise PreventUpdate

    log.info(f"***** [CALC TempRise] CALLBACK INICIADO - n_clicks = {n_clicks}, Trigger: {callback_context.triggered_id} *****")

    if n_clicks is None or n_clicks <= 0: # Garante que só execute com clique válido
        log.warning(f"[CALC TempRise] Prevenindo atualização: n_clicks={n_clicks}")
        raise PreventUpdate

    print(f"\n\n[CALC TempRise] Callback calculate disparado (n_clicks={n_clicks}). Trigger: {callback_context.triggered_id}\n\n")
    print(f"\n\nINPUTS: temp_amb={temp_amb_str}, material={winding_material}, rc={res_cold_str}, tc={temp_cold_str}, rw={res_hot_str}, t_oil={temp_top_oil_str}, delta_theta_oil_max={delta_theta_oil_max_str}\n\n")

    log.info(f"[CALC TempRise] Callback calculate disparado (n_clicks={n_clicks}). Trigger: {callback_context.triggered_id}")

    # --- 1. Validar e converter inputs locais ---
    input_values_local = {
        'ta': safe_float(temp_amb_str), 'material': winding_material,
        'rc': safe_float(res_cold_str), 'tc': safe_float(temp_cold_str),
        'rw': safe_float(res_hot_str), 't_oil': safe_float(temp_top_oil_str),
        'delta_theta_oil_max_ui': safe_float(delta_theta_oil_max_str)
    }
    validation_rules = {
        'ta': {'required': True, 'label': 'Temp. Ambiente (Θa)'},
        'material': {'required': True, 'allowed': ['cobre', 'aluminio'], 'label': 'Material'},
        'rc': {'required': True, 'positive': True, 'label': 'Resistência Fria (Rc)'},
        'tc': {'required': True, 'label': 'Temp. Ref. Fria (Θc)'},
        'rw': {'required': True, 'positive': True, 'label': 'Resistência Quente (Rw)'},
        't_oil': {'required': True, 'label': 'Temp. Topo Óleo Final (Θoil)'},
        'delta_theta_oil_max_ui': {'required': False, 'positive': True, 'label': 'ΔΘoil_max (UI)'},
    }
    log.info(f"[CALC TempRise] Valores de entrada: {input_values_local}")
    errors = validate_dict_inputs(input_values_local, validation_rules)
    if errors:
        log.warning(f"[CALC TempRise] Erros de validação Inputs Locais: {errors}")
        error_msg_div = html.Ul([html.Li(e) for e in errors], style={"color": colors.get('fail', 'red'), "fontSize": "0.7rem"})
        log.warning(f"[CALC TempRise] Retornando mensagem de erro: {error_msg_div}")
        return None, None, None, None, None, error_msg_div, no_update

    temp_amb = input_values_local['ta']; material = input_values_local['material']
    rc = input_values_local['rc']; tc = input_values_local['tc']
    rw = input_values_local['rw']; t_oil = input_values_local['t_oil']
    delta_theta_oil_max_ui = input_values_local['delta_theta_oil_max_ui']

    # --- 2. Ler e processar dados globais para Tau0 ---
    global_transformer_data = transformer_data if transformer_data and isinstance(transformer_data, dict) else {}
    global_losses_data = losses_data if losses_data and isinstance(losses_data, dict) else {}
    log.debug(f"[CALC TempRise] Dados globais lidos: Trafo={global_transformer_data}, Losses={global_losses_data}")

    peso_total_ton = safe_float(global_transformer_data.get('peso_total'))
    peso_oleo_ton = safe_float(global_transformer_data.get('peso_oleo'))
    perdas_vazio_kw = safe_float(global_losses_data.get('resultados_perdas_vazio', {}).get('perdas_vazio_kw'))
    perdas_carga_min_kw = safe_float(global_losses_data.get('resultados_perdas_carga', {}).get('perdas_carga_min'))
    delta_theta_oil_max_global = safe_float(global_transformer_data.get('elevacao_oleo_topo'))

    delta_theta_oil_max_calc = delta_theta_oil_max_ui if delta_theta_oil_max_ui is not None else delta_theta_oil_max_global
    log.debug(f"[CALC TempRise] Delta Theta Max UI: {delta_theta_oil_max_ui}, Global: {delta_theta_oil_max_global}, Usado: {delta_theta_oil_max_calc}")

    ptot_used_kw = perdas_carga_min_kw
    log.debug(f"[CALC TempRise] Perdas CargaMin={perdas_carga_min_kw} -> Ptot={ptot_used_kw}")

    # --- 3. Cálculos Principais ---
    avg_winding_temp, avg_winding_rise, top_oil_rise, tau0_h = None, None, None, None
    error_message = ""; warning_message_tau0 = ""
    try:
        log.info(f"[CALC TempRise] Chamando calculate_winding_temps com rc={rc}, tc={tc}, rw={rw}, temp_amb={temp_amb}, material={material}")
        avg_winding_temp, avg_winding_rise = calculate_winding_temps(rc, tc, rw, temp_amb, material)
        log.info(f"[CALC TempRise] Resultado calculate_winding_temps: avg_winding_temp={avg_winding_temp}, avg_winding_rise={avg_winding_rise}")

        log.info(f"[CALC TempRise] Chamando calculate_top_oil_rise com t_oil={t_oil}, temp_amb={temp_amb}")
        top_oil_rise = calculate_top_oil_rise(t_oil, temp_amb)
        log.info(f"[CALC TempRise] Resultado calculate_top_oil_rise: top_oil_rise={top_oil_rise}")

        if avg_winding_temp is None or avg_winding_rise is None or top_oil_rise is None:
             raise ValueError("Falha no cálculo básico de temperatura/elevação.")
        log.info(f"[CALC TempRise] Cálculos básicos OK: Tw={avg_winding_temp:.1f}, ΔTw={avg_winding_rise:.1f}, ΔToil={top_oil_rise:.1f}")

        # Cálculo tau0
        required_tau0 = {'Ptot': ptot_used_kw, 'ΔΘoil_max': delta_theta_oil_max_calc, 'Peso Total': peso_total_ton, 'Peso Óleo': peso_oleo_ton}
        missing_tau0 = [name for name, val in required_tau0.items() if val is None]
        if missing_tau0:
            warning_message_tau0 = f"Aviso: τ₀ não calculado. Dados faltantes: {', '.join(missing_tau0)}."
            log.warning(f"[CALC TempRise] {warning_message_tau0}")
        else:
            peso_total_kg = peso_total_ton * 1000
            peso_oleo_kg = peso_oleo_ton * 1000
            log.debug(f"[CALC TempRise] Calculando τ₀ com: Ptot={ptot_used_kw:.2f}kW, ΔΘmax={delta_theta_oil_max_calc:.1f}K, mT={peso_total_kg:.0f}kg, mO={peso_oleo_kg:.0f}kg")
            tau0_h = calculate_thermal_time_constant(ptot_used_kw, delta_theta_oil_max_calc, peso_total_kg, peso_oleo_kg)
            if tau0_h is None: warning_message_tau0 = "Aviso: Erro interno ao calcular τ₀."; log.error(f"[CALC TempRise] {warning_message_tau0}")
            else: log.info(f"[CALC TempRise] τ₀ calculado: {tau0_h:.2f} h")

    except ValueError as ve: log.warning(f"[CALC TempRise] Erro cálculo: {ve}"); error_message = f"Erro: {ve}"; avg_winding_temp=avg_winding_rise=top_oil_rise=tau0_h=None
    except Exception as e: log.exception("[CALC TempRise] Erro inesperado"); error_message = f"Erro inesperado: {e}"; avg_winding_temp=avg_winding_rise=top_oil_rise=tau0_h=None

    # --- 4. Preparar e Salvar Dados no Store Local ---
    final_message = error_message or warning_message_tau0
    store_to_save = {
        'inputs_temp_rise': { # Salva os valores originais da UI
            'input_ta': temp_amb_str, 'input_material': material, 'input_rc': res_cold_str,
            'input_tc': temp_cold_str, 'input_rw': res_hot_str, 'input_t_oil': temp_top_oil_str,
            'input_delta_theta_oil_max': delta_theta_oil_max_str
        },
        'resultados_temp_rise': { # Salva resultados numéricos e mensagem
            'avg_winding_temp': round(avg_winding_temp, 1) if avg_winding_temp is not None else None,
            'avg_winding_rise': round(avg_winding_rise, 1) if avg_winding_rise is not None else None,
            'top_oil_rise': round(top_oil_rise, 1) if top_oil_rise is not None else None,
            'ptot_used_kw': round(ptot_used_kw, 2) if ptot_used_kw is not None else None,
            'tau0_h': round(tau0_h, 2) if tau0_h is not None else None,
            'constante_C': constants.TEMP_RISE_CONSTANT.get(material),
            'message': final_message # Salva a mensagem final
        },
        'timestamp': datetime.datetime.now().isoformat()
    }
    log.info(f"[CALC TempRise] Dados a serem salvos no temperature-rise-store: {store_to_save}")

    # --- 5. Preparar Mensagem para UI ---
    display_message = ""
    if final_message:
        is_warning = "Aviso" in final_message
        display_message = html.Div(final_message,
                                    style={"color": colors.get('warning', 'orange') if is_warning else colors.get('fail', 'red'),
                                           "fontSize": "0.7rem"})

    # --- 6. Retornar Valores na Ordem CORRETA ---
    return_values = (
        store_to_save['resultados_temp_rise']['avg_winding_temp'],
        store_to_save['resultados_temp_rise']['avg_winding_rise'],
        store_to_save['resultados_temp_rise']['top_oil_rise'],
        store_to_save['resultados_temp_rise']['ptot_used_kw'],
        store_to_save['resultados_temp_rise']['tau0_h'],
        display_message,
        store_to_save
    )
    log.info(f"[CALC TempRise] Retornando valores: {return_values}")
    return return_values

# Callback para cálculo (usando o botão que era Limpar)
@callback(
    [
        Output("avg-winding-temp", "value", allow_duplicate=True),
        Output("avg-winding-rise", "value", allow_duplicate=True),
        Output("top-oil-rise", "value", allow_duplicate=True),
        Output("ptot-used", "value", allow_duplicate=True),
        Output("tau0-result", "value", allow_duplicate=True),
        Output("temp-rise-error-message", "children", allow_duplicate=True),
        Output("temperature-rise-store", "data", allow_duplicate=True)
    ],
    [Input("limpar-temp-rise", "n_clicks")],
    [
        State("temp-amb", "value"), State("winding-material", "value"),
        State("res-cold", "value"), State("temp-cold", "value"),
        State("res-hot", "value"), State("temp-top-oil", "value"),
        State("delta-theta-oil-max", "value"),
        State("transformer-inputs-store", "data"),
        State("losses-store", "data"),
        State("url", "pathname") # Adicionado pathname para verificação
    ],
    prevent_initial_call=True
)
def temperature_rise_calculate_limpar(n_clicks, temp_amb_str, winding_material, res_cold_str, temp_cold_str, res_hot_str, temp_top_oil_str, delta_theta_oil_max_str, transformer_data, losses_data, pathname):
    # Verificar se estamos na página correta
    if pathname != "/elevacao-temperatura":
        log.info(f"Ignorando callback temperature_rise_calculate_limpar em página diferente: {pathname}")
        raise PreventUpdate

    if n_clicks is None or n_clicks <= 0:
        raise PreventUpdate

    # Log detalhado para debug
    log.info("\n\n***** [CALC TempRise] CALLBACK INICIADO *****")
    log.info(f"[CALC TempRise] n_clicks = {n_clicks}")
    log.info(f"[CALC TempRise] Trigger: {callback_context.triggered_id}")

    # Imprimir no console também
    print(f"\n\n***** [CALC TempRise] CALLBACK INICIADO *****")
    print(f"[CALC TempRise] n_clicks = {n_clicks}")
    print(f"[CALC TempRise] Trigger: {callback_context.triggered_id}")
    print(f"[CALC TempRise] Inputs: temp_amb={temp_amb_str}, material={winding_material}, rc={res_cold_str}, tc={temp_cold_str}, rw={res_hot_str}, t_oil={temp_top_oil_str}")

    # --- 1. Validar e converter inputs locais ---
    input_values_local = {
        'ta': safe_float(temp_amb_str), 'material': winding_material,
        'rc': safe_float(res_cold_str), 'tc': safe_float(temp_cold_str),
        'rw': safe_float(res_hot_str), 't_oil': safe_float(temp_top_oil_str),
        'delta_theta_oil_max_ui': safe_float(delta_theta_oil_max_str)
    }
    validation_rules = {
        'ta': {'required': True, 'label': 'Temp. Ambiente (Θa)'},
        'material': {'required': True, 'allowed': ['cobre', 'aluminio'], 'label': 'Material'},
        'rc': {'required': True, 'positive': True, 'label': 'Resistência Fria (Rc)'},
        'tc': {'required': True, 'label': 'Temp. Ref. Fria (Θc)'},
        'rw': {'required': True, 'positive': True, 'label': 'Resistência Quente (Rw)'},
        't_oil': {'required': True, 'label': 'Temp. Topo Óleo Final (Θoil)'},
        'delta_theta_oil_max_ui': {'required': False, 'positive': True, 'label': 'ΔΘoil_max (UI)'},
    }
    log.info(f"[CALC TempRise] Valores de entrada: {input_values_local}")
    errors = validate_dict_inputs(input_values_local, validation_rules)
    if errors:
        log.warning(f"[CALC TempRise] Erros de validação Inputs Locais: {errors}")
        error_msg_div = html.Ul([html.Li(e) for e in errors], style={"color": colors.get('fail', 'red'), "fontSize": "0.7rem"})
        log.warning(f"[CALC TempRise] Retornando mensagem de erro: {error_msg_div}")
        return None, None, None, None, None, error_msg_div, no_update

    temp_amb = input_values_local['ta']; material = input_values_local['material']
    rc = input_values_local['rc']; tc = input_values_local['tc']
    rw = input_values_local['rw']; t_oil = input_values_local['t_oil']
    delta_theta_oil_max_ui = input_values_local['delta_theta_oil_max_ui']

    # --- 2. Ler e processar dados globais para Tau0 ---
    global_transformer_data = transformer_data if transformer_data and isinstance(transformer_data, dict) else {}
    global_losses_data = losses_data if losses_data and isinstance(losses_data, dict) else {}
    log.debug(f"[CALC TempRise] Dados globais lidos: Trafo={global_transformer_data}, Losses={global_losses_data}")

    peso_total_ton = safe_float(global_transformer_data.get('peso_total'))
    peso_oleo_ton = safe_float(global_transformer_data.get('peso_oleo'))
    perdas_vazio_kw = safe_float(global_losses_data.get('resultados_perdas_vazio', {}).get('perdas_vazio_kw'))
    perdas_carga_min_kw = safe_float(global_losses_data.get('resultados_perdas_carga', {}).get('perdas_carga_min'))
    delta_theta_oil_max_global = safe_float(global_transformer_data.get('elevacao_oleo_topo'))

    delta_theta_oil_max_calc = delta_theta_oil_max_ui if delta_theta_oil_max_ui is not None else delta_theta_oil_max_global
    log.debug(f"[CALC TempRise] Delta Theta Max UI: {delta_theta_oil_max_ui}, Global: {delta_theta_oil_max_global}, Usado: {delta_theta_oil_max_calc}")

    ptot_used_kw = perdas_carga_min_kw
    log.debug(f"[CALC TempRise] Perdas CargaMin={perdas_carga_min_kw} -> Ptot={ptot_used_kw}")

    # --- 3. Cálculos Principais ---
    avg_winding_temp, avg_winding_rise, top_oil_rise, tau0_h = None, None, None, None
    error_message = ""; warning_message_tau0 = ""
    try:
        log.info(f"[CALC TempRise] Chamando calculate_winding_temps com rc={rc}, tc={tc}, rw={rw}, temp_amb={temp_amb}, material={material}")
        avg_winding_temp, avg_winding_rise = calculate_winding_temps(rc, tc, rw, temp_amb, material)
        log.info(f"[CALC TempRise] Resultado calculate_winding_temps: avg_winding_temp={avg_winding_temp}, avg_winding_rise={avg_winding_rise}")

        log.info(f"[CALC TempRise] Chamando calculate_top_oil_rise com t_oil={t_oil}, temp_amb={temp_amb}")
        top_oil_rise = calculate_top_oil_rise(t_oil, temp_amb)
        log.info(f"[CALC TempRise] Resultado calculate_top_oil_rise: top_oil_rise={top_oil_rise}")

        if avg_winding_temp is None or avg_winding_rise is None or top_oil_rise is None:
             raise ValueError("Falha no cálculo básico de temperatura/elevação.")
        log.info(f"[CALC TempRise] Cálculos básicos OK: Tw={avg_winding_temp:.1f}, ΔTw={avg_winding_rise:.1f}, ΔToil={top_oil_rise:.1f}")

        # Cálculo tau0
        required_tau0 = {'Ptot': ptot_used_kw, 'ΔΘoil_max': delta_theta_oil_max_calc, 'Peso Total': peso_total_ton, 'Peso Óleo': peso_oleo_ton}
        missing_tau0 = [name for name, val in required_tau0.items() if val is None]
        if missing_tau0:
            warning_message_tau0 = f"Aviso: τ₀ não calculado. Dados faltantes: {', '.join(missing_tau0)}."
            log.warning(f"[CALC TempRise] {warning_message_tau0}")
        else:
            peso_total_kg = peso_total_ton * 1000
            peso_oleo_kg = peso_oleo_ton * 1000
            log.debug(f"[CALC TempRise] Calculando τ₀ com: Ptot={ptot_used_kw:.2f}kW, ΔΘmax={delta_theta_oil_max_calc:.1f}K, mT={peso_total_kg:.0f}kg, mO={peso_oleo_kg:.0f}kg")
            tau0_h = calculate_thermal_time_constant(ptot_used_kw, delta_theta_oil_max_calc, peso_total_kg, peso_oleo_kg)
            if tau0_h is None: warning_message_tau0 = "Aviso: Erro interno ao calcular τ₀."; log.error(f"[CALC TempRise] {warning_message_tau0}")
            else: log.info(f"[CALC TempRise] τ₀ calculado: {tau0_h:.2f} h")

    except ValueError as ve: log.warning(f"[CALC TempRise] Erro cálculo: {ve}"); error_message = f"Erro: {ve}"; avg_winding_temp=avg_winding_rise=top_oil_rise=tau0_h=None
    except Exception as e: log.exception("[CALC TempRise] Erro inesperado"); error_message = f"Erro inesperado: {e}"; avg_winding_temp=avg_winding_rise=top_oil_rise=tau0_h=None

    # --- 4. Preparar e Salvar Dados no Store Local ---
    final_message = error_message or warning_message_tau0
    store_to_save = {
        'inputs_temp_rise': { # Salva os valores originais da UI
            'input_ta': temp_amb_str, 'input_material': material, 'input_rc': res_cold_str,
            'input_tc': temp_cold_str, 'input_rw': res_hot_str, 'input_t_oil': temp_top_oil_str,
            'input_delta_theta_oil_max': delta_theta_oil_max_str
        },
        'resultados_temp_rise': { # Salva resultados numéricos e mensagem
            'avg_winding_temp': round(avg_winding_temp, 1) if avg_winding_temp is not None else None,
            'avg_winding_rise': round(avg_winding_rise, 1) if avg_winding_rise is not None else None,
            'top_oil_rise': round(top_oil_rise, 1) if top_oil_rise is not None else None,
            'ptot_used_kw': round(ptot_used_kw, 2) if ptot_used_kw is not None else None,
            'tau0_h': round(tau0_h, 2) if tau0_h is not None else None,
            'constante_C': constants.TEMP_RISE_CONSTANT.get(material),
            'message': final_message # Salva a mensagem final
        },
        'timestamp': datetime.datetime.now().isoformat()
    }
    log.info(f"[CALC TempRise] Dados a serem salvos no temperature-rise-store: {store_to_save}")

    # --- 5. Preparar Mensagem para UI ---
    display_message = ""
    if final_message:
        is_warning = "Aviso" in final_message
        display_message = html.Div(final_message,
                                    style={"color": colors.get('warning', 'orange') if is_warning else colors.get('fail', 'red'),
                                           "fontSize": "0.7rem"})
    else:
        display_message = html.Div("Cálculo realizado com sucesso!", style={"color": "green", "fontSize": "0.7rem"})

    # --- 6. Retornar Valores na Ordem CORRETA ---
    return_values = (
        store_to_save['resultados_temp_rise']['avg_winding_temp'],
        store_to_save['resultados_temp_rise']['avg_winding_rise'],
        store_to_save['resultados_temp_rise']['top_oil_rise'],
        store_to_save['resultados_temp_rise']['ptot_used_kw'],
        store_to_save['resultados_temp_rise']['tau0_h'],
        display_message,
        store_to_save
    )
    log.info(f"[CALC TempRise] Retornando valores: {return_values}")
    return return_values

