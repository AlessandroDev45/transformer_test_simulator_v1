"""
Utilitários para cálculos elétricos.
Centraliza funções de cálculo para evitar duplicação de código.
"""
import math
import logging
from typing import Dict, Any, Optional, Union, List, Tuple

from utils.validators import safe_float

log = logging.getLogger(__name__)

def calculate_nominal_currents(transformer_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Calcula as correntes nominais do transformador.
    
    Args:
        transformer_data: Dicionário com os dados do transformador
        
    Returns:
        Dicionário com as correntes calculadas
    """
    log.debug("[elec] Calculating nominal currents...")
    
    # Inicializar resultado
    result = {k: None for k in [
        'corrente_nominal_at', 
        'corrente_nominal_at_tap_maior', 
        'corrente_nominal_at_tap_menor', 
        'corrente_nominal_bt', 
        'corrente_nominal_terciario'
    ]}
    
    # Se transformer_data for None ou vazio, retornar resultado vazio
    if not transformer_data:
        log.warning("[elec] Dados vazios! Não é possível calcular correntes.")
        return result
    
    # Extrair valores
    tipo = transformer_data.get('tipo_transformador', 'Trifásico')  # Default para Trifásico
    potencia = safe_float(transformer_data.get('potencia_mva'))
    tensao_at = safe_float(transformer_data.get('tensao_at'))
    tensao_at_maior = safe_float(transformer_data.get('tensao_at_tap_maior'))
    tensao_at_menor = safe_float(transformer_data.get('tensao_at_tap_menor'))
    tensao_bt = safe_float(transformer_data.get('tensao_bt'))
    tensao_terciario = safe_float(transformer_data.get('tensao_terciario'))
    
    # Verificação detalhada dos dados
    log.debug(f"[elec] Valores para cálculo: tipo={tipo}, potencia={potencia}, " +
             f"tensao_at={tensao_at}, tensao_bt={tensao_bt}, tensao_terciario={tensao_terciario}")
    
    # Verificar se temos valores válidos para o cálculo
    if potencia <= 0:
        log.warning("[elec] Potência inválida ou ausente.")
        return result
    
    if tensao_at <= 0:
        log.warning("[elec] Tensão AT inválida ou ausente.")
        result['corrente_nominal_at'] = None
        result['corrente_nominal_at_tap_maior'] = None
        result['corrente_nominal_at_tap_menor'] = None
    
    if tensao_bt <= 0:
        log.warning("[elec] Tensão BT inválida ou ausente.")
        result['corrente_nominal_bt'] = None
    
    try:
        # Fator para cálculo da corrente
        sqrt3 = math.sqrt(3) if tipo == 'Trifásico' else 1.0
        
        # Cálculo das correntes com base no tipo de transformador
        if tipo == 'Trifásico':
            if tensao_at > 0:
                result['corrente_nominal_at'] = round((potencia * 1000) / (sqrt3 * tensao_at), 2)
                log.debug(f"[elec] Corrente AT calculada: {result['corrente_nominal_at']}A")
            
            if tensao_at_maior > 0:
                result['corrente_nominal_at_tap_maior'] = round((potencia * 1000) / (sqrt3 * tensao_at_maior), 2)
                log.debug(f"[elec] Corrente AT tap maior calculada: {result['corrente_nominal_at_tap_maior']}A")
            
            if tensao_at_menor > 0:
                result['corrente_nominal_at_tap_menor'] = round((potencia * 1000) / (sqrt3 * tensao_at_menor), 2)
                log.debug(f"[elec] Corrente AT tap menor calculada: {result['corrente_nominal_at_tap_menor']}A")
            
            if tensao_bt > 0:
                result['corrente_nominal_bt'] = round((potencia * 1000) / (sqrt3 * tensao_bt), 2)
                log.debug(f"[elec] Corrente BT calculada: {result['corrente_nominal_bt']}A")
            
            if tensao_terciario > 0:
                result['corrente_nominal_terciario'] = round((potencia * 1000) / (sqrt3 * tensao_terciario), 2)
                log.debug(f"[elec] Corrente Terciário calculada: {result['corrente_nominal_terciario']}A")
        else:  # Monofásico
            if tensao_at > 0:
                result['corrente_nominal_at'] = round((potencia * 1000) / tensao_at, 2)
                log.debug(f"[elec] Corrente AT calculada (monofásico): {result['corrente_nominal_at']}A")
            
            if tensao_at_maior > 0:
                result['corrente_nominal_at_tap_maior'] = round((potencia * 1000) / tensao_at_maior, 2)
                log.debug(f"[elec] Corrente AT tap maior calculada (monofásico): {result['corrente_nominal_at_tap_maior']}A")
            
            if tensao_at_menor > 0:
                result['corrente_nominal_at_tap_menor'] = round((potencia * 1000) / tensao_at_menor, 2)
                log.debug(f"[elec] Corrente AT tap menor calculada (monofásico): {result['corrente_nominal_at_tap_menor']}A")
            
            if tensao_bt > 0:
                result['corrente_nominal_bt'] = round((potencia * 1000) / tensao_bt, 2)
                log.debug(f"[elec] Corrente BT calculada (monofásico): {result['corrente_nominal_bt']}A")
            
            if tensao_terciario > 0:
                result['corrente_nominal_terciario'] = round((potencia * 1000) / tensao_terciario, 2)
                log.debug(f"[elec] Corrente Terciário calculada (monofásico): {result['corrente_nominal_terciario']}A")
    
    except Exception as e:
        log.error(f"[elec] Erro inesperado no cálculo: {e}", exc_info=True)
        # Em caso de erro inesperado, retornar todos os valores nulos
        for key in result:
            result[key] = None
    
    return result

def format_current(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Formata um valor de corrente com o número especificado de casas decimais.
    
    Args:
        value: Valor da corrente
        decimal_places: Número de casas decimais
        
    Returns:
        String formatada
    """
    if value is None:
        return "-"
    return f"{value:.{decimal_places}f}A"
