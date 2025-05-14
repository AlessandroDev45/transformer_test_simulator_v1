
# callbacks/dieletric_analysis.py
import datetime
import logging
import time  # Add time for precise logging

import dash_bootstrap_components as dbc
import numpy as np
from dash import ALL, Input, Output, State, callback, ctx, html, no_update
from dash.exceptions import PreventUpdate

import config

# Importações da aplicação
from app import app
from app_core.standards import VerificadorTransformador, safe_float_convert
from utils.mcp_utils import patch_mcp  # Importar função patch_mcp

# Importar constantes de rota
from utils.routes import ROUTE_DIELECTRIC_ANALYSIS, normalize_pathname
from utils.store_diagnostics import convert_numpy_types

log = logging.getLogger(__name__)

# Cache de dados do transformador é gerenciado centralmente em outro lugar


# --- Helper Function to Get Verificador Instance (mantido) ---
def get_verificador_instance() -> VerificadorTransformador | None:
    """Instantiates VerificadorTransformador, handling potential errors."""
    try:
        verificador = VerificadorTransformador()
        if not verificador.is_valid():
            log.error("Instância VerificadorTransformador criada, mas inválida (falha dados?).")
            return None
        log.debug("Instância VerificadorTransformador criada com sucesso.")
        return verificador
    except Exception as e:
        log.critical(f"Erro CRÍTICO ao instanciar VerificadorTransformador: {e}", exc_info=True)
        return None


# --- Callbacks de Atualização de Opções e Cálculos (Mantidos como estavam) ---


# Callback para mostrar/ocultar opções de neutro
@app.callback(
    Output({"type": "div-neutro", "index": ALL}, "style"),
    [
        Input({"type": "conexao", "index": ALL}, "value"),
        Input("url", "pathname"),
    ],  # Adicionado para garantir que seja executado quando a página carrega
    prevent_initial_call=False,  # Executado na carga inicial
)
def dieletric_analysis_toggle_neutro_visibility(conexoes, pathname=None):
    if not conexoes:
        return no_update
    log.debug(f"Toggle Neutro: Conexões={conexoes}, pathname={pathname}")

    # Estilo para quando o neutro deve ser visível - consistente com os demais campos
    neutro_visible_style = {"display": "block", "marginBottom": "0.5rem"}

    # Estilo para quando o neutro deve estar oculto
    neutro_hidden_style = {"display": "none"}

    # Gera os estilos com base nas conexões
    styles = []
    for i, c in enumerate(conexoes):
        if c == "YN":
            log.info(f"Conexão YN detectada no índice {i}, mostrando campos de neutro")
            styles.append(neutro_visible_style)
        else:
            styles.append(neutro_hidden_style)

    # Garante que retornamos uma lista do tamanho certo se conexoes for menor que o esperado
    num_outputs = len(ctx.outputs_list[0]) if ctx.outputs_list and ctx.outputs_list[0] else 0
    while len(styles) < num_outputs:
        styles.append(neutro_hidden_style)  # Adiciona estilos ocultos se necessário

    log.info(f"Estilos de neutro gerados: {styles}")
    return styles[:num_outputs]


# Callback para atualizar opções de IA
@app.callback(
    Output({"type": "ia", "index": ALL}, "options"),
    Input({"type": "um", "index": ALL}, "value"),
    State("tipo-isolamento", "children"),
    prevent_initial_call=True,
)
def dieletric_analysis_update_ia_options(um_values, tipo_isolamento):
    num_outputs = (
        len(ctx.outputs_list[0])
        if ctx.outputs_list and ctx.outputs_list[0]
        else len(um_values)
        if um_values
        else 0
    )
    if num_outputs == 0:
        return no_update
    verificador = get_verificador_instance()
    if verificador is None:
        return [[] for _ in range(num_outputs)]
    tipo_isolamento = tipo_isolamento or "uniforme"
    options_list = []
    for um in um_values:
        opcoes_ia = []
        if um:
            try:
                nbr_ia_vals = verificador.nbr.get_impulso_atm_values(um)
                ieee_ia_vals = verificador.ieee.get_bil_values(um)
                nbr_ia_floats = {
                    safe_float_convert(v) for v in nbr_ia_vals if safe_float_convert(v) is not None
                }
                ieee_ia_floats = {
                    safe_float_convert(v) for v in ieee_ia_vals if safe_float_convert(v) is not None
                }
                valores_combinados_floats = sorted(list(nbr_ia_floats.union(ieee_ia_floats)))
                for valor in valores_combinados_floats:
                    fonte = []
                    if any(vf is not None and np.isclose(vf, valor) for vf in nbr_ia_floats):
                        fonte.append("NBR")
                    if any(vf is not None and np.isclose(vf, valor) for vf in ieee_ia_floats):
                        fonte.append("IEEE")
                    label = f"{valor:.0f} kV ({'/'.join(fonte)})" if fonte else f"{valor:.0f} kV"
                    value_str = (
                        str(int(valor)) if np.isclose(valor, round(valor)) else str(valor)
                    )  # Garante string
                    opcoes_ia.append({"label": label, "value": value_str})
            except Exception as e:
                log.exception(f"Erro opções IA (Um={um}, Isol={tipo_isolamento}): {e}")
        options_list.append(opcoes_ia)
    while len(options_list) < num_outputs:
        options_list.append([])
    return options_list[:num_outputs]


# Callback para atualizar opções de IA Neutro
@app.callback(
    Output({"type": "impulso-atm-neutro", "index": ALL}, "options"),
    Input({"type": "neutro-um", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def dieletric_analysis_update_ia_neutro_options(neutro_um_values):
    num_outputs = (
        len(ctx.outputs_list[0])
        if ctx.outputs_list and ctx.outputs_list[0]
        else len(neutro_um_values)
        if neutro_um_values
        else 0
    )
    if num_outputs == 0:
        return no_update
    verificador = get_verificador_instance()
    if verificador is None:
        return [[] for _ in range(num_outputs)]
    options_list = []
    for um_neutro in neutro_um_values:
        opcoes_ia_neutro = []
        if um_neutro:
            try:
                nbr_ia_vals = verificador.nbr.get_impulso_atm_values(um_neutro)
                for v in nbr_ia_vals:
                    v_float = safe_float_convert(v)
                    if v_float is not None:
                        value_str = (
                            str(int(v_float))
                            if np.isclose(v_float, round(v_float))
                            else str(v_float)
                        )
                        opcoes_ia_neutro.append(
                            {"label": f"{v_float:.0f} kV (NBR)", "value": value_str}
                        )
            except Exception as e:
                log.exception(f"Erro opções IA Neutro (Um={um_neutro}): {e}")
        options_list.append(opcoes_ia_neutro)
    while len(options_list) < num_outputs:
        options_list.append([])
    return options_list[:num_outputs]


# Callback para atualizar opções de IM
@app.callback(
    Output({"type": "im", "index": ALL}, "options"),
    [Input({"type": "um", "index": ALL}, "value"), Input({"type": "ia", "index": ALL}, "value")],
    State("tipo-isolamento", "children"),
    prevent_initial_call=True,
)
def dieletric_analysis_update_im_options(um_values, ia_values, tipo_isolamento):
    num_outputs = (
        len(ctx.outputs_list[0])
        if ctx.outputs_list and ctx.outputs_list[0]
        else len(um_values)
        if um_values
        else 0
    )
    if num_outputs == 0:
        return no_update
    verificador = get_verificador_instance()
    if verificador is None:
        return [[] for _ in range(num_outputs)]
    tipo_isolamento = tipo_isolamento or "uniforme"
    options_list = []
    na_option = [{"label": "Não Aplicável", "value": "na"}]
    if len(ia_values) < len(um_values):
        ia_values = list(ia_values) + [None] * (len(um_values) - len(ia_values))
    for um, ia in zip(um_values, ia_values):
        opcoes_im = []
        if um:
            try:
                um_float = safe_float_convert(um)
                if um_float is None:
                    options_list.append([])
                    continue
                nbr_im_vals = verificador.nbr.get_impulso_man_values(um, ia)
                is_na_nbr = "na" in nbr_im_vals
                ieee_im_val = (
                    verificador.ieee.get_test_levels(um).get("switching")
                    if verificador.ieee.get_test_levels(um)
                    else None
                )
                nbr_im_floats = {
                    safe_float_convert(v)
                    for v in nbr_im_vals
                    if v != "na" and safe_float_convert(v) is not None
                }
                ieee_im_float = safe_float_convert(ieee_im_val)
                valores_combinados_floats = nbr_im_floats.copy()
                if ieee_im_float is not None:
                    valores_combinados_floats.add(ieee_im_float)
                valores_filtrados = sorted(list(valores_combinados_floats))
                ia_float = safe_float_convert(ia)
                if tipo_isolamento == "progressivo" and um_float >= 245 and ia_float is not None:
                    limite_minimo = ia_float * 0.7
                    valores_filtrados_prog = [v for v in valores_filtrados if v >= limite_minimo]
                    if valores_filtrados_prog:
                        valores_filtrados = valores_filtrados_prog
                for valor in valores_filtrados:
                    fonte = []
                    if any(vf is not None and np.isclose(vf, valor) for vf in nbr_im_floats):
                        fonte.append("NBR")
                    if ieee_im_float is not None and np.isclose(ieee_im_float, valor):
                        fonte.append("IEEE")
                    label = f"{valor:.0f} kV ({'/'.join(fonte)})" if fonte else f"{valor:.0f} kV"
                    value_str = str(int(valor)) if np.isclose(valor, round(valor)) else str(valor)
                    opcoes_im.append({"label": label, "value": value_str})
                if is_na_nbr and ieee_im_float is None:
                    opcoes_im = na_option + opcoes_im
                elif is_na_nbr and ieee_im_float is not None:
                    opcoes_im = na_option + opcoes_im
                elif not is_na_nbr and not opcoes_im:
                    opcoes_im = na_option
            except Exception as e:
                log.exception(f"Erro opções IM (Um={um}, IA={ia}): {e}")
                opcoes_im = na_option
        options_list.append(opcoes_im)
    while len(options_list) < num_outputs:
        options_list.append([])
    return options_list[:num_outputs]


# Callback para atualizar opções de Tensão Aplicada/Curta Duração
@app.callback(
    Output({"type": "tensao-curta", "index": ALL}, "options"),
    [
        Input({"type": "um", "index": ALL}, "value"),
        Input({"type": "conexao", "index": ALL}, "value"),
        Input({"type": "neutro-um", "index": ALL}, "value"),
    ],
    State("tipo-isolamento", "children"),
    prevent_initial_call=True,
)
def dieletric_analysis_update_tensao_curta_options(
    um_values, conexoes, neutro_um_values, tipo_isolamento
):
    num_outputs = (
        len(ctx.outputs_list[0])
        if ctx.outputs_list and ctx.outputs_list[0]
        else len(um_values)
        if um_values
        else 0
    )
    if num_outputs == 0:
        return no_update
    verificador = get_verificador_instance()
    if verificador is None:
        return [[] for _ in range(num_outputs)]
    tipo_isolamento = tipo_isolamento or "uniforme"
    options_list = []
    if len(conexoes) < len(um_values):
        conexoes = list(conexoes) + [None] * (len(um_values) - len(conexoes))
    if len(neutro_um_values) < len(um_values):
        neutro_um_values = list(neutro_um_values) + [None] * (
            len(um_values) - len(neutro_um_values)
        )
    for i, um in enumerate(um_values):
        opcoes_tc = []
        if um:
            conexao = conexoes[i]
            neutro_um = neutro_um_values[i]
            try:
                nbr_tc_vals = verificador.nbr.get_tensao_curta_values(um, conexao, neutro_um)
                ieee_tc_val = (
                    verificador.ieee.get_test_levels(um).get("applied")
                    if verificador.ieee.get_test_levels(um)
                    else None
                )
                nbr_tc_floats = {
                    safe_float_convert(v) for v in nbr_tc_vals if safe_float_convert(v) is not None
                }
                ieee_tc_float = safe_float_convert(ieee_tc_val)
                valores_combinados_floats = nbr_tc_floats.copy()
                if ieee_tc_float is not None:
                    valores_combinados_floats.add(ieee_tc_float)
                valores_filtrados = sorted(list(valores_combinados_floats))
                # (Filtragem por isolamento progressivo pode ser adicionada aqui)
                for valor in valores_filtrados:
                    fonte = []
                    if any(vf is not None and np.isclose(vf, valor) for vf in nbr_tc_floats):
                        fonte.append("NBR")
                    if ieee_tc_float is not None and np.isclose(ieee_tc_float, valor):
                        fonte.append("IEEE")
                    label = f"{valor:.0f} kV ({'/'.join(fonte)})" if fonte else f"{valor:.0f} kV"
                    value_str = str(int(valor)) if np.isclose(valor, round(valor)) else str(valor)
                    opcoes_tc.append({"label": label, "value": value_str})
            except Exception as e:
                log.exception(f"Erro opções T.Curta (Um={um}, Isol={tipo_isolamento}): {e}")
        options_list.append(opcoes_tc)
    while len(options_list) < num_outputs:
        options_list.append([])
    return options_list[:num_outputs]


# Callback consolidado para calcular IAC para todos os enrolamentos
@app.callback(
    Output({"type": "impulso-atm-cortado", "index": ALL}, "value"),
    Input({"type": "ia", "index": ALL}, "value"),
    prevent_initial_call=False,
)
def dieletric_analysis_update_iac(ia_values):
    """Calcula o valor de IAC como 1.1 vezes o valor de IA/BIL para todos os enrolamentos."""
    log.info(f"[IAC CALC] Calculando IAC para todos os enrolamentos com IA={ia_values}")

    results = []
    for ia in ia_values:
        if not ia or ia == "na":
            results.append("")
            continue

        try:
            ia_float = safe_float_convert(ia)
            if ia_float is not None:
                iac_float = ia_float * 1.1
                result = f"{iac_float:.1f} kV"
                results.append(result)
            else:
                log.warning(f"[IAC CALC] Não foi possível converter IA={ia} para float")
                results.append("")
        except Exception as e:
            log.exception(f"[IAC CALC] Erro: {e}")
            results.append("")

    log.info(f"[IAC CALC] Resultados: {results}")
    return results


# Callback para calcular Espaçamentos
@app.callback(
    [
        Output({"type": "espacamentos-nbr", "index": ALL}, "children"),
        Output({"type": "espacamentos-ieee", "index": ALL}, "children"),
    ],
    [
        Input({"type": "um", "index": ALL}, "value"),
        Input({"type": "ia", "index": ALL}, "value"),
        Input({"type": "im", "index": ALL}, "value"),
    ],
    State("transformer-inputs-store", "data"),
    prevent_initial_call=True,
)
def dieletric_analysis_update_espacamentos_display(
    um_values, ia_values, im_values, transformer_data
):
    """Atualiza a exibição de espaçamentos NBR e IEEE com base nos valores de entrada."""
    try:
        log.info(f"Atualizando espaçamentos: Um={um_values}, IA={ia_values}, IM={im_values}")

        # Determina o número de saídas necessárias
        num_outputs_nbr = (
            len(ctx.outputs_list[0]) if ctx.outputs_list and ctx.outputs_list[0] else 0
        )
        num_outputs_ieee = (
            len(ctx.outputs_list[1]) if ctx.outputs_list and ctx.outputs_list[1] else 0
        )
        num_outputs = max(num_outputs_nbr, num_outputs_ieee, len(um_values) if um_values else 0)

        if num_outputs == 0:
            log.warning("Nenhuma saída necessária para espaçamentos.")
            return no_update, no_update

        # Cores e estilos padrão
        default_error_color = config.colors.get("fail", "red")
        default_muted_color = config.colors.get("text_muted", "grey")

        # Obtém instância do verificador
        verificador = get_verificador_instance()
        if verificador is None:
            log.error("Verificador não inicializado para cálculo de espaçamentos.")
            no_data_msg = html.P(
                "Erro Verif.", style={"fontSize": "0.7rem", "color": default_error_color}
            )
            return ([no_data_msg] * num_outputs, [no_data_msg] * num_outputs)

        # Determina o tipo de transformador
        tipo_transformador_geral = (
            transformer_data.get("tipo_transformador", "Trifásico")
            if transformer_data and isinstance(transformer_data, dict)
            else "Trifásico"
        )
        transformer_type_ieee = (
            "power" if tipo_transformador_geral == "Trifásico" else "distribution"
        )
        log.info(
            f"Tipo de transformador para espaçamentos: {tipo_transformador_geral} (IEEE: {transformer_type_ieee})"
        )

        # Inicializa listas de resultados
        esp_nbr_list = []
        esp_ieee_list = []

        # Garante que as listas de entrada tenham o mesmo tamanho
        if len(ia_values) < len(um_values):
            ia_values = list(ia_values) + [None] * (len(um_values) - len(ia_values))
        if len(im_values) < len(um_values):
            im_values = list(im_values) + [None] * (len(um_values) - len(im_values))

        # Processa cada conjunto de valores
        for i, (um, ia, im) in enumerate(zip(um_values, ia_values, im_values)):
            nbr_display = ""
            ieee_display = ""

            if um:
                try:
                    log.info(
                        f"Calculando espaçamentos para enrolamento {i}: Um={um}, IA={ia}, IM={im}"
                    )
                    resultados = verificador.get_clearances(um, transformer_type_ieee, ia, im)

                    # Processa dados NBR
                    nbr_data = resultados.get("NBR")
                    if nbr_data:
                        log.debug(f"Dados NBR encontrados: {nbr_data}")
                        nbr_display = html.Div(
                            [
                                html.Strong("NBR:", style={"fontSize": "0.7rem"}),
                                html.P(
                                    f"F-T: {nbr_data.get('fase_terra', '-')} | F-F: {nbr_data.get('fase_fase', '-')} | Outro: {nbr_data.get('outro_enrolamento', '-')} mm",
                                    style={"fontSize": "0.7rem", "marginBottom": "0.1rem"},
                                ),
                            ]
                        )
                    else:
                        log.warning(f"Nenhum dado NBR encontrado para Um={um}")
                        nbr_display = html.P(
                            "NBR: N/A", style={"fontSize": "0.7rem", "color": default_muted_color}
                        )

                    # Processa dados IEEE
                    ieee_data = resultados.get("IEEE")
                    if ieee_data:
                        log.debug(f"Dados IEEE encontrados: {ieee_data}")
                        clearance_key = (
                            "internal_clearance_phase_ground"
                            if transformer_type_ieee == "power"
                            else "clearance"
                        )
                        strike_key = (
                            "internal_strike_phase_ground"
                            if transformer_type_ieee == "power"
                            else None
                        )

                        clearance_val = ieee_data.get(clearance_key, "-")
                        strike_val = ieee_data.get(strike_key, "-") if strike_key else None

                        ieee_parts = [f"Clearance: {clearance_val} mm"]
                        if strike_val and strike_val != "-":
                            ieee_parts.append(f"Strike: {strike_val} mm")

                        ieee_display = html.Div(
                            [
                                html.Strong("IEEE:", style={"fontSize": "0.7rem"}),
                                html.P(
                                    " | ".join(ieee_parts),
                                    style={"fontSize": "0.7rem", "marginBottom": "0.1rem"},
                                ),
                            ]
                        )
                    else:
                        log.warning(f"Nenhum dado IEEE encontrado para Um={um}")
                        ieee_display = html.P(
                            "IEEE: N/A", style={"fontSize": "0.7rem", "color": default_muted_color}
                        )

                except Exception as e:
                    log.exception(
                        f"Erro ao calcular espaçamentos para Um={um}, IA={ia}, IM={im}: {e}"
                    )
                    error_msg = html.P(
                        "Erro Calc.", style={"fontSize": "0.7rem", "color": default_error_color}
                    )
                    nbr_display = error_msg
                    ieee_display = error_msg
            else:
                log.debug(f"Nenhum valor Um para enrolamento {i}, usando placeholders")
                nbr_display = html.P(
                    "NBR: -", style={"fontSize": "0.7rem", "color": default_muted_color}
                )
                ieee_display = html.P(
                    "IEEE: -", style={"fontSize": "0.7rem", "color": default_muted_color}
                )

            # Adiciona os resultados às listas
            esp_nbr_list.append(nbr_display)
            esp_ieee_list.append(ieee_display)

        # Garante que as listas de saída tenham o tamanho correto
        default_placeholder = html.P(
            "-", style={"fontSize": "0.7rem", "color": default_muted_color}
        )
        while len(esp_nbr_list) < num_outputs:
            esp_nbr_list.append(default_placeholder)
        while len(esp_ieee_list) < num_outputs:
            esp_ieee_list.append(default_placeholder)

        log.info(
            f"Espaçamentos calculados com sucesso: {len(esp_nbr_list)} NBR, {len(esp_ieee_list)} IEEE"
        )
        return esp_nbr_list[:num_outputs], esp_ieee_list[:num_outputs]

    except Exception as e:
        log.exception(f"Erro crítico no callback de espaçamentos: {e}")
        default_error = html.P("Erro", style={"fontSize": "0.7rem", "color": "red"})
        num_outputs = max(3, len(um_values) if um_values else 0)
        return [default_error] * num_outputs, [default_error] * num_outputs


# Callback para exibir o tipo de transformador
@app.callback(
    [
        Output("display-tipo-transformador-dieletric", "children"),
        Output("tipo_transformador", "value"),
    ],
    Input("transformer-inputs-store", "data"),
)
def display_transformer_type_readonly(transformer_data):
    if transformer_data and isinstance(transformer_data, dict):
        tipo = transformer_data.get("tipo_transformador", "Trifásico")
        return tipo, tipo
    return "-", "Trifásico"


# Preenchimento automático substituído pelo botão "Preencher Campos"
def populate_dielectric_fields(pathname_input, transformer_data, pathname_state):
    """
    Preenche automaticamente os campos da análise dielétrica com base nos dados do transformador.
    Acionado pela navegação para a página OU pela atualização dos dados básicos.
    Verifica se está na página correta antes de atualizar.
    """
    start_time = time.perf_counter()
    triggered_id = ctx.triggered_id if ctx.triggered else "Initial Load / No Trigger"
    current_pathname = (
        pathname_state if triggered_id == "transformer-inputs-store" else pathname_input
    )
    log.info(
        f"[POPULATE START @ {start_time:.4f}] Trigger: {triggered_id}, Pathname: {current_pathname}"
    )

    if not current_pathname:
        raise PreventUpdate
    clean_path = normalize_pathname(current_pathname)
    if clean_path != ROUTE_DIELECTRIC_ANALYSIS:
        log.debug(
            f"[POPULATE @ {time.perf_counter():.4f}] Não na página '{ROUTE_DIELECTRIC_ANALYSIS}'. Prevenindo update."
        )
        raise PreventUpdate

    log.info(f"[POPULATE @ {time.perf_counter():.4f}] Na página correta '{clean_path}'.")

    if not transformer_data or not isinstance(transformer_data, dict):
        log.warning(f"[POPULATE @ {time.perf_counter():.4f}] Dados inválidos. Retornando Nones.")
        return [None] * 13

    log.info(
        f"   -> [VERIFICANDO STORE @ {time.perf_counter():.4f}]: Keys={list(transformer_data.keys())}"
    )
    # Adicionar logs específicos das chaves aqui se necessário...

    # --- Lógica de Processamento (Robusta) ---
    um_at, um_bt, um_terciario = None, None, None
    conexao_at, conexao_bt, conexao_terciario = None, None, None
    nbi_at, nbi_bt, nbi_terciario = None, None, None
    sil_at, sil_bt, sil_terciario = None, None, None
    tipo_isolamento = transformer_data.get("tipo_isolamento", "uniforme")

    def safe_str_output(value):
        if value is None or value == "":
            return None
        try:
            f_val = float(value)
            if np.isclose(f_val, round(f_val)):
                return str(int(f_val))
        except (ValueError, TypeError):
            pass
        return str(value)

    verificador = get_verificador_instance()  # Para fallback de Um

    um_at = safe_str_output(transformer_data.get("classe_tensao_at"))
    if um_at is None and transformer_data.get("tensao_at"):
        try:
            tensao_at_f = float(transformer_data.get("tensao_at"))
            um_at = (
                verificador.get_nearest_um_value(tensao_at_f) if verificador else str(tensao_at_f)
            )
        except (ValueError, TypeError):
            pass

    um_bt = safe_str_output(transformer_data.get("classe_tensao_bt"))
    if um_bt is None and transformer_data.get("tensao_bt"):
        try:
            tensao_bt_f = float(transformer_data.get("tensao_bt"))
            um_bt = (
                verificador.get_nearest_um_value(tensao_bt_f) if verificador else str(tensao_bt_f)
            )
        except (ValueError, TypeError):
            pass

    um_terciario = safe_str_output(transformer_data.get("classe_tensao_terciario"))
    if um_terciario is None and transformer_data.get("tensao_terciario"):
        try:
            tensao_ter_f = float(transformer_data.get("tensao_terciario"))
            um_terciario = (
                verificador.get_nearest_um_value(tensao_ter_f) if verificador else str(tensao_ter_f)
            )
        except (ValueError, TypeError):
            pass

    def determine_connection(conn_key, neutral_volt_key):
        connection_stored = transformer_data.get(conn_key)
        default_conn = (
            "estrela" if "at" in conn_key else ("triangulo" if "bt" in conn_key else None)
        )
        if not connection_stored or not isinstance(connection_stored, str):
            connection_stored = default_conn
            if connection_stored is None:
                return None
        conn_lower = connection_stored.lower()

        # Verifica se é estrela sem neutro (Y)
        if conn_lower == "estrela_sem_neutro":
            return "Y"
        # Verifica se é estrela com neutro (YN) ou estrela sem especificação
        elif "estrela" in conn_lower or "star" in conn_lower or conn_lower.startswith("y"):
            neutral_voltage = transformer_data.get(neutral_volt_key)
            try:
                if neutral_voltage is not None and str(neutral_voltage).strip() != "":
                    if safe_float_convert(neutral_voltage) > 0:
                        return "YN"
            except:
                pass
            return "Y"
        # Verifica se é triângulo (D)
        elif "triangulo" in conn_lower or "delta" in conn_lower or conn_lower.startswith("d"):
            return "D"
        else:
            if default_conn == "estrela":
                return "Y"
            if default_conn == "triangulo":
                return "D"
            return None

    conexao_at = determine_connection("conexao_at", "tensao_bucha_neutro_at")
    conexao_bt = determine_connection("conexao_bt", "tensao_bucha_neutro_bt")
    conexao_terciario = determine_connection("conexao_terciario", "tensao_bucha_neutro_terciario")

    nbi_at = safe_str_output(transformer_data.get("nbi_at"))
    nbi_bt = safe_str_output(transformer_data.get("nbi_bt"))
    nbi_terciario = safe_str_output(transformer_data.get("nbi_terciario"))
    sil_at = safe_str_output(transformer_data.get("sil_at"))
    sil_bt = safe_str_output(transformer_data.get("sil_bt"))
    sil_terciario = safe_str_output(transformer_data.get("sil_terciario"))
    # --- Fim Lógica ---

    end_time = time.perf_counter()
    valores_retorno = [
        um_at,
        um_bt,
        um_terciario,
        conexao_at,
        conexao_bt,
        conexao_terciario,
        nbi_at,
        nbi_bt,
        nbi_terciario,
        sil_at,
        sil_bt,
        sil_terciario,
        tipo_isolamento,
    ]
    log.info(
        f"[POPULATE END @ {end_time:.4f}] Duração: {(end_time - start_time)*1000:.2f} ms. Retornando: {valores_retorno}"
    )

    return tuple(valores_retorno)


# --- Callback para Preenchimento Automático ao Carregar a Página ---
@callback(
    [
        Output({"type": "um", "index": "at"}, "value"),
        Output({"type": "um", "index": "bt"}, "value"),
        Output({"type": "um", "index": "terciario"}, "value"),
        Output({"type": "conexao", "index": "at"}, "value"),
        Output({"type": "conexao", "index": "bt"}, "value"),
        Output({"type": "conexao", "index": "terciario"}, "value"),
        Output({"type": "ia", "index": "at"}, "value"),
        Output({"type": "ia", "index": "bt"}, "value"),
        Output({"type": "ia", "index": "terciario"}, "value"),
        Output({"type": "im", "index": "at"}, "value"),
        Output({"type": "im", "index": "bt"}, "value"),
        Output({"type": "im", "index": "terciario"}, "value"),
        Output("tipo-isolamento", "children"),
        Output("display-tipo-transformador-dieletric", "children"),
        Output({"type": "tensao-curta", "index": "at"}, "value"),
        Output({"type": "tensao-curta", "index": "bt"}, "value"),
        Output({"type": "tensao-curta", "index": "terciario"}, "value"),
        Output({"type": "tensao-induzida", "index": "at"}, "value"),
        Output({"type": "tensao-induzida", "index": "bt"}, "value"),
        Output({"type": "tensao-induzida", "index": "terciario"}, "value"),
        Output({"type": "neutro-um", "index": "at"}, "value"),
        Output({"type": "neutro-um", "index": "bt"}, "value"),
        Output({"type": "neutro-um", "index": "terciario"}, "value"),
        Output({"type": "impulso-atm-neutro", "index": "at"}, "value"),
        Output({"type": "impulso-atm-neutro", "index": "bt"}, "value"),
        Output({"type": "impulso-atm-neutro", "index": "terciario"}, "value"),
        Output({"type": "impulso-atm-cortado", "index": "at"}, "value"),
        Output({"type": "impulso-atm-cortado", "index": "bt"}, "value"),
        Output({"type": "impulso-atm-cortado", "index": "terciario"}, "value"),
    ],
    [
        Input("url", "pathname"),
        Input("dieletric-analysis-store", "data")
    ],
    [State("transformer-inputs-store", "data")],
    prevent_initial_call=False,  # Executa na carga inicial
)
def populate_dielectric_fields_auto(pathname, dieletric_store_data, transformer_data):
    """
    Preenche automaticamente os campos da análise dielétrica quando a página é carregada.
    Prioriza dados do dieletric-analysis-store (carregados do histórico),
    depois recalcula a partir do transformer-inputs-store se necessário.
    """
    triggered_id = ctx.triggered_id if ctx.triggered else "Initial Load"
    log.info(
        f"[AUTO FILL START] Trigger: {triggered_id}, Pathname: {pathname}, Store data available: {bool(dieletric_store_data)}"
    )

    # Verifica se estamos na página correta
    if not pathname:
        raise PreventUpdate

    clean_path = normalize_pathname(pathname)
    if clean_path != ROUTE_DIELECTRIC_ANALYSIS:
        log.debug(f"[AUTO FILL] Não na página '{ROUTE_DIELECTRIC_ANALYSIS}'. Prevenindo update.")
        raise PreventUpdate

    log.info(f"[AUTO FILL] Na página correta '{clean_path}'.")

    # Inicializar valores de retorno como None
    (
        um_at,
        um_bt,
        um_terciario,
        conexao_at,
        conexao_bt,
        conexao_terciario,
        nbi_at,
        nbi_bt,
        nbi_terciario,
        sil_at,
        sil_bt,
        sil_terciario,
        tipo_isolamento,
        tipo_transformador,
        tensao_aplicada_at,
        tensao_aplicada_bt,
        tensao_aplicada_terciario,
        tensao_induzida_at,
        tensao_induzida_bt,
        tensao_induzida_terciario,
        neutro_um_at,
        neutro_um_bt,
        neutro_um_terciario,
        nbi_neutro_at,
        nbi_neutro_bt,
        nbi_neutro_terciario,
        iac_at,
        iac_bt,
        iac_terciario,
    ) = [None] * 29

    # Tentar preencher a partir do dieletric-analysis-store (dados do histórico)
    loaded_from_store = False
    if dieletric_store_data and isinstance(dieletric_store_data, dict):
        parametros = dieletric_store_data.get("parametros", {})
        enrolamentos = parametros.get("enrolamentos", [])
        if enrolamentos and isinstance(enrolamentos, list) and len(enrolamentos) > 0:
            log.info("[AUTO FILL] Tentando preencher a partir do dieletric-analysis-store.")
            try:
                # Preencher tipo de isolamento e transformador
                tipo_isolamento = parametros.get("tipo_isolamento", "uniforme")
                tipo_transformador = parametros.get("tipo_transformador", "-")

                # Preencher dados dos enrolamentos
                if len(enrolamentos) > 0:
                    um_at = enrolamentos[0].get("um")
                    conexao_at = enrolamentos[0].get("conexao")
                    nbi_at = enrolamentos[0].get("ia")  # Mapeamento correto: ia -> nbi
                    sil_at = enrolamentos[0].get("im")  # Mapeamento correto: im -> sil
                    tensao_aplicada_at = enrolamentos[0].get("tensao_curta")
                    tensao_induzida_at = enrolamentos[0].get("tensao_induzida")
                    neutro_um_at = enrolamentos[0].get("neutro_um")
                    nbi_neutro_at = enrolamentos[0].get("nbi_neutro")
                if len(enrolamentos) > 1:
                    um_bt = enrolamentos[1].get("um")
                    conexao_bt = enrolamentos[1].get("conexao")
                    nbi_bt = enrolamentos[1].get("ia")
                    sil_bt = enrolamentos[1].get("im")
                    tensao_aplicada_bt = enrolamentos[1].get("tensao_curta")
                    tensao_induzida_bt = enrolamentos[1].get("tensao_induzida")
                    neutro_um_bt = enrolamentos[1].get("neutro_um")
                    nbi_neutro_bt = enrolamentos[1].get("nbi_neutro")
                if len(enrolamentos) > 2:
                    um_terciario = enrolamentos[2].get("um")
                    conexao_terciario = enrolamentos[2].get("conexao")
                    nbi_terciario = enrolamentos[2].get("ia")
                    sil_terciario = enrolamentos[2].get("im")
                    tensao_aplicada_terciario = enrolamentos[2].get("tensao_curta")
                    tensao_induzida_terciario = enrolamentos[2].get("tensao_induzida")
                    neutro_um_terciario = enrolamentos[2].get("neutro_um")
                    nbi_neutro_terciario = enrolamentos[2].get("nbi_neutro")

                # Calcular IAC (pode ser recalculado ou lido se estiver no store)
                resultados = dieletric_store_data.get("resultados", {})
                enrolamentos_res = resultados.get("enrolamentos", [])
                if len(enrolamentos_res) > 0:
                    iac_at = enrolamentos_res[0].get("impulso_cortado", {}).get("valor_str")
                if len(enrolamentos_res) > 1:
                    iac_bt = enrolamentos_res[1].get("impulso_cortado", {}).get("valor_str")
                if len(enrolamentos_res) > 2:
                    iac_terciario = enrolamentos_res[2].get("impulso_cortado", {}).get("valor_str")

                loaded_from_store = True
                log.info("[AUTO FILL] Campos preenchidos com sucesso a partir do store.")

            except Exception as e:
                log.warning(f"[AUTO FILL] Erro ao extrair dados do store: {e}. Recalculando...")
                loaded_from_store = False

    # Se não carregou do store ou houve erro, recalcula a partir dos dados básicos
    if not loaded_from_store:
        log.info("[AUTO FILL] Recalculando/Derivando campos a partir do transformer-inputs-store.")
        if not transformer_data or not isinstance(transformer_data, dict):
            log.warning("[AUTO FILL] Dados do transformador inválidos ou vazios para recálculo.")
            return [None] * 29

        # --- Lógica de Recálculo (igual à versão anterior) ---
        tipo_isolamento = transformer_data.get("tipo_isolamento", "uniforme")
        tipo_transformador = transformer_data.get("tipo_transformador", "-")
        tensao_aplicada_at = transformer_data.get("teste_tensao_aplicada_at", "-")
        tensao_aplicada_bt = transformer_data.get("teste_tensao_aplicada_bt", "-")
        tensao_aplicada_terciario = transformer_data.get("teste_tensao_aplicada_terciario", "-")
        tensao_induzida_at = transformer_data.get("tensao_induzida_at", None)
        tensao_induzida_bt = transformer_data.get("tensao_induzida_bt", None)
        tensao_induzida_terciario = transformer_data.get("tensao_induzida_terciario", None)

        # Formatar valores de tensão induzida para exibição
        try:
            if tensao_induzida_at is not None and tensao_induzida_at != "":
                tensao_induzida_at_float = safe_float_convert(tensao_induzida_at)
                if tensao_induzida_at_float is not None:
                    tensao_induzida_at = f"{tensao_induzida_at_float:.1f}"
        except Exception as e:
            log.warning(f"[AUTO FILL] Erro ao formatar tensão induzida AT: {e}")
        try:
            if tensao_induzida_bt is not None and tensao_induzida_bt != "":
                tensao_induzida_bt_float = safe_float_convert(tensao_induzida_bt)
                if tensao_induzida_bt_float is not None:
                    tensao_induzida_bt = f"{tensao_induzida_bt_float:.1f}"
        except Exception as e:
            log.warning(f"[AUTO FILL] Erro ao formatar tensão induzida BT: {e}")
        try:
            if tensao_induzida_terciario is not None and tensao_induzida_terciario != "":
                tensao_induzida_terciario_float = safe_float_convert(tensao_induzida_terciario)
                if tensao_induzida_terciario_float is not None:
                    tensao_induzida_terciario = f"{tensao_induzida_terciario_float:.1f}"
        except Exception as e:
            log.warning(f"[AUTO FILL] Erro ao formatar tensão induzida Terciário: {e}")

        def safe_str_output(value):
            if value is None or value == "": return None
            try:
                f_val = float(value)
                if np.isclose(f_val, round(f_val)): return str(int(f_val))
            except (ValueError, TypeError): pass
            return str(value)

        verificador = get_verificador_instance()

        um_at = safe_str_output(transformer_data.get("classe_tensao_at"))
        if um_at is None and transformer_data.get("tensao_at"):
            try:
                tensao_at_f = float(transformer_data.get("tensao_at"))
                um_at = verificador.get_nearest_um_value(tensao_at_f) if verificador else str(tensao_at_f)
            except (ValueError, TypeError): pass

        um_bt = safe_str_output(transformer_data.get("classe_tensao_bt"))
        if um_bt is None and transformer_data.get("tensao_bt"):
            try:
                tensao_bt_f = float(transformer_data.get("tensao_bt"))
                um_bt = verificador.get_nearest_um_value(tensao_bt_f) if verificador else str(tensao_bt_f)
            except (ValueError, TypeError): pass

        um_terciario = safe_str_output(transformer_data.get("classe_tensao_terciario"))
        if um_terciario is None and transformer_data.get("tensao_terciario"):
            try:
                tensao_ter_f = float(transformer_data.get("tensao_terciario"))
                um_terciario = verificador.get_nearest_um_value(tensao_ter_f) if verificador else str(tensao_ter_f)
            except (ValueError, TypeError): pass

        def determine_connection(conn_key, neutral_volt_key):
            connection_stored = transformer_data.get(conn_key)
            default_conn = "estrela" if "at" in conn_key else ("triangulo" if "bt" in conn_key else None)
            if not connection_stored or not isinstance(connection_stored, str): connection_stored = default_conn
            if connection_stored is None: return None
            conn_lower = connection_stored.lower()
            if conn_lower == "estrela_sem_neutro": return "Y"
            elif "estrela" in conn_lower or "star" in conn_lower or conn_lower.startswith("y"):
                neutral_voltage = transformer_data.get(neutral_volt_key)
                try:
                    if neutral_voltage is not None and str(neutral_voltage).strip() != "":
                        if safe_float_convert(neutral_voltage) > 0: return "YN"
                except: pass
                return "Y"
            elif "triangulo" in conn_lower or "delta" in conn_lower or conn_lower.startswith("d"): return "D"
            else:
                if default_conn == "estrela": return "Y"
                if default_conn == "triangulo": return "D"
                return None

        conexao_at = determine_connection("conexao_at", "tensao_bucha_neutro_at")
        conexao_bt = determine_connection("conexao_bt", "tensao_bucha_neutro_bt")
        conexao_terciario = determine_connection("conexao_terciario", "tensao_bucha_neutro_terciario")

        def get_neutro_nbi(conn_key, neutral_volt_key, neutral_nbi_key):
            connection_stored = transformer_data.get(conn_key)
            if not connection_stored or not isinstance(connection_stored, str): return None
            conn_lower = connection_stored.lower()
            if conn_lower == "estrela_sem_neutro": return None
            elif "estrela" in conn_lower or "star" in conn_lower or conn_lower.startswith("y"):
                neutral_voltage = transformer_data.get(neutral_volt_key)
                try:
                    if neutral_voltage is not None and str(neutral_voltage).strip() != "":
                        if safe_float_convert(neutral_voltage) > 0:
                            return safe_str_output(transformer_data.get(neutral_nbi_key))
                except: pass
            return None

        nbi_at = safe_str_output(transformer_data.get("nbi_at"))
        nbi_bt = safe_str_output(transformer_data.get("nbi_bt"))
        nbi_terciario = safe_str_output(transformer_data.get("nbi_terciario"))
        neutro_um_at = safe_str_output(transformer_data.get("tensao_bucha_neutro_at"))
        neutro_um_bt = safe_str_output(transformer_data.get("tensao_bucha_neutro_bt"))
        neutro_um_terciario = safe_str_output(transformer_data.get("tensao_bucha_neutro_terciario"))
        nbi_neutro_at = get_neutro_nbi("conexao_at", "tensao_bucha_neutro_at", "nbi_neutro_at")
        nbi_neutro_bt = get_neutro_nbi("conexao_bt", "tensao_bucha_neutro_bt", "nbi_neutro_bt")
        nbi_neutro_terciario = get_neutro_nbi("conexao_terciario", "tensao_bucha_neutro_terciario", "nbi_neutro_terciario")
        sil_at = safe_str_output(transformer_data.get("sil_at"))
        sil_bt = safe_str_output(transformer_data.get("sil_bt"))
        sil_terciario = safe_str_output(transformer_data.get("sil_terciario"))

        # Calcular IAC
        iac_at = None
        if nbi_at:
            try: iac_at = f"{float(nbi_at) * 1.1:.1f}"
            except (ValueError, TypeError): pass
        iac_bt = None
        if nbi_bt:
            try: iac_bt = f"{float(nbi_bt) * 1.1:.1f}"
            except (ValueError, TypeError): pass
        iac_terciario = None
        if nbi_terciario:
            try: iac_terciario = f"{float(nbi_terciario) * 1.1:.1f}"
            except (ValueError, TypeError): pass
        # --- Fim da Lógica de Recálculo ---

    # Log final dos valores a serem retornados
    log.info(
        f"[AUTO FILL END] Valores Finais: Um=[{um_at},{um_bt},{um_terciario}], Conn=[{conexao_at},{conexao_bt},{conexao_terciario}], NBI=[{nbi_at},{nbi_bt},{nbi_terciario}], SIL=[{sil_at},{sil_bt},{sil_terciario}], Isol={tipo_isolamento}"
    )
    log.info(f"[AUTO FILL END] NBI Neutro=[{nbi_neutro_at},{nbi_neutro_bt},{nbi_neutro_terciario}]")
    log.info(f"[AUTO FILL END] IAC=[{iac_at},{iac_bt},{iac_terciario}]")
    log.info(
        f"[AUTO FILL END] T.Induzida=[{tensao_induzida_at},{tensao_induzida_bt},{tensao_induzida_terciario}]"
    )
    log.info(
        f"[AUTO FILL END] Valores adicionais: Tipo Trafo={tipo_transformador}, T.Aplicada AT={tensao_aplicada_at}, T.Aplicada BT={tensao_aplicada_bt}, T.Aplicada Ter.={tensao_aplicada_terciario}"
    )

    # Retorna todos os valores para preencher os Outputs
    return (
        um_at,
        um_bt,
        um_terciario,
        conexao_at,
        conexao_bt,
        conexao_terciario,
        nbi_at,
        nbi_bt,
        nbi_terciario,
        sil_at,
        sil_bt,
        sil_terciario,
        tipo_isolamento,
        tipo_transformador,
        tensao_aplicada_at,
        tensao_aplicada_bt,
        tensao_aplicada_terciario,
        tensao_induzida_at,
        tensao_induzida_bt,
        tensao_induzida_terciario,
        neutro_um_at,
        neutro_um_bt,
        neutro_um_terciario,
        nbi_neutro_at,
        nbi_neutro_bt,
        nbi_neutro_terciario,
        iac_at,
        iac_bt,
        iac_terciario,
    )


# Callback para Ensaios Complementares removido - funcionalidade movida para a página de análise dielétrica completa


# --- Callback para Salvar Dados (MODIFICADO) ---
@app.callback(
    [
        Output("dieletric-analysis-store", "data"),
        Output("dielectric-save-confirmation", "children"),
    ],  # NOVO Output
    [
        Input("save-dielectric-params-btn", "n_clicks"),  # Trigger PRINCIPAL é o botão
        Input("url", "pathname"),
    ],  # Trigger secundário para carregar
    [
        State({"type": "um", "index": ALL}, "value"),
        State({"type": "conexao", "index": ALL}, "value"),
        State({"type": "neutro-um", "index": ALL}, "value"),
        State({"type": "ia", "index": ALL}, "value"),
        State({"type": "impulso-atm-neutro", "index": ALL}, "value"),
        State({"type": "im", "index": ALL}, "value"),
        State({"type": "tensao-curta", "index": ALL}, "value"),
        State({"type": "tensao-induzida", "index": ALL}, "value"),
        State("tipo-isolamento", "children"),
        State({"type": "impulso-atm-cortado", "index": ALL}, "value"),
        State("transformer-inputs-store", "data"),
        State("dieletric-analysis-store", "data"),
    ],
    prevent_initial_call=True,  # AGORA É TRUE - Só executa com clique ou mudança de URL
)
def store_dielectric_analysis_data(
    n_clicks_save,
    pathname,  # Inputs
    um_values,
    conexoes,
    neutro_ums,
    ia_values,
    ia_neutro_values,
    im_values,
    tensao_curta_values,
    tensao_induzida_values,
    tipo_isolamento,
    iac_values,
    transformer_data,  # States
    current_store_data,
):
    """Coleta todos os inputs e resultados calculados e salva no dcc.Store."""
    triggered_id = ctx.triggered_id if ctx.triggered else "No trigger"
    log.debug(f"Storing dielectric data. Triggered by: {triggered_id}")
    print(f"--- [STORE DIELECTRIC DATA] Trigger: {triggered_id} ---")  # DEBUG

    # Se o trigger foi a URL, tentamos carregar dados existentes (se houver)
    # Se for o botão, salvamos os dados atuais
    if triggered_id == "url":
        # Lógica para carregar dados ao entrar na página (se necessário)
        # Normalmente, os callbacks de 'options' e 'value' que dependem do store
        # já farão isso se o store tiver dados.
        # Aqui, apenas retornamos o estado atual do store sem modificá-lo
        # e sem mensagem de confirmação.
        log.debug("[STORE DATA] Trigger foi URL, retornando dados atuais do store sem salvar.")
        return current_store_data, ""  # Retorna dados atuais e mensagem vazia
    elif triggered_id == "save-dielectric-params-btn" and n_clicks_save:
        log.info("[STORE DATA] Botão Salvar Parâmetros clicado. Salvando dados...")
        print("[STORE DATA] Botão Salvar Parâmetros clicado. Salvando dados...")
    else:
        # Outro trigger ou botão não clicado
        log.debug(
            f"[STORE DATA] Trigger não esperado ou n_clicks={n_clicks_save}. Prevenindo update."
        )
        raise PreventUpdate

    # Verificar se estamos na página correta
    if pathname:
        clean_path = normalize_pathname(pathname)
        if clean_path != ROUTE_DIELECTRIC_ANALYSIS:
            log.debug(
                f"[STORE DATA] Não na página '{ROUTE_DIELECTRIC_ANALYSIS}'. Prevenindo update."
            )
            raise PreventUpdate

    triggered_input_info = ctx.triggered[0] if ctx.triggered else {}
    triggered_input = triggered_input_info.get("prop_id", "No trigger")
    log.debug(f"Storing dielectric data. Triggered by: {triggered_input}")

    # Função auxiliar para formatar valores
    def safe_str_output(value):
        if value is None or value == "":
            return None
        try:
            f_val = float(value)
            if np.isclose(f_val, round(f_val)):
                return str(int(f_val))
        except (ValueError, TypeError):
            pass
        return str(value)

    verificador = get_verificador_instance()
    if verificador is None:
        log.error("Verificador não inicializado, salvando dados dielétricos incompletos.")

    if not um_values or not any(um_values):  # Check if at least one Um is present
        log.debug("Nenhum Um definido, não salvando dados dielétricos.")
        return current_store_data  # Don't save if essential data is missing

    tipo_transformador_geral = (
        transformer_data.get("tipo_transformador")
        if transformer_data and isinstance(transformer_data, dict)
        else None
    )

    data_to_store = {
        "parametros": {
            "enrolamentos": [],
            "tipo_transformador": tipo_transformador_geral,
            "tipo_isolamento": tipo_isolamento,
        },
        "resultados": {"enrolamentos": []},
        "timestamp": datetime.datetime.now().isoformat(),
    }
    try:
        num_enrolamentos = 3
        # Pad lists
        um_values = list(um_values) + [None] * (num_enrolamentos - len(um_values))
        conexoes = list(conexoes) + [None] * (num_enrolamentos - len(conexoes))
        neutro_ums = list(neutro_ums) + [None] * (num_enrolamentos - len(neutro_ums))
        ia_values = list(ia_values) + [None] * (num_enrolamentos - len(ia_values))
        ia_neutro_values = list(ia_neutro_values) + [None] * (
            num_enrolamentos - len(ia_neutro_values)
        )
        im_values = list(im_values) + [None] * (num_enrolamentos - len(im_values))
        tensao_curta_values = list(tensao_curta_values) + [None] * (
            num_enrolamentos - len(tensao_curta_values)
        )
        tensao_induzida_values = list(tensao_induzida_values) + [None] * (
            num_enrolamentos - len(tensao_induzida_values)
        )
        iac_values = list(iac_values) + [None] * (num_enrolamentos - len(iac_values))

        nomes = ["Alta Tensão", "Baixa Tensão", "Terciário"]
        for i in range(num_enrolamentos):
            um = um_values[i]
            conexao = conexoes[i]
            neutro_um = neutro_ums[i] if conexao in ["YN", "Y"] else None
            ia = ia_values[i]
            ia_neutro = ia_neutro_values[i] if conexao == "YN" else None
            im = im_values[i]
            tensao_curta = tensao_curta_values[i]
            tensao_induzida = tensao_induzida_values[i]
            iac = iac_values[i]

            if um:  # Save winding only if Um is defined
                # Get NBI Neutro value based on index
                nbi_neutro_value = None
                if (
                    i == 0
                    and conexao == "YN"
                    and transformer_data
                    and isinstance(transformer_data, dict)
                ):
                    nbi_neutro_value = safe_str_output(transformer_data.get("nbi_neutro_at"))
                elif (
                    i == 1
                    and conexao == "YN"
                    and transformer_data
                    and isinstance(transformer_data, dict)
                ):
                    nbi_neutro_value = safe_str_output(transformer_data.get("nbi_neutro_bt"))
                elif (
                    i == 2
                    and conexao == "YN"
                    and transformer_data
                    and isinstance(transformer_data, dict)
                ):
                    nbi_neutro_value = safe_str_output(transformer_data.get("nbi_neutro_terciario"))

                data_to_store["parametros"]["enrolamentos"].append(
                    {
                        "nome": nomes[i],
                        "um": um,
                        "conexao": conexao,
                        "neutro_um": neutro_um,
                        "ia": ia,
                        "ia_neutro": ia_neutro,
                        "im": im,
                        "tensao_curta": tensao_curta,
                        "tensao_induzida": tensao_induzida,
                        "nbi_neutro": nbi_neutro_value,
                    }
                )
                resultados_enrolamento = {"nome": nomes[i]}
                resultados_enrolamento["impulso_cortado"] = {"valor_str": iac}  # Save IAC string

                if verificador:
                    transformer_type_ieee = (
                        "power"
                        if tipo_transformador_geral == "Trifásico"
                        else "distribution"
                        if tipo_transformador_geral
                        else None
                    )
                    resultados_enrolamento["espacamentos"] = verificador.get_clearances(
                        um, transformer_type_ieee, ia, im
                    )
                else:
                    resultados_enrolamento["espacamentos"] = {}
                data_to_store["resultados"]["enrolamentos"].append(resultados_enrolamento)

        # Não armazenamos mais os ensaios complementares aqui, pois foram movidos para a página de análise dielétrica completa

        # Adicionar logs detalhados para diagnóstico
        print("\n--- [DIELETRIC STORE SAVE DEBUG] ---")
        log.info("--- [DIELETRIC STORE SAVE DEBUG] ---")

        print(f"  Tipo de data_to_store: {type(data_to_store)}")
        if isinstance(data_to_store, dict):
            print(f"  Chaves principais: {list(data_to_store.keys())}")
            # Detalhar sub-dicionários importantes
            parametros = data_to_store.get("parametros", {})
            resultados = data_to_store.get("resultados", {})
            print(f"  parametros (tipo): {type(parametros).__name__}")
            if isinstance(parametros, dict):
                print(f"    parametros chaves: {list(parametros.keys())}")
                enrolamentos = parametros.get("enrolamentos", [])
                print(
                    f"    enrolamentos (tipo): {type(enrolamentos).__name__}, tamanho: {len(enrolamentos)}"
                )
                for i, enrol in enumerate(enrolamentos):
                    print(f"      Enrolamento #{i+1}: {enrol.get('nome', 'Sem nome')}")

            print(f"  resultados (tipo): {type(resultados).__name__}")
            if isinstance(resultados, dict):
                print(f"    resultados chaves: {list(resultados.keys())}")
                enrolamentos_res = resultados.get("enrolamentos", [])
                print(
                    f"    enrolamentos (tipo): {type(enrolamentos_res).__name__}, tamanho: {len(enrolamentos_res)}"
                )
        else:
            print(f"  Conteúdo: {repr(data_to_store)[:100]}")

        # Verificar se o MCP está disponível
        if hasattr(app, "mcp") and app.mcp is not None:
            log.info("[STORE DATA] Usando MCP para salvar dados dielétricos")
            print("[STORE DATA] Usando MCP para salvar dados dielétricos")

            # Usar patch_mcp para atualizar apenas campos não vazios
            if patch_mcp("dieletric-analysis-store", data_to_store):
                log.info("[STORE DATA] Dados dielétricos salvos via MCP")
                print("[STORE DATA] Dados dielétricos salvos via MCP")
            else:
                log.warning("[STORE DATA] Nenhum dado válido para atualizar no MCP")
                print("[STORE DATA] Nenhum dado válido para atualizar no MCP")

            # Obter dados atualizados do MCP
            final_data_store = app.mcp.get_data("dieletric-analysis-store") or {}
        else:
            # Fallback para o método antigo se o MCP não estiver disponível
            log.warning(
                "[STORE DATA] MCP não disponível. Usando método antigo para salvar dados dielétricos."
            )
            print(
                "[STORE DATA] MCP não disponível. Usando método antigo para salvar dados dielétricos."
            )

            final_data_store = current_store_data or {}
            final_data_store.update(data_to_store)

        print(f"  Tipo de final_data_store após update: {type(final_data_store)}")
        if isinstance(final_data_store, dict):
            print(f"  Chaves de final_data_store após update: {list(final_data_store.keys())}")
            # Verificar se os dados foram realmente atualizados
            parametros_final = final_data_store.get("parametros", {})
            enrolamentos_final = parametros_final.get("enrolamentos", [])
            print(f"  Número de enrolamentos no store final: {len(enrolamentos_final)}")
            for i, enrol in enumerate(enrolamentos_final):
                print(f"    Enrolamento #{i+1}: {enrol.get('nome', 'Sem nome')}")
        else:
            print(f"  Conteúdo de final_data_store após update: {repr(final_data_store)[:100]}")

        log.info("Dados de Análise Dielétrica salvos no store.")
        print("--- Fim [DIELETRIC STORE SAVE DEBUG] ---")

        # Cria a mensagem de confirmação
        timestamp_str = datetime.datetime.now().strftime("%H:%M:%S")
        confirmation_message = dbc.Alert(
            f"Parâmetros salvos com sucesso às {timestamp_str}!",
            color="success",
            duration=4000,  # Mensagem some após 4 segundos
            fade=True,
            className="p-1 text-center",
            style={"fontSize": "0.75rem"},
        )

        return convert_numpy_types(final_data_store), confirmation_message

    except Exception as e:
        log.exception(f"Erro ao salvar dados dielétricos no store: {e}")
        error_msg = dbc.Alert(f"Erro ao salvar: {e}", color="danger", className="p-1")
        return current_store_data, error_msg


# Removido o callback que causava conflito com outros callbacks
# Os valores de neutro já são preenchidos pelo callback populate_dielectric_fields_auto


# --- Callback para atualizar valores de Tensão Induzida ---
@app.callback(
    Output({"type": "tensao-induzida", "index": ALL}, "value"),
    Input({"type": "um", "index": ALL}, "value"),
    prevent_initial_call=False,  # Alterado para False para executar na carga inicial
)
def dieletric_analysis_update_tensao_induzida_values(um_values):
    """Atualiza os valores de Tensão Induzida com base nos valores de Um."""
    log.info(f"[TENSAO INDUZIDA] Callback iniciado com valores Um={um_values}")

    num_outputs = (
        len(ctx.outputs_list[0])
        if ctx.outputs_list and ctx.outputs_list[0]
        else len(um_values)
        if um_values
        else 0
    )
    if num_outputs == 0:
        log.warning("[TENSAO INDUZIDA] Nenhum output necessário")
        return no_update

    verificador = get_verificador_instance()
    if verificador is None:
        log.error("[TENSAO INDUZIDA] Verificador não disponível")
        return ["" for _ in range(num_outputs)]  # Retorna strings vazias em vez de None

    values_list = []
    for i, um in enumerate(um_values):
        ti_value = ""  # Valor padrão é string vazia em vez de None
        if um:
            try:
                log.info(f"[TENSAO INDUZIDA] Processando Um={um} para índice {i}")
                # Obter valores de tensão induzida para o Um atual
                ti_vals = verificador.nbr.get_tensao_induzida_values(um)
                log.info(f"[TENSAO INDUZIDA] Valores obtidos para Um={um}: {ti_vals}")

                # Se encontrou valores, usa o primeiro (maior valor)
                if ti_vals and len(ti_vals) > 0:
                    # Ordena os valores em ordem decrescente e pega o maior
                    ti_vals_float = [
                        safe_float_convert(v) for v in ti_vals if safe_float_convert(v) is not None
                    ]
                    if ti_vals_float:
                        ti_vals_float.sort(reverse=True)
                        v_float = ti_vals_float[0]
                        # Formata o valor com uma casa decimal
                        ti_value = f"{v_float:.1f}"
                        log.info(f"[TENSAO INDUZIDA] Valor selecionado para Um={um}: {ti_value}")

                # Se não encontrou valores, não calcula mais um valor padrão
                if not ti_value:
                    log.warning(f"[TENSAO INDUZIDA] Nenhum valor encontrado para Um={um}")
            except Exception as e:
                log.exception(f"[TENSAO INDUZIDA] Erro ao obter valor para Um={um}: {e}")

        values_list.append(ti_value)
        log.info(f"[TENSAO INDUZIDA] Valor final para índice {i}: {ti_value}")

    # Garante que a lista tenha o tamanho correto
    while len(values_list) < num_outputs:
        values_list.append("")  # Adiciona strings vazias em vez de None

    log.info(f"[TENSAO INDUZIDA] Valores finais: {values_list[:num_outputs]}")
    return values_list[:num_outputs]


# --- Callback para Atualizar Display do Tipo de Isolamento ---
@callback(
    Output("display-tipo-isolamento", "children"),
    Input("transformer-inputs-store", "data"),
    prevent_initial_call=False,
)
def dielectric_analysis_update_tipo_isolamento_display(transformer_data):
    """Atualiza o display do tipo de isolamento com base nos dados do transformador."""
    if not transformer_data or not isinstance(transformer_data, dict):
        return "-"
    tipo_isolamento = transformer_data.get("tipo_isolamento", "uniforme")
    if not tipo_isolamento:
        return "-"
    return tipo_isolamento.capitalize()


# --- Callback para exibir informações do transformador na página ---
# Este callback copia o conteúdo do painel global para o painel específico da página
@callback(
    Output("transformer-info-dieletric-page", "children"),
    Input("transformer-info-dieletric", "children"),
    prevent_initial_call=False,
)
def update_dieletric_page_info_panel(global_panel_content):
    """Copia o conteúdo do painel global para o painel específico da página."""
    log.debug("Atualizando painel de informações do transformador na página de análise dielétrica")
    return global_panel_content
