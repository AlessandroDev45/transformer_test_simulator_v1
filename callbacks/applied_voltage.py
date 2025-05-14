# callbacks/applied_voltage.py
""" Callbacks para a seção de Tensão Aplicada. """
import datetime
import logging
import os
import sys

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, no_update

# Adiciona o diretório raiz ao caminho de importação quando executado diretamente
if __name__ == "__main__":
    # Obtém o caminho absoluto do diretório atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Obtém o diretório pai (raiz do projeto)
    parent_dir = os.path.dirname(current_dir)
    # Adiciona o diretório raiz ao caminho de importação
    sys.path.insert(0, parent_dir)

# Importações da aplicação
# Removido import direto do app
from app_core.calculations import calculate_capacitive_load  # Função de cálculo principal
from components.formatters import (  # Formatadores
    format_parameter_value,
)
from layouts import COLORS  # Para estilos padronizados
from utils import constants  # Para RESOANT_SYSTEM_CONFIGS
from utils.store_diagnostics import convert_numpy_types
from components.validators import validate_dict_inputs  # Para validação

log = logging.getLogger(__name__)

# Funções de callback que serão registradas explicitamente

# Função update_transformer_info_applied removida - não é mais necessária pois usamos o template padrão

# Função populate_test_voltage_fields removida - não é mais necessária pois usamos displays em vez de campos de entrada


# --- Funções Auxiliares ---
def safe_float(value, default=None):
    """Safely convert value to float, return default on error."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def analyze_resonant_system_viability(capacitance_nf, voltage_kv, enrolamento=""):
    """
    Analisa qual configuração do sistema ressonante é adequada e se o ensaio é viável.
    Prioriza a configuração "Módulos 1||2||3 (3 Par.)" sempre que possível.

    Args:
        capacitance_nf (float): Capacitância de ensaio em nF.
        voltage_kv (float): Tensão de ensaio em kV.
        enrolamento (str, optional): Nome do enrolamento (AT, BT, Terciário). Defaults to "".

    Returns:
        dict: Contendo 'resonant_config', 'viabilidade', 'recommendation', 'cor_alerta', 'enrolamento'.
              Retorna Nones se inputs inválidos.
    """
    if capacitance_nf is None or voltage_kv is None or capacitance_nf < 0 or voltage_kv < 0:
        return {
            "resonant_config": "Inválido",
            "viabilidade": "Erro",
            "recommendation": "Capacitância ou Tensão de ensaio inválida.",
            "cor_alerta": "danger",
            "enrolamento": enrolamento,
        }

    # Primeiro, verificar se podemos usar Módulos 1||2||3 (3 Par.)
    modulos_3par_450kv = None
    modulos_3par_270kv = None

    # Encontrar as configurações de Módulos 1||2||3 (3 Par.)
    for name, config in constants.RESONANT_SYSTEM_CONFIGS.items():
        if "Módulos 1||2||3 (3 Par.) 450kV" in name:
            modulos_3par_450kv = (name, config)
        elif "Módulos 1||2||3 (3 Par.) 270kV" in name:
            modulos_3par_270kv = (name, config)

    # Verificar se podemos usar Módulos 1||2||3 (3 Par.) 450kV
    if (
        modulos_3par_450kv
        and voltage_kv <= modulos_3par_450kv[1]["tensao_max"]
        and capacitance_nf >= modulos_3par_450kv[1]["cap_min"]
        and capacitance_nf <= modulos_3par_450kv[1]["cap_max"]
    ):
        viable_config = modulos_3par_450kv[1]
        viable_config["nome"] = modulos_3par_450kv[0]

    # Verificar se podemos usar Módulos 1||2||3 (3 Par.) 270kV
    elif (
        modulos_3par_270kv
        and voltage_kv <= modulos_3par_270kv[1]["tensao_max"]
        and capacitance_nf >= modulos_3par_270kv[1]["cap_min"]
        and capacitance_nf <= modulos_3par_270kv[1]["cap_max"]
    ):
        viable_config = modulos_3par_270kv[1]
        viable_config["nome"] = modulos_3par_270kv[0]

    # Se não for possível usar Módulos 1||2||3 (3 Par.), tentar outras configurações
    else:
        # Ordenar as configurações por tensão máxima (decrescente) e capacitância máxima (crescente)
        # para priorizar configurações com menor capacitância para uma dada tensão
        sorted_configs = sorted(
            [(name, config) for name, config in constants.RESONANT_SYSTEM_CONFIGS.items()],
            key=lambda x: (-x[1]["tensao_max"], x[1]["cap_max"]),
        )

        viable_config = None
        for name, config in sorted_configs:
            if (
                voltage_kv <= config["tensao_max"]
                and capacitance_nf >= config["cap_min"]
                and capacitance_nf <= config["cap_max"]
            ):
                viable_config = config
                viable_config["nome"] = name  # Adiciona o nome ao dicionário
                break  # Encontrou a primeira configuração viável

    if viable_config:
        # Verificar se é uma configuração de Módulos 1||2||3 (3 Par.)
        is_modulos_3par = "Módulos 1||2||3 (3 Par.)" in viable_config["nome"]

        # Calcular a capacitância original (sem o divisor de tensão)
        divisor_capacitancia = 0.33 if voltage_kv > 450 else 0.66  # Valor em nF (330pF ou 660pF)
        capacitancia_original_nf = capacitance_nf - divisor_capacitancia

        # Mensagem de recomendação personalizada
        if is_modulos_3par:
            recommendation = (
                f"Configuração ideal: {viable_config['nome']}. "
                f"Limites: {viable_config['tensao_max']}kV / "
                f"{viable_config['cap_min']:.2f}-{viable_config['cap_max']:.1f}nF."
            )
        else:
            recommendation = (
                f"Configuração alternativa: {viable_config['nome']}. "
                f"Limites: {viable_config['tensao_max']}kV / "
                f"{viable_config['cap_min']:.2f}-{viable_config['cap_max']:.1f}nF. "
                f"Capacitância fora do range ideal para Módulos 1||2||3 (3 Par.)."
            )

        # Adiciona informação sobre a capacitância do divisor de tensão
        recommendation += f" Nota: A capacitância de {capacitance_nf:.2f} nF inclui {divisor_capacitancia:.2f} nF do divisor de tensão."

        return {
            "resonant_config": viable_config["nome"],
            "viabilidade": "Viável",
            "recommendation": recommendation,
            "cor_alerta": "success",
            "enrolamento": enrolamento,
        }
    else:
        # Determinar a razão da inviabilidade
        reason = ""
        configs_tensao_ok = [
            c for _, c in constants.RESONANT_SYSTEM_CONFIGS.items() if voltage_kv <= c["tensao_max"]
        ]

        # Verificar especificamente os limites dos Módulos 1||2||3 (3 Par.)
        modulos_3par_min_cap = None
        modulos_3par_max_cap = None
        modulos_3par_max_volt = None

        if modulos_3par_450kv and modulos_3par_270kv:
            modulos_3par_min_cap = min(
                modulos_3par_450kv[1]["cap_min"], modulos_3par_270kv[1]["cap_min"]
            )
            modulos_3par_max_cap = max(
                modulos_3par_450kv[1]["cap_max"], modulos_3par_270kv[1]["cap_max"]
            )
            modulos_3par_max_volt = max(
                modulos_3par_450kv[1]["tensao_max"], modulos_3par_270kv[1]["tensao_max"]
            )

        if not configs_tensao_ok:
            max_sys_volt = max(
                c["tensao_max"] for _, c in constants.RESONANT_SYSTEM_CONFIGS.items()
            )
            reason = f"Tensão ({voltage_kv:.1f} kV) excede o máximo do sistema ({max_sys_volt} kV)."

            if modulos_3par_max_volt:
                reason += (
                    f" Para Módulos 1||2||3 (3 Par.), a tensão máxima é {modulos_3par_max_volt} kV."
                )
        else:
            # Tensão OK, problema é capacitância
            min_cap_needed = min(c["cap_min"] for c in configs_tensao_ok)
            max_cap_allowed = max(c["cap_max"] for c in configs_tensao_ok)

            if capacitance_nf < min_cap_needed:
                # Calcular a capacitância original (sem o divisor de tensão)
                divisor_capacitancia = (
                    0.33 if voltage_kv > 450 else 0.66
                )  # Valor em nF (330pF ou 660pF)
                capacitancia_original_nf = capacitance_nf - divisor_capacitancia

                reason = f"Capacitância ({capacitance_nf:.2f} nF) abaixo do mínimo ({min_cap_needed:.2f} nF) para esta tensão."
                reason += f" Nota: Inclui {divisor_capacitancia:.2f} nF do divisor de tensão."

                if capacitancia_original_nf < min_cap_needed - divisor_capacitancia:
                    reason += f" Mesmo sem o divisor, a capacitância informada ({capacitancia_original_nf:.2f} nF) estaria abaixo do limite."

                if modulos_3par_min_cap and capacitance_nf < modulos_3par_min_cap:
                    reason += f" Para Módulos 1||2||3 (3 Par.), a capacitância mínima é {modulos_3par_min_cap:.2f} nF."
            elif capacitance_nf > max_cap_allowed:
                # Calcular a capacitância original (sem o divisor de tensão)
                divisor_capacitancia = (
                    0.33 if voltage_kv > 450 else 0.66
                )  # Valor em nF (330pF ou 660pF)
                capacitancia_original_nf = capacitance_nf - divisor_capacitancia

                reason = f"Capacitância ({capacitance_nf:.2f} nF) acima do máximo ({max_cap_allowed:.1f} nF) para esta tensão."
                reason += f" Nota: Inclui {divisor_capacitancia:.2f} nF do divisor de tensão."

                if capacitancia_original_nf <= max_cap_allowed:
                    reason += f" A capacitância informada ({capacitancia_original_nf:.2f} nF) estaria dentro do limite sem o divisor."

                if modulos_3par_max_cap and capacitance_nf > modulos_3par_max_cap:
                    reason += f" Para Módulos 1||2||3 (3 Par.), a capacitância máxima é {modulos_3par_max_cap:.1f} nF."
            else:
                # Caso raro onde a tensão está OK, mas a capacitância cai num 'gap' entre configs
                reason = "Nenhuma configuração cobre esta combinação Tensão/Capacitância."

                if modulos_3par_min_cap and modulos_3par_max_cap:
                    reason += f" Para Módulos 1||2||3 (3 Par.), o range de capacitância é {modulos_3par_min_cap:.2f}-{modulos_3par_max_cap:.1f} nF."

        return {
            "resonant_config": "Nenhuma",
            "viabilidade": "Não Viável",
            "recommendation": f"Inválido: {reason}",
            "cor_alerta": "danger",
            "enrolamento": enrolamento,
        }


# --- Callbacks ---


# --- Callback para exibir informações do transformador na página ---
# Este callback copia o conteúdo do painel global para o painel específico da página
@dash.callback(
    Output("transformer-info-applied-page", "children"),
    Input("transformer-info-applied", "children"),
    prevent_initial_call=False,
)
def update_applied_page_info_panel(global_panel_content):
    """Copia o conteúdo do painel global para o painel específico da página."""
    return global_panel_content


# Callback para preencher o campo de frequência na página de tensão aplicada
# Removido para permitir que o usuário preencha manualmente a frequência de ensaio
# A frequência de ensaio deve ser preenchida pelo usuário, não calculada automaticamente


# Função de callback principal para cálculo e análise de viabilidade
def applied_voltage_calculate_and_analyze(
    n_clicks,  # Parâmetro para o botão
    cap_at_pf,
    cap_bt_pf,
    cap_ter_pf,  # Parâmetros de capacitância
    transformer_data,
    current_store_data,
):
    """
    Calcula Zc, I, P para cada enrolamento e analisa a viabilidade com o sistema ressonante.
    Salva os inputs e resultados no store.
    Obtém a frequência diretamente do transformer-inputs-store.
    """
    from dash import callback_context

    print("=" * 80)
    print(
        f"***** CALLBACK applied_voltage_calculate_and_analyze INICIADO - Botão clicado {n_clicks} vezes - Trigger: {callback_context.triggered_id if callback_context.triggered else 'N/A'} *****"
    )
    print("=" * 80)
    log.info(
        f"***** CALLBACK applied_voltage_calculate_and_analyze INICIADO - Botão clicado {n_clicks} vezes - Trigger: {callback_context.triggered_id if callback_context.triggered else 'N/A'} *****"
    )

    # Logs para os States
    log.debug(f"[CALC Applied] State cap_at_pf: {cap_at_pf}")
    log.debug(f"[CALC Applied] State cap_bt_pf: {cap_bt_pf}")
    log.debug(f"[CALC Applied] State cap_ter_pf: {cap_ter_pf}")
    log.debug(f"[CALC Applied] State transformer_data: {transformer_data}")
    log.debug(f"[CALC Applied] State current_store_data: {current_store_data}")

    # A frequência será obtida diretamente do transformer_data mais abaixo no código

    log.debug("Calculating Applied Voltage...")

    # --- Obtenção dos valores de tensão diretamente do transformer_data ---
    if not transformer_data or not isinstance(transformer_data, dict):
        log.error("[Applied Voltage] Dados do transformador inválidos ou ausentes")
        error_msg = html.Ul(
            [
                html.Li(
                    "Dados do transformador não encontrados. Configure os dados básicos do transformador primeiro."
                )
            ],
            style={"color": "red", "fontSize": "0.7rem"},
        )
        return error_msg, "", no_update

    # Verificar se os dados estão aninhados em transformer_data
    if "transformer_data" in transformer_data and isinstance(transformer_data["transformer_data"], dict):
        # Usar os dados aninhados
        data_dict = transformer_data["transformer_data"]
        log.debug(f"[CALC Applied] Usando dados aninhados em transformer_data")
    else:
        # Usar os dados diretamente
        data_dict = transformer_data
        log.debug(f"[CALC Applied] Usando dados diretamente do dicionário principal")

    # Obtém os valores de tensão do dicionário apropriado
    tensao_at_kv_str = data_dict.get("teste_tensao_aplicada_at")
    tensao_bt_kv_str = data_dict.get("teste_tensao_aplicada_bt")
    tensao_ter_kv_str = data_dict.get("teste_tensao_aplicada_terciario")

    log.info(
        f"[Applied Voltage] Usando tensões do transformer_data: AT={tensao_at_kv_str}, BT={tensao_bt_kv_str}, Ter={tensao_ter_kv_str}"
    )

    # Obtém a frequência diretamente do dicionário apropriado
    frequencia_str = data_dict.get("frequencia", "60")  # Valor padrão de 60 Hz

    inputs = {
        "Cap. AT (pF)": cap_at_pf,
        "Cap. BT (pF)": cap_bt_pf,
        "Tensão AT (kV)": tensao_at_kv_str,
        "Tensão BT (kV)": tensao_bt_kv_str,
        "Frequência (Hz)": frequencia_str,
    }
    # Cap Ter e Tensão Ter são opcionais
    cap_ter_pf_val = safe_float(cap_ter_pf, default=0.0)  # Default 0 se vazio/inválido
    tensao_ter_kv = safe_float(tensao_ter_kv_str, default=0.0)  # Default 0 se vazio/inválido

    # Regras de validação
    validation_rules = {
        "Cap. AT (pF)": {"required": True, "min": 0},
        "Cap. BT (pF)": {"required": True, "min": 0},
        "Tensão AT (kV)": {"required": True, "positive": True},
        "Tensão BT (kV)": {"required": True, "positive": True},
        "Frequência (Hz)": {"required": True, "positive": True},
    }
    # Valida os inputs numéricos principais
    log.debug("[CALC Applied] Antes da validação...")
    num_inputs = {k: safe_float(v) for k, v in inputs.items()}
    errors = validate_dict_inputs(num_inputs, validation_rules)
    log.debug(f"[CALC Applied] Erros de validação: {errors}")

    # Validação adicional para terciário (se preenchido)
    if cap_ter_pf_val > 0 and (tensao_ter_kv is None or tensao_ter_kv <= 0):
        errors.append("Tensão Terciário (kV) é obrigatória e deve ser > 0 se Cap. Ter. > 0.")
    elif tensao_ter_kv > 0 and (cap_ter_pf_val is None or cap_ter_pf_val <= 0):
        errors.append("Cap. Terciário (pF) é obrigatória e deve ser > 0 se Tensão Ter. > 0.")

    if errors:
        log.warning(f"Erros de validação Tensão Aplicada: {errors}")
        error_msg = html.Ul(
            [html.Li(e) for e in errors], style={"color": "red", "fontSize": "0.7rem"}
        )
        return error_msg, "", no_update  # Retorna erro, sem recomendação, não atualiza store

    # --- Cálculos ---
    try:
        # Converte inputs validados com valores padrão para capacitâncias
        cap_at = num_inputs["Cap. AT (pF)"] or 1000  # Valor padrão de 1000 pF se for None
        cap_bt = num_inputs["Cap. BT (pF)"] or 1000  # Valor padrão de 1000 pF se for None
        tensao_at_kv = num_inputs["Tensão AT (kV)"]
        tensao_bt_kv = num_inputs["Tensão BT (kV)"]
        freq_hz = num_inputs["Frequência (Hz)"]
        # Usa valores já tratados para terciário
        cap_ter = cap_ter_pf_val or 0  # Garante que não seja None
        tensao_ter_kv = tensao_ter_kv  # Já é float ou 0.0

        # Log dos valores padrão usados
        if num_inputs["Cap. AT (pF)"] is None or num_inputs["Cap. AT (pF)"] == 0:
            log.info("[CALC Applied] Usando valor padrão para Cap. AT (pF): 1000 pF")
        if num_inputs["Cap. BT (pF)"] is None or num_inputs["Cap. BT (pF)"] == 0:
            log.info("[CALC Applied] Usando valor padrão para Cap. BT (pF): 1000 pF")

        # Registra os valores que serão usados nos cálculos
        print("=" * 80)
        print("[CALC Applied] VALORES USADOS NOS CÁLCULOS DE TENSÃO APLICADA:")
        print(f"[CALC Applied] Capacitância AT (pF): {cap_at}")
        print(f"[CALC Applied] Capacitância BT (pF): {cap_bt}")
        print(f"[CALC Applied] Capacitância Terciário (pF): {cap_ter}")
        print(f"[CALC Applied] Tensão AT (kV): {tensao_at_kv}")
        print(f"[CALC Applied] Tensão BT (kV): {tensao_bt_kv}")
        print(f"[CALC Applied] Tensão Terciário (kV): {tensao_ter_kv}")
        print(f"[CALC Applied] Frequência (Hz): {freq_hz}")
        print("=" * 80)

        # Calcula parâmetros para cada enrolamento
        # Assume que cap_at_pf, etc., são as capacitâncias *equivalentes* vistas pela fonte
        # durante o ensaio de cada enrolamento específico.

        # Adiciona capacitância fixa dependendo da tensão
        # Para tensão > 450 kV: adicionar 330 pF (capacitância do divisor de tensão)
        # Para tensão ≤ 450 kV: adicionar 660 pF (capacitância do divisor de tensão)
        cap_at_adicional = 330 if tensao_at_kv > 450 else 660
        cap_bt_adicional = 330 if tensao_bt_kv > 450 else 660
        cap_ter_adicional = 330 if tensao_ter_kv > 450 else 660

        cap_at_ajustado = cap_at + cap_at_adicional
        cap_bt_ajustado = cap_bt + cap_bt_adicional
        cap_ter_ajustado = cap_ter + cap_ter_adicional if cap_ter > 0 else 0

        log.debug(
            f"[CALC Applied] Capacitância AT ajustada: {cap_at} + {cap_at_adicional} = {cap_at_ajustado} pF (divisor de tensão)"
        )
        log.debug(
            f"[CALC Applied] Capacitância BT ajustada: {cap_bt} + {cap_bt_adicional} = {cap_bt_ajustado} pF (divisor de tensão)"
        )
        if cap_ter > 0:
            log.debug(
                f"[CALC Applied] Capacitância Terciário ajustada: {cap_ter} + {cap_ter_adicional} = {cap_ter_ajustado} pF (divisor de tensão)"
            )

        log.debug(
            f"[CALC Applied] Chamando calculate_capacitive_load para AT com cap_at={cap_at_ajustado}, tensao_at_kv={tensao_at_kv}, freq_hz={freq_hz}"
        )
        zc_at, i_at_ma, p_at_kvar = calculate_capacitive_load(
            cap_at_ajustado, tensao_at_kv * 1000, freq_hz
        )
        log.debug(
            f"[CALC Applied] calculate_capacitive_load para AT retornou: zc_at={zc_at}, i_at_ma={i_at_ma}, p_at_kvar={p_at_kvar}"
        )

        log.debug(
            f"[CALC Applied] Chamando calculate_capacitive_load para BT com cap_bt={cap_bt_ajustado}, tensao_bt_kv={tensao_bt_kv}, freq_hz={freq_hz}"
        )
        zc_bt, i_bt_ma, p_bt_kvar = calculate_capacitive_load(
            cap_bt_ajustado, tensao_bt_kv * 1000, freq_hz
        )
        log.debug(
            f"[CALC Applied] calculate_capacitive_load para BT retornou: zc_bt={zc_bt}, i_bt_ma={i_bt_ma}, p_bt_kvar={p_bt_kvar}"
        )

        if cap_ter_ajustado > 0:
            log.debug(
                f"[CALC Applied] Chamando calculate_capacitive_load para Terciário com cap_ter={cap_ter_ajustado}, tensao_ter_kv={tensao_ter_kv}, freq_hz={freq_hz}"
            )
            zc_ter, i_ter_ma, p_ter_kvar = calculate_capacitive_load(
                cap_ter_ajustado, tensao_ter_kv * 1000, freq_hz
            )
            log.debug(
                f"[CALC Applied] calculate_capacitive_load para Terciário retornou: zc_ter={zc_ter}, i_ter_ma={i_ter_ma}, p_ter_kvar={p_ter_kvar}"
            )
        else:
            zc_ter, i_ter_ma, p_ter_kvar = None, None, None
            log.debug("[CALC Applied] Terciário não calculado (cap_ter <= 0)")

        # --- Análise de Viabilidade ---
        # Usa as capacitâncias ajustadas para a análise de viabilidade
        cap_at_nf = cap_at_ajustado / 1000.0
        cap_bt_nf = cap_bt_ajustado / 1000.0
        cap_ter_nf = cap_ter_ajustado / 1000.0 if cap_ter_ajustado > 0 else 0.0

        analise_at = analyze_resonant_system_viability(cap_at_nf, tensao_at_kv, "AT")
        analise_bt = analyze_resonant_system_viability(cap_bt_nf, tensao_bt_kv, "BT")
        analise_ter = (
            analyze_resonant_system_viability(cap_ter_nf, tensao_ter_kv, "Terciário")
            if cap_ter_ajustado > 0
            else None
        )

        analise_enrolamentos = [analise_at, analise_bt]
        if analise_ter:
            analise_enrolamentos.append(analise_ter)

        # --- Montagem dos Resultados para UI ---
        # Tabela de Dados Calculados
        results_table_data = [
            ["Parâmetro", "AT", "BT", "Terciário"],
            [
                "Tensão Ensaio (kV)",
                f"{tensao_at_kv:.2f}",
                f"{tensao_bt_kv:.2f}",
                f"{tensao_ter_kv:.2f}" if tensao_ter_kv > 0 else "-",
            ],
            [
                "Cap. Informada (pF)",
                f"{cap_at:.0f}",
                f"{cap_bt:.0f}",
                f"{cap_ter:.0f}" if cap_ter > 0 else "-",
            ],
            [
                "Cap. Divisor (pF)",
                f"{cap_at_adicional}",
                f"{cap_bt_adicional}",
                f"{cap_ter_adicional}" if cap_ter > 0 else "-",
            ],
            [
                "Cap. Ajustada (pF)",
                f"{cap_at_ajustado:.0f}",
                f"{cap_bt_ajustado:.0f}",
                f"{cap_ter_ajustado:.0f}" if cap_ter_ajustado > 0 else "-",
            ],
            [
                "Corrente (mA)",
                format_parameter_value(i_at_ma, 2),
                format_parameter_value(i_bt_ma, 2),
                format_parameter_value(i_ter_ma, 2) if i_ter_ma else "-",
            ],
            [
                "Zc (Ω)",
                format_parameter_value(zc_at, 1),
                format_parameter_value(zc_bt, 1),
                format_parameter_value(zc_ter, 1) if zc_ter else "-",
            ],
            [
                "Potência Reativa (kVAr)",
                format_parameter_value(p_at_kvar, 3),
                format_parameter_value(p_bt_kvar, 3),
                format_parameter_value(p_ter_kvar, 3) if p_ter_kvar else "-",
            ],
        ]

        # Criação manual da tabela com estilos personalizados
        header = html.Thead(
            html.Tr(
                [
                    html.Th(
                        col,
                        style={
                            "fontSize": "0.7rem",
                            "padding": "0.2rem",
                            "backgroundColor": COLORS["background_card_header"],
                            "color": COLORS["text_light"],
                        },
                    )
                    for col in results_table_data[0]
                ]
            )
        )

        rows = []
        for i, row_data in enumerate(results_table_data[1:]):
            # Alterna cores de fundo para as linhas
            bg_color = "#4F4F4F" if i % 2 == 0 else "#3D3D3D"
            rows.append(
                html.Tr(
                    [
                        html.Td(
                            cell,
                            style={
                                "fontSize": "0.7rem",
                                "padding": "0.2rem",
                                "backgroundColor": bg_color,
                                "color": COLORS["text_light"],
                            },
                        )
                        for cell in row_data
                    ]
                )
            )

        results_table = dbc.Table(
            [header, html.Tbody(rows)],
            bordered=True,
            hover=True,
            size="sm",
            style={"backgroundColor": "#3D3D3D"},
        )

        # Display das Recomendações em 3 colunas
        # Cria as colunas para as recomendações
        colunas_recomendacoes = []
        for i, enr in enumerate(analise_enrolamentos):
            coluna = dbc.Col(
                [
                    dbc.Alert(
                        [
                            html.Strong(
                                f"{enr['enrolamento']} ({enr['viabilidade']}):",
                                className=f"text-{enr['cor_alerta']}",
                            ),
                            html.P(
                                enr["recommendation"],
                                style={
                                    "fontSize": "0.7rem",
                                    "marginBottom": "0.2rem",
                                    "color": COLORS["text_light"],
                                },
                            ),
                        ],
                        color=enr["cor_alerta"],
                        className="mb-1 p-1",
                        style={
                            "borderRadius": "4px",
                            "backgroundColor": "#3D3D3D",
                            "borderColor": "#6E6E6E",
                        },
                    )
                ],
                width=4,
            )  # Largura igual para cada coluna (4 de 12 = 1/3)
            colunas_recomendacoes.append(coluna)

        # Se houver menos de 3 colunas, adiciona colunas vazias para manter o layout
        while len(colunas_recomendacoes) < 3:
            colunas_recomendacoes.append(dbc.Col([], width=4))

        # Monta o layout final das recomendações
        recomendacoes_div = dbc.Row(colunas_recomendacoes)

        # --- Armazenar Dados no Store ---
        if current_store_data is None:
            current_store_data = {}
        # Guarda inputs e resultados formatados para PDF
        data_for_store = {
            "inputs": {  # Salva inputs originais da UI e do transformer_data
                "cap_at_pf": cap_at_pf,
                "cap_bt_pf": cap_bt_pf,
                "cap_ter_pf": cap_ter_pf,
                "cap_at_ajustado_pf": cap_at_ajustado,
                "cap_bt_ajustado_pf": cap_bt_ajustado,
                "cap_ter_ajustado_pf": cap_ter_ajustado,
                "tensao_at_kv": transformer_data.get(
                    "teste_tensao_aplicada_at"
                ),  # Usa valor do transformer_data
                "tensao_bt_kv": transformer_data.get(
                    "teste_tensao_aplicada_bt"
                ),  # Usa valor do transformer_data
                "tensao_ter_kv": transformer_data.get(
                    "teste_tensao_aplicada_terciario"
                ),  # Usa valor do transformer_data
                "frequencia_hz": frequencia_str,
            },
            "resultados": {
                "dados_calculo": {  # Salva resultados numéricos
                    "zc_at": zc_at,
                    "i_at": i_at_ma,
                    "p_at": p_at_kvar,
                    "zc_bt": zc_bt,
                    "i_bt": i_bt_ma,
                    "p_bt": p_bt_kvar,
                    "zc_ter": zc_ter,
                    "i_ter": i_ter_ma,
                    "p_ter": p_ter_kvar,
                    # Salva análise de viabilidade completa
                    "analise_enrolamentos": analise_enrolamentos,
                }
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Adicionar os inputs específicos para tensão aplicada conforme solicitado
        inputs_tensao_aplicada = {
            "capacitancia_at_pf": cap_at_pf,
            "capacitancia_bt_pf": cap_bt_pf,
            "capacitancia_terciario_pf": cap_ter_pf,
            "frequencia_teste_hz": frequencia_str,
        }

        # Adicionar logs detalhados para diagnóstico
        print("\n--- [APPLIED VOLTAGE STORE SAVE DEBUG] ---")
        log.info("--- [APPLIED VOLTAGE STORE SAVE DEBUG] ---")

        print(f"  Tipo de data_for_store: {type(data_for_store)}")
        if isinstance(data_for_store, dict):
            print(f"  Chaves principais: {list(data_for_store.keys())}")
            # Detalhar sub-dicionários importantes
            inputs = data_for_store.get("inputs", {})
            resultados = data_for_store.get("resultados", {})
            print(f"  inputs (tipo): {type(inputs).__name__}")
            if isinstance(inputs, dict):
                print(f"    inputs chaves: {list(inputs.keys())}")
            print(f"  resultados (tipo): {type(resultados).__name__}")
            if isinstance(resultados, dict):
                print(f"    resultados chaves: {list(resultados.keys())}")
                dados_calculo = resultados.get("dados_calculo", {})
                if isinstance(dados_calculo, dict):
                    print(f"      dados_calculo chaves: {list(dados_calculo.keys())}")
        else:
            print(f"  Conteúdo: {repr(data_for_store)[:100]}")

        # Atualizar o store com os novos dados
        current_store_data.update(data_for_store)

        # Adicionar os inputs específicos para tensão aplicada no store
        if "inputs_tensao_aplicada" not in current_store_data:
            current_store_data["inputs_tensao_aplicada"] = {}
        current_store_data["inputs_tensao_aplicada"].update(inputs_tensao_aplicada)

        print(f"  Tipo de current_store_data após update: {type(current_store_data)}")
        if isinstance(current_store_data, dict):
            print(f"  Chaves de current_store_data após update: {list(current_store_data.keys())}")
        else:
            print(f"  Conteúdo de current_store_data após update: {repr(current_store_data)[:100]}")

        print("--- Fim [APPLIED VOLTAGE STORE SAVE DEBUG] ---")

        # Registra os resultados dos cálculos nos logs
        print("=" * 80)
        print("[CALC Applied] RESULTADOS DOS CÁLCULOS DE TENSÃO APLICADA:")
        print(
            f"[CALC Applied] AT: Cap={cap_at:.0f}pF (Ajustada={cap_at_ajustado:.0f}pF), Zc={zc_at:.2f} Ω, I={i_at_ma:.2f} mA, P={p_at_kvar:.3f} kVAr"
        )
        print(
            f"[CALC Applied] BT: Cap={cap_bt:.0f}pF (Ajustada={cap_bt_ajustado:.0f}pF), Zc={zc_bt:.2f} Ω, I={i_bt_ma:.2f} mA, P={p_bt_kvar:.3f} kVAr"
        )
        if zc_ter is not None:
            print(
                f"[CALC Applied] Terciário: Cap={cap_ter:.0f}pF (Ajustada={cap_ter_ajustado:.0f}pF), Zc={zc_ter:.2f} Ω, I={i_ter_ma:.2f} mA, P={p_ter_kvar:.3f} kVAr"
            )

        # Registra a análise de viabilidade
        print("[CALC Applied] ANÁLISE DE VIABILIDADE:")
        for enr in analise_enrolamentos:
            print(
                f"[CALC Applied] {enr['enrolamento']} ({enr['viabilidade']}): {enr['recommendation']}"
            )
        print("=" * 80)

        # Combina a tabela de resultados com a nota explicativa
        resultados_completos = html.Div(
            [
                results_table,
                html.Div(
                    [
                        html.P(
                            "Nota: A capacitância ajustada inclui a capacitância do divisor de tensão:",
                            style={
                                "fontSize": "0.7rem",
                                "marginTop": "10px",
                                "marginBottom": "5px",
                                "fontWeight": "bold",
                                "color": COLORS["text_light"],
                            },
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    "330 pF para tensão > 450 kV",
                                    style={"fontSize": "0.7rem", "color": COLORS["text_light"]},
                                ),
                                html.Li(
                                    "660 pF para tensão ≤ 450 kV",
                                    style={"fontSize": "0.7rem", "color": COLORS["text_light"]},
                                ),
                            ],
                            style={"marginBottom": "10px", "paddingLeft": "20px"},
                        ),
                    ]
                ),
            ]
        )

        log.info("Cálculo de Tensão Aplicada e análise de viabilidade concluídos.")
        log.debug(
            f"[CALC Applied] Retornando: results_table={type(results_table)}, recomendacoes_div={type(recomendacoes_div)}, current_store_data={type(current_store_data)}"
        )
        return resultados_completos, recomendacoes_div, convert_numpy_types(current_store_data)

    except Exception as e:
        log.exception("Erro no callback calculate_and_analyze_applied_voltage.")
        error_msg = f"Erro inesperado no cálculo: {str(e)}"
        return dbc.Alert(error_msg, color="danger", style={"fontSize": "0.7rem"}), "", no_update


# Função para carregar dados iniciais quando a página é acessada
def load_applied_voltage_inputs(pathname, applied_voltage_store_data):
    """
    Carrega os valores de capacitância do store quando a página é acessada.
    """
    from dash import ctx
    from utils.routes import ROUTE_APPLIED_VOLTAGE, normalize_pathname

    triggered_id = ctx.triggered_id
    log.debug(f"[LOAD AppliedInputs] Acionado por: {triggered_id}, Pathname: {pathname}")

    clean_path = normalize_pathname(pathname) if pathname else ""
    if clean_path != ROUTE_APPLIED_VOLTAGE and triggered_id == 'url':
        log.debug(f"[LOAD AppliedInputs] Não na página de Tensão Aplicada ({clean_path}). Abortando trigger de URL.")
        raise dash.no_update

    # Se o trigger foi a mudança de URL e estamos na página correta, ou se foi a mudança do store, atualiza.
    if (triggered_id == 'url' and clean_path == ROUTE_APPLIED_VOLTAGE) or triggered_id == 'applied-voltage-store':
        if not applied_voltage_store_data or not isinstance(applied_voltage_store_data, dict):
            log.warning("[LOAD AppliedInputs] Store vazio ou inválido.")
            return None, None, None

        # Verificar múltiplas estruturas possíveis para compatibilidade
        cap_at = None
        cap_bt = None
        cap_ter = None

        # Verificar se os dados estão em 'inputs'
        if "inputs" in applied_voltage_store_data:
            inputs = applied_voltage_store_data.get("inputs", {})
            cap_at = inputs.get("cap_at_pf")
            cap_bt = inputs.get("cap_bt_pf")
            cap_ter = inputs.get("cap_ter_pf")
            log.debug(f"[LOAD AppliedInputs] Valores encontrados em 'inputs': cap_at={cap_at}, cap_bt={cap_bt}, cap_ter={cap_ter}")

        # Verificar se os dados estão diretamente no dicionário principal
        if cap_at is None and "cap_at_pf" in applied_voltage_store_data:
            cap_at = applied_voltage_store_data.get("cap_at_pf")
            log.debug(f"[LOAD AppliedInputs] Valor encontrado diretamente no dicionário principal: cap_at={cap_at}")

        if cap_bt is None and "cap_bt_pf" in applied_voltage_store_data:
            cap_bt = applied_voltage_store_data.get("cap_bt_pf")
            log.debug(f"[LOAD AppliedInputs] Valor encontrado diretamente no dicionário principal: cap_bt={cap_bt}")

        if cap_ter is None and "cap_ter_pf" in applied_voltage_store_data:
            cap_ter = applied_voltage_store_data.get("cap_ter_pf")
            log.debug(f"[LOAD AppliedInputs] Valor encontrado diretamente no dicionário principal: cap_ter={cap_ter}")

        log.info(f"[LOAD AppliedInputs] Valores carregados: cap_at={cap_at}, cap_bt={cap_bt}, cap_ter={cap_ter}")
        return cap_at, cap_bt, cap_ter

    raise dash.no_update


# Função para registrar todos os callbacks
def register_applied_voltage_callbacks(app):
    """
    Registra todos os callbacks relacionados à tensão aplicada.

    Args:
        app: A instância do aplicativo Dash
    """
    log.info("Registrando callbacks de tensão aplicada...")

    # Callback para atualizar as informações do transformador removido
    # Este callback foi removido pois a atualização é feita pelo callback global em global_updates.py

    # Callback para atualizar os displays de tensão e frequência
    app.callback(
        [
            Output("tensao-at-display", "children"),
            Output("tensao-bt-display", "children"),
            Output("tensao-terciario-display", "children"),
            Output("frequencia-display", "children"),
        ],
        [Input("transformer-inputs-store", "data")],
        prevent_initial_call=False,
    )(
        lambda transformer_data: ["-", "-", "-", "60 Hz"]
        if not transformer_data or not isinstance(transformer_data, dict)
        else [
            f"{transformer_data.get('teste_tensao_aplicada_at', '-')} kV",
            f"{transformer_data.get('teste_tensao_aplicada_bt', '-')} kV",
            f"{transformer_data.get('teste_tensao_aplicada_terciario', '-')} kV",
            f"{transformer_data.get('frequencia', 60)} Hz",
        ]
    )

    # Removido callback para preencher campos de tensão - agora usamos displays em vez de campos de entrada

    # Removido callback que causava ciclo de dependência

    # Callback para carregar dados iniciais quando a página é carregada
    app.callback(
        [
            Output("cap-at", "value"),
            Output("cap-bt", "value"),
            Output("cap-ter", "value"),
        ],
        [
            Input("url", "pathname"),
            Input("applied-voltage-store", "data"),
        ],
        prevent_initial_call=False,
    )(load_applied_voltage_inputs)

    # Callback principal para cálculo e análise de viabilidade
    app.callback(
        [
            Output("applied-voltage-results", "children"),
            Output("resonant-system-recommendation", "children"),
            Output("applied-voltage-store", "data"),
        ],
        [Input("calc-applied-voltage-btn", "n_clicks")],  # Usa o botão como gatilho
        [
            State("cap-at", "value"),
            State("cap-bt", "value"),
            State("cap-ter", "value"),
            State(
                "transformer-inputs-store", "data"
            ),  # Lê dados básicos para referência (incluindo frequência)
            State("applied-voltage-store", "data"),
        ],  # Lê estado atual do store
        prevent_initial_call=True,
    )(applied_voltage_calculate_and_analyze)

    log.info("Callbacks de tensão aplicada registrados com sucesso.")


# Código para teste quando o arquivo é executado diretamente
if __name__ == "__main__":
    print("Testando o módulo de tensão aplicada...")

    # Teste das funções auxiliares
    print("\nTestando a função safe_float:")
    test_values = [10, "20", "abc", None, ""]
    for val in test_values:
        result = safe_float(val)
        print(f"  safe_float({val}) = {result}")

    print(
        "\nTestando a função analyze_resonant_system_viability com prioridade para Módulos 1||2||3 (3 Par.):"
    )
    test_cases = [
        (
            0.5,
            100,
            "AT",
        ),  # Caso típico - Deve usar outra configuração (capacitância abaixo do mínimo para Módulos 1||2||3)
        (5.0, 500, "BT"),  # Tensão alta - Deve ser inviável (acima do máximo)
        (0.1, 50, "Terciário"),  # Capacitância baixa - Deve usar outra configuração
        (None, 100, "AT"),  # Valor inválido - Deve retornar erro
        # Testes específicos para Módulos 1||2||3 (3 Par.)
        (
            3.0,
            450,
            "AT",
        ),  # Dentro do range para Módulos 1||2||3 (3 Par.) 450kV - Deve ser recomendado
        (
            20.0,
            450,
            "BT",
        ),  # Dentro do range para Módulos 1||2||3 (3 Par.) 450kV - Deve ser recomendado
        (
            25.0,
            270,
            "Terciário",
        ),  # Dentro do range para Módulos 1||2||3 (3 Par.) 270kV - Deve ser recomendado
        (
            35.0,
            270,
            "AT",
        ),  # Dentro do range para Módulos 1||2||3 (3 Par.) 270kV - Deve ser recomendado
        # Testes de limites
        (
            1.9,
            450,
            "BT",
        ),  # Abaixo do mínimo para Módulos 1||2||3 (3 Par.) - Deve usar outra configuração
        (
            23.7,
            450,
            "Terciário",
        ),  # No limite entre as duas configurações - Deve usar Módulos 1||2||3 (3 Par.) 270kV
        (39.4, 270, "AT"),  # Acima do máximo para Módulos 1||2||3 (3 Par.) - Deve ser inviável
        (30.0, 300, "BT"),  # Tensão entre 270kV e 450kV - Deve ser inviável
    ]
    for cap, voltage, winding in test_cases:
        result = analyze_resonant_system_viability(cap, voltage, winding)
        print(f"  Análise para {winding}: Cap={cap}nF, Tensão={voltage}kV")
        print(f"    Resultado: {result['viabilidade']} - {result['recommendation']}")

    print("\nTeste concluído com sucesso!")
