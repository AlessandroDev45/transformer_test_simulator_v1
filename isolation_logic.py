from __future__ import annotations

import dash

"""
Lógica consolidada e *test‑friendly* para determinação automática de:
  • NBI / BIL
  • SIL / IM
  • LI  (LIC – impulso atmosférico cortado)
  • NBI do neutro

Regras implementadas
--------------------
1.  Valores‑base vêm da tabela JSON em `tabela.json`, separada por norma:
        {
          "NBR": {"Um_kV": {"NBI": int, "LI": int}},
          "IEEE": {"Um_kV": {"BIL": int}}
        }
   Caso a chave não exista, é levantada `KeyError` explícita.

2.  SIL/IM só existe para Um ≥ 300 kV e é calculado como
        SIL/IM = round(0.75 * NBI)
    — retorna `None` abaixo desse limite.

3.  LIC:
        LIC_NBR   = round(1.10 * NBI_NBR)
        LIC_IEEE  = round(1.15 * BIL_IEEE)

4.  NBI neutro (fase‑terra) = 0.60 × NBI fase, **apenas** se a conexão
    for estrela aterrada (YN).

Funções públicas
----------------
• `get_isolation_set(um_kv: int | float,
                    conexao: str,
                    norma: str = "NBR") -> dict`
    Retorna dicionário com todos os valores calculados já tratados com
    `None` quando não se aplicam.

• `dash_update_isolation(um_kv, conexao)` — função pronta para ser usada
  como callback no Dash, atualizando *dropdowns* de NBI / IM / etc.

Todo: testes unitários em `tests/test_isolation_logic.py`.
"""

from dataclasses import dataclass
from pathlib import Path
import json
from functools import lru_cache
from typing import Any, Dict, Optional

# -----------------------------------------------------------------------------
# Carregamento da tabela
# -----------------------------------------------------------------------------
_TABLE_PATH = Path(__file__).with_name("tabela.json")

@lru_cache(maxsize=1)
def _load_table() -> Dict[str, Any]:
    if not _TABLE_PATH.exists():
        raise FileNotFoundError(f"Tabela de isolamento não encontrada em {_TABLE_PATH}")
    with _TABLE_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)

# -----------------------------------------------------------------------------
# Helpers de cálculo
# -----------------------------------------------------------------------------

def _round(x: float) -> int:
    """Arredonda para inteiro mais próximo mantendo compatibilidade com normas."""
    return int(round(x))

@dataclass(frozen=True)
class IsolationSet:
    nbi: int
    lic: int
    sil_im: Optional[int]
    neutro: Optional[int]

    def to_dict(self) -> Dict[str, Optional[int]]:
        return {
            "NBI": self.nbi,
            "LIC": self.lic,
            "SIL/IM": self.sil_im,
            "NBI_neutro": self.neutro,
        }

# -----------------------------------------------------------------------------
# API pública
# -----------------------------------------------------------------------------

def get_isolation_set(um_kv: float | int, conexao: str, norma: str = "NBR") -> IsolationSet:
    """Calcula todos os níveis de isolamento para a *classe de tensão* dada.

    Parameters
    ----------
    um_kv : int | float
        Classe de tensão Um em kV (e.g. 230). Pode vir como str; será convertida.
    conexao : str
        Código da conexão ("yn", "yn0", "yn11", "d", etc.). A presença de
        "yn" em qualquer *case* indica estrela aterrada.
    norma : {"NBR", "IEEE"}
        Qual tabela usar como origem.

    Returns
    -------
    IsolationSet
        Estrutura com NBI/BIL, LIC, SIL/IM (quando aplicável) e NBI neutro.
    """
    um_key = str(int(round(float(um_kv))))  # normaliza p/ string inteira
    data = _load_table()

    norma = norma.upper()
    if norma not in data:
        raise ValueError(f"Norma desconhecida: {norma}")
    if um_key not in data[norma]:
        raise KeyError(f"Classe de tensão {um_key} kV não encontrada para {norma}")

    # --- NBI / BIL -----------------------------------------------------------
    if norma == "NBR":
        nbi = int(data["NBR"][um_key]["NBI"])
    else:  # IEEE
        nbi = int(data["IEEE"][um_key]["BIL"])

    # --- SIL / IM ------------------------------------------------------------
    sil_im = _round(0.75 * nbi) if float(um_kv) >= 300 else None

    # --- LIC -----------------------------------------------------------------
    fator_lic = 1.10 if norma == "NBR" else 1.15
    lic = _round(fator_lic * nbi)

    # --- Neutro --------------------------------------------------------------
    neutro = _round(0.60 * nbi) if "YN" in conexao.upper() else None

    return IsolationSet(nbi=nbi, lic=lic, sil_im=sil_im, neutro=neutro)

# -----------------------------------------------------------------------------
# Dash integration helper
# -----------------------------------------------------------------------------

def dash_update_isolation(um_kv, conexao):
    """Pode ser usado diretamente como *callback* no Dash.

    *Inputs*
        - um_kv      : valor do dropdown de classe de tensão
        - conexao    : valor do dropdown de conexão

    *Outputs*
        - options/values para os quatro dropdowns de NBI, IM, LIC, Neutro.
    """
    if um_kv is None:
        raise dash.exceptions.PreventUpdate

    iso_nbr = get_isolation_set(um_kv, conexao, "NBR").to_dict()
    iso_ieee = get_isolation_set(um_kv, conexao, "IEEE").to_dict()

    # Monta opções (poderá virar toggle de norma no futuro)
    def _opts(val):
        return [{"label": str(val), "value": val}] if val is not None else []

    return (
        _opts(iso_nbr["NBI"]), iso_nbr["NBI"],          # NBI dropdown
        _opts(iso_nbr["SIL/IM"]), iso_nbr["SIL/IM"],    # IM dropdown
        _opts(iso_nbr["LIC"]), iso_nbr["LIC"],          # LIC dropdown
        _opts(iso_nbr["NBI_neutro"]), iso_nbr["NBI_neutro"],  # Neutro dropdown
    )
