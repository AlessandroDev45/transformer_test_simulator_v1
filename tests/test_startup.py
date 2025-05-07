"""
Testes para o módulo app_core.startup.
"""
import json
import os
import pathlib
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app_core.startup import load_default_transformer_data, seed_mcp


@pytest.fixture
def mock_json_file():
    """Cria um arquivo JSON temporário para testes."""
    # Dados de teste
    test_data = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "frequencia": 60,
        "impedancia_nominal": 12.5
    }
    
    # Criar diretório temporário
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar diretório defaults
        defaults_dir = os.path.join(temp_dir, "defaults")
        os.makedirs(defaults_dir, exist_ok=True)
        
        # Criar arquivo JSON
        json_path = os.path.join(defaults_dir, "transformer.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
        
        # Patch para o caminho do arquivo
        with patch("pathlib.Path") as mock_path:
            # Configurar mock para retornar o caminho do arquivo temporário
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = json.dumps(test_data)
            
            yield test_data


@pytest.fixture
def mock_mcp():
    """Cria um mock do MCP para testes."""
    mock = MagicMock()
    mock.set_data.return_value = True
    mock.get_data.return_value = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8
    }
    return mock


@pytest.fixture
def mock_app(mock_mcp):
    """Cria um mock da aplicação Dash para testes."""
    mock = MagicMock()
    mock.mcp = mock_mcp
    return mock


def test_load_default_transformer_data(mock_json_file):
    """Testa o carregamento de dados padrão do arquivo JSON."""
    # Carregar dados padrão
    data = load_default_transformer_data()
    
    # Verificar se os dados foram carregados corretamente
    assert data is not None
    assert isinstance(data, dict)
    assert data["tipo_transformador"] == mock_json_file["tipo_transformador"]
    assert data["potencia_mva"] == mock_json_file["potencia_mva"]
    assert data["tensao_at"] == mock_json_file["tensao_at"]
    assert data["tensao_bt"] == mock_json_file["tensao_bt"]
    assert data["frequencia"] == mock_json_file["frequencia"]
    assert data["impedancia_nominal"] == mock_json_file["impedancia_nominal"]


def test_load_default_transformer_data_file_not_found():
    """Testa o comportamento quando o arquivo JSON não é encontrado."""
    # Patch para o caminho do arquivo
    with patch("pathlib.Path") as mock_path:
        # Configurar mock para retornar que o arquivo não existe
        mock_path.return_value.exists.return_value = False
        
        # Carregar dados padrão
        data = load_default_transformer_data()
        
        # Verificar se um dicionário vazio foi retornado
        assert data == {}


def test_seed_mcp_with_mcp_instance(mock_mcp, mock_json_file):
    """Testa a inicialização do MCP com dados padrão usando uma instância do MCP."""
    # Inicializar MCP
    result = seed_mcp(mcp_instance=mock_mcp)
    
    # Verificar se a inicialização foi bem-sucedida
    assert result is True
    
    # Verificar se o método set_data foi chamado
    mock_mcp.set_data.assert_called_once()
    
    # Verificar argumentos do método set_data
    args, kwargs = mock_mcp.set_data.call_args
    assert args[0] == "transformer-inputs-store"
    assert isinstance(args[1], dict)
    assert kwargs["notify"] is False


def test_seed_mcp_with_app_instance(mock_app, mock_json_file):
    """Testa a inicialização do MCP com dados padrão usando uma instância da aplicação."""
    # Inicializar MCP
    result = seed_mcp(app_instance=mock_app)
    
    # Verificar se a inicialização foi bem-sucedida
    assert result is True
    
    # Verificar se o método set_data foi chamado
    mock_app.mcp.set_data.assert_called_once()
    
    # Verificar argumentos do método set_data
    args, kwargs = mock_app.mcp.set_data.call_args
    assert args[0] == "transformer-inputs-store"
    assert isinstance(args[1], dict)
    assert kwargs["notify"] is False


def test_seed_mcp_no_instance():
    """Testa o comportamento quando nenhuma instância é fornecida."""
    # Inicializar MCP sem instância
    result = seed_mcp()
    
    # Verificar se a inicialização falhou
    assert result is False


def test_seed_mcp_load_error(mock_mcp):
    """Testa o comportamento quando ocorre um erro ao carregar dados padrão."""
    # Patch para o carregamento de dados padrão
    with patch("app_core.startup.load_default_transformer_data") as mock_load:
        # Configurar mock para retornar um dicionário vazio
        mock_load.return_value = {}
        
        # Inicializar MCP
        result = seed_mcp(mcp_instance=mock_mcp)
        
        # Verificar se a inicialização falhou
        assert result is False
        
        # Verificar se o método set_data não foi chamado
        mock_mcp.set_data.assert_not_called()
