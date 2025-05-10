"""
Testes para verificar a persistência de dados no MCP durante a navegação entre páginas.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app_core.transformer_mcp import TransformerMCP
from utils.mcp_persistence import ensure_mcp_data_propagation
# from utils.mcp_persistence import ensure_mcp_data_propagation, patch_mcp # Comentado para remover patch_mcp


class TestMCPPersistence(unittest.TestCase):
    """Testes para verificar a persistência de dados no MCP."""

    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar um mock para o app
        self.app = MagicMock()
        self.app.mcp = TransformerMCP()

        # Dados completos para o transformer-inputs-store
        self.complete_data = {
            "tipo_transformador": "Trifásico",
            "frequencia": 60,
            "conexao_at": "estrela",
            "conexao_bt": "triangulo",
            "conexao_terciario": "estrela",
            "liquido_isolante": "Mineral",
            "tipo_isolamento": "uniforme",
            "potencia_mva": 100.0,
            "grupo_ligacao": "YNd1",
            "elevacao_oleo_topo": 65,
            "elevacao_enrol": 55,
            "tensao_at": 230.0,
            "classe_tensao_at": 245,
            "elevacao_enrol_at": 55,
            "impedancia": 12.5,
            "nbi_at": 950,
            "sil_at": 750,
            "tensao_at_tap_maior": 245.0,
            "impedancia_tap_maior": 13.0,
            "tensao_at_tap_menor": 215.0,
            "impedancia_tap_menor": 12.0,
            "teste_tensao_aplicada_at": 460.0,
            "teste_tensao_induzida": 460.0,
            "tensao_bt": 13.8,
            "classe_tensao_bt": 15,
            "elevacao_enrol_bt": 55,
            "nbi_bt": 110,
            "sil_bt": 95,
            "teste_tensao_aplicada_bt": 34.0,
            "tensao_terciario": 13.8,
            "classe_tensao_terciario": 15,
            "elevacao_enrol_terciario": 55,
            "nbi_terciario": 110,
            "sil_terciario": 95,
            "teste_tensao_aplicada_terciario": 34.0,
            "tensao_bucha_neutro_at": 34.5,
            "tensao_bucha_neutro_bt": None,
            "tensao_bucha_neutro_terciario": None,
            "nbi_neutro_at": 170,
            "nbi_neutro_bt": None,
            "nbi_neutro_terciario": None,
            "peso_total": 270,
            "peso_parte_ativa": 80,
            "peso_oleo": 90,
            "peso_tanque_acessorios": 100,
            "corrente_nominal_at": 251.0,
            "corrente_nominal_at_tap_maior": 236.0,
            "corrente_nominal_at_tap_menor": 269.0,
            "corrente_nominal_bt": 4184.0,
            "corrente_nominal_terciario": 4184.0,
        }

        # Dados incompletos para o transformer-inputs-store
        self.incomplete_data = {
            "tipo_transformador": "Trifásico",
            "frequencia": 60,
            "conexao_at": "estrela",
            "conexao_bt": "triangulo",
            "conexao_terciario": "estrela",
            "liquido_isolante": "Mineral",
            "tipo_isolamento": "uniforme",
        }

    # def test_patch_mcp_with_complete_data(self):
    #     """Testar a função patch_mcp com dados completos."""
    #     # Configurar o MCP com dados iniciais
    #     self.app.mcp.set_data("transformer-inputs-store", self.complete_data)

    #     # Verificar se os dados foram salvos corretamente
    #     saved_data = self.app.mcp.get_data("transformer-inputs-store")
    #     self.assertEqual(saved_data["potencia_mva"], 100.0)
    #     self.assertEqual(saved_data["tensao_at"], 230.0)
    #     self.assertEqual(saved_data["tensao_bt"], 13.8)

    #     # Modificar alguns dados
    #     modified_data = self.complete_data.copy()
    #     modified_data["potencia_mva"] = 150.0

    #     # Aplicar o patch
    #     result = patch_mcp(self.app, "transformer-inputs-store", modified_data)

    #     # Verificar se o patch foi aplicado
    #     self.assertTrue(result)

    #     # Verificar se os dados foram atualizados corretamente
    #     updated_data = self.app.mcp.get_data("transformer-inputs-store")
    #     self.assertEqual(updated_data["potencia_mva"], 150.0)
    #     self.assertEqual(updated_data["tensao_at"], 230.0)
    #     self.assertEqual(updated_data["tensao_bt"], 13.8)

    # def test_patch_mcp_with_incomplete_data(self):
    #     """Testar a função patch_mcp com dados incompletos."""
    #     # Configurar o MCP com dados iniciais
    #     self.app.mcp.set_data("transformer-inputs-store", self.complete_data)

    #     # Verificar se os dados foram salvos corretamente
    #     saved_data = self.app.mcp.get_data("transformer-inputs-store")
    #     self.assertEqual(saved_data["potencia_mva"], 100.0)

    #     # Tentar aplicar o patch com dados incompletos
    #     result = patch_mcp(self.app, "transformer-inputs-store", self.incomplete_data)

    #     # Verificar se o patch foi rejeitado
    #     self.assertFalse(result)

    #     # Verificar se os dados originais foram mantidos
    #     unchanged_data = self.app.mcp.get_data("transformer-inputs-store")
    #     self.assertEqual(unchanged_data["potencia_mva"], 100.0)

    def test_ensure_mcp_data_propagation(self):
        """Testar a função ensure_mcp_data_propagation."""
        # Configurar o MCP com dados iniciais
        self.app.mcp.set_data("transformer-inputs-store", self.complete_data)

        # Lista de stores para os quais propagar os dados
        target_stores = [
            "losses-store",
            "impulse-store",
            "dieletric-analysis-store",
            "applied-voltage-store",
            "induced-voltage-store",
            "short-circuit-store",
            "temperature-rise-store",
            "comprehensive-analysis-store",
        ]

        # Propagar dados para todos os stores
        results = ensure_mcp_data_propagation(self.app, "transformer-inputs-store", target_stores)

        # Verificar se todos os stores foram atualizados
        for store, success in results.items():
            self.assertTrue(success)

            # Verificar se os dados foram propagados corretamente
            store_data = self.app.mcp.get_data(store)
            self.assertIsNotNone(store_data)
            self.assertIn("transformer_data", store_data)
            self.assertEqual(store_data["transformer_data"]["potencia_mva"], 100.0)
            self.assertEqual(store_data["transformer_data"]["tensao_at"], 230.0)
            self.assertEqual(store_data["transformer_data"]["tensao_bt"], 13.8)

    def test_global_updates_does_not_overwrite_mcp(self):
        """
        Testar que o callback global_updates não sobrescreve dados válidos no MCP.

        Este teste simula o comportamento do callback global_updates quando ele
        recebe dados vazios do store, mas o MCP já contém dados válidos.
        """
        # Configurar o MCP com dados iniciais
        self.app.mcp.set_data("transformer-inputs-store", self.complete_data)

        # Simular o comportamento do callback global_updates
        with patch("callbacks.global_updates.app") as mock_app:
            mock_app.mcp = self.app.mcp

            # Importar o callback após o mock para usar o mock
            from callbacks.global_updates import update_transformer_calculations_and_mcp

            # Chamar o callback com dados vazios
            result = update_transformer_calculations_and_mcp(None, self.incomplete_data)

            # Verificar se o resultado não é None
            self.assertIsNotNone(result)

            # Verificar se os dados originais foram mantidos no MCP
            unchanged_data = self.app.mcp.get_data("transformer-inputs-store")
            self.assertEqual(unchanged_data["potencia_mva"], 100.0)
            self.assertEqual(unchanged_data["tensao_at"], 230.0)
            self.assertEqual(unchanged_data["tensao_bt"], 13.8)


if __name__ == "__main__":
    unittest.main()
