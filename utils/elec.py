"""
Utilitários para cálculos elétricos.
Centraliza funções de cálculo para evitar duplicação de código.
"""
import logging
import math
from typing import Any, Dict, Optional



log = logging.getLogger(__name__)


def safe_float(value, default=None):
    """Converte valor para float de forma segura, retorna default em caso de erro."""
    if value is None or value == "":
        return default
    try:
        # Se o valor já for um número, retorná-lo diretamente
        if isinstance(value, (int, float)):
            return float(value)

        # Se for uma string, tratar formatação
        s_value = str(value).strip()
        # Substituir vírgula por ponto (formato brasileiro para decimal)
        s_value = s_value.replace(",", ".")
        # Remover espaços
        s_value = s_value.replace(" ", "")

        # Verificar se é um número válido
        result = float(s_value)

        # Verificar se é um número positivo
        if result <= 0:
            log.warning(f"Valor '{value}' convertido para {result}, mas é zero ou negativo.")
            return default

        return result
    except (ValueError, TypeError) as e:
        log.warning(f"Could not convert '{value}' to float: {e}")
        return default


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
    result = {
        k: None
        for k in [
            "corrente_nominal_at",
            "corrente_nominal_at_tap_maior",
            "corrente_nominal_at_tap_menor",
            "corrente_nominal_bt",
            "corrente_nominal_terciario",
        ]
    }

    # Se transformer_data for None ou vazio, retornar resultado vazio
    if not transformer_data:
        log.warning("[elec] Dados vazios! Não é possível calcular correntes.")
        return result

    # Extrair valores
    tipo = transformer_data.get("tipo_transformador", "Trifásico")  # Default para Trifásico
    potencia = safe_float(transformer_data.get("potencia_mva"))
    tensao_at = safe_float(transformer_data.get("tensao_at"))
    tensao_at_maior = safe_float(transformer_data.get("tensao_at_tap_maior"))
    tensao_at_menor = safe_float(transformer_data.get("tensao_at_tap_menor"))
    tensao_bt = safe_float(transformer_data.get("tensao_bt"))
    tensao_terciario = safe_float(transformer_data.get("tensao_terciario"))

    # Log detalhado dos valores após conversão
    log.debug(f"[elec] Valores após conversão segura: potencia={potencia}, tensao_at={tensao_at}, tensao_bt={tensao_bt}, tensao_terciario={tensao_terciario}, tensao_at_maior={tensao_at_maior}, tensao_at_menor={tensao_at_menor}")

    # Verificação detalhada dos dados
    log.info(
        f"[elec] Valores para cálculo: tipo={tipo}, potencia={potencia}, "
        + f"tensao_at={tensao_at}, tensao_at_maior={tensao_at_maior}, tensao_at_menor={tensao_at_menor}, "
        + f"tensao_bt={tensao_bt}, tensao_terciario={tensao_terciario}"
    )

    # Verificar se temos valores válidos para o cálculo
    if potencia is None:
        log.warning("[elec] Potência ausente.")
        return result

    if tensao_at is None:
        log.warning("[elec] Tensão AT ausente.")
        result["corrente_nominal_at"] = None
        result["corrente_nominal_at_tap_maior"] = None
        result["corrente_nominal_at_tap_menor"] = None
        return result

    try:
        # Fator para cálculo da corrente
        sqrt3 = math.sqrt(3) if tipo == "Trifásico" else 1.0
        log.info(f"[elec] Fator de cálculo (sqrt3): {sqrt3}")

        # Cálculo das correntes com base no tipo de transformador
        if tipo == "Trifásico":
            # Corrente AT
            result["corrente_nominal_at"] = round((potencia * 1000) / (sqrt3 * tensao_at), 2)
            log.info(f"[elec] Corrente AT calculada: {result['corrente_nominal_at']}A (Fórmula: {potencia}*1000/({sqrt3}*{tensao_at}))")

            # Corrente AT tap maior
            if tensao_at_maior is not None:
                result["corrente_nominal_at_tap_maior"] = round(
                    (potencia * 1000) / (sqrt3 * tensao_at_maior), 2
                )
                log.info(
                    f"[elec] Corrente AT tap maior calculada: {result['corrente_nominal_at_tap_maior']}A (Fórmula: {potencia}*1000/({sqrt3}*{tensao_at_maior}))"
                )

            # Corrente AT tap menor
            if tensao_at_menor is not None:
                result["corrente_nominal_at_tap_menor"] = round(
                    (potencia * 1000) / (sqrt3 * tensao_at_menor), 2
                )
                log.info(
                    f"[elec] Corrente AT tap menor calculada: {result['corrente_nominal_at_tap_menor']}A (Fórmula: {potencia}*1000/({sqrt3}*{tensao_at_menor}))"
                )

            # Corrente BT
            if tensao_bt is not None:
                result["corrente_nominal_bt"] = round((potencia * 1000) / (sqrt3 * tensao_bt), 2)
                log.info(f"[elec] Corrente BT calculada: {result['corrente_nominal_bt']}A (Fórmula: {potencia}*1000/({sqrt3}*{tensao_bt}))")

            # Corrente Terciário
            if tensao_terciario is not None:
                result["corrente_nominal_terciario"] = round(
                    (potencia * 1000) / (sqrt3 * tensao_terciario), 2
                )
                log.info(
                    f"[elec] Corrente Terciário calculada: {result['corrente_nominal_terciario']}A (Fórmula: {potencia}*1000/({sqrt3}*{tensao_terciario}))"
                )
        else:  # Monofásico
            # Corrente AT
            result["corrente_nominal_at"] = round((potencia * 1000) / tensao_at, 2)
            log.info(
                f"[elec] Corrente AT calculada (monofásico): {result['corrente_nominal_at']}A (Fórmula: {potencia}*1000/{tensao_at})"
            )

            # Corrente AT tap maior
            if tensao_at_maior is not None:
                result["corrente_nominal_at_tap_maior"] = round(
                    (potencia * 1000) / tensao_at_maior, 2
                )
                log.info(
                    f"[elec] Corrente AT tap maior calculada (monofásico): {result['corrente_nominal_at_tap_maior']}A (Fórmula: {potencia}*1000/{tensao_at_maior})"
                )

            # Corrente AT tap menor
            if tensao_at_menor is not None:
                result["corrente_nominal_at_tap_menor"] = round(
                    (potencia * 1000) / tensao_at_menor, 2
                )
                log.info(
                    f"[elec] Corrente AT tap menor calculada (monofásico): {result['corrente_nominal_at_tap_menor']}A (Fórmula: {potencia}*1000/{tensao_at_menor})"
                )

            # Corrente BT
            if tensao_bt is not None:
                result["corrente_nominal_bt"] = round((potencia * 1000) / tensao_bt, 2)
                log.info(
                    f"[elec] Corrente BT calculada (monofásico): {result['corrente_nominal_bt']}A (Fórmula: {potencia}*1000/{tensao_bt})"
                )

            # Corrente Terciário
            if tensao_terciario is not None:
                result["corrente_nominal_terciario"] = round(
                    (potencia * 1000) / tensao_terciario, 2
                )
                log.info(
                    f"[elec] Corrente Terciário calculada (monofásico): {result['corrente_nominal_terciario']}A (Fórmula: {potencia}*1000/{tensao_terciario})"
                )

        # Log final com todos os resultados calculados
        log.info(f"[elec] RESULTADOS FINAIS DE CORRENTES: {result}")

    except Exception as e:
        log.error(f"[elec] Erro inesperado no cálculo: {e}", exc_info=True)
        # Em caso de erro inesperado, retornar todos os valores nulos
        for key in result:
            result[key] = None

    return result



