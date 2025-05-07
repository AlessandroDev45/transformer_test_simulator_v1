"""
Configurações e fixtures para testes com pytest.
"""
import tempfile
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_app():
    """Cria um mock da aplicação Dash para testes."""
    mock = MagicMock()
    mock.mcp = MagicMock()
    mock.mcp.get_data.return_value = {
        "tipo_transformador": "Trifásico",
        "potencia_mva": 30,
        "tensao_at": 138,
        "tensao_bt": 13.8,
        "frequencia": 60,
        "impedancia_nominal": 12.5,
    }
    mock.mcp.set_data.return_value = True
    return mock


@pytest.fixture
def temp_test_dir():
    """Cria um diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
