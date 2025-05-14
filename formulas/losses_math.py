"""
Fórmulas matemáticas para cálculos de perdas em transformadores.
Centraliza cálculos de perdas em vazio e em carga.
"""

import logging
import math

# Configuração de logging
log = logging.getLogger(__name__)


def calculate_empty_losses(
    tensao_bt: float, inducao: float, peso_nucleo: float, tipo_transformador: str = "Trifásico"
) -> tuple[float, float, float]:
    """
    Calcula perdas em vazio, corrente de excitação e potência magnética.

    Args:
        tensao_bt: Tensão de baixa tensão em kV
        inducao: Indução do núcleo em T
        peso_nucleo: Peso do núcleo em toneladas
        tipo_transformador: Tipo do transformador ('Trifásico' ou 'Monofásico')

    Returns:
        Tupla com (perdas_vazio_kw, corrente_excitacao_a, potencia_magnetica_kvar)
    """
    # Validação de entradas
    if None in [tensao_bt, inducao, peso_nucleo]:
        log.warning("Dados insuficientes para calcular perdas em vazio.")
        return None, None, None

    try:
        tensao_bt_f = float(tensao_bt)
        inducao_f = float(inducao)
        peso_nucleo_f = float(peso_nucleo)

        if tensao_bt_f <= 0 or inducao_f <= 0 or peso_nucleo_f <= 0:
            log.error(
                f"Valores inválidos para cálculo de perdas em vazio: V={tensao_bt_f}, B={inducao_f}, m={peso_nucleo_f}"
            )
            return None, None, None

        # Fator de perdas específicas do núcleo (W/kg) - Aproximação para aço silício GO
        # Valores típicos: 1.0-1.3 W/kg @ 1.7T, 60Hz para aço M4
        fator_perdas = 0.7 * (inducao_f**1.8)  # W/kg

        # Perdas totais no núcleo
        perdas_vazio = fator_perdas * peso_nucleo_f * 1000  # W
        perdas_vazio_kw = perdas_vazio / 1000  # kW

        # Fator de potência magnética (aproximado)
        fator_potencia_mag = 0.2  # Valor típico

        # Potência magnética
        potencia_mag = perdas_vazio / fator_potencia_mag  # VAr
        potencia_mag_kvar = potencia_mag / 1000  # kVAr

        # Fator de excitação diferente para mono e trifásico
        sqrt_3 = math.sqrt(3)
        fator_excitacao = 3 if tipo_transformador == "Trifásico" else 5

        # Corrente de excitação
        corrente_excitacao = (
            potencia_mag / (tensao_bt_f * 1000 * sqrt_3) if tensao_bt_f != 0 else 0
        )  # A

        log.info(
            f"Perdas em vazio calculadas: P0={perdas_vazio_kw:.2f}kW, I0={corrente_excitacao:.2f}A, Q0={potencia_mag_kvar:.2f}kVAr"
        )
        return perdas_vazio_kw, corrente_excitacao, potencia_mag_kvar

    except Exception as e:
        log.exception(f"Erro ao calcular perdas em vazio: {e}")
        return None, None, None


def calculate_load_losses(
    corrente: float,
    impedancia_percent: float,
    tensao: float,
    temperatura_teste: float = 75,
    temperatura_referencia: float = 75,
) -> tuple[float, float, float]:
    """
    Calcula perdas em carga, tensão de curto-circuito e potência de teste.

    Args:
        corrente: Corrente nominal em A
        impedancia_percent: Impedância percentual
        tensao: Tensão nominal em kV
        temperatura_teste: Temperatura de teste em °C
        temperatura_referencia: Temperatura de referência em °C

    Returns:
        Tupla com (perdas_carga_kw, tensao_cc_kv, potencia_teste_mva)
    """
    # Validação de entradas
    if None in [corrente, impedancia_percent, tensao]:
        log.warning("Dados insuficientes para calcular perdas em carga.")
        return None, None, None

    try:
        corrente_f = float(corrente)
        impedancia_f = float(impedancia_percent)
        tensao_f = float(tensao)
        temp_teste_f = float(temperatura_teste)
        temp_ref_f = float(temperatura_referencia)

        if corrente_f <= 0 or impedancia_f <= 0 or tensao_f <= 0:
            log.error(
                f"Valores inválidos para cálculo de perdas em carga: I={corrente_f}, Z%={impedancia_f}, V={tensao_f}"
            )
            return None, None, None

        # Tensão de curto-circuito
        tensao_cc = (tensao_f / 100) * impedancia_f  # kV

        # Potência nominal
        sqrt_3 = math.sqrt(3)
        potencia_nominal = tensao_f * corrente_f * sqrt_3 / 1000  # MVA

        # Perdas em carga (aproximação)
        # Assume 80% perdas ôhmicas (I²R) e 20% perdas adicionais
        perdas_carga = 0.01 * potencia_nominal * 1000  # kW (aproximadamente 1% da potência nominal)

        # Correção de temperatura
        fator_correcao = (235 + temp_ref_f) / (235 + temp_teste_f)  # Para cobre
        perdas_carga_corrigidas = perdas_carga * fator_correcao

        # Potência de teste
        potencia_teste = tensao_cc * corrente_f * sqrt_3 / 1000  # MVA

        log.info(
            f"Perdas em carga calculadas: Pk={perdas_carga_corrigidas:.2f}kW, Vcc={tensao_cc:.2f}kV, Steste={potencia_teste:.2f}MVA"
        )
        return perdas_carga_corrigidas, tensao_cc, potencia_teste

    except Exception as e:
        log.exception(f"Erro ao calcular perdas em carga: {e}")
        return None, None, None
