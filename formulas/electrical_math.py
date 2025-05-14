"""
Fórmulas matemáticas para cálculos elétricos gerais.
Centraliza cálculos de circuitos elétricos, capacitâncias, eficiência, etc.
"""

import logging

import numpy as np

# Configuração de logging
log = logging.getLogger(__name__)


def calculate_capacitive_load(
    capacitance_pf: float, voltage_v: float, frequency_hz: float
) -> tuple[float, float, float]:
    """
    Calcula Zc (Ohm), Corrente (mA) e Potência Reativa (kVAr) para um enrolamento.

    Args:
        capacitance_pf: Capacitância em pF
        voltage_v: Tensão em V
        frequency_hz: Frequência em Hz

    Returns:
        Tupla com (impedância_capacitiva_ohm, corrente_ma, potência_reativa_kvar)
    """
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
        zc_ohm = 1.0 / (omega * cap_f)
        current_a = v_v / zc_ohm
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


def calculate_circuit_efficiency(
    c_gen_effective_f: float, c_load_total_f: float, impulse_type: str
) -> tuple[float, float, float]:
    """
    Calcula a eficiência total, do circuito e de forma.

    Args:
        c_gen_effective_f: Capacitância efetiva do gerador em F
        c_load_total_f: Capacitância total da carga em F
        impulse_type: Tipo de impulso ("lightning", "chopped", "switching")

    Returns:
        Tupla com (eficiência_total, eficiência_circuito, eficiência_forma)
    """
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


def calculate_energy_requirements(actual_test_voltage_kv: float, c_load_total_f: float) -> float:
    """
    Calcula a energia requerida pela carga durante o ensaio em kJ.

    Args:
        actual_test_voltage_kv: Tensão de teste em kV
        c_load_total_f: Capacitância total da carga em F

    Returns:
        Energia requerida em kJ
    """
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


def calculate_total_load_capacitance(
    c_dut_pf: float,
    c_stray_pf: float,
    impulse_type: str,
    c_divider_f: float,
    c_chopping_gap_f: float = 0.0,
) -> float:
    """
    Calcula a capacitância total da carga vista pelo gerador.

    Args:
        c_dut_pf: Capacitância do objeto sob teste em pF
        c_stray_pf: Capacitância parasita em pF
        impulse_type: Tipo de impulso ("lightning", "chopped", "switching")
        c_divider_f: Capacitância do divisor em F
        c_chopping_gap_f: Capacitância do gap de corte em F

    Returns:
        Capacitância total da carga em F
    """
    c_dut_f = float(c_dut_pf or 0.0) * 1e-12  # Converte pF para F, default 0
    c_stray_f = float(c_stray_pf or 0.0) * 1e-12  # Converte pF para F, default 0
    c_load_extra_f = c_chopping_gap_f if impulse_type == "chopped" else 0.0

    c_load_total_f = c_dut_f + c_divider_f + c_stray_f + c_load_extra_f
    log.debug(
        f"Carga Total: C_dut={c_dut_f*1e12:.0f}pF, C_div={c_divider_f*1e12:.0f}pF, C_stray={c_stray_f*1e12:.0f}pF, C_extra={c_load_extra_f*1e12:.0f}pF => C_load={c_load_total_f*1e9:.2f}nF"
    )
    return c_load_total_f
