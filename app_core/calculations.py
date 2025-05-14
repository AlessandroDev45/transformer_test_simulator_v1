# app_core/calculations.py
"""
Módulo central para funções de cálculo puras, independentes da interface Dash.
Utiliza constantes definidas em utils.constants.
"""
import logging
import math
import re
import warnings

import numpy as np
import pandas as pd  # Needed for buscar_valores_tabela
from scipy.fftpack import fft, fftfreq, ifft
from scipy.optimize import OptimizeWarning, curve_fit

# Importar constantes definidas centralmente
from utils import constants

# Assumindo que config.py está acessível, para cores por exemplo (embora cálculos não devam usar cores)
# import config # Geralmente não necessário aqui

log = logging.getLogger(__name__)

# --- Supressão de Warnings (Opcional, mas útil para SciPy) ---
warnings.filterwarnings("ignore", category=OptimizeWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Funções Movidas e Refatoradas ---

# === Funções de Análise de Expressão (de impulse.py) ===


def parse_resistor_expression(expression: str | None) -> tuple[float, dict]:
    """
    Analisa uma expressão de configuração de resistores (série '+', paralelo '||').
    Suporta unidades 'k' e 'm', e capacitores de acoplamento ('pf').

    Args:
        expression: A string contendo a expressão (ex: "100 + 50||50", "1.5k || 600 pF").

    Returns:
        Uma tupla contendo:
        - float: A resistência equivalente em Ohms (float('inf') em caso de erro).
        - dict: Um dicionário com componentes especiais detectados (ex: {'coupling_capacitor': 600e-12}).
    """
    if not expression or not isinstance(expression, str) or expression.strip() == "":
        log.warning("Expressão de resistor vazia ou inválida recebida.")
        return float("inf"), {}

    expression = expression.lower().strip()
    special_components = {}

    # Detecta capacitor de acoplamento (ex: "|| 600pF" ou "600pF ||")
    # Trata pF, nF, uF
    cap_regex = r"\|\|\s*(\d+(?:\.\d+)?)\s*(p|n|u)?f"
    cap_match_suffix = re.search(cap_regex, expression)
    cap_match_prefix = re.search(r"(\d+(?:\.\d+)?)\s*(p|n|u)?f\s*\|\|", expression)

    cap_match = cap_match_suffix or cap_match_prefix
    multiplier = {"p": 1e-12, "n": 1e-9, "u": 1e-6, None: 1e-12}  # Default pF

    if cap_match:
        try:
            cap_value_str = cap_match.group(1)
            unit_prefix = cap_match.group(2)
            cap_value = float(cap_value_str) * multiplier.get(unit_prefix, 1e-12)
            special_components["coupling_capacitor"] = cap_value
            # Remove a parte do capacitor da expressão principal
            expression = re.sub(cap_regex, "", expression).strip()
            expression = re.sub(r"\d+(?:\.\d+)?\s*(p|n|u)?f\s*\|\|", "", expression).strip()
            log.info(
                f"Capacitor de acoplamento {cap_value*1e12:.1f} pF detectado e removido da expressão Rf/Rt."
            )
        except (ValueError, IndexError) as e:
            log.error(f"Erro ao converter valor do capacitor em '{expression}': {e}")
            return float("inf"), {}  # Retorna erro se o capacitor for inválido

    try:
        # Prepara a expressão para eval seguro
        expression_safe = expression.replace("||", "__parallel__")
        # Substitui k e m por multiplicação (tratando casos como 1k5 ou 1.5k)
        expression_safe = re.sub(r"(\d+(?:\.\d+)?)\s*k", r"(\1 * 1000)", expression_safe)
        expression_safe = re.sub(
            r"(\d+)\s*k\s*(\d+)", r"(\1 * 1000 + \2 * 100)", expression_safe
        )  # 1k5 -> 1500
        expression_safe = re.sub(
            r"(\d+(?:\.\d+)?)\s*m", r"(\1 * 1000000)", expression_safe
        )  # Para Mega Ohms (raro)

        def calculate_parallel(*args):
            """Calcula a resistência equivalente de resistores em paralelo."""
            if not args:
                return float("inf")
            inv_sum = 0.0
            valid_resistors_found = False
            for r in args:
                try:
                    r_float = float(r)
                    if (
                        r_float > 1e-9
                    ):  # Considera resistências muito pequenas como circuito aberto no paralelo
                        inv_sum += 1.0 / r_float
                        valid_resistors_found = True
                except (ValueError, TypeError, ZeroDivisionError):
                    continue  # Ignora valores inválidos
            if not valid_resistors_found:
                return float("inf")  # Nenhum resistor válido no paralelo
            return 1.0 / inv_sum if inv_sum > 1e-12 else float("inf")

        # Define o ambiente seguro para eval
        # Permite apenas números, operadores +, *, /, __parallel__, e parênteses
        allowed_chars = r"^[\d\.\s\*\+\(\)/,eE-]+$"  # Permitir 'e' ou 'E' para notação científica
        safe_dict = {"__parallel__": calculate_parallel, "__builtins__": None}

        # Divide por '+' para tratar partes em série
        series_parts = expression_safe.split("+")
        total_resistance = 0.0
        if not series_parts or all(not part.strip() for part in series_parts):
            # Caso a expressão seja vazia após remover o capacitor, por exemplo
            if special_components:
                return 0.0, special_components  # Retorna 0 Ohm se só tinha capacitor
            log.warning(
                f"Expressão de resistor '{expression}' sem partes válidas após processamento."
            )
            return float("inf"), special_components

        for part in series_parts:
            part = part.strip()
            if not part:
                continue

            # Substitui a vírgula do decimal por ponto, se houver
            part = part.replace(",", ".")

            # Valida caracteres permitidos na parte
            # Remove espaços antes de validar
            part_no_space = "".join(part.split())
            if not re.match(allowed_chars, part_no_space.replace("__parallel__", "")):
                # Permite __parallel__ na checagem mas não valida os caracteres dentro dele diretamente
                # A segurança vem de só permitir a função calculate_parallel
                is_parallel_call = "__parallel__" in part
                temp_part_for_check = part
                if is_parallel_call:
                    # Simplifica a checagem permitindo a estrutura da chamada
                    temp_part_for_check = re.sub(r"__parallel__\s*\(.+?\)", "1.0", part)

                if not re.match(allowed_chars, "".join(temp_part_for_check.split())):
                    log.error(
                        f"Parte da expressão de resistor contém caracteres inválidos: '{part}'"
                    )
                    return float("inf"), special_components

            try:
                # Avalia a parte no ambiente seguro
                part_value = eval(part, {"__builtins__": {}}, safe_dict)
                if (
                    not isinstance(part_value, (int, float))
                    or part_value < 0
                    or math.isinf(part_value)
                    or math.isnan(part_value)
                ):
                    log.warning(
                        f"Parte da expressão resultou em valor inválido: {part} -> {part_value}"
                    )
                    return float("inf"), special_components
                total_resistance += part_value
            except ZeroDivisionError:
                log.error(f"Divisão por zero ao avaliar parte da expressão: {part}")
                return float("inf"), special_components
            except Exception as e:
                log.error(f"Erro ao avaliar parte da expressão '{part}': {e}")
                return float("inf"), special_components

        if total_resistance < 0 or math.isinf(total_resistance) or math.isnan(total_resistance):
            log.warning(f"Resistência total calculada inválida: {total_resistance}")
            return float("inf"), special_components

        log.debug(
            f"Expressão '{expression}' -> Resistência: {total_resistance:.3f} Ω, Especiais: {special_components}"
        )
        return total_resistance, special_components

    except Exception as e:
        log.exception(f"Erro inesperado ao analisar expressão de resistor '{expression}': {e}")
        return float("inf"), special_components


# === Funções Relacionadas ao Gerador de Impulso (de impulse.py) ===


def get_generator_params(config_value: str) -> tuple[int, int, float, float]:
    """Obtém os parâmetros (estágios, paralelo, Vmax, Energia) de uma configuração."""
    config = next(
        (item for item in constants.GENERATOR_CONFIGURATIONS if item["value"] == config_value), None
    )
    if config:
        try:
            stages = int(config["stages"])
            parallel = int(config["parallel"])
            max_voltage_kv = float(config["max_voltage_kv"])
            energy_kj = float(config.get("energy_kj", 0.0))  # Default 0 se faltar
            if stages <= 0 or parallel <= 0 or max_voltage_kv <= 0:
                raise ValueError("Valores de configuração inválidos (<= 0).")
            return stages, parallel, max_voltage_kv, energy_kj
        except (ValueError, TypeError, KeyError) as e:
            log.error(
                f"Erro ao ler parâmetros da configuração '{config_value}': {e}. Usando padrão 12S-1P."
            )
    else:
        log.warning(
            f"Configuração do gerador '{config_value}' não encontrada. Usando padrão 12S-1P."
        )

    # Fallback para padrão 12S-1P
    default_config = next(
        (item for item in constants.GENERATOR_CONFIGURATIONS if item["value"] == "12S-1P"), {}
    )
    return (
        default_config.get("stages", 12),
        default_config.get("parallel", 1),
        default_config.get("max_voltage_kv", 2400.0),
        default_config.get("energy_kj", 360.0),
    )


def get_divider_capacitance(generator_max_voltage_kv: float) -> float:
    """Retorna a capacitância do divisor baseada na tensão MÁXIMA da configuração."""
    try:
        # Usa as constantes definidas em utils.constants
        if generator_max_voltage_kv <= 1200:
            return constants.C_DIVIDER_LOW_VOLTAGE_F
        else:
            return constants.C_DIVIDER_HIGH_VOLTAGE_F
    except Exception as e:
        log.error(
            f"Erro ao obter capacitância do divisor para Vmax={generator_max_voltage_kv}: {e}. Usando padrão HIGH."
        )
        return constants.C_DIVIDER_HIGH_VOLTAGE_F  # Fallback seguro


def calculate_effective_gen_params(n_stages: int, n_parallel: int) -> tuple[float, float]:
    """Calcula a capacitância e indutância efetivas do gerador."""
    if n_stages <= 0 or n_parallel <= 0:
        log.error("Número de estágios/paralelo deve ser positivo.")
        return 0.0, 0.0
    # Ceq = C / N * P
    c_gen_effective = (constants.C_PER_STAGE_F * n_parallel) / n_stages
    # Leq = L * N / P
    l_gen_effective = (constants.L_PER_STAGE_H * n_stages) / n_parallel
    log.debug(
        f"Parâmetros Efetivos Gerador ({n_stages}S-{n_parallel}P): Cg={c_gen_effective*1e6:.3f} µF, Lg={l_gen_effective*1e6:.3f} µH"
    )
    return c_gen_effective, l_gen_effective


# === Funções de Cálculo de Carga (de impulse.py) ===


def calculate_transformer_inductance(
    voltage_kv: float | None,
    power_mva: float | None,
    impedance_percent: float | None,
    freq_hz: float = constants.DEFAULT_FREQUENCY,
) -> float:
    """Calcula a indutância de curto-circuito (Lcc) do transformador."""
    # Valor padrão típico se dados faltarem
    default_inductance = 0.05
    if voltage_kv is None or power_mva is None or impedance_percent is None or freq_hz is None:
        log.warning(
            f"Dados insuficientes para calcular Lcc do trafo. Usando padrão {default_inductance} H."
        )
        return default_inductance
    try:
        voltage_v = float(voltage_kv) * 1000
        power_va = float(power_mva) * 1e6
        impedance_pu = float(impedance_percent) / 100.0
        freq_hz_f = float(freq_hz)

        if voltage_v <= 0 or power_va <= 0 or freq_hz_f <= 0 or impedance_pu <= 0:
            log.warning(
                f"Valores inválidos (<=0) para cálculo de Lcc: V={voltage_v}, P={power_va}, f={freq_hz_f}, Z%={impedance_pu*100}. Usando padrão {default_inductance} H."
            )
            return default_inductance

        omega = 2 * np.pi * freq_hz_f
        z_base = (voltage_v**2) / power_va  # Ohm
        z_cc_ohm = z_base * impedance_pu  # Ohm
        # Assume que Zcc é predominantemente indutivo (Xcc)
        l_cc = z_cc_ohm / omega  # Henry

        # Limita a indutância a um valor razoável (ex: > 1 mH)
        if l_cc < 1e-4:
            log.warning(
                f"Indutância calculada muito baixa ({l_cc:.4e} H), pode indicar erro nos dados. Retornando padrão {default_inductance} H."
            )
            return default_inductance

        log.info(
            f"Indutância do trafo calculada (Lcc): {l_cc:.4f} H (V={voltage_kv}kV, P={power_mva}MVA, Z={impedance_percent}%, f={freq_hz_f}Hz)"
        )
        return l_cc
    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(
            f"Erro ao calcular indutância do trafo: {e}. Usando padrão {default_inductance} H."
        )
        return default_inductance


def calculate_total_load_capacitance(
    c_dut_pf: float | None,
    c_stray_pf: float | None,
    impulse_type: str,
    generator_max_voltage_kv: float,
) -> float:
    """Calcula a capacitância total da carga vista pelo gerador."""
    c_dut_f = float(c_dut_pf or 0.0) * 1e-12  # Converte pF para F, default 0
    c_stray_f = float(c_stray_pf or 0.0) * 1e-12  # Converte pF para F, default 0
    c_divider_f = get_divider_capacitance(generator_max_voltage_kv)
    c_load_extra_f = constants.C_CHOPPING_GAP_F if impulse_type == "chopped" else 0.0

    c_load_total_f = c_dut_f + c_divider_f + c_stray_f + c_load_extra_f
    log.debug(
        f"Carga Total: C_dut={c_dut_f*1e12:.0f}pF, C_div={c_divider_f*1e12:.0f}pF, C_stray={c_stray_f*1e12:.0f}pF, C_extra={c_load_extra_f*1e12:.0f}pF => C_load={c_load_total_f*1e9:.2f}nF"
    )
    return c_load_total_f


# === Funções de Cálculo de Eficiência e Energia (de impulse.py) ===


def calculate_circuit_efficiency(
    c_gen_effective_f: float, c_load_total_f: float, impulse_type: str
) -> tuple[float, float, float]:
    """Calcula a eficiência total, do circuito e de forma."""
    if c_gen_effective_f <= 0 or c_load_total_f < 0:
        log.warning(
            f"Capacitâncias inválidas para cálculo de eficiência: Cg_eff={c_gen_effective_f}, C_load={c_load_total_f}"
        )
        return 0.0, 0.0, 0.0

    # Eficiência do circuito (η_c = Cg / (Cg + Cl))
    denominator = c_gen_effective_f + c_load_total_f
    circuit_efficiency = c_gen_effective_f / denominator if denominator > 1e-15 else 0.0

    # Eficiência de forma (η_s) - Estimativa
    # Pode ser mais complexo, dependendo de Rf, Rt, L
    shape_efficiency = (
        0.95 if impulse_type in ["lightning", "chopped"] else 0.85
    )  # Ajustado para SI

    # Eficiência total (η = η_c * η_s)
    total_efficiency = circuit_efficiency * shape_efficiency
    log.debug(
        f"Eficiência: Total={total_efficiency:.3f} (Circuito={circuit_efficiency:.3f} * Forma={shape_efficiency:.2f})"
    )
    return total_efficiency, circuit_efficiency, shape_efficiency


def calculate_energy_requirements(
    actual_test_voltage_kv: float | None, c_load_total_f: float | None
) -> float:
    """Calcula a energia requerida pela carga durante o ensaio em kJ."""
    if actual_test_voltage_kv is None or c_load_total_f is None or c_load_total_f < 0:
        return 0.0
    try:
        test_voltage_v = float(actual_test_voltage_kv) * 1000
        c_load = float(c_load_total_f)
        if test_voltage_v < 0:
            return 0.0

        energy_joules = 0.5 * c_load * (test_voltage_v**2)
        energy_kj = energy_joules / 1000
        log.debug(
            f"Energia requerida pela carga @ {actual_test_voltage_kv:.1f} kV (C={c_load*1e9:.2f} nF): {energy_kj:.2f} kJ"
        )
        return energy_kj
    except (ValueError, TypeError) as e:
        log.error(f"Erro ao calcular energia requerida: {e}")
        return 0.0


# === Funções de Cálculo de Parâmetros de Circuito (de impulse.py) ===


def calculate_rlc_equivalent_params(
    n_stages: int,
    n_parallel: int,
    rf_per_column: float,
    rt_per_column: float,
    c_load_total_f: float,
    l_extra_h: float,
    l_transformer_h: float,
    l_inductor_h: float,
    inductance_factor: float = 1.0,
    tail_resistance_factor: float = 1.0,
) -> dict | None:
    """
    Calcula os parâmetros RLC equivalentes do circuito de impulso,
    incluindo Cg_eff, Lg_eff, L_total, C_eq, Rf_total, Rt_total, alpha, beta, omega0, zeta.

    Retorna um dicionário com os parâmetros ou None em caso de erro.
    """
    log.debug(
        f"Calculando RLC equiv. para {n_stages}S-{n_parallel}P, Rf={rf_per_column}, Rt={rt_per_column}"
    )
    if (
        n_stages <= 0
        or n_parallel <= 0
        or rf_per_column <= 0
        or rt_per_column <= 0
        or c_load_total_f < 0
    ):
        log.error("Parâmetros de entrada inválidos para cálculo RLC equivalente.")
        return None

    try:
        c_gen_effective, l_gen_effective = calculate_effective_gen_params(n_stages, n_parallel)
        if c_gen_effective <= 0:
            return None  # Erro já logado em calculate_effective_gen_params

        c_eq = (
            (c_gen_effective * c_load_total_f) / (c_gen_effective + c_load_total_f)
            if (c_gen_effective + c_load_total_f) > 1e-15
            else 0.0
        )

        rf_total_initial = (rf_per_column * n_stages) / n_parallel
        rt_total_initial = (rt_per_column * n_stages) / n_parallel

        l_total_initial = l_gen_effective + l_extra_h + l_transformer_h + l_inductor_h
        log.debug(
            f"Componentes L inicial: Lgen={l_gen_effective:.3e}, Lext={l_extra_h:.3e}, Ltrafo={l_transformer_h:.3e}, Ladd={l_inductor_h:.3e} => Ltotal_init={l_total_initial:.3e} H"
        )

        # Aplica fatores de ajuste
        rf_total = rf_total_initial  # Fator de ajuste para Rf não implementado aqui
        rt_total = rt_total_initial * tail_resistance_factor
        l_total = l_total_initial * inductance_factor
        log.debug(
            f"Ajustes: L_factor={inductance_factor:.2f}, Rt_factor={tail_resistance_factor:.2f} => L_total={l_total:.3e} H, Rt_total={rt_total:.2f} Ohm"
        )

        # Calcula constantes de tempo e parâmetros RLC
        # Alpha ~ 1 / (Rt * (Cg + Cl))
        alpha = (
            1.0 / (rt_total * (c_gen_effective + c_load_total_f))
            if rt_total > 1e-9 and (c_gen_effective + c_load_total_f) > 1e-15
            else 0.0
        )
        # Beta ~ 1 / (Rf * Ceq)
        beta = 1.0 / (rf_total * c_eq) if rf_total > 1e-9 and c_eq > 1e-15 else 0.0

        # Garante Beta > Alpha para função dupla exponencial padrão
        if beta <= alpha + 1e-9:  # Adiciona pequena tolerância
            adjust_factor = 1.05
            add_factor = 1e3  # Valor arbitrário para garantir separação
            new_beta = alpha * adjust_factor + add_factor
            log.warning(
                f"Beta calculado ({beta:.2e}) <= Alpha ({alpha:.2e}). Ajustando Beta para {new_beta:.2e} para evitar singularidade."
            )
            beta = new_beta  # Usa o beta ajustado

        # Parâmetros RLC para oscilação
        r_damping = rf_total + constants.R_PARASITIC_OHM  # Resistência total para amortecimento RLC
        omega0_sq = 1.0 / (l_total * c_eq) if l_total * c_eq > 1e-18 else 0.0
        omega0 = math.sqrt(omega0_sq) if omega0_sq > 0 else 0.0
        # Fator de amortecimento (zeta = R / (2 * L * omega0))
        zeta = r_damping / (2 * l_total * omega0) if l_total * omega0 > 1e-12 else float("inf")
        is_oscillatory = zeta < 1.0 if omega0 > 0 else False

        log.debug(
            f"Parâmetros RLC Efetivos: Cg={c_gen_effective:.3e}F, Cl={c_load_total_f:.3e}F, Ceq={c_eq:.3e}F"
        )
        log.debug(
            f"                       Rf={rf_total:.2f}Ω, Rt={rt_total:.2f}Ω, L={l_total:.3e}H"
        )
        log.debug(f"Constantes: Alpha={alpha:.2e} s⁻¹, Beta={beta:.2e} s⁻¹")
        log.debug(
            f"Amortecimento: R_damp={r_damping:.2f}Ω, ω0={omega0:.2e} rad/s, ζ={zeta:.3f}, Oscilatório={is_oscillatory}"
        )

        return {
            "c_gen_effective_f": c_gen_effective,
            "l_gen_effective_h": l_gen_effective,
            "c_load_total_f": c_load_total_f,
            "c_eq_f": c_eq,
            "rf_total_ohm": rf_total,
            "rt_total_ohm": rt_total,
            "l_total_h": l_total,
            "alpha": alpha,
            "beta": beta,
            "r_damping_ohm": r_damping,
            "omega0_rad_s": omega0,
            "zeta": zeta,
            "is_oscillatory": is_oscillatory,
        }

    except Exception as e:
        log.exception(f"Erro ao calcular parâmetros RLC equivalentes: {e}")
        return None


# === Funções de Simulação da Forma de Onda (de impulse.py) ===


def rlc_solution(
    t_sec: np.ndarray, v0: float, r_total: float, l_total: float, c_eq: float
) -> np.ndarray:
    """Calcula a solução da EDO para o circuito RLC série (resposta ao degrau)."""
    v_out = np.zeros_like(t_sec)
    # Verifica parâmetros básicos
    if l_total <= 1e-12 or c_eq <= 1e-15:
        log.warning(f"Parâmetros L ou Ceq inválidos para solução RLC: L={l_total}, Ceq={c_eq}")
        return v_out  # Retorna zeros
    if r_total < 0:  # Resistência não pode ser negativa
        log.warning(f"Resistência total negativa ({r_total}) inválida para solução RLC.")
        return v_out

    try:
        omega0_sq = 1.0 / (l_total * c_eq)
        alpha_damp = r_total / (2.0 * l_total) if l_total > 1e-12 else float("inf")

        if alpha_damp < 0:  # Amortecimento não pode ser negativo
            log.warning(f"Fator de amortecimento alpha_damp ({alpha_damp}) negativo inválido.")
            return v_out

        delta = alpha_damp**2 - omega0_sq
        t_valid = t_sec[t_sec >= 0]  # Calcula apenas para t >= 0

        if abs(delta / omega0_sq) < 1e-6:  # Criticamente Amortecido (delta ≈ 0)
            if alpha_damp < 1e-9:  # Praticamente não amortecido
                omega_n = math.sqrt(omega0_sq)
                v_out[t_sec >= 0] = v0 * np.cos(omega_n * t_valid)
            else:
                a = alpha_damp
                v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
            log.debug("RLC: Caso Criticamente Amortecido")

        elif delta < 0:  # Subamortecido (Oscilatório)
            omega_d = np.sqrt(-delta)
            a = alpha_damp
            if omega_d < 1e-6 * a:  # Próximo ao crítico
                v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
                log.debug("RLC: Caso Subamortecido (próximo ao crítico)")
            elif a < 1e-9:  # R=0 (oscilador puro)
                omega_n = math.sqrt(omega0_sq)
                v_out[t_sec >= 0] = v0 * np.cos(omega_n * t_valid)
                log.debug("RLC: Caso Subamortecido (R=0, Oscilador Puro)")
            else:
                cos_term = np.cos(omega_d * t_valid)
                sin_term = (a / omega_d) * np.sin(omega_d * t_valid)
                exp_term = np.exp(-a * t_valid)
                v_out[t_sec >= 0] = v0 * exp_term * (cos_term + sin_term)
                log.debug("RLC: Caso Subamortecido (Oscilatório)")

        else:  # Sobreamortecido (delta > 0)
            sqrt_delta = np.sqrt(delta)
            s1 = -alpha_damp + sqrt_delta
            s2 = -alpha_damp - sqrt_delta

            if s1 > 1e-9 or s2 > 1e-9:
                log.warning(
                    f"Raízes instáveis ou zeradas na solução RLC sobreamortecida: s1={s1:.2e}, s2={s2:.2e}."
                )
                return np.zeros_like(t_sec)

            if abs(s1 - s2) < 1e-9 * abs(s1 + s2):  # Quase criticamente amortecido
                a = alpha_damp
                v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
                log.debug("RLC: Caso Sobreamortecido (próximo ao crítico)")
            else:
                exp_s1 = np.exp(s1 * t_valid)
                exp_s2 = np.exp(s2 * t_valid)
                v_out[t_sec >= 0] = v0 / (s1 - s2) * (s1 * exp_s2 - s2 * exp_s1)
                log.debug("RLC: Caso Sobreamortecido")

        # Limit output based on v0 (Allowing for some overshoot/undershoot)
        v_out[v_out > v0 * 1.1] = v0 * 1.1  # Limit overshoot to 10%
        v_out[v_out < -v0 * 0.3] = -v0 * 0.3  # Limit undershoot to 30% (adjust as needed)

        return v_out
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        log.error(f"Erro na solução RLC: {e}")
        return np.zeros_like(t_sec)


def double_exp_func(t_sec: np.ndarray, V0_norm: float, alpha: float, beta: float) -> np.ndarray:
    """
    Função de dupla exponencial normalizada V(t) = K * [exp(-alpha*t) - exp(-beta*t)],
    onde K é ajustado para que o pico da função seja V0_norm.
    Requer beta > alpha.
    """
    v_out = np.zeros_like(t_sec)
    if alpha <= 0 or beta <= 0:
        log.warning(
            f"Alpha ({alpha}) ou Beta ({beta}) inválido (não positivo) para dupla exponencial."
        )
        return v_out
    if beta <= alpha + 1e-9 * alpha:  # Adiciona tolerância relativa
        log.warning(
            f"Beta ({beta:.3e}) deve ser maior que Alpha ({alpha:.3e}) para dupla exponencial."
        )
        return v_out
    # Allow negative V0_norm, as it might represent negative polarity pulses
    # if V0_norm < 0:
    #      log.warning(f"V0_norm ({V0_norm}) negativo não usual para dupla exponencial padrão.")

    try:
        t_peak = math.log(beta / alpha) / (beta - alpha)
        val_at_peak = math.exp(-alpha * t_peak) - math.exp(-beta * t_peak)

        if abs(val_at_peak) < 1e-12:
            log.warning(
                "Valor no pico da dupla exponencial próximo de zero. Não é possível normalizar."
            )
            return v_out

        k_norm = V0_norm / val_at_peak
        t_valid = np.maximum(t_sec, 0)
        exp_alpha = np.exp(-alpha * t_valid)
        exp_beta = np.exp(-beta * t_valid)
        v_out = k_norm * (exp_alpha - exp_beta)
        return v_out

    except (ValueError, OverflowError, ZeroDivisionError) as e:
        log.error(f"Erro na função dupla exponencial: {e}")
        return np.zeros_like(t_sec)


def calculate_k_factor_transform(
    v_kv: np.ndarray, t_us: np.ndarray, return_params: bool = False
) -> tuple:
    """
    Aplica a transformação K-factor (IEC 61083-2) a uma forma de onda de impulso.

    Args:
        v_kv: Array de tensão em kV.
        t_us: Array de tempo em µs.
        return_params: Se True, retorna também os parâmetros alpha e beta ajustados.

    Returns:
        Uma tupla contendo:
        - v_test_kv (np.ndarray): Onda de ensaio filtrada.
        - v_base_kv (np.ndarray): Curva base (dupla exponencial ajustada).
        - v_residual_filtered (np.ndarray): Resíduo filtrado.
        - overshoot_rel (float): Overshoot relativo em %.
        - (alpha_fit, beta_fit) (tuple | None): Parâmetros ajustados, se return_params=True.
    """
    log.debug("Aplicando transformação K-Factor...")
    v_test = np.copy(v_kv)
    v_base = np.copy(v_kv)
    v_residual_filtered = np.zeros_like(v_kv)
    overshoot_rel = 0.0
    alpha_fit, beta_fit = None, None
    fit_success = False

    # --- Validações Iniciais ---
    if (
        not isinstance(v_kv, np.ndarray)
        or not isinstance(t_us, np.ndarray)
        or v_kv.ndim != 1
        or t_us.ndim != 1
        or len(v_kv) != len(t_us)
        or len(v_kv) < 10
    ):
        log.warning("Dados de entrada inválidos para K-factor (tamanho/tipo).")
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )
    if np.std(v_kv) < 1e-9 * np.mean(np.abs(v_kv)):
        log.warning("Variação muito baixa na tensão para aplicar K-factor.")
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )
    if t_us[-1] <= t_us[0]:
        log.warning("Vetor de tempo inválido (não crescente) para K-factor.")
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )

    peak_value_orig = np.max(v_kv)
    if abs(peak_value_orig) < 1e-3:  # Check absolute value for negative pulses
        log.warning(
            f"Amplitude de pico ({peak_value_orig:.2e} kV) muito baixa para K-factor significativo."
        )
        return (
            (v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit))
            if return_params
            else (v_test, v_base, v_residual_filtered, overshoot_rel)
        )

    # --- 1. Ajuste da Curva Base (Dupla Exponencial) ---
    try:
        t_sec = t_us * 1e-6
        peak_idx = np.argmax(v_kv)
        t_peak_sec = t_sec[peak_idx]

        # Find t_half (time to 50% on the tail) - more robustly
        v_half_target = 0.5 * peak_value_orig
        indices_after_peak = np.where(t_sec >= t_peak_sec)[0]
        if len(indices_after_peak) < 2:  # Need at least two points for interpolation
            raise ValueError("Not enough data points after peak to find t_half.")

        v_after_peak = v_kv[indices_after_peak]
        t_after_peak = t_sec[indices_after_peak]

        # Find where voltage drops below 50% target
        # Handle cases where voltage might oscillate around 50%
        crossed_indices = np.where(np.diff(np.sign(v_after_peak - v_half_target)))[0]
        t_half_sec = t_sec[-1]  # Default to last time if it never drops below 50%
        if len(crossed_indices) > 0:
            # Find the first crossing index after the peak
            first_cross_idx = crossed_indices[0]
            idx1 = first_cross_idx
            idx2 = first_cross_idx + 1
            if idx1 < len(t_after_peak) and idx2 < len(t_after_peak):
                t1_tail, v1_tail = t_after_peak[idx1], v_after_peak[idx1]
                t2_tail, v2_tail = t_after_peak[idx2], v_after_peak[idx2]
                if abs(v2_tail - v1_tail) > 1e-9:  # Avoid division by zero
                    t_half_sec = t1_tail + (v_half_target - v1_tail) * (t2_tail - t1_tail) / (
                        v2_tail - v1_tail
                    )
                elif v1_tail >= v_half_target:  # If already at or above the point
                    t_half_sec = t1_tail
                else:  # If v2_tail is the point or below
                    t_half_sec = t2_tail
            else:
                log.warning("Indices for t_half interpolation out of bounds.")
        elif np.all(v_after_peak > v_half_target):
            log.warning("Voltage never dropped below 50% on tail.")
            t_half_sec = t_sec[-1]  # Use last time point

        # Estimate initial parameters
        T2_approx_sec = max(1.4 * t_half_sec, 5e-6)
        T1_approx_sec = max(t_peak_sec, 0.5e-6) if t_peak_sec > 0 else 1e-6
        alpha_est = 1.0 / T2_approx_sec
        beta_est = 2.0 / T1_approx_sec
        if beta_est <= alpha_est:
            beta_est = alpha_est * 5
        A_est = peak_value_orig

        def _double_exp_fit_func(t, A_norm, alpha, beta):
            try:
                if alpha <= 0 or beta <= 0 or beta <= alpha + 1e-9 * alpha:
                    return np.full_like(t, 1e12)
                t_peak = math.log(beta / alpha) / (beta - alpha)
                val_at_peak = math.exp(-alpha * t_peak) - math.exp(-beta * t_peak)
                if abs(val_at_peak) < 1e-12:
                    return np.zeros_like(t)
                k_norm = A_norm / val_at_peak
                t_safe = np.maximum(t, 0)
                res = k_norm * (np.exp(-alpha * t_safe) - np.exp(-beta * t_safe))
                return res
            except (ValueError, OverflowError, ZeroDivisionError):
                return np.full_like(t, 1e12)

        # Adjust bounds based on sign of A_est
        if A_est > 0:
            lower_bounds = [A_est * 0.5, alpha_est * 0.1, beta_est * 0.1]
            upper_bounds = [A_est * 1.5, alpha_est * 10, beta_est * 10]
        else:  # Negative pulse
            lower_bounds = [A_est * 1.5, alpha_est * 0.1, beta_est * 0.1]  # A_est is negative
            upper_bounds = [A_est * 0.5, alpha_est * 10, beta_est * 10]  # A_est is negative

        p0 = [A_est, alpha_est, beta_est]

        popt, pcov = curve_fit(
            _double_exp_fit_func,
            t_sec,
            v_kv,
            p0=p0,
            bounds=(lower_bounds, upper_bounds),
            maxfev=5000,
            method="trf",
        )

        A_fit, alpha_fit, beta_fit = popt
        log.debug(
            f"Ajuste Curva Base K-Factor: A={A_fit:.2f}, alpha={alpha_fit:.2e}, beta={beta_fit:.2e}"
        )
        v_base = _double_exp_fit_func(t_sec, A_fit, alpha_fit, beta_fit)
        fit_success = True

    except (RuntimeError, ValueError, OptimizeWarning, Exception) as e:
        log.warning(
            f"Ajuste da curva base para K-Factor falhou: {e}. Usando onda original como base."
        )
        v_base = np.copy(v_kv)  # Use original as base if fit fails
        alpha_fit, beta_fit = None, None
        fit_success = False

    # --- 2. Cálculo do Resíduo ---
    v_residual = v_kv - v_base  # This is kV

    # --- 3. Filtragem do Resíduo (Filtro K) ---
    if fit_success and len(t_us) > 1:
        dt_us = np.mean(np.diff(t_us))
        if dt_us > 1e-9:
            dt_sec = dt_us * 1e-6
            try:
                frequencies = fftfreq(len(t_us), dt_sec)
                v_residual_fft = fft(v_residual)

                # IEC 61083-2 filter K(f) = 1 / (1 + (f / fc)^2)^n
                # Parameters: fc = 0.2 MHz, n = 1.1
                fc_mhz = 0.2
                n_filter = 1.1
                f_mhz = np.abs(frequencies) * 1e-6

                # Calculate |K(f)|^2 = 1 / (1 + (f/fc)^2)^(2n)
                filter_power = np.ones_like(frequencies, dtype=float)
                non_zero_freq_mask = f_mhz > 1e-12
                denominator = 1.0 + (f_mhz[non_zero_freq_mask] / fc_mhz) ** 2
                # Add small epsilon to avoid issues with denominator near 1 if needed
                filter_power[non_zero_freq_mask] = 1.0 / (denominator ** (2 * n_filter) + 1e-18)

                # Apply the amplitude filter K(f) = sqrt(|K(f)|^2)
                k_filter_amplitude = np.sqrt(filter_power + 0j)
                v_residual_filtered_fft = v_residual_fft * k_filter_amplitude
                v_residual_filtered = np.real(ifft(v_residual_filtered_fft))

            except Exception as e_fft:
                log.error(
                    f"Erro durante FFT/Filtragem/IFFT no K-factor: {e_fft}. Resíduo filtrado será zero."
                )
                v_residual_filtered = np.zeros_like(v_residual)
        else:
            log.warning(
                "Passo de tempo inválido ou ajuste base falhou. Resíduo filtrado K-factor será zero."
            )
            v_residual_filtered = np.zeros_like(v_residual)
    else:  # If fit failed
        v_residual_filtered = np.zeros_like(v_residual)

    # --- 4. Cálculo da Onda de Ensaio Vt(t) ---
    v_test = v_base + v_residual_filtered
    # Keep negative values if the pulse is negative polarity
    # v_test = np.maximum(v_test, 0) # Remove this line

    # --- 5. Cálculo do Overshoot ---
    peak_value_base = np.max(np.abs(v_base)) if len(v_base) > 0 else 0
    # Overshoot = max(v_residual) / |peak_base| * 100%
    if peak_value_base > 1e-9:
        max_residual = np.max(v_residual)  # Use the actual residual, not filtered
        overshoot_rel = max(0.0, (max_residual / peak_value_base)) * 100.0
        log.debug(
            f"Overshoot K-Factor: Vp_orig={peak_value_orig:.2f}, Vp_base={np.max(v_base):.2f}, MaxRes={max_residual:.2f} => Overshoot={overshoot_rel:.1f}%"
        )
    else:
        overshoot_rel = 0.0

    if return_params:
        return v_test, v_base, v_residual_filtered, overshoot_rel, (alpha_fit, beta_fit)
    else:
        return v_test, v_base, v_residual_filtered, overshoot_rel


# --- Funções de Análise de Forma de Onda (de impulse.py) ---


def analyze_lightning_impulse(t_us: np.ndarray, v_kv: np.ndarray) -> dict:
    """Analisa parâmetros de Impulso Atmosférico (LI) usando K-Factor."""
    log.info("Analisando Impulso Atmosférico (LI)...")
    results = {
        "waveform_type": "LI",
        "peak_value_measured": None,
        "peak_value_base": None,
        "peak_value_test": None,
        "peak_time_test_us": None,
        "t_30_us": None,
        "t_90_us": None,
        "t_0_virtual_us": None,
        "t_front_us": None,
        "t_50_us": None,
        "t_tail_us": None,
        "overshoot_percent": 0.0,
        "params_base_alpha": None,
        "params_base_beta": None,
        "conforme_frente": False,
        "conforme_cauda": False,
        "conforme_overshoot": True,
        "conforme_pico": False,  # Pico check needs target
        "status_geral": "Indeterminado",
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
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results

        results["peak_value_measured"] = np.max(v_kv)

        # 1. Aplica K-Factor
        v_test_kv, v_base_kv, _, overshoot_rel, params_base = calculate_k_factor_transform(
            v_kv, t_us, return_params=True
        )
        results["overshoot_percent"] = overshoot_rel
        results["peak_value_base"] = (
            np.max(v_base_kv) if v_base_kv is not None and len(v_base_kv) > 0 else 0.0
        )
        if params_base:
            results["params_base_alpha"], results["params_base_beta"] = params_base

        if (
            v_test_kv is None
            or len(v_test_kv) < 5
            or np.std(v_test_kv) < 1e-6 * np.mean(np.abs(v_test_kv))
        ):
            results["error"] = "Onda de ensaio (Vt) inválida após K-factor. Usando original."
            log.warning(results["error"])
            v_test_kv = v_kv
            results["overshoot_percent"] = 0.0  # Assume zero overshoot if K-factor failed

        # 2. Encontra Pico de Vt
        test_peak_idx = np.argmax(v_test_kv)
        results["peak_time_test_us"] = t_us[test_peak_idx]
        results["peak_value_test"] = v_test_kv[test_peak_idx]

        # 3. Análise da Frente (T1 e O1) baseada em Vt
        t_0_virtual_us = 0.0
        if results["peak_value_test"] > 1e-6:
            v_30_target = 0.3 * results["peak_value_test"]
            v_90_target = 0.9 * results["peak_value_test"]
            mask_before_peak = t_us <= results["peak_time_test_us"]
            t_before_us = t_us[mask_before_peak]
            v_before_kv = v_test_kv[mask_before_peak]

            if len(v_before_kv) > 1:
                v_min_b, v_max_b = np.min(v_before_kv), np.max(v_before_kv)
                if v_max_b >= v_90_target and v_min_b <= v_30_target:
                    try:
                        t_30 = np.interp(
                            v_30_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                        )
                        t_90 = np.interp(
                            v_90_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                        )
                        results["t_30_us"] = t_30
                        results["t_90_us"] = t_90
                        if not np.isnan(t_30) and not np.isnan(t_90) and t_90 > t_30:
                            delta_t_front = t_90 - t_30
                            results["t_front_us"] = 1.67 * delta_t_front
                            if delta_t_front > 1e-9:
                                slope = (v_90_target - v_30_target) / delta_t_front
                                if abs(slope) > 1e-9:
                                    t_0_virtual_us = t_30 - (v_30_target / slope)
                                else:
                                    t_0_virtual_us = t_30
                            results["t_0_virtual_us"] = t_0_virtual_us
                        else:
                            log.warning("t30 ou t90 inválidos ou não crescentes.")
                    except Exception as e_interp_front:
                        log.error(f"Erro interpolação frente LI: {e_interp_front}")
                else:
                    log.warning(f"Níveis 30%/90% fora do range ({v_min_b:.2f}-{v_max_b:.2f}).")
            else:
                log.warning("Dados insuficientes antes do pico.")
        else:
            log.warning("Pico de Vt muito baixo.")

        # 4. Análise da Cauda (T2) baseada em Vt
        v_50_target = 0.5 * results["peak_value_test"]
        mask_after_peak = t_us >= results["peak_time_test_us"]
        t_after_us = t_us[mask_after_peak]
        v_after_kv = v_test_kv[mask_after_peak]

        if len(v_after_kv) > 1 and np.min(v_after_kv) <= v_50_target + 1e-6:
            try:
                # Robust interpolation for t_50
                indices_below_50 = np.where(v_after_kv <= v_50_target)[0]
                if len(indices_below_50) > 0:
                    idx2 = indices_below_50[0]
                    idx1 = idx2 - 1 if idx2 > 0 else 0
                    t1_tail, v1_tail = t_after_us[idx1], v_after_kv[idx1]
                    t2_tail, v2_tail = t_after_us[idx2], v_after_kv[idx2]
                    if abs(v2_tail - v1_tail) > 1e-9:
                        t_50 = t1_tail + (v_50_target - v1_tail) * (t2_tail - t1_tail) / (
                            v2_tail - v1_tail
                        )
                    elif v1_tail >= v_50_target:
                        t_50 = t1_tail
                    else:
                        t_50 = t2_tail  # Should ideally not happen if search is correct
                    if not np.isnan(t_50):
                        results["t_50_us"] = t_50
                        results["t_tail_us"] = t_50 - t_0_virtual_us
            except Exception as e_interp_tail:
                log.error(f"Erro interpolação cauda LI: {e_interp_tail}")
        else:
            log.warning("Dados insuficientes ou tensão não caiu para 50% na cauda.")

        # 5. Verificação de Conformidade
        t1 = results["t_front_us"]
        t2 = results["t_tail_us"]
        vt = results["peak_value_test"]
        beta = results["overshoot_percent"]
        if t1 is not None:
            results["conforme_frente"] = (
                constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 - constants.LIGHTNING_FRONT_TOLERANCE)
                <= t1
                <= constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 + constants.LIGHTNING_FRONT_TOLERANCE)
            )
        if t2 is not None:
            results["conforme_cauda"] = (
                constants.LIGHTNING_IMPULSE_TAIL_TIME_NOM * (1 - constants.LIGHTNING_TAIL_TOLERANCE)
                <= t2
                <= constants.LIGHTNING_IMPULSE_TAIL_TIME_NOM
                * (1 + constants.LIGHTNING_TAIL_TOLERANCE)
            )
        if beta is not None:
            results["conforme_overshoot"] = beta <= (constants.LIGHTNING_OVERSHOOT_MAX * 100.0)
        # Conformidade de pico é omitida por padrão, precisa de um alvo

        if (
            results["conforme_frente"]
            and results["conforme_cauda"]
            and results["conforme_overshoot"]
        ):
            results["status_geral"] = "Conforme"
        else:
            results["status_geral"] = "Não Conforme"

        log.info(
            f"Análise LI Concluída: Vt={vt:.2f}kV, T1={t1:.2f}µs, T2={t2:.1f}µs, β={beta:.1f}%, Status={results['status_geral']}"
        )
        return results

    except Exception as e:
        log.exception(f"Erro geral em analyze_lightning_impulse: {e}")
        results["error"] = f"Erro inesperado: {str(e)}"
        results["status_geral"] = "Erro"
        return results


def analyze_switching_impulse(t_us: np.ndarray, v_kv: np.ndarray) -> dict:
    """Analisa parâmetros de Impulso de Manobra (SI) conforme IEC 60060-1."""
    log.info("Analisando Impulso de Manobra (SI)...")
    results = {
        "waveform_type": "SI",
        "peak_value_measured": None,
        "peak_time_us": None,
        "t_p_us": None,
        "t_d_us": None,
        "t_half_us": None,
        "t_2_us": None,
        "t_z_us": None,
        "t_zero_us": None,
        "t_ab_us": None,
        "t_30_us": None,
        "t_90_us": None,
        "conforme_tp": False,
        "conforme_t2": False,
        "conforme_td": False,
        "conforme_tzero": False,
        "status_geral": "Indeterminado",
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
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results

        peak_index = np.argmax(v_kv)
        results["peak_time_us"] = t_us[peak_index]
        results["peak_value_measured"] = v_kv[peak_index]
        t_origin_us = t_us[0]

        # --- Cálculo de Td ---
        v_90_target = 0.9 * results["peak_value_measured"]
        indices_above_90 = np.where(v_kv >= v_90_target)[0]
        if len(indices_above_90) > 1:
            first_idx, last_idx = indices_above_90[0], indices_above_90[-1]
            if 0 <= first_idx < len(t_us) and 0 <= last_idx < len(t_us):
                results["td_us"] = t_us[last_idx] - t_us[first_idx]
            else:
                log.warning("Índices Td fora dos limites.")
        else:
            log.warning("Não foi possível calcular Td (pontos >= 90%).")

        # --- Cálculo de T2 ---
        v_50_target = 0.5 * results["peak_value_measured"]
        mask_after_peak = t_us >= results["peak_time_us"]
        t_after_us = t_us[mask_after_peak]
        v_after_kv = v_kv[mask_after_peak]
        if len(v_after_kv) > 1 and np.min(v_after_kv) <= v_50_target + 1e-6:
            try:
                indices_below_50 = np.where(v_after_kv <= v_50_target)[0]
                if len(indices_below_50) > 0:
                    idx2 = indices_below_50[0]
                    idx1 = max(0, idx2 - 1)
                    t1_tail, v1_tail = t_after_us[idx1], v_after_kv[idx1]
                    t2_tail, v2_tail = t_after_us[idx2], v_after_kv[idx2]
                    if abs(v2_tail - v1_tail) > 1e-9:
                        t_half = t1_tail + (v_50_target - v1_tail) * (t2_tail - t1_tail) / (
                            v2_tail - v1_tail
                        )
                    elif v1_tail >= v_50_target:
                        t_half = t1_tail
                    else:
                        t_half = t2_tail
                    if not np.isnan(t_half):
                        results["t_half_us"] = t_half
                        results["t_2_us"] = t_half - t_origin_us
            except Exception as e:
                log.error(f"Erro interpolação T2 SI: {e}")
        else:
            log.warning("Tensão não caiu para 50% para cálculo T2.")

        # --- Cálculo de Tz ---
        if len(v_after_kv) > 0 and np.min(v_after_kv) <= 1e-6:
            try:
                zero_cross_indices = np.where(v_after_kv <= 0)[0]
                if len(zero_cross_indices) > 0:
                    first_zero_idx_rel = zero_cross_indices[0]
                    first_zero_idx_abs = np.where(t_us == t_after_us[first_zero_idx_rel])[0][0]
                    if first_zero_idx_abs > 0:
                        idx1_z, idx2_z = first_zero_idx_abs - 1, first_zero_idx_abs
                        t1_z, v1_z = t_us[idx1_z], v_kv[idx1_z]
                        t2_z, v2_z = t_us[idx2_z], v_kv[idx2_z]
                        if v1_z > 0 and v2_z <= 0 and abs(v2_z - v1_z) > 1e-9:
                            t_z = t1_z - v1_z * (t2_z - t1_z) / (v2_z - v1_z)
                        elif v2_z <= 0:
                            t_z = t2_z
                        else:
                            t_z = np.nan  # Should not happen if logic is correct
                        if not np.isnan(t_z):
                            results["t_z_us"] = t_z
                            results["t_zero_us"] = t_z - t_origin_us
            except Exception as e:
                log.error(f"Erro interpolação Tz SI: {e}")
        else:
            log.warning("Tensão não cruzou zero para cálculo Tz.")

        # --- Cálculo de Tp ---
        v_30_target = 0.3 * results["peak_value_measured"]
        v_90_target_tp = 0.9 * results["peak_value_measured"]
        mask_before_peak = t_us <= results["peak_time_us"]
        t_before_us = t_us[mask_before_peak]
        v_before_kv = v_kv[mask_before_peak]
        t_30, t_90 = np.nan, np.nan
        if len(v_before_kv) > 1:
            v_min_b, v_max_b = np.min(v_before_kv), np.max(v_before_kv)
            if v_max_b >= v_90_target_tp and v_min_b <= v_30_target:
                try:
                    t_30 = np.interp(
                        v_30_target, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    t_90 = np.interp(
                        v_90_target_tp, v_before_kv, t_before_us, left=np.nan, right=np.nan
                    )
                    results["t_30_us"] = t_30
                    results["t_90_us"] = t_90
                    if not np.isnan(t_30) and not np.isnan(t_90) and t_90 > t_30:
                        results["t_ab_us"] = t_90 - t_30
                except Exception as e:
                    log.error(f"Erro interpolação T_AB SI: {e}")
            else:
                log.warning("Níveis 30%/90% fora do range T_AB.")

        if results.get("t_ab_us") is not None and results.get("t_2_us") is not None:
            try:
                tab, t2 = results["t_ab_us"], results["t_2_us"]
                K = 2.42 - (3.08e-3 * tab) + (1.51e-6 * (t2**2))  # Fórmula K aproximada
                results["t_p_us"] = K * tab
            except Exception as e:
                log.error(f"Erro cálculo Tp fórmula K: {e}")
                results["t_p_us"] = results["peak_time_us"] - t_origin_us
        else:
            results["t_p_us"] = results["peak_time_us"] - t_origin_us

        # --- Verificação de Conformidade ---
        tp, t2, td, tz = (
            results["t_p_us"],
            results["t_2_us"],
            results.get("td_us"),
            results.get("t_zero_us"),
        )
        if tp is not None:
            results["conforme_tp"] = (
                constants.SWITCHING_IMPULSE_PEAK_TIME_NOM
                * (1 - constants.SWITCHING_PEAK_TIME_TOLERANCE)
                <= tp
                <= constants.SWITCHING_IMPULSE_PEAK_TIME_NOM
                * (1 + constants.SWITCHING_PEAK_TIME_TOLERANCE)
            )
        if t2 is not None:
            results["conforme_t2"] = (
                constants.SWITCHING_IMPULSE_TAIL_TIME_NOM * (1 - constants.SWITCHING_TAIL_TOLERANCE)
                <= t2
                <= constants.SWITCHING_IMPULSE_TAIL_TIME_NOM
                * (1 + constants.SWITCHING_TAIL_TOLERANCE)
            )
        if td is not None:
            results["conforme_td"] = td >= constants.SWITCHING_TIME_ABOVE_90_MIN
        if tz is not None:
            results["conforme_tzero"] = tz >= constants.SWITCHING_TIME_TO_ZERO_MIN

        if (
            results["conforme_tp"]
            and results["conforme_t2"]
            and results["conforme_td"]
            and results["conforme_tzero"]
        ):
            results["status_geral"] = "Conforme"
        else:
            results["status_geral"] = "Não Conforme"

        log.info(
            f"Análise SI Concluída: Vp={results['peak_value_measured']:.1f}kV, Tp={tp:.1f}µs, T2={t2:.1f}µs, Td={td:.1f}µs, Tz={tz:.1f}µs, Status={results['status_geral']}"
        )
        return results

    except Exception as e:
        log.exception(f"Erro geral em analyze_switching_impulse: {e}")
        results["error"] = f"Erro inesperado: {str(e)}"
        results["status_geral"] = "Erro"
        return results


def analyze_chopped_impulse(
    t_us: np.ndarray, v_kv: np.ndarray, chop_time_actual_us: float | None
) -> dict:
    """Analisa parâmetros de Impulso Cortado (LIC) usando K-Factor na frente."""
    log.info(f"Analisando Impulso Cortado (LIC) com corte real em ~{chop_time_actual_us:.2f} µs...")
    results = {
        "waveform_type": "LIC",
        "peak_value_full_wave_test": None,
        "peak_time_full_wave_us": None,
        "t_front_us": None,
        "t_0_virtual_us": None,
        "chop_time_us": None,
        "chop_time_absolute_us": None,
        "chop_voltage_test_kv": None,
        "chop_voltage_measured_kv": None,
        "undershoot_percent": 0.0,
        "t_30_us": None,
        "t_90_us": None,
        "conforme_frente": False,
        "conforme_corte": False,
        "conforme_undershoot": True,  # Conformidade Vc omitida
        "status_geral": "Indeterminado",
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
            results["error"] = "Dados de entrada inválidos/insuficientes para análise LIC."
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results
        if (
            chop_time_actual_us is None
            or chop_time_actual_us <= t_us[0]
            or chop_time_actual_us >= t_us[-1]
        ):
            results["error"] = f"Tempo de corte ({chop_time_actual_us}) inválido ou fora do range."
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results

        results["chop_time_absolute_us"] = chop_time_actual_us
        chop_start_index = np.argmin(np.abs(t_us - chop_time_actual_us))
        if chop_start_index < 10:
            results["error"] = f"Tempo de corte ({chop_time_actual_us}µs) muito próximo do início."
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results

        t_before_chop_us = t_us[: chop_start_index + 1]
        v_before_chop_kv = v_kv[: chop_start_index + 1]
        v_test_before_chop, _, _, _, _ = calculate_k_factor_transform(
            v_before_chop_kv, t_before_chop_us, return_params=False
        )
        if v_test_before_chop is None or len(v_test_before_chop) < 5:
            results["error"] = "Falha K-factor na frente cortada."
            log.error(results["error"])
            results["status_geral"] = "Erro"
            return results

        # --- Parâmetros da Onda Plena Subjacente ---
        peak_idx_before = np.argmax(v_test_before_chop)
        results["peak_time_full_wave_us"] = t_before_chop_us[peak_idx_before]
        results["peak_value_full_wave_test"] = v_test_before_chop[peak_idx_before]
        t_0_virtual_us_subj = 0.0
        if results["peak_value_full_wave_test"] > 1e-6:
            v_30_t = 0.3 * results["peak_value_full_wave_test"]
            v_90_t = 0.9 * results["peak_value_full_wave_test"]
            mask_f = t_before_chop_us <= results["peak_time_full_wave_us"]
            t_f_us = t_before_chop_us[mask_f]
            v_f_kv = v_test_before_chop[mask_f]
            if len(v_f_kv) > 1:
                v_min_s, v_max_s = np.min(v_f_kv), np.max(v_f_kv)
                if v_max_s >= v_90_t and v_min_s <= v_30_t:
                    try:
                        t_30 = np.interp(v_30_t, v_f_kv, t_f_us, left=np.nan, right=np.nan)
                        t_90 = np.interp(v_90_t, v_f_kv, t_f_us, left=np.nan, right=np.nan)
                        results["t_30_us"] = t_30
                        results["t_90_us"] = t_90
                        if not np.isnan(t_30) and not np.isnan(t_90) and t_90 > t_30:
                            delta_t = t_90 - t_30
                            results["t_front_us"] = 1.67 * delta_t
                            if delta_t > 1e-9:
                                slope = (v_90_t - v_30_t) / delta_t
                                if abs(slope) > 1e-9:
                                    t_0_virtual_us_subj = t_30 - (v_30_t / slope)
                                else:
                                    t_0_virtual_us_subj = t_30
                            results["t_0_virtual_us"] = t_0_virtual_us_subj
                    except Exception as e:
                        log.error(f"Erro interpolação frente LIC: {e}")
                else:
                    log.warning("Níveis 30/90 não encontrados na frente subj.")
            else:
                log.warning("Dados insuficientes na frente subj.")
        else:
            log.warning("Pico da onda plena subj. muito baixo.")

        # --- Parâmetros do Corte ---
        if results["t_0_virtual_us"] is not None:
            results["chop_time_us"] = results["chop_time_absolute_us"] - results["t_0_virtual_us"]
        results["chop_voltage_test_kv"] = np.interp(
            results["chop_time_absolute_us"],
            t_before_chop_us,
            v_test_before_chop,
            left=np.nan,
            right=np.nan,
        )
        results["chop_voltage_measured_kv"] = v_kv[chop_start_index]

        # --- Undershoot ---
        v_after_chop_kv = v_kv[chop_start_index + 1 :]
        if len(v_after_chop_kv) > 0:
            min_after_chop = np.min(v_after_chop_kv)
            vc_ref = results["chop_voltage_test_kv"]
            if min_after_chop < 0 and vc_ref is not None and abs(vc_ref) > 1e-6:
                results["undershoot_percent"] = max(0.0, abs(min_after_chop) / abs(vc_ref)) * 100.0
                log.debug(
                    f"Undershoot LIC: Vmin={min_after_chop:.2f}, Vc={vc_ref:.2f} => Undershoot={results['undershoot_percent']:.1f}%"
                )
            elif vc_ref is None or abs(vc_ref) < 1e-6:
                log.warning("Vc inválido para undershoot.")

        # --- Conformidade ---
        t1, tc, undershoot = (
            results["t_front_us"],
            results["chop_time_us"],
            results["undershoot_percent"],
        )
        if t1 is not None:
            results["conforme_frente"] = (
                constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM * (1 - constants.CHOPPED_FRONT_TOLERANCE)
                <= t1
                <= constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 + constants.CHOPPED_FRONT_TOLERANCE)
            )
        if tc is not None:
            results["conforme_corte"] = (
                constants.CHOPPED_IMPULSE_CHOP_TIME_MIN
                <= tc
                <= constants.CHOPPED_IMPULSE_CHOP_TIME_MAX
            )
        if undershoot is not None:
            results["conforme_undershoot"] = undershoot <= (
                constants.CHOPPED_UNDERSHOOT_MAX * 100.0
            )

        if (
            results["conforme_frente"]
            and results["conforme_corte"]
            and results["conforme_undershoot"]
        ):
            results["status_geral"] = "Conforme"
        else:
            results["status_geral"] = "Não Conforme"

        log.info(
            f"Análise LIC Concluída: Vc={results['chop_voltage_test_kv']:.1f}kV, T1_subj={t1:.2f}µs, Tc={tc:.2f}µs, Undershoot={undershoot:.1f}%, Status={results['status_geral']}"
        )
        return results

    except Exception as e:
        log.exception(f"Erro geral em analyze_chopped_impulse: {e}")
        results["error"] = f"Erro inesperado: {str(e)}"
        results["status_geral"] = "Erro"
        return results


# === Funções de Cálculo de Elevação de Temperatura (de temperature_rise.py) ===


def calculate_winding_temps(
    rc: float, tc: float, rw: float, ta: float, material: str
) -> tuple[float | None, float | None]:
    """Calcula a temperatura média final e a elevação média do enrolamento."""
    if not all(isinstance(x, (int, float)) for x in [rc, tc, rw, ta]) or rc <= 0 or rw < 0:
        log.error("Valores inválidos para cálculo de temperatura do enrolamento.")
        return None, None
    if material not in constants.TEMP_RISE_CONSTANT:
        log.error(f"Material do enrolamento inválido: {material}")
        return None, None

    C = constants.TEMP_RISE_CONSTANT[material]
    try:
        theta_w = (rw / rc) * (C + tc) - C
        delta_theta_w = theta_w - ta
        log.debug(
            f"Calc Temps: Rc={rc:.3f}Ω, Tc={tc:.1f}°C, Rw={rw:.3f}Ω, Ta={ta:.1f}°C, C={C} => Θw={theta_w:.1f}°C, ΔΘw={delta_theta_w:.1f}K"
        )
        return theta_w, delta_theta_w
    except ZeroDivisionError:
        log.error("Erro: Resistência a frio (Rc) não pode ser zero.")
        return None, None
    except Exception as e:
        log.exception(f"Erro ao calcular temperaturas do enrolamento: {e}")
        return None, None


def calculate_top_oil_rise(t_oil: float, ta: float) -> float | None:
    """Calcula a elevação do topo do óleo sobre o ambiente."""
    if not all(isinstance(x, (int, float)) for x in [t_oil, ta]):
        log.error("Valores inválidos para cálculo de elevação do óleo.")
        return None
    try:
        delta_theta_oil = t_oil - ta
        log.debug(
            f"Calc Oil Rise: Toil={t_oil:.1f}°C, Ta={ta:.1f}°C => ΔΘoil={delta_theta_oil:.1f}K"
        )
        return delta_theta_oil
    except Exception as e:
        log.exception(f"Erro ao calcular elevação do óleo: {e}")
        return None


def calculate_thermal_time_constant(
    ptot_kw: float | None,
    delta_theta_oil_max_k: float | None,
    mass_total_kg: float | None,
    mass_oil_kg: float | None,
) -> float | None:
    """
    Calcula a constante de tempo térmica do óleo (τ₀) em horas.
    Usa a fórmula simplificada da IEC 60076-2, Anexo C.

    Args:
        ptot_kw: Perdas totais em kW
        delta_theta_oil_max_k: Elevação máxima do óleo em K
        mass_total_kg: Massa total do transformador em kg
        mass_oil_kg: Massa do óleo em kg

    Returns:
        Constante de tempo térmica em horas ou None em caso de erro
    """
    if None in [ptot_kw, delta_theta_oil_max_k, mass_total_kg, mass_oil_kg]:
        log.warning("Dados insuficientes para calcular τ₀.")
        return None
    try:
        ptot = float(ptot_kw)
        delta_max = float(delta_theta_oil_max_k)
        mt_kg = float(mass_total_kg)
        mo_kg = float(mass_oil_kg)

        # Converter para toneladas
        mt = mt_kg / 1000.0
        mo = mo_kg / 1000.0
        log.debug(f"Valores convertidos para toneladas: mT={mt:.1f}t, mO={mo:.1f}t")

        if ptot <= 0 or delta_max <= 0 or mt <= 0 or mo < 0:
            log.error(
                f"Valores inválidos para cálculo de τ₀: Ptot={ptot}, ΔΘmax={delta_max}, mT={mt}, mO={mo}"
            )
            return None

        # Verificação adicional para garantir que a massa total seja maior que a massa do óleo
        if mt < mo:
            log.warning(
                f"Massa total ({mt}t) menor que massa do óleo ({mo}t). Ajustando para cálculo."
            )
            mt = mo * 1.1  # Ajusta para um valor ligeiramente maior que a massa do óleo

        # Fórmula IEC 60076-2 Simplificação Anexo C (aproximada)
        capacidade_termica_kj_k = 5 * mt + 15 * mo
        log.debug(f"Capacidade térmica calculada: {capacidade_termica_kj_k:.1f} kJ/K")

        if ptot <= 1e-9:
            log.error(f"Perdas totais muito próximas de zero: {ptot}kW")
            return None

        tau0_segundos = capacidade_termica_kj_k * delta_max / ptot
        tau0_h = tau0_segundos / 3600.0

        if tau0_h <= 0 or math.isnan(tau0_h) or math.isinf(tau0_h):
            log.error(f"Cálculo de τ₀ resultou em valor inválido: {tau0_h}")
            return None

        log.info(
            f"Constante Térmica Óleo (τ₀) calculada: {tau0_h:.2f} h (Ptot={ptot:.1f}kW, ΔΘmax={delta_max:.1f}K, mT={mt:.1f}t, mO={mo:.1f}t)"
        )
        return tau0_h

    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(f"Erro ao calcular τ₀: {e}")
        return None
    except Exception as e:
        log.exception(f"Erro inesperado ao calcular τ₀: {e}")
        return None


# === Funções de Cálculo de Curto-Circuito (de short_circuit_withstand.py) ===


def calculate_short_circuit_params(
    corrente_nominal_a: float | None, impedancia_pu: float | None, k_peak_factor: float | None
) -> tuple[float | None, float | None]:
    """Calcula Isc simétrica (kA) e de pico (kA)."""
    isc_sym_ka, isc_peak_ka = None, None
    if None in [corrente_nominal_a, impedancia_pu, k_peak_factor]:
        log.warning("Dados insuficientes para calcular correntes de curto-circuito.")
        return isc_sym_ka, isc_peak_ka
    try:
        in_a = float(corrente_nominal_a)
        z_pu = float(impedancia_pu)
        k_sqrt2 = float(k_peak_factor)  # Este fator já é k*sqrt(2)

        if in_a <= 0 or z_pu <= 0 or k_sqrt2 <= 0:
            log.error(f"Valores inválidos para cálculo Isc: In={in_a}, Zpu={z_pu}, k√2={k_sqrt2}")
            return isc_sym_ka, isc_peak_ka

        isc_sym_a = in_a / z_pu
        isc_sym_ka = isc_sym_a / 1000
        isc_peak_ka = k_sqrt2 * isc_sym_ka  # Usa k_sqrt2 diretamente

        log.info(
            f"Cálculo Curto: In={in_a:.1f}A, Zpu={z_pu:.4f}, k√2={k_sqrt2:.2f} => Isc={isc_sym_ka:.2f}kA, ip={isc_peak_ka:.2f}kA"
        )
        return isc_sym_ka, isc_peak_ka

    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(f"Erro ao calcular correntes de curto-circuito: {e}")
        return None, None
    except Exception as e:
        log.exception(f"Erro inesperado ao calcular Isc/ip: {e}")
        return None, None


def calculate_impedance_variation(z_before: float | None, z_after: float | None) -> float | None:
    """Calcula a variação percentual da impedância."""
    if None in [z_before, z_after]:
        log.warning("Impedâncias pré/pós ensaio não fornecidas para cálculo de variação.")
        return None
    try:
        z_b = float(z_before)
        z_a = float(z_after)
        if z_b == 0:
            log.error("Impedância pré-ensaio (Z_antes) não pode ser zero.")
            return None

        delta_z = ((z_a - z_b) / z_b) * 100.0
        log.info(
            f"Cálculo Variação Z: Z_antes={z_b:.4f}%, Z_depois={z_a:.4f}% => ΔZ={delta_z:.2f}%"
        )
        return delta_z
    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(f"Erro ao calcular variação de impedância: {e}")
        return None


# === Funções de Cálculo de Tensão Aplicada (de applied_voltage.py) ===


def calculate_capacitive_load(
    capacitance_pf: float | None, voltage_v: float | None, frequency_hz: float | None
) -> tuple[float | None, float | None, float | None]:
    """Calcula Zc (Ohm), Corrente (mA) e Potência Reativa (kVAr) para um enrolamento."""
    zc_ohm, current_ma, power_kvar = None, None, None
    if None in [capacitance_pf, voltage_v, frequency_hz]:
        log.warning("Dados insuficientes para calcular carga capacitiva.")
        return zc_ohm, current_ma, power_kvar
    try:
        cap_f = float(capacitance_pf) * 1e-12
        v_v = float(voltage_v)
        f_hz = float(frequency_hz)

        if cap_f <= 0 or v_v < 0 or f_hz <= 0:
            log.error(
                f"Valores inválidos para cálculo capacitivo: C={cap_f}F, V={v_v}V, f={f_hz}Hz"
            )
            return None, None, None

        omega = 2 * np.pi * f_hz
        zc_ohm = 1.0 / (omega * cap_f) if omega * cap_f > 1e-15 else float("inf")
        current_a = v_v / zc_ohm if abs(zc_ohm) > 1e-9 else 0.0
        current_ma = current_a * 1000
        power_var = v_v * current_a
        power_kvar = power_var / 1000

        log.debug(
            f"Carga Capacitiva: C={capacitance_pf:.1f}pF, V={v_v/1000:.2f}kV, f={f_hz:.1f}Hz => Zc={zc_ohm:.1f}Ω, I={current_ma:.2f}mA, Q={power_kvar:.3f}kVAr"
        )
        return zc_ohm, current_ma, power_kvar

    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(f"Erro ao calcular carga capacitiva: {e}")
        return None, None, None
    except Exception as e:
        log.exception(f"Erro inesperado ao calcular carga capacitiva: {e}")
        return None, None, None


# === Funções Auxiliares Adicionais (Ex: Interpolação) ===


def interpolate_resistor_data(
    c_load_nf: float, reference_data: list[tuple[float, float]]
) -> float | None:
    """Interpola dados de referência (log-log) para sugerir valor de resistor."""
    if c_load_nf <= 0 or not reference_data:
        return None
    try:
        sorted_data = sorted(reference_data, key=lambda p: p[0])
        c_loads = np.array([point[0] for point in sorted_data])
        r_values = np.array([point[1] for point in sorted_data])

        if c_load_nf <= c_loads[0]:
            return r_values[0]
        if c_load_nf >= c_loads[-1]:
            return r_values[-1]

        log_c_loads = np.log10(c_loads)
        log_r_values = np.log10(r_values)
        log_c_load_target = np.log10(c_load_nf)

        log_r_interp = np.interp(log_c_load_target, log_c_loads, log_r_values)
        r_interp = 10**log_r_interp
        log.debug(f"Interpolação Resistor: C_load={c_load_nf:.2f}nF -> R_interp={r_interp:.1f}Ω")
        return r_interp

    except (ValueError, IndexError, Exception) as e:
        log.error(f"Erro ao interpolar dados de resistores para C={c_load_nf}nF: {e}")
        return None


# === Funções de Cálculo de Perdas em Carga (de losses.py) ===


def calculate_cap_bank_parameters(
    voltage_kv: float | None, power_mvar: float | None
) -> tuple[float | None, float | None]:
    """
    Determina a tensão nominal do banco de capacitores EPS adequada e
    calcula a potência reativa necessária nesse banco.
    """
    cap_bank_voltage_kv, pot_cap_bank_mvar = None, None
    if voltage_kv is None or power_mvar is None:
        log.warning("Tensão ou Potência ausente para cálculo do Cap Bank.")
        return cap_bank_voltage_kv, pot_cap_bank_mvar
    try:
        v_kv = float(voltage_kv)
        p_mvar = float(power_mvar)
        if v_kv <= 0 or p_mvar < 0:
            log.warning(f"Valores inválidos para cálculo Cap Bank: V={v_kv}, P={p_mvar}")
            return cap_bank_voltage_kv, pot_cap_bank_mvar

        required_min_bank_voltage = v_kv / 1.1
        cap_bank_voltage_kv = next(
            (v for v in constants.EPS_CAP_BANK_VOLTAGES_KV if v >= required_min_bank_voltage),
            constants.EPS_CAP_BANK_VOLTAGES_KV[-1],
        )

        if cap_bank_voltage_kv <= 23.9:
            factor = 0.25
        elif cap_bank_voltage_kv <= 71.7:
            factor = 0.75
        else:
            factor = 1.0

        if cap_bank_voltage_kv > 1e-6:
            voltage_ratio_sq = (v_kv / cap_bank_voltage_kv) ** 2
            denominator = voltage_ratio_sq * factor
            if denominator > 1e-9:
                pot_cap_bank_mvar = p_mvar / denominator
            else:
                log.warning("Denominador zero no cálculo da potência do Cap Bank.")
                pot_cap_bank_mvar = float("inf")
        else:
            log.error("Tensão nominal do Cap Bank calculada é zero.")
            pot_cap_bank_mvar = float("inf")

        log.debug(
            f"Cap Bank Calc: Vtest={v_kv:.2f}kV, Ptest={p_mvar:.2f}MVAr -> Vbank={cap_bank_voltage_kv:.1f}kV, Pbank={pot_cap_bank_mvar:.2f}MVAr"
        )
        return cap_bank_voltage_kv, pot_cap_bank_mvar

    except (ValueError, TypeError, ZeroDivisionError) as e:
        log.error(f"Erro ao calcular parâmetros do Cap Bank: {e}")
        return None, None
    except Exception as e:
        log.exception(f"Erro inesperado ao calcular Cap Bank: {e}")
        return None, None


def evaluate_eps_limits(
    voltage_kv: float | None,
    current_a: float | None,
    active_power_kw: float | None,
    reactive_power_mvar: float | None,
    cap_bank_voltage_kv: float | None,
) -> dict:
    """
    Avalia os parâmetros de ensaio contra os limites da fonte EPS e do banco.
    """
    status = "OK"
    messages = []
    event_count = 0
    params = {
        "Tensão": voltage_kv,
        "Corrente": current_a,
        "Pot. Ativa": active_power_kw,
        "Pot. Reativa Banco": reactive_power_mvar,
        "Tensão Banco": cap_bank_voltage_kv,
    }
    valid_inputs = True
    for name, val in params.items():
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            messages.append(f"{name} inválido ou não calculado.")
            valid_inputs = False
    if not valid_inputs:
        return {"status": "Erro", "messages": messages}

    if voltage_kv > constants.EPS_VOLTAGE_LIMIT_KV:
        messages.append(
            f"Tensão ({voltage_kv:.1f} kV) > Limite EPS ({constants.EPS_VOLTAGE_LIMIT_KV} kV)."
        )
        status = "Alerta"
        event_count += 1
    if current_a > constants.EPS_CURRENT_LIMIT_A:
        messages.append(
            f"Corrente ({current_a:.1f} A) > Limite EPS ({constants.EPS_CURRENT_LIMIT_A} A)."
        )
        status = "Alerta"
        event_count += 1
    if active_power_kw > constants.EPS_ACTIVE_POWER_LIMIT_KW:
        messages.append(
            f"Pot. Ativa ({active_power_kw:.1f} kW) > Limite EPS ({constants.EPS_ACTIVE_POWER_LIMIT_KW} kW)."
        )
        status = "Alerta"
        event_count += 1
    if reactive_power_mvar > constants.EPS_REACTIVE_POWER_LIMIT_MVAR_HIGH:
        messages.append(
            f"Pot. Reativa Banco ({reactive_power_mvar:.1f} MVAr) > Limite Máximo ({constants.EPS_REACTIVE_POWER_LIMIT_MVAR_HIGH} MVAr). Ensaio IMPOSSÍVEL."
        )
        status = "Erro"
        event_count += 1
    elif reactive_power_mvar > constants.EPS_REACTIVE_POWER_LIMIT_MVAR_LOW:
        messages.append(
            f"Pot. Reativa Banco ({reactive_power_mvar:.1f} MVAr) > Limite Inferior ({constants.EPS_REACTIVE_POWER_LIMIT_MVAR_LOW} MVAr). Requer aumento do banco."
        )
        status = "Alerta" if status != "Erro" else status
        event_count += 1
    if cap_bank_voltage_kv is not None and voltage_kv > cap_bank_voltage_kv * 1.1:
        percent_above = (
            ((voltage_kv / cap_bank_voltage_kv) - 1) * 100 if cap_bank_voltage_kv > 0 else 0
        )
        messages.append(
            f"Tensão ({voltage_kv:.1f} kV) > 110% Vbanco ({cap_bank_voltage_kv:.1f} kV) - {percent_above:.1f}% acima."
        )
        status = "Alerta" if status != "Erro" else status
        event_count += 1
    if event_count > 1:
        messages.append(f"Total de {event_count} alertas/erros.")
    if status == "OK":
        messages.append("Parâmetros dentro dos limites esperados.")

    log.debug(f"Avaliação Limites EPS: Status={status}, Mensagens={messages}")
    return {"status": status, "messages": messages}


# --- Function for Bilinear Interpolation (Moved here) ---
def buscar_valores_tabela(
    inducao_teste: float | None, frequencia_teste: float | None, df: pd.DataFrame
) -> float | None:
    """Realiza interpolação bilinear nos DataFrames de perdas/potência."""
    if df.empty or inducao_teste is None or frequencia_teste is None:
        log.warning(
            f"DataFrame vazio ou inputs inválidos ({inducao_teste=}, {frequencia_teste=}) para buscar_valores_tabela."
        )
        return None
    if not isinstance(inducao_teste, (int, float)) or not isinstance(
        frequencia_teste, (int, float)
    ):
        log.warning(
            f"Tipos inválidos para inducao/frequencia ({type(inducao_teste)}, {type(frequencia_teste)})."
        )
        return None
    if math.isnan(inducao_teste) or math.isnan(frequencia_teste):
        log.warning("Valores NaN recebidos para inducao/frequencia.")
        return None

    try:
        # Extrai índices únicos e ordenados
        inducoes = sorted(df.index.get_level_values("inducao_nominal").unique())
        frequencias = sorted(df.index.get_level_values("frequencia_nominal").unique())

        if not inducoes or not frequencias:
            log.warning("Índices de indução ou frequência vazios no DataFrame.")
            return None

        # Clamping
        inducao_teste_clamped = max(min(inducao_teste, inducoes[-1]), inducoes[0])
        frequencia_teste_clamped = max(min(frequencia_teste, frequencias[-1]), frequencias[0])

        # Encontra índices
        ind_idx = np.searchsorted(inducoes, inducao_teste_clamped)
        freq_idx = np.searchsorted(frequencias, frequencia_teste_clamped)

        # Garante limites
        ind_idx = min(max(ind_idx, 1), len(inducoes) - 1)
        freq_idx = min(max(freq_idx, 1), len(frequencias) - 1)

        ind_low, ind_high = inducoes[ind_idx - 1], inducoes[ind_idx]
        freq_low, freq_high = frequencias[freq_idx - 1], frequencias[freq_idx]

        try:
            # Acessa valores - iloc[0] para Series, iloc[0,0] para DataFrame (se index não for único)
            q11 = (
                df.loc[(ind_low, freq_low)].iloc[0]
                if isinstance(df.loc[(ind_low, freq_low)], pd.Series)
                else df.loc[(ind_low, freq_low)].iloc[0, 0]
            )
            q12 = (
                df.loc[(ind_low, freq_high)].iloc[0]
                if isinstance(df.loc[(ind_low, freq_high)], pd.Series)
                else df.loc[(ind_low, freq_high)].iloc[0, 0]
            )
            q21 = (
                df.loc[(ind_high, freq_low)].iloc[0]
                if isinstance(df.loc[(ind_high, freq_low)], pd.Series)
                else df.loc[(ind_high, freq_low)].iloc[0, 0]
            )
            q22 = (
                df.loc[(ind_high, freq_high)].iloc[0]
                if isinstance(df.loc[(ind_high, freq_high)], pd.Series)
                else df.loc[(ind_high, freq_high)].iloc[0, 0]
            )
        except (KeyError, IndexError) as e:
            log.error(
                f"Erro ao acessar DataFrame em buscar_valores_tabela: {e}. Índices: ({ind_low},{freq_low}), etc."
            )
            return None

        # Pesos
        delta_ind = (ind_high - ind_low) + 1e-12
        delta_freq = (freq_high - freq_low) + 1e-12
        x_weight = (inducao_teste_clamped - ind_low) / delta_ind
        y_weight = (frequencia_teste_clamped - freq_low) / delta_freq

        # Interpolação
        valor_interpolado = (
            (1 - x_weight) * (1 - y_weight) * q11
            + x_weight * (1 - y_weight) * q21
            + (1 - x_weight) * y_weight * q12
            + x_weight * y_weight * q22
        )

        col_name = df.columns[0] if not df.empty else "valor"
        log.debug(
            f"Interpolação ({col_name}): B={inducao_teste_clamped:.2f}T, f={frequencia_teste_clamped:.1f}Hz -> {valor_interpolado:.3f}"
        )
        return valor_interpolado

    except Exception as e:
        log.exception(
            f"Erro durante interpolação bilinear para B={inducao_teste}, f={frequencia_teste}: {e}"
        )
        return None


# === Funções de Simulação de Impulso (Híbrida) ===


def simulate_hybrid_impulse(
    t_sec: np.ndarray,
    v0_charge: float,
    rf: float,
    rt: float,
    l_total: float,
    c_gen: float,
    c_load: float,
    impulse_type: str,
    gap_distance_cm: float = None,
) -> tuple:
    """
    Simula o circuito de impulso usando a abordagem híbrida RLC + K-Factor + Dupla Exponencial.

    Args:
        t_sec: Array de tempo em segundos
        v0_charge: Tensão de carga inicial em Volts
        rf: Resistência de frente em Ohms
        rt: Resistência de cauda em Ohms
        l_total: Indutância total em Henries
        c_gen: Capacitância do gerador em Farads
        c_load: Capacitância da carga em Farads
        impulse_type: Tipo de impulso ("lightning", "chopped", "switching")
        gap_distance_cm: Distância do gap em cm (apenas para impulso cortado)

    Returns:
        Tupla contendo (v_rlc, v_final, i_load, alpha, beta, chop_time_sec)
    """
    # Validação de parâmetros de entrada
    if t_sec is None or len(t_sec) < 2:
        log.error("Vetor de tempo inválido ou muito curto para simulação de impulso")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(v0_charge, (int, float)) or v0_charge <= 0:
        log.error(f"Tensão de carga inválida: {v0_charge}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(rf, (int, float)) or rf <= 0:
        log.error(f"Resistência de frente inválida: {rf}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(rt, (int, float)) or rt <= 0:
        log.error(f"Resistência de cauda inválida: {rt}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(l_total, (int, float)) or l_total <= 0:
        log.error(f"Indutância total inválida: {l_total}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(c_gen, (int, float)) or c_gen <= 0:
        log.error(f"Capacitância do gerador inválida: {c_gen}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if not isinstance(c_load, (int, float)) or c_load <= 0:
        log.error(f"Capacitância da carga inválida: {c_load}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    if impulse_type not in ["lightning", "chopped", "switching"]:
        log.error(f"Tipo de impulso inválido: {impulse_type}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None

    # Parâmetros da simulação
    collapse_time = 0.1e-6  # Tempo de colapso do gap em segundos
    log.info(f"Simulando Híbrido: Tipo={impulse_type}, V0_carga={v0_charge/1000:.1f}kV")

    try:
        # Cálculo da capacitância equivalente
        c_eq = (c_gen * c_load) / (c_gen + c_load) if (c_gen + c_load) > 1e-15 else 0
        r_rlc = rf + constants.R_PARASITIC_OHM  # Adiciona resistência parasita

        log.debug(f"Simulando RLC: R={r_rlc:.1f}, L={l_total:.2e}, Ceq={c_eq:.2e}")

        # Solução RLC
        v_rlc = rlc_solution(t_sec, v0_charge, r_rlc, l_total, c_eq)
        v_rlc_kv = v_rlc / 1000  # Converte para kV para K-factor
        t_us = t_sec * 1e6  # Converte para µs para K-factor

        # Transformação K-factor
        v_test, v_base, _, overshoot, (alpha_fit, beta_fit) = calculate_k_factor_transform(
            v_rlc_kv, t_us, return_params=True
        )

        # Se o ajuste K-factor falhar, usa estimativas teóricas
        if alpha_fit is None or beta_fit is None:
            log.warning("Ajuste K-factor falhou. Usando estimativas teóricas.")
            # Estimativas teóricas baseadas nos parâmetros do circuito
            alpha = 1 / (rt * (c_gen + c_load)) if rt > 1e-9 and (c_gen + c_load) > 1e-15 else 0
            beta = 1 / (rf * c_eq) if rf > 1e-9 and c_eq > 1e-15 else 0

            # Garante que beta > alpha (necessário para dupla exponencial)
            if beta <= alpha + 1e-9:
                adjust_factor = 1.05
                add_factor = 1e3 if impulse_type in ["lightning", "chopped"] else 1e2
                beta = alpha * adjust_factor + add_factor
                log.warning(f"Beta ajustado para {beta:.2e} (era <= alpha)")
        else:
            alpha = alpha_fit
            beta = beta_fit
            log.info(f"Parâmetros K-factor: alpha={alpha:.2e}, beta={beta:.2e}")

        # Gera forma de onda final usando dupla exponencial
        v_final = double_exp_func(t_sec, v0_charge, alpha, beta)

        # Processamento especial para impulso cortado
        chop_time_sec = None
        if impulse_type == "chopped" and gap_distance_cm is not None and gap_distance_cm > 0:
            # Tensão de breakdown estimada (30 kV/cm)
            breakdown_voltage = 30.0 * gap_distance_cm * 1000  # Converte para V

            # Encontra o primeiro ponto onde a tensão excede a tensão de breakdown
            times_above_threshold = np.where(v_final >= breakdown_voltage)[0]

            if len(times_above_threshold) > 0:
                chop_idx = times_above_threshold[0]

                if chop_idx < len(t_sec):
                    chop_time_sec = t_sec[chop_idx]
                    log.info(
                        f"Corte detectado: t={chop_time_sec*1e6:.2f} µs, V={v_final[chop_idx]/1000:.1f} kV"
                    )

                    # Índices após o corte
                    collapse_idx = np.where(t_sec >= chop_time_sec)[0]

                    if len(collapse_idx) > 0:
                        chop_voltage_final = v_final[chop_idx]
                        dt_after_chop = t_sec[collapse_idx] - chop_time_sec

                        # Fase de colapso (queda linear)
                        mask_collapse = dt_after_chop <= collapse_time
                        idx_collapse = collapse_idx[mask_collapse]

                        # Fase de oscilação (após colapso)
                        mask_osc = dt_after_chop > collapse_time
                        idx_osc = collapse_idx[mask_osc]

                        # Aplica queda linear durante o colapso
                        if len(idx_collapse) > 0:
                            v_final[idx_collapse] = chop_voltage_final * (
                                1 - (t_sec[idx_collapse] - chop_time_sec) / collapse_time
                            )

                        # Aplica oscilação amortecida após o colapso
                        if len(idx_osc) > 0:
                            freq_osc = 5e6  # Frequência de oscilação em Hz
                            damp_factor = 1.5  # Fator de amortecimento
                            undershoot_ratio = 0.25  # Razão de undershoot

                            # Tempo após o colapso
                            time_after_collapse = t_sec[idx_osc] - chop_time_sec - collapse_time

                            # Amplitude da oscilação
                            amp = (
                                -chop_voltage_final
                                * undershoot_ratio
                                * np.exp(-damp_factor * time_after_collapse * 1e6)
                            )

                            # Oscilação
                            osc = amp * np.cos(2 * np.pi * freq_osc * time_after_collapse)
                            v_final[idx_osc] = osc

                            # Limita o undershoot e zera após algumas oscilações
                            v_final[idx_osc] = np.clip(
                                v_final[idx_osc], -0.3 * abs(chop_voltage_final), float("inf")
                            )
                            v_final[idx_osc[time_after_collapse > 3 / freq_osc]] = 0
            else:
                log.warning(
                    f"Tensão não atingiu breakdown ({breakdown_voltage/1000:.1f} kV) para gap={gap_distance_cm} cm"
                )

        # Calcula corrente na carga (derivada da tensão)
        i_load = c_load * np.gradient(v_final, t_sec)

        return v_rlc, v_final, i_load, alpha, beta, chop_time_sec

    except Exception as e:
        log.exception(f"Erro na simulação de impulso híbrido: {e}")
        return np.zeros_like(t_sec), np.zeros_like(t_sec), np.zeros_like(t_sec), 0, 0, None


# --- END OF FILE app_core/calculations.py ---
