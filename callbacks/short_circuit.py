# callbacks/short_circuit.py
"""
Módulo short_circuit que usa o padrão de registro centralizado.
"""
import datetime  # Importado para o timestamp no store
import logging
import math

import pandas as pd
import plotly.express as px
from dash import Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate

from app_core.calculations import calculate_impedance_variation, calculate_short_circuit_params
from config import colors  # Importar cores para estilos de status

# Importações da aplicação
# Não importar app diretamente para evitar importações circulares
from utils import constants  # Para limites de variação de impedância
from utils.callback_helpers import safe_float
from utils.mcp_utils import patch_mcp  # Importar função patch_mcp
from utils.store_diagnostics import convert_numpy_types
from components.validators import validate_dict_inputs  # Para validação

log = logging.getLogger(__name__)

# --- Define Styles Locally Using Imported Colors ---
# Define base styles first
BASE_STATUS_STYLE = {
    "fontWeight": "bold",
    "fontSize": "0.8rem",
    "padding": "2px 5px",
    "borderRadius": "3px",
}

# Define specific status styles by merging base with colors
PASS_STYLE = {
    **BASE_STATUS_STYLE,
    "color": colors.get("pass", "#198754"),
    "backgroundColor": "#d1e7dd",
}  # Green text, light green bg
FAIL_STYLE = {
    **BASE_STATUS_STYLE,
    "color": colors.get("fail", "#dc3545"),
    "backgroundColor": "#f8d7da",
}  # Red text, light red bg
WARNING_STYLE = {
    **BASE_STATUS_STYLE,
    "color": colors.get("warning", "#ffc107"),
    "backgroundColor": "#fff3cd",
}  # Yellow text, light yellow bg


# --- Funções Auxiliares ---
def create_empty_sc_figure():
    """Creates an empty placeholder figure for the impedance variation graph."""
    fig = px.bar(title="Variação da Impedância (%)")
    fig.update_layout(
        template="plotly_white",
        yaxis_title="ΔZ (%)",
        xaxis_title="",
        margin=dict(t=30, b=10, l=10, r=10),
        title_font_size=12,
        font_size=10,
    )
    return fig


# --- Função de Registro de Callbacks ---
def register_short_circuit_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de short_circuit.
    Esta função é chamada por app.py durante a inicialização.

    Registra os callbacks que foram convertidos para o padrão de registro centralizado.
    """
    log.info(f"Registrando callbacks do módulo short_circuit para app {app_instance.title}...")

    # --- Callback para exibir informações do transformador na página ---
    @app_instance.callback(
        Output("transformer-info-short-circuit-page", "children"),
        Input("transformer-info-short-circuit", "children"),
        prevent_initial_call=False,
    )
    def update_short_circuit_page_info_panel(global_panel_content):
        """Copia o conteúdo do painel global para o painel específico da página."""
        log.debug("Atualizando painel de informações do transformador na página de curto-circuito")
        return global_panel_content

    # Callback para CARREGAR dados do Store
    @app_instance.callback(
        [
            Output("impedance-before", "value"),
            Output("impedance-after", "value"),
            Output("peak-factor", "value"),
            Output("isc-side", "value"),
            Output("power-category", "value"),
            Output("isc-sym-result", "value"),
            Output("isc-peak-result", "value"),
            Output("delta-impedance-result", "value"),
            Output("impedance-check-status", "children"),
            Output("impedance-variation-graph", "figure"),
            Output("short-circuit-error-message", "children"),
        ],
        [
            Input("short-circuit-store", "data"),
            Input("url", "pathname"),
            Input("transformer-inputs-store", "data") # Adicionado para ler dados globais
        ],  # Triggered when store data is loaded/changed or URL changes
        prevent_initial_call=False,  # Allow running on initial load
    )
    def short_circuit_load_data(stored_data_local, pathname, transformer_data_global): # Parâmetros renomeados
        """Carrega os dados da aba Curto-Circuito armazenados no dcc.Store."""
        from utils.routes import ROUTE_SHORT_CIRCUIT, normalize_pathname # Import local

        ctx_triggered = ctx.triggered_id
        log.debug(f"[LOAD ShortCircuit] Callback triggered by: {ctx_triggered}, Pathname: {pathname}")

        # Se o callback foi disparado pela URL, verifica se estamos na página correta
        clean_path = normalize_pathname(pathname) if pathname else ""
        if ctx_triggered == "url" and clean_path != ROUTE_SHORT_CIRCUIT:
            log.debug(f"[LOAD ShortCircuit] Não na página de Curto-Circuito ({clean_path}). Abortando trigger de URL.")
            raise PreventUpdate

        # Processar dados locais (do short-circuit-store)
        inputs_local = {}
        results_local = {}
        if stored_data_local and isinstance(stored_data_local, dict):
            # Verificar se os dados estão em 'inputs_curto_circuito'
            inputs_local = stored_data_local.get("inputs_curto_circuito", {})
            results_local = stored_data_local.get("resultados_curto_circuito", {})

            # Verificar se os dados estão diretamente no dicionário principal
            log.debug(f"[LOAD ShortCircuit] Verificando dados diretamente no dicionário principal: {list(stored_data_local.keys())}")

            # Verificar inputs diretamente no dicionário principal
            if "impedance_before" in stored_data_local and not inputs_local.get("impedance_before"):
                inputs_local["impedance_before"] = stored_data_local.get("impedance_before")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: impedance_before={inputs_local['impedance_before']}")

            if "impedance_after" in stored_data_local and not inputs_local.get("impedance_after"):
                inputs_local["impedance_after"] = stored_data_local.get("impedance_after")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: impedance_after={inputs_local['impedance_after']}")

            if "peak_factor" in stored_data_local and not inputs_local.get("peak_factor"):
                inputs_local["peak_factor"] = stored_data_local.get("peak_factor")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: peak_factor={inputs_local['peak_factor']}")

            if "isc_side" in stored_data_local and not inputs_local.get("isc_side"):
                inputs_local["isc_side"] = stored_data_local.get("isc_side")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: isc_side={inputs_local['isc_side']}")

            if "category" in stored_data_local and not inputs_local.get("category"):
                inputs_local["category"] = stored_data_local.get("category")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: category={inputs_local['category']}")

            # Verificar resultados diretamente no dicionário principal
            if "isc_sym_kA" in stored_data_local and not results_local.get("isc_sym_kA"):
                results_local["isc_sym_kA"] = stored_data_local.get("isc_sym_kA")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: isc_sym_kA={results_local['isc_sym_kA']}")

            if "isc_peak_kA" in stored_data_local and not results_local.get("isc_peak_kA"):
                results_local["isc_peak_kA"] = stored_data_local.get("isc_peak_kA")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: isc_peak_kA={results_local['isc_peak_kA']}")

            if "delta_impedance_percent" in stored_data_local and not results_local.get("delta_impedance_percent"):
                results_local["delta_impedance_percent"] = stored_data_local.get("delta_impedance_percent")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: delta_impedance_percent={results_local['delta_impedance_percent']}")

            if "status_text" in stored_data_local and not results_local.get("status_text"):
                results_local["status_text"] = stored_data_local.get("status_text")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: status_text={results_local['status_text']}")

            if "limit_used" in stored_data_local and not results_local.get("limit_used"):
                results_local["limit_used"] = stored_data_local.get("limit_used")
                log.debug(f"[LOAD ShortCircuit] Valor encontrado diretamente no dicionário principal: limit_used={results_local['limit_used']}")

        # Processar dados globais (do transformer-inputs-store)
        impedancia_nominal_global = None
        if transformer_data_global and isinstance(transformer_data_global, dict):
            # Verificar se os dados estão aninhados em transformer_data
            if "transformer_data" in transformer_data_global and isinstance(transformer_data_global["transformer_data"], dict):
                # Usar os dados aninhados
                data_dict = transformer_data_global["transformer_data"]
                log.debug(f"[LOAD ShortCircuit] Usando dados aninhados em transformer_data")
            else:
                # Usar os dados diretamente
                data_dict = transformer_data_global
                log.debug(f"[LOAD ShortCircuit] Usando dados diretamente do dicionário principal")

            impedancia_nominal_global = safe_float(data_dict.get("impedancia"))

        # Decidir valor para impedance-before
        z_before_local = inputs_local.get("impedance_before")
        final_z_before = z_before_local if z_before_local is not None else impedancia_nominal_global

        # Outros inputs são carregados do store local ou usam padrão
        z_after = inputs_local.get("impedance_after")
        peak_factor = inputs_local.get("peak_factor", 2.55)
        isc_side = inputs_local.get("isc_side", "AT")
        category = inputs_local.get("category")

        # Extract result values
        isc_sym = results_local.get("isc_sym_kA")
        isc_peak = results_local.get("isc_peak_kA")
        delta_z = results_local.get("delta_impedance_percent")
        status_text = results_local.get("status_text", "-")  # Status textual (APROVADO/REPROVADO/etc.)
        limit = results_local.get("limit_used")  # Limite numérico usado

        # Rebuild status display with appropriate style
        status_children = "-"
        status_style_to_use = {}  # Default empty style
        if status_text == "APROVADO":
            status_style_to_use = PASS_STYLE
            status_children = html.Span(
                f"ΔZ={delta_z:.2f}% | {status_text}", style=status_style_to_use
            )
        elif status_text == "REPROVADO":
            status_style_to_use = FAIL_STYLE
            status_children = html.Span(
                f"ΔZ={delta_z:.2f}% | {status_text}", style=status_style_to_use
            )
        elif status_text != "-":  # Handle other statuses like "Erro", "Categoria Inválida"
            status_style_to_use = WARNING_STYLE  # Use warning style for indeterminates/errors
            status_children = html.Span(status_text, style=status_style_to_use)

        # Rebuild the graph
        fig = create_empty_sc_figure()  # Start with empty
        if delta_z is not None and limit is not None and limit > 0:
            try:
                df_graph = pd.DataFrame(
                    {
                        "Métrica": ["Variação Medida (ΔZ)", "Limite Superior", "Limite Inferior"],
                        "Valor (%)": [delta_z, limit, -limit],
                        "Tipo": ["Medido", "Limite", "Limite"],
                    }
                )
                limit_text = f"Cat.{category or results_local.get('category','?')} (±{limit:.1f}%)"
                fig = px.bar(
                    df_graph,
                    x="Métrica",
                    y="Valor (%)",
                    color="Tipo",
                    title=f"Variação da Impedância vs Limite ({limit_text})",
                    color_discrete_map={
                        "Medido": colors.get("primary", "royalblue"),
                        "Limite": colors.get("fail", "firebrick"),
                    },
                    text="Valor (%)",
                    height=300,
                )

                fig.update_traces(
                    texttemplate="%{y:.2f}%", textposition="outside", cliponaxis=False
                )
                fig.update_layout(
                    template="plotly_white",
                    yaxis_title="Variação (%)",
                    xaxis_title="",
                    legend_title_text="",
                    yaxis_range=[-limit * 1.5 - 1, limit * 1.5 + 1],
                    margin=dict(t=50, b=10, l=10, r=10),
                    title_font_size=12,
                    font_size=10,
                )
            except Exception as e_fig:
                log.error(f"Error rebuilding short-circuit graph: {e_fig}")
                # Keep the empty figure

        log.debug(f"[LOAD ShortCircuit] Returning values: z_before={final_z_before}, z_after={z_after}, delta_z={delta_z}")

        return (
            final_z_before,
            z_after,
            peak_factor,
            isc_side,
            category,
            isc_sym,
            isc_peak,
            f"{delta_z:.2f}" if delta_z is not None else "",
            status_children,
            fig,
            "",
        )

    # Callback principal para cálculo e verificação
    @app_instance.callback(
        [
            Output("isc-sym-result", "value", allow_duplicate=True),  # Output: Isc Simétrica (kA)
            Output("isc-peak-result", "value", allow_duplicate=True),  # Output: Isc Pico (kA)
            Output(
                "delta-impedance-result", "value", allow_duplicate=True
            ),  # Output: Variação Z (%)
            Output(
                "impedance-check-status", "children", allow_duplicate=True
            ),  # Output: Status (APROVADO/REPROVADO)
            Output(
                "impedance-variation-graph", "figure", allow_duplicate=True
            ),  # Output: Gráfico de barras
            Output(
                "short-circuit-error-message", "children", allow_duplicate=True
            ),  # Output: Mensagem de erro
            Output("short-circuit-store", "data", allow_duplicate=True),
        ],  # Output: Store com resultados
        [Input("calc-short-circuit-btn", "n_clicks")],  # Trigger: Botão Calcular
        [
            State("impedance-before", "value"),  # State: Z antes (%)
            State("impedance-after", "value"),  # State: Z depois (%)
            State("peak-factor", "value"),  # State: Fator k√2
            State("isc-side", "value"),  # State: Lado (AT/BT/TERCIARIO)
            State("power-category", "value"),  # State: Categoria (I/II/III)
            State("transformer-inputs-store", "data"),  # State: Dados básicos do trafo
            State("short-circuit-store", "data"),  # State: Dados atuais do store
            State("url", "pathname"),
        ],  # State: URL atual para verificação
        prevent_initial_call=True,
    )
    def short_circuit_calculate_and_verify(
        n_clicks,
        z_before_str,
        z_after_str,
        k_peak_factor_str,
        side,
        category,
        transformer_data,
        current_store_data,
        pathname,
    ):
        """
        Calcula correntes de curto-circuito, variação de impedância, verifica conformidade
        e atualiza a UI e o store.
        """
        # Verificar se estamos na página correta
        if pathname != "/curto-circuito":
            log.info(
                f"Ignorando callback short_circuit_calculate_and_verify em página diferente: {pathname}"
            )
            raise PreventUpdate

        if n_clicks is None:
            raise PreventUpdate

        log.info("Calculando Suportabilidade a Curto-Circuito...")

        # --- Gráfico Vazio Padrão ---
        empty_fig = create_empty_sc_figure()

        # --- Validação de Entradas da UI ---
        input_values = {
            "z_before": safe_float(z_before_str),
            "z_after": safe_float(z_after_str),
            "k_peak_factor": safe_float(k_peak_factor_str),
            "side": side,
            "category": category,
        }
        validation_rules = {
            "z_before": {"required": True, "positive": True, "label": "Z Pré-Ensaio (%)"},
            "z_after": {"required": True, "positive": True, "label": "Z Pós-Ensaio (%)"},
            "k_peak_factor": {"required": True, "positive": True, "label": "Fator de Pico (k√2)"},
            "side": {
                "required": True,
                "allowed": ["AT", "BT", "TERCIARIO"],
                "label": "Lado Cálculo Isc",
            },
            "category": {
                "required": True,
                "allowed": ["I", "II", "III"],
                "label": "Categoria Potência",
            },
        }
        errors = validate_dict_inputs(input_values, validation_rules)

        # --- Validação de Dados do Transformador ---
        if not transformer_data:
            errors.append("Dados do transformador (Dados Básicos) não encontrados.")
        else:
            # Define keys based on 'side'
            if side == "AT":
                req_keys = ["potencia_mva", "tensao_at", "corrente_nominal_at", "impedancia"]
            elif side == "BT":
                req_keys = ["potencia_mva", "tensao_bt", "corrente_nominal_bt", "impedancia"]
            elif side == "TERCIARIO":
                req_keys = [
                    "potencia_mva",
                    "tensao_terciario",
                    "corrente_nominal_terciario",
                    "impedancia",
                ]
            else:
                req_keys = []  # Already caught by validation rules

            missing_trafo = [
                k
                for k in req_keys
                if transformer_data.get(k) is None or str(transformer_data.get(k)).strip() == ""
            ]
            if missing_trafo:
                errors.append(
                    f"Dados básicos necessários para cálculo Isc ({side}) ausentes: {', '.join(missing_trafo)}."
                )
            # Also check if nominal impedance exists and is valid
            if "impedancia" not in req_keys:  # Should not happen if side is valid
                pass
            elif (
                transformer_data.get("impedancia") is None
                or safe_float(transformer_data.get("impedancia"), default=-1) <= 0
            ):
                errors.append("Impedância nominal (%) em 'Dados Básicos' é inválida ou ausente.")

        if errors:
            log.warning(f"Erros de validação Curto-Circuito: {errors}")
            error_msg = html.Ul(
                [html.Li(e) for e in errors], style={"color": "red", "fontSize": "0.7rem"}
            )
            return None, None, None, "-", empty_fig, error_msg, no_update

        # --- Cálculos ---
        try:
            # Extrai valores validados
            z_before = input_values["z_before"]
            z_after = input_values["z_after"]
            k_peak_factor = input_values["k_peak_factor"]  # This is k*sqrt(2)

            # Verificar se os dados estão aninhados em transformer_data
            if "transformer_data" in transformer_data and isinstance(transformer_data["transformer_data"], dict):
                # Usar os dados aninhados
                data_dict = transformer_data["transformer_data"]
                log.debug(f"[Short Circuit] Usando dados aninhados em transformer_data")
            else:
                # Usar os dados diretamente
                data_dict = transformer_data
                log.debug(f"[Short Circuit] Usando dados diretamente do dicionário principal")

            # Pega dados do transformador (garantidos que existem e são válidos)
            try:
                potencia_mva = float(data_dict["potencia_mva"])
                impedancia_nominal_percent = float(data_dict["impedancia"])
                impedancia_pu = impedancia_nominal_percent / 100.0
                tipo = data_dict.get("tipo_transformador", "Trifásico")
                sqrt_3 = math.sqrt(3) if tipo == "Trifásico" else 1.0
            except (KeyError, TypeError, ValueError) as e:
                log.error(f"[Short Circuit] Erro ao obter dados do transformador: {e}")
                errors.append(f"Erro ao obter dados do transformador: {e}")
                error_msg = html.Ul(
                    [html.Li(e) for e in errors], style={"color": "red", "fontSize": "0.7rem"}
                )
                return None, None, None, "-", empty_fig, error_msg, no_update

            # Pega corrente nominal do lado selecionado
            corrente_nominal_a = None

            # Primeiro tenta obter do dicionário de dados do transformador
            if side == "AT":
                corrente_nominal_a = data_dict.get("corrente_nominal_at")
            elif side == "BT":
                corrente_nominal_a = data_dict.get("corrente_nominal_bt")
            else:
                corrente_nominal_a = data_dict.get("corrente_nominal_terciario")

            # Se não encontrou ou é None, calcula usando o MCP
            if corrente_nominal_a is None:
                log.warning(
                    f"[Short Circuit] Corrente nominal para lado {side} não encontrada no MCP. Calculando..."
                )
                calculated_currents = app_instance.mcp.calculate_nominal_currents(transformer_data)

                # Atualiza o MCP com as correntes calculadas
                updated_transformer_data = transformer_data.copy()
                updated_transformer_data.update(
                    {
                        "corrente_nominal_at": calculated_currents.get("corrente_nominal_at"),
                        "corrente_nominal_at_tap_maior": calculated_currents.get(
                            "corrente_nominal_at_tap_maior"
                        ),
                        "corrente_nominal_at_tap_menor": calculated_currents.get(
                            "corrente_nominal_at_tap_menor"
                        ),
                        "corrente_nominal_bt": calculated_currents.get("corrente_nominal_bt"),
                        "corrente_nominal_terciario": calculated_currents.get(
                            "corrente_nominal_terciario"
                        ),
                    }
                )

                # Serializa e salva no MCP usando patch_mcp
                serializable_data = convert_numpy_types(
                    updated_transformer_data, debug_path="short_circuit_calculate_currents"
                )
                if patch_mcp("transformer-inputs-store", serializable_data, app_instance):
                    log.info("[Short Circuit] MCP atualizado com correntes calculadas.")
                else:
                    log.warning("[Short Circuit] Nenhum dado válido para atualizar no MCP")

                # Obtém a corrente nominal calculada
                if side == "AT":
                    corrente_nominal_a = calculated_currents.get("corrente_nominal_at")
                elif side == "BT":
                    corrente_nominal_a = calculated_currents.get("corrente_nominal_bt")
                else:
                    corrente_nominal_a = calculated_currents.get("corrente_nominal_terciario")

            # Verifica se a corrente nominal é válida
            if corrente_nominal_a is None or corrente_nominal_a <= 0:
                log.error(
                    f"[Short Circuit] Corrente nominal para lado {side} inválida ou não calculada: {corrente_nominal_a}"
                )
                errors.append(f"Corrente nominal para lado {side} inválida ou não calculada.")
                error_msg = html.Ul(
                    [html.Li(e) for e in errors], style={"color": "red", "fontSize": "0.7rem"}
                )
                return None, None, None, "-", empty_fig, error_msg, no_update

            # Converte para float para uso nos cálculos
            corrente_nominal_a = float(corrente_nominal_a)

            # --- Cálculos Principais ---
            isc_sym_ka, isc_peak_ka = calculate_short_circuit_params(
                corrente_nominal_a, impedancia_pu, k_peak_factor
            )
            delta_z_percent = calculate_impedance_variation(z_before, z_after)

            # --- Verificação do Critério ---
            limit = constants.IMPEDANCE_VARIATION_LIMITS.get(category)
            limit_text = f"Cat.{category} (±{limit:.1f}%)" if limit is not None else "Cat. Inválida"
            status_str = "Indeterminado"
            status_style_to_use = WARNING_STYLE  # Default to warning style

            if delta_z_percent is None:
                status_str = "Erro no cálculo ΔZ"
                status_style_to_use = FAIL_STYLE
            elif limit is None:
                status_str = "Limite não definido (Cat?)"
            elif abs(delta_z_percent) <= limit:
                status_str = "APROVADO"
                status_style_to_use = PASS_STYLE
            else:
                status_str = "REPROVADO"
                status_style_to_use = FAIL_STYLE

            status_children = html.Span(
                f"ΔZ={delta_z_percent:.2f}% | {status_str}", style=status_style_to_use
            )

            # ---- Criar Gráfico ----
            fig = create_empty_sc_figure()  # Start with empty
            if delta_z_percent is not None and limit is not None and limit > 0:
                df_graph = pd.DataFrame(
                    {
                        "Métrica": ["Variação Medida (ΔZ)", "Limite Superior", "Limite Inferior"],
                        "Valor (%)": [delta_z_percent, limit, -limit],
                        "Tipo": ["Medido", "Limite", "Limite"],
                    }
                )
                fig = px.bar(
                    df_graph,
                    x="Métrica",
                    y="Valor (%)",
                    color="Tipo",
                    title=f"Variação da Impedância vs Limite ({limit_text})",
                    color_discrete_map={
                        "Medido": colors.get("primary", "royalblue"),
                        "Limite": colors.get("fail", "firebrick"),
                    },
                    text="Valor (%)",
                    height=300,
                )
                fig.update_traces(
                    texttemplate="%{y:.2f}%", textposition="outside", cliponaxis=False
                )
                fig.update_layout(
                    template="plotly_white",
                    yaxis_title="Variação (%)",
                    xaxis_title="",
                    legend_title_text="",
                    yaxis_range=[-limit * 1.5 - 1, limit * 1.5 + 1],
                    margin=dict(t=50, b=10, l=10, r=10),
                    title_font_size=12,
                    font_size=10,
                )

            # --- Preparar Dados para Store ---
            # Estrutura de dados para o store
            store_data = current_store_data.copy() if current_store_data else {}

            # Adicionar inputs
            store_data["inputs_curto_circuito"] = {
                "impedance_before": z_before,
                "impedance_after": z_after,
                "peak_factor": k_peak_factor,
                "isc_side": side,
                "category": category,
                "timestamp": datetime.datetime.now().isoformat(),
            }

            # Adicionar resultados
            store_data["resultados_curto_circuito"] = {
                "isc_sym_kA": isc_sym_ka,
                "isc_peak_kA": isc_peak_ka,
                "delta_impedance_percent": delta_z_percent,
                "status_text": status_str,
                "limit_used": limit,
                "category": category,
                "timestamp": datetime.datetime.now().isoformat(),
            }

            # Adicionar os inputs específicos para curto-circuito conforme solicitado
            inputs_curto_circuito = {
                "z_antes": z_before,
                "z_depois": z_after,
                "fator_pico": k_peak_factor,
                "lado": side,
                "categoria": category,
            }

            # Adicionar os inputs específicos para curto-circuito no store
            if "inputs_curto_circuito_especificos" not in store_data:
                store_data["inputs_curto_circuito_especificos"] = {}
            store_data["inputs_curto_circuito_especificos"].update(inputs_curto_circuito)

            # Converter para tipos serializáveis
            store_data = convert_numpy_types(store_data, debug_path="short_circuit_calculate")

            log.info(
                f"Cálculo de curto-circuito concluído: ΔZ={delta_z_percent:.2f}%, Status={status_str}"
            )

            # Retornar resultados para a UI
            return (
                isc_sym_ka,  # Isc Simétrica (kA)
                isc_peak_ka,  # Isc Pico (kA)
                f"{delta_z_percent:.2f}",  # Variação Z (%)
                status_children,  # Status (APROVADO/REPROVADO)
                fig,  # Gráfico de barras
                "",  # Mensagem de erro (vazia se sucesso)
                store_data,  # Store com resultados
            )

        except Exception as e:
            log.error(f"Erro no cálculo de curto-circuito: {e}")
            error_msg = html.Div(
                [
                    html.P("Erro no cálculo de curto-circuito:"),
                    html.Pre(str(e)),
                ],
                style={"color": "red", "fontSize": "0.7rem"},
            )
            return None, None, None, "-", empty_fig, error_msg, no_update
