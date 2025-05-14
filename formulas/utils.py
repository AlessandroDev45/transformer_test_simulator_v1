"""
Funções matemáticas utilitárias para o simulador de ensaios de transformadores.
"""

import logging
import math
from typing import Any, Optional

import numpy as np

# Configuração de logging
log = logging.getLogger(__name__)


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Converte um valor para float de forma segura.

    Args:
        value: Valor a ser convertido
        default: Valor padrão a ser retornado em caso de erro

    Returns:
        Valor convertido ou valor padrão
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Converte um valor para int de forma segura.

    Args:
        value: Valor a ser convertido
        default: Valor padrão a ser retornado em caso de erro

    Returns:
        Valor convertido ou valor padrão
    """
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def find_nearest_index(array: np.ndarray, value: float) -> int:
    """
    Encontra o índice do valor mais próximo em um array.

    Args:
        array: Array de valores
        value: Valor a ser procurado

    Returns:
        Índice do valor mais próximo
    """
    if len(array) == 0:
        return -1
    idx = (np.abs(array - value)).argmin()
    return idx


def interpolate_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Realiza interpolação linear entre dois pontos.

    Args:
        x: Valor x para interpolação
        x1: Valor x do primeiro ponto
        y1: Valor y do primeiro ponto
        x2: Valor x do segundo ponto
        y2: Valor y do segundo ponto

    Returns:
        Valor y interpolado
    """
    if x2 == x1:
        return (y1 + y2) / 2  # Evita divisão por zero
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)


def calculate_parallel_resistance(*resistances: float) -> float:
    """
    Calcula a resistência equivalente de resistores em paralelo.

    Args:
        *resistances: Valores de resistência em Ohms

    Returns:
        Resistência equivalente em Ohms
    """
    if not resistances:
        return float("inf")

    valid_resistances = []
    for r in resistances:
        try:
            r_float = float(r)
            if r_float <= 0:
                continue
            valid_resistances.append(r_float)
        except (ValueError, TypeError):
            continue

    if not valid_resistances:
        return float("inf")

    inv_sum = sum(1.0 / r for r in valid_resistances)
    return 1.0 / inv_sum if inv_sum > 1e-12 else float("inf")


def calculate_series_resistance(*resistances: float) -> float:
    """
    Calcula a resistência equivalente de resistores em série.

    Args:
        *resistances: Valores de resistência em Ohms

    Returns:
        Resistência equivalente em Ohms
    """
    valid_resistances = []
    for r in resistances:
        try:
            r_float = float(r)
            if r_float < 0:
                continue
            valid_resistances.append(r_float)
        except (ValueError, TypeError):
            continue

    return sum(valid_resistances)


def deg2rad(degrees: float) -> float:
    """
    Converte graus para radianos.

    Args:
        degrees: Ângulo em graus

    Returns:
        Ângulo em radianos
    """
    return degrees * (math.pi / 180.0)


def rad2deg(radians: float) -> float:
    """
    Converte radianos para graus.

    Args:
        radians: Ângulo em radianos

    Returns:
        Ângulo em graus
    """
    return radians * (180.0 / math.pi)
