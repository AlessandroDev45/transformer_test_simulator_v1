# -*- coding: utf-8 -*-
"""
Módulo de callbacks para a seção de Tensão Induzida.
Utiliza o padrão de registro centralizado de callbacks para evitar problemas com o reloader.
"""
import datetime
import logging

# Usado para cálculos matemáticos como potência
import math

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate
from plotly import graph_objects as go

# Importações da aplicação
from components.formatters import format_parameter_value

# Configurar logger
log = logging.getLogger(__name__)


# --- Funções Auxiliares ---
def safe_float(value, default=None):
    """Converte valor para float de forma segura, retorna default em caso de erro."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# Tabelas de potência magnética e perdas do núcleo
potencia_magnet = {
    (0.5, 50): 0.10,
    (0.5, 60): 0.15,
    (0.5, 100): 0.35,
    (0.5, 120): 0.45,
    (0.5, 150): 0.70,
    (0.5, 200): 1.00,
    (0.5, 240): 1.30,
    (0.6, 50): 0.15,
    (0.6, 60): 0.20,
    (0.6, 100): 0.45,
    (0.6, 120): 0.60,
    (0.6, 150): 0.90,
    (0.6, 200): 1.40,
    (0.6, 240): 1.80,
    (0.7, 50): 0.23,
    (0.7, 60): 0.28,
    (0.7, 100): 0.60,
    (0.7, 120): 0.80,
    (0.7, 150): 1.10,
    (0.7, 200): 1.70,
    (0.7, 240): 2.30,
    (0.8, 50): 0.30,
    (0.8, 60): 0.35,
    (0.8, 100): 0.80,
    (0.8, 120): 1.00,
    (0.8, 150): 1.40,
    (0.8, 200): 2.20,
    (0.8, 240): 3.00,
    (0.9, 50): 0.38,
    (0.9, 60): 0.45,
    (0.9, 100): 0.95,
    (0.9, 120): 1.30,
    (0.9, 150): 1.70,
    (0.9, 200): 2.80,
    (0.9, 240): 3.80,
    (1.0, 50): 0.45,
    (1.0, 60): 0.55,
    (1.0, 100): 1.10,
    (1.0, 120): 1.60,
    (1.0, 150): 2.20,
    (1.0, 200): 3.50,
    (1.0, 240): 4.50,
    (1.1, 50): 0.55,
    (1.1, 60): 0.70,
    (1.1, 100): 1.50,
    (1.1, 120): 2.00,
    (1.1, 150): 2.80,
    (1.1, 200): 4.10,
    (1.1, 240): 5.50,
    (1.2, 50): 0.65,
    (1.2, 60): 0.85,
    (1.2, 100): 2.00,
    (1.2, 120): 2.40,
    (1.2, 150): 3.30,
    (1.2, 200): 5.00,
    (1.2, 240): 6.50,
    (1.3, 50): 0.80,
    (1.3, 60): 1.00,
    (1.3, 100): 2.20,
    (1.3, 120): 2.85,
    (1.3, 150): 3.80,
    (1.3, 200): 6.00,
    (1.3, 240): 7.50,
    (1.4, 50): 0.95,
    (1.4, 60): 1.20,
    (1.4, 100): 2.50,
    (1.4, 120): 3.30,
    (1.4, 150): 4.50,
    (1.4, 200): 7.00,
    (1.4, 240): 9.00,  # <-- Relevant for Mag interpolation
    (1.5, 50): 1.10,
    (1.5, 60): 1.40,
    (1.5, 100): 3.00,
    (1.5, 120): 4.00,
    (1.5, 150): 5.50,
    (1.5, 200): 9.00,
    (1.5, 240): 11.00,  # <-- Relevant for Mag interpolation
    (1.6, 50): 1.30,
    (1.6, 60): 1.60,
    (1.6, 100): 3.50,
    (1.6, 120): 4.80,
    (1.6, 150): 6.50,
    (1.6, 200): 12.00,
    (1.6, 240): 14.00,
    (1.7, 50): 1.60,
    (1.7, 60): 2.00,
    (1.7, 100): 4.00,
    (1.7, 120): 5.50,
    (1.7, 150): 7.00,
    (1.7, 200): 15.00,
    (1.7, 240): 17.00,
}

perdas_nucleo = {
    (0.5, 50): 0.10,
    (0.5, 60): 0.13,
    (0.5, 100): 0.25,
    (0.5, 120): 0.35,
    (0.5, 150): 0.50,
    (0.5, 200): 0.80,
    (0.5, 240): 1.10,
    (0.6, 50): 0.12,
    (0.6, 60): 0.18,
    (0.6, 100): 0.38,
    (0.6, 120): 0.48,
    (0.6, 150): 0.70,
    (0.6, 200): 1.10,
    (0.6, 240): 1.50,
    (0.7, 50): 0.15,
    (0.7, 60): 0.23,
    (0.7, 100): 0.50,
    (0.7, 120): 0.62,
    (0.7, 150): 0.95,
    (0.7, 200): 1.55,
    (0.7, 240): 2.10,
    (0.8, 50): 0.20,
    (0.8, 60): 0.30,
    (0.8, 100): 0.65,
    (0.8, 120): 0.80,
    (0.8, 150): 1.20,
    (0.8, 200): 2.00,
    (0.8, 240): 2.80,
    (0.9, 50): 0.25,
    (0.9, 60): 0.37,
    (0.9, 100): 0.82,
    (0.9, 120): 1.00,
    (0.9, 150): 1.50,
    (0.9, 200): 2.50,
    (0.9, 240): 3.50,
    (1.0, 50): 0.32,
    (1.0, 60): 0.46,
    (1.0, 100): 1.00,
    (1.0, 120): 1.25,
    (1.0, 150): 1.85,
    (1.0, 200): 3.10,
    (1.0, 240): 4.20,
    (1.1, 50): 0.41,
    (1.1, 60): 0.55,
    (1.1, 100): 1.21,
    (1.1, 120): 1.55,
    (1.1, 150): 2.20,
    (1.1, 200): 3.70,
    (1.1, 240): 5.00,
    (1.2, 50): 0.50,
    (1.2, 60): 0.65,
    (1.2, 100): 1.41,
    (1.2, 120): 1.90,
    (1.2, 150): 2.70,
    (1.2, 200): 4.50,
    (1.2, 240): 6.00,
    (1.3, 50): 0.60,
    (1.3, 60): 0.80,
    (1.3, 100): 1.65,
    (1.3, 120): 2.30,
    (1.3, 150): 3.20,
    (1.3, 200): 5.20,
    (1.3, 240): 7.00,
    (1.4, 50): 0.71,
    (1.4, 60): 0.95,
    (1.4, 100): 1.95,
    (1.4, 120): 2.80,
    (1.4, 150): 3.80,
    (1.4, 200): 6.00,
    (1.4, 240): 8.50,  # <-- Relevant for Perdas interpolation
    (1.5, 50): 0.85,
    (1.5, 60): 1.10,
    (1.5, 100): 2.30,
    (1.5, 120): 3.30,
    (1.5, 150): 4.50,
    (1.5, 200): 7.00,
    (1.5, 240): 10.00,  # <-- Relevant for Perdas interpolation
    (1.6, 50): 1.00,
    (1.6, 60): 1.30,
    (1.6, 100): 2.80,
    (1.6, 120): 3.80,
    (1.6, 150): 5.30,
    (1.6, 200): 8.00,
    (1.6, 240): 12.00,
    (1.7, 50): 1.20,
    (1.7, 60): 1.55,
    (1.7, 100): 3.50,
    (1.7, 120): 4.40,
    (1.7, 150): 6.00,
    (1.7, 200): 9.00,
    (1.7, 240): 15.00,
}

# Converter as tabelas para DataFrames para facilitar a interpolação
df_potencia_magnet = pd.DataFrame(list(potencia_magnet.items()), columns=["key", "potencia_magnet"])
df_potencia_magnet[["inducao_nominal", "frequencia_nominal"]] = pd.DataFrame(
    df_potencia_magnet["key"].tolist(), index=df_potencia_magnet.index
)
df_potencia_magnet.drop("key", axis=1, inplace=True)
df_potencia_magnet.set_index(["inducao_nominal", "frequencia_nominal"], inplace=True)

df_perdas_nucleo = pd.DataFrame(list(perdas_nucleo.items()), columns=["key", "perdas_nucleo"])
df_perdas_nucleo[["inducao_nominal", "frequencia_nominal"]] = pd.DataFrame(
    df_perdas_nucleo["key"].tolist(), index=df_perdas_nucleo.index
)
df_perdas_nucleo.drop("key", axis=1, inplace=True)
df_perdas_nucleo.set_index(["inducao_nominal", "frequencia_nominal"], inplace=True)


def register_induced_voltage_callbacks(app_instance):
    """
    Registra todos os callbacks para a seção de Tensão Induzida.

    Esta função deve ser chamada após a definição do layout da aplicação,
    passando a instância do app como parâmetro.
    """
    log.debug("Registrando callbacks de Tensão Induzida")

    @app_instance.callback(
        [
            Output("tipo-transformador", "value"),
            Output("frequencia-teste", "value"),
            Output("capacitancia", "value"),
            # Adicionar outros outputs de input da UI aqui se necessário
        ],
        [
            Input("url", "pathname"),
            Input("transformer-inputs-store", "data"),
            Input("induced-voltage-store", "data")
        ],
        prevent_initial_call=False
    )
    def load_induced_voltage_inputs(pathname, transformer_data_global, induced_data_local):
        from dash import ctx
        from utils.routes import ROUTE_INDUCED_VOLTAGE, normalize_pathname # Movido para dentro para evitar import circular no topo

        triggered_id = ctx.triggered_id
        log.debug(f"[LOAD InducedInputs] Acionado por: {triggered_id}, Pathname: {pathname}")

        clean_path = normalize_pathname(pathname) if pathname else ""
        if clean_path != ROUTE_INDUCED_VOLTAGE and triggered_id == 'url':
            log.debug(f"[LOAD InducedInputs] Não na página de Tensão Induzida ({clean_path}). Abortando trigger de URL.")
            raise PreventUpdate

        # Valores padrão ou do store local
        tipo_trafo_local = None
        freq_teste_local = None
        cap_local = None

        if induced_data_local and isinstance(induced_data_local, dict):
            # Verificar se os dados estão em 'inputs'
            inputs_local = induced_data_local.get('inputs', {}) # Assumindo que os inputs estão em 'inputs'
            if isinstance(inputs_local, dict):
                tipo_trafo_local = inputs_local.get('tipo_transformador')
                freq_teste_local = inputs_local.get('freq_teste') # Nome da chave como no store
                cap_local = inputs_local.get('capacitancia')    # Nome da chave como no store
                log.debug(f"[LOAD InducedInputs] Valores encontrados em 'inputs': tipo_trafo={tipo_trafo_local}, freq_teste={freq_teste_local}, cap={cap_local}")

            # Verificar se os dados estão diretamente no dicionário principal
            if tipo_trafo_local is None and "tipo_transformador" in induced_data_local:
                tipo_trafo_local = induced_data_local.get("tipo_transformador")
                log.debug(f"[LOAD InducedInputs] Valor encontrado diretamente no dicionário principal: tipo_trafo={tipo_trafo_local}")

            if freq_teste_local is None and "freq_teste" in induced_data_local:
                freq_teste_local = induced_data_local.get("freq_teste")
                log.debug(f"[LOAD InducedInputs] Valor encontrado diretamente no dicionário principal: freq_teste={freq_teste_local}")

            if cap_local is None and "capacitancia" in induced_data_local:
                cap_local = induced_data_local.get("capacitancia")
                log.debug(f"[LOAD InducedInputs] Valor encontrado diretamente no dicionário principal: cap={cap_local}")

        # Obter tipo de transformador do store global
        tipo_trafo_global = None
        if transformer_data_global and isinstance(transformer_data_global, dict):
            tipo_trafo_global = transformer_data_global.get('tipo_transformador')

        # Decidir qual valor usar para tipo_transformador
        # Prioriza valor local se existir, senão global, senão padrão
        final_tipo_trafo = tipo_trafo_local if tipo_trafo_local else tipo_trafo_global if tipo_trafo_global else "Monofásico" # Padrão

        # Para frequência de teste e capacitância, priorizar valor local, senão None (ou um padrão se definido)
        final_freq_teste = freq_teste_local # Pode ser None se não estiver no store local
        final_cap = cap_local             # Pode ser None se não estiver no store local

        log.debug(f"[LOAD InducedInputs] Valores para UI: TipoTrafo={final_tipo_trafo}, FreqTeste={final_freq_teste}, Cap={final_cap}")

        # Se o trigger foi a mudança de URL e estamos na página correta, ou se foi a mudança de um dos stores, atualiza.
        # Se o trigger foi a mudança de URL para OUTRA página, o PreventUpdate acima já tratou.
        if (triggered_id == 'url' and clean_path == ROUTE_INDUCED_VOLTAGE) or \
           triggered_id == 'transformer-inputs-store' or \
           triggered_id == 'induced-voltage-store':
            return final_tipo_trafo, final_freq_teste, final_cap

        raise PreventUpdate


    # --- Callback para exibir informações do transformador na página ---
    # Este callback copia o conteúdo do painel global para o painel específico da página
    @app_instance.callback(
        Output("transformer-info-induced-page", "children"),
        Input("transformer-info-induced", "children"),
        prevent_initial_call=False,
    )
    def update_induced_page_info_panel(global_panel_content):
        """Copia o conteúdo do painel global para o painel específico da página."""
        return global_panel_content

    # --- Callback principal para cálculo de tensão induzida ---
    @app_instance.callback(
        [
            Output("resultado-tensao-induzida", "children"),
            Output("induced-voltage-store", "data"),
            Output("induced-voltage-error-message", "children"),
        ],
        Input("calc-induced-voltage-btn", "n_clicks"),
        [
            State("transformer-inputs-store", "data"),
            State("losses-store", "data"),
            State("induced-voltage-store", "data"),
            State("url", "pathname"),
            State("frequencia-teste", "value"),
            State("capacitancia", "value"),
            State("tipo-transformador", "value"),
        ],
        prevent_initial_call=True,
    )
    def calculate_induced_voltage(
        n_clicks,
        transformer_data,
        losses_data,
        current_store_data,
        pathname,
        freq_teste_input,
        capacitancia_input,
        tipo_transformador_input,
    ):
        """Calcula a tensão induzida com base nos dados do transformador e perdas."""
        log.debug(
            f"[Induced Voltage] Callback calculate_induced_voltage: n_clicks={n_clicks}, pathname={pathname}"
        )

        # Obter todos os estados para debug (will only show explicitly listed states)
        # from dash import callback_context
        # ctx = callback_context
        # states = ctx.states if ctx else {}
        # log.debug(f"[Induced Voltage] ESTADOS PASSADOS NO INÍCIO DO CALLBACK: {states}")

        # Verificar se estamos na página de tensão induzida
        from utils.routes import ROUTE_INDUCED_VOLTAGE, normalize_pathname

        # Normaliza o pathname para remover barras extras
        clean_path = normalize_pathname(pathname) if pathname else ""

        # Verifica se estamos na página de tensão induzida
        if clean_path != ROUTE_INDUCED_VOLTAGE:
            log.debug(
                f"[Induced Voltage] Não estamos na página de tensão induzida (pathname={pathname}, clean_path={clean_path}), prevenindo atualização"
            )
            raise PreventUpdate

        # Se não foi um clique no botão, não faz nada
        if n_clicks is None or n_clicks == 0:
            return no_update, no_update, no_update

        # Validar dados de entrada
        if not transformer_data:
            error_msg = html.Div(
                "Erro: Dados do transformador não disponíveis. Preencha a seção de dados básicos do transformador.",
                className="alert alert-danger",
            )
            return no_update, no_update, error_msg

        # Verificar se os dados de perdas estão disponíveis e contém as informações necessárias
        if not losses_data or "resultados_perdas_vazio" not in losses_data:
            error_msg = html.Div(
                "Erro: Dados de perdas em vazio não disponíveis. Por favor, complete a seção de perdas em vazio antes de prosseguir.",
                className="alert alert-danger",
            )
            return no_update, no_update, error_msg

        try:
            # Verificar se os dados do transformador estão aninhados em transformer_data
            if "transformer_data" in transformer_data and isinstance(transformer_data["transformer_data"], dict):
                # Usar os dados aninhados
                transformer_dict = transformer_data["transformer_data"]
                log.debug(f"[Induced Voltage] Usando dados aninhados em transformer_data")
            else:
                # Usar os dados diretamente
                transformer_dict = transformer_data
                log.debug(f"[Induced Voltage] Usando dados diretamente do dicionário principal")

            # --- Obtenção de Dados de Entrada ---
            # Prioritize data from stores, use inputs/states as potential overrides if applicable

            # Frequência nominal (fn)
            freq_nominal = safe_float(transformer_dict.get("frequencia"), 60)  # Default 60 Hz

            # Frequência de teste (fp) - Directly from input parameter
            log.debug(
                f"[Induced Voltage] VALOR OBTIDO DO PARÂMETRO freq_teste_input: {freq_teste_input}, tipo: {type(freq_teste_input)}"
            )
            try:
                if freq_teste_input is not None:
                    if isinstance(freq_teste_input, str):
                        freq_teste_input = freq_teste_input.replace(",", ".")
                    freq_teste = float(freq_teste_input)
                else:
                    freq_teste = None
            except (ValueError, TypeError):
                freq_teste = None
            log.debug(f"[Induced Voltage] Frequência de teste após conversão: {freq_teste}")
            if freq_teste is None or freq_teste <= 0:
                raise ValueError(
                    "A frequência de teste não foi fornecida ou é inválida. Preencha o campo 'Teste (fp)'."
                )

            # Tensão AT (Un_AT)
            tensao_at = safe_float(transformer_data.get("tensao_at", 0), 0)

            # Tensão BT (Un_BT)
            tensao_bt = safe_float(transformer_data.get("tensao_bt", 0), 0)

            # Tensão de ensaio (Up) - from transformer_data
            tensao_prova = safe_float(transformer_data.get("teste_tensao_induzida_at"), None) # Modificado para _at
            log.debug(
                f"[Induced Voltage] Tensão de ensaio obtida de transformer-inputs-store.teste_tensao_induzida_at: {tensao_prova}" # Log modificado
            )
            if tensao_prova is None or tensao_prova <= 0:
                raise ValueError(
                    "A tensão de ensaio (Up) não foi encontrada nos dados do transformador ('teste_tensao_induzida_at'). Verifique os dados básicos." # Mensagem modificada
                )
            log.debug(f"[Induced Voltage] Tensão de ensaio (Up): {tensao_prova} kV")

            # Capacitância AT-GND (C) - Directly from input parameter
            log.debug(
                f"[Induced Voltage] Valor bruto da capacitância: {capacitancia_input}, tipo: {type(capacitancia_input)}"
            )
            try:
                if capacitancia_input is not None:
                    if isinstance(capacitancia_input, str):
                        capacitancia_input = capacitancia_input.replace(",", ".")
                    capacitancia = float(capacitancia_input)
                else:
                    capacitancia = None
            except (ValueError, TypeError):
                capacitancia = None
            log.debug(f"[Induced Voltage] Capacitância após conversão: {capacitancia}")
            if capacitancia is None or capacitancia <= 0:
                raise ValueError(
                    "A capacitância AT-GND não foi fornecida ou é inválida. Preencha o campo 'Cap. AT-GND (pF)'."
                )
            log.debug(f"[Induced Voltage] Capacitância AT-GND: {capacitancia} pF")

            # Os dados de perdas já foram verificados no início do callback

            # Indução nominal (Bn) - obrigatoriamente do losses_data
            inducao_from_losses = safe_float(
                losses_data["resultados_perdas_vazio"].get("inducao"), None
            )
            if inducao_from_losses is None or inducao_from_losses <= 0:
                raise ValueError(
                    "Indução nominal não encontrada nos dados de perdas em vazio. Por favor, complete a seção de perdas em vazio."
                )
            inducao_nominal = inducao_from_losses
            log.debug(
                f"[Induced Voltage] Indução nominal obtida do losses-store: {inducao_nominal} T"
            )

            # Peso do núcleo (m_core) - obrigatoriamente do losses_data
            peso_nucleo = safe_float(
                losses_data["resultados_perdas_vazio"].get("peso_nucleo"), None
            )
            if peso_nucleo is None or peso_nucleo <= 0:
                raise ValueError(
                    "Peso do núcleo não encontrado nos dados de perdas em vazio. Por favor, complete a seção de perdas em vazio."
                )
            log.debug(f"[Induced Voltage] Peso do núcleo obtido do losses-store: {peso_nucleo} Ton")
            peso_nucleo_kg = peso_nucleo * 1000  # Convert to kg for factor calculations

            # Perdas em vazio (P0) - obrigatoriamente do losses_data
            perdas_vazio = safe_float(
                losses_data["resultados_perdas_vazio"].get("perdas_vazio_kw"), None
            )
            if perdas_vazio is None or perdas_vazio <= 0:
                raise ValueError(
                    "Perdas em vazio não encontradas nos dados de perdas em vazio. Por favor, complete a seção de perdas em vazio."
                )
            log.debug(
                f"[Induced Voltage] Perdas em vazio obtidas do losses-store: {perdas_vazio} kW"
            )

            # Tipo do transformador - Directly from input parameter or transformer_data
            tipo_transformador = (
                tipo_transformador_input
                if tipo_transformador_input
                else transformer_data.get("tipo_transformador", "Trifásico")
            )
            log.debug(f"[Induced Voltage] Tipo de transformador: {tipo_transformador}")

            # --- Cálculos Intermediários ---

            # Tensão induzida = Tensão de Ensaio (Up)
            tensao_induzida = tensao_prova
            log.debug(
                f"[Induced Voltage] Tensão induzida: {tensao_induzida} kV (igual à tensão de ensaio)"
            )

            # Indução no núcleo na frequência de teste (Beta_teste)
            # B_teste = B_nominal * (U_teste / U_nominal_AT) * (f_nominal / f_teste)
            # Ensure all components are valid before calculation
            if not all([tensao_at, freq_teste, freq_nominal, tensao_induzida, inducao_nominal]):
                raise ValueError(
                    "Valores inválidos ou ausentes para cálculo da indução de teste (tensão AT, frequências, tensão de ensaio, indução nominal)."
                )
            if tensao_at <= 0 or freq_teste <= 0 or freq_nominal <= 0:
                raise ValueError(
                    "Tensão AT, frequência de teste ou frequência nominal devem ser positivas."
                )

            inducao_teste = (
                inducao_nominal * (tensao_induzida / tensao_at) * (freq_nominal / freq_teste)
            )
            log.debug(
                f"[Induced Voltage] Indução no teste (β) calculada: {inducao_teste:.4f} T (Bn={inducao_nominal}, Up={tensao_induzida}, Un_AT={tensao_at}, fn={freq_nominal}, fp={freq_teste})"
            )

            # Garantir que a indução de teste não seja maior que 1.9T (limite físico típico)
            if inducao_teste > 1.9:
                inducao_teste = 1.9
                log.warning("[Induced Voltage] Indução no teste limitada a 1.9T")
            elif inducao_teste <= 0:
                # Handle cases where calculation might lead to non-positive induction
                raise ValueError(
                    f"Cálculo da indução de teste resultou em valor não positivo ({inducao_teste:.4f} T). Verifique os parâmetros de entrada."
                )

            beta_teste = inducao_teste  # Alias for clarity

            # Relação entre frequência de teste e frequência nominal
            fp_fn = freq_teste / freq_nominal

            # Relação entre tensão de prova e tensão nominal (Up/Un)
            # Definition of 'Un' depends on the transformer type for phase vs line voltage
            if tipo_transformador == "Monofásico":
                un_ref = tensao_at  # Use nominal AT voltage directly
                up_un = tensao_prova / un_ref if un_ref else 0
                log.debug(
                    f"[Induced Voltage] Up/Un (Monofásico): {up_un:.4f} (Up={tensao_prova}, Un_ref=Un_AT={un_ref})"
                )
            else:  # Trifásico
                # Use phase voltage for reference (assuming delta connection or equivalent test setup)
                un_ref = tensao_at / math.sqrt(3) if tensao_at else 0
                up_un = tensao_prova / un_ref if un_ref else 0
                log.debug(
                    f"[Induced Voltage] Up/Un (Trifásico): {up_un:.4f} (Up={tensao_prova}, Un_ref=Un_AT_phase={un_ref:.2f})"
                )

            # Tensão aplicada no lado BT (U_aplicada_BT)
            # Needs careful consideration of transformation ratio (phase/line)
            if tipo_transformador == "Monofásico":
                # Simple ratio for monofásico
                tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova if tensao_at else 0
            else:  # Trifásico
                # Assuming test voltage (Up) is phase-to-ground or equivalent, and nominal voltages are line-to-line
                # Ratio applied should be line-to-line
                tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova if tensao_at else 0
            log.debug(
                f"[Induced Voltage] Tensão aplicada BT calculada: {tensao_aplicada_bt:.2f} kV"
            )

            # --- Função de Interpolação (já existente e verificada) ---
            def buscar_valores_tabela(inducao_teste, frequencia_teste, df):
                """Busca valores nas tabelas usando interpolação bilinear."""
                inducoes = sorted(df.index.get_level_values("inducao_nominal").unique())
                frequencias = sorted(df.index.get_level_values("frequencia_nominal").unique())

                inducao_teste_clipped = max(min(inducao_teste, max(inducoes)), min(inducoes))
                frequencia_teste_clipped = max(
                    min(frequencia_teste, max(frequencias)), min(frequencias)
                )
                if inducao_teste != inducao_teste_clipped:
                    log.warning(
                        f"Indução de teste {inducao_teste:.3f}T fora do range da tabela [{min(inducoes)}, {max(inducoes)}], usando {inducao_teste_clipped:.3f}T."
                    )
                if frequencia_teste != frequencia_teste_clipped:
                    log.warning(
                        f"Frequência de teste {frequencia_teste:.1f}Hz fora do range da tabela [{min(frequencias)}, {max(frequencias)}], usando {frequencia_teste_clipped:.1f}Hz."
                    )

                inducao_teste = inducao_teste_clipped
                frequencia_teste = frequencia_teste_clipped

                ind_idx = np.searchsorted(inducoes, inducao_teste)
                freq_idx = np.searchsorted(frequencias, frequencia_teste)

                ind_idx = min(max(ind_idx, 1), len(inducoes) - 1)
                freq_idx = min(max(freq_idx, 1), len(frequencias) - 1)

                ind_low, ind_high = inducoes[ind_idx - 1], inducoes[ind_idx]
                freq_low, freq_high = frequencias[freq_idx - 1], frequencias[freq_idx]

                q11 = df.loc[(ind_low, freq_low)].iloc[0]
                q12 = df.loc[(ind_low, freq_high)].iloc[0]
                q21 = df.loc[(ind_high, freq_low)].iloc[0]
                q22 = df.loc[(ind_high, freq_high)].iloc[0]

                # Handle cases where indices might be the same (value is exactly on grid boundary)
                if ind_high == ind_low:
                    x = 0.0
                else:
                    x = (inducao_teste - ind_low) / (ind_high - ind_low)

                if freq_high == freq_low:
                    y = 0.0
                else:
                    y = (frequencia_teste - freq_low) / (freq_high - freq_low)

                # Bilinear interpolation formula
                valor_interpolado = (
                    (1 - x) * (1 - y) * q11 + x * (1 - y) * q21 + (1 - x) * y * q12 + x * y * q22
                )

                log.debug(
                    f"Interpolação para B={inducao_teste:.3f}, f={frequencia_teste:.1f}: Pontos ({ind_low},{freq_low})={q11}, ({ind_low},{freq_high})={q12}, ({ind_high},{freq_low})={q21}, ({ind_high},{freq_high})={q22}. Pesos x={x:.3f}, y={y:.3f}. Resultado={valor_interpolado:.4f}"
                )
                return valor_interpolado

            # --- Obtenção dos Fatores das Tabelas ---
            log.debug(
                f"[Induced Voltage] Buscando valores nas tabelas para beta_teste={beta_teste:.4f} T e freq_teste={freq_teste:.1f} Hz"
            )
            fator_potencia_mag = buscar_valores_tabela(
                beta_teste, freq_teste, df_potencia_magnet
            )  # VAr/kg
            fator_perdas = buscar_valores_tabela(beta_teste, freq_teste, df_perdas_nucleo)  # W/kg
            log.debug(
                f"[Induced Voltage] Valores interpolados: fator_potencia_mag={fator_potencia_mag:.2f} VAr/kg, fator_perdas={fator_perdas:.2f} W/kg"
            )

            # --- Cálculos Finais ---
            results_data = {}  # Initialize dictionary for results

            if tipo_transformador == "Monofásico":
                # Potência Ativa (Pw) = Fator Perdas [W/kg] * Peso Núcleo [kg] / 1000 [kW]
                pot_ativa = fator_perdas * peso_nucleo_kg / 1000.0
                log.debug(
                    f"[Monofásico] Potência ativa (Pw): {pot_ativa:.2f} kW (fator_perdas={fator_perdas:.2f} W/kg, peso_kg={peso_nucleo_kg})"
                )

                # Potência Magnética (Sm) = Fator Pot Mag [VAr/kg] * Peso Núcleo [kg] / 1000 [kVAr] -> should be kVA
                pot_magnetica = (
                    fator_potencia_mag * peso_nucleo_kg / 1000.0
                )  # This is technically kVAr, but often referred to as kVA in this context
                log.debug(
                    f"[Monofásico] Potência magnética (Sm): {pot_magnetica:.2f} kVA (fator_pot_mag={fator_potencia_mag:.2f} VAr/kg, peso_kg={peso_nucleo_kg})"
                )

                # Componente Indutiva (Sind) = sqrt(Sm^2 - Pw^2) [kVAr]
                # Ensure Sm^2 >= Pw^2
                if pot_magnetica**2 < pot_ativa**2:
                    log.warning(
                        f"Potência magnética ao quadrado ({pot_magnetica**2:.2f}) menor que potência ativa ao quadrado ({pot_ativa**2:.2f}). Sind será zero."
                    )
                    pot_induzida = 0.0
                else:
                    pot_induzida = math.sqrt(pot_magnetica**2 - pot_ativa**2)
                log.debug(f"[Monofásico] Componente indutiva (Sind): {pot_induzida:.2f} kVAr ind")

                # Tensão para cálculo de Scap (U_dif)
                # Calculamos a diferença de tensão entre AT e terra, considerando a tensão BT refletida
                # U = tensao_prova - (up_un * tensao_bt)
                # Onde up_un é a relação entre tensão de prova e tensão nominal AT
                u_calc_scap = tensao_prova - (up_un * tensao_bt)
                log.debug(
                    f"[Monofásico] Tensão para cálculo Scap (U_calc_scap): {u_calc_scap:.2f} kV (tensao_prova={tensao_prova}, up_un={up_un}, tensao_bt={tensao_bt})"
                )

                # Potência Capacitiva (Scap) = - (U_calc^2 * 2 * pi * f * C * 10^-12) / 3 [kVAr]
                # O sinal negativo indica potência reativa capacitiva
                # Para transformadores monofásicos, dividimos por 3 para ajustar o valor da potência capacitiva
                # Convertemos u_calc_scap de kV para V multiplicando por 1000
                pcap = (
                    -(
                        (
                            (u_calc_scap * 1000) ** 2
                            * 2
                            * math.pi
                            * freq_teste
                            * capacitancia
                            * 1e-12
                        )
                        / 3
                    )
                    / 1000
                )  # Convertendo para kVAr
                log.debug(
                    f"[Monofásico] Potência capacitiva (Scap): {pcap:.2f} kVAr cap (U={u_calc_scap} kV, f={freq_teste} Hz, C={capacitancia} pF)"
                )

                results_data = {
                    "tensao_aplicada_bt": tensao_aplicada_bt,
                    "pot_ativa": pot_ativa,  # Pw
                    "pot_magnetica": pot_magnetica,  # Sm
                    "pot_induzida": pot_induzida,  # Sind
                    "u_dif": u_calc_scap,  # U para cálculo de Scap (renamed from u_dif for clarity)
                    "pcap": pcap,  # Scap
                }

            else:  # Trifásico
                # Potência Ativa Total (Pw_total) = Fator Perdas [W/kg] * Peso Núcleo [kg] / 1000 [kW]
                pot_ativa_total = fator_perdas * peso_nucleo_kg / 1000.0
                log.debug(f"[Trifásico] Potência ativa total (Pw): {pot_ativa_total:.2f} kW")

                # Potência Magnética Total (Sm_total) = Fator Pot Mag [VAr/kg] * Peso Núcleo [kg] / 1000 [kVAr] -> interpret as kVA
                pot_magnetica_total = fator_potencia_mag * peso_nucleo_kg / 1000.0
                log.debug(
                    f"[Trifásico] Potência magnética total (Sm): {pot_magnetica_total:.2f} kVA"
                )

                # Corrente de Excitação (Iexc) = Potência Magnética Sm (Total) / (√3 * Tensão Aplicada BT)
                corrente_excitacao = 0
                if tensao_aplicada_bt > 0:
                    corrente_excitacao = pot_magnetica_total / tensao_aplicada_bt * math.sqrt(3)
                log.debug(
                    f"[Trifásico] Corrente de excitação (Iexc): {corrente_excitacao:.2f} A (Sm={pot_magnetica_total:.2f} kVA, U_aplicada_bt={tensao_aplicada_bt:.2f} kV)"
                )

                # Potência de Teste (Total) = Potência Magnética Sm (Total)
                potencia_teste = corrente_excitacao * tensao_aplicada_bt * math.sqrt(3)
                log.debug(f"[Trifásico] Potência de teste (kVA): {potencia_teste:.2f} kVA")

                # Note: Capacitive effects are usually less dominant or calculated differently in standard 3-phase induced tests.
                # The input capacitance seems related to AT-GND, which might be relevant for single-phase tests or specific configurations.
                # We are not calculating a specific Pcap for the standard 3-phase case here.

                results_data = {
                    "tensao_aplicada_bt": tensao_aplicada_bt,
                    "pot_ativa": pot_ativa_total,  # Renaming for consistency in dict key
                    "pot_magnetica": pot_magnetica_total,  # Renaming for consistency in dict key
                    "corrente_excitacao": corrente_excitacao,
                    "potencia_teste": potencia_teste,
                    # No separate pcap or pot_induzida typically shown for 3-phase summary
                }

            # --- Preparação da Saída ---

            # Add common parameters to results_data
            results_data.update(
                {
                    "tensao_induzida": tensao_prova,
                    "frequencia_teste": freq_teste,
                    "inducao_teste": beta_teste,
                    "capacitancia": capacitancia,
                    "tipo_transformador": tipo_transformador,
                    "timestamp": datetime.datetime.now().isoformat(),
                    # Include factors used
                    "fator_potencia_mag": fator_potencia_mag,
                    "fator_perdas": fator_perdas,
                }
            )

            # Importar estilos padronizados
            from layouts import COLORS  # Assuming this exists

            # Define Styles (as provided in the original code)
            param_cell_style = {
                "backgroundColor": "#34495e",
                "color": "#ecf0f1",
                "fontWeight": "500",
                "fontSize": "0.8rem",
                "padding": "0.3rem 0.5rem",
                "textAlign": "left",
                "borderRight": "1px solid #2c3e50",
                "fontFamily": "Arial, sans-serif",
            }
            value_cell_style = {
                "backgroundColor": "#34495e",
                "color": "#ecf0f1",
                "fontSize": "0.8rem",
                "padding": "0.3rem 0.5rem",
                "textAlign": "right",
                "fontFamily": "Consolas, monospace",
                "letterSpacing": "0.02rem",
            }
            unit_cell_style = {
                "backgroundColor": "#34495e",
                "color": "#bdc3c7",
                "fontSize": "0.75rem",
                "padding": "0.3rem 0.5rem",
                "textAlign": "left",
                "fontStyle": "italic",
                "width": "60px",
            }
            card_header_style = {
                "backgroundColor": COLORS.get("primary", "#3498db"),
                "color": COLORS["text_light"],
                "fontWeight": "bold",
                "fontSize": "0.9rem",
                "padding": "0.4rem 0.5rem",
                "borderBottom": "1px solid " + COLORS["border"],
                "borderRadius": "4px 4px 0 0",
            }
            card_style = {
                "backgroundColor": COLORS["background_card"],
                "border": "1px solid " + COLORS["border"],
                "borderRadius": "4px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
                "height": "100%",
            }
            section_title_style = {
                "fontSize": "0.85rem",
                "color": "#3498db",
                "fontWeight": "bold",
                "marginBottom": "0.5rem",
            }  # Added margin
            table_style = {"fontSize": "0.8rem", "color": "#ecf0f1"}
            recommendation_card_style = {
                "backgroundColor": COLORS["background_card"],
                "border": "1px solid " + COLORS["border"],
                "borderRadius": "4px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.2)",
                "height": "100%",
            }
            recommendation_header_style = card_header_style
            recommendation_item_style = {
                "fontSize": "0.75rem",
                "padding": "0.2rem 0.4rem",
                "color": "#000000",
                "backgroundColor": "#f8f9fa",
                "borderBottom": "1px solid " + COLORS["border"],
                "lineHeight": "1.3",
            }

            # --- Construção das Tabelas de Saída ---

            # Tabela: Parâmetros de Entrada
            parametros_entrada = dbc.Col(
                [
                    html.H6(
                        "Parâmetros de Entrada", className="text-center", style=section_title_style
                    ),
                    dbc.Table(
                        html.Tbody(
                            [
                                html.Tr(
                                    [
                                        html.Td("Tipo do Transformador", style=param_cell_style),
                                        html.Td(tipo_transformador, style=value_cell_style),
                                        html.Td("", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Tensão Nominal AT", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(tensao_at, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("kV", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Tensão Nominal BT", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(tensao_bt, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("kV", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Frequência Nominal", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(freq_nominal, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("Hz", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Indução Nominal", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(inducao_nominal, 3),
                                            style=value_cell_style,
                                        ),
                                        html.Td("T", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Perdas em Vazio", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(perdas_vazio, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("kW", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Peso do Núcleo", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(peso_nucleo, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("Ton", style=unit_cell_style),
                                    ]
                                ),
                            ]
                        ),
                        bordered=True,
                        hover=True,
                        size="sm",
                        className="table-dark mb-0",
                        style=table_style,
                    ),
                ],
                md=4,
            )

            # Tabela: Parâmetros do Ensaio
            parametros_ensaio = dbc.Col(
                [
                    html.H6(
                        "Parâmetros do Ensaio", className="text-center", style=section_title_style
                    ),
                    dbc.Table(
                        html.Tbody(
                            [
                                html.Tr(
                                    [
                                        html.Td("Frequência de Teste", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(freq_teste, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("Hz", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Relação fp/fn", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(fp_fn, 2), style=value_cell_style
                                        ),
                                        html.Td("", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Tensão de Ensaio", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(tensao_prova, 1),
                                            style=value_cell_style,
                                        ),
                                        html.Td("kV", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Up/Un", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(up_un, 2), style=value_cell_style
                                        ),
                                        html.Td("", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Capacitância AT-GND", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(capacitancia, 0),
                                            style=value_cell_style,
                                        ),
                                        html.Td("pF", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Indução no Teste (β)", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(beta_teste, 3),
                                            style=value_cell_style,
                                        ),
                                        html.Td("T", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td(
                                            "Fator de Potência Magnética", style=param_cell_style
                                        ),
                                        html.Td(
                                            format_parameter_value(fator_potencia_mag, 2),
                                            style=value_cell_style,
                                        ),
                                        html.Td("VAr/kg", style=unit_cell_style),
                                    ]
                                ),
                                html.Tr(
                                    [
                                        html.Td("Fator de Perdas", style=param_cell_style),
                                        html.Td(
                                            format_parameter_value(fator_perdas, 2),
                                            style=value_cell_style,
                                        ),
                                        html.Td("W/kg", style=unit_cell_style),
                                    ]
                                ),
                            ]
                        ),
                        bordered=True,
                        hover=True,
                        size="sm",
                        className="table-dark mb-0",
                        style=table_style,
                    ),
                ],
                md=4,
            )

            # Tabela: Resultados Calculados (varia por tipo)
            if tipo_transformador == "Monofásico":
                resultados_calculados = dbc.Col(
                    [
                        html.H6(
                            "Resultados (Monofásico)",
                            className="text-center",
                            style=section_title_style,
                        ),
                        dbc.Table(
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td("Tensão Aplicada BT", style=param_cell_style),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("tensao_aplicada_bt"), 1
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kV", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td("Potência Ativa Pw", style=param_cell_style),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("pot_ativa"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kW", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Potência Reativa Magnética Sm",
                                                style=param_cell_style,
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("pot_magnetica"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kVA", style=unit_cell_style),
                                        ]
                                    ),  # Labelled kVA as per image
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Componente Indutiva Sind", style=param_cell_style
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("pot_induzida"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kVAr ind", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "U para cálculo de Scap", style=param_cell_style
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("u_dif"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kV", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Potência Capacitiva Scap",
                                                style={**param_cell_style, "fontWeight": "bold"},
                                            ),
                                            html.Td(
                                                format_parameter_value(results_data.get("pcap"), 2),
                                                style={
                                                    **value_cell_style,
                                                    "fontWeight": "bold",
                                                    "color": "red",
                                                },
                                            ),
                                            html.Td("kVAr cap", style=unit_cell_style),
                                        ]
                                    ),
                                ]
                            ),
                            bordered=True,
                            hover=True,
                            size="sm",
                            className="table-dark mb-0",
                            style=table_style,
                        ),
                    ],
                    md=4,
                )
            else:  # Trifásico
                resultados_calculados = dbc.Col(
                    [
                        html.H6(
                            "Resultados (Trifásico)",
                            className="text-center",
                            style=section_title_style,
                        ),
                        dbc.Table(
                            html.Tbody(
                                [
                                    html.Tr(
                                        [
                                            html.Td("Tensão Aplicada BT", style=param_cell_style),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("tensao_aplicada_bt"), 1
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kV", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td("Potência Ativa Pw", style=param_cell_style),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("pot_ativa"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kW", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Potência Magnética Sm (Total)",
                                                style=param_cell_style,
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("pot_magnetica"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("kVA", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Corrente de Excitação Iexc", style=param_cell_style
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("corrente_excitacao"), 2
                                                ),
                                                style=value_cell_style,
                                            ),
                                            html.Td("A", style=unit_cell_style),
                                        ]
                                    ),
                                    html.Tr(
                                        [
                                            html.Td(
                                                "Potência de Teste (Total)",
                                                style={**param_cell_style, "fontWeight": "bold"},
                                            ),
                                            html.Td(
                                                format_parameter_value(
                                                    results_data.get("potencia_teste"), 2
                                                ),
                                                style={
                                                    **value_cell_style,
                                                    "fontWeight": "bold",
                                                    "backgroundColor": "#FFF3CD"
                                                    if results_data.get("potencia_teste", 0) > 1500
                                                    else "",
                                                },
                                            ),
                                            html.Td("kVA", style=unit_cell_style),
                                        ]
                                    ),
                                    # Removed rows not directly calculated or less relevant for standard 3ph summary
                                ]
                            ),
                            bordered=True,
                            hover=True,
                            size="sm",
                            className="table-dark mb-0",
                            style=table_style,
                        ),
                    ],
                    md=4,
                )

                # Adicionar alerta para valores críticos em transformadores trifásicos
                alert_content = []
                if results_data.get("potencia_teste", 0) > 1500:
                    alert_content.append(
                        html.Li(
                            "Potência de Teste > 1500 kVA: Pode exceder capacidade da fonte.",
                            style={
                                "fontSize": "0.7rem",
                                "color": "#856404",
                                "marginBottom": "0.1rem",
                            },
                        )
                    )
                if results_data.get("tensao_aplicada_bt", 0) > 140:  # Example threshold
                    alert_content.append(
                        html.Li(
                            f"Tensão Aplicada em BT ({results_data.get('tensao_aplicada_bt', 0):.1f} kV) pode ser alta.",
                            style={
                                "fontSize": "0.7rem",
                                "color": "#856404",
                                "marginBottom": "0.1rem",
                            },
                        )
                    )

                if alert_content:
                    resultados_calculados = html.Div(
                        [
                            resultados_calculados,
                            html.Div(
                                [
                                    html.P(
                                        "* Atenção aos valores:",
                                        style={
                                            "fontSize": "0.7rem",
                                            "color": "#856404",
                                            "marginBottom": "0.2rem",
                                            "marginTop": "0.5rem",
                                        },
                                    ),
                                    html.Ul(
                                        alert_content,
                                        style={"paddingLeft": "1rem", "marginBottom": "0.2rem"},
                                    ),
                                ],
                                className="mt-2",
                            ),
                        ]
                    )

            # Montar a tabela de resultados completa
            results_table = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H6(
                            f"Resultados do Cálculo - {tipo_transformador}",
                            className="m-0 text-center",
                        ),
                        style=card_header_style,
                    ),
                    dbc.CardBody(
                        [dbc.Row([parametros_entrada, parametros_ensaio, resultados_calculados])],
                        style={"padding": "0.5rem"},
                    ),
                ],
                style=card_style,
            )

            # --- Construção das Recomendações ---
            recommendations = html.Div("Recomendações a serem implementadas")  # Placeholder

            if tipo_transformador == "Monofásico":
                pot_ativa = results_data.get("pot_ativa", 0)
                pot_magnetica = results_data.get("pot_magnetica", 0)  # Sm
                pot_induzida = results_data.get("pot_induzida", 0)  # Sind
                pcap = results_data.get("pcap", 0)  # Scap

                # Fonte precisa suprir Pw e a *diferença* entre Sind e Scap
                # Nota: pcap já está dividido por 3 conforme solicitado
                potencia_total_kVA_recomendada = (
                    max(pot_magnetica, pot_ativa + pcap) * 1.2
                )  # Based on image text, seems to consider worst case summation?
                tensao_saida_recomendada = tensao_aplicada_bt * 1.1
                pot_ativa_recomendada = pot_ativa * 1.2
                pot_indutiva_recomendada = pot_induzida * 1.2
                pot_capacitiva_recomendada = pcap * 1.2

                classe_potencia = "pequeno porte"
                if potencia_total_kVA_recomendada > 100:
                    classe_potencia = "grande porte"
                elif potencia_total_kVA_recomendada > 50:
                    classe_potencia = "médio porte"

                recommendations = dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H6("Recomendações para o Teste (Monofásico)", className="m-0"),
                            style=recommendation_header_style,
                        ),
                        dbc.CardBody(
                            [
                                html.P(
                                    "Recomendações para o ensaio:",
                                    className="mb-1",
                                    style={
                                        "fontSize": "0.75rem",
                                        "fontWeight": "500",
                                        "color": "#000000",
                                        "backgroundColor": "#f8f9fa",
                                        "padding": "0.2rem 0.4rem",
                                    },
                                ),
                                dbc.ListGroup(
                                    [
                                        dbc.ListGroupItem(
                                            f"Utilizar fonte de {freq_teste:.1f} Hz com capacidade mínima de {potencia_total_kVA_recomendada:.1f} kVA ({classe_potencia})",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Tensão de saída ajustável até {tensao_saida_recomendada:.1f} kV",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Potência ativa mínima de {pot_ativa_recomendada:.1f} kW",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Potência reativa indutiva de {pot_indutiva_recomendada:.1f} kVAr ind",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Potência reativa capacitiva de {pot_capacitiva_recomendada:.1f} kVAr cap",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            "Atenção à ressonância devido à alta potência capacitiva.",
                                            style=recommendation_item_style,
                                        ),
                                    ],
                                    flush=True,
                                ),
                            ],
                            style={"padding": "0.4rem", "backgroundColor": "#f8f9fa"},
                        ),
                    ],
                    style=recommendation_card_style,
                )

            else:  # Trifásico
                potencia_teste = results_data.get("potencia_teste", 0)  # Total kVA
                corrente_excitacao = results_data.get("corrente_excitacao", 0)
                pot_magnetica_total = results_data.get("pot_magnetica", 0)

                potencia_total_kVA_recomendada = potencia_teste * 1.2
                tensao_saida_recomendada = tensao_aplicada_bt * 1.1
                corrente_min_recomendada = corrente_excitacao * 1.5

                classe_potencia = "pequeno porte"
                if potencia_total_kVA_recomendada > 100:
                    classe_potencia = "grande porte"
                elif potencia_total_kVA_recomendada > 50:
                    classe_potencia = "médio porte"

                recommendations = dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H6("Recomendações para o Teste (Trifásico)", className="m-0"),
                            style=recommendation_header_style,
                        ),
                        dbc.CardBody(
                            [
                                html.P(
                                    "Recomendações para o ensaio:",
                                    className="mb-1",
                                    style={
                                        "fontSize": "0.75rem",
                                        "fontWeight": "500",
                                        "color": "#000000",
                                        "backgroundColor": "#f8f9fa",
                                        "padding": "0.2rem 0.4rem",
                                    },
                                ),
                                dbc.ListGroup(
                                    [
                                        dbc.ListGroupItem(
                                            f"Utilizar fonte de {freq_teste:.1f} Hz com capacidade mínima de {potencia_total_kVA_recomendada:.1f} kVA ({classe_potencia})",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Tensão de saída ajustável até {tensao_saida_recomendada:.1f} kV",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Corrente nominal mínima de {corrente_min_recomendada:.1f} A",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Potência magnética de {pot_magnetica_total:.1f} kVA",
                                            style=recommendation_item_style,
                                        ),  # Sm
                                        dbc.ListGroupItem(
                                            "Monitorar corrente e tensão durante o teste.",
                                            style=recommendation_item_style,
                                        ),
                                        dbc.ListGroupItem(
                                            f"Verificar capacidade da fonte vs. Potência de Teste ({potencia_teste:.1f} kVA).",
                                            style=recommendation_item_style,
                                        ),
                                    ],
                                    flush=True,
                                ),
                            ],
                            style={"padding": "0.4rem", "backgroundColor": "#f8f9fa"},
                        ),
                    ],
                    style=recommendation_card_style,
                )

            # --- Montagem Final do Layout ---
            results_div = html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col([results_table], md=9),  # Resultados ocupam 3/4
                            dbc.Col([recommendations], md=3),  # Recomendações ocupam 1/4
                        ],
                        className="g-0",
                    )  # No gutters
                ],
                className="p-0",
            )

            # --- Atualização do Store ---
            if current_store_data is None:
                current_store_data = {}

            # Dados para o store - inputs usados e resultados calculados
            data_for_store = {
                "inputs": {
                    "freq_nominal": freq_nominal,
                    "freq_teste": freq_teste,
                    "tensao_at": tensao_at,
                    "tensao_bt": tensao_bt,
                    "tensao_prova": tensao_prova,
                    "capacitancia": capacitancia,
                    "inducao_nominal": inducao_nominal,
                    "peso_nucleo_ton": peso_nucleo,
                    "perdas_vazio_kw": perdas_vazio,
                    "tipo_transformador": tipo_transformador,
                },
                "resultados": results_data,  # Contains all calculated values including factors
                "timestamp": datetime.datetime.now().isoformat(),
            }

            # Adicionar os inputs específicos para tensão induzida conforme solicitado
            inputs_tensao_induzida = {
                "tipo": tipo_transformador,
                "teste_fp": freq_teste,
                "cap_at_gnd_pf": capacitancia,
            }

            # Adicionar os inputs específicos para tensão induzida no store
            if "inputs_tensao_induzida" not in current_store_data:
                current_store_data["inputs_tensao_induzida"] = {}
            current_store_data["inputs_tensao_induzida"].update(inputs_tensao_induzida)

            # Atualizar o store com os novos dados
            current_store_data.update(data_for_store)

            # Limpar mensagem de erro
            error_msg = None

            return results_div, current_store_data, error_msg

        except Exception as e:
            log.error(f"Erro ao calcular tensão induzida: {e}", exc_info=True)
            error_msg = html.Div(
                f"Erro ao calcular tensão induzida: {str(e)}", className="alert alert-danger"
            )
            # Return no_update for results and store, but update error message
            return no_update, no_update, error_msg

    @app_instance.callback(
        Output("induced-voltage-error-message", "children", allow_duplicate=True),
        [
            Input("frequencia-teste", "value"),
            Input("capacitancia", "value"),
            Input("tipo-transformador", "value"),
        ],
        prevent_initial_call=True,
    )
    def monitor_remaining_inputs(freq_teste, capacitancia, tipo_transformador):
        """Monitora quando valores são inseridos em qualquer campo da página de tensão induzida."""
        # Obter o ID do input que disparou o callback
        from dash import callback_context

        ctx = callback_context

        if not ctx.triggered:
            return None  # No trigger, no message change

        input_id = ctx.triggered[0]["prop_id"].split(".")[0]
        input_value = ctx.triggered[0]["value"]

        id_to_name = {
            "frequencia-teste": "Teste (fp)",
            "capacitancia": "Cap. AT-GND (pF)",
            "tipo-transformador": "Tipo de Transformador",
        }
        input_name = id_to_name.get(input_id, input_id)

        log.debug(
            f"[Induced Voltage] VALOR INSERIDO NO CAMPO '{input_name}': {input_value}, tipo: {type(input_value)}"
        )

        # Limpa a mensagem de erro quando o usuário digita em um campo relevante
        # (Assumindo que a digitação visa corrigir um erro anterior)
        return None  # Clear previous errors on new input

    # Callback para gerar tabela de frequências
    @app_instance.callback(
        Output("frequency-table-container", "children"),
        [
            Input("generate-frequency-table-button", "n_clicks"),
            Input("clear-frequency-table-button", "n_clicks"),
        ],
        [
            State("transformer-inputs-store", "data"),
            State("losses-store", "data"),
            State("induced-voltage-store", "data"),
            State("tipo-transformador", "value"),
            State("capacitancia", "value"),
        ],
        prevent_initial_call=True,
    )
    def generate_frequency_table(
        generate_clicks,
        clear_clicks,
        transformer_data,
        losses_data,
        current_store_data,
        tipo_transformador_input,
        capacitancia_input,
    ):
        """Gera uma tabela com resultados para diferentes frequências ou limpa a tabela existente."""
        # Identificar qual botão foi clicado
        from dash import callback_context

        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        # Obter o ID do botão que foi clicado
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Se o botão de limpar foi clicado, retornar um div vazio
        if button_id == "clear-frequency-table-button":
            log.debug("[Induced Voltage] Limpando tabela de frequências")
            return html.Div()

        # Se o botão de gerar foi clicado, mas não tem clicks, não fazer nada
        if generate_clicks is None or generate_clicks == 0:
            raise PreventUpdate

        log.debug(
            f"[Induced Voltage] Gerando tabela de frequências: generate_clicks={generate_clicks}"
        )

        try:
            # Adicionar logs para diagnóstico
            log.debug(
                f"[Induced Voltage] Dados para tabela de frequências: transformer_data={transformer_data}, losses_data={losses_data}, current_store_data={current_store_data}"
            )

            # Verificar se temos os dados necessários
            if transformer_data is None or losses_data is None or current_store_data is None:
                log.warning(
                    f"[Induced Voltage] Dados insuficientes para gerar tabela de frequências: transformer_data={transformer_data}, losses_data={losses_data}, current_store_data={current_store_data}"
                )
                return html.Div(
                    "Dados insuficientes para gerar a tabela. Por favor, preencha todos os campos necessários e execute o cálculo de tensão induzida primeiro.",
                    className="alert alert-warning",
                )

            # Verificar se o cálculo de tensão induzida foi executado
            if "inputs" not in current_store_data or "resultados" not in current_store_data:
                log.warning(
                    f"[Induced Voltage] Cálculo de tensão induzida não foi executado: current_store_data={current_store_data}"
                )
                return html.Div(
                    "Por favor, execute o cálculo de tensão induzida antes de gerar a tabela de frequências.",
                    className="alert alert-warning",
                )

            # Extrair dados do transformador a partir do induced-voltage-store
            # Priorizar os dados do store, que contém os valores usados no último cálculo bem-sucedido
            inputs = current_store_data.get("inputs", {})
            resultados = current_store_data.get("resultados", {})

            tipo_transformador = inputs.get(
                "tipo_transformador",
                tipo_transformador_input
                or transformer_data.get("tipo_transformador", "Monofásico"),
            )
            log.debug(
                f"[Induced Voltage] Tipo de transformador para tabela de frequências: {tipo_transformador}"
            )

            # Verificar se o tipo de transformador é válido
            if tipo_transformador not in ["Monofásico", "Trifásico"]:
                return html.Div(
                    f"A tabela de frequências não está disponível para o tipo de transformador '{tipo_transformador}'.",
                    className="alert alert-info",
                )

            # Extrair parâmetros necessários do induced-voltage-store
            tensao_at = float(inputs.get("tensao_at", transformer_data.get("tensao_at", 0)))
            tensao_bt = float(inputs.get("tensao_bt", transformer_data.get("tensao_bt", 0)))
            freq_nominal = float(inputs.get("freq_nominal", transformer_data.get("frequencia", 60)))
            inducao_nominal = float(inputs.get("inducao_nominal", 0))
            peso_nucleo = float(inputs.get("peso_nucleo_ton", 0))
            tensao_prova = float(
                inputs.get("tensao_prova", transformer_data.get("teste_tensao_induzida", 0))
            )
            capacitancia = float(inputs.get("capacitancia", capacitancia_input or 0))

            # Verificar se temos todos os parâmetros necessários
            missing_params = []
            if tensao_at <= 0:
                missing_params.append("Tensão AT")
            if tensao_bt <= 0:
                missing_params.append("Tensão BT")
            if freq_nominal <= 0:
                missing_params.append("Frequência Nominal")
            if inducao_nominal <= 0:
                missing_params.append("Indução Nominal")
            if peso_nucleo <= 0:
                missing_params.append("Peso do Núcleo")
            if tensao_prova <= 0:
                missing_params.append("Tensão de Prova")
            if capacitancia <= 0:
                missing_params.append("Capacitância AT-GND")

            if missing_params:
                return html.Div(
                    f"Parâmetros insuficientes para gerar a tabela. Faltam: {', '.join(missing_params)}. Execute o cálculo de tensão induzida primeiro.",
                    className="alert alert-warning",
                )

            # Converter peso do núcleo de toneladas para kg
            peso_nucleo_kg = peso_nucleo * 1000.0

            # Obter os fatores usados no cálculo principal para referência
            fator_potencia_mag_ref = resultados.get("fator_potencia_mag", 0)
            fator_perdas_ref = resultados.get("fator_perdas", 0)

            log.debug(
                f"[Induced Voltage] Parâmetros para tabela de frequências: tensao_at={tensao_at}, tensao_bt={tensao_bt}, freq_nominal={freq_nominal}, inducao_nominal={inducao_nominal}, peso_nucleo={peso_nucleo}, tensao_prova={tensao_prova}, capacitancia={capacitancia}"
            )
            log.debug(
                f"[Induced Voltage] Fatores de referência: fator_potencia_mag={fator_potencia_mag_ref}, fator_perdas={fator_perdas_ref}"
            )

            # Lista de frequências para a tabela
            frequencias = [100, 120, 150, 180, 200, 240]

            # Preparar dados para a tabela
            table_data = []

            for freq_teste in frequencias:
                # Calcular parâmetros para esta frequência
                fp_fn = freq_teste / freq_nominal
                up_un = tensao_prova / tensao_at

                # Calcular indução de teste
                beta_teste = inducao_nominal * (up_un / fp_fn)

                # Garantir que a indução de teste não seja maior que 1.9T (limite físico típico)
                if beta_teste > 1.9:
                    beta_teste = 1.9
                    log.warning(
                        f"[Induced Voltage] Indução no teste limitada a 1.9T para frequência {freq_teste} Hz"
                    )

                # Função de interpolação (copiada da função principal)
                def buscar_valores_tabela(inducao_teste, frequencia_teste, df):
                    """Busca valores nas tabelas usando interpolação bilinear."""
                    inducoes = sorted(df.index.get_level_values("inducao_nominal").unique())
                    frequencias = sorted(df.index.get_level_values("frequencia_nominal").unique())

                    inducao_teste_clipped = max(min(inducao_teste, max(inducoes)), min(inducoes))
                    frequencia_teste_clipped = max(
                        min(frequencia_teste, max(frequencias)), min(frequencias)
                    )
                    if inducao_teste != inducao_teste_clipped:
                        log.warning(
                            f"Indução de teste {inducao_teste:.3f}T fora do range da tabela [{min(inducoes)}, {max(inducoes)}], usando {inducao_teste_clipped:.3f}T."
                        )
                    if frequencia_teste != frequencia_teste_clipped:
                        log.warning(
                            f"Frequência de teste {frequencia_teste:.1f}Hz fora do range da tabela [{min(frequencias)}, {max(frequencias)}], usando {frequencia_teste_clipped:.1f}Hz."
                        )

                    inducao_teste = inducao_teste_clipped
                    frequencia_teste = frequencia_teste_clipped

                    ind_idx = np.searchsorted(inducoes, inducao_teste)
                    freq_idx = np.searchsorted(frequencias, frequencia_teste)

                    ind_idx = min(max(ind_idx, 1), len(inducoes) - 1)
                    freq_idx = min(max(freq_idx, 1), len(frequencias) - 1)

                    ind_low, ind_high = inducoes[ind_idx - 1], inducoes[ind_idx]
                    freq_low, freq_high = frequencias[freq_idx - 1], frequencias[freq_idx]

                    q11 = df.loc[(ind_low, freq_low)].iloc[0]
                    q12 = df.loc[(ind_low, freq_high)].iloc[0]
                    q21 = df.loc[(ind_high, freq_low)].iloc[0]
                    q22 = df.loc[(ind_high, freq_high)].iloc[0]

                    # Handle cases where indices might be the same (value is exactly on grid boundary)
                    if ind_high == ind_low:
                        x = 0.0
                    else:
                        x = (inducao_teste - ind_low) / (ind_high - ind_low)

                    if freq_high == freq_low:
                        y = 0.0
                    else:
                        y = (frequencia_teste - freq_low) / (freq_high - freq_low)

                    # Bilinear interpolation formula
                    valor_interpolado = (
                        (1 - x) * (1 - y) * q11
                        + x * (1 - y) * q21
                        + (1 - x) * y * q12
                        + x * y * q22
                    )

                    log.debug(
                        f"Interpolação para B={inducao_teste:.3f}, f={frequencia_teste:.1f}: Pontos ({ind_low},{freq_low})={q11}, ({ind_low},{freq_high})={q12}, ({ind_high},{freq_low})={q21}, ({ind_high},{freq_high})={q22}. Pesos x={x:.3f}, y={y:.3f}. Resultado={valor_interpolado:.4f}"
                    )
                    return valor_interpolado

                # Calcular fatores específicos para esta frequência e indução usando a função de interpolação
                fator_potencia_mag = buscar_valores_tabela(
                    beta_teste, freq_teste, df_potencia_magnet
                )
                fator_perdas = buscar_valores_tabela(beta_teste, freq_teste, df_perdas_nucleo)

                log.debug(
                    f"[Induced Voltage] Frequência {freq_teste} Hz: beta_teste={beta_teste:.4f} T, fator_potencia_mag={fator_potencia_mag:.2f} VAr/kg, fator_perdas={fator_perdas:.2f} W/kg"
                )

                # Calcular potência ativa
                pot_ativa = fator_perdas * peso_nucleo_kg / 1000.0

                # Calcular potência magnética
                pot_magnetica = fator_potencia_mag * peso_nucleo_kg / 1000.0

                # Calcular potência indutiva com verificação
                if pot_magnetica**2 < pot_ativa**2:
                    log.warning(
                        f"[Induced Voltage] Frequência {freq_teste} Hz: Potência magnética ao quadrado ({pot_magnetica**2:.2f}) menor que potência ativa ao quadrado ({pot_ativa**2:.2f}). Sind será zero."
                    )
                    pot_induzida = 0.0
                else:
                    pot_induzida = math.sqrt(pot_magnetica**2 - pot_ativa**2)

                # Calcular tensão aplicada BT usando a fórmula correta
                tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova

                # Calcular potência capacitiva
                # Calculamos a diferença de tensão entre AT e terra, considerando a tensão BT refletida
                u_calc_scap = tensao_prova - (up_un * tensao_bt)
                # Convertemos u_calc_scap de kV para V multiplicando por 1000
                pcap = (
                    -((u_calc_scap * 1000) ** 2 * 2 * math.pi * freq_teste * capacitancia * 1e-12)
                    / 3
                    / 1000
                )  # Convertendo para kVAr

                # Calcular a razão Scap/Sind (sem sinal)
                if pot_induzida > 0:
                    scap_sind_ratio = abs(pcap) / pot_induzida
                else:
                    scap_sind_ratio = 0  # Evitar divisão por zero

                # Adicionar linha à tabela
                table_data.append(
                    {
                        "frequencia": freq_teste,
                        "tensao_aplicada_bt": tensao_aplicada_bt,
                        "pot_ativa": pot_ativa,
                        "pot_magnetica": pot_magnetica,
                        "pot_induzida": pot_induzida,
                        "u_calc_scap": u_calc_scap,
                        "pcap": pcap,
                        "scap_sind_ratio": scap_sind_ratio,
                    }
                )

            # Criar tabela HTML com base no tipo de transformador
            if tipo_transformador == "Monofásico":
                table_header = [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(
                                    "Frequência (Hz)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Ativa Pw (kW)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Reativa Magnética Sm (kVA)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Componente Indutiva Sind (kVAr ind)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Capacitiva Scap (kVAr cap)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Scap/Sind",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                            ]
                        )
                    )
                ]

                table_rows = []
                for row in table_data:
                    # Usar format_parameter_value para formatar os valores
                    table_rows.append(
                        html.Tr(
                            [
                                html.Td(f"{row['frequencia']}", style={"textAlign": "center"}),
                                html.Td(
                                    format_parameter_value(row["pot_ativa"], 2),
                                    style={"textAlign": "center"},
                                ),
                                html.Td(
                                    format_parameter_value(row["pot_magnetica"], 2),
                                    style={"textAlign": "center"},
                                ),
                                html.Td(
                                    format_parameter_value(row["pot_induzida"], 2),
                                    style={"textAlign": "center"},
                                ),
                                html.Td(
                                    format_parameter_value(abs(row["pcap"]), 2),
                                    style={"textAlign": "center", "color": "red"},
                                ),
                                html.Td(
                                    format_parameter_value(row["scap_sind_ratio"], 2),
                                    style={"textAlign": "center", "fontWeight": "bold"},
                                ),
                            ]
                        )
                    )
            else:  # Trifásico
                table_header = [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(
                                    "Frequência (Hz)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Ativa Pw (kW)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Reativa Magnética Sm (kVA)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Th(
                                    "Potência Capacitiva Scap (kVAr cap)",
                                    style={
                                        "backgroundColor": "#34495e",
                                        "color": "#ecf0f1",
                                        "textAlign": "center",
                                    },
                                ),
                            ]
                        )
                    )
                ]

                table_rows = []
                for row in table_data:
                    # Usar format_parameter_value para formatar os valores
                    table_rows.append(
                        html.Tr(
                            [
                                html.Td(f"{row['frequencia']}", style={"textAlign": "center"}),
                                html.Td(
                                    format_parameter_value(row["pot_ativa"], 2),
                                    style={"textAlign": "center"},
                                ),
                                html.Td(
                                    format_parameter_value(row["pot_magnetica"], 2),
                                    style={"textAlign": "center"},
                                ),
                                html.Td(
                                    format_parameter_value(abs(row["pcap"]), 2),
                                    style={"textAlign": "center", "color": "red"},
                                ),
                            ]
                        )
                    )

            table_body = [html.Tbody(table_rows)]

            table = dbc.Table(
                table_header + table_body,
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
                className="mt-3",
            )

            # Adicionar logs para diagnóstico
            log.debug(
                f"[Induced Voltage] Tabela de frequências gerada com sucesso: {len(table_data)} linhas"
            )

            # Preparar dados para o gráfico
            frequencias = [row["frequencia"] for row in table_data]
            pot_ativa_values = [row["pot_ativa"] for row in table_data]
            pot_magnetica_values = [row["pot_magnetica"] for row in table_data]
            pot_capacitiva_values = [abs(row["pcap"]) for row in table_data]

            if tipo_transformador == "Monofásico":
                pot_indutiva_values = [row["pot_induzida"] for row in table_data]

            # Criar gráfico usando plotly

            # Criar figura
            fig = go.Figure()

            # Adicionar linhas para cada tipo de potência
            fig.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_ativa_values,
                    mode="lines+markers",
                    name="Potência Ativa (kW)",
                    line=dict(color="#e74c3c", width=2),
                    marker=dict(size=8),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_magnetica_values,
                    mode="lines+markers",
                    name="Potência Magnética (kVA)",
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=8),
                )
            )

            # Para transformadores monofásicos, adicionar também a potência indutiva
            if tipo_transformador == "Monofásico":
                fig.add_trace(
                    go.Scatter(
                        x=frequencias,
                        y=pot_indutiva_values,
                        mode="lines+markers",
                        name="Potência Indutiva (kVAr ind)",
                        line=dict(color="#9b59b6", width=2),
                        marker=dict(size=8),
                    )
                )

            fig.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_capacitiva_values,
                    mode="lines+markers",
                    name="Potência Capacitiva (kVAr)",
                    line=dict(color="#2ecc71", width=2),
                    marker=dict(size=8),
                )
            )

            # Criar uma segunda figura com escala logarítmica
            fig_log = go.Figure()

            # Adicionar as mesmas linhas para a figura com escala logarítmica
            fig_log.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_ativa_values,
                    mode="lines+markers",
                    name="Potência Ativa (kW)",
                    line=dict(color="#e74c3c", width=2),
                    marker=dict(size=8),
                )
            )

            fig_log.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_magnetica_values,
                    mode="lines+markers",
                    name="Potência Magnética (kVA)",
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=8),
                )
            )

            # Para transformadores monofásicos, adicionar também a potência indutiva
            if tipo_transformador == "Monofásico":
                fig_log.add_trace(
                    go.Scatter(
                        x=frequencias,
                        y=pot_indutiva_values,
                        mode="lines+markers",
                        name="Potência Indutiva (kVAr ind)",
                        line=dict(color="#9b59b6", width=2),
                        marker=dict(size=8),
                    )
                )

            fig_log.add_trace(
                go.Scatter(
                    x=frequencias,
                    y=pot_capacitiva_values,
                    mode="lines+markers",
                    name="Potência Capacitiva (kVAr)",
                    line=dict(color="#2ecc71", width=2),
                    marker=dict(size=8),
                )
            )

            # Atualizar layout da figura com escala linear
            fig.update_layout(
                title="Potências vs. Frequência (Escala Linear)",
                xaxis_title="Frequência (Hz)",
                yaxis_title="Potência",
                template="plotly_dark",
                margin=dict(l=50, r=120, t=50, b=50),  # Aumentar margem direita para a legenda
                legend=dict(
                    orientation="v",  # Orientação vertical
                    yanchor="middle",  # Ancorar no meio verticalmente
                    y=0.5,  # Posição vertical no meio
                    xanchor="right",  # Ancorar à direita
                    x=1.15,  # Posição horizontal fora do gráfico
                ),
                height=300,
            )

            # Atualizar layout da figura com escala logarítmica
            fig_log.update_layout(
                title="Potências vs. Frequência (Escala Logarítmica)",
                xaxis_title="Frequência (Hz)",
                yaxis=dict(title="Potência (escala log)", type="log", exponentformat="power"),
                template="plotly_dark",
                margin=dict(l=50, r=120, t=50, b=50),  # Aumentar margem direita para a legenda
                legend=dict(
                    orientation="v",  # Orientação vertical
                    yanchor="middle",  # Ancorar no meio verticalmente
                    y=0.5,  # Posição vertical no meio
                    xanchor="right",  # Ancorar à direita
                    x=1.15,  # Posição horizontal fora do gráfico
                ),
                height=300,
            )

            # Criar componentes gráficos
            graph_linear = dcc.Graph(figure=fig, config={"displayModeBar": False})
            graph_log = dcc.Graph(figure=fig_log, config={"displayModeBar": False})

            # Criar layout com tabela e gráficos
            log.debug(
                f"[Induced Voltage] Criando layout com tipo_transformador={tipo_transformador}"
            )

            # Garantir que o tipo de transformador seja exibido corretamente
            tipo_texto = "monofásico" if tipo_transformador == "Monofásico" else "trifásico"

            result_div = html.Div(
                [
                    html.H5(
                        "Tabela de Resultados para Diferentes Frequências",
                        className="text-center mt-4 mb-3",
                    ),
                    html.P(
                        f"Resultados calculados para transformador {tipo_texto} com diferentes frequências de teste:",
                        className="text-muted",
                    ),
                    dbc.Row(
                        [
                            # Tabela (50% de largura)
                            dbc.Col([table], width=6),
                            # Gráficos (50% de largura)
                            dbc.Col(
                                [
                                    # Tabs para alternar entre gráficos linear e logarítmico
                                    dbc.Tabs(
                                        [
                                            dbc.Tab(graph_linear, label="Escala Linear"),
                                            dbc.Tab(graph_log, label="Escala Logarítmica"),
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                        ]
                    ),
                ]
            )

            return result_div

        except Exception as e:
            import traceback

            error_traceback = traceback.format_exc()
            log.error(f"Erro ao gerar tabela de frequências: {e}\n{error_traceback}")

            # Mensagem de erro mais detalhada para o usuário
            return html.Div(
                [
                    html.H5("Erro ao gerar tabela de frequências", className="text-danger"),
                    html.P(f"Erro: {str(e)}"),
                    html.P("Verifique se todos os campos necessários foram preenchidos:"),
                    html.Ul(
                        [
                            html.Li("Tipo de Transformador: Monofásico ou Trifásico"),
                            html.Li("Tensão Nominal AT e BT"),
                            html.Li("Frequência Nominal"),
                            html.Li("Indução Nominal"),
                            html.Li("Peso do Núcleo"),
                            html.Li("Tensão de Prova"),
                            html.Li("Capacitância AT-GND"),
                        ]
                    ),
                    html.P("Detalhes técnicos (para suporte):", className="mt-3 text-muted"),
                    html.Pre(
                        error_traceback,
                        style={
                            "fontSize": "0.7rem",
                            "backgroundColor": "#f8f9fa",
                            "padding": "0.5rem",
                            "maxHeight": "200px",
                            "overflow": "auto",
                        },
                    ),
                ],
                className="alert alert-danger",
            )

    log.debug("Callbacks de Tensão Induzida registrados com sucesso")


# --- Fim do registro ---
