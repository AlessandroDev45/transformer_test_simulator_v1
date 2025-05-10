# callbacks/insulation_level_callbacks.py
"""
Callbacks para seleção detalhada de níveis de isolamento, permitindo seleção individual
de NBI, SIL, Aplicada e Induzida após filtrar por Norma e Classe de Tensão.
"""

import json
import logging
from dash import Input, Output, State, html, dcc, no_update
from dash.exceptions import PreventUpdate

log = logging.getLogger(__name__)

# Carregar os dados do JSON
try:
    with open("assets/tabela.json", "r", encoding="utf-8") as f:
        TABELA_DATA = json.load(f)
    INSULATION_LEVELS = TABELA_DATA.get("insulation_levels", [])
    log.info(f"Dados de níveis de isolamento carregados: {len(INSULATION_LEVELS)} registros")
except FileNotFoundError:
    log.error("ERRO: assets/tabela.json não encontrado!")
    INSULATION_LEVELS = []
except json.JSONDecodeError:
    log.error("ERRO: Falha ao decodificar assets/tabela.json!")
    INSULATION_LEVELS = []

def create_dropdown_options(filtered_levels, field_key, current_value, label_suffix=""):
    """
    Cria opções para um dropdown a partir de valores distintos de um campo em níveis filtrados.
    Tenta manter o current_value selecionado se ainda for válido.
    Permite que o usuário selecione qualquer valor, mesmo que não esteja nos níveis filtrados.
    """
    if not filtered_levels:
        return [{"label": "-", "value": ""}], None

    distinct_values = sorted(list(set(
        level[field_key] for level in filtered_levels if level.get(field_key) is not None
    )))

    if not distinct_values:
        return [{"label": "N/A", "value": ""}], None

    options = [{"label": f"{val}{label_suffix}", "value": val} for val in distinct_values]

    # Manter o valor atual mesmo que não esteja na lista de valores distintos
    selected_value = None
    if current_value is not None:
        # Se o valor atual não estiver na lista, adicione-o como uma opção personalizada
        if current_value not in distinct_values:
            options.append({"label": f"{current_value}{label_suffix} (Personalizado)", "value": current_value})
        selected_value = current_value
    elif options:
        selected_value = options[0]["value"] # Seleciona o primeiro por defeito se nada mantido

    return options, selected_value

def register_insulation_level_callbacks(app_instance):
    log.info("Registrando callbacks de níveis de isolamento (seleção individual)...")

    # --- CALLBACKS PARA ENROLAMENTOS PRINCIPAIS (AT, BT, TERCIARIO) ---
    def create_main_winding_insulation_callback(winding_prefix):
        outputs = [
            Output(f"nbi_{winding_prefix}", "options"), Output(f"nbi_{winding_prefix}", "value"),
            Output(f"sil_{winding_prefix}", "options"), Output(f"sil_{winding_prefix}", "value"),
            Output(f"teste_tensao_aplicada_{winding_prefix}", "options"), Output(f"teste_tensao_aplicada_{winding_prefix}", "value")
        ]
        # Terciário e BT podem não ter 'teste_tensao_induzida' no layout ou na lógica desejada
        # O layout atual para BT não tem induzida, e para terciário também não.
        # Apenas AT tem todos os quatro.
        if winding_prefix == "at":
            outputs.extend([
                Output(f"teste_tensao_induzida_{winding_prefix}", "options"), Output(f"teste_tensao_induzida_{winding_prefix}", "value")
            ])

        states = [
            State(f"nbi_{winding_prefix}", "value"), State(f"sil_{winding_prefix}", "value"),
            State(f"teste_tensao_aplicada_{winding_prefix}", "value")
        ]
        if winding_prefix == "at":
            states.append(State(f"teste_tensao_induzida_{winding_prefix}", "value"))

        @app_instance.callback(outputs,
            [Input("norma_iso", "value"), Input(f"classe_tensao_{winding_prefix}", "value")],
            states
        )
        def update_winding_insulation_dropdowns(norma, um_kv_str, *current_values):
            log.debug(f"[{winding_prefix.upper()}] Update Dropdowns: Norma={norma}, Um_kv_str={um_kv_str}, CurrentVals={current_values}")

            current_nbi, current_sil, current_acsd = current_values[0], current_values[1], current_values[2]
            current_acld = current_values[3] if winding_prefix == "at" and len(current_values) > 3 else None

            empty_opts = [{"label": "-", "value": ""}]
            na_opts = [{"label": "N/A", "value": ""}] # Para quando não há valores distintos

            if not norma or um_kv_str is None or str(um_kv_str).strip() == "":
                if winding_prefix == "at":
                    return empty_opts, None, empty_opts, None, empty_opts, None, empty_opts, None
                return empty_opts, None, empty_opts, None, empty_opts, None

            try:
                um_kv = float(um_kv_str)
            except ValueError:
                log.warning(f"[{winding_prefix.upper()}] Valor Um_kv inválido: {um_kv_str}")
                if winding_prefix == "at":
                    return empty_opts, None, empty_opts, None, empty_opts, None, empty_opts, None
                return empty_opts, None, empty_opts, None, empty_opts, None

            # Determinar o padrão com base na norma (verificando se contém IEC ou IEEE)
            standard_filter = "IEC/NBR" if norma and "IEC" in norma else "IEEE"

            filtered_levels = [
                level for level in INSULATION_LEVELS
                if level["standard"] == standard_filter and \
                   level.get("um_kv") == um_kv
            ]

            log.debug(f"[{winding_prefix.upper()}] Filtrando por standard={standard_filter}, um_kv={um_kv}, encontrados {len(filtered_levels)} níveis")

            if not filtered_levels:
                no_levels_found_opts = [{"label": "Nenhum nível encontrado", "value": ""}]
                if winding_prefix == "at":
                    return no_levels_found_opts, None, no_levels_found_opts, None, no_levels_found_opts, None, no_levels_found_opts, None
                return no_levels_found_opts, None, no_levels_found_opts, None, no_levels_found_opts, None

            # Não adicionamos mais valores padrão, apenas usamos o que está na tabela
            log.debug(f"[{winding_prefix.upper()}] Usando apenas os valores da tabela para a classe {um_kv} kV")

            nbi_options, nbi_value = create_dropdown_options(filtered_levels, "bil_kvp", current_nbi, " kVp")
            log.debug(f"[{winding_prefix.upper()}] Opções NBI: {nbi_options}, valor selecionado: {nbi_value}")

            sil_options, sil_value = create_dropdown_options(filtered_levels, "sil_kvp", current_sil, " kVp")
            log.debug(f"[{winding_prefix.upper()}] Opções SIL: {sil_options}, valor selecionado: {sil_value}")

            # Para IEEE, BSL pode ser uma alternativa se SIL não estiver presente para o mesmo BIL
            if norma and "IEEE" in norma and not sil_options[0].get("value"): # Se sil_options for N/A
                bsl_options, bsl_value = create_dropdown_options(filtered_levels, "bsl_kvp", current_sil, " kVp (BSL)")
                if bsl_options[0].get("value"): # Se houver opções BSL
                    sil_options, sil_value = bsl_options, bsl_value


            # Não adicionamos mais valores padrão para tensão aplicada, apenas usamos o que está na tabela
            acsd_values = [val for level in filtered_levels if level.get("acsd_kv_rms") for val in [level.get("acsd_kv_rms")]]
            log.debug(f"[{winding_prefix.upper()}] Valores ACSD disponíveis na tabela para classe {um_kv} kV: {sorted(list(set(acsd_values)))}")

            # Criar opções para tensão aplicada (ACSD)
            acsd_options, acsd_value = create_dropdown_options(filtered_levels, "acsd_kv_rms", current_acsd, " kVrms")
            log.debug(f"[{winding_prefix.upper()}] Opções ACSD: {acsd_options}, valor selecionado: {acsd_value}")

            if winding_prefix == "at":
                # Para ACLD, podemos ter valores de 'acld_kv_rms' ou usar 'acsd_kv_rms' como fallback se ACLD não existir
                # A lógica aqui é pegar todos os 'acld_kv_rms' e todos os 'acsd_kv_rms' como possíveis opções para induzida
                induced_values_acld = [lvl['acld_kv_rms'] for lvl in filtered_levels if lvl.get('acld_kv_rms') is not None]
                induced_values_acsd_fallback = [lvl['acsd_kv_rms'] for lvl in filtered_levels if lvl.get('acsd_kv_rms') is not None and lvl.get('acld_kv_rms') is None] # Apenas ACSD se ACLD não existir para esse nível

                # Não adicionamos mais valores padrão para tensão induzida, apenas usamos o que está na tabela
                log.debug(f"[{winding_prefix.upper()}] Valores ACLD disponíveis na tabela para classe {um_kv} kV: {induced_values_acld}")

                distinct_induced_values = sorted(list(set(induced_values_acld + induced_values_acsd_fallback)))
                log.debug(f"[{winding_prefix.upper()}] Valores distintos para induzida: {distinct_induced_values}")

                if not distinct_induced_values:
                    acld_options, acld_value = na_opts, None
                else:
                    acld_options = [{"label": f"{val} kVrms", "value": val} for val in distinct_induced_values]
                    acld_value = None
                    if current_acld is not None:
                        # Se o valor atual não estiver na lista, adicione-o como uma opção personalizada
                        if current_acld not in distinct_induced_values:
                            acld_options.append({"label": f"{current_acld} kVrms (Personalizado)", "value": current_acld})
                        acld_value = current_acld
                    elif acld_options:
                        acld_value = acld_options[0]["value"]

                log.debug(f"[{winding_prefix.upper()}] Opções ACLD: {acld_options}, valor selecionado: {acld_value}")

                return nbi_options, nbi_value, sil_options, sil_value, acsd_options, acsd_value, acld_options, acld_value

            return nbi_options, nbi_value, sil_options, sil_value, acsd_options, acsd_value

    create_main_winding_insulation_callback("at")
    create_main_winding_insulation_callback("bt")
    create_main_winding_insulation_callback("terciario")


    # --- CALLBACKS PARA GERENCIAMENTO DO NEUTRO ---
    def create_neutral_insulation_callbacks(winding_prefix):
        neutral_voltage_id = f"tensao_bucha_neutro_{winding_prefix}"
        neutral_nbi_id = f"nbi_neutro_{winding_prefix}"
        neutral_sil_id = f"sil_neutro_{winding_prefix}"
        neutral_row_id = f"{winding_prefix}_neutral_fields_row"

        # Callback para habilitar/desabilitar campos do neutro e a linha
        @app_instance.callback(
            [Output(neutral_voltage_id, "disabled"),
             Output(neutral_nbi_id, "disabled"),
             Output(neutral_sil_id, "disabled"),
             Output(neutral_row_id, "style")],
            [Input(f"conexao_{winding_prefix}", "value")]
        )
        def manage_neutral_fields_visibility_state(connection_type):
            is_neutral_accessible = connection_type in ["estrela", "ziguezague"]
            disabled_state = not is_neutral_accessible
            display_style = {"display": "none"} if disabled_state else {"display": "flex"}
            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Vis/State: Conexão={connection_type}, Acessível={is_neutral_accessible}, Disabled={disabled_state}")
            return disabled_state, disabled_state, disabled_state, display_style

        # Callback para popular dropdowns NBI e SIL do Neutro
        @app_instance.callback(
            [Output(neutral_nbi_id, "options"), Output(neutral_nbi_id, "value"),
             Output(neutral_sil_id, "options"), Output(neutral_sil_id, "value")],
            [Input("norma_iso", "value"), Input(neutral_voltage_id, "value")],
            [State(neutral_nbi_id, "value"), State(neutral_sil_id, "value"),
             State(f"conexao_{winding_prefix}", "value")] # Para verificar se o neutro está acessível
        )
        def update_neutral_insulation_dropdowns(norma, um_kv_neutral_str, current_nbi_neutro, current_sil_neutro, connection_type):
            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Update Dropdowns: Norma={norma}, Um_Neutro_str={um_kv_neutral_str}, Conexão={connection_type}")

            empty_opts = [{"label": "-", "value": ""}]

            is_neutral_accessible = connection_type in ["estrela", "ziguezague"]
            if not is_neutral_accessible: # Se não acessível, retorna vazio e não atualiza
                log.debug(f"[{winding_prefix.upper()}-NEUTRO] Não acessível, retornando no_update para opções.")
                # Retorna opções vazias e None para valores para limpar se o callback for disparado
                return empty_opts, None, empty_opts, None


            if not norma or um_kv_neutral_str is None or str(um_kv_neutral_str).strip() == "":
                return empty_opts, None, empty_opts, None

            try:
                um_kv_neutral = float(um_kv_neutral_str)
            except ValueError:
                log.warning(f"[{winding_prefix.upper()}-NEUTRO] Valor Um_Neutro inválido: {um_kv_neutral_str}")
                return empty_opts, None, empty_opts, None

            # Determinar o padrão com base na norma (verificando se contém IEC ou IEEE)
            standard_filter = "IEC/NBR" if norma and "IEC" in norma else "IEEE"

            filtered_levels = [
                level for level in INSULATION_LEVELS
                if level["standard"] == standard_filter and \
                   level.get("um_kv") == um_kv_neutral
            ]

            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Filtrando por standard={standard_filter}, um_kv={um_kv_neutral}, encontrados {len(filtered_levels)} níveis")

            if not filtered_levels:
                no_levels_found_opts = [{"label": "Nenhum nível encontrado", "value": ""}]
                return no_levels_found_opts, None, no_levels_found_opts, None

            # Não adicionamos mais valores padrão para o neutro, apenas usamos o que está na tabela
            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Usando apenas os valores da tabela para o neutro da classe {um_kv_neutral} kV")

            # Usar a função create_dropdown_options que já foi modificada para permitir valores personalizados
            nbi_options, nbi_value = create_dropdown_options(filtered_levels, "bil_kvp", current_nbi_neutro, " kVp")
            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Opções NBI: {nbi_options}, valor selecionado: {nbi_value}")

            sil_options, sil_value = create_dropdown_options(filtered_levels, "sil_kvp", current_sil_neutro, " kVp")
            log.debug(f"[{winding_prefix.upper()}-NEUTRO] Opções SIL: {sil_options}, valor selecionado: {sil_value}")
            # Para IEEE, BSL pode ser uma alternativa se SIL não estiver presente para o mesmo BIL
            if norma and "IEEE" in norma and not sil_options[0].get("value"): # Se sil_options for N/A
                bsl_options, bsl_value = create_dropdown_options(filtered_levels, "bsl_kvp", current_sil_neutro, " kVp (BSL)")
                if bsl_options[0].get("value"): # Se houver opções BSL
                    sil_options, sil_value = bsl_options, bsl_value

            return nbi_options, nbi_value, sil_options, sil_value

    create_neutral_insulation_callbacks("at")
    create_neutral_insulation_callbacks("bt")
    create_neutral_insulation_callbacks("terciario")

    log.info("Callbacks de níveis de isolamento (seleção individual) registrados.")
