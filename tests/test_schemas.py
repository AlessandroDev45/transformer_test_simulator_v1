"""
Testes para o módulo schemas.
"""
import pytest
from pydantic import ValidationError

from schemas import (
    LiquidoIsolante,
    TipoConexao,
    TipoIsolamento,
    TipoTransformador,
    TransformerInputs,
    validate_transformer_inputs,
)


def test_transformer_inputs_default_values():
    """Testa os valores padrão do esquema TransformerInputs."""
    # Criar modelo com valores padrão
    model = TransformerInputs()

    # Verificar valores padrão
    assert model.tipo_transformador == TipoTransformador.TRIFASICO
    assert model.frequencia == 60.0
    assert model.conexao_at == TipoConexao.ESTRELA
    assert model.conexao_bt == TipoConexao.TRIANGULO
    assert model.conexao_terciario == TipoConexao.VAZIO
    assert model.liquido_isolante == LiquidoIsolante.MINERAL
    assert model.tipo_isolamento == TipoIsolamento.UNIFORME


def test_transformer_inputs_custom_values():
    """Testa a criação do esquema TransformerInputs com valores personalizados."""
    # Dados de teste
    test_data = {
        "tipo_transformador": "Monofásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "frequencia": 50,
        "impedancia_nominal": 12.5,
        "conexao_at": "estrela",
        "conexao_bt": "triangulo",
        "liquido_isolante": "Vegetal",
    }

    # Criar modelo com valores personalizados
    model = TransformerInputs(**test_data)

    # Verificar valores personalizados
    assert model.tipo_transformador == TipoTransformador.MONOFASICO
    assert model.potencia_mva == 30
    assert model.tensao_at == 138
    assert model.tensao_bt == 13.8
    assert model.frequencia == 50
    assert model.impedancia_nominal == 12.5
    assert model.conexao_at == TipoConexao.ESTRELA
    assert model.conexao_bt == TipoConexao.TRIANGULO
    assert model.liquido_isolante == LiquidoIsolante.VEGETAL


def test_transformer_inputs_invalid_values():
    """Testa a validação de valores inválidos no esquema TransformerInputs."""
    # Dados de teste com valores inválidos
    test_data = {
        "tipo_transformador": "Inválido",
        "potencia_mva": -30,
        "tensao_at": "inválido",
        "frequencia": 0,
        "impedancia_nominal": -12.5,
        "conexao_at": "inválido",
    }

    # Verificar se a validação falha
    with pytest.raises(ValidationError):
        TransformerInputs(**test_data)


def test_transformer_inputs_type_conversion():
    """Testa a conversão de tipos no esquema TransformerInputs."""
    # Dados de teste com valores que precisam ser convertidos
    test_data = {
        "potencia_mva": "30",
        "tensao_at": "138",
        "tensao_bt": "13.8",
        "frequencia": "60",
        "impedancia_nominal": "12.5",
    }

    # Criar modelo com valores que precisam ser convertidos
    model = TransformerInputs(**test_data)

    # Verificar se os valores foram convertidos corretamente
    assert isinstance(model.potencia_mva, float)
    assert model.potencia_mva == 30.0
    assert isinstance(model.tensao_at, float)
    assert model.tensao_at == 138.0
    assert isinstance(model.tensao_bt, float)
    assert model.tensao_bt == 13.8
    assert isinstance(model.frequencia, float)
    assert model.frequencia == 60.0
    assert isinstance(model.impedancia_nominal, float)
    assert model.impedancia_nominal == 12.5


def test_validate_transformer_inputs_valid_data():
    """Testa a função validate_transformer_inputs com dados válidos."""
    # Dados de teste válidos
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "frequencia": 60,
        "impedancia_nominal": 12.5,
        "conexao_at": "estrela",
        "conexao_bt": "triangulo",
        "liquido_isolante": "Mineral",
    }

    # Validar dados
    validated_data = validate_transformer_inputs(test_data)

    # Verificar se os dados foram validados corretamente
    assert validated_data is not None
    assert validated_data["tipo_transformador"] == "Trifásico"
    assert validated_data["potencia_mva"] == 30
    assert validated_data["tensao_at"] == 138
    assert validated_data["tensao_bt"] == 13.8
    assert validated_data["frequencia"] == 60
    assert validated_data["impedancia_nominal"] == 12.5
    assert validated_data["conexao_at"] == "estrela"
    assert validated_data["conexao_bt"] == "triangulo"
    assert validated_data["liquido_isolante"] == "Mineral"


def test_validate_transformer_inputs_invalid_data():
    """Testa a função validate_transformer_inputs com dados inválidos."""
    # Dados de teste inválidos
    test_data = {
        "tipo_transformador": "Inválido",
        "potencia_mva": -30,
        "tensao_at": "inválido",
        "frequencia": 0,
        "impedancia_nominal": -12.5,
        "conexao_at": "inválido",
    }

    # Validar dados (deve retornar os dados originais em caso de erro)
    validated_data = validate_transformer_inputs(test_data)

    # Verificar se os dados originais foram retornados
    assert validated_data is test_data
