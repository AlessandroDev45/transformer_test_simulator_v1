"""
Fórmulas matemáticas para cálculos relacionados a transformadores.
Centraliza todos os cálculos de parâmetros de transformadores.
"""

import logging

import numpy as np

# Configuração de logging
log = logging.getLogger(__name__)

# Constantes
DEFAULT_FREQUENCY = 60  # Hz


def calculate_transformer_inductance(
    voltage_kv: float,
    power_mva: float,
    impedance_percent: float,
    freq_hz: float = DEFAULT_FREQUENCY,
) -> float:
    """
    Calcula a indutância de curto-circuito (Lcc) do transformador.

    Args:
        voltage_kv: Tensão nominal em kV
        power_mva: Potência nominal em MVA
        impedance_percent: Impedância percentual
        freq_hz: Frequência em Hz

    Returns:
        Indutância em Henries
    """
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

        log.info(f"Indutância do transformador calculada: {l_cc:.4f} H")
        return l_cc
    except Exception as e:
        log.exception(f"Erro ao calcular indutância do transformador: {e}")
        return default_inductance


def calculate_short_circuit_params(
    corrente_nominal_a: float, impedancia_pu: float, k_peak_factor: float
) -> tuple[float, float]:
    """
    Calcula correntes de curto-circuito simétricas e de pico.

    Args:
        corrente_nominal_a: Corrente nominal em A
        impedancia_pu: Impedância em pu
        k_peak_factor: Fator de pico k*sqrt(2)

    Returns:
        Tupla com (Isc_simetrica_kA, Isc_pico_kA)
    """
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

        # Corrente de curto-circuito simétrica (kA)
        isc_sym_a = in_a / z_pu
        isc_sym_ka = isc_sym_a / 1000

        # Corrente de curto-circuito de pico (kA)
        isc_peak_a = isc_sym_a * k_sqrt2
        isc_peak_ka = isc_peak_a / 1000

        log.info(
            f"Correntes de curto-circuito calculadas: Isc_sym={isc_sym_ka:.2f} kA, Isc_peak={isc_peak_ka:.2f} kA"
        )
        return isc_sym_ka, isc_peak_ka
    except Exception as e:
        log.exception(f"Erro ao calcular correntes de curto-circuito: {e}")
        return None, None


def calculate_impedance_variation(z_before: float, z_after: float) -> float:
    """
    Calcula a variação percentual da impedância.

    Args:
        z_before: Impedância antes do ensaio em %
        z_after: Impedância após o ensaio em %

    Returns:
        Variação percentual da impedância
    """
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
