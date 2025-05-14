# --- START OF FILE app_core/data_models.py ---

# app_core/data_models.py
"""
Defines Pydantic models for structuring and validating data
stored in dcc.Store components throughout the application.
"""

import datetime
import math  # For NaN/Inf checks
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# --- Helper Function for Validation (Optional) ---
def check_positive(v: Optional[float]) -> Optional[float]:
    if v is not None and v <= 0:
        raise ValueError("Value must be positive")
    # Allow NaN and Inf initially, they will be handled during conversion/saving
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return v  # Keep them for now
    return v


def check_non_negative(v: Optional[float]) -> Optional[float]:
    if v is not None and v < 0:
        raise ValueError("Value must be non-negative")
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return v  # Keep them for now
    return v


# --- Transformer Inputs Store Model ---
class TransformerInputsData(BaseModel):
    tipo_transformador: Optional[str] = Field(
        default="Trifásico", description="Tipo: Monofásico ou Trifásico"
    )
    potencia_mva: Optional[float] = Field(default=None, description="Potência nominal (MVA)")
    frequencia: Optional[float] = Field(default=60.0, description="Frequência nominal (Hz)")
    # AT
    tensao_at: Optional[float] = Field(default=None, description="Tensão nominal AT (kV)")
    corrente_nominal_at: Optional[float] = Field(
        default=None, description="Corrente nominal AT (A) - Calculada"
    )
    impedancia: Optional[float] = Field(default=None, description="Impedância nominal (%)")
    nbi_at: Optional[Union[int, float, str]] = Field(
        default=None, description="NBI AT (kV)"
    )  # Accept string for 'na'
    sil_at: Optional[Union[int, float, str]] = Field(
        default=None, description="SIL AT (kV)"
    )  # Accept string for 'na'
    conexao_at: Optional[str] = Field(
        default="estrela", description="Conexão AT (estrela, estrela_sem_neutro, triangulo)"
    )
    classe_tensao_at: Optional[float] = Field(default=None, description="Classe Tensão AT (kV)")
    elevacao_enrol_at: Optional[float] = Field(
        default=None, description="Elev. Enrolamento AT (°C)"
    )
    tensao_bucha_neutro_at: Optional[float] = Field(
        default=None, description="Tensão Bucha Neutro AT (kV)"
    )
    nbi_neutro_at: Optional[Union[int, float, str]] = Field(
        default=None, description="NBI Neutro AT (kV)"
    )  # Accept string for 'na'
    # AT Taps
    tensao_at_tap_maior: Optional[float] = Field(default=None, description="Tensão Tap+ AT (kV)")
    corrente_nominal_at_tap_maior: Optional[float] = Field(
        default=None, description="Corrente Tap+ AT (A) - Calculada"
    )
    impedancia_tap_maior: Optional[float] = Field(default=None, description="Impedância Tap+ (%)")
    tensao_at_tap_menor: Optional[float] = Field(default=None, description="Tensão Tap- AT (kV)")
    corrente_nominal_at_tap_menor: Optional[float] = Field(
        default=None, description="Corrente Tap- AT (A) - Calculada"
    )
    impedancia_tap_menor: Optional[float] = Field(default=None, description="Impedância Tap- (%)")
    # BT
    tensao_bt: Optional[float] = Field(default=None, description="Tensão nominal BT (kV)")
    corrente_nominal_bt: Optional[float] = Field(
        default=None, description="Corrente nominal BT (A) - Calculada"
    )
    nbi_bt: Optional[Union[int, float, str]] = Field(default=None, description="NBI BT (kV)")
    sil_bt: Optional[Union[int, float, str]] = Field(default=None, description="SIL BT (kV)")
    conexao_bt: Optional[str] = Field(
        default="triangulo", description="Conexão BT (estrela, estrela_sem_neutro, triangulo)"
    )
    classe_tensao_bt: Optional[float] = Field(default=None, description="Classe Tensão BT (kV)")
    elevacao_enrol_bt: Optional[float] = Field(
        default=None, description="Elev. Enrolamento BT (°C)"
    )
    tensao_bucha_neutro_bt: Optional[float] = Field(
        default=None, description="Tensão Bucha Neutro BT (kV)"
    )
    nbi_neutro_bt: Optional[Union[int, float, str]] = Field(
        default=None, description="NBI Neutro BT (kV)"
    )
    # Terciario
    tensao_terciario: Optional[float] = Field(
        default=None, description="Tensão nominal Terciário (kV)"
    )
    corrente_nominal_terciario: Optional[float] = Field(
        default=None, description="Corrente nominal Terciário (A) - Calculada"
    )
    nbi_terciario: Optional[Union[int, float, str]] = Field(
        default=None, description="NBI Terciário (kV)"
    )
    sil_terciario: Optional[Union[int, float, str]] = Field(
        default=None, description="SIL Terciário (kV)"
    )
    conexao_terciario: Optional[str] = Field(
        default="", description="Conexão Terciário (estrela, estrela_sem_neutro, triangulo, '')"
    )
    classe_tensao_terciario: Optional[float] = Field(
        default=None, description="Classe Tensão Terciário (kV)"
    )
    elevacao_enrol_terciario: Optional[float] = Field(
        default=None, description="Elev. Enrolamento Terciário (°C)"
    )
    tensao_bucha_neutro_terciario: Optional[float] = Field(
        default=None, description="Tensão Bucha Neutro Terciário (kV)"
    )
    nbi_neutro_terciario: Optional[Union[int, float, str]] = Field(
        default=None, description="NBI Neutro Terciário (kV)"
    )
    # Geral
    grupo_ligacao: Optional[str] = Field(default=None, description="Grupo de Ligação (Ex: Dyn1)")
    liquido_isolante: Optional[str] = Field(default="Mineral", description="Líquido Isolante")
    elevacao_oleo_topo: Optional[float] = Field(
        default=None, description="Elev. Óleo no Topo (°C/K)"
    )
    elevacao_enrol: Optional[float] = Field(
        default=None, description="Elev. Enrolamento Comum (°C)"
    )
    tipo_isolamento: Optional[str] = Field(default="uniforme", description="Tipo de Isolamento")
    # Tensões de Ensaio (Podem ser nulas se não definidas)
    teste_tensao_aplicada_at: Optional[Union[int, float, str]] = Field(
        default=None, description="Tensão Aplicada AT (kV)"
    )
    teste_tensao_aplicada_bt: Optional[Union[int, float, str]] = Field(
        default=None, description="Tensão Aplicada BT (kV)"
    )
    teste_tensao_aplicada_terciario: Optional[Union[int, float, str]] = Field(
        default=None, description="Tensão Aplicada Terciário (kV)"
    )
    teste_tensao_induzida: Optional[Union[int, float, str]] = Field(
        default=None, description="Tensão Induzida AT (kV)"
    )
    # Pesos
    peso_total: Optional[float] = Field(default=None, description="Peso Total (ton)")
    peso_parte_ativa: Optional[float] = Field(default=None, description="Peso Parte Ativa (ton)")
    peso_oleo: Optional[float] = Field(default=None, description="Peso Óleo (ton)")
    peso_tanque_acessorios: Optional[float] = Field(
        default=None, description="Peso Tanque/Acessórios (ton)"
    )
    timestamp: Optional[datetime.datetime] = Field(
        default=None, description="Timestamp da última atualização"
    )

    class Config:
        extra = "ignore"  # Ignora campos extras do store
        validate_assignment = True  # Valida ao atribuir valores


# --- Losses Store Model ---
class LossesData(BaseModel):
    # Mantendo a estrutura flexível, pois a saída pode variar
    resultados_perdas_vazio: Optional[Dict[str, Any]] = Field(default={})
    resultados_perdas_carga: Optional[Dict[str, Any]] = Field(default={})
    # Campos adicionais que podem ser salvos
    perdas_vazio_kw: Optional[float] = None
    peso_nucleo: Optional[float] = None
    corrente_excitacao: Optional[float] = None
    inducao: Optional[float] = None
    corrente_exc_1_1: Optional[float] = None
    corrente_exc_1_2: Optional[float] = None
    temperatura_referencia: Optional[float] = None
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "allow"  # Permite campos extras para compatibilidade


# --- Impulse Store Model ---
class ImpulseSimulationData(BaseModel):  # Mantendo flexível
    inputs: Optional[Dict[str, Any]] = Field(default={})
    analysis: Optional[Dict[str, Any]] = Field(default={})
    circuit_params: Optional[Dict[str, Any]] = Field(default={})
    voltages: Optional[Dict[str, Any]] = Field(default={})
    efficiency: Optional[Dict[str, Any]] = Field(default={})
    energy: Optional[Dict[str, Any]] = Field(default={})
    compliance_msg: Optional[str] = None

    class Config:
        extra = "allow"


class ImpulseData(BaseModel):
    simulation: Optional[ImpulseSimulationData] = Field(default=None)
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "ignore"


# --- Dielectric Analysis Store Model ---
class EnrolamentoParams(BaseModel):
    nome: str
    um: Optional[Union[str, float]] = None  # Guardar como string original ou float
    conexao: Optional[str] = None
    neutro_um: Optional[Union[str, float]] = None
    ia: Optional[Union[str, float]] = None
    ia_neutro: Optional[Union[str, float]] = None
    im: Optional[Union[str, float]] = None
    tensao_curta: Optional[Union[str, float]] = None
    nbi_neutro: Optional[Union[str, float]] = None


class EnrolamentoResults(BaseModel):
    nome: str
    impulso_cortado: Optional[Dict[str, Any]] = Field(default={})
    espacamentos: Optional[Dict[str, Any]] = Field(default={})


class DielectricAnalysisData(BaseModel):
    parametros: Optional[Dict[str, Any]] = Field(
        default={}
    )  # Inclui enrolamentos, tipo_transformador, tipo_isolamento
    resultados: Optional[Dict[str, Any]] = Field(
        default={}
    )  # Inclui enrolamentos, ensaios_requeridos, sequencias_ensaio
    timestamp: Optional[datetime.datetime] = Field(default=None)
    tensao_induzida: Optional[Dict[str, Optional[Union[str, float]]]] = Field(
        default={}
    )  # Adicionado

    class Config:
        extra = "ignore"


# --- Applied Voltage Store Model ---
class AppliedVoltageData(BaseModel):
    inputs: Optional[Dict[str, Any]] = Field(default={})
    resultados: Optional[Dict[str, Any]] = Field(default={})
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "ignore"


# --- Induced Voltage Store Model ---
class InducedVoltageData(BaseModel):
    inputs: Optional[Dict[str, Any]] = Field(default={})
    resultados: Optional[Dict[str, Any]] = Field(default={})
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "ignore"


# --- Short Circuit Store Model ---
class ShortCircuitData(BaseModel):
    inputs_curto_circuito: Optional[Dict[str, Any]] = Field(default={})
    resultados_curto_circuito: Optional[Dict[str, Any]] = Field(default={})
    graph_figure: Optional[Dict[str, Any]] = None  # Store graph definition
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "ignore"


# --- Temperature Rise Store Model ---
class TemperatureRiseData(BaseModel):
    inputs_temp_rise: Optional[Dict[str, Any]] = Field(default={})
    resultados_temp_rise: Optional[Dict[str, Any]] = Field(default={})
    timestamp: Optional[datetime.datetime] = Field(default=None)

    class Config:
        extra = "ignore"


# --- Comprehensive Analysis Store Model ---
class ComprehensiveAnalysisData(BaseModel):
    enrolamentos: Optional[List[Dict[str, Any]]] = Field(default=[])
    tipo_transformador: Optional[str] = None
    tipo_isolamento: Optional[str] = None
    timestamp: Optional[float] = None

    class Config:
        extra = "ignore"


# --- END OF FILE app_core/data_models.py ---
