# callbacks/short_circuit_fix.py
"""
Versão corrigida do módulo short_circuit que usa o padrão de registro centralizado.
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
# from app import app  # REMOVIDO
from utils import constants  # Para limites de variação de impedância
from utils.callback_helpers import safe_float
from utils.mcp_utils import patch_mcp  # Importar função patch_mcp
from utils.store_diagnostics import convert_numpy_types
from utils.validators import validate_dict_inputs_enhanced as validate_dict_inputs  # Para validação

# Importar módulo de debug
try:
    from callbacks.short_circuit_debug import add_short_circuit_debug_logs

    DEBUG_ENABLED = True
except ImportError:
    # Se o módulo não existir, criar uma função dummy
    def add_short_circuit_debug_logs(original_inputs, results, current_store_data):
        return current_store_data

    DEBUG_ENABLED = False

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
        ],  # Triggered when store data is loaded/changed or URL changes
        prevent_initial_call=False,  # Allow running on initial load
    )
    def short_circuit_load_data(stored_data, pathname):
        """Carrega os dados da aba Curto-Circuito armazenados no dcc.Store."""
        ctx_triggered = ctx.triggered_id
        log.debug(f"load_short_circuit_data triggered by: {ctx_triggered}")
        print("\n\n***** [LOAD ShortCircuit] CALLBACK INICIADO *****")
        print(f"[LOAD ShortCircuit] Trigger: {ctx_triggered}")
        print(f"[LOAD ShortCircuit] Pathname: {pathname}")

        # Se o callback foi disparado pela URL, verifica se estamos na página correta
        if ctx_triggered == "url":
            # Normaliza o pathname para remover barras extras
            if pathname is None:
                raise PreventUpdate

            clean_path = pathname.strip("/")

            # Verifica se estamos na página de curto-circuito
            if clean_path != "curto-circuito":
                raise PreventUpdate

        print(f"[LOAD ShortCircuit] Stored data: {stored_data}")

        if not stored_data or not isinstance(stored_data, dict):
            log.debug("Short-circuit store is empty or invalid. Returning defaults.")
            # Return default values for all outputs
            return None, None, 2.55, "AT", None, None, None, None, "-", create_empty_sc_figure(), ""

        log.debug("Loading short-circuit data from store.")
        inputs = stored_data.get("inputs_curto_circuito", {})
        results = stored_data.get("resultados_curto_circuito", {})

        # Extract input values with defaults
        z_before = inputs.get("impedance_before")
        z_after = inputs.get("impedance_after")
        peak_factor = inputs.get("peak_factor", 2.55)
        isc_side = inputs.get("isc_side", "AT")
        category = inputs.get("category")

        # Extract result values
        isc_sym = results.get("isc_sym_kA")
        isc_peak = results.get("isc_peak_kA")
        delta_z = results.get("delta_impedance_percent")
        status_text = results.get("status_text", "-")  # Status textual (APROVADO/REPROVADO/etc.)
        limit = results.get("limit_used")  # Limite numérico usado

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
                limit_text = f"Cat.{category or results.get('category','?')} (±{limit:.1f}%)"
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

        print(
            f"[LOAD ShortCircuit] Returning values: z_before={z_before}, z_after={z_after}, delta_z={delta_z}"
        )
        print(f"[LOAD ShortCircuit] Returning figure: {fig}")

        return (
            z_before,
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

            # Pega dados do transformador (garantidos que existem e são válidos)
            potencia_mva = float(transformer_data["potencia_mva"])
            impedancia_nominal_percent = float(transformer_data["impedancia"])
            impedancia_pu = impedancia_nominal_percent / 100.0
            tipo = transformer_data.get("tipo_transformador", "Trifásico")
            sqrt_3 = math.sqrt(3) if tipo == "Trifásico" else 1.0

            # Pega corrente nominal do lado selecionado
            corrente_nominal_a = None

            # Primeiro tenta obter do dicionário de dados do transformador
            if side == "AT":
                corrente_nominal_a = transformer_data.get("corrente_nominal_at")
            elif side == "BT":
                corrente_nominal_a = transformer_data.get("corrente_nominal_bt")
            else:
                corrente_nominal_a = transformer_data.get("corrente_nominal_terciario")

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

            # --- Armazenar Resultados ---
            results = {
                "isc_sym_kA": round(isc_sym_ka, 2) if isc_sym_ka is not None else None,
                "isc_peak_kA": round(isc_peak_ka, 2) if isc_peak_ka is not None else None,
                "delta_impedance_percent": round(delta_z_percent, 2)
                if delta_z_percent is not None
                else None,
                "limit_used": limit,
                "status_text": status_str,  # Armazena o status textual
            }
            if current_store_data is None:
                current_store_data = {}
            # Salva inputs originais E resultados
            original_inputs = {
                "impedance_before": z_before_str,
                "impedance_after": z_after_str,
                "peak_factor": k_peak_factor_str,
                "isc_side": side,
                "category": category,
            }
            current_store_data["inputs_curto_circuito"] = original_inputs
            current_store_data["resultados_curto_circuito"] = results
            current_store_data["timestamp"] = datetime.datetime.now().isoformat()

            # Armazenar o gráfico no store para persistência
            current_store_data["graph_figure"] = fig

            print(f"[CALC ShortCircuit] Stored data: {current_store_data}")

            log.info("Cálculo de Curto-Circuito concluído.")
            # Limpa mensagem de erro e retorna resultados
            return (
                round(isc_sym_ka, 2) if isc_sym_ka else None,
                round(isc_peak_ka, 2) if isc_peak_ka else None,
                round(delta_z_percent, 2) if delta_z_percent else None,
                status_children,
                fig,
                "",
                current_store_data,
            )

        # --- Tratamento de Erros ---
        except ValueError as e:
            log.warning(f"Erro de valor no cálculo de curto-circuito: {e}")
            error_message = f"Erro: {e}"
            return None, None, None, "-", empty_fig, error_message, no_update
        except Exception as e:
            log.exception("Erro inesperado no cálculo de curto-circuito.")
            error_message = f"Erro inesperado: {e}"
            return None, None, None, "-", empty_fig, error_message, no_update

    log.info(
        f"Todos os callbacks do módulo short_circuit registrados com sucesso para app {app_instance.title}."
    )
    return True
