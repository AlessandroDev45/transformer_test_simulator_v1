# callbacks/losses.py
import datetime
import itertools
import logging
import math

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, State, html, no_update, ctx
from dash.exceptions import PreventUpdate

from app import app
from config import (
    CARD_HEADER_STYLE,
    ERROR_STYLE,
    PLACEHOLDER_STYLE,
    TABLE_HEADER_STYLE_MD,
    TABLE_HEADER_STYLE_SM,
    TABLE_PARAM_STYLE_MD,
    TABLE_PARAM_STYLE_SM,
    TABLE_STATUS_STYLE,
    TABLE_VALUE_STYLE_MD,
    TABLE_VALUE_STYLE_SM,
    TABLE_WRAPPER_STYLE,
)
from config import colors as CONFIG_COLORS
from utils.constants import (
    CAPACITORS_BY_VOLTAGE,
    CS_SWITCHES_BY_VOLTAGE_MONO,
    CS_SWITCHES_BY_VOLTAGE_TRI,
    DUT_POWER_LIMIT,
    EPS_CURRENT_LIMIT,
    Q_SWITCH_POWERS,
    SUT_AT_MAX_VOLTAGE,
    SUT_AT_MIN_VOLTAGE,
    SUT_AT_STEP_VOLTAGE,
    SUT_BT_VOLTAGE,
    perdas_nucleo_data,
    potencia_magnet_data,
)

# Importar funções de utilidade para stores
from utils.store_diagnostics import convert_numpy_types

# Importar estilos do módulo centralizado
from utils.styles import COLORS, COMPONENTS, TYPOGRAPHY

# Importações da aplicação
from components.validators import validate_dict_inputs

log = logging.getLogger(__name__)

# Data Definitions (No-Load Losses)
potencia_magnet = potencia_magnet_data
perdas_nucleo = perdas_nucleo_data

# Tolerance for floating point comparisons
epsilon = 1e-6

# DataFrame Creation (No-Load Losses)
try:
    df_potencia_magnet = pd.DataFrame(
        list(potencia_magnet.items()), columns=["key", "potencia_magnet"]
    )
    df_potencia_magnet[["inducao_nominal", "frequencia_nominal"]] = pd.DataFrame(
        df_potencia_magnet["key"].tolist(), index=df_potencia_magnet.index
    )
    df_potencia_magnet.drop("key", axis=1, inplace=True)
    df_potencia_magnet.set_index(["inducao_nominal", "frequencia_nominal"], inplace=True)

    df_perdas_nucleo = pd.DataFrame(list(perdas_nucleo.items()), columns=["key", "perdas_nucleo"])
    df_perdas_nucleo[["inducao_nominal", "frequencia_nominal"]] = pd.DataFrame(
        df_perdas_nucleo["key"].tolist(), index=df_perdas_nucleo.index
    )
    df_perdas_nucleo.drop("key", axis=1, inplace=True)
    df_perdas_nucleo.set_index(["inducao_nominal", "frequencia_nominal"], inplace=True)
except Exception as e:
    log.error(f"Erro criando DataFrames: {e}")
    df_potencia_magnet, df_perdas_nucleo = pd.DataFrame(), pd.DataFrame()


# Helpers
def create_input_row(label, id, placeholder, input_type="number"):
    """Creates a standard input row with label."""
    label_style = TYPOGRAPHY.get(
        "label", {"fontSize": "0.65rem", "fontWeight": "bold", "color": COLORS["text_light"]}
    )
    input_base_style = COMPONENTS.get(
        "input",
        {
            "fontSize": "0.7rem",
            "color": COLORS["text_light"],
            "backgroundColor": COLORS["background_input"],
            "border": f"1px solid {COLORS['border']}",
        },
    )
    final_input_style = {
        **input_base_style,
        "height": "26px",
        "padding": "0.15rem 0.3rem",
        "width": "75%",
    }
    return dbc.Row(
        [
            dbc.Col(dbc.Label(label, style=label_style), width=9, className="text-end pe-1"),
            dbc.Col(
                dbc.Input(
                    type=input_type,
                    id=id,
                    placeholder=placeholder,
                    persistence=True,
                    persistence_type="local",
                    style=final_input_style,
                ),
                width=3,
            ),
        ],
        className="g-1 mb-1",
    )


# --- Render Functions (Assumed to be in layouts/losses.py) ---
# Import render functions locally to avoid circular dependency
try:
    from layouts.losses import render_perdas_carga, render_perdas_vazio
except ImportError:
    log.error("Could not import render functions from layouts.losses. Defining placeholders.")

    def render_perdas_vazio():
        return html.Div("Layout Vazio não carregado.", style=ERROR_STYLE)

    def render_perdas_carga():
        return html.Div("Layout Carga não carregado.", style=ERROR_STYLE)


# --- Callbacks ---
@dash.callback(
    Output("conteudo-perdas", "children"),
    [
        Input("tabs-perdas", "active_tab"),
        # Removido Input("losses-store", "data") para evitar re-renderização quando o store muda
    ]
)
def losses_render_tab_content(tab_ativa):
    """
    Renderiza o conteúdo da aba selecionada na página de perdas.
    Agora é acionado APENAS quando a aba é alterada, não quando o store muda.
    """
    log.debug(f"losses_render_tab_content triggered. Active tab: {tab_ativa}, Trigger: {ctx.triggered_id}")

    if tab_ativa == "tab-vazio":
        return render_perdas_vazio()
    elif tab_ativa == "tab-carga":
        return render_perdas_carga()
    return html.P("Selecione uma aba.")


# --- Callbacks para Carregar Valores do Store (Perdas Vazio e Carga) ---
@dash.callback(
    [
        Output("perdas-vazio-kw", "value"),  # Removido allow_duplicate
        Output("peso-projeto-Ton", "value"),
        Output("corrente-excitacao", "value"),
        Output("inducao-nucleo", "value"),
        Output("corrente-excitacao-1-1", "value"),
        Output("corrente-excitacao-1-2", "value"),
    ],
    [
        Input("tabs-perdas", "active_tab"),
        Input("losses-store", "data")  # Adicionado Input do losses-store
    ],
    # Removido prevent_initial_call=True para garantir que o callback seja executado na carga inicial
)
def losses_populate_vazio_inputs(active_tab, losses_data_from_store):
    """
    Carrega e popula os valores de perdas em vazio nos inputs quando a aba é selecionada
    ou quando o store losses-store é atualizado.
    """
    log.critical(f"[LOSSES POPULATE VAZIO] Acionado. Aba: {active_tab}, Trigger: {ctx.triggered_id if ctx.triggered else 'N/A'}")

    if active_tab != "tab-vazio":
        # Se a aba não é a de vazio, não atualizamos NADA (nem com None).
        # Isso evita que os valores sejam apagados ao mudar de aba e voltar.
        raise PreventUpdate

    # Tentar usar os dados do store primeiro
    losses_data = losses_data_from_store

    # Se o store estiver vazio, tentar carregar do MCP diretamente
    if not losses_data or not isinstance(losses_data, dict) or "resultados_perdas_vazio" not in losses_data:
        log.warning("[LOSSES POPULATE VAZIO] Store vazio ou sem dados de vazio. Tentando carregar do MCP...")
        if hasattr(app, "mcp") and app.mcp is not None:
            mcp_data = app.mcp.get_data("losses-store")
            if mcp_data and isinstance(mcp_data, dict) and "resultados_perdas_vazio" in mcp_data:
                log.info("[LOSSES POPULATE VAZIO] Dados encontrados no MCP. Usando-os para popular os inputs.")
                losses_data = mcp_data
            else:
                log.warning("[LOSSES POPULATE VAZIO] Nenhum dado encontrado no MCP.")

    # Lista de chaves a serem carregadas
    keys_to_load = [
        "perdas_vazio_kw",
        "peso_nucleo",
        "corrente_excitacao",
        "inducao",
        "corrente_exc_1_1",
        "corrente_exc_1_2",
    ]

    # Sempre retorna valores (None se não encontrado), não no_update.
    outputs = [None] * len(keys_to_load)

    if losses_data and isinstance(losses_data, dict):
        # Verificar múltiplas estruturas possíveis para compatibilidade
        if "resultados_perdas_vazio" in losses_data:
            stored = losses_data["resultados_perdas_vazio"]
            if isinstance(stored, dict):
                outputs = [
                    stored.get(k) for k in keys_to_load
                ]
                log.info(f"[LOSSES POPULATE VAZIO] Valores encontrados em 'resultados_perdas_vazio': {outputs}")
            else:
                log.warning("[LOSSES POPULATE VAZIO] 'resultados_perdas_vazio' não é um dicionário.")
        # Verificar se os dados estão diretamente no dicionário principal
        elif any(k in losses_data for k in keys_to_load):
            outputs = [
                losses_data.get(k) for k in keys_to_load
            ]
            log.info(f"[LOSSES POPULATE VAZIO] Valores encontrados diretamente no dicionário principal: {outputs}")
        else:
            log.warning("[LOSSES POPULATE VAZIO] Nenhum dado válido encontrado nas estruturas conhecidas.")
    else:
        log.warning("[LOSSES POPULATE VAZIO] Nenhum dado válido em 'losses-store' ou MCP para perdas em vazio. Campos de Vazio serão None.")

    return tuple(outputs)


@dash.callback(
    [
        Output("perdas-carga-kw_U_nom", "value"),  # Removido allow_duplicate
        Output("perdas-carga-kw_U_min", "value"),
        Output("perdas-carga-kw_U_max", "value"),
        Output("temperatura-referencia", "value"),
    ],
    [
        Input("tabs-perdas", "active_tab"),
        Input("losses-store", "data")  # Adicionado Input do losses-store
    ],
    # Removido prevent_initial_call=True para garantir que o callback seja executado na carga inicial
)
def losses_populate_carga_inputs(active_tab, losses_data_from_store):
    """
    Carrega e popula os valores de perdas em carga nos inputs quando a aba é selecionada
    ou quando o store losses-store é atualizado.
    """
    log.critical(f"[LOSSES POPULATE CARGA] Acionado. Aba: {active_tab}, Trigger: {ctx.triggered_id if ctx.triggered else 'N/A'}")

    if active_tab != "tab-carga":
        raise PreventUpdate

    # Tentar usar os dados do store primeiro
    losses_data = losses_data_from_store

    # Se o store estiver vazio, tentar carregar do MCP diretamente
    if not losses_data or not isinstance(losses_data, dict) or "resultados_perdas_carga" not in losses_data:
        log.warning("[LOSSES POPULATE CARGA] Store vazio ou sem dados de carga. Tentando carregar do MCP...")
        if hasattr(app, "mcp") and app.mcp is not None:
            mcp_data = app.mcp.get_data("losses-store")
            if mcp_data and isinstance(mcp_data, dict) and "resultados_perdas_carga" in mcp_data:
                log.info("[LOSSES POPULATE CARGA] Dados encontrados no MCP. Usando-os para popular os inputs.")
                losses_data = mcp_data
            else:
                log.warning("[LOSSES POPULATE CARGA] Nenhum dado encontrado no MCP.")

    # Lista de chaves a serem carregadas
    keys_to_load = [
        "perdas_carga_nom",
        "perdas_carga_min",
        "perdas_carga_max",
        "temperatura_referencia",
    ]

    # Sempre retorna valores (None se não encontrado), não no_update.
    outputs = [None] * len(keys_to_load)

    if losses_data and isinstance(losses_data, dict):
        # Verificar múltiplas estruturas possíveis para compatibilidade
        if "resultados_perdas_carga" in losses_data:
            stored = losses_data["resultados_perdas_carga"]
            if isinstance(stored, dict):
                outputs = [
                    stored.get(k) for k in keys_to_load
                ]
                log.info(f"[LOSSES POPULATE CARGA] Valores encontrados em 'resultados_perdas_carga': {outputs}")
            else:
                log.warning("[LOSSES POPULATE CARGA] 'resultados_perdas_carga' não é um dicionário.")
        # Verificar se os dados estão diretamente no dicionário principal
        elif any(k in losses_data for k in keys_to_load):
            outputs = [
                losses_data.get(k) for k in keys_to_load
            ]
            log.info(f"[LOSSES POPULATE CARGA] Valores encontrados diretamente no dicionário principal: {outputs}")
        else:
            log.warning("[LOSSES POPULATE CARGA] Nenhum dado válido encontrado nas estruturas conhecidas.")
    else:
        log.warning("[LOSSES POPULATE CARGA] Nenhum dado válido em 'losses-store' ou MCP para perdas em carga. Campos de Carga serão None.")

    return tuple(outputs)


# --- Callback para Atualizar Cache de Dados do Transformador removido ---
# Este callback foi removido pois a atualização é feita pelo callback global em global_updates.py


# --- Callback para atualizar o painel de informações do transformador na página de perdas ---
@dash.callback(
    Output("transformer-info-losses-page", "children"),
    Input("transformer-info-losses", "children"),
    prevent_initial_call=False,
)
def update_losses_page_info_panel(global_panel_content):
    """
    Copia o conteúdo do painel de informações global para o painel local da página de perdas.
    Este callback é acionado quando o painel global é atualizado pelo callback global_updates_all_transformer_info_panels.
    """
    log.debug("Atualizando painel de informações do transformador na página de perdas")
    return global_panel_content


# --- Callback Perdas em Vazio (Unchanged from previous version) ---
@dash.callback(
    [
        Output("parametros-gerais-card-body", "children"),
        Output("dut-voltage-level-results-body", "children"),
        Output("sut-analysis-results-area", "children"),
        Output("legend-observations-area", "children"),
        Output("losses-store", "data", allow_duplicate=True),
    ],
    [Input("calcular-perdas-vazio", "n_clicks")],
    [
        State(id, "value")
        for id in [
            "perdas-vazio-kw",
            "peso-projeto-Ton",
            "corrente-excitacao",
            "inducao-nucleo",
            "corrente-excitacao-1-1",
            "corrente-excitacao-1-2",
        ]
    ] + [State("losses-store", "data")],  # Adicionado State do losses-store
    prevent_initial_call=True,
)
def losses_handle_perdas_vazio(
    n_clicks,
    perdas_vazio_ui,
    peso_nucleo_ui,
    corrente_excitacao_ui,
    inducao_ui,
    corrente_exc_1_1_ui,
    corrente_exc_1_2_ui,
    current_losses_store_data,  # Novo parâmetro para o State do losses-store
):
    """
    Processa os inputs de perdas em vazio, atualiza o MCP, e retorna os resultados para a UI.
    """
    if n_clicks is None:
        raise PreventUpdate

    # Verificar se o callback foi acionado pelo botão de calcular
    if ctx.triggered_id != "calcular-perdas-vazio":
        log.warning(f"[losses_handle_perdas_vazio] Bloqueando gravação fantasma. Trigger: {ctx.triggered_id}")
        raise PreventUpdate

    initial_params = html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE)
    initial_dut_volt = html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE)
    initial_sut = html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE)
    initial_legend_obs = html.Div()

    # Verificar se o MCP está disponível
    if not hasattr(app, "mcp") or app.mcp is None:
        error_div = html.Div(
            "MCP não disponível. Não é possível processar os dados.", style=ERROR_STYLE
        )
        return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update

    # --- Input Validation ---
    required_inputs = [perdas_vazio_ui, peso_nucleo_ui, corrente_excitacao_ui, inducao_ui]
    if any(val is None or val == "" for val in required_inputs):
        error_div = html.Div(
            "Preencha todos os campos obrigatórios (Perdas, Peso, Corr. Exc%, Indução).",
            style=ERROR_STYLE,
        )
        return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update

    # Obter dados do transformador do MCP
    transformer_data = app.mcp.get_data("transformer-inputs-store")
    if not transformer_data:
        log.error("Dados básicos do transformador não encontrados no MCP.")
        error_div = html.Div("Dados básicos do transformador não encontrados.", style=ERROR_STYLE)
        return initial_params, initial_dut_volt, initial_sut, initial_legend_obs, no_update

    # Verificar se os dados essenciais estão presentes
    if (
        not transformer_data.get("potencia_mva")
        or not transformer_data.get("tensao_at")
        or not transformer_data.get("tensao_bt")
    ):
        log.error(
            f"Dados essenciais ausentes no transformer-inputs-store: potencia={transformer_data.get('potencia_mva')}, tensao_at={transformer_data.get('tensao_at')}, tensao_bt={transformer_data.get('tensao_bt')}"
        )
        error_div = html.Div(
            "Dados essenciais do transformador ausentes. Preencha os dados básicos na página 'Dados Básicos'.",
            style=ERROR_STYLE,
        )
        return initial_params, initial_dut_volt, initial_sut, initial_legend_obs, no_update

    # Obter dados de perdas existentes do MCP (já temos via current_losses_store_data)
    # losses_data = app.mcp.get_data("losses-store")

    try:
        # --- Constants & Helpers ---
        tensao_sut_bt = SUT_BT_VOLTAGE
        tensao_sut_at_min = SUT_AT_MIN_VOLTAGE
        tensao_sut_at_max = SUT_AT_MAX_VOLTAGE
        step_sut_at = SUT_AT_STEP_VOLTAGE
        limite_corrente_eps = EPS_CURRENT_LIMIT
        limite_potencia_dut = DUT_POWER_LIMIT
        # Small number for safe division is now epsilon (defined at module level)

        def safe_float(value, default=None):
            try:
                return float(value) if value is not None and value != "" else default
            except (ValueError, TypeError):
                return default

        # --- Calculations ---
        frequencia = safe_float(transformer_data.get("frequencia", 60), 60)
        perdas_vazio = safe_float(perdas_vazio_ui, 0.0)
        peso_nucleo = safe_float(peso_nucleo_ui, 0.0)
        corrente_excitacao_percentual = safe_float(corrente_excitacao_ui, 0.0)
        tensao_bt_kv = safe_float(transformer_data.get("tensao_bt", 0), 0.0)  # Assume BT is in kV
        inducao = safe_float(inducao_ui, 0.0)
        tipo_transformador = transformer_data.get("tipo_transformador", "Trifásico")
        corrente_nominal_bt = safe_float(transformer_data.get("corrente_nominal_bt", 0), 0.0)
        potencia = safe_float(transformer_data.get("potencia_mva", 0), 0.0)
        tensao_nominal_at = safe_float(transformer_data.get("tensao_at", 0), 0.0)
        corrente_exc_1_1_input = safe_float(corrente_exc_1_1_ui)  # Keep None if empty/invalid
        corrente_exc_1_2_input = safe_float(corrente_exc_1_2_ui)  # Keep None if empty/invalid

        # --- Data Validation after Conversion ---
        if any(
            v is None or v <= epsilon
            for v in [
                potencia,
                tensao_nominal_at,
                tensao_bt_kv,
                corrente_nominal_bt,
                perdas_vazio,
                inducao,
                corrente_excitacao_percentual,
            ]
        ):
            # Peso núcleo can be zero if calculated
            error_msg_detail = ", ".join(
                [
                    f"{k}={v}"
                    for k, v in {
                        "Potência": potencia,
                        "Tensão AT": tensao_nominal_at,
                        "Tensão BT": tensao_bt_kv,
                        "Corrente BT": corrente_nominal_bt,
                        "Perdas Vazio": perdas_vazio,
                        "Indução": inducao,
                        "Corr Exc %": corrente_excitacao_percentual,
                    }.items()
                    if v is None or v <= epsilon
                ]
            )
            error_div = html.Div(
                f"Dados essenciais devem ser maiores que zero ou não nulos. Inválidos: {error_msg_detail}",
                style=ERROR_STYLE,
            )
            return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update
        # Special check for peso_nucleo if it was an input > 0
        if peso_nucleo is not None and peso_nucleo <= epsilon:
            error_div = html.Div(
                f"Peso do núcleo de projeto ({peso_nucleo}) deve ser maior que zero.",
                style=ERROR_STYLE,
            )
            return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update

        sqrt_3 = math.sqrt(3) if tipo_transformador == "Trifásico" else 1.0
        inducao_arredondada = round(inducao * 10) / 10
        frequencias_validas = [50, 60, 100, 120, 150, 200, 240, 250, 300, 350, 400, 500]
        frequencia_arredondada = min(frequencias_validas, key=lambda x: abs(x - frequencia))

        # --- Factor Lookup ---
        lookup_key = (inducao_arredondada, frequencia_arredondada)
        try:
            # Use .get with a default to handle potential missing keys more gracefully
            fator_perdas = (
                df_perdas_nucleo.loc[lookup_key, "perdas_nucleo"]
                if lookup_key in df_perdas_nucleo.index
                else None
            )
            fator_potencia_mag = (
                df_potencia_magnet.loc[lookup_key, "potencia_magnet"]
                if lookup_key in df_potencia_magnet.index
                else None
            )
            # More specific error if lookup worked but value is missing/None
            if fator_perdas is None or fator_potencia_mag is None:
                raise KeyError(f"Valor não encontrado para {lookup_key} em um dos DataFrames.")
        except KeyError:
            error_div = html.Div(
                f"Fatores de perdas/potência não encontrados para Indução {inducao_arredondada}T @ {frequencia_arredondada}Hz.",
                style=ERROR_STYLE,
            )
            return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update
        except Exception as e:
            log.error(f"Erro ao buscar fatores no DataFrame: {e}")
            error_div = html.Div(f"Erro ao buscar fatores: {e}", style=ERROR_STYLE)
            return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update

        if (
            fator_perdas is None
            or fator_perdas <= epsilon
            or fator_potencia_mag is None
            or fator_potencia_mag <= epsilon
        ):
            error_div = html.Div(
                f"Fatores de perdas/potência inválidos ({fator_perdas=}, {fator_potencia_mag=}) para Indução {inducao_arredondada}T @ {frequencia_arredondada}Hz.",
                style=ERROR_STYLE,
            )
            return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update

        # --- Core & Excitation Calculations ---
        peso_nucleo_calc = perdas_vazio / fator_perdas if fator_perdas > epsilon else 0
        potencia_mag = fator_potencia_mag * peso_nucleo_calc  # kVAR
        corrente_excitacao_calc = (
            potencia_mag / (tensao_bt_kv * sqrt_3) if (tensao_bt_kv * sqrt_3) > epsilon else 0
        )  # A
        corrente_excitacao_percentual_calc = (
            (corrente_excitacao_calc / corrente_nominal_bt) * 100
            if corrente_nominal_bt > epsilon
            else 0
        )

        tensao_teste_1_1_kv = tensao_bt_kv * 1.1
        tensao_teste_1_2_kv = tensao_bt_kv * 1.2

        # Calculated 1.1pu / 1.2pu currents (based on M4 assumption)
        corrente_excitacao_1_1_calc = 2 * corrente_excitacao_calc
        corrente_excitacao_1_2_calc = 4 * corrente_excitacao_calc

        # Project currents (from % input)
        corrente_excitacao_projeto = corrente_nominal_bt * (corrente_excitacao_percentual / 100.0)
        fator_excitacao_default = (
            3 if tipo_transformador == "Trifásico" else 5
        )  # Default multiplier if inputs are missing

        if corrente_exc_1_1_input is not None:
            corrente_excitacao_1_1 = corrente_nominal_bt * (corrente_exc_1_1_input / 100.0)
        else:
            corrente_excitacao_1_1 = fator_excitacao_default * corrente_excitacao_projeto

        if corrente_exc_1_2_input is not None:
            corrente_excitacao_1_2 = corrente_nominal_bt * (corrente_exc_1_2_input / 100.0)
        else:
            corrente_excitacao_1_2 = None  # No default assumption for 1.2pu

        # Test Powers (kVA)
        potencia_ensaio_1pu_calc_kva = tensao_bt_kv * corrente_excitacao_calc * sqrt_3
        potencia_ensaio_1_1pu_calc_kva = tensao_teste_1_1_kv * corrente_excitacao_1_1_calc * sqrt_3
        potencia_ensaio_1_2pu_calc_kva = tensao_teste_1_2_kv * corrente_excitacao_1_2_calc * sqrt_3

        potencia_ensaio_1pu_projeto_kva = tensao_bt_kv * corrente_excitacao_projeto * sqrt_3
        potencia_ensaio_1_1pu_projeto_kva = tensao_teste_1_1_kv * corrente_excitacao_1_1 * sqrt_3
        potencia_ensaio_1_2pu_projeto_kva = (
            (tensao_teste_1_2_kv * corrente_excitacao_1_2 * sqrt_3)
            if corrente_excitacao_1_2 is not None
            else None
        )

        # Project Factors
        fator_perdas_projeto = (
            perdas_vazio / peso_nucleo if peso_nucleo > epsilon else 0
        )  # W/kg (assuming peso is Ton -> *1000) -> Actually kW/Ton
        potencia_mag_projeto_kvar = (
            potencia_ensaio_1pu_projeto_kva  # Approximated as test power at 1pu
        )
        # fator_potencia_mag_projeto = potencia_mag_projeto_kvar / peso_nucleo if peso_nucleo > epsilon else 0 # kVAR / Ton
        # Match units with M4 factor (VAR/kg)
        fator_potencia_mag_projeto = (
            (potencia_mag_projeto_kvar * 1000) / (peso_nucleo * 1000)
            if peso_nucleo > epsilon
            else 0
        )  # VAR/kg

        # --- Result Dictionaries ---
        resultados_aco_m4 = {
            "Perdas em Vazio (kW)": perdas_vazio,
            "Tensão nominal teste 1.0 pu (kV)": tensao_bt_kv,
            "Corrente de excitação calculada (A)": corrente_excitacao_calc,
            "Corrente de excitação percentual (%)": corrente_excitacao_percentual_calc,
            "Tensão de teste 1.1 pu (kV)": tensao_teste_1_1_kv,
            "Tensão de teste 1.2 pu (kV)": tensao_teste_1_2_kv,
            "Corrente de excitação 1.1 pu (A)": corrente_excitacao_1_1_calc,
            "Corrente de excitação 1.2 pu (A)": corrente_excitacao_1_2_calc,
            "Frequência (Hz)": frequencia,
            "Potência Mag. (kVAR)": potencia_mag,
            "Fator de perdas Mag. (VAR/kg)": fator_potencia_mag,
            "Fator de perdas (W/kg)": fator_perdas,  # Assuming input fator_perdas is W/kg
            "Peso do núcleo Calculado(Ton)": peso_nucleo_calc,
            "Potência de Ensaio (1 pu) (kVA)": potencia_ensaio_1pu_calc_kva,
            "Potência de Ensaio (1.1 pu) (kVA)": potencia_ensaio_1_1pu_calc_kva,
            "Potência de Ensaio (1.2 pu) (kVA)": potencia_ensaio_1_2pu_calc_kva,
        }
        resultados_projeto = {
            "Perdas em Vazio (kW)": perdas_vazio,
            "Tensão nominal teste 1.0 pu (kV)": tensao_bt_kv,
            "Corrente Nominal BT (A)": corrente_nominal_bt,
            "Corrente de excitação (A)": corrente_excitacao_projeto,
            "Tensão de teste 1.1 pu (kV)": tensao_teste_1_1_kv,
            "Corrente de excitação 1.1 pu (A)": corrente_excitacao_1_1,
            "Frequência (Hz)": frequencia,
            "Potência Mag. (kVAR)": potencia_mag_projeto_kvar,
            "Fator de perdas Mag. (VAR/kg)": fator_potencia_mag_projeto,
            "Fator de perdas (W/kg)": fator_perdas_projeto
            * 1000
            / 1000,  # kW/Ton -> W/kg? Assuming input perdas_vazio is kW, peso_nucleo is Ton. Then perdas_vazio / peso_nucleo = kW/Ton. Need W/kg. (kW/Ton) * (1000 W/kW) / (1000 kg/Ton) = W/kg
            "Potência de Ensaio (1 pu) (kVA)": potencia_ensaio_1pu_projeto_kva,
            "Potência de Ensaio (1.1 pu) (kVA)": potencia_ensaio_1_1pu_projeto_kva,
        }
        if corrente_excitacao_1_2 is not None:
            resultados_projeto["Tensão de teste 1.2 pu (kV)"] = tensao_teste_1_2_kv
            resultados_projeto["Corrente de excitação 1.2 pu (A)"] = corrente_excitacao_1_2
            resultados_projeto[
                "Potência de Ensaio (1.2 pu) (kVA)"
            ] = potencia_ensaio_1_2pu_projeto_kva

        # --- SUT/EPS Analysis (Vazio - Simple Reflection) ---
        sut_analysis_data = {"1.0": None, "1.1": None, "1.2": None}
        for pu_level in ["1.0", "1.1", "1.2"]:
            V_teste_dut_lv_kv, I_exc_dut_lv = (None, None)
            if pu_level == "1.0":
                V_teste_dut_lv_kv, I_exc_dut_lv = tensao_bt_kv, corrente_excitacao_projeto
            elif pu_level == "1.1":
                V_teste_dut_lv_kv, I_exc_dut_lv = tensao_teste_1_1_kv, corrente_excitacao_1_1
            elif pu_level == "1.2" and corrente_excitacao_1_2 is not None:
                V_teste_dut_lv_kv, I_exc_dut_lv = tensao_teste_1_2_kv, corrente_excitacao_1_2

            if (
                V_teste_dut_lv_kv is None
                or V_teste_dut_lv_kv <= epsilon
                or I_exc_dut_lv is None
                or I_exc_dut_lv <= epsilon
            ):
                sut_analysis_data[pu_level] = {
                    "status": "Sem dados de corrente/tensão",
                    "taps_info": [],
                }
                continue

            V_target_sut_hv = V_teste_dut_lv_kv * 1000  # Target in Volts
            taps_sut_hv = np.arange(tensao_sut_at_min, tensao_sut_at_max + step_sut_at, step_sut_at)
            taps_sut_hv = taps_sut_hv[taps_sut_hv > epsilon]
            if len(taps_sut_hv) == 0:
                sut_analysis_data[pu_level] = {"status": "Faixa SUT inválida", "taps_info": []}
                continue

            taps_adequados = [
                tap for tap in taps_sut_hv if tap >= V_target_sut_hv - 1e-6
            ]  # Tolerance

            if not taps_adequados:
                highest_sut_tap_kv = taps_sut_hv[-1] / 1000 if len(taps_sut_hv) > 0 else "N/A"
                sut_analysis_data[pu_level] = {
                    "status": f"Tensão > {highest_sut_tap_kv}kV SUT Max",
                    "taps_info": [],
                }
                continue

            diffs = {tap: abs(tap - V_target_sut_hv) for tap in taps_adequados}
            taps_ordenados = sorted(taps_adequados, key=lambda tap: diffs[tap])
            # Select top 5 closest ADEQUATE taps
            top_taps = taps_ordenados[:5]

            taps_info_list = []
            for V_sut_hv_tap in top_taps:
                if tensao_sut_bt <= epsilon:
                    continue  # Avoid division by zero
                ratio_sut = V_sut_hv_tap / tensao_sut_bt
                I_sut_lv = I_exc_dut_lv * ratio_sut  # Simple reflection for vazio
                percent_limite = (
                    (I_sut_lv / limite_corrente_eps) * 100
                    if limite_corrente_eps > epsilon
                    else float("inf")
                )
                taps_info_list.append(
                    {
                        "tap_sut_kv": V_sut_hv_tap / 1000,
                        "corrente_eps_a": I_sut_lv,
                        "percent_limite": percent_limite,
                    }
                )

            # Sort final list by voltage
            taps_info_list.sort(key=lambda x: x["tap_sut_kv"])
            sut_analysis_data[pu_level] = {"status": "OK", "taps_info": taps_info_list}

        # --- Layout Helper Functions (Vazio - Unchanged) ---
        def create_general_parameters_table(res_proj, res_m4):
            """Creates the general parameters comparison table."""
            params = [
                "Tensão nominal teste 1.0 pu (kV)",
                "Corrente Nominal BT (A)",
                "Frequência (Hz)",
                "Potência Mag. (kVAR)",
                "Fator de perdas Mag. (VAR/kg)",
                "Fator de perdas (W/kg)",
                "Peso do núcleo Calculado(Ton)",
                "Corrente de excitação percentual (%)",
            ]  # M4 Only
            header = html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Parâmetro",
                            style={**TABLE_HEADER_STYLE_SM, "width": "50%", "textAlign": "left"},
                        ),
                        html.Th("Valor (Projeto)", style={**TABLE_HEADER_STYLE_SM, "width": "25%"}),
                        html.Th("Valor (Aço M4)", style={**TABLE_HEADER_STYLE_SM, "width": "25%"}),
                    ]
                )
            )
            rows = []
            for param in params:
                proj_val = res_proj.get(param)
                m4_val = res_m4.get(param)
                # Use specific formatting for better readability
                prec = 2
                if "Tensão" in param:
                    prec = 1
                if "Corrente" in param:
                    prec = 1
                if "Frequência" in param:
                    prec = 0
                if "Peso" in param:
                    prec = 3
                if "Fator" in param:
                    prec = 2

                disp_proj = (
                    f"{proj_val:.{prec}f}"
                    if isinstance(proj_val, (int, float))
                    else str(proj_val)
                    if proj_val is not None
                    else "-"
                )
                disp_m4 = (
                    f"{m4_val:.{prec}f}"
                    if isinstance(m4_val, (int, float))
                    else str(m4_val)
                    if m4_val is not None
                    else "-"
                )

                # Adjust display for specific params
                if param in ["Corrente Nominal BT (A)"]:
                    disp_m4 = "-"
                if param == "Peso do núcleo Calculado(Ton)":
                    disp_proj = "-"
                if param == "Corrente de excitação percentual (%)":
                    proj_input_perc = corrente_excitacao_percentual  # Use the original input value
                    disp_proj = f"{proj_input_perc:.2f}" if proj_input_perc is not None else "-"

                rows.append(
                    html.Tr(
                        [
                            html.Td(param, style=TABLE_PARAM_STYLE_SM),
                            html.Td(
                                disp_proj, style=TABLE_VALUE_STYLE_SM, className="table-value-cell"
                            ),
                            html.Td(
                                disp_m4, style=TABLE_VALUE_STYLE_SM, className="table-value-cell"
                            ),
                        ]
                    )
                )
            body = html.Tbody(rows)
            return dbc.Table([header, body], bordered=True, hover=True, striped=True, size="sm")

        def create_voltage_level_table(res_proj, res_m4):
            """Creates the voltage level comparison table."""
            color_red_style = {
                "backgroundColor": CONFIG_COLORS["danger_bg"],
                "color": CONFIG_COLORS["danger_text"],
                "fontWeight": "bold",
            }
            header_style_base = {
                **TABLE_HEADER_STYLE_MD,
                "borderBottom": f"2px solid {COLORS['border']}",
            }

            header = html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Parâmetro",
                            style={**header_style_base, "width": "25%", "textAlign": "left"},
                        ),
                        html.Th(
                            "Origem",
                            style={**header_style_base, "width": "15%", "textAlign": "center"},
                        ),
                        html.Th(
                            "1.0 pu",
                            style={
                                **header_style_base,
                                "width": "20%",
                                "borderLeft": f"2px solid {COLORS['border_strong']}",
                            },
                        ),
                        html.Th(
                            "1.1 pu",
                            style={
                                **header_style_base,
                                "width": "20%",
                                "borderLeft": f"1px solid {COLORS['border']}",
                            },
                        ),
                        html.Th(
                            "1.2 pu",
                            style={
                                **header_style_base,
                                "width": "20%",
                                "borderLeft": f"1px solid {COLORS['border']}",
                            },
                        ),
                    ]
                )
            )

            params = [
                "Tensão de teste (kV)",
                "Corrente de excitação (A)",
                "Potência de Ensaio (kVA)",
            ]
            keys_proj = {
                "Tensão de teste (kV)": {
                    "1.0 pu": "Tensão nominal teste 1.0 pu (kV)",
                    "1.1 pu": "Tensão de teste 1.1 pu (kV)",
                    "1.2 pu": "Tensão de teste 1.2 pu (kV)",
                },
                "Corrente de excitação (A)": {
                    "1.0 pu": "Corrente de excitação (A)",
                    "1.1 pu": "Corrente de excitação 1.1 pu (A)",
                    "1.2 pu": "Corrente de excitação 1.2 pu (A)",
                },
                "Potência de Ensaio (kVA)": {
                    "1.0 pu": "Potência de Ensaio (1 pu) (kVA)",
                    "1.1 pu": "Potência de Ensaio (1.1 pu) (kVA)",
                    "1.2 pu": "Potência de Ensaio (1.2 pu) (kVA)",
                },
            }
            keys_m4 = {
                "Tensão de teste (kV)": {
                    "1.0 pu": "Tensão nominal teste 1.0 pu (kV)",
                    "1.1 pu": "Tensão de teste 1.1 pu (kV)",
                    "1.2 pu": "Tensão de teste 1.2 pu (kV)",
                },
                "Corrente de excitação (A)": {
                    "1.0 pu": "Corrente de excitação calculada (A)",
                    "1.1 pu": "Corrente de excitação 1.1 pu (A)",
                    "1.2 pu": "Corrente de excitação 1.2 pu (A)",
                },
                "Potência de Ensaio (kVA)": {
                    "1.0 pu": "Potência de Ensaio (1 pu) (kVA)",
                    "1.1 pu": "Potência de Ensaio (1.1 pu) (kVA)",
                    "1.2 pu": "Potência de Ensaio (1.2 pu) (kVA)",
                },
            }
            exceeded_values = {
                "projeto": {"1.0 pu": False, "1.1 pu": False, "1.2 pu": False},
                "aco_m4": {"1.0 pu": False, "1.1 pu": False, "1.2 pu": False},
            }

            param_style = {
                **TABLE_PARAM_STYLE_MD,
                "borderRight": f"1px solid {COLORS['border']}",
                "verticalAlign": "middle",
                "textAlign": "left",
            }
            origin_style = {
                **TABLE_PARAM_STYLE_MD,
                "textAlign": "center",
                "borderRight": f"2px solid {COLORS['border_strong']}",
                "verticalAlign": "middle",
            }
            value_styles = {
                0: {
                    **TABLE_VALUE_STYLE_MD,
                    "borderLeft": f"2px solid {COLORS['border_strong']}",
                    "verticalAlign": "middle",
                },
                1: {
                    **TABLE_VALUE_STYLE_MD,
                    "borderLeft": f"1px solid {COLORS['border']}",
                    "verticalAlign": "middle",
                },
                2: {
                    **TABLE_VALUE_STYLE_MD,
                    "borderLeft": f"1px solid {COLORS['border']}",
                    "verticalAlign": "middle",
                },
            }

            rows = []
            for param_idx, param in enumerate(params):
                # Project Row
                proj_cells = [
                    html.Td(param, rowSpan=2, style=param_style),
                    html.Td("Projeto", style=origin_style),
                ]
                for i, pu in enumerate(["1.0 pu", "1.1 pu", "1.2 pu"]):
                    key = keys_proj.get(param, {}).get(pu)
                    value = res_proj.get(key)
                    prec = (
                        1 if "Tensão" in param else 1 if "Corrente" in param else 0
                    )  # kVA integer
                    display = f"{value:.{prec}f}" if isinstance(value, (int, float)) else "-"

                    # Calcular percentual em relação à corrente nominal de BT para "Corrente de excitação (A)"
                    if (
                        param == "Corrente de excitação (A)"
                        and isinstance(value, (int, float))
                        and corrente_nominal_bt > epsilon
                    ):
                        percentual = (value / corrente_nominal_bt) * 100
                        display = f"{value:.{prec}f} ({percentual:.1f}%)"

                    style = {**value_styles[i]}
                    if (
                        param == "Potência de Ensaio (kVA)"
                        and isinstance(value, (int, float))
                        and value > limite_potencia_dut
                    ):
                        style.update(color_red_style)
                        exceeded_values["projeto"][pu] = True
                    proj_cells.append(html.Td(display, style=style, className="table-value-cell"))
                rows.append(html.Tr(proj_cells))

                # M4 Row
                m4_cells = [html.Td("Aço M4", style=origin_style)]
                for i, pu in enumerate(["1.0 pu", "1.1 pu", "1.2 pu"]):
                    key = keys_m4.get(param, {}).get(pu)
                    value = res_m4.get(key)
                    prec = (
                        1 if "Tensão" in param else 1 if "Corrente" in param else 0
                    )  # kVA integer
                    display = f"{value:.{prec}f}" if isinstance(value, (int, float)) else "-"

                    # Calcular percentual em relação à corrente nominal de BT para "Corrente de excitação (A)"
                    if (
                        param == "Corrente de excitação (A)"
                        and isinstance(value, (int, float))
                        and corrente_nominal_bt > epsilon
                    ):
                        percentual = (value / corrente_nominal_bt) * 100
                        display = f"{value:.{prec}f} ({percentual:.1f}%)"

                    style = {**value_styles[i]}
                    if (
                        param == "Potência de Ensaio (kVA)"
                        and isinstance(value, (int, float))
                        and value > limite_potencia_dut
                    ):
                        style.update(color_red_style)
                        exceeded_values["aco_m4"][pu] = True
                    m4_cells.append(html.Td(display, style=style, className="table-value-cell"))
                rows.append(html.Tr(m4_cells))

                # Divider
                if param_idx < len(params) - 1:
                    rows.append(
                        html.Tr(
                            html.Td(
                                colSpan=5,
                                style={
                                    "borderBottom": f"2px solid {COLORS['border']}",
                                    "padding": "0",
                                    "height": "1px",
                                },
                            )
                        )
                    )

            body = html.Tbody(rows)
            return (
                dbc.Table(
                    [header, body],
                    bordered=True,
                    hover=True,
                    size="sm",
                    style={"border": f"1px solid {COLORS['border']}", "borderCollapse": "collapse"},
                ),
                exceeded_values,
            )

        def _create_single_sut_analysis_table(pu_data):
            """Creates a small table for SUT/EPS analysis for one PU level (Vazio)."""
            header_style = {
                **TABLE_HEADER_STYLE_SM,
                "backgroundColor": COLORS["background_header"],
                "color": COLORS["text_header"],
            }
            cell_style = TABLE_VALUE_STYLE_SM
            current_styles = {
                "low": {**cell_style, "backgroundColor": CONFIG_COLORS["ok_bg_faint"]},
                "medium": {**cell_style, "backgroundColor": CONFIG_COLORS["warning_bg_faint"]},
                "high": {**cell_style, "backgroundColor": CONFIG_COLORS["warning_high_bg_faint"]},
                "critical": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["danger_bg"],
                    "color": CONFIG_COLORS["danger_text"],
                    "fontWeight": "bold",
                },
            }

            def get_style(percent):
                if percent is None or math.isnan(percent):
                    return cell_style
                if percent < 50:
                    return current_styles["low"]
                elif percent < 85:
                    return current_styles["medium"]
                elif percent <= 100:
                    return current_styles["high"]
                else:
                    return current_styles["critical"]

            rows = [
                html.Tr(
                    [
                        html.Th("Tap SUT (kV)", style=header_style),
                        html.Th("Corrente EPS (A)", style=header_style),
                    ]
                )
            ]
            status_msg = pu_data.get("status", "Erro")
            taps_info = pu_data.get("taps_info", [])

            if status_msg != "OK":
                rows.append(
                    html.Tr(
                        html.Td(
                            status_msg,
                            colSpan=2,
                            style={**cell_style, "color": COLORS["danger"], "fontWeight": "bold"},
                            className="table-value-cell",
                        )
                    )
                )
            elif not taps_info:
                rows.append(
                    html.Tr(
                        html.Td(
                            "Nenhum tap SUT aplicável.",
                            colSpan=2,
                            style=cell_style,
                            className="table-value-cell",
                        )
                    )
                )
            else:
                for info in taps_info:  # Already sorted by voltage and limited to 5
                    current_style = get_style(info.get("percent_limite"))
                    tap_disp = (
                        f"{info['tap_sut_kv']:.1f}" if info.get("tap_sut_kv") is not None else "-"
                    )
                    curr_disp = (
                        f"{info['corrente_eps_a']:.1f}"
                        if info.get("corrente_eps_a") is not None
                        else "-"
                    )
                    rows.append(
                        html.Tr(
                            [
                                html.Td(tap_disp, style=cell_style, className="table-value-cell"),
                                html.Td(
                                    curr_disp, style=current_style, className="table-value-cell"
                                ),
                            ]
                        )
                    )
            return dbc.Table(
                html.Tbody(rows),
                bordered=True,
                hover=True,
                striped=True,
                size="sm",
                style={"width": "100%", "tableLayout": "fixed", "marginBottom": "0"},
            )

        def create_sut_analysis_layout(sut_data):
            """Creates the 3-column layout for SUT/EPS analysis (Vazio)."""
            title_style = {
                "fontSize": "0.75rem",
                "fontWeight": "bold",
                "color": COLORS["text_header"],
                "backgroundColor": COLORS["background_header"],
                "borderRadius": "2px",
                "padding": "0.2rem 0",
            }
            container_style = {"padding": "0 0.25rem"}
            cols = []
            for pu_level in ["1.0", "1.1", "1.2"]:
                pu_info = sut_data.get(pu_level)
                content = html.Div("Dados indisponíveis", style=PLACEHOLDER_STYLE)
                if pu_info:
                    content = _create_single_sut_analysis_table(pu_info)
                cols.append(
                    dbc.Col(
                        [
                            html.Div(
                                f"Análise para {pu_level} pu",
                                className="text-center py-1 mb-1",
                                style=title_style,
                            ),
                            html.Div(content),
                        ],
                        width=12,
                        md=4,
                        style=container_style,
                    )
                )  # Responsive width
            return dbc.Row(cols, className="g-2")

        def create_legend_section(exceeded, sut_data):
            """Creates the legend and observations card (Vazio)."""
            power_warn = any(exceeded[origem][pu] for origem in exceeded for pu in exceeded[origem])
            eps_warn_texts = []
            pu_map = {"1.0": "1.0 pu", "1.1": "1.1 pu", "1.2": "1.2 pu"}

            for pu, data in sut_data.items():
                if not data:
                    continue
                status = data.get("status", "")
                taps_info = data.get("taps_info", [])
                if "Sem dados de corrente/tensão" in status:
                    eps_warn_texts.append(f"Ensaio a {pu_map[pu]}: {status} (Projeto).")
                elif "Sem Taps SUT Adequados" in status or "Tensão >" in status:
                    eps_warn_texts.append(f"Ensaio a {pu_map[pu]}: {status}.")
                elif (
                    status == "OK"
                    and taps_info
                    and all(t.get("percent_limite", 0) > 100 for t in taps_info)
                ):
                    eps_warn_texts.append(
                        f"Ensaio a {pu_map[pu]}: Corrente EPS > {limite_corrente_eps}A para todos os taps."
                    )
                # Optional: Warn if any tap exceeds 100%
                # elif status == 'OK' and taps_info and any(t.get('percent_limite', 0) > 100 for t in taps_info):
                #      eps_warn_texts.append(f"Ensaio a {pu_map[pu]}: Corrente EPS > {limite_corrente_eps}A para alguns taps.")

            power_warn_texts = []
            if power_warn:
                for pu in ["1.0 pu", "1.1 pu", "1.2 pu"]:
                    # Correct key access for exceeded_values dict
                    origins = [
                        o.replace("_", " ").title()
                        for o in ["projeto", "aco_m4"]
                        if exceeded[o][pu]
                    ]
                    if origins:
                        power_warn_texts.append(
                            f"Ensaio a {pu}: Potência DUT > {limite_potencia_dut} kVA em {', '.join(origins)}."
                        )

            items = []
            all_warnings = power_warn_texts + eps_warn_texts
            if all_warnings:
                items.append(
                    html.Div(
                        [
                            html.Strong(
                                "Observações Importantes:", style={"color": COLORS["danger"]}
                            ),
                            html.Ul(
                                [
                                    html.Li(text, style={"color": COLORS["danger"]})
                                    for text in all_warnings
                                ],
                                style={"paddingLeft": "20px", "marginTop": "5px"},
                            ),
                        ],
                        style={"fontSize": "0.75rem", "marginBottom": "0.5rem"},
                    )
                )
                items.append(html.Hr(style={"borderColor": COLORS["border"], "margin": "0.5rem 0"}))

            # Cor do texto da legenda
            legend_style = {
                "fontSize": "0.8rem",
                "marginBottom": "0.5rem",
                "color": "inherit",
                "padding": "4px",
                "border": f"1px solid {COLORS['border_light']}",
                "borderRadius": "4px",
                "backgroundColor": COLORS["background_faint"],
            }
            span_style = {
                "display": "inline-block",
                "width": "12px",
                "height": "12px",
                "marginRight": "5px",
                "border": f"1px solid {COLORS['border']}",
                "verticalAlign": "middle",
            }
            legend_list = [
                html.Div(
                    [
                        html.Span(
                            style={**span_style, "backgroundColor": CONFIG_COLORS["danger_bg"]}
                        ),
                        html.Span(f"Potência DUT > {limite_potencia_dut} kVA"),
                    ],
                    style=legend_style,
                ),
                html.Div(
                    [
                        html.Span(
                            style={**span_style, "backgroundColor": CONFIG_COLORS["ok_bg_faint"]}
                        ),
                        html.Span(f"Corrente EPS < 50% ({limite_corrente_eps}A)"),
                    ],
                    style=legend_style,
                ),
                html.Div(
                    [
                        html.Span(
                            style={
                                **span_style,
                                "backgroundColor": CONFIG_COLORS["warning_bg_faint"],
                            }
                        ),
                        html.Span("Corrente EPS 50-85% Limite"),
                    ],
                    style=legend_style,
                ),
                html.Div(
                    [
                        html.Span(
                            style={
                                **span_style,
                                "backgroundColor": CONFIG_COLORS["warning_high_bg_faint"],
                            }
                        ),
                        html.Span("Corrente EPS 85-100% Limite"),
                    ],
                    style=legend_style,
                ),
                html.Div(
                    [
                        html.Span(
                            style={**span_style, "backgroundColor": CONFIG_COLORS["danger_bg"]}
                        ),
                        html.Span("Corrente EPS > 100% Limite"),
                    ],
                    style=legend_style,
                ),
            ]

            # Arrange legend items more compactly
            items.append(
                dbc.Row(
                    [
                        dbc.Col(legend_list[0], width=12, lg=4),
                        dbc.Col(legend_list[1], width=12, lg=4),
                        dbc.Col(legend_list[2], width=12, lg=4),
                        dbc.Col(legend_list[3], width=12, lg=4),
                        dbc.Col(legend_list[4], width=12, lg=4),
                    ],
                    className="g-2",
                )
            )

            return dbc.Card(
                [
                    dbc.CardHeader(
                        html.H6(
                            "LEGENDA E OBSERVAÇÕES",
                            className="text-center m-0",
                            style=CARD_HEADER_STYLE,
                        ),
                        style=COMPONENTS["card_header"],
                    ),
                    dbc.CardBody(
                        html.Div(items),
                        style={
                            **COMPONENTS["card_body"],
                            "backgroundColor": COLORS["background_card"],
                        },
                    ),
                ],
                style=COMPONENTS["card"],
            )

        # --- End of Layout Helpers (Vazio) ---

        # --- Generate Final Content (Vazio) ---
        parametros_gerais_content = create_general_parameters_table(
            resultados_projeto, resultados_aco_m4
        )
        tabela_resultados_dut_content, valores_excedidos = create_voltage_level_table(
            resultados_projeto, resultados_aco_m4
        )
        layout_analise_sut_content = create_sut_analysis_layout(sut_analysis_data)
        legenda_observacoes_content = create_legend_section(valores_excedidos, sut_analysis_data)
        dut_voltage_results_content = html.Div(
            tabela_resultados_dut_content, style=TABLE_WRAPPER_STYLE
        )

        # --- Update MCP (Vazio) ---
        # Prepare the new data to be stored
        new_data = {
            "resultados_aco_m4": resultados_aco_m4,
            "resultados_projeto": resultados_projeto,
            "perdas_vazio_kw": perdas_vazio,
            "peso_nucleo": peso_nucleo,
            "corrente_excitacao": corrente_excitacao_percentual,
            "inducao": inducao,
            "corrente_exc_1_1": corrente_exc_1_1_input,
            "corrente_exc_1_2": corrente_exc_1_2_input,
            "sut_analysis_data": sut_analysis_data,
        }

        # Adicionar os inputs específicos para perdas em vazio conforme solicitado
        inputs_perdas_vazio = {
            "perdas_vazio_kw": perdas_vazio,
            "peso_nucleo_ton": peso_nucleo,
            "corrente_excitacao_percentual": corrente_excitacao_percentual,
            "inducao_nucleo_t": inducao,
            "corrente_excitacao_1_1pu_percentual": corrente_exc_1_1_input,
            "corrente_excitacao_1_2pu_percentual": corrente_exc_1_2_input,
        }

        # Initialize the store data if it's None
        store_para_salvar = current_losses_store_data if isinstance(current_losses_store_data, dict) else {}

        # Initialize the resultados_perdas_vazio section if it doesn't exist or não é um dicionário
        if "resultados_perdas_vazio" not in store_para_salvar or not isinstance(store_para_salvar["resultados_perdas_vazio"], dict):
            log.warning("Seção 'resultados_perdas_vazio' não existe ou não é um dicionário. Inicializando como dicionário vazio.")
            store_para_salvar["resultados_perdas_vazio"] = {}

        # Initialize the inputs_perdas_vazio section if it doesn't exist
        if "inputs_perdas_vazio" not in store_para_salvar or not isinstance(store_para_salvar["inputs_perdas_vazio"], dict):
            log.warning("Seção 'inputs_perdas_vazio' não existe ou não é um dicionário. Inicializando como dicionário vazio.")
            store_para_salvar["inputs_perdas_vazio"] = {}

        # Update the resultados_perdas_vazio section with the new data
        store_para_salvar["resultados_perdas_vazio"].update(new_data)

        # Update the inputs_perdas_vazio section with the inputs data
        store_para_salvar["inputs_perdas_vazio"].update(inputs_perdas_vazio)

        store_para_salvar["timestamp_vazio"] = datetime.datetime.now().isoformat()

        # Log para debug
        log.info(f"[LOSSES VAZIO] Dados atualizados em resultados_perdas_vazio: {store_para_salvar['resultados_perdas_vazio'].keys()}")
        log.info(f"[LOSSES VAZIO] Valor de perdas_vazio_kw: {store_para_salvar['resultados_perdas_vazio'].get('perdas_vazio_kw')}")

        # Validar os dados antes de armazenar no MCP
        validation_rules = {
            "perdas_vazio_kw": {"required": True, "positive": True, "label": "Perdas em Vazio"},
            "peso_nucleo": {"required": True, "positive": True, "label": "Peso do Núcleo"},
            "corrente_excitacao": {
                "required": True,
                "positive": True,
                "label": "Corrente de Excitação",
            },
            "inducao": {"required": True, "positive": True, "label": "Indução"},
        }

        validation_errors = validate_dict_inputs(new_data, validation_rules)
        if validation_errors:
            log.warning(f"Validação de dados de perdas em vazio falhou: {validation_errors}")
            # Continua mesmo com erros, mas loga os problemas

        # Serializar os dados antes de armazenar no MCP
        serializable_data = convert_numpy_types(store_para_salvar, debug_path="losses_vazio_update")

        # Armazenar no MCP
        app.mcp.set_data("losses-store", serializable_data)
        log.critical(f"[LOSSES CALC VAZIO] losses-store atualizado com: {serializable_data.get('resultados_perdas_vazio')}")

        # Verificar se os dados foram armazenados corretamente
        verification_data = app.mcp.get_data("losses-store")
        if verification_data and "resultados_perdas_vazio" in verification_data and isinstance(verification_data["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in verification_data["resultados_perdas_vazio"]:
            log.info(f"[LOSSES CALC VAZIO] Verificação: dados armazenados corretamente no MCP. perdas_vazio_kw = {verification_data['resultados_perdas_vazio'].get('perdas_vazio_kw')}")
        else:
            log.error(f"[LOSSES CALC VAZIO] Verificação: dados NÃO foram armazenados corretamente no MCP. verification_data = {verification_data}")

        # Retornar os dados para o store (para manter compatibilidade)
        final_data = serializable_data

        return (
            parametros_gerais_content,
            dut_voltage_results_content,
            layout_analise_sut_content,
            legenda_observacoes_content,
            final_data,
        )

    except ValueError as e:
        log.error(f"ValueError in handle_perdas_vazio: {e}")
        error_msg = f"Erro: Verifique os inputs numéricos. Detalhe: {str(e)}"
        error_div = html.Div(error_msg, style=ERROR_STYLE)
        return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update
    except Exception as e:
        log.exception(f"Exception in handle_perdas_vazio: {e}")
        error_msg = f"Erro inesperado no cálculo de perdas em vazio: {str(e)}"
        error_div = html.Div(error_msg, style=ERROR_STYLE)
        return error_div, initial_dut_volt, initial_sut, initial_legend_obs, no_update


# --- Capacitor Bank Suggestion Helper Functions (Unchanged from previous version) ---
def generate_q_combinations(num_switches=5):
    """Generates all non-empty combinations of Q switch indices (1-based)."""
    q_indices = list(range(1, num_switches + 1))
    combinations = []
    for i in range(1, num_switches + 1):
        combinations.extend(itertools.combinations(q_indices, i))
    return [list(comb) for comb in combinations]


def calculate_q_combination_power(q_combination, available_caps):
    """Calculates the total MVAr for a given Q combination across available capacitors."""
    total_power = 0
    # Assuming Q_SWITCH_POWERS["generic_cp"] holds the power steps [Q1, Q2, Q3, Q4, Q5] in MVAr
    power_steps = Q_SWITCH_POWERS.get("generic_cp")
    if not power_steps or len(power_steps) != 5:
        log.error("Generic Q switch power profile is missing or invalid.")
        return 0

    power_per_cap = sum(power_steps[q - 1] for q in q_combination)
    total_power = power_per_cap * len(available_caps)  # Sum power across all available units
    return total_power


def select_target_bank_voltage(max_test_voltage_kv):
    """Selects the target capacitor bank voltage level based on max test voltage."""
    # Use voltages where caps exist
    cap_bank_voltages_num = sorted([float(v) for v in CAPACITORS_BY_VOLTAGE.keys()])
    target_v_cf = None
    target_v_sf = None

    # Selection COM FATOR (V_test > V_bank * 1.1)
    for v_bank in cap_bank_voltages_num:
        if max_test_voltage_kv <= (v_bank * 1.1) + epsilon:
            target_v_cf = v_bank
            break
    # If no suitable voltage found, use the highest available
    if target_v_cf is None and cap_bank_voltages_num:
        target_v_cf = cap_bank_voltages_num[-1]
        log.warning(
            f"Max test voltage {max_test_voltage_kv:.2f}kV exceeds 110% of highest bank ({cap_bank_voltages_num[-1]}kV). Using highest bank."
        )

    # Selection SEM FATOR (V_test <= V_bank)
    for v_bank in cap_bank_voltages_num:
        if max_test_voltage_kv <= v_bank + epsilon:
            target_v_sf = v_bank
            break
    if target_v_sf is None and cap_bank_voltages_num:
        target_v_sf = cap_bank_voltages_num[-1]
        log.warning(
            f"Max test voltage {max_test_voltage_kv:.2f}kV exceeds highest bank ({cap_bank_voltages_num[-1]}kV). Using highest bank for S/F."
        )

    # Return as strings for dictionary keys
    target_v_cf_str = str(target_v_cf) if target_v_cf is not None else None
    target_v_sf_str = str(target_v_sf) if target_v_sf is not None else None

    return target_v_cf_str, target_v_sf_str


def get_cs_configuration(target_bank_voltage_key, use_group1_only, circuit_type):
    """Determines the CS switch configuration string."""
    if target_bank_voltage_key is None:
        return "N/A (Tensão alvo inválida)"

    cs_switch_dict = (
        CS_SWITCHES_BY_VOLTAGE_TRI if circuit_type == "Trifásico" else CS_SWITCHES_BY_VOLTAGE_MONO
    )
    # Ensure lookup key exactly matches the dictionary keys
    available_switches = cs_switch_dict.get(str(target_bank_voltage_key))  # Ensure string key

    if not available_switches:
        log.warning(
            f"No CS switches found for key '{target_bank_voltage_key}' (Type: {circuit_type}). Available keys: {list(cs_switch_dict.keys())}"
        )
        return f"N/A (Sem chaves CS para {target_bank_voltage_key}kV)"

    cs_config_list = []
    for switch_name in available_switches:
        # Logic from C# GetCsConfiguration: Skip group 2 switches if use_group1_only is True for Trifásico
        # Assuming Group 1 switches end in '1' (CSxA1 etc.) and Group 2 switches end in '2' (CSxA2 etc.)
        is_group_2_switch = len(switch_name) > 4 and switch_name.endswith("2")  # e.g., CS1A2, CS2B2

        if use_group1_only and circuit_type == "Trifásico" and is_group_2_switch:
            log.debug(
                f"Skipping Group 2 CS switch {switch_name} because use_group1_only is True (Trifásico)."
            )
            continue

        # Monophase CS selection is simpler here, include all listed switches.
        cs_config_list.append(switch_name)

    return ", ".join(sorted(cs_config_list)) if cs_config_list else "N/A"  # Sort for consistency


def find_best_q_configuration(target_bank_voltage_key, required_power_mvar, use_group1_only):
    """Finds the best Q switch combination."""
    if (
        target_bank_voltage_key is None
        or required_power_mvar is None
        or required_power_mvar <= epsilon
    ):
        return "N/A", 0.0

    # Ensure lookup key exactly matches the dictionary keys
    all_available_caps = CAPACITORS_BY_VOLTAGE.get(
        str(target_bank_voltage_key), []
    )  # Ensure string key
    if not all_available_caps:
        log.warning(
            f"No capacitors found for key '{target_bank_voltage_key}'. Available keys: {list(CAPACITORS_BY_VOLTAGE.keys())}"
        )
        return f"N/A (Sem capacitores para {target_bank_voltage_key}kV)", 0.0

    # Corrected Group Logic: Group 1 ends with '1', Group 2 ends with '2' based on CAPACITORS_BY_VOLTAGE
    if use_group1_only:
        available_caps = [cap for cap in all_available_caps if len(cap) > 4 and cap.endswith("1")]
        log.debug(f"Using Group 1 capacitors only ({target_bank_voltage_key}kV): {available_caps}")
        if not available_caps:
            log.warning(
                f"No Group 1 (ending in '1') capacitors found for {target_bank_voltage_key}kV, trying all."
            )
            available_caps = all_available_caps  # Fallback to all
    else:
        available_caps = all_available_caps
        log.debug(f"Using Group 1+2 capacitors ({target_bank_voltage_key}kV): {available_caps}")

    if not available_caps:
        return f"N/A (Sem capacitores selecionados para {target_bank_voltage_key}kV)", 0.0

    q_combinations = generate_q_combinations()
    best_combination = None
    min_power_above_req = float("inf")

    for q_comb in q_combinations:
        current_power = calculate_q_combination_power(q_comb, available_caps)
        # Need power slightly above or equal to required
        if current_power >= required_power_mvar - epsilon:  # Add tolerance
            if current_power < min_power_above_req - epsilon:  # Found a better (lower) power
                min_power_above_req = current_power
                best_combination = q_comb
            # If powers are equal (within tolerance), prefer the one with fewer switches (simpler combo)
            elif (
                abs(current_power - min_power_above_req) < epsilon
                and best_combination
                and len(q_comb) < len(best_combination)
            ):
                min_power_above_req = (
                    current_power  # Update power in case it's slightly different but within epsilon
                )
                best_combination = q_comb

    if best_combination:
        q_config_str = ", ".join(
            [f"Q{q}" for q in sorted(best_combination)]
        )  # Sort for consistency
        return (
            q_config_str,
            min_power_above_req,
        )  # Return the actual power provided by this combination
    else:
        # Calculate max possible power with all Q switches on all available caps
        max_possible_power = calculate_q_combination_power([1, 2, 3, 4, 5], available_caps)
        required_str = f"{required_power_mvar:.1f}" if required_power_mvar else "?"
        max_str = f"{max_possible_power:.1f}" if max_possible_power is not None else "?"
        log.warning(
            f"Could not find suitable Q config for {target_bank_voltage_key}kV, {required_power_mvar:.2f} MVAr. Max possible: {max_possible_power:.2f} MVAr"
        )
        return f"N/A (Req: {required_str} MVAr > Max: {max_str} MVAr)", max_possible_power


def suggest_capacitor_bank_config(max_voltage_kv, max_power_mvar, circuit_type):
    """Suggests CS and Q configuration based on max requirements."""
    log.info(
        f"Suggesting config for Max V: {max_voltage_kv:.2f} kV, Max Q Req: {max_power_mvar:.2f} MVAr, Type: {circuit_type}"
    )

    if (
        max_voltage_kv is None
        or max_voltage_kv <= epsilon
        or max_power_mvar is None
        or max_power_mvar <= epsilon
    ):
        return "N/A (Dados insuficientes)", "N/A", 0.0

    # 1. Select Target Bank Voltage (use Com Fator for lookups)
    target_v_cf_key, _ = select_target_bank_voltage(max_voltage_kv)
    if target_v_cf_key is None:
        log.error("Could not determine target bank voltage.")
        return "N/A (Erro Tensão)", "N/A", 0.0

    # 2. Determine if Group 1 is sufficient for Com Fator
    # Corrected Group Logic: Group 1 ends with '1', Group 2 ends with '2'
    group1_caps = [
        cap
        for cap in CAPACITORS_BY_VOLTAGE.get(target_v_cf_key, [])
        if len(cap) > 4 and cap.endswith("1")
    ]
    max_power_group1 = (
        calculate_q_combination_power([1, 2, 3, 4, 5], group1_caps) if group1_caps else 0
    )
    # Use tolerance when comparing power requirements
    use_group1_only = max_power_mvar <= max_power_group1 + epsilon
    log.debug(
        f"Target Voltage Key: {target_v_cf_key}, Max Power Group 1: {max_power_group1:.2f} MVAr, Required Power: {max_power_mvar:.2f} MVAr -> Use Group 1 Only: {use_group1_only}"
    )

    # 3. Get CS Configuration for Com Fator
    cs_config_str = get_cs_configuration(target_v_cf_key, use_group1_only, circuit_type)

    # 4. Get Q Configuration for Com Fator (using max_power_mvar directly)
    q_config_str, q_power_mvar_provided = find_best_q_configuration(
        target_v_cf_key, max_power_mvar, use_group1_only
    )

    return cs_config_str, q_config_str, q_power_mvar_provided


# --- *** NEW: Helper Function for Compensated SUT/EPS Current Calculation *** ---
def calculate_sut_eps_current_compensated(
    tensao_ref_dut_kv,
    corrente_ref_dut_a,
    q_power_scenario_sf_mvar,
    cap_bank_voltage_scenario_sf_kv,
    q_power_scenario_cf_mvar,
    cap_bank_voltage_scenario_cf_kv,
    transformer_type,
    V_sut_hv_tap_v,
    tensao_sut_bt_v,
    limite_corrente_eps_a,
):
    """
    Calculates the net EPS current demanded from the SUT LV side,
    considering reactive compensation from a capacitor bank for both S/F and C/F cases.

    Args:
        tensao_ref_dut_kv: DUT test voltage (kV) for the scenario.
        corrente_ref_dut_a: DUT test current (A) for the scenario.
        q_power_scenario_sf_mvar: Reactive power PROVIDED by the S/F configured cap bank (MVAr).
        cap_bank_voltage_scenario_sf_kv: NOMINAL voltage of the S/F configured cap bank (kV).
        q_power_scenario_cf_mvar: Reactive power PROVIDED by the C/F configured cap bank (MVAr).
        cap_bank_voltage_scenario_cf_kv: NOMINAL voltage of the C/F configured cap bank (kV).
        transformer_type: 'Trifásico' or 'Monofásico'.
        V_sut_hv_tap_v: SUT HV tap voltage being analyzed (Volts).
        tensao_sut_bt_v: SUT nominal LV voltage (Volts).
        limite_corrente_eps_a: EPS current limit (Amps).

    Returns:
        dict: {'corrente_eps_sf_a': sf_net_current, 'percent_limite_sf': sf_percentage,
               'corrente_eps_cf_a': cf_net_current, 'percent_limite_cf': cf_percentage}
    """

    # Basic validation
    if any(
        v is None or v <= epsilon
        for v in [tensao_ref_dut_kv, corrente_ref_dut_a, V_sut_hv_tap_v, tensao_sut_bt_v]
    ):
        log.warning(
            "Compensated current calc: Invalid base inputs (Vref, Iref, Vsut_hv, Vsut_bt). Returning uncompensated."
        )
        # Calculate uncompensated as fallback
        ratio_sut = V_sut_hv_tap_v / tensao_sut_bt_v if tensao_sut_bt_v > epsilon else 0
        I_dut_reflected = corrente_ref_dut_a * ratio_sut
        percent_limite = (
            (I_dut_reflected / limite_corrente_eps_a) * 100
            if limite_corrente_eps_a > epsilon
            else float("inf")
        )
        return {
            "corrente_eps_sf_a": I_dut_reflected,
            "percent_limite_sf": percent_limite,
            "corrente_eps_cf_a": I_dut_reflected,
            "percent_limite_cf": percent_limite,
        }

    # 1. Calculate SUT Ratio
    ratio_sut = V_sut_hv_tap_v / tensao_sut_bt_v  # V/V

    # 2. Calculate Initial Reflected Current (DUT demand on SUT LV side)
    I_dut_reflected = corrente_ref_dut_a * ratio_sut  # Amps

    # 3. Calculate Sqrt(3) Factor
    sqrt_3_factor = math.sqrt(3) if transformer_type == "Trifásico" else 1.0

    # 4. Initialize results with uncompensated values
    I_eps_sf_net = I_dut_reflected
    I_eps_cf_net = I_dut_reflected

    # 5. Calculate S/F compensation
    sf_compensation_valid = (
        q_power_scenario_sf_mvar is not None
        and q_power_scenario_sf_mvar > epsilon
        and cap_bank_voltage_scenario_sf_kv is not None
        and cap_bank_voltage_scenario_sf_kv > epsilon
    )

    if sf_compensation_valid:
        try:
            # Calculate Corrected Reactive Power for S/F
            Cap_Correct_factor_sf = (
                0.25
                if cap_bank_voltage_scenario_sf_kv in [13.8, 23.9]
                else 0.75
                if cap_bank_voltage_scenario_sf_kv in [41.4, 71.7]
                else 1.0
            )
            q_denominator_sf = (
                tensao_ref_dut_kv / cap_bank_voltage_scenario_sf_kv
            ) ** 2 * Cap_Correct_factor_sf
            pteste_mvar_corrected_sf = (
                q_power_scenario_sf_mvar * q_denominator_sf if q_denominator_sf > epsilon else 0
            )

            # Calculate Capacitive Current for S/F
            I_cap_base_sf = (pteste_mvar_corrected_sf * 1000.0) / (
                tensao_ref_dut_kv * sqrt_3_factor
            )
            I_cap_adjustment_sf = I_cap_base_sf * ratio_sut

            # Calculate Net EPS Current for S/F
            I_eps_sf_net = I_dut_reflected - I_cap_adjustment_sf

            log.debug(
                f"S/F Calc: Tap={V_sut_hv_tap_v/1000:.1f}kV, Q_prov={q_power_scenario_sf_mvar:.2f}MVAr @ {cap_bank_voltage_scenario_sf_kv:.1f}kV"
            )
            log.debug(
                f"  S/F: Factor={Cap_Correct_factor_sf}, Q_corr={pteste_mvar_corrected_sf:.2f}MVAr, I_cap_adj={I_cap_adjustment_sf:.1f}A, I_net={I_eps_sf_net:.1f}A"
            )
        except Exception as e:
            log.error(f"S/F current calc error: {e}")
            # Keep default uncompensated value

    # 6. Calculate C/F compensation
    cf_compensation_valid = (
        q_power_scenario_cf_mvar is not None
        and q_power_scenario_cf_mvar > epsilon
        and cap_bank_voltage_scenario_cf_kv is not None
        and cap_bank_voltage_scenario_cf_kv > epsilon
    )

    if cf_compensation_valid:
        try:
            # Calculate Corrected Reactive Power for C/F
            Cap_Correct_factor_cf = (
                1.0
                if cap_bank_voltage_scenario_cf_kv in [13.8, 23.9]
                else 1.0
                if cap_bank_voltage_scenario_cf_kv in [41.4, 71.7]
                else 1.0
            )
            q_denominator_cf = (
                tensao_ref_dut_kv / cap_bank_voltage_scenario_cf_kv
            ) ** 2 * Cap_Correct_factor_cf
            pteste_mvar_corrected_cf = (
                q_power_scenario_cf_mvar * q_denominator_cf if q_denominator_cf > epsilon else 0
            )

            # Calculate Capacitive Current for C/F
            I_cap_base_cf = (pteste_mvar_corrected_cf * 1000.0) / (
                tensao_ref_dut_kv * sqrt_3_factor
            )
            I_cap_adjustment_cf = I_cap_base_cf * ratio_sut

            # Calculate Net EPS Current for C/F
            I_eps_cf_net = I_dut_reflected - I_cap_adjustment_cf

            log.debug(
                f"C/F Calc: Tap={V_sut_hv_tap_v/1000:.1f}kV, Q_prov={q_power_scenario_cf_mvar:.2f}MVAr @ {cap_bank_voltage_scenario_cf_kv:.1f}kV"
            )
            log.debug(
                f"  C/F: Factor={Cap_Correct_factor_cf}, Q_corr={pteste_mvar_corrected_cf:.2f}MVAr, I_cap_adj={I_cap_adjustment_cf:.1f}A, I_net={I_eps_cf_net:.1f}A"
            )
        except Exception as e:
            log.error(f"C/F current calc error: {e}")
            # Keep default uncompensated value

    # 7. Calculate % Limit for both S/F and C/F
    percent_limite_sf = (
        (abs(I_eps_sf_net) / limite_corrente_eps_a) * 100
        if limite_corrente_eps_a > epsilon
        else float("inf")
    )
    if I_eps_sf_net < 0:
        percent_limite_sf = -percent_limite_sf

    percent_limite_cf = (
        (abs(I_eps_cf_net) / limite_corrente_eps_a) * 100
        if limite_corrente_eps_a > epsilon
        else float("inf")
    )
    if I_eps_cf_net < 0:
        percent_limite_cf = -percent_limite_cf

    return {
        "corrente_eps_sf_a": I_eps_sf_net,
        "percent_limite_sf": percent_limite_sf,
        "corrente_eps_cf_a": I_eps_cf_net,
        "percent_limite_cf": percent_limite_cf,
    }


# --- MODIFIED Callback Perdas em Carga ---
@dash.callback(
    [
        Output("resultados-perdas-carga", "children"),
        Output("condicoes-nominais-card-body", "children"),
        Output("losses-store", "data", allow_duplicate=True),
    ],
    [Input("calcular-perdas-carga", "n_clicks")],
    [
        State(id, "value")
        for id in [
            "perdas-carga-kw_U_nom",
            "perdas-carga-kw_U_min",
            "perdas-carga-kw_U_max",
            "temperatura-referencia",
        ]
    ] + [State("losses-store", "data")],  # Adicionado State do losses-store
    prevent_initial_call=True,
)
def losses_handle_perdas_carga(
    n_clicks,
    perdas_carga_nom_ui,
    perdas_carga_min_ui,
    perdas_carga_max_ui,
    temperatura_referencia_ui,
    current_losses_store_data  # Novo parâmetro para o State do losses-store
):
    """
    Processa os inputs de perdas em carga, atualiza o MCP, e retorna os resultados para a UI.
    """
    # Verificar se o botão foi clicado
    if n_clicks is None or n_clicks <= 0:
        raise PreventUpdate

    # Verificar se o callback foi acionado pelo botão de calcular
    if ctx.triggered_id != "calcular-perdas-carga":
        log.warning(f"[losses_handle_perdas_carga] Bloqueando gravação fantasma. Trigger: {ctx.triggered_id}")
        raise PreventUpdate

    initial_detailed_content = html.Div("Aguardando cálculo...", style=PLACEHOLDER_STYLE)
    error_div = None  # Initialize error div

    # Verificar se o MCP está disponível
    if not hasattr(app, "mcp") or app.mcp is None:
        error_div = html.Div(
            "MCP não disponível. Não é possível processar os dados.", style=ERROR_STYLE
        )
        return initial_detailed_content, error_div, no_update

    # --- Input Validation ---
    required_fields = [perdas_carga_nom_ui, perdas_carga_min_ui, perdas_carga_max_ui]
    required_transformer_fields = [
        "tipo_transformador",
        "potencia_mva",
        "tensao_at",
        "tensao_at_tap_maior",
        "tensao_at_tap_menor",
        "impedancia",
        "impedancia_tap_maior",
        "impedancia_tap_menor",
        "frequencia",
        "tensao_bt",
        "corrente_nominal_bt",
    ]  # Added BT info needed for Vazio losses check

    if any(field is None or field == "" for field in required_fields):
        error_div = html.Div(
            "Por favor, preencha todos os campos de perdas em carga.", style=ERROR_STYLE
        )
        return initial_detailed_content, error_div, no_update  # Put error in nominal card

    # Obter dados do transformador do MCP
    transformer_data = app.mcp.get_data("transformer-inputs-store")
    if not transformer_data or any(
        transformer_data.get(field) is None or transformer_data.get(field) == ""
        for field in required_transformer_fields
    ):
        error_div = html.Div(
            "Dados incompletos do transformador. Verifique os dados básicos.", style=ERROR_STYLE
        )
        return initial_detailed_content, error_div, no_update

    # Obter dados de perdas existentes do MCP
    losses_data = app.mcp.get_data("losses-store")

    # Verificação mais robusta dos dados de perdas em vazio
    if not losses_data:
        log.error("[LOSSES CARGA] Dados de perdas não encontrados no MCP.")
        error_div = html.Div(
            "Dados de perdas não encontrados. Calcule as perdas em vazio primeiro na aba 'Perdas em Vazio'.",
            style=ERROR_STYLE,
        )
        return initial_detailed_content, error_div, no_update

    # Verificar se a seção resultados_perdas_vazio existe e é um dicionário
    if "resultados_perdas_vazio" not in losses_data:
        log.error("[LOSSES CARGA] Seção 'resultados_perdas_vazio' não encontrada no losses_data.")
        # Verificar o conteúdo atual do losses_data para diagnóstico
        log.debug(f"[LOSSES CARGA] Conteúdo atual do losses_data: {list(losses_data.keys()) if isinstance(losses_data, dict) else type(losses_data)}")

        # Tentar recuperar dados do current_losses_store_data (parâmetro de entrada)
        if current_losses_store_data and isinstance(current_losses_store_data, dict) and "resultados_perdas_vazio" in current_losses_store_data:
            log.info("[LOSSES CARGA] Encontrados dados de perdas em vazio no current_losses_store_data. Tentando usar esses dados.")
            losses_data = current_losses_store_data
        else:
            error_div = html.Div(
                "Seção 'resultados_perdas_vazio' não encontrada. Calcule as perdas em vazio primeiro na aba 'Perdas em Vazio'.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

    if not isinstance(losses_data["resultados_perdas_vazio"], dict):
        log.error(f"[LOSSES CARGA] 'resultados_perdas_vazio' não é um dicionário. Tipo atual: {type(losses_data['resultados_perdas_vazio'])}")
        # Tentar inicializar como dicionário vazio
        losses_data["resultados_perdas_vazio"] = {}
        log.warning("[LOSSES CARGA] Inicializando 'resultados_perdas_vazio' como dicionário vazio.")

        # Verificar se há dados no current_losses_store_data
        if current_losses_store_data and isinstance(current_losses_store_data, dict) and "resultados_perdas_vazio" in current_losses_store_data and isinstance(current_losses_store_data["resultados_perdas_vazio"], dict):
            log.info("[LOSSES CARGA] Copiando dados de 'resultados_perdas_vazio' do current_losses_store_data.")
            losses_data["resultados_perdas_vazio"] = current_losses_store_data["resultados_perdas_vazio"]
        else:
            error_div = html.Div(
                "Formato inválido para 'resultados_perdas_vazio'. Recalcule as perdas em vazio na aba 'Perdas em Vazio'.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

    # Verificar se o valor de perdas_vazio_kw existe e é válido
    if "perdas_vazio_kw" not in losses_data["resultados_perdas_vazio"]:
        log.error("[LOSSES CARGA] Chave 'perdas_vazio_kw' não encontrada em 'resultados_perdas_vazio'.")
        log.debug(f"[LOSSES CARGA] Chaves disponíveis em 'resultados_perdas_vazio': {list(losses_data['resultados_perdas_vazio'].keys())}")

        # Verificar se há dados no current_losses_store_data
        if current_losses_store_data and isinstance(current_losses_store_data, dict) and "resultados_perdas_vazio" in current_losses_store_data and isinstance(current_losses_store_data["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in current_losses_store_data["resultados_perdas_vazio"]:
            log.info("[LOSSES CARGA] Copiando valor de 'perdas_vazio_kw' do current_losses_store_data.")
            losses_data["resultados_perdas_vazio"]["perdas_vazio_kw"] = current_losses_store_data["resultados_perdas_vazio"]["perdas_vazio_kw"]
        else:
            error_div = html.Div(
                "Valor de 'perdas_vazio_kw' não encontrado. Recalcule as perdas em vazio na aba 'Perdas em Vazio'.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

    if losses_data["resultados_perdas_vazio"]["perdas_vazio_kw"] is None:
        log.error("[LOSSES CARGA] Valor de 'perdas_vazio_kw' é nulo.")

        # Verificar se há dados no current_losses_store_data
        if current_losses_store_data and isinstance(current_losses_store_data, dict) and "resultados_perdas_vazio" in current_losses_store_data and isinstance(current_losses_store_data["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in current_losses_store_data["resultados_perdas_vazio"] and current_losses_store_data["resultados_perdas_vazio"]["perdas_vazio_kw"] is not None:
            log.info("[LOSSES CARGA] Usando valor de 'perdas_vazio_kw' do current_losses_store_data.")
            losses_data["resultados_perdas_vazio"]["perdas_vazio_kw"] = current_losses_store_data["resultados_perdas_vazio"]["perdas_vazio_kw"]
        else:
            error_div = html.Div(
                "Valor de 'perdas_vazio_kw' é nulo. Recalcule as perdas em vazio na aba 'Perdas em Vazio'.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

    # Log para debug
    log.info(f"[LOSSES CARGA] Valor de perdas_vazio_kw encontrado: {losses_data['resultados_perdas_vazio'].get('perdas_vazio_kw')}")

    try:
        # --- Helpers & Constants ---
        def safe_float(value, default=None):
            try:
                return float(value) if value is not None and value != "" else default
            except (ValueError, TypeError):
                return default

        def get_formatted(res_dict, key, precision=2):
            # Helper to safely format values from the results dictionary
            if res_dict and key in res_dict and res_dict[key] is not None:
                try:
                    val = float(res_dict[key])
                    if math.isinf(val):
                        return "Inf"
                    if math.isnan(val):
                        return "-"
                    return f"{val:.{precision}f}"
                except (ValueError, TypeError):
                    return str(
                        res_dict[key]
                    )  # Return original string if conversion fails (e.g., config strings)
            return "-"  # Return hyphen if key missing or value is None

        temperatura_ref = int(temperatura_referencia_ui) if temperatura_referencia_ui is not None else 75
        # Use voltage keys from CAPACITORS_BY_VOLTAGE for consistency
        cap_bank_voltages = sorted([float(v) for v in CAPACITORS_BY_VOLTAGE.keys()])
        sqrt_3 = math.sqrt(3)

        # --- Input Processing ---
        perdas_totais_nom_input = safe_float(perdas_carga_nom_ui)
        perdas_totais_min_input = safe_float(perdas_carga_min_ui)
        perdas_totais_max_input = safe_float(perdas_carga_max_ui)
        perdas_vazio_nom = safe_float(losses_data["resultados_perdas_vazio"].get("perdas_vazio_kw"))

        # Validate essential numeric inputs
        if any(
            v is None
            for v in [
                perdas_totais_nom_input,
                perdas_totais_min_input,
                perdas_totais_max_input,
                perdas_vazio_nom,
            ]
        ):
            error_div = html.Div(
                "Valores de perdas (carga e vazio) devem ser numéricos.", style=ERROR_STYLE
            )
            return initial_detailed_content, error_div, no_update
        if any(
            v is not None and v <= 0
            for v in [perdas_totais_nom_input, perdas_totais_min_input, perdas_totais_max_input]
        ):
            error_div = html.Div(
                "Valores de perdas totais em carga devem ser maiores que zero.", style=ERROR_STYLE
            )
            return initial_detailed_content, error_div, no_update
        if perdas_vazio_nom is not None and perdas_vazio_nom <= 0:
            error_div = html.Div(
                "Valor de perdas em vazio deve ser maior que zero.", style=ERROR_STYLE
            )
            return initial_detailed_content, error_div, no_update

        tipo_transformador = transformer_data.get("tipo_transformador", "Trifásico")
        potencia = safe_float(transformer_data.get("potencia_mva"))
        tensao_nominal_at = safe_float(transformer_data.get("tensao_at"))
        tensao_at_tap_maior = safe_float(transformer_data.get("tensao_at_tap_maior"))
        tensao_at_tap_menor = safe_float(transformer_data.get("tensao_at_tap_menor"))
        impedancia = safe_float(transformer_data.get("impedancia"))
        impedancia_tap_maior = safe_float(transformer_data.get("impedancia_tap_maior"))
        impedancia_tap_menor = safe_float(transformer_data.get("impedancia_tap_menor"))

        # Validate essential transformer numerics
        essential_transformer_nums = [
            potencia,
            tensao_nominal_at,
            tensao_at_tap_maior,
            tensao_at_tap_menor,
            impedancia,
            impedancia_tap_maior,
            impedancia_tap_menor,
        ]
        if any(v is None for v in essential_transformer_nums):
            missing_keys = [
                k
                for k, v in transformer_data.items()
                if k
                in [
                    "potencia_mva",
                    "tensao_at",
                    "tensao_at_tap_maior",
                    "tensao_at_tap_menor",
                    "impedancia",
                    "impedancia_tap_maior",
                    "impedancia_tap_menor",
                ]
                and v is None
            ]
            error_div = html.Div(
                f"Dados numéricos essenciais do transformador estão faltando: {', '.join(missing_keys)}.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update
        if any(v is not None and v <= epsilon for v in essential_transformer_nums):
            invalid_keys = [
                k
                for k, v in transformer_data.items()
                if k
                in [
                    "potencia_mva",
                    "tensao_at",
                    "tensao_at_tap_maior",
                    "tensao_at_tap_menor",
                    "impedancia",
                    "impedancia_tap_maior",
                    "impedancia_tap_menor",
                ]
                and (v is not None and v <= epsilon)
            ]
            error_div = html.Div(
                f"Dados essenciais do transformador devem ser maiores que zero: {', '.join(invalid_keys)}.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

        sqrt_3_factor = sqrt_3 if tipo_transformador == "Trifásico" else 1.0

        # Verificar se as correntes já estão disponíveis no transformer_data
        corrente_at_nom = safe_float(transformer_data.get("corrente_nominal_at"))
        corrente_at_max = safe_float(transformer_data.get("corrente_nominal_at_tap_maior"))
        corrente_at_min = safe_float(transformer_data.get("corrente_nominal_at_tap_menor"))

        # Log das correntes obtidas do transformer_data
        log.info(f"[losses] Correntes obtidas do transformer_data: AT Nominal={corrente_at_nom}A, AT Tap Maior={corrente_at_max}A, AT Tap Menor={corrente_at_min}A")

        # Se alguma corrente não estiver disponível, calcular manualmente
        if corrente_at_nom is None or corrente_at_nom <= epsilon:
            corrente_at_nom = (
                (potencia * 1000 / (tensao_nominal_at * sqrt_3_factor))
                if tensao_nominal_at > epsilon
                else 0
            )
            log.info(f"[losses] Corrente AT Nominal calculada manualmente: {corrente_at_nom}A (Fórmula: {potencia}*1000/({tensao_nominal_at}*{sqrt_3_factor}))")

        if corrente_at_max is None or corrente_at_max <= epsilon:
            corrente_at_max = (
                (potencia * 1000 / (tensao_at_tap_maior * sqrt_3_factor))
                if tensao_at_tap_maior > epsilon
                else 0
            )
            log.info(f"[losses] Corrente AT Tap Maior calculada manualmente: {corrente_at_max}A (Fórmula: {potencia}*1000/({tensao_at_tap_maior}*{sqrt_3_factor}))")

        if corrente_at_min is None or corrente_at_min <= epsilon:
            corrente_at_min = (
                (potencia * 1000 / (tensao_at_tap_menor * sqrt_3_factor))
                if tensao_at_tap_menor > epsilon
                else 0
            )
            log.info(f"[losses] Corrente AT Tap Menor calculada manualmente: {corrente_at_min}A (Fórmula: {potencia}*1000/({tensao_at_tap_menor}*{sqrt_3_factor}))")

        # Log das correntes finais que serão utilizadas
        log.info(f"[losses] Correntes finais utilizadas: AT Nominal={corrente_at_nom}A, AT Tap Maior={corrente_at_max}A, AT Tap Menor={corrente_at_min}A")

        if any(v <= epsilon for v in [corrente_at_nom, corrente_at_max, corrente_at_min]):
            error_div = html.Div(
                "Falha ao calcular correntes nominais AT (resultado zero ou negativo). Verifique tensões e potência.",
                style=ERROR_STYLE,
            )
            return initial_detailed_content, error_div, no_update

        # --- Capacitor Bank Calculation Function (For individual scenarios) ---
        def calculate_cap_bank(voltage, power):
            """Calculates capacitor bank voltage and power requirements.
            Returns tuple: (V_bank_cf, Q_bank_cf, V_bank_sf, Q_bank_sf)
            cf = Com Fator (selected based on V_test > V_bank * 1.1)
            sf = Sem Fator (selected based on V_test <= V_bank)
            """
            if voltage is None or power is None or voltage <= epsilon or power <= epsilon:
                return None, None, None, None
            try:
                voltage_f = float(voltage)
                power_f = float(power)  # Power is expected in MVA for this calc

                local_cap_bank_voltages = cap_bank_voltages  # Use globally defined sorted list

                if not local_cap_bank_voltages:  # Check if list is empty
                    log.error("Lista de tensões de banco de capacitores está vazia.")
                    return None, None, None, None

                # Selection COM FATOR (Find smallest bank V where V_test > V_bank * 1.1)
                cap_bank_voltage_com_fator = next(
                    (v for v in local_cap_bank_voltages if voltage_f <= (v * 1.1) + 1e-6),
                    local_cap_bank_voltages[-1],
                )

                # Selection SEM FATOR (Find smallest bank V where V_test <= V_bank)
                cap_bank_voltage_sem_fator = next(
                    (v for v in local_cap_bank_voltages if voltage_f <= v + 1e-6),
                    local_cap_bank_voltages[-1],
                )

                # Definir o fator de correção com base na tensão do banco
                def get_cap_correct_factor(bank_voltage):
                    # Alterado para sempre retornar 1.0, independentemente da tensão do banco
                    return 1.0

                pot_cap_bank_com_fator = None
                if cap_bank_voltage_com_fator is not None and cap_bank_voltage_com_fator > epsilon:
                    # Aplicar o mesmo fator de correção para C/F
                    Cap_Correct_factor_cf = get_cap_correct_factor(cap_bank_voltage_com_fator)
                    q_denominator_cf = (
                        voltage_f / cap_bank_voltage_com_fator
                    ) ** 2 * Cap_Correct_factor_cf
                    pot_cap_bank_com_fator = (
                        power_f / q_denominator_cf if q_denominator_cf > epsilon else float("inf")
                    )

                pot_cap_bank_sem_fator = None
                if cap_bank_voltage_sem_fator is not None and cap_bank_voltage_sem_fator > epsilon:
                    Cap_Correct_factor_sf = get_cap_correct_factor(cap_bank_voltage_sem_fator)
                    q_denominator_sf = (
                        voltage_f / cap_bank_voltage_sem_fator
                    ) ** 2 * Cap_Correct_factor_sf
                    pot_cap_bank_sem_fator = (
                        power_f / q_denominator_sf if q_denominator_sf > epsilon else float("inf")
                    )

                return (
                    cap_bank_voltage_com_fator,
                    pot_cap_bank_com_fator,
                    cap_bank_voltage_sem_fator,
                    pot_cap_bank_sem_fator,
                )
            except (ValueError, TypeError, ZeroDivisionError) as e:
                log.error(f"Error in calculate_cap_bank(V={voltage}, P={power}): {e}")
                return None, None, None, None

        # --- Main Calculation Loop ---
        cenarios = [
            (tensao_nominal_at, corrente_at_nom, impedancia, perdas_totais_nom_input, "Nominal"),
            (
                tensao_at_tap_menor,
                corrente_at_min,
                impedancia_tap_menor,
                perdas_totais_min_input,
                "Menor",
            ),
            (
                tensao_at_tap_maior,
                corrente_at_max,
                impedancia_tap_maior,
                perdas_totais_max_input,
                "Maior",
            ),
        ]
        resultados = []
        calculation_error = False

        # Variables to track maximums for overall config suggestion
        max_test_voltage_kv_overall = 0.0
        max_test_power_mva_overall = 0.0
        max_test_power_mvar_overall_required = 0.0  # Track max *required* reactive power

        for i, (tensao, corrente, imp, perdas_totais, tap_label) in enumerate(cenarios):
            res_dict = {"Tap": tap_label, "Tensão": tensao, "Corrente": corrente, "Vcc (%)": imp}

            vcc_percent = imp
            # Calculate Vcc in kV
            vcc = (tensao / 100.0) * vcc_percent if tensao > 0 else 0.0
            res_dict["Vcc (kV)"] = vcc

            pnominal = tensao * corrente * sqrt_3_factor  # kVA
            res_dict["Pnominal (kVA)"] = pnominal

            res_dict["Perdas totais (kW)"] = perdas_totais
            perdas_carga_sem_vazio = perdas_totais - perdas_vazio_nom
            if perdas_carga_sem_vazio <= epsilon:
                error_msg = f"Perdas em carga ({perdas_carga_sem_vazio:.2f} kW) no Tap {tap_label} são inválidas (não positivas). Verifique as perdas totais ({perdas_totais:.2f}) e em vazio ({perdas_vazio_nom:.2f})."
                log.error(error_msg)
                error_div = html.Div(error_msg, style=ERROR_STYLE)
                calculation_error = True
                break  # Stop calculation loop

            res_dict["Perdas Carga Sem Vazio (kW)"] = perdas_carga_sem_vazio

            # Calculate cold losses (at 25°C) from reference temperature
            temp_factor = (
                (235.0 + 25.0) / (235.0 + float(temperatura_ref))
                if (235.0 + float(temperatura_ref)) > epsilon
                else 1.0
            )
            perdas_cc_a_frio = perdas_carga_sem_vazio * temp_factor
            if perdas_cc_a_frio <= epsilon:
                error_msg = f"Cálculo de Perdas CC a frio ({perdas_cc_a_frio:.2f} kW) no Tap {tap_label} resultou em valor inválido."
                log.error(error_msg)
                error_div = html.Div(error_msg, style=ERROR_STYLE)
                calculation_error = True
                break
            res_dict["Perdas a Frio (25°C) (kW)"] = perdas_cc_a_frio

            # Calculate "Frio" (Cold Energization - Total Losses) test parameters
            frio_ratio_sqrt = (
                np.sqrt(perdas_totais / perdas_cc_a_frio) if perdas_cc_a_frio > epsilon else 0
            )
            tensao_frio = frio_ratio_sqrt * vcc
            corrente_frio = frio_ratio_sqrt * corrente
            pteste_frio_kva = tensao_frio * corrente_frio * sqrt_3_factor  # kVA
            pteste_frio_mva = pteste_frio_kva / 1000.0  # MVA
            potencia_ativa_eps_frio_kw = perdas_totais  # Total losses for cold energization
            # Calculate reactive power Q = sqrt(S^2 - P^2)
            pteste_frio_mvar = (
                math.sqrt(max(0, pteste_frio_kva**2 - potencia_ativa_eps_frio_kw**2)) / 1000.0
                if pteste_frio_kva >= potencia_ativa_eps_frio_kw
                else 0
            )

            res_dict.update(
                {
                    "Tensão frio (kV)": tensao_frio,
                    "Corrente frio (A)": corrente_frio,
                    "Pteste frio (MVA)": pteste_frio_mva,
                    "Potencia Ativa EPS Frio (kW)": potencia_ativa_eps_frio_kw,
                    "Pteste frio (MVAr)": pteste_frio_mvar,  # Store reactive power test requirement
                }
            )
            cap_bank_frio = calculate_cap_bank(tensao_frio, pteste_frio_mva)
            res_dict.update(
                {
                    "Cap Bank Voltage Frio Com Fator (kV)": cap_bank_frio[0],
                    "Cap Bank Power Frio Com Fator (MVAr)": cap_bank_frio[1],  # Required C/F
                    "Cap Bank Voltage Frio Sem Fator (kV)": cap_bank_frio[2],
                    "Cap Bank Power Frio Sem Fator (MVAr)": cap_bank_frio[3],  # Required S/F
                }
            )
            # Update overall maximums based on test conditions and required bank power
            max_test_voltage_kv_overall = max(max_test_voltage_kv_overall, tensao_frio or 0)
            max_test_power_mva_overall = max(max_test_power_mva_overall, pteste_frio_mva or 0)
            if cap_bank_frio[1] is not None and not math.isinf(cap_bank_frio[1]):  # Required C/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_frio[1]
                )
            if cap_bank_frio[3] is not None and not math.isinf(cap_bank_frio[3]):  # Required S/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_frio[3]
                )

            # Calculate "Quente" (Hot Condition - Load Losses at Tref) test parameters
            quente_ratio_sqrt = (
                np.sqrt(perdas_carga_sem_vazio / perdas_cc_a_frio)
                if perdas_cc_a_frio > epsilon
                else 0
            )
            tensao_quente = quente_ratio_sqrt * vcc
            corrente_quente = quente_ratio_sqrt * corrente
            pteste_quente_kva = tensao_quente * corrente_quente * sqrt_3_factor  # kVA
            pteste_quente_mva = pteste_quente_kva / 1000.0  # MVA
            potencia_ativa_eps_quente_kw = (
                perdas_carga_sem_vazio  # Just the load losses at Tref for this test's active power
            )
            pteste_quente_mvar = (
                math.sqrt(max(0, pteste_quente_kva**2 - potencia_ativa_eps_quente_kw**2))
                / 1000.0
                if pteste_quente_kva >= potencia_ativa_eps_quente_kw
                else 0
            )

            res_dict.update(
                {
                    "Tensão quente (kV)": tensao_quente,
                    "Corrente quente (A)": corrente_quente,
                    "Pteste quente (MVA)": pteste_quente_mva,
                    "Potencia Ativa Quente (kW)": potencia_ativa_eps_quente_kw,  # Corrected active power
                    "Pteste quente (MVAr)": pteste_quente_mvar,  # Store reactive power test requirement
                }
            )
            cap_bank_quente = calculate_cap_bank(tensao_quente, pteste_quente_mva)
            res_dict.update(
                {
                    "Cap Bank Voltage Quente Com Fator (kV)": cap_bank_quente[0],
                    "Cap Bank Power Quente Com Fator (MVAr)": cap_bank_quente[1],  # Required C/F
                    "Cap Bank Voltage Quente Sem Fator (kV)": cap_bank_quente[2],
                    "Cap Bank Power Quente Sem Fator (MVAr)": cap_bank_quente[3],  # Required S/F
                }
            )
            # Update overall maximums
            max_test_voltage_kv_overall = max(max_test_voltage_kv_overall, tensao_quente or 0)
            max_test_power_mva_overall = max(max_test_power_mva_overall, pteste_quente_mva or 0)
            if cap_bank_quente[1] is not None and not math.isinf(
                cap_bank_quente[1]
            ):  # Required C/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_quente[1]
                )
            if cap_bank_quente[3] is not None and not math.isinf(
                cap_bank_quente[3]
            ):  # Required S/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_quente[3]
                )

            # Calculate 25°C condition test parameters (using Vcc and I nominal for this tap)
            tensao_25c = vcc  # Vcc is the test voltage
            corrente_25c = corrente  # Nominal current for this tap
            pteste_25c_kva = tensao_25c * corrente_25c * sqrt_3_factor  # kVA
            pteste_25c_mva = pteste_25c_kva / 1000.0  # MVA
            potencia_ativa_eps_25c_kw = perdas_cc_a_frio  # Just the cold losses
            pteste_25c_mvar = (
                math.sqrt(max(0, pteste_25c_kva**2 - potencia_ativa_eps_25c_kw**2)) / 1000.0
                if pteste_25c_kva >= potencia_ativa_eps_25c_kw
                else 0
            )

            res_dict.update(
                {
                    "Tensão 25°C (kV)": tensao_25c,
                    "Corrente 25°C (A)": corrente_25c,
                    "Pteste 25°C (MVA)": pteste_25c_mva,
                    "Potencia Ativa 25°C (kW)": potencia_ativa_eps_25c_kw,
                    "Pteste 25°C (MVAr)": pteste_25c_mvar,  # Store reactive power test requirement
                }
            )
            cap_bank_25c = calculate_cap_bank(tensao_25c, pteste_25c_mva)
            res_dict.update(
                {
                    "Cap Bank Voltage 25°C Com Fator (kV)": cap_bank_25c[0],
                    "Cap Bank Power 25°C Com Fator (MVAr)": cap_bank_25c[1],  # Required C/F
                    "Cap Bank Voltage 25°C Sem Fator (kV)": cap_bank_25c[2],
                    "Cap Bank Power 25°C Sem Fator (MVAr)": cap_bank_25c[3],  # Required S/F
                }
            )
            # Update overall maximums
            max_test_voltage_kv_overall = max(max_test_voltage_kv_overall, tensao_25c or 0)
            max_test_power_mva_overall = max(max_test_power_mva_overall, pteste_25c_mva or 0)
            if cap_bank_25c[1] is not None and not math.isinf(cap_bank_25c[1]):  # Required C/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_25c[1]
                )
            if cap_bank_25c[3] is not None and not math.isinf(cap_bank_25c[3]):  # Required S/F
                max_test_power_mvar_overall_required = max(
                    max_test_power_mvar_overall_required, cap_bank_25c[3]
                )

            resultados.append(res_dict)
        # End of main calculation loop

        if calculation_error:
            # If an error occurred inside the loop, return the error message
            return initial_detailed_content, error_div, no_update

        # --- Overload Calculations (if applicable) ---
        overload_applicable = tensao_nominal_at >= 230
        if overload_applicable:
            # Iterate through results again to add overload calcs
            for resultado in resultados:
                vcc = resultado.get("Vcc (kV)")
                corrente = resultado.get("Corrente")
                perdas_carga = resultado.get("Perdas Carga Sem Vazio (kW)")  # Base losses at Tref

                if vcc is None or corrente is None or perdas_carga is None:
                    log.warning(
                        f"Skipping overload calculation for Tap {resultado.get('Tap')} due to missing base data."
                    )
                    continue

                # --- 1.2 PU ---
                corrente_1_2 = corrente * 1.2
                tensao_1_2 = vcc * 1.2  # Simple scaling
                pteste_1_2_kva = tensao_1_2 * corrente_1_2 * sqrt_3_factor  # kVA
                pteste_1_2_mva = pteste_1_2_kva / 1000.0  # MVA
                perdas_1_2_kw = perdas_carga * (1.2**2)  # Scale base load losses (I^2R)
                potencia_ativa_eps_1_2_kw = (
                    perdas_1_2_kw  # Active power for overload is the scaled losses
                )
                pteste_1_2_mvar = (
                    math.sqrt(max(0, pteste_1_2_kva**2 - potencia_ativa_eps_1_2_kw**2)) / 1000.0
                    if pteste_1_2_kva >= potencia_ativa_eps_1_2_kw
                    else 0
                )

                resultado.update(
                    {
                        "Tensão 1.2 pu (kV)": tensao_1_2,
                        "Corrente 1.2 pu (A)": corrente_1_2,
                        "Pteste 1.2 pu (MVA)": pteste_1_2_mva,
                        "Perdas 1.2 pu (kW)": perdas_1_2_kw,
                        "Potencia Ativa 1.2 pu (kW)": potencia_ativa_eps_1_2_kw,
                        "Pteste 1.2 pu (MVAr)": pteste_1_2_mvar,  # Store reactive power test requirement
                    }
                )
                cap_bank_1_2 = calculate_cap_bank(tensao_1_2, pteste_1_2_mva)
                resultado.update(
                    {
                        "Cap Bank Voltage 1.2 pu Com Fator (kV)": cap_bank_1_2[0],
                        "Cap Bank Power 1.2 pu Com Fator (MVAr)": cap_bank_1_2[1],  # Required C/F
                        "Cap Bank Voltage 1.2 pu Sem Fator (kV)": cap_bank_1_2[2],
                        "Cap Bank Power 1.2 pu Sem Fator (MVAr)": cap_bank_1_2[3],  # Required S/F
                    }
                )
                # Update overall maximums
                max_test_voltage_kv_overall = max(max_test_voltage_kv_overall, tensao_1_2 or 0)
                max_test_power_mva_overall = max(max_test_power_mva_overall, pteste_1_2_mva or 0)
                if cap_bank_1_2[1] is not None and not math.isinf(cap_bank_1_2[1]):  # Required C/F
                    max_test_power_mvar_overall_required = max(
                        max_test_power_mvar_overall_required, cap_bank_1_2[1]
                    )
                if cap_bank_1_2[3] is not None and not math.isinf(cap_bank_1_2[3]):  # Required S/F
                    max_test_power_mvar_overall_required = max(
                        max_test_power_mvar_overall_required, cap_bank_1_2[3]
                    )

                # --- 1.4 PU ---
                corrente_1_4 = corrente * 1.4
                tensao_1_4 = vcc * 1.4  # Simple scaling
                pteste_1_4_kva = tensao_1_4 * corrente_1_4 * sqrt_3_factor  # kVA
                pteste_1_4_mva = pteste_1_4_kva / 1000.0  # MVA
                perdas_1_4_kw = perdas_carga * (1.4**2)  # Scale base load losses (I^2R)
                potencia_ativa_eps_1_4_kw = (
                    perdas_1_4_kw  # Active power for overload is the scaled losses
                )
                pteste_1_4_mvar = (
                    math.sqrt(max(0, pteste_1_4_kva**2 - potencia_ativa_eps_1_4_kw**2)) / 1000.0
                    if pteste_1_4_kva >= potencia_ativa_eps_1_4_kw
                    else 0
                )

                resultado.update(
                    {
                        "Tensão 1.4 pu (kV)": tensao_1_4,
                        "Corrente 1.4 pu (A)": corrente_1_4,
                        "Pteste 1.4 pu (MVA)": pteste_1_4_mva,
                        "Perdas 1.4 pu (kW)": perdas_1_4_kw,
                        "Potencia Ativa 1.4 pu (kW)": potencia_ativa_eps_1_4_kw,
                        "Pteste 1.4 pu (MVAr)": pteste_1_4_mvar,  # Store reactive power test requirement
                    }
                )
                cap_bank_1_4 = calculate_cap_bank(tensao_1_4, pteste_1_4_mva)
                resultado.update(
                    {
                        "Cap Bank Voltage 1.4 pu Com Fator (kV)": cap_bank_1_4[0],
                        "Cap Bank Power 1.4 pu Com Fator (MVAr)": cap_bank_1_4[1],  # Required C/F
                        "Cap Bank Voltage 1.4 pu Sem Fator (kV)": cap_bank_1_4[2],
                        "Cap Bank Power 1.4 pu Sem Fator (MVAr)": cap_bank_1_4[3],  # Required S/F
                    }
                )
                # Update overall maximums
                max_test_voltage_kv_overall = max(max_test_voltage_kv_overall, tensao_1_4 or 0)
                max_test_power_mva_overall = max(max_test_power_mva_overall, pteste_1_4_mva or 0)
                if cap_bank_1_4[1] is not None and not math.isinf(cap_bank_1_4[1]):  # Required C/F
                    max_test_power_mvar_overall_required = max(
                        max_test_power_mvar_overall_required, cap_bank_1_4[1]
                    )
                if cap_bank_1_4[3] is not None and not math.isinf(cap_bank_1_4[3]):  # Required S/F
                    max_test_power_mvar_overall_required = max(
                        max_test_power_mvar_overall_required, cap_bank_1_4[3]
                    )
        # End of overload calculations

        # --- *** Calculate Capacitor Bank Configuration for Each Scenario *** ---
        # Helper function to calculate and store capacitor bank configuration for each scenario
        def calculate_and_store_cap_bank_config(res_dict, scenario_suffix):
            """Calculate and store CS/Q config and PROVIDED power in the results dictionary."""
            # Get the S/F and C/F *required* bank voltage and power values
            cap_bank_voltage_cf_key = f"Cap Bank Voltage {scenario_suffix} Com Fator (kV)"
            cap_bank_power_cf_key = f"Cap Bank Power {scenario_suffix} Com Fator (MVAr)"
            cap_bank_voltage_sf_key = f"Cap Bank Voltage {scenario_suffix} Sem Fator (kV)"
            cap_bank_power_sf_key = f"Cap Bank Power {scenario_suffix} Sem Fator (MVAr)"

            cap_bank_voltage_cf = res_dict.get(cap_bank_voltage_cf_key)
            cap_bank_power_cf_required = res_dict.get(cap_bank_power_cf_key)  # Required power C/F
            cap_bank_voltage_sf = res_dict.get(cap_bank_voltage_sf_key)
            cap_bank_power_sf_required = res_dict.get(cap_bank_power_sf_key)  # Required power S/F

            # Initialize outputs
            config_results = {
                f"CS Config {scenario_suffix}": "N/A",
                f"CS Config {scenario_suffix} S/F": "N/A",
                f"Q Config {scenario_suffix}": "N/A",
                f"Q Config {scenario_suffix} S/F": "N/A",
                f"Q Power Provided {scenario_suffix} (MVAr)": 0.0,  # Store the PROVIDED power (C/F)
                f"Q Power Provided {scenario_suffix} S/F (MVAr)": 0.0,  # Store the PROVIDED power (S/F)
            }

            # Get available voltage keys for lookup
            available_voltages_str = list(CAPACITORS_BY_VOLTAGE.keys())
            available_voltages_flt = [float(v) for v in available_voltages_str]

            # --- Calculate C/F configuration ---
            if (
                cap_bank_voltage_cf is not None
                and cap_bank_power_cf_required is not None
                and not math.isinf(cap_bank_power_cf_required)
                and cap_bank_power_cf_required > 0
            ):
                target_v_cf_key = None
                try:
                    # Find the index of the closest float voltage
                    closest_voltage_idx_cf = min(
                        range(len(available_voltages_flt)),
                        key=lambda i: abs(available_voltages_flt[i] - cap_bank_voltage_cf),
                    )
                    target_v_cf_key = available_voltages_str[
                        closest_voltage_idx_cf
                    ]  # Get the corresponding string key
                    log.debug(
                        f"Tap {res_dict.get('Tap')}, Scen {scenario_suffix} C/F: Target V float = {cap_bank_voltage_cf:.2f}, Closest Key = {target_v_cf_key}"
                    )
                except ValueError:
                    log.error(f"Could not find closest voltage key for C/F {cap_bank_voltage_cf}")

                if target_v_cf_key:
                    # Determine if Group 1 is sufficient for C/F
                    group1_caps_cf = [
                        cap
                        for cap in CAPACITORS_BY_VOLTAGE.get(target_v_cf_key, [])
                        if len(cap) > 4 and cap.endswith("1")
                    ]
                    max_power_group1_cf = (
                        calculate_q_combination_power([1, 2, 3, 4, 5], group1_caps_cf)
                        if group1_caps_cf
                        else 0
                    )
                    use_group1_only_cf = (
                        cap_bank_power_cf_required <= max_power_group1_cf + 1e-6
                    )  # Add tolerance

                    # Get CS Configuration for C/F
                    config_results[f"CS Config {scenario_suffix}"] = get_cs_configuration(
                        target_v_cf_key, use_group1_only_cf, tipo_transformador
                    )

                    # Get Q Configuration and PROVIDED power for C/F (using the required power)
                    q_config_cf, q_power_cf_provided = find_best_q_configuration(
                        target_v_cf_key, cap_bank_power_cf_required, use_group1_only_cf
                    )
                    config_results[f"Q Config {scenario_suffix}"] = q_config_cf
                    config_results[
                        f"Q Power Provided {scenario_suffix} (MVAr)"
                    ] = q_power_cf_provided
                else:
                    config_results[f"CS Config {scenario_suffix}"] = "N/A (Erro Chave V C/F)"
                    config_results[f"Q Config {scenario_suffix}"] = "N/A"
                    config_results[f"Q Power Provided {scenario_suffix} (MVAr)"] = 0.0
            else:
                log.warning(
                    f"Dados C/F insuficientes ou inválidos para config {scenario_suffix} no Tap {res_dict.get('Tap')}. V: {cap_bank_voltage_cf}, Req P: {cap_bank_power_cf_required}"
                )
                config_results[f"CS Config {scenario_suffix}"] = "N/A (Dados C/F Insuf.)"
                config_results[f"Q Config {scenario_suffix}"] = "N/A"
                config_results[f"Q Power Provided {scenario_suffix} (MVAr)"] = 0.0

            # --- Calculate S/F configuration ---
            if (
                cap_bank_voltage_sf is not None
                and cap_bank_power_sf_required is not None
                and not math.isinf(cap_bank_power_sf_required)
                and cap_bank_power_sf_required > 0
            ):
                target_v_sf_key = None
                try:
                    # Find the index of the closest float voltage
                    closest_voltage_idx_sf = min(
                        range(len(available_voltages_flt)),
                        key=lambda i: abs(available_voltages_flt[i] - cap_bank_voltage_sf),
                    )
                    target_v_sf_key = available_voltages_str[
                        closest_voltage_idx_sf
                    ]  # Get the corresponding string key
                    log.debug(
                        f"Tap {res_dict.get('Tap')}, Scen {scenario_suffix} S/F: Target V float = {cap_bank_voltage_sf:.2f}, Closest Key = {target_v_sf_key}"
                    )
                except ValueError:
                    log.error(f"Could not find closest voltage key for S/F {cap_bank_voltage_sf}")

                if target_v_sf_key:
                    # Determine if Group 1 is sufficient for S/F
                    group1_caps_sf = [
                        cap
                        for cap in CAPACITORS_BY_VOLTAGE.get(target_v_sf_key, [])
                        if len(cap) > 4 and cap.endswith("1")
                    ]
                    max_power_group1_sf = (
                        calculate_q_combination_power([1, 2, 3, 4, 5], group1_caps_sf)
                        if group1_caps_sf
                        else 0
                    )
                    use_group1_only_sf = (
                        cap_bank_power_sf_required <= max_power_group1_sf + 1e-6
                    )  # Add tolerance

                    # Get CS Configuration for S/F
                    config_results[f"CS Config {scenario_suffix} S/F"] = get_cs_configuration(
                        target_v_sf_key, use_group1_only_sf, tipo_transformador
                    )

                    # Get Q Configuration and PROVIDED power for S/F (using the required power)
                    q_config_sf, q_power_sf_provided = find_best_q_configuration(
                        target_v_sf_key, cap_bank_power_sf_required, use_group1_only_sf
                    )
                    config_results[f"Q Config {scenario_suffix} S/F"] = q_config_sf
                    config_results[
                        f"Q Power Provided {scenario_suffix} S/F (MVAr)"
                    ] = q_power_sf_provided
                else:
                    config_results[f"CS Config {scenario_suffix} S/F"] = "N/A (Erro Chave V S/F)"
                    config_results[f"Q Config {scenario_suffix} S/F"] = "N/A"
                    config_results[f"Q Power Provided {scenario_suffix} S/F (MVAr)"] = 0.0
            else:
                log.warning(
                    f"Dados S/F insuficientes ou inválidos para config {scenario_suffix} no Tap {res_dict.get('Tap')}. V: {cap_bank_voltage_sf}, Req P: {cap_bank_power_sf_required}"
                )
                config_results[f"CS Config {scenario_suffix} S/F"] = "N/A (Dados S/F Insuf.)"
                config_results[f"Q Config {scenario_suffix} S/F"] = "N/A"
                config_results[f"Q Power Provided {scenario_suffix} S/F (MVAr)"] = 0.0

            res_dict.update(config_results)

        # Calculate configurations for each scenario and add to results
        for res in resultados:
            calculate_and_store_cap_bank_config(res, "25°C")
            calculate_and_store_cap_bank_config(res, "Frio")
            calculate_and_store_cap_bank_config(res, "Quente")
            if overload_applicable:
                calculate_and_store_cap_bank_config(res, "1.2 pu")
                calculate_and_store_cap_bank_config(res, "1.4 pu")

        # --- *** Suggest Overall Capacitor Bank Configuration *** ---
        cs_config_str, q_config_str, q_power_mvar_provided_overall = suggest_capacitor_bank_config(
            max_test_voltage_kv_overall,
            max_test_power_mvar_overall_required,  # Use max *REQUIRED* power found
            tipo_transformador,
        )

        # Format the output for the overall suggestion card (Unchanged)
        if "N/A" not in cs_config_str and "N/A" not in q_config_str:
            # Configuração do banco de capacitores calculada e armazenada no store
            target_v_cf_key, _ = select_target_bank_voltage(max_test_voltage_kv_overall)
            log.info(
                f"Configuração do banco de capacitores: Tensão={max_test_voltage_kv_overall:.1f}kV (Banco {target_v_cf_key}kV), Potência={q_power_mvar_provided_overall:.1f}MVAr"
            )
        else:
            fail_reason = (
                cs_config_str if "N/A" in cs_config_str else q_config_str
            )  # Get the reason
            log.warning(
                f"Não foi possível sugerir a configuração do banco de capacitores: {fail_reason}"
            )

        # --- Layout Generation Setup ---
        class ParameterAnalyzer:
            # (Unchanged from previous version)
            def __init__(self):
                self.type_keywords = {
                    "tensao": ["Tensão", "Vcc (kV)", "Cap Bank Voltage"],
                    "corrente": ["Corrente"],
                    "perdas": ["Perdas", "Potencia Ativa EPS"],
                    "pteste": [
                        "Pteste",
                        "Cap Bank Power",
                        "Q Power Provided",
                    ],  # Includes MVA and MVAr (required and provided)
                }
                cap_bank_voltages_num = sorted([float(v) for v in CAPACITORS_BY_VOLTAGE.keys()])
                high_voltage_threshold = (
                    95.6
                    if 95.6 in cap_bank_voltages_num
                    else (cap_bank_voltages_num[-1] if cap_bank_voltages_num else 100.0)
                )

                self.thresholds = {
                    "tensao": 95.6,  # Highlight if test voltage exceeds 95.6 kV
                    "corrente": 2000,  # Highlight if current exceeds 2000 A
                    "perdas": 1300,  # Highlight if losses exceed 1300 kW
                    "pteste_high": 93.6,  # Highlight if power exceeds 93.6 MVA/MVAr
                    "pteste_medium": 46.8,  # Highlight if power exceeds 46.8 MVA/MVAr
                    "default": float("inf"),
                }
                self.highlight_colors = {
                    "tensao": {
                        "backgroundColor": "#ffcdd2",
                        "color": "black",
                    },  # Soft red for voltage (kV)
                    "corrente": {
                        "backgroundColor": "#ffcc80",
                        "color": "black",
                    },  # Soft orange for current (A)
                    "perdas": {
                        "backgroundColor": "#d1c4e9",
                        "color": "black",
                    },  # Soft violet for losses (kW)
                    "pteste_high": {
                        "backgroundColor": "#ffb74d",
                        "color": "black",
                    },  # Deep orange for high power (MVA/MVAr)
                    "pteste_medium": {
                        "backgroundColor": "#fff59d",
                        "color": "black",
                    },  # Soft yellow for medium power (MVA/MVAr)
                }

            def get_param_type(self, param_name):
                # Exclude Cap Bank Power Req fields from highlighting
                if "Cap Bank Power" in param_name and "Req" in param_name:
                    return "default"

                # 1. Campos de Tensão (Destacados em vermelho Suave)
                if any(keyword in param_name for keyword in ["Tensão", "Cap Bank V Disp."]):
                    return "tensao"

                # 2. Campos de Corrente (Destacados em laranja Suave)
                if "Corrente" in param_name:
                    return "corrente"

                # 3. Campos de Perdas (Destacados em violeta Suave)
                if any(keyword in param_name for keyword in ["Perdas", "Potencia Ativa"]):
                    return "perdas"

                # 4. Campos de Potência de Teste (Destacados em SandyBrown ou SandyBrown+DeepPink)
                if any(
                    keyword in param_name
                    for keyword in ["Pteste", "Cap Bank Q Disp.", "Q Power Provided"]
                ):
                    return "pteste"

                # Configuration fields get the same formatting as their parent field
                if "Configuração CS" in param_name:
                    return "tensao"
                if "Configuração Q" in param_name:
                    return "pteste"

                # 5. Campos Excluídos de Formatação Condicional
                if "Vcc (%)" in param_name or "Pnominal (kVA)" in param_name:
                    return "default"

                return "default"

            def get_highlight_style(self, value, param_type):
                if value is None or param_type == "default":
                    return {}
                try:
                    v = float(value)
                    if math.isnan(v) or math.isinf(v):
                        return {}
                except (ValueError, TypeError):
                    return {}

                style = {}
                if param_type == "pteste":
                    # Two levels of highlighting for power fields
                    if v > self.thresholds["pteste_high"]:
                        style = self.highlight_colors["pteste_high"]
                    elif v > self.thresholds["pteste_medium"]:
                        style = self.highlight_colors["pteste_medium"]
                elif param_type == "tensao":
                    # Highlight voltage fields if > 95.6 kV
                    if v > self.thresholds["tensao"]:
                        style = self.highlight_colors["tensao"]
                elif param_type == "corrente":
                    # Highlight current fields if > 2000 A
                    if v > self.thresholds["corrente"]:
                        style = self.highlight_colors["corrente"]
                elif param_type == "perdas":
                    # Highlight loss fields if > 1300 kW
                    if v > self.thresholds["perdas"]:
                        style = self.highlight_colors["perdas"]
                return style

        parameter_analyzer = ParameterAnalyzer()

        def highlight_cell(value, param_type=None):
            if param_type is None:
                return {}
            return parameter_analyzer.get_highlight_style(value, param_type)

        class CapBankStatusAnalyzer:
            # (Unchanged from previous version)
            def __init__(self):
                self.potencia_critica_threshold = parameter_analyzer.thresholds["pteste_high"]
                self.potencia_alerta_threshold = parameter_analyzer.thresholds["pteste_medium"]
                self.tensao_eval_fator = (
                    1.1  # Factor to evaluate Test Voltage against Bank Voltage C/F
                )

            def validate_inputs(
                self,
                test_voltage,
                cap_bank_voltage_cf,
                power_cf_required,
                cap_bank_voltage_sf=None,
                power_sf_required=None,
                corrente=None,
                potencia_ativa=None,
            ):
                """Validates and converts inputs to float, returns dict or None"""
                try:
                    if any(
                        v is None for v in [test_voltage, cap_bank_voltage_cf, power_cf_required]
                    ):
                        log.debug(
                            f"Status input validation failed: test_v={test_voltage}, bank_v_cf={cap_bank_voltage_cf}, power_cf_req={power_cf_required}"
                        )
                        return None
                    result = {
                        "test_v": float(test_voltage),
                        "bank_v_cf": float(cap_bank_voltage_cf),
                        "power_cf_req": float(power_cf_required),
                        "bank_v_sf": None,
                        "power_sf_req": None,
                    }
                    if cap_bank_voltage_sf is not None:
                        result["bank_v_sf"] = float(cap_bank_voltage_sf)
                    if power_sf_required is not None:
                        result["power_sf_req"] = float(power_sf_required)
                    if corrente is not None:
                        result["corrente"] = float(corrente)
                    if potencia_ativa is not None:
                        result["potencia_ativa"] = float(potencia_ativa)
                    return result
                except (ValueError, TypeError):
                    log.error(
                        f"Status input conversion failed: test_v={test_voltage}, bank_v_cf={cap_bank_voltage_cf}, power_cf_req={power_cf_required}, bank_v_sf={cap_bank_voltage_sf}, power_sf_req={power_sf_required}, corrente={corrente}, potencia_ativa={potencia_ativa}"
                    )
                    return None

            def check_tensao_excedida(self, test_v, bank_v_cf):
                """Checks if Test Voltage exceeds 1.1 * Bank Voltage C/F"""
                if bank_v_cf <= epsilon:
                    return False, 0.0
                limit_v = bank_v_cf * self.tensao_eval_fator
                tensao_excedida = test_v > limit_v + 1e-6
                percent_above = ((test_v / (limit_v + epsilon)) - 1) * 100 if tensao_excedida else 0
                return tensao_excedida, percent_above

            def check_potencia_status(self, power_cf_req, power_sf_req):
                """Checks required power levels against thresholds for both C/F and S/F"""
                status = {"crit_cf": False, "alert_cf": False, "crit_sf": False, "alert_sf": False}
                if (
                    power_cf_req is not None
                    and not math.isinf(power_cf_req)
                    and not math.isnan(power_cf_req)
                ):
                    status["crit_cf"] = power_cf_req > self.potencia_critica_threshold
                    status["alert_cf"] = (
                        self.potencia_alerta_threshold
                        < power_cf_req
                        <= self.potencia_critica_threshold
                    )
                if (
                    power_sf_req is not None
                    and not math.isinf(power_sf_req)
                    and not math.isnan(power_sf_req)
                ):
                    # Check S/F only if it's relevant (different from C/F or C/F is invalid)
                    # S/F critical/alert has lower priority if C/F is already critical/alert
                    is_sf_relevant = (
                        power_cf_req is None or abs(power_sf_req - power_cf_req) > epsilon
                    )
                    if is_sf_relevant:
                        status["crit_sf"] = power_sf_req > self.potencia_critica_threshold
                        status["alert_sf"] = (
                            self.potencia_alerta_threshold
                            < power_sf_req
                            <= self.potencia_critica_threshold
                        )
                return status

            def get_status(
                self,
                test_voltage,
                cap_bank_voltage_cf,
                power_cf_required,
                cap_bank_voltage_sf=None,
                power_sf_required=None,
                corrente=None,
                potencia_ativa=None,
            ):
                """Generates the status string based on voltage, current, active power and required power checks"""
                inputs = self.validate_inputs(
                    test_voltage,
                    cap_bank_voltage_cf,
                    power_cf_required,
                    cap_bank_voltage_sf,
                    power_sf_required,
                    corrente,
                )
                if inputs is None:
                    return "N/A (Dados Status Inválidos)"

                status_parts = []
                events = 0

                # 1. Voltage Check (based on C/F bank)
                tensao_excedida, percent_above = self.check_tensao_excedida(
                    inputs["test_v"], inputs["bank_v_cf"]
                )
                if tensao_excedida:
                    bank_v_disp = f"{inputs['bank_v_cf']:.1f}kV"
                    status_parts.append(f"(V) > Limite ({percent_above:.1f}%)")
                    events += 1

                # 2. Current Check (if current > 2000A)
                if inputs["test_v"] > 0 and "corrente" in inputs:
                    corrente = inputs.get("corrente", 0)
                    if corrente > 2000:
                        status_parts.append(f"(A) > Limite ({corrente:.1f}A)")
                        events += 1

                # 3. Active Power Check (if power > 1300kW)
                if potencia_ativa is not None and potencia_ativa > 1300:
                    status_parts.append(f"(P) > Limite ({potencia_ativa:.1f}kW)")
                    events += 1

                # 3. Power Check (based on Required Power)
                potencia_status = self.check_potencia_status(
                    inputs["power_cf_req"], inputs["power_sf_req"]
                )
                pwr_disp_cf = (
                    f"{inputs['power_cf_req']:.1f}"
                    if inputs["power_cf_req"] is not None and not math.isinf(inputs["power_cf_req"])
                    else "Inf"
                )
                pwr_disp_sf = (
                    f"{inputs['power_sf_req']:.1f}"
                    if inputs["power_sf_req"] is not None and not math.isinf(inputs["power_sf_req"])
                    else "Inf"
                )

                # Prioritize critical messages
                if potencia_status["crit_cf"]:
                    status_parts.append(f"Cap Bank ↑ ({self.potencia_critica_threshold:.1f}+ MVAr)")
                    events += 1
                elif potencia_status["crit_sf"]:  # Only show S/F critical if C/F wasn't critical
                    status_parts.append(f"Cap Bank ↑ ({self.potencia_critica_threshold:.1f}+ MVAr)")
                    events += 1
                # Then alert messages (if not critical)
                elif potencia_status["alert_cf"]:
                    status_parts.append(f"Cap Bank ↑ ({self.potencia_alerta_threshold:.1f}+ MVAr)")
                    events += 1
                elif potencia_status[
                    "alert_sf"
                ]:  # Only show S/F alert if C/F wasn't alert/critical
                    status_parts.append(f"Cap Bank ↑ ({self.potencia_alerta_threshold:.1f}+ MVAr)")
                    events += 1

                # Combine messages
                if not status_parts:
                    return "OK"
                if events > 1:
                    status_parts.append(f"({events})")
                return " | ".join(status_parts)

        cap_bank_analyzer = CapBankStatusAnalyzer()

        def get_cap_bank_status(
            test_voltage,
            cap_bank_voltage_cf,
            power_cf_required,
            cap_bank_voltage_sf=None,
            power_sf_required=None,
            corrente=None,
            potencia_ativa=None,
        ):
            # Wrapper for status analyzer - uses REQUIRED power for status
            return cap_bank_analyzer.get_status(
                test_voltage,
                cap_bank_voltage_cf,
                power_cf_required,
                cap_bank_voltage_sf,
                power_sf_required,
                corrente,
                potencia_ativa,
            )

        # --- TableCellFormatter Class (IMPROVED for Config Split Cells) ---
        class TableCellFormatter:
            def __init__(self, column_widths, results_meta):
                self.column_widths = column_widths
                self.results_meta = results_meta  # Store tap/scenario info for unique IDs
                self.font_size = "0.75rem"  # Standardized font size
                self.padding = "0.3rem"
                self._unique_counter = 0  # Add a counter for absolutely unique IDs

            def _get_unique_id(self, base_id):
                """Helper to generate unique ID index part"""
                self._unique_counter += 1
                return f"{base_id}-{self._unique_counter}"

            def format_value(self, value, precision=2):
                """Formats a single numeric value or returns '-'"""
                if value is None:
                    return "-"
                if isinstance(value, (int, float)):
                    if math.isinf(value):
                        return "Inf"
                    if math.isnan(value):
                        return "-"
                    try:
                        # Format with specified precision
                        return f"{float(value):.{precision}f}"
                    except ValueError:
                        return str(value)  # Fallback
                return str(value)  # Return as string if not int/float

            def format_config_string(self, config_str, max_len=25):
                """Formats and shortens configuration strings for display IN TOOLTIPS."""
                # Tooltips can handle longer strings, just ensure it's a string
                if not config_str or not isinstance(config_str, str) or "N/A" in config_str:
                    return "N/A"
                return config_str  # Return full string for tooltip

            def get_base_style(self, table_col_index):
                """Gets base style with width for a given column index (1-based)"""
                width = self.column_widths.get(table_col_index, "auto")
                return {
                    "fontSize": self.font_size,
                    "padding": self.padding,
                    "textAlign": "center",
                    "width": width,
                    "maxWidth": width,
                    "minWidth": width,
                    "verticalAlign": "middle",
                    "color": "black",
                }

            def create_cell(
                self,
                value,
                row_idx,
                col_idx,
                apply_highlighting=False,
                param_type=None,
                param_name=None,
                precision=2,
            ):
                """Creates a table cell (Td), handling single, dual, or config (dict) values"""
                table_col_idx = col_idx + 1  # Actual table column index (1-based)
                base_style = self.get_base_style(table_col_idx)
                highlight_style = {}

                # Check if it's a split cell configuration (passed as a dict)
                is_split_cell = isinstance(value, dict) and value.get("split_cell") == True

                if is_split_cell:
                    # Get S/F and C/F values (dict: {'numeric': val, 'config': str})
                    sf_data = value.get("sf", {"numeric": None, "config": "N/A"})
                    cf_data = value.get("cf", {"numeric": None, "config": "N/A"})

                    sf_numeric_val = sf_data.get("numeric")
                    sf_config_str = sf_data.get("config", "N/A")
                    cf_numeric_val = cf_data.get("numeric")
                    cf_config_str = cf_data.get("config", "N/A")

                    # Ensure config strings are actually strings
                    sf_config_str_safe = self.format_config_string(
                        sf_config_str
                    )  # Format for tooltip
                    cf_config_str_safe = self.format_config_string(
                        cf_config_str
                    )  # Format for tooltip

                    # Format numeric values for display in cell
                    sf_numeric_text = self.format_value(sf_numeric_val, precision)
                    cf_numeric_text = self.format_value(cf_numeric_val, precision)

                    # Check if values exist for display
                    has_sf_display = sf_numeric_val is not None and sf_numeric_text != "-"
                    has_cf_display = cf_numeric_val is not None and cf_numeric_text != "-"
                    has_sf_tooltip = "N/A" not in sf_config_str_safe
                    has_cf_tooltip = "N/A" not in cf_config_str_safe

                    # Generate unique IDs for tooltips
                    # Incorporate row and col index for better uniqueness
                    base_unique_id = f"split-cell-{row_idx}-{col_idx}"
                    sf_id_str = self._get_unique_id(base_unique_id + "-sf")
                    cf_id_str = self._get_unique_id(base_unique_id + "-cf")

                    # Determine param_type for highlighting based on numeric value
                    highlight_param_type = param_type  # Use the passed param_type

                    sf_highlight_style = (
                        highlight_cell(sf_numeric_val, highlight_param_type)
                        if apply_highlighting and has_sf_display
                        else {}
                    )
                    cf_highlight_style = (
                        highlight_cell(cf_numeric_val, highlight_param_type)
                        if apply_highlighting and has_cf_display
                        else {}
                    )

                    # Create the split cell content
                    cell_content_components = []  # Store components (divs and tooltips)

                    # Check if S/F and C/F values are equal (within a small tolerance)
                    values_are_equal = False
                    configs_are_equal = False

                    # Check if this is a Cap Bank V Disp. (kV) field
                    is_cap_bank_voltage = (
                        "Cap Bank V Disp. (kV)" in param_name if param_name else False
                    )

                    # Check if this is a Cap Bank Q Disp. (MVAr) field
                    is_cap_bank_q = "Cap Bank Q Disp. (MVAr)" in param_name if param_name else False

                    # Check if numeric values are equal
                    if (
                        has_sf_display
                        and has_cf_display
                        and sf_numeric_val is not None
                        and cf_numeric_val is not None
                    ):
                        # Use a small tolerance for floating point comparison
                        tolerance = 0.001
                        values_are_equal = abs(sf_numeric_val - cf_numeric_val) < tolerance

                    # Check if config strings are equal
                    if has_sf_tooltip and has_cf_tooltip:
                        configs_are_equal = sf_config_str_safe == cf_config_str_safe

                    # Only show as a single value if:
                    # 1. Both values AND configs are equal, or
                    # 2. This is a Cap Bank V Disp. (kV) field and the values are equal, or
                    # 3. This is a Cap Bank Q Disp. (MVAr) field (always show as single value)
                    values_are_equal = (
                        (
                            values_are_equal
                            and (configs_are_equal or (not has_sf_tooltip and not has_cf_tooltip))
                        )
                        or (is_cap_bank_voltage and values_are_equal)
                        or is_cap_bank_q
                    )

                    # If values are equal, show only one value
                    if values_are_equal:
                        # Create a single cell with the value
                        single_id = self._get_unique_id(base_unique_id + "-single")

                        # Determine what to display based on the field type
                        if (
                            is_cap_bank_q
                            and has_sf_display
                            and has_cf_display
                            and sf_numeric_val is not None
                            and cf_numeric_val is not None
                        ):
                            # For Cap Bank Q Disp. (MVAr), if values are different, show both
                            if abs(sf_numeric_val - cf_numeric_val) >= 0.001:
                                single_content = [
                                    html.Span(
                                        sf_numeric_text,
                                        style={
                                            "fontSize": "0.9em",
                                            "fontWeight": "bold",
                                            "color": "black",
                                        },
                                    ),
                                    html.Sup(
                                        " S/F",
                                        style={
                                            "fontSize": "0.65em",
                                            "color": COLORS["text_muted"],
                                            "marginLeft": "2px",
                                        },
                                    ),
                                    html.Span(" / ", style={"fontSize": "0.9em", "color": "black"}),
                                    html.Span(
                                        cf_numeric_text,
                                        style={
                                            "fontSize": "0.9em",
                                            "fontWeight": "bold",
                                            "color": "black",
                                        },
                                    ),
                                    html.Sup(
                                        " C/F",
                                        style={
                                            "fontSize": "0.65em",
                                            "color": COLORS["text_muted"],
                                            "marginLeft": "2px",
                                        },
                                    ),
                                ]
                            else:
                                # Values are the same, show as S/F=C/F
                                single_content = [
                                    html.Span(
                                        sf_numeric_text,
                                        style={
                                            "fontSize": "0.9em",
                                            "fontWeight": "bold",
                                            "color": "black",
                                        },
                                    ),
                                    html.Sup(
                                        " S/F=C/F",
                                        style={
                                            "fontSize": "0.65em",
                                            "color": COLORS["text_muted"],
                                            "marginLeft": "2px",
                                        },
                                    ),
                                ]
                        else:
                            # For other fields, use the S/F value (they're the same)
                            single_content = [
                                html.Span(
                                    sf_numeric_text,
                                    style={
                                        "fontSize": "0.9em",
                                        "fontWeight": "bold",
                                        "color": "black",
                                    },
                                ),
                                html.Sup(
                                    " S/F=C/F",
                                    style={
                                        "fontSize": "0.65em",
                                        "color": COLORS["text_muted"],
                                        "marginLeft": "2px",
                                    },
                                ),
                            ]

                        # Use the S/F highlight style (they should be the same)
                        single_div = html.Div(
                            single_content,
                            id=single_id,
                            style={
                                "width": "100%",
                                "textAlign": "center",
                                "padding": "0.15rem",
                                "backgroundColor": sf_highlight_style.get(
                                    "backgroundColor", "transparent"
                                ),
                                "cursor": "help"
                                if (has_sf_tooltip or has_cf_tooltip)
                                else "default",
                            },
                        )
                        cell_content_components.append(single_div)

                        # Create a combined popover if either tooltip has content
                        if has_sf_tooltip or has_cf_tooltip:
                            combined_title = "S/F = C/F"
                            combined_content = ""

                            if has_sf_tooltip and has_cf_tooltip:
                                if sf_config_str_safe == cf_config_str_safe:
                                    combined_content = f"S/F e C/F usam a mesma configuração:\n\n{sf_config_str_safe}"
                                else:
                                    combined_content = f"Configuração S/F:\n{sf_config_str_safe}\n\nConfiguração C/F:\n{cf_config_str_safe}"
                            elif has_sf_tooltip:
                                combined_content = f"Configuração S/F:\n\n{sf_config_str_safe}"
                            elif has_cf_tooltip:
                                combined_content = f"Configuração C/F:\n\n{cf_config_str_safe}"

                            combined_popover = dbc.Popover(
                                [
                                    dbc.PopoverHeader(combined_title),
                                    dbc.PopoverBody([html.Code(combined_content)]),
                                ],
                                target=single_id,
                                trigger="hover",
                                placement="top",
                            )
                            cell_content_components.append(combined_popover)
                    else:
                        # --- Left side (S/F) ---
                        sf_content_inner = []
                        if has_sf_display:
                            sf_content_inner.append(
                                html.Span(
                                    sf_numeric_text,
                                    style={
                                        "fontSize": "0.9em",
                                        "fontWeight": "bold",
                                        "color": "black",
                                    },
                                )
                            )
                            sf_content_inner.append(
                                html.Sup(
                                    " S/F",
                                    style={
                                        "fontSize": "0.7em",
                                        "color": COLORS["text_muted"],
                                        "marginLeft": "2px",
                                    },
                                )
                            )
                        else:
                            sf_content_inner.append("-")  # Display hyphen if no numeric value

                        sf_div = html.Div(
                            sf_content_inner,
                            id=sf_id_str if has_sf_tooltip else f"sf-no-tooltip-{base_unique_id}",
                            style={
                                "width": "50%",
                                "float": "left",
                                "borderRight": f'1px solid {COLORS["border"]}',
                                "padding": "0.15rem",
                                "textAlign": "center",  # Center align the content
                                "backgroundColor": sf_highlight_style.get(
                                    "backgroundColor", "transparent"
                                ),
                                "cursor": "help" if has_sf_tooltip else "default",
                            },
                        )
                        cell_content_components.append(sf_div)

                        # Create popover for S/F only if there's a config string to show
                        if has_sf_tooltip:
                            tooltip_title = "S/F: V_teste ≤ V_banco"
                            # Usar Popover em vez de Tooltip para melhor visualização
                            sf_popover = dbc.Popover(
                                [
                                    dbc.PopoverHeader(tooltip_title),
                                    dbc.PopoverBody([html.Code(sf_config_str_safe)]),
                                ],
                                target=sf_id_str,
                                trigger="hover",
                                placement="top",
                            )
                            cell_content_components.append(sf_popover)

                        # --- Right side (C/F) ---
                        cf_content_inner = []
                        if has_cf_display:
                            cf_content_inner.append(
                                html.Span(
                                    cf_numeric_text,
                                    style={
                                        "fontSize": "0.9em",
                                        "fontWeight": "bold",
                                        "color": "black",
                                    },
                                )
                            )
                            cf_content_inner.append(
                                html.Sup(
                                    " C/F",
                                    style={
                                        "fontSize": "0.7em",
                                        "color": COLORS["text_muted"],
                                        "marginLeft": "2px",
                                    },
                                )
                            )
                        else:
                            cf_content_inner.append("-")  # Display hyphen if no numeric value

                        cf_div = html.Div(
                            cf_content_inner,
                            id=cf_id_str if has_cf_tooltip else f"cf-no-tooltip-{base_unique_id}",
                            style={
                                "width": "50%",
                                "float": "right",
                                "padding": "0.15rem",
                                "textAlign": "center",  # Center align the content
                                "backgroundColor": cf_highlight_style.get(
                                    "backgroundColor", "transparent"
                                ),
                                "cursor": "help" if has_cf_tooltip else "default",
                            },
                        )
                        cell_content_components.append(cf_div)

                    # Create popover for C/F only if there's a config string to show
                    if has_cf_tooltip:
                        tooltip_title = "C/F: V_teste > V_banco × 1.1"
                        # Usar Popover em vez de Tooltip para melhor visualização
                        cf_popover = dbc.Popover(
                            [
                                dbc.PopoverHeader(tooltip_title),
                                dbc.PopoverBody([html.Code(cf_config_str_safe)]),
                            ],
                            target=cf_id_str,
                            trigger="hover",
                            placement="top",
                        )
                        cell_content_components.append(cf_popover)

                    # Return the split cell
                    # Ensure overall cell padding is 0 to make inner divs fill it
                    cell_style = {
                        **base_style,
                        "padding": "0",  # Remove padding from TD
                        "height": "100%",
                        "overflow": "hidden",  # Ensure content doesn't overflow TD
                    }

                    # Use an inner div to clear floats and contain the components
                    # This prevents layout issues with subsequent cells/rows
                    container_div = html.Div(
                        cell_content_components, style={"overflow": "hidden", "height": "100%"}
                    )

                    return html.Td(
                        container_div, style=cell_style, className="table-value-cell split-cell"
                    )

                # Handle regular dual value [sem_fator, com_fator] (e.g., Cap Bank Voltage/Power)
                elif isinstance(value, list) and len(value) == 2:
                    sem_fator, com_fator = value
                    sem_fator_text = self.format_value(sem_fator, precision)
                    com_fator_text = self.format_value(com_fator, precision)

                    has_sf = sem_fator is not None and sem_fator_text != "-"
                    has_cf = com_fator is not None and com_fator_text != "-"

                    # Determine which value to use for highlighting (Prioritize C/F)
                    highlight_val = com_fator if has_cf else sem_fator if has_sf else None
                    if apply_highlighting and param_type is not None and highlight_val is not None:
                        highlight_style = highlight_cell(highlight_val, param_type)

                    cell_style = {**base_style, **highlight_style}
                    if "color" not in cell_style:
                        cell_style["color"] = "black"

                    # Display Logic
                    if (
                        has_sf
                        and has_cf
                        and abs(float(sem_fator or 0) - float(com_fator or 0)) > epsilon
                    ):  # Show both if different
                        return html.Td(
                            [
                                html.Span(sem_fator_text, style={"fontSize": "0.9em"}),
                                html.Sup(
                                    " S/F",
                                    style={"fontSize": "0.7em", "color": COLORS["text_muted"]},
                                ),
                                " / ",
                                html.Span(com_fator_text, style={"fontSize": "0.9em"}),
                                html.Sup(
                                    " C/F",
                                    style={"fontSize": "0.7em", "color": COLORS["text_muted"]},
                                ),
                            ],
                            style=cell_style,
                            className="table-value-cell",
                        )
                    elif has_sf:  # Show only S/F if C/F missing or same
                        return html.Td(
                            [
                                html.Span(sem_fator_text, style={"fontSize": "0.9em"}),
                                html.Sup(
                                    " S/F",
                                    style={"fontSize": "0.7em", "color": COLORS["text_muted"]},
                                ),
                            ],
                            style=cell_style,
                            className="table-value-cell",
                        )
                    elif has_cf:  # Show only C/F if S/F missing
                        return html.Td(
                            [
                                html.Span(com_fator_text, style={"fontSize": "0.9em"}),
                                html.Sup(
                                    " C/F",
                                    style={"fontSize": "0.7em", "color": COLORS["text_muted"]},
                                ),
                            ],
                            style=cell_style,
                            className="table-value-cell",
                        )
                    else:  # Display N/A if neither value exists
                        return html.Td("-", style=cell_style, className="table-value-cell")
                else:
                    # Handle single value
                    text = self.format_value(value, precision)
                    highlight_style = {}
                    if apply_highlighting and param_type is not None and param_type != "default":
                        try:
                            highlight_style = highlight_cell(
                                float(value) if value is not None else None, param_type
                            )
                        except (ValueError, TypeError):
                            pass  # Ignore highlighting if not numeric

                    cell_style = {**base_style, **highlight_style}
                    if "color" not in cell_style:
                        cell_style["color"] = "black"

                    return html.Td(text, style=cell_style, className="table-value-cell")

        # --- StatusStyler Class (Improved Styling) ---
        class StatusStyler:
            def __init__(self, column_widths):
                self.column_widths = column_widths
                self.base_style = {
                    **TABLE_STATUS_STYLE,
                    "verticalAlign": "middle",
                    "fontSize": "0.7rem",
                    "padding": "0.2rem",
                }  # Adjust padding
                # Define styles based on keywords in the status string
                self.status_styles = {
                    "(V)": {
                        "color": CONFIG_COLORS["danger_text"],
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para voltage
                    "(A)": {
                        "color": CONFIG_COLORS["danger_text"],
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para current
                    "(P)": {
                        "color": CONFIG_COLORS["danger_text"],
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para active power
                    f"{cap_bank_analyzer.potencia_critica_threshold:.1f}+": {
                        "color": CONFIG_COLORS["danger_text"],
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para critical power
                    f"{cap_bank_analyzer.potencia_alerta_threshold:.1f}+": {
                        "color": CONFIG_COLORS["warning_text"],
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para alert power
                    "eventos": {
                        "color": "#6a1b9a",
                        "backgroundColor": "transparent",
                        "fontWeight": "bold",
                    },  # Sem fundo para eventos
                    "OK": {
                        "color": CONFIG_COLORS["ok_text"],
                        "backgroundColor": "transparent",
                    },  # Green text, no background
                    "N/A": {
                        "color": COLORS["text_muted"],
                        "backgroundColor": "transparent",
                    },  # Gray text, no background
                }
                self.default_style = self.status_styles["N/A"]

            def get_style(self, status_text, col_idx):
                """Determines the style based on keywords"""
                table_col_idx = col_idx + 1  # Actual table column index
                width = self.column_widths.get(table_col_idx, "auto")
                style = {
                    **self.base_style,
                    "width": width,
                    "maxWidth": width,
                    "minWidth": width,
                    "textAlign": "center",
                }  # Center align status
                if not isinstance(status_text, str):
                    status_text = "N/A"

                applied_style = self.default_style  # Default

                # Check keywords in order of precedence
                pot_crit_key = f"{cap_bank_analyzer.potencia_critica_threshold:.1f}+"
                pot_alert_key = f"{cap_bank_analyzer.potencia_alerta_threshold:.1f}+"

                if "(V)" in status_text:
                    applied_style = self.status_styles["(V)"]
                elif "(A)" in status_text:
                    applied_style = self.status_styles["(A)"]
                elif "(P)" in status_text:
                    applied_style = self.status_styles["(P)"]
                elif pot_crit_key in status_text:
                    applied_style = self.status_styles[pot_crit_key]
                elif pot_alert_key in status_text:
                    applied_style = self.status_styles[pot_alert_key]
                elif "(" in status_text and ")" in status_text and "Inv" not in status_text:
                    applied_style = self.status_styles["eventos"]
                elif status_text == "OK":
                    applied_style = self.status_styles["OK"]
                # N/A is the default

                style.update(applied_style)
                return style

        # --- Table Generation Setup ---
        headers = ["Parâmetro"] + [f"Tap {r['Tap']}" for r in resultados]
        num_taps = len(resultados)
        param_col_width = 36  # Percentage
        tap_width_total = 100 - param_col_width
        tap_width = f"{math.floor(tap_width_total / num_taps)}%" if num_taps > 0 else "21%"
        column_widths = {0: f"{param_col_width}%"}
        for i in range(num_taps):
            column_widths[i + 1] = tap_width

        results_meta = [{"Tap": r["Tap"]} for r in resultados]
        cell_formatter = TableCellFormatter(column_widths, results_meta)
        status_styler = StatusStyler(column_widths)

        def create_table_cell(
            value,
            row_idx,
            col_idx,
            apply_highlighting,
            param_type=None,
            param_name=None,
            precision=2,
        ):
            return cell_formatter.create_cell(
                value,
                row_idx,
                col_idx,
                apply_highlighting,
                param_type,
                param_name,
                precision=precision,
            )

        def create_status_cell(value_tuple, col_idx):
            """Creates the status cell using the analyzer and styler"""
            if not isinstance(value_tuple, tuple) or len(value_tuple) < 7:
                status_text = "N/A (Dados Status Inv.)"
                status_style = status_styler.get_style(status_text, col_idx)
                return html.Td(status_text, style=status_style)

            # Unpack the tuple for the status analyzer (uses REQUIRED power)
            (
                test_voltage,
                cap_bank_voltage_cf,
                power_cf_required,
                cap_bank_voltage_sf,
                power_sf_required,
                corrente,
                potencia_ativa,
            ) = value_tuple

            status_text = get_cap_bank_status(
                test_voltage,
                cap_bank_voltage_cf,
                power_cf_required,
                cap_bank_voltage_sf,
                power_sf_required,
                corrente,
                potencia_ativa,
            )
            status_style = status_styler.get_style(status_text, col_idx)

            # Wrap text for better readability in narrow columns
            wrapped_status = html.Div(
                status_text,
                style={"whiteSpace": "normal", "wordWrap": "break-word", "lineHeight": "1.2"},
            )
            return html.Td(wrapped_status, style=status_style)

        def create_table_body(rows_data, apply_highlighting=False):
            """Creates the Tbody element, handling parameter, value, and status rows"""
            tbody_rows = []
            param_style = {
                **TABLE_PARAM_STYLE_MD,
                "width": column_widths[0],
                "verticalAlign": "middle",
                "color": "black",
                "textAlign": "left",
                "paddingLeft": "5px",
            }
            for row_idx, row_data in enumerate(rows_data):
                param_name = row_data[0]
                param_type = parameter_analyzer.get_param_type(param_name)
                cells = [html.Td(param_name, style=param_style)]

                for i, value in enumerate(row_data[1:]):
                    col_index = i  # 0-based index for the tap column
                    if param_name == "Status":
                        status_cell = create_status_cell(value, col_index)
                        cells.append(status_cell)
                    else:
                        precision = 2  # Default precision é 2 casas decimais para padronização
                        if "(kV)" in param_name or "(MVA)" in param_name or "(MVAr)" in param_name:
                            precision = 2  # Alterado de 1 para 2 casas decimais
                        elif "(A)" in param_name:
                            precision = 2  # Mantido em 2 casas decimais
                        elif "(kW)" in param_name:
                            precision = 2  # Mantido em 2 casas decimais
                        elif "Vcc (%)" in param_name:
                            precision = 2  # Alterado de 3 para 2 casas decimais
                        elif "Pnominal (kVA)" in param_name:
                            precision = 2  # Alterado de 0 para 2 casas decimais
                        elif "Q Power Provided" in param_name:
                            precision = 2  # Alterado de 1 para 2 casas decimais

                        cell = create_table_cell(
                            value,
                            row_idx,
                            col_index,
                            apply_highlighting,
                            param_type,
                            param_name,
                            precision=precision,
                        )
                        cells.append(cell)
                tbody_rows.append(html.Tr(cells))
            return html.Tbody(tbody_rows)

        # Define Table Headers and Styles
        header_cells = []
        for i, h in enumerate(headers):
            width = column_widths.get(i, "auto")
            text_align = "left" if i == 0 else "center"
            header_style = {
                **TABLE_HEADER_STYLE_MD,
                "width": width,
                "maxWidth": width,
                "minWidth": width,
                "verticalAlign": "middle",
                "textAlign": text_align,
            }
            if i == 0:
                header_style["paddingLeft"] = "5px"
            header_cells.append(html.Th(h, style=header_style))
        header_row = html.Thead(html.Tr(header_cells))
        table_style = {"tableLayout": "fixed", "width": "100%"}

        # --- Define Row Keys for Each Table Section (UPDATED for split cells) ---
        # Format for config cells: {'split_cell': True, 'sf': {'numeric': num_key, 'config': cfg_key}, 'cf': {'numeric': num_key, 'config': cfg_key}}
        # Format for dual value cells: [sf_key, cf_key]
        # Format for status cells: (test_v_key, bank_v_cf_key, power_cf_REQ_key, bank_v_sf_key, power_sf_REQ_key)
        rows_frio_keys = [
            ("Tensão frio (kV)", "Tensão frio (kV)"),
            (
                "Corrente frio (A)",
                "Corrente frio (A)",
            ),  # Changed from split cell to simple string key
            ("Pteste frio (MVA)", "Pteste frio (MVA)"),
            ("Potencia Ativa Frio (kW)", "Potencia Ativa EPS Frio (kW)"),
            (
                "Cap Bank Power Frio Req (MVAr)",
                ["Cap Bank Power Frio Sem Fator (MVAr)", "Cap Bank Power Frio Com Fator (MVAr)"],
            ),  # Dual Value (Required Power)
            (
                "Cap Bank V Disp. (kV)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Cap Bank Voltage Frio Sem Fator (kV)",
                        "config": "CS Config Frio S/F",
                    },
                    "cf": {
                        "numeric": "Cap Bank Voltage Frio Com Fator (kV)",
                        "config": "CS Config Frio",
                    },
                },
            ),  # Split cell config
            (
                "Cap Bank Q Disp. (MVAr)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Q Power Provided Frio S/F (MVAr)",
                        "config": "Q Config Frio S/F",
                    },
                    "cf": {"numeric": "Q Power Provided Frio (MVAr)", "config": "Q Config Frio"},
                },
            ),  # Split cell config
            (
                "Status",
                (
                    "Tensão frio (kV)",
                    "Cap Bank Voltage Frio Com Fator (kV)",
                    "Cap Bank Power Frio Com Fator (MVAr)",
                    "Cap Bank Voltage Frio Sem Fator (kV)",
                    "Cap Bank Power Frio Sem Fator (MVAr)",
                    "Corrente frio (A)",
                    "Potencia Ativa EPS Frio (kW)",
                ),
            ),  # Status Tuple (Uses REQUIRED power)
        ]
        rows_quente_keys = [
            ("Tensão quente (kV)", "Tensão quente (kV)"),
            (
                "Corrente quente (A)",
                "Corrente quente (A)",
            ),  # Changed from split cell to simple string key
            ("Pteste quente (MVA)", "Pteste quente (MVA)"),
            ("Potencia Ativa Quente (kW)", "Potencia Ativa Quente (kW)"),
            (
                "Cap Bank Power Quente Req (MVAr)",
                [
                    "Cap Bank Power Quente Sem Fator (MVAr)",
                    "Cap Bank Power Quente Com Fator (MVAr)",
                ],
            ),
            (
                "Cap Bank V Disp. (kV)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Cap Bank Voltage Quente Sem Fator (kV)",
                        "config": "CS Config Quente S/F",
                    },
                    "cf": {
                        "numeric": "Cap Bank Voltage Quente Com Fator (kV)",
                        "config": "CS Config Quente",
                    },
                },
            ),
            (
                "Cap Bank Q Disp. (MVAr)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Q Power Provided Quente S/F (MVAr)",
                        "config": "Q Config Quente S/F",
                    },
                    "cf": {
                        "numeric": "Q Power Provided Quente (MVAr)",
                        "config": "Q Config Quente",
                    },
                },
            ),
            (
                "Status",
                (
                    "Tensão quente (kV)",
                    "Cap Bank Voltage Quente Com Fator (kV)",
                    "Cap Bank Power Quente Com Fator (MVAr)",
                    "Cap Bank Voltage Quente Sem Fator (kV)",
                    "Cap Bank Power Quente Sem Fator (MVAr)",
                    "Corrente quente (A)",
                    "Potencia Ativa Quente (kW)",
                ),
            ),
        ]
        rows_25c_keys = [
            ("Tensão 25°C (kV)", "Tensão 25°C (kV)"),
            (
                "Corrente 25°C (A)",
                "Corrente 25°C (A)",
            ),  # Changed from split cell to simple string key
            ("Pteste 25°C (MVA)", "Pteste 25°C (MVA)"),
            ("Potencia Ativa 25°C (kW)", "Potencia Ativa 25°C (kW)"),
            (
                "Cap Bank Power 25°C Req (MVAr)",
                ["Cap Bank Power 25°C Sem Fator (MVAr)", "Cap Bank Power 25°C Com Fator (MVAr)"],
            ),
            (
                "Cap Bank V Disp. (kV)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Cap Bank Voltage 25°C Sem Fator (kV)",
                        "config": "CS Config 25°C S/F",
                    },
                    "cf": {
                        "numeric": "Cap Bank Voltage 25°C Com Fator (kV)",
                        "config": "CS Config 25°C",
                    },
                },
            ),
            (
                "Cap Bank Q Disp. (MVAr)",
                {
                    "split_cell": True,
                    "sf": {
                        "numeric": "Q Power Provided 25°C S/F (MVAr)",
                        "config": "Q Config 25°C S/F",
                    },
                    "cf": {"numeric": "Q Power Provided 25°C (MVAr)", "config": "Q Config 25°C"},
                },
            ),
            (
                "Status",
                (
                    "Tensão 25°C (kV)",
                    "Cap Bank Voltage 25°C Com Fator (kV)",
                    "Cap Bank Power 25°C Com Fator (MVAr)",
                    "Cap Bank Voltage 25°C Sem Fator (kV)",
                    "Cap Bank Power 25°C Sem Fator (MVAr)",
                    "Corrente 25°C (A)",
                    "Potencia Ativa 25°C (kW)",
                ),
            ),
        ]
        rows_1_2_keys, rows_1_4_keys = [], []
        if overload_applicable:
            rows_1_2_keys = [
                ("Tensão 1.2 pu (kV)", "Tensão 1.2 pu (kV)"),
                (
                    "Corrente 1.2 pu (A)",
                    "Corrente 1.2 pu (A)",
                ),  # Changed from split cell to simple string key
                ("Pteste 1.2 pu (MVA)", "Pteste 1.2 pu (MVA)"),
                ("Potencia Ativa 1.2 pu (kW)", "Potencia Ativa 1.2 pu (kW)"),
                (
                    "Cap Bank Power 1.2 pu Req (MVAr)",
                    [
                        "Cap Bank Power 1.2 pu Sem Fator (MVAr)",
                        "Cap Bank Power 1.2 pu Com Fator (MVAr)",
                    ],
                ),
                (
                    "Cap Bank V Disp. (kV)",
                    {
                        "split_cell": True,
                        "sf": {
                            "numeric": "Cap Bank Voltage 1.2 pu Sem Fator (kV)",
                            "config": "CS Config 1.2 pu S/F",
                        },
                        "cf": {
                            "numeric": "Cap Bank Voltage 1.2 pu Com Fator (kV)",
                            "config": "CS Config 1.2 pu",
                        },
                    },
                ),
                (
                    "Cap Bank Q Disp. (MVAr)",
                    {
                        "split_cell": True,
                        "sf": {
                            "numeric": "Q Power Provided 1.2 pu S/F (MVAr)",
                            "config": "Q Config 1.2 pu S/F",
                        },
                        "cf": {
                            "numeric": "Q Power Provided 1.2 pu (MVAr)",
                            "config": "Q Config 1.2 pu",
                        },
                    },
                ),
                (
                    "Status",
                    (
                        "Tensão 1.2 pu (kV)",
                        "Cap Bank Voltage 1.2 pu Com Fator (kV)",
                        "Cap Bank Power 1.2 pu Com Fator (MVAr)",
                        "Cap Bank Voltage 1.2 pu Sem Fator (kV)",
                        "Cap Bank Power 1.2 pu Sem Fator (MVAr)",
                        "Corrente 1.2 pu (A)",
                        "Potencia Ativa 1.2 pu (kW)",
                    ),
                ),
            ]
            rows_1_4_keys = [
                ("Tensão 1.4 pu (kV)", "Tensão 1.4 pu (kV)"),
                (
                    "Corrente 1.4 pu (A)",
                    "Corrente 1.4 pu (A)",
                ),  # Changed from split cell to simple string key
                ("Pteste 1.4 pu (MVA)", "Pteste 1.4 pu (MVA)"),
                ("Potencia Ativa 1.4 pu (kW)", "Potencia Ativa 1.4 pu (kW)"),
                (
                    "Cap Bank Power 1.4 pu Req (MVAr)",
                    [
                        "Cap Bank Power 1.4 pu Sem Fator (MVAr)",
                        "Cap Bank Power 1.4 pu Com Fator (MVAr)",
                    ],
                ),
                (
                    "Cap Bank V Disp. (kV)",
                    {
                        "split_cell": True,
                        "sf": {
                            "numeric": "Cap Bank Voltage 1.4 pu Sem Fator (kV)",
                            "config": "CS Config 1.4 pu S/F",
                        },
                        "cf": {
                            "numeric": "Cap Bank Voltage 1.4 pu Com Fator (kV)",
                            "config": "CS Config 1.4 pu",
                        },
                    },
                ),
                (
                    "Cap Bank Q Disp. (MVAr)",
                    {
                        "split_cell": True,
                        "sf": {
                            "numeric": "Q Power Provided 1.4 pu S/F (MVAr)",
                            "config": "Q Config 1.4 pu S/F",
                        },
                        "cf": {
                            "numeric": "Q Power Provided 1.4 pu (MVAr)",
                            "config": "Q Config 1.4 pu",
                        },
                    },
                ),
                (
                    "Status",
                    (
                        "Tensão 1.4 pu (kV)",
                        "Cap Bank Voltage 1.4 pu Com Fator (kV)",
                        "Cap Bank Power 1.4 pu Com Fator (MVAr)",
                        "Cap Bank Voltage 1.4 pu Sem Fator (kV)",
                        "Cap Bank Power 1.4 pu Sem Fator (MVAr)",
                        "Corrente 1.4 pu (A)",
                        "Potencia Ativa 1.4 pu (kW)",
                    ),
                ),
            ]

        def extract_row_data(keys_list, results_list):
            """Extracts data for table rows based on keys (Handles single, list, dict, tuple keys)."""
            data = []
            for param_name, keys in keys_list:
                row = [param_name]
                for res_dict in results_list:
                    if isinstance(keys, str):
                        row.append(res_dict.get(keys))
                    elif isinstance(keys, list):  # Dual value [sf_key, cf_key]
                        if len(keys) == 2 and isinstance(keys[0], str) and isinstance(keys[1], str):
                            row.append([res_dict.get(keys[0]), res_dict.get(keys[1])])
                        else:  # Should not happen with current keys_list structure
                            log.warning(f"Unexpected list format for keys: {keys}")
                            row.append(None)
                    elif isinstance(keys, dict) and keys.get("split_cell"):  # Split cell config
                        sf_num_key = keys["sf"]["numeric"]
                        sf_cfg_key = keys["sf"]["config"]
                        cf_num_key = keys["cf"]["numeric"]
                        cf_cfg_key = keys["cf"]["config"]
                        # Pass the dict structure directly to the formatter
                        row.append(
                            {
                                "split_cell": True,
                                "sf": {
                                    "numeric": res_dict.get(sf_num_key),
                                    "config": res_dict.get(sf_cfg_key),
                                },
                                "cf": {
                                    "numeric": res_dict.get(cf_num_key),
                                    "config": res_dict.get(cf_cfg_key),
                                },
                            }
                        )
                    elif isinstance(keys, tuple):  # Status tuple
                        row.append(tuple(res_dict.get(k) for k in keys))
                    else:
                        log.warning(f"Unexpected key format: {keys}")
                        row.append(None)
                data.append(row)
            return data

        # Create Tables for Each Section
        table_frio = dbc.Table(
            [
                header_row,
                create_table_body(
                    extract_row_data(rows_frio_keys, resultados), apply_highlighting=True
                ),
            ],
            bordered=True,
            hover=True,
            striped=True,
            size="sm",
            className="mb-3",
            style=table_style,
        )
        table_quente = dbc.Table(
            [
                header_row,
                create_table_body(
                    extract_row_data(rows_quente_keys, resultados), apply_highlighting=True
                ),
            ],
            bordered=True,
            hover=True,
            striped=True,
            size="sm",
            className="mb-3",
            style=table_style,
        )
        table_25c = dbc.Table(
            [
                header_row,
                create_table_body(
                    extract_row_data(rows_25c_keys, resultados), apply_highlighting=True
                ),
            ],
            bordered=True,
            hover=True,
            striped=True,
            size="sm",
            className="mb-3",
            style=table_style,
        )
        table_1_2 = (
            dbc.Table(
                [
                    header_row,
                    create_table_body(
                        extract_row_data(rows_1_2_keys, resultados), apply_highlighting=True
                    ),
                ],
                bordered=True,
                hover=True,
                striped=True,
                size="sm",
                className="mb-3",
                style=table_style,
            )
            if overload_applicable
            else None
        )
        table_1_4 = (
            dbc.Table(
                [
                    header_row,
                    create_table_body(
                        extract_row_data(rows_1_4_keys, resultados), apply_highlighting=True
                    ),
                ],
                bordered=True,
                hover=True,
                striped=True,
                size="sm",
                className="mb-3",
                style=table_style,
            )
            if overload_applicable
            else None
        )

        # --- Legend ---

        legend = html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H6(
                                "LEGENDA", className="text-center m-0", style=CARD_HEADER_STYLE
                            ),
                            style=COMPONENTS["card_header"],
                        ),
                        dbc.CardBody(
                            [
                                # Tabela de Status
                                html.Table(
                                    [
                                        html.Thead(
                                            html.Tr(
                                                [
                                                    html.Th(
                                                        "Status",
                                                        style={
                                                            "fontSize": "0.8rem",
                                                            "textAlign": "center",
                                                            "color": COLORS["text_header"],
                                                            "backgroundColor": COLORS[
                                                                "background_header"
                                                            ],
                                                            "padding": "4px",
                                                        },
                                                    )
                                                ]
                                            )
                                        ),
                                        html.Tbody(
                                            html.Tr(
                                                [
                                                    html.Td(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                "(V) > Limite",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        "(V)"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "120px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                "(A) > Limite",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        "(A)"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "120px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                "(P) > Limite",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        "(P)"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "120px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                f"Cap Bank ↑ ({cap_bank_analyzer.potencia_critica_threshold:.1f}+ MVAr)",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        f"{cap_bank_analyzer.potencia_critica_threshold:.1f}+"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "150px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                f"Cap Bank ↑ ({cap_bank_analyzer.potencia_alerta_threshold:.1f}+ MVAr)",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        f"{cap_bank_analyzer.potencia_alerta_threshold:.1f}+"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "150px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        [
                                                                            html.Span(
                                                                                "OK",
                                                                                style={
                                                                                    **status_styler.status_styles[
                                                                                        "OK"
                                                                                    ],
                                                                                    "backgroundColor": COLORS[
                                                                                        "background_faint"
                                                                                    ],
                                                                                },
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "flex": "1",
                                                                            "minWidth": "60px",
                                                                            "textAlign": "center",
                                                                        },
                                                                    ),
                                                                ],
                                                                style={
                                                                    "display": "flex",
                                                                    "flexWrap": "wrap",
                                                                    "justifyContent": "space-between",
                                                                    "gap": "5px",
                                                                    "padding": "5px",
                                                                },
                                                            )
                                                        ],
                                                        style={"fontSize": "0.75rem"},
                                                    )
                                                ]
                                            )
                                        ),
                                    ],
                                    style={
                                        "width": "100%",
                                        "borderCollapse": "collapse",
                                        "border": f'1px solid {COLORS["border"]}',
                                        "marginBottom": "10px",
                                    },
                                ),
                                # Explicação S/F e C/F
                                html.Table(
                                    [
                                        html.Thead(
                                            html.Tr(
                                                [
                                                    html.Th(
                                                        "Significado S/F e C/F",
                                                        style={
                                                            "fontSize": "0.8rem",
                                                            "textAlign": "center",
                                                            "color": COLORS["text_header"],
                                                            "backgroundColor": COLORS[
                                                                "background_header"
                                                            ],
                                                            "padding": "4px",
                                                        },
                                                    )
                                                ]
                                            )
                                        ),
                                        html.Tbody(
                                            [
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "S/F:",
                                                                                    style={
                                                                                        "fontWeight": "bold"
                                                                                    },
                                                                                ),
                                                                                " Banco V_teste ≤ V_banco",
                                                                            ],
                                                                            style={
                                                                                "flex": "1",
                                                                                "textAlign": "center",
                                                                            },
                                                                        ),
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    "C/F:",
                                                                                    style={
                                                                                        "fontWeight": "bold"
                                                                                    },
                                                                                ),
                                                                                " Banco V_teste > V_banco × 1.1",
                                                                            ],
                                                                            style={
                                                                                "flex": "1",
                                                                                "textAlign": "center",
                                                                            },
                                                                        ),
                                                                    ],
                                                                    style={
                                                                        "display": "flex",
                                                                        "justifyContent": "space-between",
                                                                        "alignItems": "center",
                                                                        "padding": "5px",
                                                                        "gap": "10px",
                                                                    },
                                                                )
                                                            ],
                                                            style={
                                                                "padding": "4px",
                                                                "fontSize": "0.75rem",
                                                            },
                                                        )
                                                    ]
                                                ),
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        # Exemplo de célula dividida (valores diferentes)
                                                                        html.Div(
                                                                            [
                                                                                html.Div(
                                                                                    [
                                                                                        html.Div(
                                                                                            [
                                                                                                html.Span(
                                                                                                    "12.3"
                                                                                                ),
                                                                                                html.Sup(
                                                                                                    " S/F"
                                                                                                ),
                                                                                            ],
                                                                                            style={
                                                                                                "width": "50%",
                                                                                                "float": "left",
                                                                                                "borderRight": f'1px solid {COLORS["border"]}',
                                                                                                "padding": "2px",
                                                                                                "textAlign": "center",
                                                                                            },
                                                                                        ),
                                                                                        html.Div(
                                                                                            [
                                                                                                html.Span(
                                                                                                    "13.8"
                                                                                                ),
                                                                                                html.Sup(
                                                                                                    " C/F"
                                                                                                ),
                                                                                            ],
                                                                                            style={
                                                                                                "width": "50%",
                                                                                                "float": "right",
                                                                                                "padding": "2px",
                                                                                                "textAlign": "center",
                                                                                            },
                                                                                        ),
                                                                                    ],
                                                                                    style={
                                                                                        "border": f'1px solid {COLORS["border_light"]}',
                                                                                        "overflow": "hidden",
                                                                                        "width": "120px",
                                                                                        "margin": "0 auto",
                                                                                        "borderRadius": "3px",
                                                                                        "backgroundColor": COLORS[
                                                                                            "background_faint"
                                                                                        ],
                                                                                        "fontSize": "0.8em",
                                                                                        "fontWeight": "bold",
                                                                                    },
                                                                                ),
                                                                                html.Div(
                                                                                    "Valores diferentes",
                                                                                    style={
                                                                                        "fontSize": "0.65rem",
                                                                                        "color": COLORS[
                                                                                            "text_muted"
                                                                                        ],
                                                                                        "marginTop": "2px",
                                                                                        "textAlign": "center",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "flex": "1",
                                                                                "textAlign": "center",
                                                                            },
                                                                        ),
                                                                        # Exemplo de célula única (valores iguais)
                                                                        html.Div(
                                                                            [
                                                                                html.Div(
                                                                                    [
                                                                                        html.Span(
                                                                                            "12.3"
                                                                                        ),
                                                                                        html.Sup(
                                                                                            " S/F=C/F"
                                                                                        ),
                                                                                    ],
                                                                                    style={
                                                                                        "border": f'1px solid {COLORS["border_light"]}',
                                                                                        "padding": "2px",
                                                                                        "textAlign": "center",
                                                                                        "width": "120px",
                                                                                        "margin": "0 auto",
                                                                                        "borderRadius": "3px",
                                                                                        "backgroundColor": COLORS[
                                                                                            "background_faint"
                                                                                        ],
                                                                                        "fontSize": "0.8em",
                                                                                        "fontWeight": "bold",
                                                                                    },
                                                                                ),
                                                                                html.Div(
                                                                                    "Valores iguais",
                                                                                    style={
                                                                                        "fontSize": "0.65rem",
                                                                                        "color": COLORS[
                                                                                            "text_muted"
                                                                                        ],
                                                                                        "marginTop": "2px",
                                                                                        "textAlign": "center",
                                                                                    },
                                                                                ),
                                                                            ],
                                                                            style={
                                                                                "flex": "1",
                                                                                "textAlign": "center",
                                                                            },
                                                                        ),
                                                                    ],
                                                                    style={
                                                                        "display": "flex",
                                                                        "justifyContent": "space-between",
                                                                        "alignItems": "center",
                                                                        "padding": "5px",
                                                                        "gap": "10px",
                                                                    },
                                                                )
                                                            ],
                                                            style={
                                                                "padding": "4px",
                                                                "fontSize": "0.7rem",
                                                            },
                                                        )
                                                    ]
                                                ),
                                            ]
                                        ),
                                    ],
                                    style={
                                        "width": "100%",
                                        "borderCollapse": "collapse",
                                        "border": f'1px solid {COLORS["border"]}',
                                        "marginBottom": "5px",
                                    },
                                ),
                            ],
                            style={
                                **COMPONENTS["card_body"],
                                "backgroundColor": COLORS["background_card"],
                                "padding": "0.75rem",
                            },
                        ),
                    ],
                    style=COMPONENTS["card"],
                )
            ],
            className="mt-3",
        )

        # --- SUT/EPS Analysis (Load Losses - WITH COMPENSATION) ---
        tensao_sut_bt_v = SUT_BT_VOLTAGE  # Voltage (e.g., 600V)
        tensao_sut_at_min_v = SUT_AT_MIN_VOLTAGE
        tensao_sut_at_max_v = SUT_AT_MAX_VOLTAGE
        step_sut_at_v = SUT_AT_STEP_VOLTAGE
        limite_corrente_eps_a = EPS_CURRENT_LIMIT  # Amps

        # Function to create the small SUT/EPS table (used below)
        def create_sut_eps_analysis_table_component_compensated(analysis_results):
            """Creates the dbc.Table component for COMPENSATED SUT/EPS analysis."""
            status_msg = analysis_results.get("status", "Erro")
            taps_info = analysis_results.get(
                "taps_info", []
            )  # List of {'tap_sut_kv': ..., 'corrente_eps_a': ..., 'percent_limite': ...}

            if status_msg != "OK":
                status_color = COLORS["danger"]
                return html.Div(
                    status_msg,
                    style={
                        "fontSize": "0.7rem",
                        "textAlign": "center",
                        "padding": "0.5rem",
                        "color": status_color,
                        "fontWeight": "bold",
                    },
                )

            if not taps_info:
                return html.Div(
                    "Nenhum tap SUT aplicável encontrado.",
                    style={
                        "fontSize": "0.7rem",
                        "textAlign": "center",
                        "padding": "0.5rem",
                        "color": COLORS["text_muted"],
                    },
                )

            header_style = {
                **TABLE_HEADER_STYLE_SM,
                "backgroundColor": COLORS["background_header"],
                "color": COLORS["text_header"],
                "padding": "0.2rem",
            }
            cell_style = {**TABLE_VALUE_STYLE_SM, "padding": "0.15rem 0.2rem", "fontSize": "0.7rem"}
            # Cores de fundo claras para status, consistentes com outras tabelas
            current_styles = {
                "negative": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["info_bg_faint"],
                    "color": "blue",
                    "fontStyle": "italic",
                },  # Azul claro para correntes negativas
                "low": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["ok_bg_faint"],
                    "color": "black",
                },  # Verde claro para < 50%
                "medium": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["warning_bg_faint"],
                    "color": "black",
                },  # Amarelo claro para 50-85%
                "high": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["warning_high_bg_faint"],
                    "color": "black",
                },  # Laranja claro para 85-100%
                "critical": {
                    **cell_style,
                    "backgroundColor": CONFIG_COLORS["danger_bg"],
                    "color": "black",
                },  # Vermelho claro para > 100%, texto preto para melhor legibilidade
            }

            def get_style(percent):
                if percent is None or math.isnan(percent):
                    return cell_style
                # Verificar se é negativo (excesso de compensação)
                if percent < 0:
                    return current_styles["negative"]
                # Valores positivos seguem a lógica original
                if percent < 50:
                    return current_styles["low"]
                elif percent < 85:
                    return current_styles["medium"]
                elif percent <= 100:
                    return current_styles["high"]
                else:
                    return current_styles["critical"]

            # Ajustar larguras: Tap SUT (kV) = 1/3, I EPS (A) = 2/3
            tap_header_style = {**header_style, "width": "33%"}
            current_header_style = {**header_style, "width": "67%", "padding": "0.1rem 0"}

            # Criar cabeçalho de duas linhas para a tabela
            header = html.Thead(
                [
                    # Primeira linha: Tap SUT (kV) e I EPS (A)
                    html.Tr(
                        [
                            html.Th(
                                "Tap SUT (kV)",
                                style={**tap_header_style, "borderBottom": "none"},
                                rowSpan=2,
                            ),
                            html.Th(
                                "I EPS (A)",
                                style={**current_header_style, "borderBottom": "none"},
                                colSpan=2,
                            ),
                        ]
                    ),
                    # Segunda linha: (S/F) e (C/F)
                    html.Tr(
                        [
                            html.Th(
                                "(S/F)",
                                style={
                                    **header_style,
                                    "width": "33.5%",
                                    "borderTop": "none",
                                    "fontSize": "0.65rem",
                                    "borderRight": f"1px solid {COLORS['border']}",
                                    "textAlign": "center",
                                },
                            ),
                            html.Th(
                                "(C/F)",
                                style={
                                    **header_style,
                                    "width": "33.5%",
                                    "borderTop": "none",
                                    "fontSize": "0.65rem",
                                    "textAlign": "center",
                                },
                            ),
                        ]
                    ),
                ]
            )
            rows = []
            for info in taps_info:  # Already sorted by voltage and limited
                tap_kv_disp = (
                    f"{info['tap_sut_kv']:.2f}" if info.get("tap_sut_kv") is not None else "-"
                )

                # Função para formatar corrente (converter para kA se > 999.99 A)
                def format_current(current_value):
                    if current_value is None:
                        return "-"

                    current_abs = abs(current_value)
                    if current_abs > 999.99:
                        # Converter para kA com 2 casas decimais
                        formatted = f"{current_value/1000:.2f} kA"
                    else:
                        # Manter em A com 2 casas decimais
                        formatted = f"{current_value:.2f}"

                    return formatted

                # Formatar corrente I EPS (A) para S/F
                if info.get("corrente_eps_sf_a") is not None:
                    corrente_eps_sf = float(info["corrente_eps_sf_a"])
                    eps_sf_a_disp = format_current(corrente_eps_sf)
                else:
                    eps_sf_a_disp = "-"

                # Formatar corrente I EPS (A) para C/F
                if info.get("corrente_eps_cf_a") is not None:
                    corrente_eps_cf = float(info["corrente_eps_cf_a"])
                    eps_cf_a_disp = format_current(corrente_eps_cf)
                else:
                    eps_cf_a_disp = "-"

                # Ajustar estilos das células para manter a proporção 1/3 e 2/3
                tap_cell_style = {**cell_style, "width": "33%", "textAlign": "center"}
                current_cell_style = {**cell_style, "width": "67%", "padding": "0"}

                # Obter estilos baseados nas porcentagens de limite para S/F e C/F
                sf_style = get_style(info.get("percent_limite_sf"))
                cf_style = get_style(info.get("percent_limite_cf"))

                # Criar células separadas para S/F e C/F em vez de uma célula dividida
                # Isso garante melhor alinhamento com os cabeçalhos

                # Célula para o valor Tap SUT (kV)
                tap_cell = html.Td(tap_kv_disp, style=tap_cell_style)

                # Célula para o valor S/F
                sf_cell = html.Td(
                    eps_sf_a_disp,
                    style={
                        **cell_style,
                        "textAlign": "center",
                        "fontWeight": "bold",
                        "backgroundColor": sf_style.get("backgroundColor", "transparent"),
                        "borderRight": f'1px solid {COLORS["border"]}',
                        "width": "33.5%",
                    },
                )

                # Célula para o valor C/F
                cf_cell = html.Td(
                    eps_cf_a_disp,
                    style={
                        **cell_style,
                        "textAlign": "center",
                        "fontWeight": "bold",
                        "backgroundColor": cf_style.get("backgroundColor", "transparent"),
                        "width": "33.5%",
                    },
                )

                # Adicionar a linha com as três células separadas
                rows.append(html.Tr([tap_cell, sf_cell, cf_cell]))
            body = html.Tbody(rows)
            return dbc.Table(
                [header, body],
                bordered=True,
                hover=True,
                striped=True,
                size="sm",
                style={"width": "100%", "tableLayout": "fixed", "marginBottom": "0"},
            )

        # --- Build SUT/EPS Analysis Cards Manually (WITH COMPENSATION) ---
        sut_scenarios_info = {
            "25°C": {
                "tensao_key": "Tensão 25°C (kV)",
                "corrente_key": "Corrente 25°C (A)",
                "q_power_key": "Q Power Provided 25°C (MVAr)",
                "cap_volt_key": "Cap Bank Voltage 25°C Com Fator (kV)",
                "title": "ANÁLISE SUT/EPS: PERDAS CARGA (25°C)",
            },
            "Frio": {
                "tensao_key": "Tensão frio (kV)",
                "corrente_key": "Corrente frio (A)",
                "q_power_key": "Q Power Provided Frio (MVAr)",
                "cap_volt_key": "Cap Bank Voltage Frio Com Fator (kV)",
                "title": "ANÁLISE SUT/EPS: ENERGIZAÇÃO A FRIO",
            },
            "Quente": {
                "tensao_key": "Tensão quente (kV)",
                "corrente_key": "Corrente quente (A)",
                "q_power_key": "Q Power Provided Quente (MVAr)",
                "cap_volt_key": "Cap Bank Voltage Quente Com Fator (kV)",
                "title": "ANÁLISE SUT/EPS: QUENTE COMPENSADO",
            },
        }
        if overload_applicable:
            sut_scenarios_info["1.2 pu"] = {
                "tensao_key": "Tensão 1.2 pu (kV)",
                "corrente_key": "Corrente 1.2 pu (A)",
                "q_power_key": "Q Power Provided 1.2 pu (MVAr)",
                "cap_volt_key": "Cap Bank Voltage 1.2 pu Com Fator (kV)",
                "title": "ANÁLISE SUT/EPS: SOBRECARGA 1.2 PU",
            }
            sut_scenarios_info["1.4 pu"] = {
                "tensao_key": "Tensão 1.4 pu (kV)",
                "corrente_key": "Corrente 1.4 pu (A)",
                "q_power_key": "Q Power Provided 1.4 pu (MVAr)",
                "cap_volt_key": "Cap Bank Voltage 1.4 pu Com Fator (kV)",
                "title": "ANÁLISE SUT/EPS: SOBRECARGA 1.4 PU",
            }

        sut_analysis_cards = {}
        for scen_key, scen_info in sut_scenarios_info.items():
            sut_cols = []
            has_valid_sut_data = False
            for res in resultados:  # Iterate through Nominal, Menor, Maior results
                tap_label = res.get("Tap")
                if tap_label not in ["Nominal", "Menor", "Maior"]:
                    continue

                tensao_ref_dut_kv = res.get(scen_info["tensao_key"])
                corrente_ref_dut_a = res.get(scen_info["corrente_key"])
                # --- Scenario-specific compensation parameters are now obtained directly in the calculation loop ---

                analysis_result = {
                    "status": "Erro nos dados de entrada SUT",
                    "taps_info": [],
                }  # Default
                if tensao_ref_dut_kv is not None and corrente_ref_dut_a is not None:
                    V_target_sut_hv_v = tensao_ref_dut_kv * 1000  # Target in Volts
                    taps_sut_hv_v = np.arange(
                        tensao_sut_at_min_v, tensao_sut_at_max_v + step_sut_at_v, step_sut_at_v
                    )
                    taps_sut_hv_v = taps_sut_hv_v[taps_sut_hv_v > epsilon]

                    if len(taps_sut_hv_v) == 0:
                        analysis_result = {"status": "Faixa SUT AT inválida", "taps_info": []}
                    else:
                        # Find top 5 taps closest to the target voltage
                        diffs = {tap: abs(tap - V_target_sut_hv_v) for tap in taps_sut_hv_v}
                        taps_ordenados = sorted(taps_sut_hv_v, key=lambda tap: diffs[tap])
                        top_5_taps_v = taps_ordenados[:5]

                        taps_info_list_compensated = []
                        for V_sut_hv_tap_v in top_5_taps_v:
                            # Get S/F and C/F values for compensation
                            q_power_scenario_sf_mvar = res.get(
                                f"Q Power Provided {scen_key} S/F (MVAr)"
                            )
                            cap_bank_voltage_scenario_sf_kv = res.get(
                                f"Cap Bank Voltage {scen_key} Sem Fator (kV)"
                            )
                            q_power_scenario_cf_mvar = res.get(
                                f"Q Power Provided {scen_key} (MVAr)"
                            )  # C/F
                            cap_bank_voltage_scenario_cf_kv = res.get(
                                f"Cap Bank Voltage {scen_key} Com Fator (kV)"
                            )

                            # Call the updated compensated calculation function with separate S/F and C/F values
                            comp_result = calculate_sut_eps_current_compensated(
                                tensao_ref_dut_kv=tensao_ref_dut_kv,
                                corrente_ref_dut_a=corrente_ref_dut_a,
                                q_power_scenario_sf_mvar=q_power_scenario_sf_mvar,
                                cap_bank_voltage_scenario_sf_kv=cap_bank_voltage_scenario_sf_kv,
                                q_power_scenario_cf_mvar=q_power_scenario_cf_mvar,
                                cap_bank_voltage_scenario_cf_kv=cap_bank_voltage_scenario_cf_kv,
                                transformer_type=tipo_transformador,
                                V_sut_hv_tap_v=V_sut_hv_tap_v,
                                tensao_sut_bt_v=tensao_sut_bt_v,
                                limite_corrente_eps_a=limite_corrente_eps_a,
                            )
                            taps_info_list_compensated.append(
                                {
                                    "tap_sut_kv": V_sut_hv_tap_v / 1000.0,
                                    "corrente_eps_sf_a": comp_result[
                                        "corrente_eps_sf_a"
                                    ],  # S/F current
                                    "percent_limite_sf": comp_result[
                                        "percent_limite_sf"
                                    ],  # S/F percentage
                                    "corrente_eps_cf_a": comp_result[
                                        "corrente_eps_cf_a"
                                    ],  # C/F current
                                    "percent_limite_cf": comp_result[
                                        "percent_limite_cf"
                                    ],  # C/F percentage
                                }
                            )

                        # Sort the final list by voltage ascending
                        taps_info_list_compensated.sort(key=lambda x: x["tap_sut_kv"])
                        analysis_result = {"status": "OK", "taps_info": taps_info_list_compensated}
                        if taps_info_list_compensated:
                            has_valid_sut_data = True

                # Create the column for this DUT tap (Nominal, Menor, Maior)
                num_display_taps = len(
                    [r for r in resultados if r.get("Tap") in ["Nominal", "Menor", "Maior"]]
                )
                sut_col_width = 12 // num_display_taps if num_display_taps > 0 else 4

                sut_cols.append(
                    dbc.Col(
                        [
                            html.Div(
                                f"Tap {tap_label}",
                                className="text-center py-1",
                                style={
                                    "fontSize": "0.7rem",
                                    "fontWeight": "bold",
                                    "color": COLORS["text_header"],
                                    "backgroundColor": COLORS["background_header"],
                                    "padding": "0.1rem 0",
                                    "marginBottom": "2px",
                                    "borderRadius": "2px 2px 0 0",
                                },
                            ),
                            create_sut_eps_analysis_table_component_compensated(
                                analysis_result
                            ),  # Use the correct render func
                        ],
                        width=sut_col_width,
                        className="px-1",
                    )
                )
            # End loop through DUT taps

            if not sut_cols:
                sut_body_content = html.Div("Erro ao gerar colunas SUT.", style=ERROR_STYLE)
            elif not has_valid_sut_data:
                sut_body_content = html.Div(
                    "Dados SUT/EPS não disponíveis ou inválidos para análise compensada.",
                    style={
                        "fontSize": "0.8rem",
                        "textAlign": "center",
                        "padding": "1rem",
                        "color": COLORS["text_muted"],
                    },
                )
            else:
                sut_body_content = dbc.Row(sut_cols, className="g-2 justify-content-center")

            sut_analysis_cards[scen_key] = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H6(
                            scen_info["title"], className="text-center m-0", style=CARD_HEADER_STYLE
                        )
                    ),
                    dbc.CardBody(
                        sut_body_content, style={**COMPONENTS["card_body"], "padding": "0.3rem"}
                    ),
                ],
                style={**COMPONENTS["card"], "height": "100%"},
            )
        # End loop through Scenarios

        # --- Assemble Final Layout with Results and SUT/EPS side-by-side ---
        detailed_results_children = []
        card_col_width_lg = 7  # Width for results tables on large screens
        sut_col_width_lg = 12 - card_col_width_lg  # Width for SUT analysis cards

        # Card for 25C Load Losses with SUT/EPS Analysis side by side
        detailed_results_children.append(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H6(
                                        "PERDAS EM CARGA 25°C (Resultados)",
                                        className="text-center m-0",
                                        style=CARD_HEADER_STYLE,
                                    )
                                ),
                                dbc.CardBody(
                                    html.Div(table_25c, style=TABLE_WRAPPER_STYLE),
                                    style=COMPONENTS["card_body"],
                                ),
                            ],
                            style={**COMPONENTS["card"], "height": "100%"},
                        ),
                        width=12,
                        lg=card_col_width_lg,
                        className="mb-2 mb-lg-0",
                    ),
                    dbc.Col(
                        sut_analysis_cards.get("25°C", html.Div()), width=12, lg=sut_col_width_lg
                    ),
                ],
                className="mb-3 g-2 align-items-stretch",
            )  # Use align-items-stretch
        )

        # Card for Cold Energization with SUT/EPS Analysis side by side
        detailed_results_children.append(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H6(
                                        "ENERGIZAÇÃO A FRIO (Resultados)",
                                        className="text-center m-0",
                                        style=CARD_HEADER_STYLE,
                                    )
                                ),
                                dbc.CardBody(
                                    html.Div(table_frio, style=TABLE_WRAPPER_STYLE),
                                    style=COMPONENTS["card_body"],
                                ),
                            ],
                            style={**COMPONENTS["card"], "height": "100%"},
                        ),
                        width=12,
                        lg=card_col_width_lg,
                        className="mb-2 mb-lg-0",
                    ),
                    dbc.Col(
                        sut_analysis_cards.get("Frio", html.Div()), width=12, lg=sut_col_width_lg
                    ),
                ],
                className="mb-3 g-2 align-items-stretch",
            )
        )

        # Card for Hot Condition with SUT/EPS Analysis side by side
        detailed_results_children.append(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H6(
                                        "CONDIÇÃO A QUENTE (Resultados)",
                                        className="text-center m-0",
                                        style=CARD_HEADER_STYLE,
                                    )
                                ),
                                dbc.CardBody(
                                    html.Div(table_quente, style=TABLE_WRAPPER_STYLE),
                                    style=COMPONENTS["card_body"],
                                ),
                            ],
                            style={**COMPONENTS["card"], "height": "100%"},
                        ),
                        width=12,
                        lg=card_col_width_lg,
                        className="mb-2 mb-lg-0",
                    ),
                    dbc.Col(
                        sut_analysis_cards.get("Quente", html.Div()), width=12, lg=sut_col_width_lg
                    ),
                ],
                className="mb-3 g-2 align-items-stretch",
            )
        )

        # Cards for Overload (if applicable) with SUT/EPS Analysis side by side
        if table_1_2:
            detailed_results_children.append(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "SOBRECARGA 1.2 PU (Resultados)",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        )
                                    ),
                                    dbc.CardBody(
                                        html.Div(table_1_2, style=TABLE_WRAPPER_STYLE),
                                        style=COMPONENTS["card_body"],
                                    ),
                                ],
                                style={**COMPONENTS["card"], "height": "100%"},
                            ),
                            width=12,
                            lg=card_col_width_lg,
                            className="mb-2 mb-lg-0",
                        ),
                        dbc.Col(
                            sut_analysis_cards.get("1.2 pu", html.Div()),
                            width=12,
                            lg=sut_col_width_lg,
                        ),
                    ],
                    className="mb-3 g-2 align-items-stretch",
                )
            )

        if table_1_4:
            detailed_results_children.append(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H6(
                                            "SOBRECARGA 1.4 PU (Resultados)",
                                            className="text-center m-0",
                                            style=CARD_HEADER_STYLE,
                                        )
                                    ),
                                    dbc.CardBody(
                                        html.Div(table_1_4, style=TABLE_WRAPPER_STYLE),
                                        style=COMPONENTS["card_body"],
                                    ),
                                ],
                                style={**COMPONENTS["card"], "height": "100%"},
                            ),
                            width=12,
                            lg=card_col_width_lg,
                            className="mb-2 mb-lg-0",
                        ),
                        dbc.Col(
                            sut_analysis_cards.get("1.4 pu", html.Div()),
                            width=12,
                            lg=sut_col_width_lg,
                        ),
                    ],
                    className="mb-3 g-2 align-items-stretch",
                )
            )

        # Add Legend
        detailed_results_children.append(legend)

        # Final layout for detailed results area
        detailed_results_layout = html.Div(detailed_results_children)

        # --- Nominal Conditions Card Content (Unchanged) ---
        res_menor = next((r for r in resultados if r.get("Tap") == "Menor"), None)
        res_nom = next((r for r in resultados if r.get("Tap") == "Nominal"), None)
        res_maior = next((r for r in resultados if r.get("Tap") == "Maior"), None)

        if res_nom is None or res_menor is None or res_maior is None:
            missing_taps = [
                tap
                for tap, res in [("Nominal", res_nom), ("Menor", res_menor), ("Maior", res_maior)]
                if res is None
            ]
            error_msg = f"Erro interno: Não foi possível extrair resultados para os Taps: {', '.join(missing_taps)}."
            log.error(error_msg + f" Resultados: {resultados}")
            error_div = html.Div(error_msg, style=ERROR_STYLE)
            return initial_detailed_content, error_div, no_update

        nominal_header_style = {**TABLE_HEADER_STYLE_MD, "width": "auto"}
        nominal_param_style = {
            **TABLE_PARAM_STYLE_MD,
            "width": "40%",
            "textAlign": "left",
            "paddingLeft": "5px",
        }
        nominal_value_style = {**TABLE_VALUE_STYLE_MD, "width": "20%", "textAlign": "center"}

        nominal_header = html.Thead(
            html.Tr(
                [
                    html.Th("Parâmetro", style={**nominal_header_style, **nominal_param_style}),
                    html.Th("Tap Nominal", style={**nominal_header_style, **nominal_value_style}),
                    html.Th("Tap Menor", style={**nominal_header_style, **nominal_value_style}),
                    html.Th("Tap Maior", style={**nominal_header_style, **nominal_value_style}),
                ]
            )
        )

        basic_rows_nominal = [
            html.Tr(
                [
                    html.Td("Temperatura de Referência (°C)", style={**nominal_param_style, "color": "black"}),
                    html.Td(f"{temperatura_ref}", style=nominal_value_style),
                    html.Td(f"{temperatura_ref}", style=nominal_value_style),
                    html.Td(f"{temperatura_ref}", style=nominal_value_style),
                ]
            ),
            html.Tr(
                [
                    html.Td("Tensão (kV)", style=nominal_param_style),
                    html.Td(get_formatted(res_nom, "Tensão", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_menor, "Tensão", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_maior, "Tensão", 2), style=nominal_value_style),
                ]
            ),
            html.Tr(
                [
                    html.Td("Corrente (A)", style=nominal_param_style),
                    html.Td(get_formatted(res_nom, "Corrente", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_menor, "Corrente", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_maior, "Corrente", 2), style=nominal_value_style),
                ]
            ),
            html.Tr(
                [
                    html.Td("Vcc (%)", style=nominal_param_style),
                    html.Td(get_formatted(res_nom, "Vcc (%)", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_menor, "Vcc (%)", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_maior, "Vcc (%)", 2), style=nominal_value_style),
                ]
            ),
            html.Tr(
                [
                    html.Td("Vcc (kV)", style=nominal_param_style),
                    html.Td(get_formatted(res_nom, "Vcc (kV)", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_menor, "Vcc (kV)", 2), style=nominal_value_style),
                    html.Td(get_formatted(res_maior, "Vcc (kV)", 2), style=nominal_value_style),
                ]
            ),
        ]
        losses_rows_nominal = [
            html.Tr(
                [
                    html.Td(f"Perdas Totais (kW) {temperatura_ref}°C", style=nominal_param_style),
                    html.Td(
                        get_formatted(res_nom, "Perdas totais (kW)", 2), style=nominal_value_style
                    ),
                    html.Td(
                        get_formatted(res_menor, "Perdas totais (kW)", 2), style=nominal_value_style
                    ),
                    html.Td(
                        get_formatted(res_maior, "Perdas totais (kW)", 2), style=nominal_value_style
                    ),
                ]
            ),
            html.Tr(
                [
                    html.Td(
                        f"Perdas Carga S/ Vazio (kW) {temperatura_ref}°C", style=nominal_param_style
                    ),
                    html.Td(
                        get_formatted(res_nom, "Perdas Carga Sem Vazio (kW)", 2),
                        style=nominal_value_style,
                    ),
                    html.Td(
                        get_formatted(res_menor, "Perdas Carga Sem Vazio (kW)", 2),
                        style=nominal_value_style,
                    ),
                    html.Td(
                        get_formatted(res_maior, "Perdas Carga Sem Vazio (kW)", 2),
                        style=nominal_value_style,
                    ),
                ]
            ),
            html.Tr(
                [
                    html.Td("Perdas Frio (25°C) (kW)", style=nominal_param_style),
                    html.Td(
                        get_formatted(res_nom, "Perdas a Frio (25°C) (kW)", 2),
                        style=nominal_value_style,
                    ),
                    html.Td(
                        get_formatted(res_menor, "Perdas a Frio (25°C) (kW)", 2),
                        style=nominal_value_style,
                    ),
                    html.Td(
                        get_formatted(res_maior, "Perdas a Frio (25°C) (kW)", 2),
                        style=nominal_value_style,
                    ),
                ]
            ),
            html.Tr(
                [
                    html.Td("Perdas Vazio (kW)", style=nominal_param_style),
                    html.Td(f"{perdas_vazio_nom:.2f}", style=nominal_value_style),
                    html.Td(f"{perdas_vazio_nom:.2f}", style=nominal_value_style),
                    html.Td(f"{perdas_vazio_nom:.2f}", style=nominal_value_style),
                ]
            ),
        ]

        condicoes_nominais_content = html.Div(
            dbc.Table(
                [nominal_header, html.Tbody(basic_rows_nominal + losses_rows_nominal)],
                bordered=True,
                striped=True,
                hover=True,
                size="sm",
            ),
            style=TABLE_WRAPPER_STYLE,
        )

        # --- Update Store ---
        # Prepare the new data to be stored
        new_data = {
            "resultados": resultados,  # Store the detailed list of dicts
            "perdas_carga_nom": perdas_totais_nom_input,
            "perdas_carga_min": perdas_totais_min_input,
            "perdas_carga_max": perdas_totais_max_input,
            "temperatura_referencia": temperatura_ref,
            "suggested_cs_config": cs_config_str,
            "suggested_q_config": q_config_str,
            "suggested_q_power_mvar": q_power_mvar_provided_overall,  # Store the OVERALL provided power
            "max_test_voltage_kv_overall": max_test_voltage_kv_overall,
            "max_test_power_mvar_overall_required": max_test_power_mvar_overall_required,  # Store the required max power
            # No need to store scenario_configs separately, they are now part of 'resultados'
        }

        # Adicionar os inputs específicos para perdas em carga conforme solicitado
        inputs_perdas_carga = {
            "temperatura_referencia_c": temperatura_ref,
            "perdas_totais_tap_menos_kw": perdas_totais_min_input,
            "perdas_totais_tap_nominal_kw": perdas_totais_nom_input,
            "perdas_totais_tap_mais_kw": perdas_totais_max_input,
        }

        # Initialize the store data if it's None
        store_para_salvar = current_losses_store_data if isinstance(current_losses_store_data, dict) else {}

        # Garantir que os dados de perdas em vazio sejam preservados
        if "resultados_perdas_vazio" in losses_data and isinstance(losses_data["resultados_perdas_vazio"], dict):
            if "resultados_perdas_vazio" not in store_para_salvar or not isinstance(store_para_salvar["resultados_perdas_vazio"], dict):
                log.info("[LOSSES CARGA] Copiando dados de 'resultados_perdas_vazio' do losses_data para store_para_salvar.")
                store_para_salvar["resultados_perdas_vazio"] = losses_data["resultados_perdas_vazio"]
            elif "perdas_vazio_kw" not in store_para_salvar["resultados_perdas_vazio"] and "perdas_vazio_kw" in losses_data["resultados_perdas_vazio"]:
                log.info("[LOSSES CARGA] Copiando valor de 'perdas_vazio_kw' do losses_data para store_para_salvar.")
                store_para_salvar["resultados_perdas_vazio"]["perdas_vazio_kw"] = losses_data["resultados_perdas_vazio"]["perdas_vazio_kw"]

        # Garantir que os dados de inputs de perdas em vazio sejam preservados
        if "inputs_perdas_vazio" in losses_data and isinstance(losses_data["inputs_perdas_vazio"], dict):
            if "inputs_perdas_vazio" not in store_para_salvar or not isinstance(store_para_salvar["inputs_perdas_vazio"], dict):
                log.info("[LOSSES CARGA] Copiando dados de 'inputs_perdas_vazio' do losses_data para store_para_salvar.")
                store_para_salvar["inputs_perdas_vazio"] = losses_data["inputs_perdas_vazio"]

        # Initialize the resultados_perdas_carga section if it doesn't exist or não é um dicionário
        if "resultados_perdas_carga" not in store_para_salvar or not isinstance(store_para_salvar["resultados_perdas_carga"], dict):
            log.warning("Seção 'resultados_perdas_carga' não existe ou não é um dicionário. Inicializando como dicionário vazio.")
            store_para_salvar["resultados_perdas_carga"] = {}

        # Initialize the inputs_perdas_carga section if it doesn't exist
        if "inputs_perdas_carga" not in store_para_salvar or not isinstance(store_para_salvar["inputs_perdas_carga"], dict):
            log.warning("Seção 'inputs_perdas_carga' não existe ou não é um dicionário. Inicializando como dicionário vazio.")
            store_para_salvar["inputs_perdas_carga"] = {}

        # Update the resultados_perdas_carga section with the new data
        store_para_salvar["resultados_perdas_carga"].update(new_data)

        # Update the inputs_perdas_carga section with the inputs data
        store_para_salvar["inputs_perdas_carga"].update(inputs_perdas_carga)

        store_para_salvar["timestamp_carga"] = datetime.datetime.now().isoformat()

        # Log para debug
        log.info(f"[LOSSES CARGA] Dados atualizados em resultados_perdas_carga: {store_para_salvar['resultados_perdas_carga'].keys()}")
        log.info(f"[LOSSES CARGA] Valores de perdas: nom={new_data.get('perdas_carga_nom')}, min={new_data.get('perdas_carga_min')}, max={new_data.get('perdas_carga_max')}")

        # Validar os dados antes de armazenar no MCP
        validation_rules = {
            "perdas_carga_nom": {
                "required": True,
                "positive": True,
                "label": "Perdas em Carga (Nominal)",
            },
            "perdas_carga_min": {
                "required": True,
                "positive": True,
                "label": "Perdas em Carga (Tap Menor)",
            },
            "perdas_carga_max": {
                "required": True,
                "positive": True,
                "label": "Perdas em Carga (Tap Maior)",
            },
            "temperatura_referencia": {
                "required": True,
                "min": 0,
                "max": 200,
                "label": "Temperatura de Referência",
            },
        }

        validation_errors = validate_dict_inputs(new_data, validation_rules)
        if validation_errors:
            log.warning(f"Validação de dados de perdas em carga falhou: {validation_errors}")
            # Continua mesmo com erros, mas loga os problemas

        # Serializar os dados antes de armazenar no MCP
        serializable_data = convert_numpy_types(store_para_salvar, debug_path="losses_carga_update")

        # Armazenar no MCP
        app.mcp.set_data("losses-store", serializable_data)
        log.critical(f"[LOSSES CALC CARGA] losses-store atualizado com: {serializable_data.get('resultados_perdas_carga')}")

        # Verificar se os dados foram armazenados corretamente
        verification_data = app.mcp.get_data("losses-store")
        if verification_data and "resultados_perdas_carga" in verification_data and isinstance(verification_data["resultados_perdas_carga"], dict):
            log.info(f"[LOSSES CALC CARGA] Verificação: dados armazenados corretamente no MCP. Chaves em resultados_perdas_carga: {verification_data['resultados_perdas_carga'].keys()}")

            # Verificar se os dados de perdas em vazio ainda estão presentes
            if "resultados_perdas_vazio" in verification_data and isinstance(verification_data["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in verification_data["resultados_perdas_vazio"]:
                log.info(f"[LOSSES CALC CARGA] Verificação: dados de perdas em vazio ainda presentes no MCP. perdas_vazio_kw = {verification_data['resultados_perdas_vazio'].get('perdas_vazio_kw')}")
            else:
                log.error(f"[LOSSES CALC CARGA] Verificação: dados de perdas em vazio PERDIDOS no MCP após atualização de perdas em carga!")

                # Tentar recuperar dados de perdas em vazio
                if "resultados_perdas_vazio" in store_para_salvar and isinstance(store_para_salvar["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in store_para_salvar["resultados_perdas_vazio"]:
                    log.info(f"[LOSSES CALC CARGA] Recuperando dados de perdas em vazio do store_para_salvar e salvando novamente no MCP.")
                    app.mcp.set_data("losses-store", store_para_salvar)

                    # Verificar novamente
                    verification_data = app.mcp.get_data("losses-store")
                    if "resultados_perdas_vazio" in verification_data and isinstance(verification_data["resultados_perdas_vazio"], dict) and "perdas_vazio_kw" in verification_data["resultados_perdas_vazio"]:
                        log.info(f"[LOSSES CALC CARGA] Recuperação bem-sucedida. perdas_vazio_kw = {verification_data['resultados_perdas_vazio'].get('perdas_vazio_kw')}")
                    else:
                        log.error(f"[LOSSES CALC CARGA] Falha na recuperação dos dados de perdas em vazio.")
        else:
            log.error(f"[LOSSES CALC CARGA] Verificação: dados NÃO foram armazenados corretamente no MCP. verification_data = {verification_data}")

        log.info(
            f"Cálculo de perdas em carga concluído para Tref={temperatura_ref}°C. Max V: {max_test_voltage_kv_overall:.1f} kV, Max Q Req: {max_test_power_mvar_overall_required:.1f} MVAr."
        )
        log.info(
            f"Sugestão Geral - CS: {cs_config_str}, Q: {q_config_str} ({q_power_mvar_provided_overall:.1f} MVAr)"
        )

        # --- Return ---
        return (detailed_results_layout, condicoes_nominais_content, serializable_data)

    except ValueError as e:
        log.error(f"ValueError in handle_perdas_carga: {e}")
        error_div = html.Div(
            f"Erro ao calcular: Verifique os inputs numéricos. Detalhe: {str(e)}", style=ERROR_STYLE
        )
        return initial_detailed_content, error_div, no_update
    except KeyError as e:
        log.error(
            f"KeyError in handle_perdas_carga: Missing key {e}. Transformer Data: {transformer_data.keys() if transformer_data else 'None'}. Losses Data: {losses_data.keys() if losses_data else 'None'}"
        )
        error_div = html.Div(
            f"Erro: Dado necessário ({e}) não encontrado. Verifique os dados do transformador e o cálculo de perdas em vazio.",
            style=ERROR_STYLE,
        )
        return initial_detailed_content, error_div, no_update
    except Exception as e:
        log.exception(f"Exception in handle_perdas_carga: {e}")  # Log full traceback
        error_div = html.Div(
            f"Erro inesperado ao calcular perdas em carga: {str(e)}", style=ERROR_STYLE
        )
        return initial_detailed_content, error_div, no_update
