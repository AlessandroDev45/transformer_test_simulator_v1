"""
Fórmulas matemáticas para cálculos térmicos de transformadores.
Centraliza todos os cálculos relacionados a temperatura e elevação térmica.
"""

import logging
import math

# Configuração de logging
log = logging.getLogger(__name__)

# Constantes para cálculo de elevação de temperatura
TEMP_RISE_CONSTANT = {"cobre": 234.5, "aluminio": 225.0}


def calculate_winding_temps(
    rc: float, tc: float, rw: float, ta: float, material: str = "cobre"
) -> tuple[float, float]:
    """
    Calcula a temperatura média e elevação do enrolamento.

    Args:
        rc: Resistência a frio em Ohms
        tc: Temperatura a frio em °C
        rw: Resistência a quente em Ohms
        ta: Temperatura ambiente em °C
        material: Material do enrolamento ('cobre' ou 'aluminio')

    Returns:
        Tupla com (temperatura_media_enrolamento, elevacao_enrolamento)
    """
    if material not in TEMP_RISE_CONSTANT:
        log.warning(f"Material '{material}' não reconhecido. Usando cobre como padrão.")
        material = "cobre"

    C = TEMP_RISE_CONSTANT[material]
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


def calculate_top_oil_rise(t_oil: float, ta: float) -> float:
    """
    Calcula a elevação do topo do óleo sobre o ambiente.

    Args:
        t_oil: Temperatura do topo do óleo em °C
        ta: Temperatura ambiente em °C

    Returns:
        Elevação do topo do óleo em K
    """
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


def calculate_thermal_time_constant(ptot: float, delta_max: float, mt: float, mo: float) -> float:
    """
    Calcula a constante de tempo térmica do transformador.

    Args:
        ptot: Perdas totais em kW
        delta_max: Elevação máxima do óleo em K
        mt: Massa total do transformador em kg
        mo: Massa do óleo em kg

    Returns:
        Constante de tempo térmica em horas
    """
    if None in [ptot, delta_max, mt, mo]:
        log.warning("Dados insuficientes para calcular constante de tempo térmica.")
        return None
    try:
        if ptot <= 0 or delta_max <= 0 or mt <= 0 or mo <= 0:
            log.error(
                f"Valores inválidos para cálculo de τ₀: Ptot={ptot}, ΔΘmax={delta_max}, mT={mt}, mO={mo}"
            )
            return None

        # Fórmula IEC 60076-2: τ₀ = ( (C_core * m_core) + (C_coil * m_coil) + (C_oil * m_oil) ) / (P_tot / delta_theta_oil_max)
        # Simplificação Anexo C (aproximada): τ₀ = (5*mT + 15*mO) * (ΔΘoil_max / Ptot) / 60.0 [horas]
        # (5*mT + 15*mO) -> Capacidade térmica em kJ/K
        # Ptot -> Perdas em kW (kJ/s)
        # ΔΘoil_max -> Elevação em K
        # (kJ/K) * K / (kJ/s) = s. Dividir por 3600 para ter horas, não 60.
        capacidade_termica_kj_k = 5 * mt + 15 * mo
        # Ptot em kW, precisa converter para kJ/s (que é o mesmo)
        tau0_segundos = capacidade_termica_kj_k * delta_max / ptot if ptot > 1e-9 else float("inf")
        tau0_h = tau0_segundos / 3600.0

        if tau0_h <= 0 or math.isnan(tau0_h) or math.isinf(tau0_h):
            log.error(f"Cálculo de τ₀ resultou em valor inválido: {tau0_h}")
            return None

        log.info(f"Constante de tempo térmica calculada: τ₀ = {tau0_h:.2f} h")
        return tau0_h
    except Exception as e:
        log.exception(f"Erro ao calcular constante de tempo térmica: {e}")
        return None
