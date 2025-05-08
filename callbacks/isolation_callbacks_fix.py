# callbacks/isolation_callbacks_fix.py
"""
Versão corrigida dos callbacks de isolamento automático.
"""

import logging
from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from app_core.isolation_repo import derive_um, get_isolation_levels
from utils.store_diagnostics import convert_numpy_types

log = logging.getLogger(__name__)

def register_isolation_callbacks(app_instance):
    """
    Registra callbacks para cálculo automático de níveis de isolamento.
    """
    log.info("Registrando callbacks de isolamento automático (versão corrigida)...")

    # Forçar suppress_callback_exceptions para True
    app_instance.suppress_callback_exceptions = True
    log.info("suppress_callback_exceptions definido como True para garantir funcionamento dos callbacks")

    # Mapeamento de valores de conexão para o formato esperado
    def map_conexao(conexao):
        """Mapeia o valor de conexão para o formato esperado."""
        if not conexao:
            return ""

        mapping = {
            "estrela": "YN",
            "estrela_sem_neutro": "Y",
            "triangulo": "D",
            "ziguezague": "ZN",
            "ziguezague_sem_neutro": "Z"
        }
        return mapping.get(conexao, conexao)

    # ⬇️ CALLBACK PARA BLOQUEAR TROCA DE NORMA
    @app_instance.callback(
        Output("norma_iso", "disabled"),
        [
            Input("classe_tensao_at", "value"),
            Input("classe_tensao_bt", "value"),
            Input("classe_tensao_terciario", "value"),
        ],
        prevent_initial_call=True,
    )
    def lock_norma(classe_at, classe_bt, classe_terciario):
        """Bloqueia a troca de norma quando qualquer classe de tensão já tiver valor."""
        if classe_at or classe_bt or classe_terciario:
            return True
        return False

    # ⬇️ CALLBACK PARA O ENROLAMENTO AT
    @app_instance.callback(
        Output("classe_tensao_at", "value"),
        Output("classe_tensao_at", "disabled"),
        Output("nbi_at", "options"),
        Output("nbi_at", "value"),
        Output("sil_at", "options"),
        Output("sil_at", "value"),
        Output("nbi_neutro_at", "options"),
        Output("nbi_neutro_at", "value"),
        Output("sil_neutro_at", "options"),
        Output("sil_neutro_at", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True),
        [
            Input("tensao_at", "value"),
            Input("tensao_at_tap_maior", "value"),
            Input("conexao_at", "value"),
            Input("norma_iso", "value"),
            Input("tensao_bucha_neutro_at", "value"),
        ],
        [
            State("transformer-inputs-store", "data"),
        ],
        prevent_initial_call=True
    )
    def auto_isolation_at(v_nom, v_tap_plus, conexao, norma, neutro_classe, store):
        """Calcula automaticamente níveis de isolamento para AT."""
        if v_nom is None and v_tap_plus is None:
            raise PreventUpdate

        try:
            # Converter para float com tratamento de erros
            v_nom_float = float(v_nom) if v_nom else 0
            v_tap_plus_float = float(v_tap_plus) if v_tap_plus else 0

            # Maior tensão fase-fase (kV)
            v_max = max(v_nom_float, v_tap_plus_float)

            # Aplicar tolerância (10%)
            v_max_with_tolerance = v_max * 1.1

            # Derivar a classe de tensão
            um = derive_um(v_max_with_tolerance)

            # Mapear o valor de conexão
            conexao_mapped = map_conexao(conexao)

            # Obter os níveis de isolamento e opções
            levels, options = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(neutro_um, conexao_mapped, norma or "IEC")

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    if neutro_levels["nbi"] is not None:
                        nbi_neutro_options = [{"label": f"{neutro_levels['nbi']} kVp", "value": neutro_levels["nbi"]}]
                        levels["nbi_neutro"] = neutro_levels["nbi"]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(neutro_levels["nbi"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro AT: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    if levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
            else:
                # Cálculo padrão (60% do NBI principal)
                if levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]

            # Atualiza store
            store = store or {}
            store.update({
                "classe_tensao_at": um,
                "nbi_at": levels["nbi"],
                "sil_at": levels["sil_im"],
                "nbi_neutro_at": levels["nbi_neutro"],
                "sil_neutro_at": sil_neutro_value,
                "norma_iso": norma,
            })

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(f"Níveis de isolamento AT calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}")

            return (
                um,  # value para classe_tensao_at
                True,  # disabled para classe_tensao_at
                options,  # options para nbi_at
                levels["nbi"],  # value para nbi_at
                options,  # options para sil_at (mesma lista)
                levels["sil_im"],  # value para sil_at
                nbi_neutro_options,  # options para nbi_neutro_at
                levels["nbi_neutro"],  # value para nbi_neutro_at
                sil_neutro_options,  # options para sil_neutro_at
                sil_neutro_value,  # value para sil_neutro_at
                store  # data para transformer-inputs-store
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento AT: {e}")
            raise PreventUpdate

    # ⬇️ CALLBACK PARA O ENROLAMENTO BT
    @app_instance.callback(
        Output("classe_tensao_bt", "value"),
        Output("classe_tensao_bt", "disabled"),
        Output("nbi_bt", "options"),
        Output("nbi_bt", "value"),
        Output("sil_bt", "options"),
        Output("sil_bt", "value"),
        Output("nbi_neutro_bt", "options"),
        Output("nbi_neutro_bt", "value"),
        Output("sil_neutro_bt", "options"),
        Output("sil_neutro_bt", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True),
        [
            Input("tensao_bt", "value"),
            Input("conexao_bt", "value"),
            Input("norma_iso", "value"),
            Input("tensao_bucha_neutro_bt", "value"),
        ],
        [
            State("transformer-inputs-store", "data"),
        ],
        prevent_initial_call=True
    )
    def auto_isolation_bt(v_nom, conexao, norma, neutro_classe, store):
        """Calcula automaticamente níveis de isolamento para BT."""
        if v_nom is None:
            raise PreventUpdate

        try:
            # Converter para float com tratamento de erros
            v_nom_float = float(v_nom) if v_nom else 0

            # Aplicar tolerância (10%)
            v_max_with_tolerance = v_nom_float * 1.1

            # Derivar a classe de tensão
            um = derive_um(v_max_with_tolerance)

            # Mapear o valor de conexão
            conexao_mapped = map_conexao(conexao)

            # Obter os níveis de isolamento e opções
            levels, options = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(neutro_um, conexao_mapped, norma or "IEC")

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    if neutro_levels["nbi"] is not None:
                        nbi_neutro_options = [{"label": f"{neutro_levels['nbi']} kVp", "value": neutro_levels["nbi"]}]
                        levels["nbi_neutro"] = neutro_levels["nbi"]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(neutro_levels["nbi"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro BT: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    if levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
            else:
                # Cálculo padrão (60% do NBI principal)
                if levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]

            # Atualiza store
            store = store or {}
            store.update({
                "classe_tensao_bt": um,
                "nbi_bt": levels["nbi"],
                "sil_bt": levels["sil_im"],
                "nbi_neutro_bt": levels["nbi_neutro"],
                "sil_neutro_bt": sil_neutro_value,
                "norma_iso": norma,
            })

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(f"Níveis de isolamento BT calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}")

            return (
                um,  # value para classe_tensao_bt
                True,  # disabled para classe_tensao_bt
                options,  # options para nbi_bt
                levels["nbi"],  # value para nbi_bt
                options,  # options para sil_bt (mesma lista)
                levels["sil_im"],  # value para sil_bt
                nbi_neutro_options,  # options para nbi_neutro_bt
                levels["nbi_neutro"],  # value para nbi_neutro_bt
                sil_neutro_options,  # options para sil_neutro_bt
                sil_neutro_value,  # value para sil_neutro_bt
                store  # data para transformer-inputs-store
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento BT: {e}")
            raise PreventUpdate

    # ⬇️ CALLBACK PARA O ENROLAMENTO TERCIÁRIO
    @app_instance.callback(
        Output("classe_tensao_terciario", "value"),
        Output("classe_tensao_terciario", "disabled"),
        Output("nbi_terciario", "options"),
        Output("nbi_terciario", "value"),
        Output("sil_terciario", "options"),
        Output("sil_terciario", "value"),
        Output("nbi_neutro_terciario", "options"),
        Output("nbi_neutro_terciario", "value"),
        Output("sil_neutro_terciario", "options"),
        Output("sil_neutro_terciario", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True),
        [
            Input("tensao_terciario", "value"),
            Input("conexao_terciario", "value"),
            Input("norma_iso", "value"),
            Input("tensao_bucha_neutro_terciario", "value"),
        ],
        [
            State("transformer-inputs-store", "data"),
        ],
        prevent_initial_call=True
    )
    def auto_isolation_terciario(v_nom, conexao, norma, neutro_classe, store):
        """Calcula automaticamente níveis de isolamento para o terciário."""
        if v_nom is None:
            raise PreventUpdate

        try:
            # Converter para float com tratamento de erros
            v_nom_float = float(v_nom) if v_nom else 0

            # Aplicar tolerância (10%)
            v_max_with_tolerance = v_nom_float * 1.1

            # Derivar a classe de tensão
            um = derive_um(v_max_with_tolerance)

            # Mapear o valor de conexão
            conexao_mapped = map_conexao(conexao)

            # Obter os níveis de isolamento e opções
            levels, options = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(neutro_um, conexao_mapped, norma or "IEC")

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    if neutro_levels["nbi"] is not None:
                        nbi_neutro_options = [{"label": f"{neutro_levels['nbi']} kVp", "value": neutro_levels["nbi"]}]
                        levels["nbi_neutro"] = neutro_levels["nbi"]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(neutro_levels["nbi"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro terciário: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    if levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                        # Calcular SIL/IM do neutro (75% do NBI do neutro)
                        if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]
            else:
                # Cálculo padrão (60% do NBI principal)
                if levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [{"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [{"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}]

            # Atualiza store
            store = store or {}
            store.update({
                "classe_tensao_terciario": um,
                "nbi_terciario": levels["nbi"],
                "sil_terciario": levels["sil_im"],
                "nbi_neutro_terciario": levels["nbi_neutro"],
                "sil_neutro_terciario": sil_neutro_value,
                "norma_iso": norma,
            })

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(f"Níveis de isolamento terciário calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}")

            return (
                um,  # value para classe_tensao_terciario
                True,  # disabled para classe_tensao_terciario
                options,  # options para nbi_terciario
                levels["nbi"],  # value para nbi_terciario
                options,  # options para sil_terciario (mesma lista)
                levels["sil_im"],  # value para sil_terciario
                nbi_neutro_options,  # options para nbi_neutro_terciario
                levels["nbi_neutro"],  # value para nbi_neutro_terciario
                sil_neutro_options,  # options para sil_neutro_terciario
                sil_neutro_value,  # value para sil_neutro_terciario
                store  # data para transformer-inputs-store
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento terciário: {e}")
            raise PreventUpdate
