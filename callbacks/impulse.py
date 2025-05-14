# callbacks/impulse.py
import logging
import math
import re
import warnings

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, html, ctx
from dash.exceptions import PreventUpdate
from scipy.fftpack import fft, fftfreq, ifft
from scipy.optimize import OptimizeWarning, curve_fit

# Import app instance and constants/utils
from app import app  # Import app instance correctly
from utils import constants as const  # Assuming constants are in utils.constants
from utils.routes import ROUTE_IMPULSE, normalize_pathname
from utils.store_diagnostics import convert_numpy_types, is_json_serializable

# --- Configuração do Logging ---
logger = logging.getLogger(__name__)
log = logger  # Alias para compatibilidade com outros módulos
# Ensure logger is configured (might be handled in app.py, but good practice)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --- Supressão de Warnings ---
warnings.filterwarnings("ignore", category=OptimizeWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Constantes Normativas e de Ensaio (Copied from user feedback) ---
LIGHTNING_IMPULSE_FRONT_TIME_NOM = 1.2
LIGHTNING_IMPULSE_TAIL_TIME_NOM = 50.0
SWITCHING_IMPULSE_PEAK_TIME_NOM = 250.0
SWITCHING_IMPULSE_TAIL_TIME_NOM = 2500.0
CHOPPED_IMPULSE_CHOP_TIME_MIN = 2.0
CHOPPED_IMPULSE_CHOP_TIME_MAX = 6.0
LIGHTNING_FRONT_TOLERANCE = 0.30
LIGHTNING_TAIL_TOLERANCE = 0.20
LIGHTNING_PEAK_TOLERANCE = 0.03
LIGHTNING_OVERSHOOT_MAX = 10.0
SWITCHING_PEAK_TOLERANCE = 0.03
SWITCHING_PEAK_TIME_TOLERANCE = 0.20
SWITCHING_TAIL_TOLERANCE = 0.60
SWITCHING_TIME_ABOVE_90_MIN = 200.0
SWITCHING_TIME_TO_ZERO_MIN = 1000.0
CHOPPED_FRONT_TOLERANCE = 0.30
CHOPPED_PEAK_TOLERANCE = 0.05
CHOPPED_UNDERSHOOT_MAX = 30.0

# --- Parâmetros Físicos e do Gerador (Copied from user feedback) ---
L_PER_STAGE_H = 5e-6
C_PER_STAGE = 1.5e-6
C_DIVIDER_HIGH_VOLTAGE = 600e-12
C_DIVIDER_LOW_VOLTAGE = 1200e-12
C_CHOPPING_GAP_PF = 600e-12  # Assuming this is pF, converting later
R_PARASITIC_OHM = 5.0

# --- Constantes Físicas ---
PI = np.pi
EPSILON_0 = 8.854e-12
MU_0 = 4 * PI * 1e-7

# --- Dados de referência para sugestão de resistores (Copied from user feedback) ---
RF_REFERENCE_DATA_LI = [(0.5, 500), (1, 350), (2, 220), (4, 140), (8, 90), (16, 60), (32, 40)]
RF_REFERENCE_DATA_SI = [
    (0.5, 5000),
    (1, 3500),
    (2, 2200),
    (4, 1400),
    (8, 900),
    (16, 600),
    (32, 400),
]
RT_DEFAULT_PER_COLUMN = {"lightning": 100, "switching": 2500, "chopped": 120}

# --- Funções Auxiliares (Copied from user feedback) ---


def parse_resistor_expression(expression):
    """
    Analisa uma expressão de configuração de resistores, suportando paralelo (||) e série (+).
    Retorna a resistência equivalente (ohms) e um dicionário com componentes especiais.
    """
    if not expression or not isinstance(expression, str) or expression.strip() == "":
        logger.warning("Expressão de resistor vazia ou inválida.")
        return float("inf"), {}

    expression = expression.lower().strip()
    special_components = {}

    cap_match = re.search(r"(\d+(?:\.\d+)?)\s*pf", expression)
    if cap_match:
        try:
            cap_value = float(cap_match.group(1)) * 1e-12
            special_components["coupling_capacitor"] = cap_value
            expression = re.sub(r"\|\|\s*\d+(?:\.\d+)?\s*pf", "", expression).strip()
            expression = re.sub(r"\d+(?:\.\d+)?\s*pf\s*\|\|", "", expression).strip()
            logger.info(
                f"Capacitor de acoplamento {cap_value*1e12:.0f} pF detectado em expressão Rf."
            )
        except ValueError:
            logger.error(f"Erro ao converter valor do capacitor em '{expression}'.")
            return float("inf"), {}

    try:
        expression_safe = expression.replace("||", "__parallel__")
        expression_safe = re.sub(r"(\d+(?:\.\d+)?)\s*k", r"(\1 * 1000)", expression_safe)
        expression_safe = re.sub(r"(\d+(?:\.\d+)?)\s*m", r"(\1 * 1000000)", expression_safe)

        def calculate_parallel(*args):
            if not args:
                return float("inf")
            args_float = []
            for r in args:
                try:
                    r_float = float(r)
                    if r_float <= 0:
                        continue
                    args_float.append(r_float)
                except (ValueError, TypeError):
                    continue
            if not args_float:
                return float("inf")
            inv_sum = sum(1.0 / r for r in args_float)
            return 1.0 / inv_sum if inv_sum > 1e-12 else float("inf")

        safe_dict = {"__parallel__": calculate_parallel, "__builtins__": None}
        series_parts = expression_safe.split("+")
        total_resistance = 0
        if not series_parts or all(not part.strip() for part in series_parts):
            logger.warning("Expressão de resistor sem partes válidas.")
            return float("inf"), special_components
        for part in series_parts:
            part = part.strip()
            if not part:
                continue
            if not re.match(r"^[\d\.\s\*\(\)/,__parallel__]+$", part):
                raise ValueError(f"Expressão de resistor contém caracteres inválidos: {part}")
            try:
                part_value = eval(part, {"__builtins__": {}}, safe_dict)
                if part_value <= 0 or math.isinf(part_value):
                    logger.warning(
                        f"Parte da expressão resultou em valor inválido: {part} -> {part_value}"
                    )
                    return float("inf"), special_components
                total_resistance += part_value
            except Exception as e:
                logger.error(f"Erro ao avaliar parte da expressão: {part}, erro: {e}")
                return float("inf"), special_components
        if total_resistance <= 0 or math.isinf(total_resistance):
            logger.warning(f"Resistência total inválida: {total_resistance}")
            return float("inf"), special_components
        return total_resistance, special_components
    except ZeroDivisionError:
        logger.error(f"Divisão por zero ao calcular resistência paralela em '{expression}'.")
        return float("inf"), special_components
    except Exception as e:
        logger.error(f"Erro ao analisar expressão de resistor '{expression}': {e}")
        return float("inf"), special_components


def get_generator_params(config_value):
    """Obtém os parâmetros de uma configuração específica do gerador."""
    config = next(
        (item for item in const.GENERATOR_CONFIGURATIONS if item["value"] == config_value), None
    )
    if config:
        energy_kj = config.get("energy_kj")
        try:
            energy_kj_float = float(energy_kj) if energy_kj is not None else 0.0
        except (ValueError, TypeError):
            logger.warning(
                f"Valor de energia inválido para config '{config_value}': {energy_kj}. Usando 0."
            )
            energy_kj_float = 0.0
        return config["stages"], config["parallel"], config["max_voltage_kv"], energy_kj_float
    logger.warning(
        f"Configuração do gerador '{config_value}' não encontrada. Usando padrão 12S-1P."
    )
    default_config = next(
        (item for item in const.GENERATOR_CONFIGURATIONS if item["value"] == "12S-1P"), None
    )
    if default_config:
        energy_kj = default_config.get("energy_kj")
        energy_kj_float = float(energy_kj) if energy_kj is not None else 360.0
        return (
            default_config["stages"],
            default_config["parallel"],
            default_config["max_voltage_kv"],
            energy_kj_float,
        )
    else:
        return 12, 1, 2400, 360.0


def get_divider_capacitance(generator_config_value):
    """Retorna a capacitância do divisor baseada na tensão MÁXIMA da configuração."""
    try:
        _, _, max_voltage_kv, _ = get_generator_params(generator_config_value)
        if max_voltage_kv <= 1200:
            return C_DIVIDER_LOW_VOLTAGE
        else:
            return C_DIVIDER_HIGH_VOLTAGE
    except Exception as e:
        logger.error(f"Erro ao obter capacitância do divisor: {e}. Usando padrão.")
        return C_DIVIDER_HIGH_VOLTAGE


def calculate_effective_gen_params(n_stages, n_parallel):
    """Calcula a capacitância efetiva do gerador."""
    if n_stages <= 0 or n_parallel <= 0:
        logger.error("Número de estágios/paralelo deve ser positivo.")
        return 0
    c_gen_effective = (C_PER_STAGE * n_parallel) / n_stages
    logger.debug(f"Cg_eff calculado: {c_gen_effective*1e6:.3f} µF para {n_stages}S-{n_parallel}P")
    return c_gen_effective


def calculate_transformer_inductance(voltage_kv, power_mva, impedance_percent, freq_hz=60):
    """Calcula a indutância do transformador a partir de seus parâmetros nominais."""
    if voltage_kv is None or power_mva is None or impedance_percent is None or freq_hz is None:
        return 0.05
    try:
        voltage_v = float(voltage_kv) * 1000
        power_va = float(power_mva) * 1e6
        impedance_pu = float(impedance_percent) / 100.0
        freq_hz = float(freq_hz)
        if voltage_v <= 0 or power_va <= 0 or freq_hz <= 0:
            return 0.05
        omega = 2 * np.pi * freq_hz
        z_base = (voltage_v**2) / power_va
        z_cc_ohm = z_base * impedance_pu
        l_cc = z_cc_ohm / omega
        logger.info(f"Indutância do trafo calculada: {l_cc:.4f} H")
        return l_cc
    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.error(f"Erro ao calcular indutância do trafo: {e}. Usando 0.05H.")
        return 0.05


def calculate_circuit_efficiency(
    n_stages, n_parallel, c_test_object_pf, c_stray_pf, impulse_type, generator_config_value
):
    """Calcula a eficiência do circuito de impulso."""
    try:
        c_gen_effective = calculate_effective_gen_params(n_stages, n_parallel)
        c_divider_f = get_divider_capacitance(generator_config_value)
        c_test_object_f = c_test_object_pf * 1e-12 if c_test_object_pf is not None else 0
        c_stray_f = c_stray_pf * 1e-12 if c_stray_pf is not None else 0
        c_load_extra_f = (
            C_CHOPPING_GAP_PF * 1e-12 if impulse_type == "chopped" else 0
        )  # Convert pF to F
        c_load = c_test_object_f + c_divider_f + c_load_extra_f + c_stray_f
        circuit_efficiency = (
            c_gen_effective / (c_gen_effective + c_load)
            if (c_gen_effective + c_load) > 1e-15
            else 0
        )
        shape_efficiency = 0.95 if impulse_type in ["lightning", "chopped"] else 0.85  # Ajustado SI
        total_efficiency = circuit_efficiency * shape_efficiency
        logger.debug(
            f"Eficiência: Total={total_efficiency:.3f}, Circuito={circuit_efficiency:.3f}, Forma={shape_efficiency:.2f}"
        )
        return total_efficiency, circuit_efficiency, shape_efficiency, c_load
    except Exception as e:
        logger.exception(f"Erro ao calcular eficiência: {e}")
        return 0, 0, 0, 0


def calculate_energy_requirements(actual_test_voltage_kv, c_load_f):
    """Calcula a energia requerida pela carga durante o ensaio."""
    try:
        if actual_test_voltage_kv is None or c_load_f is None:
            return 0.0
        test_voltage_v = float(actual_test_voltage_kv) * 1000
        c_load_f = float(c_load_f)
        if c_load_f < 0:
            return 0.0
        energy_joules = 0.5 * c_load_f * (test_voltage_v**2)
        energy_kj = energy_joules / 1000
        logger.debug(
            f"Energia requerida pela carga @ {actual_test_voltage_kv:.1f} kV: {energy_kj:.2f} kJ"
        )
        return energy_kj
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao calcular energia requerida: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Erro não esperado ao calcular energia: {e}")
        return 0.0


def _calculate_waveform_parameters(
    n_stages,
    n_parallel,
    rf_per_column,
    rt_per_column,
    c_test_object_pf,
    c_stray_pf,
    l_extra_h,
    transformer_inductance_h,
    inductor_value_h,
    impulse_type,
    generator_config_value,
    inductance_factor=1.0,
    tail_resistance_factor=1.0,
):
    """Calcula os parâmetros RLC equivalentes do circuito, aplicando fatores de ajuste."""
    logger.debug(f"Calculando parâmetros para {n_stages}S-{n_parallel}P, Tipo: {impulse_type}")
    c_gen_effective = calculate_effective_gen_params(n_stages, n_parallel)
    c_divider_f = get_divider_capacitance(generator_config_value)
    c_test_object_f = c_test_object_pf * 1e-12 if c_test_object_pf is not None else 0
    c_stray_f = c_stray_pf * 1e-12 if c_stray_pf is not None else 0
    c_load_extra_f = (
        C_CHOPPING_GAP_PF * 1e-12 if impulse_type == "chopped" else 0
    )  # Convert pF to F
    c_load = c_test_object_f + c_divider_f + c_load_extra_f + c_stray_f
    c_eq = (
        (c_gen_effective * c_load) / (c_gen_effective + c_load)
        if (c_gen_effective + c_load) > 1e-15
        else 0
    )
    rf_total_initial = (rf_per_column * n_stages) / n_parallel if n_parallel > 0 else float("inf")
    rt_total_initial = (rt_per_column * n_stages) / n_parallel if n_parallel > 0 else float("inf")
    l_gen = (L_PER_STAGE_H * n_stages) / n_parallel if n_parallel > 0 else 0
    l_total_initial = l_gen + l_extra_h + transformer_inductance_h + inductor_value_h
    logger.debug(
        f"Cálculo completo de l_total_initial: l_gen={l_gen:.3e}, l_extra_h={l_extra_h:.3e}, transformer_inductance_h={transformer_inductance_h:.3e}, inductor_value_h={inductor_value_h:.3e}"
    )
    rf_total = rf_total_initial
    l_total = l_total_initial * inductance_factor
    rt_total = rt_total_initial * tail_resistance_factor
    logger.debug(
        f"Parâmetros RLC Efetivos (Ajustados): Rf={rf_total:.2f}, Rt={rt_total:.2f}, L={l_total:.3e}, Cg={c_gen_effective:.3e}, Cl={c_load:.3e}, Ceq={c_eq:.3e}"
    )
    alpha = (
        1 / (rt_total * (c_gen_effective + c_load))
        if rt_total > 1e-9 and (c_gen_effective + c_load) > 1e-15
        else 0
    )
    beta = 1 / (rf_total * c_eq) if rf_total > 1e-9 and c_eq > 1e-15 else 0
    if beta <= alpha + 1e-9:
        adjust_factor = 1.05
        add_factor = 1e3
        new_beta = alpha * adjust_factor + add_factor
        logger.warning(
            f"Beta ({beta:.2e}) <= Alpha ({alpha:.2e}). Ajustando Beta para {new_beta:.2e}"
        )
        beta = new_beta
    r_eq_damping = rf_total + R_PARASITIC_OHM
    omega0 = 1 / math.sqrt(l_total * c_eq) if l_total * c_eq > 1e-18 else 0
    zeta = r_eq_damping / (2 * l_total * omega0) if l_total * omega0 > 1e-9 else float("inf")
    is_oscillatory = zeta < 1.0 if omega0 > 0 else False
    logger.debug(
        f"Alpha={alpha:.2e}, Beta={beta:.2e}, Zeta={zeta:.3f}, Oscilatório={is_oscillatory}"
    )
    return (
        c_gen_effective,
        c_load,
        rf_total,
        rt_total,
        c_eq,
        alpha,
        beta,
        l_total,
        is_oscillatory,
        zeta,
    )


# --- Funções de Simulação da Forma de Onda (Copied from user feedback) ---


def rlc_solution(t_sec, v0, r_total, l_total, c_eq):
    """Calcula a solução para o circuito RLC série em função do tempo."""
    if l_total <= 1e-12 or c_eq <= 1e-15 or r_total <= 1e-9:
        logger.warning(f"Parâmetros RLC inválidos: R={r_total}, L={l_total}, Ceq={c_eq}")
        return np.zeros_like(t_sec)
    try:
        omega0_sq = 1.0 / (l_total * c_eq)
        alpha_damp = r_total / (2.0 * l_total)
        if alpha_damp <= 0:
            logger.warning("Amortecimento RLC não positivo.")
            return np.zeros_like(t_sec)
        delta = alpha_damp**2 - omega0_sq
        v_out = np.zeros_like(t_sec)
        t_valid = t_sec[t_sec >= 0]
        if abs(delta) < 1e-12 * omega0_sq:
            a = alpha_damp
            v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
        elif delta < 0:
            omega_d = np.sqrt(-delta)
            a = alpha_damp
            v_out[t_sec >= 0] = (
                v0
                * np.exp(-a * t_valid)
                * (np.cos(omega_d * t_valid) + (a / omega_d) * np.sin(omega_d * t_valid))
                if omega_d > 1e-9
                else v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
            )
        else:
            sqrt_delta = np.sqrt(delta)
            s1 = -alpha_damp + sqrt_delta
            s2 = -alpha_damp - sqrt_delta
            if abs(s1 - s2) < 1e-9 * abs(s1 + s2):
                a = alpha_damp
                v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
            else:
                if s1 > 1e-9 or s2 > 1e-9:
                    logger.warning(f"Raízes instáveis RLC: s1={s1:.2e}, s2={s2:.2e}.")
                    v_out = (
                        np.zeros_like(t_sec)
                        if s2 >= 0
                        else v0 / (s1 - s2) * (-s2 * np.exp(s1 * t_valid))
                    )
                else:
                    v_out[t_sec >= 0] = (
                        v0 / (s1 - s2) * (s1 * np.exp(s2 * t_valid) - s2 * np.exp(s1 * t_valid))
                    )
        v_out[t_sec < 0] = 0
        return v_out
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        logger.error(f"Erro solução RLC: {e}")
        return np.zeros_like(t_sec)


def double_exp_func(t, V0_norm, alpha, beta):
    """Função de dupla exponencial normalizada para ter pico V0_norm."""
    if alpha <= 1e-12 or beta <= 1e-12 or beta <= alpha + 1e-9:
        logger.warning(f"Alpha/Beta inválidos: a={alpha:.2e}, b={beta:.2e}")
        return np.zeros_like(t)
    try:
        t_peak = math.log(beta / alpha) / (beta - alpha) if beta > alpha else 0
        norm_factor = (math.exp(-alpha * t_peak) - math.exp(-beta * t_peak)) if t_peak >= 0 else 0
        if abs(norm_factor) < 1e-12:
            logger.warning("Fator norm. dupla exp zero.")
            return np.zeros_like(t)
        k_norm = V0_norm / norm_factor
        t_safe = np.maximum(t, 0)
        result = k_norm * (np.exp(-alpha * t_safe) - np.exp(-beta * t_safe))
        return result
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        logger.error(f"Erro dupla exp: {e}")
        return np.zeros_like(t)


def calculate_k_factor_transform(v, t, return_params=False):
    """Aplica a transformação K-factor conforme IEC 61083-2."""
    v_test = np.copy(v)
    v_base = np.copy(v)
    v_residual_filtered = np.zeros_like(v)
    overshoot_rel = 0.0
    v_base_success = False
    alpha_fit, beta_fit = None, None
    if len(v) < 10 or len(t) < 10 or np.std(v) < 1e-9 or t[-1] <= t[0]:
        logger.warning("Dados insuficientes/inválidos para k-factor.")
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )
    peak_value_orig = np.max(v)
    if peak_value_orig < 1e-6:
        logger.warning("Amplitude baixa para k-factor.")
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )

    def double_exp_func_fit(t_fit, A_norm, alpha, beta):
        if alpha <= 1e-12 or beta <= 1e-12 or beta <= alpha + 1e-9:
            return np.full_like(t_fit, 1e12)
        try:
            t_peak = math.log(beta / alpha) / (beta - alpha) if beta > alpha else 0
            norm_factor = math.exp(-alpha * t_peak) - math.exp(-beta * t_peak) if t_peak >= 0 else 0
            if abs(norm_factor) < 1e-12:
                return np.zeros_like(t_fit)
            k_norm = A_norm / norm_factor
            t_safe = np.maximum(t_fit, 0)
            result = k_norm * (np.exp(-alpha * t_safe) - np.exp(-beta * t_safe))
            return result
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            logger.error(f"Erro interno dupla exp ajuste: {e}")
            return np.full_like(t_fit, 1e12)

    try:
        t_sec = t * 1e-6
        peak_idx = np.argmax(v)
        t_half_idx = (
            np.argmin(np.abs(v[peak_idx:] - 0.5 * peak_value_orig)) + peak_idx
            if peak_idx < len(v) - 1
            else len(v) - 1
        )
        T2_approx_sec = max(1e-7, t_sec[t_half_idx])
        t_30_idx = (
            np.argmin(np.abs(v[: peak_idx + 1] - 0.3 * peak_value_orig)) if peak_idx > 0 else 0
        )
        t_90_idx = (
            np.argmin(np.abs(v[: peak_idx + 1] - 0.9 * peak_value_orig))
            if peak_idx > 0
            else peak_idx
        )
        T1_approx_sec = (
            (1.67 / 1e6) * max(1e-3, (t[t_90_idx] - t[t_30_idx]))
            if t_90_idx > t_30_idx
            else (LIGHTNING_IMPULSE_FRONT_TIME_NOM * 1e-6)
        )
        T1_approx_sec = max(0.1e-6, T1_approx_sec)
        alpha_est = 0.7 / T2_approx_sec if T2_approx_sec > 1e-9 else 1e7
        beta_est = 2.5 / T1_approx_sec if T1_approx_sec > 1e-9 else 1e8
        if beta_est <= alpha_est:
            beta_est = alpha_est * 5
        A_est = peak_value_orig
        lower_bounds = [peak_value_orig * 0.5, alpha_est * 0.1, beta_est * 0.5]
        upper_bounds = [peak_value_orig * 1.5, alpha_est * 10, beta_est * 10]
        popt, pcov = curve_fit(
            double_exp_func_fit,
            t_sec,
            v,
            p0=[A_est, alpha_est, beta_est],
            bounds=(lower_bounds, upper_bounds),
            maxfev=5000,
            method="trf",
        )
        A_fit, alpha_fit, beta_fit = popt
        logger.debug(
            f"Ajuste curva base: A={A_fit:.2f}, alpha={alpha_fit:.2e}, beta={beta_fit:.2e}"
        )
        v_base = double_exp_func_fit(t_sec, A_fit, alpha_fit, beta_fit)
        v_base_success = True
    except (RuntimeError, ValueError, Exception) as e:
        logger.warning(f"Ajuste curva base K-Factor falhou: {e}. Usando onda original.")
        v_base = np.copy(v)
        v_base_success = False
        alpha_fit, beta_fit = None, None
    v_base = np.maximum(v_base, 0)
    v_residual = v - v_base
    v_residual_filtered = np.zeros_like(v_residual)
    if len(t) > 1 and abs(t[1] - t[0]) > 1e-12 and v_base_success:
        try:
            dt_fft = (t[1] - t[0]) * 1e-6
            frequencies = fftfreq(len(t), dt_fft)
            v_residual_fft = fft(v_residual)
            k_factor_filter = np.ones_like(frequencies, dtype=complex)
            f_MHz = np.abs(frequencies) * 1e-6
            f_MHz_sq = f_MHz**2
            non_zero_freq_mask = f_MHz_sq > 1e-12
            denominator = 1.0 + 2.2 * f_MHz_sq[non_zero_freq_mask]
            filter_values = np.divide(
                1.0, denominator, where=denominator > 1e-12, out=np.zeros_like(denominator)
            )
            k_factor_filter[non_zero_freq_mask] = filter_values
            v_residual_filtered_fft = v_residual_fft * k_factor_filter
            v_residual_filtered = np.real(ifft(v_residual_filtered_fft))
        except Exception as e_fft:
            logger.error(f"Erro FFT/IFFT K-factor: {e_fft}.")
            v_residual_filtered = np.zeros_like(v_residual)
    elif not v_base_success:
        logger.info("K-factor não aplicado (ajuste base falhou).")
        v_residual_filtered = np.zeros_like(v)
    else:
        logger.warning("Vetor tempo inválido para FFT K-factor.")
        v_residual_filtered = np.zeros_like(v_residual)
    v_test = v_base + v_residual_filtered
    v_test = np.maximum(v_test, 0)
    peak_value_base = np.max(v_base) if len(v_base) > 0 else 0
    overshoot_rel = 0.0
    if peak_value_orig > 1e-9 and peak_value_base > 1e-9:
        overshoot_rel = max(0.0, (peak_value_orig - peak_value_base) / peak_value_orig) * 100
    if return_params:
        return v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit)
    return v_test, v_base, v_residual_filtered, overshoot_rel


def simulate_hybrid_impulse(
    t_sec, v0_charge, rf, rt, l_total, c_gen, c_load, impulse_type, gap_distance_cm=None
):
    """Simula o circuito usando a abordagem híbrida RLC + K-Factor + Dupla Exp."""
    collapse_time = 0.1e-6
    logger.info(f"Simulando Híbrido: Tipo={impulse_type}, V0_carga={v0_charge/1000:.1f}kV")
    c_eq = (c_gen * c_load) / (c_gen + c_load) if (c_gen + c_load) > 1e-15 else 0
    r_rlc = rf + R_PARASITIC_OHM
    logger.debug(f"Simulando RLC: R={r_rlc:.1f}, L={l_total:.2e}, Ceq={c_eq:.2e}")
    v_rlc = rlc_solution(t_sec, v0_charge, r_rlc, l_total, c_eq)
    v_rlc_kv = v_rlc / 1000
    t_us = t_sec * 1e6
    v_test, v_base, _, overshoot, (alpha_fit, beta_fit) = calculate_k_factor_transform(
        v_rlc_kv, t_us, return_params=True
    )
    if alpha_fit is None or beta_fit is None:
        logger.warning("Ajuste K-factor falhou. Usando estimativas.")
        alpha = 1 / (rt * (c_gen + c_load)) if rt > 1e-9 and (c_gen + c_load) > 1e-15 else 0
        beta = 1 / (rf * c_eq) if rf > 1e-9 and c_eq > 1e-15 else 0
        if beta <= alpha + 1e-9:
            adjust_factor = 1.05
            add_factor = 1e3 if impulse_type in ["lightning", "chopped"] else 1e2
            beta = alpha * adjust_factor + add_factor
    else:
        alpha = alpha_fit
        beta = beta_fit
        logger.info(f"Parâmetros K-factor: alpha={alpha:.2e}, beta={beta:.2e}")
    v_final = double_exp_func(t_sec, v0_charge, alpha, beta)
    chop_time_sec = None
    if impulse_type == "chopped" and gap_distance_cm is not None and gap_distance_cm > 0:
        breakdown_voltage = 30.0 * gap_distance_cm * 1000
        times_above_threshold = np.where(v_final >= breakdown_voltage)[0]
        if len(times_above_threshold) > 0:
            chop_idx = times_above_threshold[0]
            if chop_idx < len(t_sec):
                chop_time_sec = t_sec[chop_idx]
                logger.info(
                    f"Corte detectado: t={chop_time_sec*1e6:.2f} µs, V={v_final[chop_idx]/1000:.1f} kV"
                )
                collapse_idx = np.where(t_sec >= chop_time_sec)[0]
                if len(collapse_idx) > 0:
                    chop_voltage_final = v_final[chop_idx]
                    dt_after_chop = t_sec[collapse_idx] - chop_time_sec
                    mask_collapse = dt_after_chop <= collapse_time
                    mask_osc = dt_after_chop > collapse_time
                    idx_collapse = collapse_idx[mask_collapse]
                    idx_osc = collapse_idx[mask_osc]
                    if len(idx_collapse) > 0:
                        v_final[idx_collapse] = chop_voltage_final * (
                            1 - (t_sec[idx_collapse] - chop_time_sec) / collapse_time
                        )
                    if len(idx_osc) > 0:
                        freq_osc = 5e6
                        damp_factor = 1.5
                        undershoot_ratio = 0.25
                        time_after_collapse = t_sec[idx_osc] - chop_time_sec - collapse_time
                        amp = (
                            -chop_voltage_final
                            * undershoot_ratio
                            * np.exp(-damp_factor * time_after_collapse * 1e6)
                        )
                        osc = amp * np.cos(2 * np.pi * freq_osc * time_after_collapse)
                        v_final[idx_osc] = osc
                        v_final[idx_osc] = np.clip(
                            v_final[idx_osc], -0.3 * abs(chop_voltage_final), float("inf")
                        )
                        v_final[idx_osc[time_after_collapse > 3 / freq_osc]] = 0
        else:
            logger.warning(
                f"Tensão não atingiu breakdown ({breakdown_voltage/1000:.1f} kV) para gap={gap_distance_cm} cm"
            )
    i_load = c_load * np.gradient(v_final, t_sec)
    return v_rlc, v_final, i_load, alpha, beta, chop_time_sec


def analyze_lightning_impulse(t_us, v_kv):
    """
    Analisa os parâmetros de um impulso atmosférico (LI) a partir dos dados simulados ou medidos.
    Aplica o K-factor para obter a curva de ensaio Vt(t).
    Calcula T1, T2, Vp (Vt), Overshoot (β).
    Verifica conformidade com as tolerâncias da IEC 60060-1.

    Args:
        t_us: Array de tempo em microssegundos (µs).
        v_kv: Array de tensão em quilovolts (kV).

    Returns:
        Dicionário contendo os parâmetros calculados e flags de conformidade.
        Retorna {"error": msg} em caso de falha na análise.
    """
    logger.info("Analisando Impulso Atmosférico (LI)...")
    results = {
        "peak_value": None,
        "test_value": None,
        "base_value": None,
        "peak_time": None,
        "t_30": None,
        "t_90": None,
        "t_0_virtual": None,
        "t_front": None,
        "t_tail": None,
        "overshoot": 0.0,
        "conforme_frente": False,
        "conforme_cauda": False,
        "conforme_overshoot": True,
        "conforme_pico": False,
        "error": None,
    }

    try:
        if (
            v_kv is None
            or t_us is None
            or len(v_kv) < 10
            or len(t_us) != len(v_kv)
            or np.std(v_kv) < 1e-9
        ):
            results["error"] = "Dados de entrada inválidos ou insuficientes para análise LI."
            logger.error(results["error"])
            return results

        # 1. Aplica Transformação K-Factor
        v_test_kv, v_base_kv, _, overshoot_rel = calculate_k_factor_transform(v_kv, t_us)

        if v_test_kv is None or len(v_test_kv) < 5 or np.std(v_test_kv) < 1e-9:
            results["error"] = "Onda de ensaio (V_test) inválida após K-factor."
            logger.error(results["error"])
            # Tenta analisar a onda original como fallback
            v_test_kv = v_kv  # Usa a onda original se K-factor falhar
            overshoot_rel = 0.0  # Assume zero overshoot se K-factor falhar
            logger.warning("K-Factor falhou, análise LI será feita na onda original.")
            # Não retorna erro ainda, tenta analisar o que for possível

        results["overshoot"] = overshoot_rel
        results["peak_value"] = np.max(v_kv) if len(v_kv) > 0 else 0
        results["base_value"] = np.max(v_base_kv) if len(v_base_kv) > 0 else 0

        # 2. Encontra o Pico da Curva de Ensaio (Vt)
        test_peak_idx = np.argmax(v_test_kv)
        test_peak_time_us = t_us[test_peak_idx]
        test_peak_value_kv = v_test_kv[test_peak_idx]
        results["test_value"] = test_peak_value_kv
        results["peak_time"] = test_peak_time_us

        # 3. Análise da Frente (T1 e O1)
        t_0_virtual_us = t_us[0]  # Padrão: origem real
        mask_before_peak = t_us <= test_peak_time_us
        t_before_us = t_us[mask_before_peak]
        v_before_kv = v_test_kv[mask_before_peak]

        if (
            len(v_before_kv) > 1 and test_peak_value_kv > 1e-6
        ):  # Evita divisão por zero se pico for zero
            v_max_before = np.max(v_before_kv)
            v_min_before = np.min(v_before_kv)
            v_30_target = 0.3 * test_peak_value_kv
            v_90_target = 0.9 * test_peak_value_kv

            if v_max_before >= v_90_target and v_min_before <= v_30_target:
                try:
                    t_30_us = np.interp(
                        v_30_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    t_90_us = np.interp(
                        v_90_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    results["t_30"] = t_30_us
                    results["t_90"] = t_90_us

                    if not np.isnan(t_30_us) and not np.isnan(t_90_us) and t_90_us > t_30_us:
                        delta_t_front = t_90_us - t_30_us
                        delta_v_front = v_90_target - v_30_target
                        if delta_t_front > 1e-9:
                            results["t_front"] = 1.67 * delta_t_front
                            slope = delta_v_front / delta_t_front
                            if abs(slope) > 1e-9:
                                t_0_virtual_us = t_30_us - (v_30_target / slope)
                            else:
                                t_0_virtual_us = t_30_us
                        else:
                            logger.warning("Intervalo t90-t30 muito pequeno para T1.")
                            results["t_front"] = None
                    else:
                        logger.warning("Não foi possível interpolar t30 ou t90 na frente.")
                        results["t_front"] = None
                except Exception as e_interp_front:
                    logger.error(f"Erro interpolação frente LI: {e_interp_front}")
                    results["t_front"] = None
            else:
                logger.warning("Níveis 30%/90% não encontrados antes do pico.")
        results["t_0_virtual"] = t_0_virtual_us

        # 4. Análise da Cauda (T2)
        mask_after_peak = t_us >= test_peak_time_us
        t_after_us = t_us[mask_after_peak]
        v_after_kv = v_test_kv[mask_after_peak]
        v_50_target = 0.5 * test_peak_value_kv

        if (
            len(v_after_kv) > 1 and np.min(v_after_kv) <= v_50_target + 1e-6
        ):  # Adiciona tolerância pequena
            try:
                indices_below_50 = np.where(v_after_kv <= v_50_target)[0]
                if len(indices_below_50) > 0:
                    idx2 = indices_below_50[0]
                    idx1 = idx2 - 1 if idx2 > 0 else 0
                    t1_tail, v1_tail = t_after_us[idx1], v_after_kv[idx1]
                    t2_tail, v2_tail = t_after_us[idx2], v_after_kv[idx2]
                    if abs(v2_tail - v1_tail) > 1e-9:
                        t_50_us = t1_tail + (v_50_target - v1_tail) * (t2_tail - t1_tail) / (
                            v2_tail - v1_tail
                        )
                        if not np.isnan(t_50_us):
                            results["t_tail"] = t_50_us - t_0_virtual_us
                    elif v1_tail >= v_50_target:
                        results["t_tail"] = t1_tail - t_0_virtual_us
                else:
                    logger.warning("Não encontrou ponto < 50% na cauda (lógica np.where).")
            except Exception as e_interp_tail:
                logger.error(f"Erro interpolação cauda LI: {e_interp_tail}")
                results["t_tail"] = None
        else:
            logger.warning("Dados insuficientes ou tensão não caiu abaixo de 50% na cauda.")

        # 5. Verificação de Conformidade
        if results["t_front"] is not None:
            t1_min = LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 - LIGHTNING_FRONT_TOLERANCE)
            t1_max = LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 + LIGHTNING_FRONT_TOLERANCE)
            results["conforme_frente"] = t1_min <= results["t_front"] <= t1_max
        if results["t_tail"] is not None:
            t2_min = LIGHTNING_IMPULSE_TAIL_TIME_NOM * (1 - LIGHTNING_TAIL_TOLERANCE)
            t2_max = LIGHTNING_IMPULSE_TAIL_TIME_NOM * (1 + LIGHTNING_TAIL_TOLERANCE)
            results["conforme_cauda"] = t2_min <= results["t_tail"] <= t2_max
        results["conforme_overshoot"] = results["overshoot"] <= LIGHTNING_OVERSHOOT_MAX
        results["conforme_pico"] = (
            results["test_value"] is not None
        )  # Conformidade do pico é apenas se ele foi calculado

        logger.info(
            f"Análise LI: Vt={results.get('test_value', 'N/A'):.2f} kV, T1={results.get('t_front', 'N/A'):.2f} µs, T2={results.get('t_tail', 'N/A'):.1f} µs, β={results.get('overshoot', 'N/A'):.1f}%"
        )
        logger.info(
            f"Conformidade LI: Frente={results['conforme_frente']}, Cauda={results['conforme_cauda']}, Overshoot={results['conforme_overshoot']}"
        )
        return results
    except Exception as e:
        logger.exception(f"Erro geral em analyze_lightning_impulse: {e}")
        return {"error": str(e)}


def analyze_switching_impulse(t_us, v_kv):
    """Analisa os parâmetros de um impulso de manobra (SI) conforme IEC 60060-1."""
    logger.info("Analisando Impulso de Manobra (SI)...")
    results = {
        "peak_value": None,
        "peak_time": None,
        "tp": None,
        "td": None,
        "t_half": None,
        "t2_calculated": None,
        "tz": None,
        "tz_calculated": None,
        "T_AB": None,
        "t_30": None,
        "t_90": None,
        "conforme_pico": False,
        "conforme_meia_onda": False,
        "conforme_td": False,
        "conforme_tz": False,
        "error": None,
    }
    try:
        if (
            v_kv is None
            or t_us is None
            or len(v_kv) < 10
            or len(t_us) != len(v_kv)
            or np.std(v_kv) < 1e-9
        ):
            results["error"] = "Dados de entrada inválidos ou insuficientes para análise SI."
            logger.error(results["error"])
            return results

        peak_index = np.argmax(v_kv)
        peak_time_us_actual = t_us[peak_index]
        peak_value_kv = v_kv[peak_index]
        results["peak_value"] = peak_value_kv
        results["peak_time"] = peak_time_us_actual
        t_origin_us = t_us[0]

        mask_before_peak = t_us <= peak_time_us_actual
        t_before_us = t_us[mask_before_peak]
        v_before_kv = v_kv[mask_before_peak]
        if len(v_before_kv) > 1 and peak_value_kv > 1e-6:
            v_max_before = np.max(v_before_kv)
            v_min_before = np.min(v_before_kv)
            v_30_target = 0.3 * peak_value_kv
            v_90_target = 0.9 * peak_value_kv
            if v_max_before >= v_90_target and v_min_before <= v_30_target:
                try:
                    results["t_30"] = np.interp(
                        v_30_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    results["t_90"] = np.interp(
                        v_90_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    if (
                        not np.isnan(results["t_30"])
                        and not np.isnan(results["t_90"])
                        and results["t_90"] > results["t_30"]
                    ):
                        results["T_AB"] = results["t_90"] - results["t_30"]
                except Exception as e_interp_front:
                    logger.error(f"Erro interpolação frente SI: {e_interp_front}")

        mask_after_peak = t_us >= peak_time_us_actual
        t_after_us = t_us[mask_after_peak]
        v_after_kv = v_kv[mask_after_peak]
        v_50_target = 0.5 * peak_value_kv
        if len(v_after_kv) > 1 and np.min(v_after_kv) <= v_50_target + 1e-6:
            try:
                indices_below_50 = np.where(v_after_kv <= v_50_target)[0]
                if len(indices_below_50) > 0:
                    idx2 = indices_below_50[0]
                    idx1 = idx2 - 1 if idx2 > 0 else 0
                    t1_tail, v1_tail = t_after_us[idx1], v_after_kv[idx1]
                    t2_tail, v2_tail = t_after_us[idx2], v_after_kv[idx2]
                    if abs(v2_tail - v1_tail) > 1e-9:
                        t_half_us = t1_tail + (v_50_target - v1_tail) * (t2_tail - t1_tail) / (
                            v2_tail - v1_tail
                        )
                        if not np.isnan(t_half_us):
                            results["t_half"] = t_half_us
                            results["t2_calculated"] = t_half_us - t_origin_us
                    elif v1_tail >= v_50_target:
                        results["t_half"] = t1_tail
                        results["t2_calculated"] = t1_tail - t_origin_us
            except Exception as e_interp_tail:
                logger.error(f"Erro interpolação cauda SI (T2): {e_interp_tail}")

        if results["T_AB"] is not None and results.get("t2_calculated") is not None:
            try:
                K = 2.42 - (3.08e-3 * results["T_AB"]) + (1.51e-6 * (results["t2_calculated"] ** 2))
                results["tp"] = K * results["T_AB"]
            except Exception as e_tp_calc:
                logger.error(f"Erro cálculo Tp fórmula K: {e_tp_calc}")
                results["tp"] = peak_time_us_actual - t_origin_us
        else:
            results["tp"] = peak_time_us_actual - t_origin_us

        indices_above_90 = np.where(v_kv >= 0.9 * peak_value_kv)[0]
        if len(indices_above_90) > 1:
            results["td"] = t_us[indices_above_90[-1]] - t_us[indices_above_90[0]]

        if (
            len(v_after_kv) > 0 and np.min(v_after_kv) <= 1e-6
        ):  # Verifica se cruza zero (com tolerância)
            try:
                zero_cross_indices = np.where(v_after_kv <= 0)[0]
                if len(zero_cross_indices) > 0:
                    first_zero_idx_rel = zero_cross_indices[0]
                    first_zero_idx_abs = peak_index + first_zero_idx_rel
                    if first_zero_idx_abs > 0:
                        idx1_z_abs = first_zero_idx_abs - 1
                        idx2_z_abs = first_zero_idx_abs
                        t1_z, v1_z = t_us[idx1_z_abs], v_kv[idx1_z_abs]
                        t2_z, v2_z = t_us[idx2_z_abs], v_kv[idx2_z_abs]
                        if abs(v2_z - v1_z) > 1e-9 and v1_z > 0:
                            tz_us = t1_z - v1_z * (t2_z - t1_z) / (v2_z - v1_z)
                            if not np.isnan(tz_us):
                                results["tz"] = tz_us
                                results["tz_calculated"] = tz_us - t_origin_us
                    else:
                        results["tz"] = t_us[first_zero_idx_abs]
                        results["tz_calculated"] = results["tz"] - t_origin_us
            except Exception as e_interp_zero:
                logger.error(f"Erro interpolação Tz SI: {e_interp_zero}")

        if results["tp"] is not None:
            tp_min = SWITCHING_IMPULSE_PEAK_TIME_NOM * (1 - SWITCHING_PEAK_TIME_TOLERANCE)
            tp_max = SWITCHING_IMPULSE_PEAK_TIME_NOM * (1 + SWITCHING_PEAK_TIME_TOLERANCE)
            results["conforme_pico"] = tp_min <= results["tp"] <= tp_max
        if results.get("t2_calculated") is not None:
            t2_min = SWITCHING_IMPULSE_TAIL_TIME_NOM * (1 - SWITCHING_TAIL_TOLERANCE)
            t2_max = SWITCHING_IMPULSE_TAIL_TIME_NOM * (1 + SWITCHING_TAIL_TOLERANCE)
            results["conforme_meia_onda"] = t2_min <= results["t2_calculated"] <= t2_max
        if results.get("td") is not None:
            results["conforme_td"] = results["td"] >= SWITCHING_TIME_ABOVE_90_MIN
        if results.get("tz_calculated") is not None:
            results["conforme_tz"] = results["tz_calculated"] >= SWITCHING_TIME_TO_ZERO_MIN
        logger.info(
            f"Análise SI: Vp={results.get('peak_value', 'N/A'):.1f} kV, Tp={results.get('tp', 'N/A'):.1f} µs, T2={results.get('t2_calculated', 'N/A'):.1f} µs, Td={results.get('td', 'N/A'):.1f} µs, Tz={results.get('tz_calculated', 'N/A'):.1f} µs"
        )
        logger.info(
            f"Conformidade SI: Pico={results['conforme_pico']}, Cauda={results['conforme_meia_onda']}, Td={results['conforme_td']}, Tz={results['conforme_tz']}"
        )
        return results
    except Exception as e:
        logger.exception(f"Erro geral em analyze_switching_impulse: {e}")
        return {"error": str(e)}


def analyze_chopped_impulse(t_us, v_kv, chop_time_actual_us):
    """Analisa os parâmetros de um impulso cortado (LIC)."""
    logger.info(f"Analisando Impulso Cortado (LIC) com corte em {chop_time_actual_us:.2f} µs...")
    results = {
        "peak_value_full_wave": None,
        "peak_time_full_wave": None,
        "t_front": None,
        "t_0_virtual": None,
        "chop_time": None,
        "chop_voltage": None,
        "chop_voltage_orig": None,
        "t_30": None,
        "t_90": None,
        "chop_collapse_time": None,
        "undershoot": 0.0,
        "conforme_frente": False,
        "conforme_corte": False,
        "conforme_undershoot": True,
        "conforme_pico_corte": False,
        "error": None,
    }
    if chop_time_actual_us is None or chop_time_actual_us <= t_us[0]:
        results["error"] = "Tempo de corte não determinado ou inválido."
        logger.warning(results["error"])
        li_params = analyze_lightning_impulse(t_us, v_kv)  # Tenta analisar como LI
        if "error" not in li_params:
            results.update({k: v for k, v in li_params.items() if k in results})
        return results
    try:
        chop_start_index = np.argmin(np.abs(t_us - chop_time_actual_us))
        chop_start_index = min(max(chop_start_index, 1), len(t_us) - 2)
        chop_time_us = t_us[chop_start_index]
        t_before_chop_us = t_us[: chop_start_index + 1]
        v_before_chop_kv = v_kv[: chop_start_index + 1]
        if len(t_before_chop_us) < 5:
            results["error"] = "Dados insuficientes antes do corte."
            logger.error(results["error"])
            return results
        v_test_before_chop, v_base_before_chop, _, overshoot_before = calculate_k_factor_transform(
            v_before_chop_kv, t_before_chop_us
        )
        if v_test_before_chop is None:
            results["error"] = "Falha K-factor pré-corte."
            logger.error(results["error"])
            return results
        chop_voltage_kv = np.interp(
            chop_time_us,
            t_before_chop_us,
            v_test_before_chop,
            left=v_test_before_chop[0],
            right=v_test_before_chop[-1],
        )
        results["chop_voltage"] = chop_voltage_kv
        results["chop_voltage_orig"] = v_kv[chop_start_index]
        peak_idx_before = np.argmax(v_test_before_chop)
        peak_time_us_before = t_before_chop_us[peak_idx_before]
        peak_value_kv_before = v_test_before_chop[peak_idx_before]
        results["peak_value_full_wave"] = peak_value_kv_before
        results["peak_time_full_wave"] = peak_time_us_before
        t_0_virtual_us = t_us[0]
        mask_front = t_before_chop_us <= peak_time_us_before
        t_front_us = t_before_chop_us[mask_front]
        v_front_kv = v_test_before_chop[mask_front]
        if len(v_front_kv) > 1 and peak_value_kv_before > 1e-6:
            v_max_front = np.max(v_front_kv)
            v_min_front = np.min(v_front_kv)
            v_30_target = 0.3 * peak_value_kv_before
            v_90_target = 0.9 * peak_value_kv_before
            if v_max_front >= v_90_target and v_min_front <= v_30_target:
                try:
                    results["t_30"] = np.interp(
                        v_30_target, v_front_kv, t_front_us, left=np.nan, right=np.nan
                    )
                    results["t_90"] = np.interp(
                        v_90_target, v_front_kv, t_front_us, left=np.nan, right=np.nan
                    )
                    if (
                        not np.isnan(results["t_30"])
                        and not np.isnan(results["t_90"])
                        and results["t_90"] > results["t_30"]
                    ):
                        delta_t = results["t_90"] - results["t_30"]
                        if delta_t > 1e-9:
                            results["t_front"] = 1.67 * delta_t
                            slope = (v_90_target - v_30_target) / delta_t
                            if abs(slope) > 1e-9:
                                t_0_virtual_us = results["t_30"] - (v_30_target / slope)
                except Exception as e_interp_front_lic:
                    logger.error(f"Erro interpolação frente LIC: {e_interp_front_lic}")
        results["t_0_virtual"] = t_0_virtual_us
        results["chop_time"] = chop_time_us - t_0_virtual_us
        results["chop_collapse_time"] = None
        v_after_chop_kv = v_kv[chop_start_index + 1 :]
        if len(v_after_chop_kv) > 0:
            min_after_chop = np.min(v_after_chop_kv)
            if min_after_chop < 0 and abs(results["chop_voltage"]) > 1e-9:
                results["undershoot"] = (
                    max(0.0, abs(min_after_chop) / abs(results["chop_voltage"])) * 100
                )
        if results["t_front"] is not None:
            t1_min = LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 - CHOPPED_FRONT_TOLERANCE)
            t1_max = LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 + CHOPPED_FRONT_TOLERANCE)
            results["conforme_frente"] = t1_min <= results["t_front"] <= t1_max
        if results["chop_time"] is not None:
            results["conforme_corte"] = (
                CHOPPED_IMPULSE_CHOP_TIME_MIN
                <= results["chop_time"]
                <= CHOPPED_IMPULSE_CHOP_TIME_MAX
            )
        results["conforme_undershoot"] = results["undershoot"] <= CHOPPED_UNDERSHOOT_MAX
        logger.info(
            f"Análise LIC: Vc={results.get('chop_voltage', 'N/A'):.1f} kV, T1_subj={results.get('t_front', 'N/A'):.2f} µs, Tc={results.get('chop_time', 'N/A'):.2f} µs, Undershoot={results.get('undershoot', 'N/A'):.1f}%"
        )
        logger.info(
            f"Conformidade LIC: Frente={results['conforme_frente']}, Corte={results['conforme_corte']}, Undershoot={results['conforme_undershoot']}"
        )
        return results
    except Exception as e:
        logger.exception(f"Erro geral em analyze_chopped_impulse: {e}")
        return {"error": str(e)}


def interpolate_resistor_data(c_load_nf, reference_data):
    """
    Interpola dados de referência para obter o valor de resistor para uma determinada carga.
    Usa escala logarítmica para a interpolação, pois a relação Rf vs. C_load é aproximadamente log-log.

    Args:
        c_load_nf: Capacitância da carga total em nF
        reference_data: Lista de tuplas (c_load_nf, rf_ohm)

    Returns:
        rf_ohm: Resistência interpolada em Ohms
    """
    try:
        # Extrai os pontos de referência
        c_loads = np.array([point[0] for point in reference_data])
        r_values = np.array([point[1] for point in reference_data])

        # Se c_load está fora dos limites dos dados de referência
        if c_load_nf <= c_loads[0]:
            return r_values[0]
        if c_load_nf >= c_loads[-1]:
            return r_values[-1]

        # Converte para escala logarítmica
        log_c_loads = np.log10(c_loads)
        log_r_values = np.log10(r_values)
        log_c_load = np.log10(c_load_nf)

        # Interpolação linear em escala logarítmica
        log_r_interp = np.interp(log_c_load, log_c_loads, log_r_values)

        # Converte de volta para escala linear
        r_interp = 10**log_r_interp

        return r_interp

    except Exception as e:
        logger.error(f"Erro ao interpolar dados de resistores: {e}")
        # Fallback para uma estimativa básica
        if c_load_nf < 5:
            return 300  # Valor típico para cargas pequenas
        elif c_load_nf < 15:
            return 150  # Valor típico para cargas médias
        else:
            return 80  # Valor típico para cargas grandes


def format_parameter_value(param_value, precision=2, unit=""):
    """Formata um valor numérico para exibição, tratando None e NaN."""
    if param_value is None or (
        isinstance(param_value, float) and (np.isnan(param_value) or np.isinf(param_value))
    ):
        return "N/A"
    try:
        if isinstance(param_value, bool):
            return "Sim" if param_value else "Não"
        val = float(param_value)  # Tenta converter para float
        if abs(val) >= 1e6:
            return f"{val/1e6:.{precision}f}  M{unit}"
        elif abs(val) >= 1e3:
            return f"{val/1e3:.{precision}f}  k{unit}"
        elif abs(val) >= 1:
            return f"{val:.{precision}f}  {unit}"
        elif abs(val) >= 1e-3:
            return f"{val*1e3:.{precision}f}  m{unit}"
        elif abs(val) >= 1e-6:
            return f"{val*1e6:.{precision}f}  µ{unit}"
        elif abs(val) >= 1e-9:
            return f"{val*1e9:.{precision}f}  n{unit}"
        elif abs(val) >= 1e-12:
            return f"{val*1e12:.{precision}f}  p{unit}"
        elif abs(val) < 1e-15:
            return f"0.00  {unit}"  # Evita notação científica para zero
        else:
            return f"{val:.{precision}e}  {unit}"
    except (ValueError, TypeError):
        return str(param_value)  # Retorna como string se não for numérico
    except Exception as e:
        logger.error(f"Erro ao formatar valor {param_value}: {e}")
        return "Erro"


def create_circuit_parameters_display(params_data):
    """Cria uma tabela HTML formatada para os parâmetros do circuito."""
    if not params_data or not isinstance(params_data, dict):
        return dbc.Alert(
            "Dados de parâmetros do circuito indisponíveis.",
            color="warning",
            style={"fontSize": "0.7rem"},
        )

    # Verificação explícita de erro
    if "error" in params_data:
        return dbc.Alert(
            f"Erro nos parâmetros do circuito: {params_data['error']}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )

    header = html.Thead(html.Tr([html.Th("Parâmetro"), html.Th("Valor")]))
    rows = []

    def add_row(label, value, unit="", precision=2):
        rows.append(
            html.Tr(
                [
                    html.Td(label, style={"fontWeight": "bold"}),
                    html.Td(format_parameter_value(value, precision, unit)),
                ]
            )
        )

    # Extrai dados com segurança usando .get()
    try:
        resistances = params_data.get("resistances", {})
        inductances = params_data.get("inductances", {})
        capacitances = params_data.get("capacitances", {})
        derived = params_data.get("derived_params", {})
        efficiency = params_data.get("efficiency", {})  # Assumindo que a eficiência está aqui

        # Adiciona linhas à tabela
        add_row("Config. Gerador", params_data.get("generator_config"))
        add_row("Cg Efetiva", capacitances.get("cg_eff"), "F", 3)
        add_row("L Gerador Efetiva", inductances.get("gen_eff"), "H", 3)
        add_row("L Externa", inductances.get("ext"), "H", 3)
        add_row("L Adicional", inductances.get("add"), "H", 3)
        add_row("L Carga (Trafo)", inductances.get("load"), "H", 4)
        add_row("L TOTAL (sem ajuste)", inductances.get("total_initial"), "H", 3)
        add_row("L TOTAL AJUSTADA", inductances.get("total"), "H", 3)
        add_row("Carga DUT", capacitances.get("c_dut"), "F", 0)  # c_dut já deve estar em F
        add_row("Carga Divisor", capacitances.get("c_divider"), "F", 0)
        add_row("Carga Parasita", capacitances.get("c_stray"), "F", 0)
        add_row("Carga Extra (Gap/Ck)", capacitances.get("c_load_extra"), "F", 0)
        add_row("Carga TOTAL (Cl)", capacitances.get("cload"), "F", 1)
        add_row("Rf por Coluna", resistances.get("front_col"), "Ω")
        add_row("Rt por Coluna", resistances.get("tail_col"), "Ω")
        add_row("Rf Efetivo Total", resistances.get("rf_eff"), "Ω")
        add_row("Rt Efetivo Total (sem ajuste)", resistances.get("rt_initial"), "Ω")
        add_row("Rt Efetivo Total AJUSTADO", resistances.get("rt_eff"), "Ω")
        add_row("C Equivalente (Ceq)", capacitances.get("ceq"), "F", 1)
        add_row("Alpha Calculado (α)", derived.get("alpha"), "s⁻¹", 2)
        add_row("Beta Calculado (β)", derived.get("beta"), "s⁻¹", 2)
        add_row("Amortecimento (ζ)", derived.get("zeta"), "", 3)
        add_row("Eficiência Circuito", efficiency.get("circuit", 0) * 100, "%", 1)
        add_row("Eficiência Forma", efficiency.get("shape", 0) * 100, "%", 1)
        add_row("Eficiência TOTAL", efficiency.get("total", 0) * 100, "%", 1)
        add_row("Tensão Carga Gerador", params_data.get("charging_voltage"), "kV", 1)
        add_row("Tensão Pico/Corte Esperada", params_data.get("actual_test_voltage"), "kV", 1)
    except Exception as e:
        return dbc.Alert(
            f"Erro ao processar parâmetros do circuito: {str(e)}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        striped=True,
        size="sm",
        className="mb-0",
    )


def create_energy_details_table(energy_required_kj, max_energy_kj, generator_config_label):
    """Cria uma tabela com detalhes de energia requerida vs. disponível."""
    if energy_required_kj is None or max_energy_kj is None:
        return dbc.Alert(
            "Dados de energia indisponíveis.", color="warning", style={"fontSize": "0.7rem"}
        )
    try:
        rows = [
            html.Tr(
                [
                    html.Td("Energia Requerida (Carga)"),
                    html.Td(format_parameter_value(energy_required_kj, 2, "kJ")),
                ]
            ),
            html.Tr(
                [
                    html.Td("Energia Disponível (Gerador)"),
                    html.Td(format_parameter_value(max_energy_kj, 1, "kJ")),
                ]
            ),
            html.Tr([html.Td("Configuração Gerador"), html.Td(generator_config_label or "N/A")]),
        ]
        energy_margin = (
            max_energy_kj / energy_required_kj if energy_required_kj > 1e-9 else float("inf")
        )
        margin_class = (
            "text-success"
            if energy_margin >= 1.2
            else "text-warning"
            if energy_margin >= 1.0
            else "text-danger"
        )
        rows.append(
            html.Tr(
                [
                    html.Td("Margem de Energia"),
                    html.Td(
                        f"{energy_margin:.2f}x" if energy_margin != float("inf") else "∞",
                        className=margin_class,
                    ),
                ]
            )
        )
        return dbc.Table(
            [html.Tbody(rows)], bordered=True, hover=True, striped=True, size="sm", className="mb-0"
        )
    except Exception as e:
        return dbc.Alert(
            f"Erro ao criar tabela de energia: {str(e)}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )


# Moved definition before usage in run_simulation
def create_waveform_analysis_table(
    analysis_results, impulse_type, v_test_kv_input=None, gap_distance_cm=None
):
    """Cria uma tabela com os resultados da análise da forma de onda e status de conformidade."""
    if not analysis_results or not isinstance(analysis_results, dict):
        return dbc.Alert(
            "Resultados da análise indisponíveis.", color="warning", style={"fontSize": "0.7rem"}
        )
    if "error" in analysis_results and analysis_results["error"]:
        return dbc.Alert(
            f"Erro na análise: {analysis_results['error']}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )

    header = html.Thead(
        html.Tr(
            [
                html.Th("Parâmetro"),
                html.Th("Valor Simulado"),
                html.Th("Requisito Norma"),
                html.Th("Status"),
            ]
        )
    )
    rows = []
    overall_compliance = True  # Assume conformidade inicial

    def check_compliance(value, req_min, req_max, is_max_limit=False):
        nonlocal overall_compliance
        if value is None or (
            isinstance(value, (float, int)) and (np.isnan(value) or np.isinf(value))
        ):
            overall_compliance = False  # Não pode ser conforme se não foi calculado
            return "table-warning", "❓"
        val = float(value)
        low = float(req_min) if req_min is not None else -np.inf
        high = float(req_max) if req_max is not None else np.inf
        status = False
        if is_max_limit:
            status = val <= high
        elif low != -np.inf and high == np.inf:
            status = val >= low
        elif low != -np.inf and high != np.inf:
            status = low <= val <= high
        else:
            return "", ""  # Sem requisito específico
        if not status:
            overall_compliance = False
        return "table-success" if status else "table-danger", "✔️" if status else "❌"

    def add_analysis_row(label, param_key, unit, req_min, req_max, is_max_limit=False, precision=2):
        value = analysis_results.get(param_key)
        val_str = format_parameter_value(value, precision, unit)
        req_str = ""
        if is_max_limit and req_max is not None:
            req_str = f"≤ {req_max:.{precision}f} {unit}"
        elif req_min is not None and req_max is None:
            req_str = f"≥ {req_min:.{precision}f} {unit}"
        elif req_min is not None and req_max is not None:
            req_str = f"{req_min:.{precision}f} - {req_max:.{precision}f} {unit}"
        else:
            req_str = "-"
        compliance_class, status_symbol = check_compliance(value, req_min, req_max, is_max_limit)
        rows.append(
            html.Tr(
                [html.Td(label), html.Td(val_str), html.Td(req_str), html.Td(status_symbol)],
                className=compliance_class,
            )
        )

    if impulse_type == "lightning":
        vt_min = v_test_kv_input * (1 - LIGHTNING_PEAK_TOLERANCE) if v_test_kv_input else None
        vt_max = v_test_kv_input * (1 + LIGHTNING_PEAK_TOLERANCE) if v_test_kv_input else None
        req = {
            "T1_min": LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 - LIGHTNING_FRONT_TOLERANCE),
            "T1_max": LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 + LIGHTNING_FRONT_TOLERANCE),
            "T2_min": LIGHTNING_IMPULSE_TAIL_TIME_NOM * (1 - LIGHTNING_TAIL_TOLERANCE),
            "T2_max": LIGHTNING_IMPULSE_TAIL_TIME_NOM * (1 + LIGHTNING_TAIL_TOLERANCE),
            "Beta_max": LIGHTNING_OVERSHOOT_MAX,
            "Vt_min": vt_min,
            "Vt_max": vt_max,
        }
        add_analysis_row(
            "Vt (Pico Ensaio)", "test_value", "kV", req["Vt_min"], req["Vt_max"], precision=1
        )
        add_analysis_row("T₁ (Frente)", "t_front", "µs", req["T1_min"], req["T1_max"])
        add_analysis_row("T₂ (Cauda)", "t_tail", "µs", req["T2_min"], req["T2_max"], precision=1)
        add_analysis_row(
            "β (Overshoot)", "overshoot", "%", None, req["Beta_max"], is_max_limit=True, precision=1
        )
    elif impulse_type == "switching":
        vt_min = v_test_kv_input * (1 - SWITCHING_PEAK_TOLERANCE) if v_test_kv_input else None
        vt_max = v_test_kv_input * (1 + SWITCHING_PEAK_TOLERANCE) if v_test_kv_input else None
        req = {
            "Tp_min": SWITCHING_IMPULSE_PEAK_TIME_NOM * (1 - SWITCHING_PEAK_TIME_TOLERANCE),
            "Tp_max": SWITCHING_IMPULSE_PEAK_TIME_NOM * (1 + SWITCHING_PEAK_TIME_TOLERANCE),
            "T2_min": SWITCHING_IMPULSE_TAIL_TIME_NOM * (1 - SWITCHING_TAIL_TOLERANCE),
            "T2_max": SWITCHING_IMPULSE_TAIL_TIME_NOM * (1 + SWITCHING_TAIL_TOLERANCE),
            "Td_min": SWITCHING_TIME_ABOVE_90_MIN,
            "Tz_min": SWITCHING_TIME_TO_ZERO_MIN,
            "Vt_min": vt_min,
            "Vt_max": vt_max,
        }
        add_analysis_row(
            "Vp (Pico Ensaio)", "peak_value", "kV", req["Vt_min"], req["Vt_max"], precision=1
        )
        add_analysis_row("Tp (Pico)", "tp", "µs", req["Tp_min"], req["Tp_max"], precision=0)
        add_analysis_row(
            "T₂ (Meio Valor)", "t2_calculated", "µs", req["T2_min"], req["T2_max"], precision=0
        )
        add_analysis_row("Td (>90%)", "td", "µs", req["Td_min"], None, precision=0)
        add_analysis_row("Tz (Zero)", "tz_calculated", "µs", req["Tz_min"], None, precision=0)
    elif impulse_type == "chopped":
        vc_nominal = (gap_distance_cm or 0) * 30.0  # Estimativa nominal
        vc_min = vc_nominal * (1 - CHOPPED_PEAK_TOLERANCE) if vc_nominal > 0 else None
        vc_max = vc_nominal * (1 + CHOPPED_PEAK_TOLERANCE) if vc_nominal > 0 else None
        req = {
            "T1_min": LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 - CHOPPED_FRONT_TOLERANCE),
            "T1_max": LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 + CHOPPED_FRONT_TOLERANCE),
            "Tc_min": CHOPPED_IMPULSE_CHOP_TIME_MIN,
            "Tc_max": CHOPPED_IMPULSE_CHOP_TIME_MAX,
            "Undershoot_max": CHOPPED_UNDERSHOOT_MAX,
            "Vc_min": vc_min,
            "Vc_max": vc_max,
        }
        add_analysis_row(
            "Vc (Tensão Corte)", "chop_voltage", "kV", req["Vc_min"], req["Vc_max"], precision=1
        )
        add_analysis_row("T₁ (Frente Subj.)", "t_front", "µs", req["T1_min"], req["T1_max"])
        add_analysis_row("Tc (Tempo Corte)", "chop_time", "µs", req["Tc_min"], req["Tc_max"])
        add_analysis_row(
            "Undershoot",
            "undershoot",
            "%",
            None,
            req["Undershoot_max"],
            is_max_limit=True,
            precision=1,
        )
    else:
        return dbc.Alert(
            f"Tipo de impulso desconhecido para análise: {impulse_type}", color="warning"
        )

    # Verifica conformidade geral (após todas as chamadas a check_compliance)
    analysis_results["overall_compliance"] = overall_compliance

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        striped=True,
        size="sm",
        className="mb-0",
    )


# --- Callbacks ---


# Callback para carregar dados iniciais quando a página é carregada
@app.callback(
    [
        Output("test-voltage", "value"),
        Output("generator-config", "value"),
        Output("simulation-model-type", "value"),
        Output("test-object-capacitance", "value"),
        Output("stray-capacitance", "value"),
        Output("shunt-resistor", "value"),
        Output("front-resistor-expression", "value"),
        Output("tail-resistor-expression", "value"),
        Output("inductance-adjustment-factor", "value"),
        Output("tail-resistance-adjustment-factor", "value"),
        Output("external-inductance", "value"),
        Output("transformer-inductance", "value"),
        Output("impulse-type", "value"),
        Output("gap-distance", "value"),
        Output("si-capacitor-value", "value"),
    ],
    [
        Input("url", "pathname"),
        Input("impulse-store", "data"),  # Adicionado para detectar mudanças no store
    ],
    prevent_initial_call=False,  # Executa na carga inicial
)
def load_impulse_data_on_page_load(pathname, impulse_store_data):
    """
    Carrega os dados iniciais do módulo de impulso quando a página é carregada ou o store muda.
    Este callback é executado quando a URL muda para '/impulso' ou quando o store é atualizado.
    """
    # Verificar qual foi o trigger
    triggered_id = ctx.triggered_id if ctx.triggered else None
    log.info(
        f"[IMPULSE LOAD] Callback de carregamento acionado. Trigger: {triggered_id}, Pathname: {pathname}"
    )

    # Se o trigger for o store, usamos os dados do store diretamente
    if triggered_id == "impulse-store" and impulse_store_data:
        log.info("[IMPULSE LOAD] Carregando dados do store que foi atualizado")
        # Continua com o processamento abaixo, usando impulse_store_data
        impulse_data = impulse_store_data
    else:
        # Se o trigger for a URL, verificamos se estamos na página correta
        if pathname is None:
            raise PreventUpdate

        clean_path = normalize_pathname(pathname)
        if clean_path != ROUTE_IMPULSE:
            log.debug(
                f"[IMPULSE LOAD] Não estamos na página de impulso (pathname={pathname}). Prevenindo atualização."
            )
            raise PreventUpdate

        # Tenta obter os dados do MCP
        if app.mcp is None:
            log.error("[IMPULSE LOAD] MCP não inicializado. Abortando.")
            raise PreventUpdate

        # Obtém os dados do store de impulso
        impulse_data = app.mcp.get_data("impulse-store")
        log.info(f"[IMPULSE LOAD] Dados obtidos do MCP: {impulse_data}")

    # Valores padrão caso não haja dados no store
    defaults = {
        "test_voltage": 1200,
        "generator_config": "6S-1P",
        "simulation_model_type": "hybrid",
        "test_object_capacitance": 3000,
        "stray_capacitance": 400,
        "shunt_resistor": 0.01,
        "front_resistor_expression": "15",
        "tail_resistor_expression": "100",
        "inductance_adjustment_factor": 1.0,
        "tail_resistance_adjustment_factor": 1.0,
        "external_inductance": 10,
        "transformer_inductance": 0.05,
        "impulse_type": "lightning",
        "gap_distance": 4.0,
        "si_capacitor_value": 600,
    }

    # Se não houver dados no store, usa os valores padrão
    if not impulse_data:
        log.info("[IMPULSE LOAD] Nenhum dado encontrado no store. Usando valores padrão.")
        return [
            defaults["test_voltage"],
            defaults["generator_config"],
            defaults["simulation_model_type"],
            defaults["test_object_capacitance"],
            defaults["stray_capacitance"],
            defaults["shunt_resistor"],
            defaults["front_resistor_expression"],
            defaults["tail_resistor_expression"],
            defaults["inductance_adjustment_factor"],
            defaults["tail_resistance_adjustment_factor"],
            defaults["external_inductance"],
            defaults["transformer_inductance"],
            defaults["impulse_type"],
            defaults["gap_distance"],
            defaults["si_capacitor_value"],
        ]

    # Extrai os valores do store ou usa os valores padrão
    # Verificar se os valores estão diretamente no dicionário principal
    log.info(f"[IMPULSE LOAD] Verificando valores diretamente no dicionário principal: {list(impulse_data.keys())}")

    return [
        impulse_data.get("test_voltage", defaults["test_voltage"]),
        impulse_data.get("generator_config", defaults["generator_config"]),
        impulse_data.get("simulation_model_type", defaults["simulation_model_type"]),
        impulse_data.get("test_object_capacitance", defaults["test_object_capacitance"]),
        impulse_data.get("stray_capacitance", defaults["stray_capacitance"]),
        impulse_data.get("shunt_resistor", defaults["shunt_resistor"]),
        impulse_data.get("front_resistor_expression", defaults["front_resistor_expression"]),
        impulse_data.get("tail_resistor_expression", defaults["tail_resistor_expression"]),
        impulse_data.get("inductance_adjustment_factor", defaults["inductance_adjustment_factor"]),
        impulse_data.get(
            "tail_resistance_adjustment_factor", defaults["tail_resistance_adjustment_factor"]
        ),
        impulse_data.get("external_inductance", defaults["external_inductance"]),
        impulse_data.get("transformer_inductance", defaults["transformer_inductance"]),
        impulse_data.get("impulse_type", defaults["impulse_type"]),
        impulse_data.get("gap_distance", defaults["gap_distance"]),
        impulse_data.get("si_capacitor_value", defaults["si_capacitor_value"]),
    ]


# Callback para iniciar/parar simulação automática
@app.callback(
    [
        Output("simulate-button-text", "children"),
        Output("simulate-spinner", "className"),
        Output("auto-simulate-interval", "disabled"),
        Output("simulation-status", "data"),
    ],
    [Input("simulate-button", "n_clicks"), Input("auto-simulate-interval", "n_intervals")],
    [State("simulation-status", "data")],
)
def toggle_simulation(n_clicks, n_intervals, status_data):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    running = (
        status_data.get("running", False) if status_data else False
    )  # Default to False if None

    if trigger_id == "simulate-button" and n_clicks:
        # Alternar estado
        new_running = not running
        return (
            "Parar Simulação" if new_running else "Simular Forma de Onda",
            "ms-2" if new_running else "ms-2 d-none",
            not new_running,  # Intervalo ativo quando running=True
            {"running": new_running},
        )

    # Manter estado atual
    return (
        "Parar Simulação" if running else "Simular Forma de Onda",
        "ms-2" if running else "ms-2 d-none",
        not running,
        {"running": running},
    )


# Callback para mostrar/esconder os containers específicos baseados no tipo de impulso
@app.callback(
    [
        Output("gap-distance-container", "style"),
        Output("capacitor-si-container", "style"),
        Output("inductor-container", "style"),
        Output("si-model-warning-alert", "style"),
    ],
    Input("impulse-type", "value"),
)
def update_dynamic_controls(impulse_type):
    """Atualiza a visibilidade dos controles dinâmicos baseados no tipo de impulso."""
    gap_style = {"display": "block"} if impulse_type == "chopped" else {"display": "none"}
    capacitor_style = {"display": "block"} if impulse_type == "switching" else {"display": "none"}
    inductor_style = (
        {"display": "block"} if impulse_type in ["lightning", "chopped"] else {"display": "none"}
    )
    si_warning_style = {"display": "block"} if impulse_type == "switching" else {"display": "none"}

    return gap_style, capacitor_style, inductor_style, si_warning_style


@app.callback(
    Output("front-resistor-expression", "value"),
    [Input("rf-up", "n_clicks"), Input("rf-down", "n_clicks")],
    [State("front-resistor-expression", "value")],
    prevent_initial_call=True,
)
def update_rf_value(up_clicks, down_clicks, current_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        # Extrair valor numérico base
        if current_value and current_value.isdigit():
            current_numeric = int(current_value)
        else:
            # Tenta extrair número de expressões mais complexas
            match = re.search(r"(\d+)", str(current_value))  # Ensure current_value is string
            if match:
                current_numeric = int(match.group(1))
            else:
                current_numeric = 15  # Valor padrão

        # Aplicar incremento/decremento
        if trigger_id == "rf-up":
            return str(current_numeric + 1)
        elif trigger_id == "rf-down":
            return str(max(1, current_numeric - 1))
    except Exception as e:
        logger.error(f"Error updating Rf value: {e}")

    return current_value


@app.callback(
    Output("tail-resistor-expression", "value"),
    [Input("rt-up", "n_clicks"), Input("rt-down", "n_clicks")],
    [State("tail-resistor-expression", "value")],
    prevent_initial_call=True,
)
def update_rt_value(up_clicks, down_clicks, current_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        # Extrair valor numérico base
        if current_value and current_value.isdigit():
            current_numeric = int(current_value)
        else:
            # Tenta extrair número de expressões mais complexas
            match = re.search(r"(\d+)", str(current_value))  # Ensure current_value is string
            if match:
                current_numeric = int(match.group(1))
            else:
                current_numeric = 100  # Valor padrão

        # Aplicar incremento/decremento
        if trigger_id == "rt-up":
            return str(current_numeric + 10)
        elif trigger_id == "rt-down":
            return str(max(10, current_numeric - 10))
    except Exception as e:
        logger.error(f"Error updating Rt value: {e}")

    return current_value


# --- Callback para exibir informações do transformador na página ---
# Este callback foi removido pois o painel agora é criado diretamente no layout
# @app.callback(
#     Output("transformer-info-impulse-page", "children"),
#     Input("transformer-info-impulse", "children"),
#     prevent_initial_call=False
# )
# def update_impulse_page_info_panel(global_panel_content):
#     """Copia o conteúdo do painel global para o painel específico da página."""
#     return global_panel_content


# Callback para mostrar/esconder a calculadora de indutância do transformador
@app.callback(
    Output("transformer-calc-collapse", "is_open"),
    Input("show-transformer-calc", "n_clicks"),
    State("transformer-calc-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_transformer_calc(n, is_open):
    if n:
        return not is_open
    return is_open


# Callback para calcular a indutância do transformador
@app.callback(
    [
        Output("transformer-inductance", "value"),
        Output("calculated-inductance-display", "children"),
        Output("calculated-inductance", "data"),
    ],
    Input("calculate-inductance", "n_clicks"),
    [
        State("transformer-voltage", "value"),
        State("transformer-power", "value"),
        State("transformer-impedance", "value"),
        State("transformer-frequency", "value"),
    ],
    prevent_initial_call=True,
)
def calculate_transformer_inductance_callback(n_clicks, voltage, power, impedance, frequency):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    try:
        l_trafo = calculate_transformer_inductance(voltage, power, impedance, frequency)
        result_text = f"L = {l_trafo:.4f} H"
        result_data = {
            "inductance": l_trafo,
            "params": {
                "voltage": voltage,
                "power": power,
                "impedance": impedance,
                "frequency": frequency,
            },
        }

        logger.info(f"Indutância do transformador calculada: {l_trafo:.4f} H")
        return l_trafo, result_text, result_data
    except Exception as e:
        logger.error(f"Erro ao calcular indutância do transformador: {e}")
        return dash.no_update, f"Erro: {str(e)}", None


# Callback para usar dados do transformador
@app.callback(
    [
        Output("transformer-voltage", "value"),
        Output("transformer-power", "value"),
        Output("transformer-impedance", "value"),
        Output("transformer-inductance", "value", allow_duplicate=True),
    ],
    Input("use-transformer-data", "n_clicks"),
    State("transformer-inputs-store", "data"),
    prevent_initial_call=True,
)
def use_transformer_data(n_clicks, transformer_data):
    if n_clicks is None or not transformer_data:
        raise dash.exceptions.PreventUpdate

    try:
        # Verificar se os dados estão aninhados em transformer_data
        if "transformer_data" in transformer_data and isinstance(transformer_data["transformer_data"], dict):
            # Usar os dados aninhados
            data_dict = transformer_data["transformer_data"]
            log.debug(f"[IMPULSE] Usando dados aninhados em transformer_data")
        else:
            # Usar os dados diretamente
            data_dict = transformer_data
            log.debug(f"[IMPULSE] Usando dados diretamente do dicionário principal")

        voltage_kv = data_dict.get("tensao_at")
        power_mva = data_dict.get("potencia_mva")
        impedance_percent = data_dict.get("impedancia")
        freq_hz = data_dict.get("frequencia", 60)

        # Calcular indutância do transformador
        l_trafo = calculate_transformer_inductance(
            voltage_kv, power_mva, impedance_percent, freq_hz
        )

        logger.info(
            f"Dados do transformador utilizados: {voltage_kv} kV, {power_mva} MVA, {impedance_percent}%, {freq_hz} Hz"
        )
        logger.info(f"Indutância calculada: {l_trafo:.4f} H")

        return voltage_kv, power_mva, impedance_percent, l_trafo
    except Exception as e:
        logger.error(f"Erro ao utilizar dados do transformador: {e}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Callback para atualizar o gráfico de impulso e salvar no store
@app.callback(
    [
        Output("impulse-graph", "figure"),
        Output("impulse-results", "children"),
        Output("impulse-store", "data"),
    ],
    [Input("run-simulation", "n_clicks_timestamp")],  # Usando n_clicks_timestamp em vez de n_clicks
    [
        State("front-resistor", "value"),
        State("tail-resistor", "value"),
        State("capacitance", "value"),
        State("transformer-inductance", "value"),
        State("stray-capacitance", "value"),
        State("shunt-resistance", "value"),
        State("simulation-time", "value"),
        State("time-step", "value"),
        State("impulse-type", "value"),
        State("impulse-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_impulse_simulation(
    n_clicks,
    r_front,
    r_tail,
    capacitance,
    inductance,
    stray_cap,
    shunt_res,
    sim_time,
    time_step,
    impulse_type,
    current_store_data,
):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    log.info(f"[IMPULSE SIMULATION] Iniciando simulação de impulso. Tipo: {impulse_type}")

    try:
        # Validar entradas
        if None in [
            r_front,
            r_tail,
            capacitance,
            inductance,
            stray_cap,
            shunt_res,
            sim_time,
            time_step,
        ]:
            return dash.no_update, html.Div(
                "Preencha todos os campos para simular", style={"color": "red"}
            )

        # Converter para valores numéricos
        r_front = float(r_front)
        r_tail = float(r_tail)
        capacitance = float(capacitance) * 1e-9  # nF para F
        inductance = float(inductance)
        stray_cap = float(stray_cap) * 1e-12  # pF para F
        shunt_res = float(shunt_res)
        sim_time = float(sim_time) * 1e-6  # µs para s
        time_step = float(time_step) * 1e-9  # ns para s

        # Simular o circuito de impulso
        t, v = simulate_impulse_circuit(
            r_front, r_tail, capacitance, inductance, stray_cap, shunt_res, sim_time, time_step
        )

        # Analisar a forma de onda
        peak_voltage, rise_time, tail_time = analyze_impulse_waveform(t, v)

        # Criar gráfico
        fig = create_impulse_graph(t, v, peak_voltage, rise_time, tail_time)

        # Criar resultados
        results = html.Div(
            [
                html.H5("Resultados da Simulação"),
                html.P(f"Tensão de Pico: {peak_voltage:.2f} kV"),
                html.P(f"Tempo de Frente (T1): {rise_time:.2f} µs"),
                html.P(f"Tempo de Cauda (T2): {tail_time:.2f} µs"),
                html.P(f"Forma de Onda: {rise_time:.1f}/{tail_time:.1f} µs"),
            ]
        )

        logger.info(f"Simulação de impulso concluída: {rise_time:.1f}/{tail_time:.1f} µs")

        # Preparar dados para o store
        if current_store_data is None:
            current_store_data = {}

        # Dados para o store - inputs usados e resultados calculados
        import datetime

        data_for_store = {
            "impulse_type": impulse_type,
            "inputs": {
                "r_front": r_front,
                "r_tail": r_tail,
                "capacitance": capacitance,
                "inductance": inductance,
                "stray_cap": stray_cap,
                "shunt_res": shunt_res,
                "sim_time": sim_time,
                "time_step": time_step,
            },
            "results": {
                "peak_voltage": peak_voltage,
                "rise_time": rise_time,
                "tail_time": tail_time,
                "waveform_type": f"{rise_time:.1f}/{tail_time:.1f} µs",
            },
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Adicionar os inputs específicos para impulso conforme solicitado
        inputs_impulso = {
            "tensao_kv": peak_voltage,
            "config": impulse_type,
            "modelo": "RLC+K",
            "cap_dut_pf": capacitance * 1e12,  # Converter de F para pF
            "shunt_ohm": shunt_res,
            "cap_parasita_pf": stray_cap * 1e12,  # Converter de F para pF
            "rf_por_coluna": r_front,
            "rt_por_coluna": r_tail,
            "aj_l_fator": 1.0,  # Valor padrão
            "aj_rt_fator": 1.0,  # Valor padrão
            "l_extra_uh": 0.0,  # Valor padrão
            "indutor_extra": "Não",  # Valor padrão
            "l_carga_trafo_h": inductance,
        }

        # Atualizar o store com os novos dados
        current_store_data.update(data_for_store)

        # Adicionar os inputs específicos para impulso no store
        if "inputs_impulso" not in current_store_data:
            current_store_data["inputs_impulso"] = {}
        current_store_data["inputs_impulso"].update(inputs_impulso)

        # Serializar os dados antes de armazenar no MCP
        serializable_data = convert_numpy_types(current_store_data, debug_path="impulse_update")

        # Salvar no MCP para que outros módulos possam acessar
        app.mcp.set_data("impulse-store", serializable_data)
        log.info(f"[IMPULSE] Dados salvos no MCP (impulse-store)")

        return fig, results, serializable_data

    except Exception as e:
        logger.error(f"Erro na simulação de impulso: {e}")
        return dash.no_update, html.Div(f"Erro: {str(e)}", style={"color": "red"}), dash.no_update


# Funções auxiliares para simulação de impulso
def simulate_impulse_circuit(
    r_front, r_tail, capacitance, inductance, stray_cap, shunt_res, sim_time, time_step
):
    """Simula o circuito de impulso e retorna os vetores de tempo e tensão"""
    # Implementação simplificada - em um sistema real, usaríamos uma biblioteca de simulação de circuitos
    num_points = int(sim_time / time_step) + 1
    t = np.linspace(0, sim_time, num_points)

    # Cálculo da forma de onda de impulso usando a equação padrão
    alpha = 1 / (r_tail * capacitance)
    beta = 1 / (r_front * capacitance)
    v0 = 1.0  # Tensão normalizada

    v = v0 * (np.exp(-alpha * t) - np.exp(-beta * t))

    # Normalizar para tensão de pico = 1.0
    peak_idx = np.argmax(v)
    v = v / v[peak_idx]

    return t, v


def analyze_impulse_waveform(t, v):
    """Analisa a forma de onda de impulso e retorna os parâmetros principais"""
    # Encontrar tensão de pico
    peak_idx = np.argmax(v)
    peak_voltage = v[peak_idx]

    # Converter tempo para µs para análise
    t_us = t * 1e6

    # Encontrar tempo de frente (T1)
    # Tempo entre 30% e 90% da tensão de pico, multiplicado por 1.67
    idx_30 = np.where(v >= 0.3 * peak_voltage)[0][0]
    idx_90 = np.where(v >= 0.9 * peak_voltage)[0][0]
    rise_time = 1.67 * (t_us[idx_90] - t_us[idx_30])

    # Encontrar tempo de cauda (T2)
    # Tempo do início até 50% da tensão de pico na cauda
    idx_50_tail = np.where(v[peak_idx:] <= 0.5 * peak_voltage)[0]
    if len(idx_50_tail) > 0:
        idx_50_tail = idx_50_tail[0] + peak_idx
        tail_time = t_us[idx_50_tail] - t_us[0]
    else:
        # Se não encontrar o ponto de 50%, estimar
        tail_time = 50.0  # valor padrão

    return peak_voltage, rise_time, tail_time


def create_impulse_graph(t, v, peak_voltage, rise_time, tail_time):
    """Cria o gráfico da forma de onda de impulso"""
    # Converter tempo para µs para exibição
    t_us = t * 1e6

    fig = go.Figure()

    # Adicionar a forma de onda
    fig.add_trace(
        go.Scatter(x=t_us, y=v, mode="lines", name="Tensão", line=dict(color="#007bff", width=2))
    )

    # Adicionar linhas de referência
    fig.add_shape(
        type="line",
        x0=0,
        y0=0.3,
        x1=max(t_us),
        y1=0.3,
        line=dict(color="gray", width=1, dash="dash"),
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=0.9,
        x1=max(t_us),
        y1=0.9,
        line=dict(color="gray", width=1, dash="dash"),
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=0.5,
        x1=max(t_us),
        y1=0.5,
        line=dict(color="gray", width=1, dash="dash"),
    )

    # Configurar layout
    fig.update_layout(
        title=f"Forma de Onda de Impulso {rise_time:.1f}/{tail_time:.1f} µs",
        xaxis_title="Tempo (µs)",
        yaxis_title="Tensão (p.u.)",
        xaxis=dict(range=[0, min(100, max(t_us))]),  # Limitar a visualização a 100 µs
        yaxis=dict(range=[0, 1.1]),
        margin=dict(l=50, r=50, t=50, b=50),
        height=500,
        template="plotly_white",
    )

    return fig


# --- Callback para exibir informações do transformador removido ---
# Este callback foi removido pois a atualização é feita pelo callback global em global_updates.py


# --- Callback para atualizar o painel de informações do transformador na página de impulso ---
@dash.callback(
    Output("transformer-info-impulse-page", "children"),
    Input("transformer-info-impulse", "children"),
    prevent_initial_call=False,
)
def update_impulse_page_info_panel(global_panel_content):
    """
    Copia o conteúdo do painel de informações global para o painel local da página de impulso.
    Este callback é acionado quando o painel global é atualizado pelo callback global_updates_all_transformer_info_panels.
    """
    log.debug("Atualizando painel de informações do transformador na página de impulso")
    return global_panel_content


# Função de registro de callbacks para compatibilidade com app.py
def register_impulse_callbacks(app):
    """
    Registra os callbacks do módulo de impulso.
    Esta função é chamada por app.py para garantir que todos os callbacks sejam registrados.

    Args:
        app: A instância da aplicação Dash
    """
    log.info(
        f"Callbacks do módulo de impulso já registrados via decoradores @dash.callback para app {app.title}."
    )
