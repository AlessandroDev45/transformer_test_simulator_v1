"""
Testes para o módulo app_core.transformer_mcp.
"""
import json
import os
import pathlib
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS, TransformerMCP


@pytest.fixture
def mock_disk_persistence():
    """Mock para as funções de persistência em disco."""
    with patch("app_core.transformer_mcp.load_mcp_state_from_disk") as mock_load:
        with patch("app_core.transformer_mcp.save_mcp_state_to_disk") as mock_save:
            with patch("app_core.transformer_mcp.create_mcp_backup") as mock_backup:
                # Configurar mocks
                mock_load.return_value = ({}, True)
                mock_save.return_value = True
                mock_backup.return_value = True
                
                yield {
                    "load": mock_load,
                    "save": mock_save,
                    "backup": mock_backup
                }


@pytest.fixture
def mcp_instance(mock_disk_persistence):
    """Cria uma instância do TransformerMCP para testes."""
    return TransformerMCP(load_from_disk=False)


def test_mcp_initialization(mcp_instance):
    """Testa a inicialização do MCP."""
    # Verificar se o MCP foi inicializado corretamente
    assert mcp_instance is not None
    assert isinstance(mcp_instance._data, dict)
    assert "transformer-inputs-store" in mcp_instance._data
    
    # Verificar se os dados padrão foram carregados
    transformer_data = mcp_instance.get_data("transformer-inputs-store")
    assert transformer_data is not None
    assert isinstance(transformer_data, dict)
    assert transformer_data["tipo_transformador"] == DEFAULT_TRANSFORMER_INPUTS["tipo_transformador"]
    assert transformer_data["frequencia"] == DEFAULT_TRANSFORMER_INPUTS["frequencia"]


def test_mcp_set_get_data(mcp_instance):
    """Testa as operações de set e get de dados no MCP."""
    # Dados de teste
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 50,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "frequencia": 60,
        "impedancia": 12.5
    }
    
    # Definir dados no MCP
    mcp_instance.set_data("transformer-inputs-store", test_data)
    
    # Obter dados do MCP
    retrieved_data = mcp_instance.get_data("transformer-inputs-store")
    
    # Verificar se os dados foram armazenados corretamente
    assert retrieved_data is not None
    assert retrieved_data["potencia_mva"] == test_data["potencia_mva"]
    assert retrieved_data["tensao_at"] == test_data["tensao_at"]
    assert retrieved_data["tensao_bt"] == test_data["tensao_bt"]


def test_mcp_calculate_nominal_currents(mcp_instance):
    """Testa o cálculo de correntes nominais."""
    # Dados de teste
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "tensao_terciario": None,
        "frequencia": 60,
        "conexao_at": "estrela",
        "conexao_bt": "triangulo",
        "conexao_terciario": ""
    }
    
    # Calcular correntes nominais
    currents = mcp_instance.calculate_nominal_currents(test_data)
    
    # Verificar se as correntes foram calculadas corretamente
    assert currents is not None
    assert "corrente_nominal_at" in currents
    assert "corrente_nominal_bt" in currents
    
    # Verificar valores específicos (aproximados)
    assert abs(currents["corrente_nominal_at"] - 125.5) < 1.0  # ~125.5 A para 30 MVA, 138 kV, trifásico
    assert abs(currents["corrente_nominal_bt"] - 1255.1) < 1.0  # ~1255.1 A para 30 MVA, 13.8 kV, trifásico


def test_mcp_clear_data(mcp_instance):
    """Testa a limpeza de dados no MCP."""
    # Dados de teste
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 50,
        "tensao_at": 138,
        "tensao_bt": 13.8
    }
    
    # Definir dados no MCP
    mcp_instance.set_data("transformer-inputs-store", test_data)
    mcp_instance.set_data("losses-store", {"perdas": 100})
    
    # Limpar dados específicos
    mcp_instance.clear_data("losses-store")
    
    # Verificar se apenas os dados específicos foram limpos
    assert mcp_instance.get_data("transformer-inputs-store")["potencia_mva"] == 50
    assert mcp_instance.get_data("losses-store") == {}
    
    # Limpar todos os dados
    mcp_instance.clear_data()
    
    # Verificar se todos os dados foram limpos
    assert mcp_instance.get_data("transformer-inputs-store") == DEFAULT_TRANSFORMER_INPUTS
    assert mcp_instance.get_data("losses-store") == {}


def test_mcp_save_load_disk(mock_disk_persistence):
    """Testa o salvamento e carregamento de dados do disco."""
    # Criar instância do MCP
    mcp = TransformerMCP(load_from_disk=True)
    
    # Verificar se o método de carregamento foi chamado
    mock_disk_persistence["load"].assert_called_once()
    
    # Dados de teste
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 50,
        "tensao_at": 138,
        "tensao_bt": 13.8
    }
    
    # Definir dados no MCP
    mcp.set_data("transformer-inputs-store", test_data)
    
    # Salvar dados no disco
    mcp.save_to_disk(force=True)
    
    # Verificar se o método de salvamento foi chamado
    mock_disk_persistence["save"].assert_called_once()
    
    # Verificar argumentos do método de salvamento
    args, kwargs = mock_disk_persistence["save"].call_args
    assert "transformer-inputs-store" in args[0]
    assert args[0]["transformer-inputs-store"]["potencia_mva"] == 50
