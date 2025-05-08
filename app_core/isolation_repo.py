# app_core/isolation_repo.py
"""
Repositório de níveis de isolamento com suporte a múltiplas opções para a mesma classe Um.
"""

import json
from pathlib import Path
from collections import defaultdict
import logging
from bisect import bisect_left

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
        _JSON = json.load(fh)
    log.info(f"Tabela de isolamento carregada com sucesso: {len(_JSON['insulation_levels'])} registros")
except Exception as e:
    log.error(f"Erro ao carregar tabela de isolamento: {e}")
    _JSON = {"insulation_levels": []}

# Pré-processar a tabela para indexar por (norma, Um_kV)
IDX = defaultdict(list)
for item in _JSON.get("insulation_levels", []):
    key = (item["standard"].upper().split()[0], float(item["um_kv"]))
    IDX[key].append(item)

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


def candidates(um_kv: float, norma: str = "IEC") -> list[dict]:
    """
    Retorna todos os registros para uma determinada classe de tensão e norma.

    Parameters
    ----------
    um_kv : float
        Classe de tensão (Um) em kV
    norma : str, optional
        Norma a ser utilizada (IEC/NBR ou IEEE), por padrão "IEC"

    Returns
    -------
    list[dict]
        Lista de registros que correspondem à classe de tensão e norma
    """
    # Mapeamento de normas para as chaves no JSON
    norma_map = {
        "IEC": "IEC",
        "NBR": "IEC",  # NBR também usa os valores de IEC
        "IEEE": "IEEE"
    }

    # Garantir que a norma seja uma das chaves válidas
    norma_upper = norma.upper()
    if norma_upper not in norma_map:
        log.warning(f"Norma '{norma}' não reconhecida, usando IEC como padrão")
        norma_upper = "IEC"

    norma_key = norma_map.get(norma_upper, "IEC")
    log.info(f"Buscando níveis de isolamento para norma={norma} (mapeada para {norma_key}) e Um={um_kv}kV")
    return IDX.get((norma_key, float(um_kv)), [])


def pick_level(cands: list[dict]) -> dict:
    """
    Escolhe o nível de isolamento padrão entre os candidatos.

    Parameters
    ----------
    cands : list[dict]
        Lista de candidatos

    Returns
    -------
    dict
        Registro escolhido

    Raises
    ------
    LookupError
        Se não houver candidatos
    """
    if not cands:
        raise LookupError("Sem nível cadastrado")

    # 1º preferência: classification_li == "Rotina" ou "Rotina (Class II)"
    rotina = [c for c in cands if "rotina" in c["classification_li"].lower()]
    alvo = rotina or cands  # se não existir, qualquer um
    return min(alvo, key=lambda x: x["bil_kvp"] or 0)  # menor BIL


def get_isolation_levels(um: float, conexao: str = "", norma: str = "IEC"):
    """
    Calcula os níveis de isolamento para uma classe de tensão.

    Parameters
    ----------
    um : float
        Classe de tensão (Um) em kV
    conexao : str, optional
        Tipo de conexão (YN, D, etc.)
    norma : str, optional
        Norma a ser utilizada (IEC/NBR ou IEEE), por padrão "IEC"

    Returns
    -------
    tuple
        (dict com níveis de isolamento, lista de opções para dropdown)
    """
    # Garantir que a norma seja uma das opções válidas
    if norma not in ["IEC", "IEEE"]:
        log.warning(f"Norma '{norma}' não reconhecida, usando IEC como padrão")
        norma = "IEC"

    log.info(f"Buscando níveis de isolamento para Um={um}kV, conexão={conexao}, norma={norma}")

    cands = candidates(um, norma)
    if not cands:
        log.warning(f"Nenhum registro encontrado para Um={um}kV e norma={norma}")

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

        sil = None if um < 300 else round(nbi * 0.75)
        nbi_neutro = round(nbi * 0.60) if conexao.upper().startswith(("YN", "ZN")) else None

        return {
            "nbi": nbi,
            "sil_im": sil,
            "nbi_neutro": nbi_neutro
        }, []

    escolha = pick_level(cands)

    # Criar lista de opções para dropdown
    lista = [
        {
            "label": f"{c['bil_kvp']} kVp (SIL {c['sil_kvp'] or '-'})",
            "value": c["bil_kvp"],
        }
        for c in cands
        if c["bil_kvp"] is not None
    ]

    nbi = escolha["bil_kvp"]
    sil = escolha["sil_kvp"]
    nbi_neutro = round(nbi * 0.60) if conexao.upper().startswith(("YN", "ZN")) else None

    return {
        "nbi": nbi,
        "sil_im": sil,
        "nbi_neutro": nbi_neutro
    }, lista
