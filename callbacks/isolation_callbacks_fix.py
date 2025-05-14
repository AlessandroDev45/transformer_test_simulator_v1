# callbacks/isolation_callbacks_fix.py
"""
Versão corrigida dos callbacks de isolamento automático.
AGORA APENAS ATUALIZA O STORE COM VALORES PADRÃO E POPULA OPTIONS.
O VALOR DOS DROPDOWNS É GERENCIADO POR populate_dynamic_dropdown_values_on_load.
"""

import logging

from dash import Input, Output, State
from dash.exceptions import PreventUpdate

# Manter os imports de app_core.isolation_repo e utils.store_diagnostics
from app_core.isolation_repo import derive_um, get_isolation_levels # <<< ESTE DEVE SER USADO
from utils.store_diagnostics import convert_numpy_types

log = logging.getLogger(__name__)


def register_isolation_callbacks(app_instance):
    """
    Registra callbacks para cálculo automático de níveis de isolamento.
    """
    log.info("Registrando callbacks de isolamento automático (versão corrigida - Store Only for NBI/SIL/TA/TI values)...")

    app_instance.suppress_callback_exceptions = True
    log.info(
        "suppress_callback_exceptions definido como True para garantir funcionamento dos callbacks"
    )

    def map_conexao(conexao):
        if not conexao: return ""
        mapping = {
            "estrela": "YN", "estrela_sem_neutro": "Y", "triangulo": "D",
            "ziguezague": "ZN", "ziguezague_sem_neutro": "Z",
        }
        return mapping.get(conexao, conexao)

    @app_instance.callback(
        [ # Outputs para recalcular quando a norma mudar (sem alteração)
            Output("tensao_at", "value", allow_duplicate=True),
            Output("tensao_bt", "value", allow_duplicate=True),
            Output("tensao_terciario", "value", allow_duplicate=True),
        ],
        [Input("norma_iso", "value")],
        [State("tensao_at", "value"), State("tensao_bt", "value"), State("tensao_terciario", "value")],
        prevent_initial_call=True,
    )
    def trigger_recalculation_on_standard_change(norma, tensao_at, tensao_bt, tensao_terciario):
        log.info(f"Norma alterada para {norma}. Disparando recálculo dos níveis de isolamento.")
        return tensao_at, tensao_bt, tensao_terciario

    # ⬇️ CALLBACK PARA O ENROLAMENTO AT - MODIFICADO
    @app_instance.callback(
        [ # ATENÇÃO: REMOVIDOS Output(..., "value") para NBI, SIL, TA, TI e seus neutros
            Output("classe_tensao_at", "value"), # Mantido
            Output("classe_tensao_at", "disabled"), # Mantido
            Output("nbi_at", "options"), # Mantido
            Output("sil_at", "options"), # Mantido
            Output("nbi_neutro_at", "options"), # Mantido
            Output("sil_neutro_at", "options"), # Mantido
            # Adicionando options para TA e TI
            Output("teste_tensao_aplicada_at", "options", allow_duplicate=True),
            Output("teste_tensao_induzida_at", "options", allow_duplicate=True),
            Output("transformer-inputs-store", "data", allow_duplicate=True), # Mantido
        ],
        [
            Input("tensao_at", "value"), Input("tensao_at_tap_maior", "value"),
            Input("conexao_at", "value"), Input("norma_iso", "value"),
            Input("tensao_bucha_neutro_at", "value"),
        ],
        [State("transformer-inputs-store", "data")],
        prevent_initial_call=True,
    )
    def auto_isolation_at(v_nom, v_tap_plus, conexao, norma, neutro_classe, store):
        if v_nom is None and v_tap_plus is None:
            raise PreventUpdate

        try:
            v_nom_float = float(v_nom) if v_nom else 0
            v_tap_plus_float = float(v_tap_plus) if v_tap_plus else 0
            v_max = max(v_nom_float, v_tap_plus_float)
            v_max_with_tolerance = v_max * 1.1
            um = derive_um(v_max_with_tolerance)
            conexao_mapped = map_conexao(conexao)

            levels_data_dict, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC")
            
            nbi_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_list", []) if val is not None]
            sil_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("sil_im_list", []) if val is not None]
            nbi_neutro_options_calc = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_neutro_list", []) if val is not None] # Renomeado para evitar conflito
            
            ta_options = [{"label": f"{val} kVrms", "value": str(val)} for val in levels_data_dict.get("tensao_aplicada_list", []) if val is not None]
            ti_options = [{"label": f"{val} kVrms", "value": str(val)} for val in levels_data_dict.get("tensao_induzida_list", []) if val is not None]

            sil_neutro_value_calculated = None
            sil_neutro_options = []
            # Usar nbi_neutro_options_calc para o dropdown do neutro se não houver classe de neutro específica
            final_nbi_neutro_options = nbi_neutro_options_calc 

            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    neutro_um_val = float(neutro_classe)
                    neutro_levels_data_dict, _ = get_isolation_levels(neutro_um_val, conexao_mapped, norma or "IEC")
                    
                    final_nbi_neutro_options = [{"label": f"{val} kVp", "value": str(val)} for val in neutro_levels_data_dict.get("nbi_list", []) if val is not None]
                    if final_nbi_neutro_options: 
                        default_nbi_neutro_for_sil_calc = float(final_nbi_neutro_options[0]["value"])
                        if neutro_um_val >= 300 and default_nbi_neutro_for_sil_calc is not None: 
                             sil_neutro_value_calculated = round(default_nbi_neutro_for_sil_calc * 0.75)
                             sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
                    
                    # Atualizar o valor padrão de nbi_neutro no levels_data_dict para o da classe do neutro
                    levels_data_dict["nbi_neutro"] = float(final_nbi_neutro_options[0]["value"]) if final_nbi_neutro_options else None

                except Exception as e_neutro:
                    log.warning(f"Erro ao processar níveis de isolamento para neutro AT (classe: {neutro_classe}): {e_neutro}")
                    if levels_data_dict.get("nbi_neutro") is not None and um >= 300:
                        sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
            elif levels_data_dict.get("nbi_neutro") is not None and um >= 300: 
                 sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                 sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []

            store = store or {}
            store_update_payload = {
                "classe_tensao_at": um,
                "nbi_at_list": levels_data_dict.get("nbi_list", []),
                "sil_at_list": levels_data_dict.get("sil_im_list", []),
                "nbi_neutro_at_list": levels_data_dict.get("nbi_neutro_list", []),
                "tensao_aplicada_at_list": levels_data_dict.get("tensao_aplicada_list", []),
                "tensao_induzida_at_list": levels_data_dict.get("tensao_induzida_list", []),
            }
            
            default_values_map = {
                "nbi_at": levels_data_dict.get("nbi"),
                "sil_at": levels_data_dict.get("sil_im"),
                "nbi_neutro_at": levels_data_dict.get("nbi_neutro"),
                "sil_neutro_at": sil_neutro_value_calculated,
                "teste_tensao_aplicada_at": levels_data_dict.get("tensao_aplicada"),
                "teste_tensao_induzida_at": levels_data_dict.get("tensao_induzida"),
            }

            for key, default_val in default_values_map.items():
                if store.get(key) is None or str(store.get(key,"")).strip() == "":
                    store_update_payload[key] = str(default_val) if default_val is not None else None
            
            store.update(store_update_payload)
            store_serializable = convert_numpy_types(store)

            log.info(f"Níveis de isolamento AT (STORE): Um={um}, NBI={store_serializable.get('nbi_at')}, SIL={store_serializable.get('sil_at')}, NBI_Neutro={store_serializable.get('nbi_neutro_at')}, SIL_Neutro={store_serializable.get('sil_neutro_at')}, TA={store_serializable.get('teste_tensao_aplicada_at')}, TI={store_serializable.get('teste_tensao_induzida_at')}")

            return (
                um, False, 
                nbi_options, sil_options, 
                final_nbi_neutro_options, sil_neutro_options, 
                ta_options, ti_options, 
                store_serializable,
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento AT: {e}", exc_info=True)
            raise PreventUpdate

    # ⬇️ CALLBACK PARA O ENROLAMENTO BT - MODIFICADO
    @app_instance.callback(
        [
            Output("classe_tensao_bt", "value"), Output("classe_tensao_bt", "disabled"),
            Output("nbi_bt", "options"), Output("sil_bt", "options"),
            Output("nbi_neutro_bt", "options"), Output("sil_neutro_bt", "options"),
            Output("teste_tensao_aplicada_bt", "options", allow_duplicate=True),
            Output("transformer-inputs-store", "data", allow_duplicate=True),
        ],
        [
            Input("tensao_bt", "value"), Input("conexao_bt", "value"),
            Input("norma_iso", "value"), Input("tensao_bucha_neutro_bt", "value"),
        ],
        [State("transformer-inputs-store", "data")],
        prevent_initial_call=True,
    )
    def auto_isolation_bt(v_nom, conexao, norma, neutro_classe, store):
        if v_nom is None: raise PreventUpdate
        try:
            v_nom_float = float(v_nom) if v_nom else 0
            v_max_with_tolerance = v_nom_float * 1.1
            um = derive_um(v_max_with_tolerance)
            conexao_mapped = map_conexao(conexao)
            levels_data_dict, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC") # Already changed in previous step, ensuring it stays _

            nbi_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_list", []) if val is not None]
            sil_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("sil_im_list", []) if val is not None]
            nbi_neutro_options_calc = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_neutro_list", []) if val is not None]
            ta_options = [{"label": f"{val} kVrms", "value": str(val)} for val in levels_data_dict.get("tensao_aplicada_list", []) if val is not None]

            sil_neutro_value_calculated = None
            sil_neutro_options = []
            final_nbi_neutro_options = nbi_neutro_options_calc

            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    neutro_um_val = float(neutro_classe)
                    neutro_levels_data_dict, _ = get_isolation_levels(neutro_um_val, conexao_mapped, norma or "IEC")
                    final_nbi_neutro_options = [{"label": f"{val} kVp", "value": str(val)} for val in neutro_levels_data_dict.get("nbi_list", []) if val is not None]
                    if final_nbi_neutro_options:
                        default_nbi_neutro_for_sil_calc = float(final_nbi_neutro_options[0]["value"])
                        if neutro_um_val >= 300 and default_nbi_neutro_for_sil_calc is not None:
                             sil_neutro_value_calculated = round(default_nbi_neutro_for_sil_calc * 0.75)
                             sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
                    levels_data_dict["nbi_neutro"] = float(final_nbi_neutro_options[0]["value"]) if final_nbi_neutro_options else None
                except Exception as e_neutro:
                    log.warning(f"Erro ao processar níveis de isolamento para neutro BT (classe: {neutro_classe}): {e_neutro}")
                    if levels_data_dict.get("nbi_neutro") is not None and um >= 300:
                        sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
            elif levels_data_dict.get("nbi_neutro") is not None and um >= 300:
                 sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                 sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []

            store = store or {}
            store_update_payload = {
                "classe_tensao_bt": um, 
                "nbi_bt_list": levels_data_dict.get("nbi_list", []),
                "sil_bt_list": levels_data_dict.get("sil_im_list", []),
                "nbi_neutro_bt_list": levels_data_dict.get("nbi_neutro_list", []),
                "tensao_aplicada_bt_list": levels_data_dict.get("tensao_aplicada_list", []),
            }
            default_values_map = {
                "nbi_bt": levels_data_dict.get("nbi"),
                "sil_bt": levels_data_dict.get("sil_im"), 
                "nbi_neutro_bt": levels_data_dict.get("nbi_neutro"),
                "sil_neutro_bt": sil_neutro_value_calculated,
                "teste_tensao_aplicada_bt": levels_data_dict.get("tensao_aplicada"),
            }
            for key, default_val in default_values_map.items():
                if store.get(key) is None or str(store.get(key,"")).strip() == "":
                    store_update_payload[key] = str(default_val) if default_val is not None else None
            
            store.update(store_update_payload)
            store_serializable = convert_numpy_types(store)
            log.info(f"Níveis de isolamento BT (STORE): Um={um}, NBI={store_serializable.get('nbi_bt')}, SIL={store_serializable.get('sil_bt')}, TA={store_serializable.get('teste_tensao_aplicada_bt')}")
            return (
                um, False, nbi_options, sil_options,
                final_nbi_neutro_options, sil_neutro_options, ta_options,
                store_serializable,
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento BT: {e}", exc_info=True)
            raise PreventUpdate

    # ⬇️ CALLBACK PARA O ENROLAMENTO TERCIÁRIO - MODIFICADO
    @app_instance.callback(
        [
            Output("classe_tensao_terciario", "value"), Output("classe_tensao_terciario", "disabled"),
            Output("nbi_terciario", "options"), Output("sil_terciario", "options"),
            Output("nbi_neutro_terciario", "options"), Output("sil_neutro_terciario", "options"),
            Output("teste_tensao_aplicada_terciario", "options", allow_duplicate=True),
            Output("transformer-inputs-store", "data", allow_duplicate=True),
        ],
        [
            Input("tensao_terciario", "value"), Input("conexao_terciario", "value"),
            Input("norma_iso", "value"), Input("tensao_bucha_neutro_terciario", "value"),
        ],
        [State("transformer-inputs-store", "data")],
        prevent_initial_call=True,
    )
    def auto_isolation_terciario(v_nom, conexao, norma, neutro_classe, store):
        if v_nom is None: raise PreventUpdate
        try:
            v_nom_float = float(v_nom) if v_nom else 0
            if v_nom_float == 0 : 
                store = store or {}
                keys_to_clear_terciario = [
                    "classe_tensao_terciario", "nbi_terciario", "sil_terciario",
                    "nbi_neutro_terciario", "sil_neutro_terciario", "teste_tensao_aplicada_terciario",
                    "nbi_terciario_list", "sil_terciario_list", "nbi_neutro_terciario_list", "tensao_aplicada_terciario_list"
                ]
                for key in keys_to_clear_terciario:
                    store[key] = None 
                    if key.endswith("_list"): store[key] = []

                empty_opts = [{"label": "-", "value": ""}]
                log.info("Tensão Terciário é zero. Limpando campos relacionados e store.")
                return (
                    None, True, 
                    empty_opts, empty_opts, 
                    empty_opts, empty_opts, 
                    empty_opts, 
                    convert_numpy_types(store)
                )

            v_max_with_tolerance = v_nom_float * 1.1
            um = derive_um(v_max_with_tolerance)
            conexao_mapped = map_conexao(conexao)
            levels_data_dict, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC") # Already changed in previous step, ensuring it stays _

            nbi_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_list", []) if val is not None]
            sil_options = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("sil_im_list", []) if val is not None]
            nbi_neutro_options_calc = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_neutro_list", []) if val is not None]
            ta_options = [{"label": f"{val} kVrms", "value": str(val)} for val in levels_data_dict.get("tensao_aplicada_list", []) if val is not None]

            sil_neutro_value_calculated = None
            sil_neutro_options = []
            final_nbi_neutro_options = nbi_neutro_options_calc

            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    neutro_um_val = float(neutro_classe)
                    neutro_levels_data_dict, _ = get_isolation_levels(neutro_um_val, conexao_mapped, norma or "IEC")
                    final_nbi_neutro_options = [{"label": f"{val} kVp", "value": str(val)} for val in neutro_levels_data_dict.get("nbi_list", []) if val is not None]
                    if final_nbi_neutro_options:
                        default_nbi_neutro_for_sil_calc = float(final_nbi_neutro_options[0]["value"])
                        if neutro_um_val >= 300 and default_nbi_neutro_for_sil_calc is not None:
                             sil_neutro_value_calculated = round(default_nbi_neutro_for_sil_calc * 0.75)
                             sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
                    levels_data_dict["nbi_neutro"] = float(final_nbi_neutro_options[0]["value"]) if final_nbi_neutro_options else None
                except Exception as e_neutro:
                    log.warning(f"Erro ao processar níveis de isolamento para neutro Terciário (classe: {neutro_classe}): {e_neutro}")
                    if levels_data_dict.get("nbi_neutro") is not None and um >= 300:
                        sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []
            elif levels_data_dict.get("nbi_neutro") is not None and um >= 300:
                 sil_neutro_value_calculated = round(float(levels_data_dict["nbi_neutro"]) * 0.75)
                 sil_neutro_options = [{"label": f"{sil_neutro_value_calculated} kVp", "value": str(sil_neutro_value_calculated)}] if sil_neutro_value_calculated is not None else []

            store = store or {}
            store_update_payload = {
                "classe_tensao_terciario": um, 
                "nbi_terciario_list": levels_data_dict.get("nbi_list", []),
                "sil_terciario_list": levels_data_dict.get("sil_im_list", []),
                "nbi_neutro_terciario_list": levels_data_dict.get("nbi_neutro_list", []),
                "tensao_aplicada_terciario_list": levels_data_dict.get("tensao_aplicada_list", []),
            }
            default_values_map = {
                "nbi_terciario": levels_data_dict.get("nbi"),
                "sil_terciario": levels_data_dict.get("sil_im"), 
                "nbi_neutro_terciario": levels_data_dict.get("nbi_neutro"),
                "sil_neutro_terciario": sil_neutro_value_calculated,
                "teste_tensao_aplicada_terciario": levels_data_dict.get("tensao_aplicada"),
            }
            for key, default_val in default_values_map.items():
                if store.get(key) is None or str(store.get(key,"")).strip() == "":
                    store_update_payload[key] = str(default_val) if default_val is not None else None

            store.update(store_update_payload)
            store_serializable = convert_numpy_types(store)
            log.info(f"Níveis de isolamento Terciário (STORE): Um={um}, NBI={store_serializable.get('nbi_terciario')}, SIL={store_serializable.get('sil_terciario')}, TA={store_serializable.get('teste_tensao_aplicada_terciario')}")
            return (
                um, False, nbi_options, sil_options,
                final_nbi_neutro_options, sil_neutro_options, ta_options,
                store_serializable,
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento Terciário: {e}", exc_info=True)
            raise PreventUpdate

    log.info("Callbacks de isolamento automático registrados com sucesso (versão Store Only).")
