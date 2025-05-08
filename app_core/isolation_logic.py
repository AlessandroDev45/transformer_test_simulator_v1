# app_core/isolation_logic.py
"""
Lógica para cálculo automático de níveis de isolamento baseados na classe de tensão.

Este módulo implementa:
1. Função para derivar a classe de tensão (Um) a partir da tensão nominal
2. Funções para calcular NBI, SIL/IM, LIC e NBI do neutro
"""

from bisect import bisect_left
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

log = logging.getLogger(__name__)

# Degraus padronizados de Um
PADROES_UM_KV = [
    1.2, 3.6, 7.2, 12, 17.5, 24, 36, 52,
    72.5, 123, 145, 170, 245, 300, 362, 420, 550, 800
]

# Caminho para o arquivo de tabela
TABLE_PATH = Path(__file__).parent.parent / "assets" / "tabela.json"

# Carrega a tabela uma vez
try:
    with open(TABLE_PATH, encoding="utf-8") as fh:
        TABLE = json.load(fh)
    log.info(f"Tabela de isolamento carregada com sucesso: {len(TABLE)} classes de tensão")
except Exception as e:
    log.error(f"Erro ao carregar tabela de isolamento: {e}")
    TABLE = {}

def derive_um(voltage_kv_ll: float) -> float:
    """
    Devolve a classe de tensão padronizada IMEDIATAMENTE ACIMA
    da maior tensão fase-fase (kV) que o enrolamento pode experimentar.

    Parameters
    ----------
    voltage_kv_ll : float
        Tensão fase-fase em kV

    Returns
    -------
    float
        Classe de tensão padronizada (Um)

    Raises
    ------
    ValueError
        Se a tensão exceder o maior valor da tabela
    """
    if not voltage_kv_ll or voltage_kv_ll <= 0:
        return PADROES_UM_KV[0]  # Retorna o menor valor da tabela

    idx = bisect_left(PADROES_UM_KV, voltage_kv_ll)
    if idx == len(PADROES_UM_KV):
        raise ValueError(f"Tensão {voltage_kv_ll} kV excede tabela de classes.")
    return PADROES_UM_KV[idx]

def get_isolation_levels(um: float, conexao: str = "") -> Dict[str, Any]:
    """
    Calcula os níveis de isolamento para uma classe de tensão.

    Parameters
    ----------
    um : float
        Classe de tensão (Um) em kV
    conexao : str, optional
        Tipo de conexão (YN, D, etc.)

    Returns
    -------
    Dict[str, Any]
        Dicionário com os níveis de isolamento:
        - nbi: Nível Básico de Isolamento
        - sil_im: Nível de Impulso de Manobra (None se não aplicável)
        - lic: Nível de Impulso Atmosférico Cortado
        - nbi_neutro: NBI do neutro (None se não aplicável)
    """
    # Converte para string com formato adequado para busca na tabela
    um_str = str(int(um))

    # Verifica se a classe de tensão existe na tabela
    if um_str not in TABLE:
        log.warning(f"Classe de tensão {um_str} kV não encontrada na tabela")
        # Valores padrão aproximados baseados na classe de tensão
        if um <= 24:
            nbi = 125
        elif um <= 36:
            nbi = 170
        elif um <= 72.5:
            nbi = 325
        elif um <= 145:
            nbi = 650
        elif um <= 245:
            nbi = 1050
        elif um <= 420:
            nbi = 1425
        else:
            nbi = 1550
    else:
        # Obtém o NBI da tabela
        nbi = TABLE[um_str].get("NBI_kV")
        if nbi is None:
            log.warning(f"NBI não encontrado para classe {um_str} kV")
            return {
                "nbi": None,
                "sil_im": None,
                "lic": None,
                "nbi_neutro": None
            }

    # Calcula SIL/IM (aplicável apenas para Um >= 300 kV)
    # "NA" para classes abaixo de 300 kV
    sil_im = "NA" if um < 300 else round(nbi * 0.75)

    # Calcula LIC (1.10 * NBI para NBR)
    lic = round(nbi * 1.10, 1)

    # Calcula NBI do neutro (60% do NBI principal, apenas para conexão YN)
    # "NA" para conexões sem neutro acessível
    nbi_neutro = round(nbi * 0.60, 1) if conexao.upper().startswith("YN") else "NA"

    return {
        "nbi": nbi,
        "sil_im": sil_im,
        "lic": lic,
        "nbi_neutro": nbi_neutro
    }
