"""
Fórmulas matemáticas para simulação e análise de impulsos.
Centraliza todos os cálculos relacionados a impulsos atmosféricos, de manobra e cortados.
"""

import logging
import math

import numpy as np

# Configuração de logging
log = logging.getLogger(__name__)

# Constantes e parâmetros físicos
R_PARASITIC_OHM = 0.5  # Resistência parasita do circuito em Ohms
L_PARASITIC_H = 1e-6  # Indutância parasita em Henries
C_CHOPPING_GAP_PF = 600  # Capacitância do gap de corte em pF

# Constantes para análise de formas de onda
LIGHTNING_IMPULSE_FRONT_TIME_NOM = 1.2  # Tempo de frente nominal LI em µs
LIGHTNING_IMPULSE_TAIL_TIME_NOM = 50.0  # Tempo de cauda nominal LI em µs
LIGHTNING_FRONT_TOLERANCE = 0.3  # Tolerância para tempo de frente LI (30%)
LIGHTNING_TAIL_TOLERANCE = 0.2  # Tolerância para tempo de cauda LI (20%)
LIGHTNING_OVERSHOOT_MAX = 5.0  # Overshoot máximo permitido para LI em %

SWITCHING_IMPULSE_PEAK_TIME_NOM = 250.0  # Tempo de pico nominal SI em µs
SWITCHING_IMPULSE_TAIL_TIME_NOM = 2500.0  # Tempo de cauda nominal SI em µs
SWITCHING_PEAK_TIME_TOLERANCE = 0.2  # Tolerância para tempo de pico SI (20%)
SWITCHING_TAIL_TOLERANCE = 0.6  # Tolerância para tempo de cauda SI (60%)
SWITCHING_TIME_ABOVE_90_MIN = 200.0  # Tempo mínimo acima de 90% para SI em µs
SWITCHING_TIME_TO_ZERO_MIN = 3000.0  # Tempo mínimo até zero para SI em µs

CHOPPED_PEAK_TOLERANCE = 0.1  # Tolerância para tensão de corte (10%)
CHOPPED_TIME_MIN = 2.0  # Tempo mínimo de corte em µs
CHOPPED_TIME_MAX = 6.0  # Tempo máximo de corte em µs
CHOPPED_UNDERSHOOT_MAX = 30.0  # Undershoot máximo permitido para LIC em %

# Valores de indutância padrão para LI/LIC conforme manual CDYH-2400kV
LI_INDUCTOR_MIN_UH = 40.0  # Indutância mínima para LI em µH
LI_INDUCTOR_MAX_UH = 70.0  # Indutância máxima para LI em µH

# Valores de capacitância típicos para objetos de teste
TEST_OBJECT_MIN_PF = 1600.0  # Capacitância mínima típica em pF
TEST_OBJECT_MAX_PF = 3500.0  # Capacitância máxima típica em pF


def double_exp_func(t_sec: np.ndarray, V0_norm: float, alpha: float, beta: float) -> np.ndarray:
    """
    Função de dupla exponencial normalizada V(t) = K * [exp(-alpha*t) - exp(-beta*t)],
    onde K é ajustado para que o pico da função seja V0_norm.
    Requer beta > alpha.

    Args:
        t_sec: Array de tempo em segundos
        V0_norm: Valor de pico normalizado
        alpha: Constante de tempo de cauda (s⁻¹)
        beta: Constante de tempo de frente (s⁻¹)

    Returns:
        Array de tensão normalizada
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

    try:
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            # Tempo de pico teórico
            t_peak = math.log(beta / alpha) / (beta - alpha) if beta > alpha else 0

            # Valor no pico para normalização
            norm_factor = (
                (math.exp(-alpha * t_peak) - math.exp(-beta * t_peak)) if t_peak >= 0 else 0
            )
            if abs(norm_factor) < 1e-12:
                log.warning("Fator de normalização da dupla exponencial próximo de zero.")
                return v_out

            # Fator K para normalização
            k_norm = V0_norm / norm_factor

            # Garante que t seja não-negativo para evitar problemas numéricos
            t_safe = np.maximum(t_sec, 0)

            # Calcula a forma de onda
            v_out = k_norm * (np.exp(-alpha * t_safe) - np.exp(-beta * t_safe))

            return v_out
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        log.error(f"Erro no cálculo da dupla exponencial: {e}")
        return np.zeros_like(t_sec)


def rlc_solution(
    t_sec: np.ndarray, v0: float, r_total: float, l_total: float, c_eq: float
) -> np.ndarray:
    """
    Solução analítica do circuito RLC série para descarga de capacitor.

    Args:
        t_sec: Array de tempo em segundos
        v0: Tensão inicial de carga em Volts
        r_total: Resistência total em Ohms
        l_total: Indutância total em Henries
        c_eq: Capacitância equivalente em Farads

    Returns:
        Array de tensão em Volts
    """
    v_out = np.zeros_like(t_sec)

    # Validação de parâmetros
    if l_total <= 0 or c_eq <= 0:
        log.warning(
            f"Parâmetros L ({l_total}) ou C ({c_eq}) inválidos (não positivos) para solução RLC."
        )
        return v_out

    try:
        # Frequência natural ao quadrado
        omega0_sq = 1.0 / (l_total * c_eq)

        # Fator de amortecimento
        alpha_damp = r_total / (2.0 * l_total) if l_total > 1e-12 else float("inf")

        if alpha_damp < 0:  # Amortecimento não pode ser negativo
            log.warning(f"Fator de amortecimento alpha_damp ({alpha_damp}) negativo inválido.")
            return v_out

        # Discriminante para determinar o tipo de resposta
        delta = alpha_damp**2 - omega0_sq

        # Considera apenas tempos não-negativos
        t_valid = t_sec[t_sec >= 0]

        # Casos de resposta do circuito RLC
        if abs(delta / omega0_sq) < 1e-6:  # Criticamente Amortecido (delta ≈ 0)
            if alpha_damp < 1e-9:  # Praticamente não amortecido
                omega_n = math.sqrt(omega0_sq)
                v_out[t_sec >= 0] = v0 * np.cos(omega_n * t_valid)
            else:
                a = alpha_damp
                v_out[t_sec >= 0] = v0 * (1 + a * t_valid) * np.exp(-a * t_valid)
            log.debug("RLC: Caso Criticamente Amortecido")

        elif delta > 0:  # Sobreamortecido
            s1 = -alpha_damp + math.sqrt(delta)
            s2 = -alpha_damp - math.sqrt(delta)
            k1 = v0 * s2 / (s2 - s1)
            k2 = v0 * s1 / (s1 - s2)
            v_out[t_sec >= 0] = k1 * np.exp(s1 * t_valid) + k2 * np.exp(s2 * t_valid)
            log.debug("RLC: Caso Sobreamortecido")

        else:  # Subamortecido (oscilante)
            omega_d = math.sqrt(-delta)
            A = v0
            phi = 0  # Fase inicial
            v_out[t_sec >= 0] = A * np.exp(-alpha_damp * t_valid) * np.cos(omega_d * t_valid + phi)
            log.debug("RLC: Caso Subamortecido (oscilante)")

        return v_out

    except Exception as e:
        log.exception(f"Erro na solução RLC: {e}")
        return np.zeros_like(t_sec)


def calculate_k_factor_transform(
    v_rlc_kv: np.ndarray, t_us: np.ndarray, return_params: bool = False
) -> tuple:
    """
    Aplica a transformação K-factor para ajustar a forma de onda RLC para uma dupla exponencial.

    Args:
        v_rlc_kv: Array de tensão RLC em kV
        t_us: Array de tempo em μs
        return_params: Se True, retorna também os parâmetros alpha e beta ajustados

    Returns:
        Tupla com (v_test, v_base, k_factor, overshoot, (alpha, beta))
    """
    # Implementação do algoritmo K-factor
    # ...

    # Valores de retorno temporários
    v_test = v_rlc_kv.copy()
    v_base = v_rlc_kv.copy()
    k_factor = 1.0
    overshoot = 0.0
    alpha = 1e4
    beta = 1e6

    if return_params:
        return v_test, v_base, k_factor, overshoot, (alpha, beta)
    else:
        return v_test, v_base, k_factor, overshoot


def analyze_lightning_impulse(t_us: np.ndarray, v_kv: np.ndarray) -> dict:
    """
    Analisa parâmetros de Impulso Atmosférico (LI) usando K-Factor.

    Args:
        t_us: Array de tempo em μs
        v_kv: Array de tensão em kV

    Returns:
        Dicionário com parâmetros da forma de onda
    """
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
        "conforme_pico": False,
        "status_geral": "Indeterminado",
        "error": None,
    }

    # Implementação da análise
    # ...

    return results


def analyze_switching_impulse(t_us: np.ndarray, v_kv: np.ndarray) -> dict:
    """
    Analisa parâmetros de Impulso de Manobra (SI) conforme IEC 60060-1.

    Args:
        t_us: Array de tempo em μs
        v_kv: Array de tensão em kV

    Returns:
        Dicionário com parâmetros da forma de onda
    """
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

    # Implementação da análise
    # ...

    return results


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
        Tupla com (v_rlc, v_final, i_load, alpha, beta, chop_time_sec)
    """
    log.info(f"Simulando Híbrido: Tipo={impulse_type}, V0_carga={v0_charge/1000:.1f}kV")

    try:
        # Cálculo da capacitância equivalente
        c_eq = (c_gen * c_load) / (c_gen + c_load) if (c_gen + c_load) > 1e-15 else 0
        r_rlc = rf + R_PARASITIC_OHM  # Adiciona resistência parasita

        log.debug(f"Simulando RLC: R={r_rlc:.1f}, L={l_total:.2e}, Ceq={c_eq:.2e}")

        # Solução RLC
        v_rlc = rlc_solution(t_sec, v0_charge, r_rlc, l_total, c_eq)
        v_rlc_kv = v_rlc / 1000  # Converte para kV para K-factor
        t_us = t_sec * 1e6  # Converte para µs para K-factor

        # Transformação K-factor
        v_test, v_base, _, overshoot, (alpha_fit, beta_fit) = calculate_k_factor_transform(
            v_rlc_kv, t_us, return_params=True
        )

        # Usa parâmetros ajustados ou estimativas
        if alpha_fit is None or beta_fit is None:
            log.warning("Ajuste K-factor falhou. Usando estimativas.")
            alpha = 1 / (rt * (c_gen + c_load)) if rt > 1e-9 and (c_gen + c_load) > 1e-15 else 0
            beta = 1 / (rf * c_eq) if rf > 1e-9 and c_eq > 1e-15 else 0

            # Garante que beta > alpha
            if beta <= alpha + 1e-9:
                adjust_factor = 1.05
                add_factor = 1e3 if impulse_type in ["lightning", "chopped"] else 1e2
                beta = alpha * adjust_factor + add_factor
        else:
            alpha = alpha_fit
            beta = beta_fit

        log.info(f"Parâmetros K-factor: alpha={alpha:.2e}, beta={beta:.2e}")

        # Gera forma de onda final com dupla exponencial
        v_final = double_exp_func(t_sec, v0_charge, alpha, beta)

        # Processa impulso cortado se necessário
        chop_time_sec = None
        if impulse_type == "chopped" and gap_distance_cm is not None and gap_distance_cm > 0:
            # Tensão de breakdown estimada (30 kV/cm para polaridade positiva)
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

                    # Processa a forma de onda após o corte
                    collapse_time = 0.1e-6  # 0.1 µs para colapso da tensão
                    collapse_idx = np.where(t_sec >= chop_time_sec)[0]

                    if len(collapse_idx) > 0:
                        chop_voltage_final = v_final[chop_idx]
                        dt_after_chop = t_sec[collapse_idx] - chop_time_sec

                        # Índices para colapso e oscilação
                        mask_collapse = dt_after_chop <= collapse_time
                        mask_osc = dt_after_chop > collapse_time
                        idx_collapse = collapse_idx[mask_collapse]
                        idx_osc = collapse_idx[mask_osc]

                        # Colapso linear da tensão
                        if len(idx_collapse) > 0:
                            v_final[idx_collapse] = chop_voltage_final * (
                                1 - (t_sec[idx_collapse] - chop_time_sec) / collapse_time
                            )

                        # Oscilação amortecida após o colapso
                        if len(idx_osc) > 0:
                            freq_osc = 5e6  # 5 MHz - frequência típica de oscilação
                            damp_factor = 1.5  # Fator de amortecimento
                            undershoot_ratio = 0.25  # 25% de undershoot

                            time_after_collapse = t_sec[idx_osc] - chop_time_sec - collapse_time
                            amp = (
                                -chop_voltage_final
                                * undershoot_ratio
                                * np.exp(-damp_factor * time_after_collapse * 1e6)
                            )
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


def get_resistors_and_inductor(
    cap_load_pf: float, impulse_type: str, n_stages: int = 12, n_parallel: int = 1
) -> tuple:
    """
    Calcula dinamicamente os valores de resistores e indutor com base na capacitância do objeto sob teste
    e no tipo de impulso, conforme especificações do manual CDYH-2400kV.

    Args:
        cap_load_pf: Capacitância do objeto sob teste em pF
        impulse_type: Tipo de impulso ("lightning", "chopped", "switching")
        n_stages: Número de estágios do gerador
        n_parallel: Número de colunas em paralelo

    Returns:
        Tupla com (rf_ohm, rt_ohm, l_total_h)
    """
    # Converte para valores em unidades base
    cap_load_f = cap_load_pf * 1e-12

    # Valores padrão para caso de erro
    default_rf = 60.0 / n_parallel * n_stages
    default_rt = 100.0 / n_parallel * n_stages
    default_l = 70e-6  # 70 µH para LI/LIC

    try:
        if impulse_type.lower() in ["lightning", "li", "chopped", "lic"]:
            # Ajuste de resistores para Impulso Atmosférico (LI) e Cortado (LIC)
            if cap_load_pf <= 1600:
                # Capacitância baixa: Rf maior para aumentar tempo de frente
                rf_per_column = parallel_resistors([60, 40])  # Paralelo de 60 e 40 Ohm
                rt_per_column = parallel_resistors([100, 100])  # Paralelo de 100 e 100 Ohm
                l_uh = 70.0  # 70 µH para capacitância baixa
            elif cap_load_pf <= 2500:
                # Capacitância média: Rf intermediário
                rf_per_column = parallel_resistors([40, 20])  # Paralelo de 40 e 20 Ohm
                rt_per_column = parallel_resistors([100, 100])  # Paralelo de 100 e 100 Ohm
                l_uh = 60.0  # 60 µH para capacitância média
            else:
                # Capacitância alta: Rf menor para reduzir tempo de frente
                rf_per_column = parallel_resistors([60, 20])  # Paralelo de 60 e 20 Ohm
                rt_per_column = parallel_resistors([100, 100])  # Paralelo de 100 e 100 Ohm
                l_uh = 50.0  # 50 µH para capacitância alta

            # Ajuste fino da indutância com base na capacitância
            # Interpola entre LI_INDUCTOR_MIN_UH e LI_INDUCTOR_MAX_UH
            cap_factor = min(
                1.0,
                max(
                    0.0,
                    (cap_load_pf - TEST_OBJECT_MIN_PF) / (TEST_OBJECT_MAX_PF - TEST_OBJECT_MIN_PF),
                ),
            )
            l_uh = LI_INDUCTOR_MAX_UH - cap_factor * (LI_INDUCTOR_MAX_UH - LI_INDUCTOR_MIN_UH)

            # Converte para Henries
            l_total_h = l_uh * 1e-6

        elif impulse_type.lower() in ["switching", "si"]:
            # Ajuste de resistores para Impulso de Manobra (SI)
            # SI usa resistores maiores e não usa indutor
            if cap_load_pf <= 1600:
                rf_per_column = 3000.0  # 3 kOhm para capacitância baixa
                rt_per_column = 5000.0  # 5 kOhm para capacitância baixa
            elif cap_load_pf <= 2500:
                rf_per_column = 2000.0  # 2 kOhm para capacitância média
                rt_per_column = 4000.0  # 4 kOhm para capacitância média
            else:
                rf_per_column = 1500.0  # 1.5 kOhm para capacitância alta
                rt_per_column = 3000.0  # 3 kOhm para capacitância alta

            # SI não usa indutor
            l_total_h = 0.0
        else:
            log.warning(f"Tipo de impulso desconhecido: {impulse_type}. Usando valores padrão.")
            return default_rf, default_rt, default_l

        # Calcula valores totais considerando número de estágios e colunas em paralelo
        rf_total = (rf_per_column * n_stages) / n_parallel if n_parallel > 0 else float("inf")
        rt_total = (rt_per_column * n_stages) / n_parallel if n_parallel > 0 else float("inf")

        log.info(
            f"Resistores e indutor calculados para {impulse_type}, C={cap_load_pf:.0f}pF: Rf={rf_total:.1f}Ω, Rt={rt_total:.1f}Ω, L={l_total_h*1e6:.1f}µH"
        )
        return rf_total, rt_total, l_total_h

    except Exception as e:
        log.exception(f"Erro ao calcular resistores e indutor: {e}")
        return default_rf, default_rt, default_l


def parallel_resistors(resistor_values: list) -> float:
    """
    Calcula a resistência equivalente de resistores em paralelo.

    Args:
        resistor_values: Lista de valores de resistência em Ohms

    Returns:
        Resistência equivalente em Ohms
    """
    if not resistor_values:
        return float("inf")

    # Soma dos inversos
    sum_inverse = sum(1.0 / r for r in resistor_values if r > 0)

    # Resistência equivalente é o inverso da soma dos inversos
    if sum_inverse > 0:
        return 1.0 / sum_inverse
    else:
        return float("inf")


def calculate_gap_chopping(
    tensao_kV: float, polaridade: str = "positiva", tempo_corte_desejado: float = 4.0
) -> float:
    """
    Calcula a distância do gap de corte para obter um tempo de corte específico,
    baseado na norma IEC 60060-1 e manual do equipamento CDYH-2400kV.

    Args:
        tensao_kV: Tensão de teste em kV
        polaridade: Polaridade do impulso ("positiva" ou "negativa")
        tempo_corte_desejado: Tempo de corte desejado em μs (entre 2-6 μs)

    Returns:
        Distância do gap em cm
    """
    # Constantes baseadas na norma IEC 60060-1
    E_atm = 30.0  # kV/cm em condições atmosféricas padrão

    # Ajuste para polaridade
    if polaridade.lower() == "negativa":
        E_atm *= 0.85  # Campo de ruptura menor para polaridade negativa

    # Limitar o tempo de corte desejado à faixa válida (2-6 μs)
    tempo_corte_desejado = max(2, min(6, tempo_corte_desejado))

    # Fator de segurança baseado no tempo de corte
    # Para tempos menores, precisamos de gaps menores (mais próximos)
    safety_factor = 1.05  # Fator base

    # Ajuste do fator de segurança com base no tempo de corte
    # Normalizado para 4 μs como ponto central
    if tempo_corte_desejado < 4.0:
        # Para tempos menores, reduzimos o gap (aumentamos o fator)
        safety_factor += 0.05 * (4.0 - tempo_corte_desejado) / 2.0
    else:
        # Para tempos maiores, aumentamos o gap (reduzimos o fator)
        safety_factor -= 0.03 * (tempo_corte_desejado - 4.0) / 2.0

    # Cálculo do gap usando a fórmula da tensão de centelhamento
    # V_gap = d_gap × E_atm
    # Reorganizando: d_gap = V_gap / E_atm
    gap_cm = tensao_kV / (E_atm * safety_factor)

    # Ajuste adicional para tensões muito altas ou muito baixas
    if tensao_kV < 200:
        gap_cm *= 0.95  # Redução de 5% para compensar não-linearidades em baixas tensões
    elif tensao_kV > 1000:
        gap_cm *= 1.05  # Aumento de 5% para compensar não-linearidades em altas tensões

    # Arredondamento para precisão prática
    gap_cm = round(gap_cm, 1)

    log.info(
        f"Gap calculado: {gap_cm} cm para tensão de {tensao_kV} kV (polaridade {polaridade}, tempo de corte {tempo_corte_desejado} μs)"
    )

    return gap_cm
