# callbacks/transformer_inputs_fix.py
"""
Versão corrigida do módulo transformer_inputs que usa o padrão de registro centralizado.
"""
import dash
from dash import Input, Output, State, callback, ctx, no_update, html
import dash_bootstrap_components as dbc
import numpy as np
import logging
from dash.exceptions import PreventUpdate

# Não importar app diretamente para evitar importações circulares
# from app import app  # REMOVIDO

from app_core.standards import TabelaTransformadorNBR
from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS
from utils.store_diagnostics import convert_numpy_types
from utils.routes import normalize_pathname, ROUTE_HOME
from utils.mcp_utils import patch_mcp

log = logging.getLogger(__name__)
log.info("============ MÓDULO TRANSFORMER_INPUTS_FIX CARREGADO ============")
log.info(f"Nível de log: {logging.getLevelName(log.getEffectiveLevel())}")
log.info(f"Handlers configurados: {[h.__class__.__name__ for h in log.handlers]}")
log.info("=============================================================")

def register_transformer_inputs_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de transformer_inputs.
    Esta função é chamada por app.py durante a inicialização.

    Registra os callbacks que foram convertidos para o padrão de registro centralizado.
    """
    log.info(f"Registrando callbacks do módulo transformer_inputs para app {app_instance.title}...")

    # Registrar o callback para calcular todas as correntes
    @app_instance.callback(
        [
            Output("corrente_nominal_at", "value"),
            Output("corrente_nominal_bt", "value"),
            Output("corrente_nominal_terciario", "value"),
            Output("corrente_nominal_at_tap_maior", "value"),
            Output("corrente_nominal_at_tap_menor", "value")
        ],
        [
            # Dados básicos
            Input("potencia_mva", "value"),
            Input("frequencia", "value"),
            Input("grupo_ligacao", "value"),
            Input("liquido_isolante", "value"),
            Input("elevacao_oleo_topo", "value"),
            Input("elevacao_enrol", "value"),
            Input("tipo_transformador", "value"),
            Input("tipo_isolamento", "value"),

            # Pesos
            Input("peso_total", "value"),
            Input("peso_parte_ativa", "value"),
            Input("peso_oleo", "value"),
            Input("peso_tanque_acessorios", "value"),

            # Alta Tensão (AT)
            Input("tensao_at", "value"),
            Input("classe_tensao_at", "value"),
            Input("impedancia", "value"),
            Input("nbi_at", "value"),
            Input("sil_at", "value"),
            Input("conexao_at", "value"),
            Input("tensao_bucha_neutro_at", "value"),
            Input("nbi_neutro_at", "value"),

            # Taps AT
            Input("tensao_at_tap_maior", "value"),
            Input("impedancia_tap_maior", "value"),
            Input("tensao_at_tap_menor", "value"),
            Input("impedancia_tap_menor", "value"),

            # Tensões de ensaio AT
            Input("teste_tensao_aplicada_at", "value"),
            Input("teste_tensao_induzida", "value"),

            # Baixa Tensão (BT)
            Input("tensao_bt", "value"),
            Input("classe_tensao_bt", "value"),
            Input("nbi_bt", "value"),
            Input("sil_bt", "value"),
            Input("conexao_bt", "value"),
            Input("tensao_bucha_neutro_bt", "value"),
            Input("nbi_neutro_bt", "value"),
            Input("teste_tensao_aplicada_bt", "value"),

            # Terciário
            Input("tensao_terciario", "value"),
            Input("classe_tensao_terciario", "value"),
            Input("nbi_terciario", "value"),
            Input("sil_terciario", "value"),
            Input("conexao_terciario", "value"),
            Input("tensao_bucha_neutro_terciario", "value"),
            Input("nbi_neutro_terciario", "value"),
            Input("teste_tensao_aplicada_terciario", "value")
        ],
        prevent_initial_call=False, # Permite rodar na carga inicial para garantir que o MCP seja atualizado
        priority=1000 # Alta prioridade para garantir que este callback seja executado antes de outros
    )
    def update_transformer_calculations_and_mcp(
        # Dados básicos
        potencia_mva, frequencia, grupo_ligacao, liquido_isolante, elevacao_oleo_topo, elevacao_enrol,
        tipo_transformador, tipo_isolamento,

        # Pesos
        peso_total, peso_parte_ativa, peso_oleo, peso_tanque_acessorios,

        # Alta Tensão (AT)
        tensao_at, classe_tensao_at, impedancia, nbi_at, sil_at, conexao_at, tensao_bucha_neutro_at, nbi_neutro_at,

        # Taps AT
        tensao_at_tap_maior, impedancia_tap_maior, tensao_at_tap_menor, impedancia_tap_menor,

        # Tensões de ensaio AT
        teste_tensao_aplicada_at, teste_tensao_induzida,

        # Baixa Tensão (BT)
        tensao_bt, classe_tensao_bt, nbi_bt, sil_bt, conexao_bt, tensao_bucha_neutro_bt, nbi_neutro_bt, teste_tensao_aplicada_bt,

        # Terciário
        tensao_terciario, classe_tensao_terciario, nbi_terciario, sil_terciario, conexao_terciario,
        tensao_bucha_neutro_terciario, nbi_neutro_terciario, teste_tensao_aplicada_terciario
    ):
        """
        Calcula as correntes nominais do transformador e atualiza o MCP.
        """
        # Log resumido para o arquivo de log
        log.info(f"[Update Callback] ACIONADO! Potência: {potencia_mva}, Tensão AT: {tensao_at}, Tensão BT: {tensao_bt}, Tensão Terciário: {tensao_terciario}, Tipo: {tipo_transformador}")

        # Verificar se os valores principais são numéricos
        try:
            if potencia_mva is not None:
                float(potencia_mva)
            if tensao_at is not None:
                float(tensao_at)
            if tensao_bt is not None:
                float(tensao_bt)
            if tensao_terciario is not None:
                float(tensao_terciario)
            if tensao_at_tap_maior is not None:
                float(tensao_at_tap_maior)
            if tensao_at_tap_menor is not None:
                float(tensao_at_tap_menor)
        except ValueError as e:
            log.error(f"[Update Callback] Erro ao converter valor para float: {e}")

        # Valores padrão para retorno
        corrente_at = None
        corrente_bt = None
        corrente_terciario = None
        corrente_at_tap_maior = None
        corrente_at_tap_menor = None

        # Fator para cálculo da corrente (depende do tipo de transformador)
        fator = 1.732  # Padrão para trifásico (raiz de 3)
        if tipo_transformador == "Monofásico":
            fator = 1.0

        # Cálculo das correntes
        try:
            # Cálculo da corrente AT
            if potencia_mva is not None and tensao_at is not None and float(potencia_mva) > 0 and float(tensao_at) > 0:
                potencia = float(potencia_mva)
                tensao = float(tensao_at)
                corrente_at = round((potencia * 1000) / (tensao * fator), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente AT calculada: {corrente_at}A")

            # Cálculo da corrente BT
            if potencia_mva is not None and tensao_bt is not None and float(potencia_mva) > 0 and float(tensao_bt) > 0:
                potencia = float(potencia_mva)
                tensao = float(tensao_bt)
                corrente_bt = round((potencia * 1000) / (tensao * fator), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente BT calculada: {corrente_bt}A")

            # Cálculo da corrente Terciário (se aplicável)
            if potencia_mva is not None and tensao_terciario is not None and float(potencia_mva) > 0 and float(tensao_terciario) > 0:
                # Para o terciário, geralmente usa-se uma fração da potência nominal
                potencia_terciario = float(potencia_mva) * 0.33  # Assumindo 1/3 da potência nominal
                tensao = float(tensao_terciario)
                corrente_terciario = round((potencia_terciario * 1000) / (tensao * fator), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente Terciário calculada: {corrente_terciario}A")

            # Cálculo da corrente AT no tap maior (se aplicável)
            if potencia_mva is not None and tensao_at_tap_maior is not None and float(potencia_mva) > 0 and float(tensao_at_tap_maior) > 0:
                potencia = float(potencia_mva)
                tensao = float(tensao_at_tap_maior)
                corrente_at_tap_maior = round((potencia * 1000) / (tensao * fator), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente AT Tap Maior calculada: {corrente_at_tap_maior}A")

            # Cálculo da corrente AT no tap menor (se aplicável)
            if potencia_mva is not None and tensao_at_tap_menor is not None and float(potencia_mva) > 0 and float(tensao_at_tap_menor) > 0:
                potencia = float(potencia_mva)
                tensao = float(tensao_at_tap_menor)
                corrente_at_tap_menor = round((potencia * 1000) / (tensao * fator), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente AT Tap Menor calculada: {corrente_at_tap_menor}A")

            # Atualizar o MCP com os valores calculados
            if hasattr(app_instance, 'mcp') and app_instance.mcp is not None:
                # Obter os dados atuais do MCP
                current_data = app_instance.mcp.get_data('transformer-inputs-store')
                if current_data:
                    # Atualizar todos os valores do formulário no MCP

                    # Dados básicos
                    current_data['potencia_mva'] = potencia_mva
                    current_data['frequencia'] = frequencia
                    current_data['grupo_ligacao'] = grupo_ligacao
                    current_data['liquido_isolante'] = liquido_isolante
                    current_data['elevacao_oleo_topo'] = elevacao_oleo_topo
                    current_data['elevacao_enrol'] = elevacao_enrol
                    current_data['tipo_transformador'] = tipo_transformador
                    current_data['tipo_isolamento'] = tipo_isolamento

                    # Pesos
                    current_data['peso_total'] = peso_total
                    current_data['peso_parte_ativa'] = peso_parte_ativa
                    current_data['peso_oleo'] = peso_oleo
                    current_data['peso_tanque_acessorios'] = peso_tanque_acessorios

                    # Alta Tensão (AT)
                    current_data['tensao_at'] = tensao_at
                    current_data['classe_tensao_at'] = classe_tensao_at
                    current_data['impedancia'] = impedancia
                    current_data['nbi_at'] = nbi_at
                    current_data['sil_at'] = sil_at
                    current_data['conexao_at'] = conexao_at
                    current_data['tensao_bucha_neutro_at'] = tensao_bucha_neutro_at
                    current_data['nbi_neutro_at'] = nbi_neutro_at

                    # Taps AT
                    current_data['tensao_at_tap_maior'] = tensao_at_tap_maior
                    current_data['impedancia_tap_maior'] = impedancia_tap_maior
                    current_data['tensao_at_tap_menor'] = tensao_at_tap_menor
                    current_data['impedancia_tap_menor'] = impedancia_tap_menor

                    # Tensões de ensaio AT
                    current_data['teste_tensao_aplicada_at'] = teste_tensao_aplicada_at
                    current_data['teste_tensao_induzida'] = teste_tensao_induzida

                    # Baixa Tensão (BT)
                    current_data['tensao_bt'] = tensao_bt
                    current_data['classe_tensao_bt'] = classe_tensao_bt
                    current_data['nbi_bt'] = nbi_bt
                    current_data['sil_bt'] = sil_bt
                    current_data['conexao_bt'] = conexao_bt
                    current_data['tensao_bucha_neutro_bt'] = tensao_bucha_neutro_bt
                    current_data['nbi_neutro_bt'] = nbi_neutro_bt
                    current_data['teste_tensao_aplicada_bt'] = teste_tensao_aplicada_bt

                    # Terciário
                    current_data['tensao_terciario'] = tensao_terciario
                    current_data['classe_tensao_terciario'] = classe_tensao_terciario
                    current_data['nbi_terciario'] = nbi_terciario
                    current_data['sil_terciario'] = sil_terciario
                    current_data['conexao_terciario'] = conexao_terciario
                    current_data['tensao_bucha_neutro_terciario'] = tensao_bucha_neutro_terciario
                    current_data['nbi_neutro_terciario'] = nbi_neutro_terciario
                    current_data['teste_tensao_aplicada_terciario'] = teste_tensao_aplicada_terciario

                    # Atualizar os valores de corrente calculados
                    current_data['corrente_nominal_at'] = corrente_at
                    current_data['corrente_nominal_bt'] = corrente_bt
                    current_data['corrente_nominal_terciario'] = corrente_terciario
                    current_data['corrente_nominal_at_tap_maior'] = corrente_at_tap_maior
                    current_data['corrente_nominal_at_tap_menor'] = corrente_at_tap_menor

                    # Log dos valores principais que serão salvos no MCP (apenas em nível debug)
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug(f"[Update Callback] Valores principais a serem salvos no MCP:")
                        log.debug(f"[Update Callback] Potência: {current_data.get('potencia_mva')}")
                        log.debug(f"[Update Callback] Tensão AT: {current_data.get('tensao_at')}")
                        log.debug(f"[Update Callback] Tensão BT: {current_data.get('tensao_bt')}")
                        log.debug(f"[Update Callback] Corrente AT: {current_data.get('corrente_nominal_at')}")
                        log.debug(f"[Update Callback] Corrente BT: {current_data.get('corrente_nominal_bt')}")
                        log.debug(f"[Update Callback] Impedância: {current_data.get('impedancia')}")

                    # Serializar e salvar no MCP usando patch_mcp
                    serializable_data = convert_numpy_types(current_data, debug_path="update_transformer_inputs_with_currents")

                    # Verificar se os dados principais estão presentes antes de salvar
                    log.debug(f"[Update Callback] Verificando dados antes de salvar no MCP: potencia_mva={serializable_data.get('potencia_mva')}, tensao_at={serializable_data.get('tensao_at')}")

                    # Usar patch_mcp para atualizar o MCP com os dados não vazios
                    # Isso evita que valores None sobrescrevam dados válidos
                    if patch_mcp('transformer-inputs-store', serializable_data, app_instance):
                        log.info("[Update Callback] MCP atualizado com valores não vazios do formulário")
                    else:
                        log.warning("[Update Callback] Nenhum dado válido para atualizar no MCP")

                    # Verificar se os dados foram salvos corretamente
                    saved_data = app_instance.mcp.get_data('transformer-inputs-store')
                    log.info(f"[Update Callback] Verificação após salvar no MCP: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}")

                    # Propagar dados para outros stores usando o novo utilitário
                    try:
                        # Obter os dados mais recentes do MCP para garantir consistência
                        latest_data = app_instance.mcp.get_data('transformer-inputs-store')

                        # Verificar se temos dados válidos para propagar
                        if not latest_data or not any(latest_data.get(key) is not None for key in
                                                    ['potencia_mva', 'tensao_at', 'tensao_bt']):
                            log.warning("[Update Callback] Dados insuficientes para propagação. Abortando.")
                            return corrente_at, corrente_bt, corrente_terciario, corrente_at_tap_maior, corrente_at_tap_menor

                        log.info(f"[Update Callback] Dados para propagação: {latest_data}")

                        # Importar o utilitário de persistência do MCP
                        from utils.mcp_persistence import ensure_mcp_data_propagation

                        # Lista de stores para os quais propagar os dados
                        target_stores = [
                            'losses-store',
                            'impulse-store',
                            'dieletric-analysis-store',
                            'applied-voltage-store',
                            'induced-voltage-store',
                            'short-circuit-store',
                            'temperature-rise-store',
                            'comprehensive-analysis-store'
                        ]

                        # Propagar dados para todos os stores
                        propagation_results = ensure_mcp_data_propagation(app_instance, 'transformer-inputs-store', target_stores)

                        # Registrar resultados
                        for store, success in propagation_results.items():
                            if success:
                                log.info(f"[Update Callback] Dados propagados para {store}")
                            else:
                                log.debug(f"[Update Callback] Não foi necessário propagar dados para {store}")
                    except Exception as e:
                        log.error(f"[Update Callback] Erro ao propagar dados para outros stores: {e}", exc_info=True)

                    # Verificar se os valores principais foram salvos corretamente (apenas em nível debug)
                    if log.isEnabledFor(logging.DEBUG):
                        saved_data = app_instance.mcp.get_data('transformer-inputs-store')
                        log.debug(f"[Update Callback] Verificação final - Potência: {saved_data.get('potencia_mva')}, Tensão AT: {saved_data.get('tensao_at')}, Tensão BT: {saved_data.get('tensao_bt')}")
                        log.debug(f"[Update Callback] Total de campos no MCP: {len(saved_data)}")

        except Exception as e:
            log.error(f"[Update Callback] Erro: {e}")

        return corrente_at, corrente_bt, corrente_terciario, corrente_at_tap_maior, corrente_at_tap_menor

    # Os callbacks para forçar atualização do MCP e limpar cache local foram removidos

    log.info(f"Todos os callbacks do módulo transformer_inputs registrados com sucesso para app {app_instance.title}.")
    return True
