"""
Esquemas de validação para dados da aplicação.
Utiliza Pydantic para validação e conversão de tipos.
"""
import logging
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator

log = logging.getLogger(__name__)


class TipoTransformador(str, Enum):
    """Tipos de transformador suportados."""

    MONOFASICO = "Monofásico"
    TRIFASICO = "Trifásico"


class TipoConexao(str, Enum):
    """Tipos de conexão suportados."""

    ESTRELA = "estrela"
    TRIANGULO = "triangulo"
    ZIG_ZAG = "zig-zag"
    VAZIO = ""


class TipoIsolamento(str, Enum):
    """Tipos de isolamento suportados."""

    UNIFORME = "uniforme"
    NAO_UNIFORME = "não-uniforme"


class LiquidoIsolante(str, Enum):
    """Tipos de líquido isolante suportados."""

    MINERAL = "Mineral"
    VEGETAL = "Vegetal"
    SILICONE = "Silicone"
    SECO = "Seco"


class TransformerInputs(BaseModel):
    """Esquema para validação dos dados de entrada do transformador."""

    # Campos obrigatórios
    tipo_transformador: TipoTransformador = Field(default=TipoTransformador.TRIFASICO)
    frequencia: float = Field(default=60.0)

    # Conexões
    conexao_at: TipoConexao = Field(default=TipoConexao.ESTRELA)
    conexao_bt: TipoConexao = Field(default=TipoConexao.TRIANGULO)
    conexao_terciario: TipoConexao = Field(default=TipoConexao.VAZIO)

    # Isolamento
    liquido_isolante: LiquidoIsolante = Field(default=LiquidoIsolante.MINERAL)
    tipo_isolamento: TipoIsolamento = Field(default=TipoIsolamento.UNIFORME)

    # Dados básicos do transformador
    potencia_mva: Optional[float] = None
    grupo_ligacao: Optional[str] = None

    # Tensões
    tensao_at: Optional[float] = None
    tensao_bt: Optional[float] = None
    tensao_terciario: Optional[float] = None

    # Classes de tensão
    classe_tensao_at: Optional[float] = None
    classe_tensao_bt: Optional[float] = None
    classe_tensao_terciario: Optional[float] = None

    # Impedâncias
    impedancia_nominal: Optional[float] = None
    impedancia_tap_maior: Optional[float] = None
    impedancia_tap_menor: Optional[float] = None

    # Taps
    tensao_at_tap_maior: Optional[float] = None
    tensao_at_tap_menor: Optional[float] = None

    # Correntes nominais (calculadas)
    corrente_nominal_at: Optional[float] = None
    corrente_nominal_bt: Optional[float] = None
    corrente_nominal_terciario: Optional[float] = None
    corrente_nominal_at_tap_maior: Optional[float] = None
    corrente_nominal_at_tap_menor: Optional[float] = None

    # Níveis de isolamento
    nbi_at: Optional[float] = None
    nbi_bt: Optional[float] = None
    nbi_terciario: Optional[float] = None
    nbi_neutro_at: Optional[float] = None
    nbi_neutro_bt: Optional[float] = None
    nbi_neutro_terciario: Optional[float] = None

    # Níveis de impulso de manobra
    sil_at: Optional[float] = None
    sil_bt: Optional[float] = None
    sil_terciario: Optional[float] = None
    sil_neutro_at: Optional[float] = None
    sil_neutro_bt: Optional[float] = None
    sil_neutro_terciario: Optional[float] = None

    # Testes de tensão
    teste_tensao_aplicada_at: Optional[float] = None
    teste_tensao_aplicada_bt: Optional[float] = None
    teste_tensao_aplicada_terciario: Optional[float] = None
    teste_tensao_induzida: Optional[float] = None

    # Elevações de temperatura
    elevacao_oleo_topo: Optional[float] = None
    elevacao_enrol: Optional[float] = None
    elevacao_enrol_at: Optional[float] = None
    elevacao_enrol_bt: Optional[float] = None
    elevacao_enrol_terciario: Optional[float] = None

    class Config:
        """Configuração do modelo Pydantic."""

        extra = "allow"  # Permite campos adicionais
        validate_assignment = True  # Valida atribuições após a criação do objeto
        arbitrary_types_allowed = True  # Permite tipos arbitrários

    @validator("potencia_mva", "tensao_at", "tensao_bt", pre=True)
    def validate_positive_float(cls, v):
        """Valida que o valor é um float positivo."""
        if v is None:
            return None
        try:
            float_val = float(v)
            if float_val <= 0:
                raise ValueError("O valor deve ser positivo")
            return float_val
        except (ValueError, TypeError) as err:
            raise ValueError(f"Não foi possível converter '{v}' para float") from err

    @validator("impedancia_nominal", "impedancia_tap_maior", "impedancia_tap_menor", pre=True)
    def validate_impedance(cls, v):
        """Valida que a impedância é um float positivo."""
        if v is None:
            return None
        try:
            float_val = float(v)
            if float_val <= 0:
                raise ValueError("A impedância deve ser positiva")
            return float_val
        except (ValueError, TypeError):
            raise ValueError(f"Não foi possível converter '{v}' para float")


def validate_transformer_inputs(data: Dict) -> Dict:
    """
    Valida os dados de entrada do transformador usando o esquema Pydantic.

    Args:
        data: Dicionário com os dados de entrada

    Returns:
        Dict: Dados validados e convertidos
    """
    try:
        # Criar modelo a partir dos dados
        model = TransformerInputs(**data)

        # Converter modelo para dicionário
        validated_data = model.dict(exclude_none=False)

        log.info(f"Dados do transformador validados: {len(validated_data)} campos")
        return validated_data
    except Exception as e:
        log.error(f"Erro ao validar dados do transformador: {e}", exc_info=True)
        # Retornar dados originais em caso de erro
        return data
