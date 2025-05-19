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


def candidates(um_kv: float, norma: str = "IEC") -> list:
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


def get_distinct_values_for_norma(norma_prefix: str, key: str) -> list:
    """
    Retorna uma lista de valores distintos para uma chave específica (bil_kvp, sil_kvp, etc.)
    de todos os níveis de isolamento para uma dada norma.

    Parameters
    ----------
    norma_prefix : str
        Prefixo da norma (IEC, IEEE, etc.)
    key : str
        Chave a ser buscada (bil_kvp, sil_kvp, acsd_kv_rms, etc.)

    Returns
    -------
    list
        Lista de valores distintos ordenados
    """
    # Mapear a norma para o formato usado no JSON
    standard_filter = "IEC/NBR" if norma_prefix.upper() in ["IEC", "NBR"] else "IEEE"

    distinct_values = set()

    try:
        # Carregar dados do JSON
        with open("assets/tabela.json", "r", encoding="utf-8") as f:
            tabela_data = json.load(f)
            insulation_levels = tabela_data.get("insulation_levels", [])

            for nivel in insulation_levels:
                if nivel.get("standard") == standard_filter:
                    valor = nivel.get(key)
                    if isinstance(valor, list):
                        for v_item in valor:
                            if v_item is not None and v_item != "NA":
                                distinct_values.add(v_item)
                    elif valor is not None and valor != "NA":
                        distinct_values.add(valor)
    except Exception as e:
        log.error(f"Erro ao obter valores distintos para {key} na norma {norma_prefix}: {e}")

    # Tenta converter para float e ordenar, depois para string para o dropdown value
    sorted_numeric_values = []
    non_numeric_values = []

    for v in distinct_values:
        try:
            sorted_numeric_values.append(float(v))
        except (ValueError, TypeError):
            non_numeric_values.append(str(v))

    sorted_numeric_values.sort()

    # Mantém os valores como números para retorno
    return sorted_numeric_values + sorted(non_numeric_values)


def create_options_for_key(norma_prefix: str, key: str, label_suffix: str = "") -> list:
    """
    Cria uma lista de opções de dropdown para uma chave específica (bil_kvp, sil_kvp, etc.)
    contendo todos os valores distintos para a norma dada.

    Parameters
    ----------
    norma_prefix : str
        Prefixo da norma (IEC, IEEE, etc.)
    key : str
        Chave a ser buscada (bil_kvp, sil_kvp, acsd_kv_rms, etc.)
    label_suffix : str, optional
        Sufixo para o label das opções, por padrão ""

    Returns
    -------
    list
        Lista de opções para dropdown no formato [{"label": "X kVp", "value": "X"}, ...]
    """
    distinct_raw_values = get_distinct_values_for_norma(norma_prefix, key)

    options = []
    if not distinct_raw_values:
        return [{"label": "N/A", "value": ""}]

    for val in distinct_raw_values:
        options.append({"label": f"{val}{label_suffix}", "value": str(val)})

    # Para SIL/IM, explicitamente adicionar "Não Aplicável" se for uma opção comum para certas classes/normas
    if key in ["sil_kvp", "bsl_kvp"] and not any(opt['value'] == "NA_SIL" for opt in options):
        # Adiciona no início para ser o primeiro
        options.insert(0, {"label": "Não Aplicável", "value": "NA_SIL"})

    if not options:  # Fallback final
        return [{"label": "N/A", "value": ""}]

    return options


def get_isolation_levels(um: float, conexao: str = "", norma: str = "IEC"):
    """
    Busca os níveis de isolamento diretamente na tabela.json para uma classe de tensão.

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
        O dicionário contém tanto valores padrão quanto listas de todas as opções disponíveis
    """
    # Garantir que a norma seja uma das opções válidas
    if norma not in ["IEC", "IEEE", "NBR"]:
        log.warning(f"Norma '{norma}' não reconhecida, usando IEC como padrão")
        norma = "IEC"

    # Mapear a norma para o formato usado no JSON
    standard_filter = "IEC/NBR" if norma in ["IEC", "NBR"] else "IEEE"

    log.debug(f"[ISOLATION] ============ INÍCIO DA BUSCA ============")
    log.debug(f"[ISOLATION] Buscando níveis de isolamento para Um={um}kV, conexão={conexao}, norma={norma} (standard_filter={standard_filter})")

    # Buscar registro diretamente na tabela.json
    target_record = None
    all_records = []

    try:
        # Carregar dados do JSON
        with open("assets/tabela.json", "r", encoding="utf-8") as f:
            tabela_data = json.load(f)
            insulation_levels = tabela_data.get("insulation_levels", [])

            log.debug(f"[ISOLATION] Tabela carregada com {len(insulation_levels)} registros")

            # Listar todos os registros disponíveis para debug (nível TRACE, que não existe em Python)
            # Comentado para reduzir verbosidade
            # for record in insulation_levels:
            #     record_id = record.get("id", "")
            #     record_standard = record.get("standard", "")
            #     record_um_kv = record.get("um_kv", "")
            #     log.debug(f"[ISOLATION] Registro disponível: ID={record_id}, Standard={record_standard}, Um={record_um_kv}")
            #     all_records.append(record)
            all_records = insulation_levels

            # Buscar registro exato para a classe de tensão e norma
            for record in insulation_levels:
                if record.get("standard") == standard_filter:
                    record_um_kv = record.get("um_kv")
                    if record_um_kv is not None:
                        try:
                            record_um_float = float(record_um_kv)
                            # Comentado para reduzir verbosidade
                            # log.debug(f"[ISOLATION] Comparando: record_um={record_um_float}, target_um={um}, diff={abs(record_um_float - um)}")
                            if abs(record_um_float - um) < 0.001:  # Comparação com tolerância
                                target_record = record
                                log.debug(f"[ISOLATION] MATCH ENCONTRADO: ID={record.get('id')}")
                                break
                        except (ValueError, TypeError) as e:
                            log.warning(f"[ISOLATION] Erro ao converter um_kv={record_um_kv}: {e}")
                            pass  # Ignora registros com um_kv não numérico
    except Exception as e:
        log.error(f"[ISOLATION] Erro ao carregar tabela.json: {e}")

    # Log detalhado do registro encontrado
    if target_record:
        log.debug(f"[ISOLATION] Registro encontrado: ID={target_record.get('id')}")
        # Comentado para reduzir verbosidade
        # log.debug(f"[ISOLATION] Registro completo: {json.dumps(target_record, indent=2)}")
        log.debug(f"[ISOLATION] BIL={target_record.get('bil_kvp')}, SIL={target_record.get('sil_kvp')}")
        log.debug(f"[ISOLATION] TA={target_record.get('acsd_kv_rms')}, TI={target_record.get('acld_kv_rms')}")
    else:
        log.warning(f"[ISOLATION] Nenhum registro encontrado para Um={um}kV e norma={standard_filter}. Usando valores padrão.")
        # Comentado para reduzir verbosidade
        # log.debug(f"[ISOLATION] Registros disponíveis para esta norma:")
        # for record in all_records:
        #     if record.get("standard") == standard_filter:
        #         log.debug(f"[ISOLATION]   - ID={record.get('id')}, Um={record.get('um_kv')}")

        # Valores padrão aproximados baseados na classe de tensão
        if um <= 24:
            nbi = 125
            ta = 50
        elif um <= 36:
            nbi = 170
            ta = 70
        elif um <= 72.5:
            nbi = 325
            ta = 140
        elif um <= 145:
            nbi = 650
            ta = 230
        elif um <= 245:
            nbi = 1050
            ta = 395
        elif um <= 420:
            nbi = 1425
            ta = 570
        else:
            nbi = 1550
            ta = 680

        # Calcular SIL/IM (apenas para Um >= 300kV)
        sil = None if um < 300 else round(nbi * 0.75)

        # Calcular TI (geralmente 2x a tensão nominal)
        ti = round(um * 2) if um >= 72.5 else None

        # Calcular NBI do neutro (60% do NBI principal para conexões YN ou ZN)
        nbi_neutro = round(nbi * 0.60) if conexao.upper().startswith(("YN", "ZN")) else None

        log.debug(f"[ISOLATION] Valores padrão calculados: NBI={nbi}, SIL/IM={sil}, TA={ta}, TI={ti}, NBI_NEUTRO={nbi_neutro}")

        # Retornar valores únicos e listas com um único elemento para compatibilidade
        result = {
            # Valores padrão (compatibilidade com código existente)
            "nbi": nbi,
            "sil_im": sil,
            "nbi_neutro": nbi_neutro,
            "tensao_aplicada": ta,
            "tensao_induzida": ti,
            # Listas de valores (para suportar múltiplas opções)
            "nbi_list": [nbi],
            "sil_im_list": [sil] if sil is not None else [],
            "nbi_neutro_list": [nbi_neutro] if nbi_neutro is not None else [],
            "tensao_aplicada_list": [ta],
            "tensao_induzida_list": [ti] if ti is not None else []
        }
        log.debug(f"[ISOLATION] ============ FIM DA BUSCA (VALORES PADRÃO) ============")
        return result, []

    # Extrair valores do registro encontrado
    # NBI (BIL)
    nbi_list = target_record.get("bil_kvp", [])
    log.debug(f"[ISOLATION] NBI original do registro: {nbi_list}")
    if isinstance(nbi_list, list):
        nbi = nbi_list[0] if nbi_list else None
    else:
        nbi = nbi_list
        nbi_list = [nbi] if nbi is not None else []

    # SIL/IM
    sil_list = target_record.get("sil_kvp", [])
    log.debug(f"[ISOLATION] SIL original do registro: {sil_list}")
    if isinstance(sil_list, list):
        sil = sil_list[0] if sil_list else None
    else:
        sil = sil_list
        sil_list = [sil] if sil is not None else []

    # TA (ACSD)
    ta_list = target_record.get("acsd_kv_rms", [])
    log.debug(f"[ISOLATION] TA original do registro: {ta_list}")
    if isinstance(ta_list, list):
        ta = ta_list[0] if ta_list else None
    else:
        ta = ta_list
        ta_list = [ta] if ta is not None else []

    # TI (ACLD)
    ti_list = target_record.get("acld_kv_rms", [])
    log.debug(f"[ISOLATION] TI original do registro: {ti_list}")
    if isinstance(ti_list, list):
        ti = ti_list[0] if ti_list else None
    else:
        ti = ti_list
        ti_list = [ti] if ti is not None else []

    # Calcular NBI do neutro (60% do NBI principal para conexões YN ou ZN)
    nbi_neutro = round(nbi * 0.60) if nbi is not None and conexao.upper().startswith(("YN", "ZN")) else None
    nbi_neutro_list = [round(n * 0.60) for n in nbi_list if n is not None] if conexao.upper().startswith(("YN", "ZN")) else []

    # Criar lista de opções para dropdown (compatibilidade com código existente)
    lista = [
        {
            "label": f"{nbi_val} kVp (SIL {sil_val or '-'})",
            "value": nbi_val,
        }
        for nbi_val, sil_val in zip(nbi_list, sil_list + [None] * (len(nbi_list) - len(sil_list)))
        if nbi_val is not None
    ]
    log.debug(f"[ISOLATION] Opções de dropdown criadas: {lista}")

    log.debug(f"[ISOLATION] Valores finais: NBI={nbi}, SIL/IM={sil}, TA={ta}, TI={ti}, NBI_NEUTRO={nbi_neutro}")
    log.debug(f"[ISOLATION] Listas de opções: NBI={nbi_list}, SIL/IM={sil_list}, TA={ta_list}, TI={ti_list}, NBI_NEUTRO={nbi_neutro_list}")

    result = {
        # Valores padrão (compatibilidade com código existente)
        "nbi": nbi,
        "sil_im": sil,
        "nbi_neutro": nbi_neutro,
        "tensao_aplicada": ta,
        "tensao_induzida": ti,
        # Listas de valores (para suportar múltiplas opções)
        "nbi_list": nbi_list,
        "sil_im_list": sil_list,
        "nbi_neutro_list": nbi_neutro_list,
        "tensao_aplicada_list": ta_list,
        "tensao_induzida_list": ti_list
    }
    log.debug(f"[ISOLATION] ============ FIM DA BUSCA (VALORES DA TABELA) ============")
    return result, lista
