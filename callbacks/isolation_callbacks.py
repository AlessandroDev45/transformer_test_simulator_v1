# callbacks/isolation_callbacks.py
"""
Callbacks para cálculo automático de níveis de isolamento.
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
    log.info("Registrando callbacks de isolamento automático...")

    # Forçar suppress_callback_exceptions para True
    app_instance.suppress_callback_exceptions = True
    log.info(
        "suppress_callback_exceptions definido como True para garantir funcionamento dos callbacks"
    )

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
            "ziguezague_sem_neutro": "Z",
        }
        return mapping.get(conexao, conexao)

    # ⬇️ CALLBACK PARA RECALCULAR QUANDO A NORMA MUDAR
    @app_instance.callback(
        [
            Output("tensao_at", "value", allow_duplicate=True),
            Output("tensao_bt", "value", allow_duplicate=True),
            Output("tensao_terciario", "value", allow_duplicate=True),
        ],
        [
            Input("norma_iso", "value"),
        ],
        [
            State("tensao_at", "value"),
            State("tensao_bt", "value"),
            State("tensao_terciario", "value"),
        ],
        prevent_initial_call=True,
    )
    def trigger_recalculation_on_standard_change(norma, tensao_at, tensao_bt, tensao_terciario):
        """
        Quando a norma muda, retorna os mesmos valores de tensão para forçar
        o recálculo dos níveis de isolamento com a nova norma.
        """
        log.info(f"Norma alterada para {norma}. Disparando recálculo dos níveis de isolamento.")
        # Retorna os mesmos valores para forçar o recálculo
        return tensao_at, tensao_bt, tensao_terciario

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
        prevent_initial_call=True,
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

            # Obter os níveis de isolamento e opções (ignoramos as opções padrão)
            levels, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI
            nbi_options = []
            for nbi_value in levels.get("nbi_list", []):
                if nbi_value is not None:
                    nbi_options.append({"label": f"{nbi_value} kVp", "value": nbi_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not nbi_options and levels["nbi"] is not None:
                nbi_options = [{"label": f"{levels['nbi']} kVp", "value": levels["nbi"]}]

            # Criar opções para o dropdown de SIL/IM
            sil_options = []
            for sil_value in levels.get("sil_im_list", []):
                if sil_value is not None:
                    sil_options.append({"label": f"{sil_value} kVp", "value": sil_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not sil_options and levels["sil_im"] is not None:
                sil_options = [{"label": f"{levels['sil_im']} kVp", "value": levels["sil_im"]}]

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(
                        neutro_um, conexao_mapped, norma or "IEC"
                    )

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    for neutro_nbi in neutro_levels.get("nbi_list", []):
                        if neutro_nbi is not None:
                            nbi_neutro_options.append(
                                {"label": f"{neutro_nbi} kVp", "value": neutro_nbi}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if nbi_neutro_options:
                        levels["nbi_neutro"] = nbi_neutro_options[0]["value"]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for neutro_nbi in neutro_levels.get("nbi_list", []):
                            if neutro_nbi is not None:
                                neutro_sil = round(neutro_nbi * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro AT: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            nbi_neutro_options.append(
                                {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                            )

                    # Se não temos opções da lista, mas temos um valor padrão, usar ele
                    if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [
                            {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                        ]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for nbi_neutro in levels.get("nbi_neutro_list", []):
                            if nbi_neutro is not None:
                                neutro_sil = round(nbi_neutro * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                        # Fallback para o cálculo baseado no valor padrão
                        elif levels["nbi_neutro"] is not None:
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [
                                {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                            ]
            else:
                # Cálculo padrão (60% do NBI principal)
                for nbi_neutro in levels.get("nbi_neutro_list", []):
                    if nbi_neutro is not None:
                        nbi_neutro_options.append(
                            {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                        )

                # Se não temos opções da lista, mas temos um valor padrão, usar ele
                if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [
                        {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                    ]

                # Calcular SIL/IM do neutro (75% do NBI do neutro)
                if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            neutro_sil = round(nbi_neutro * 0.75)
                            sil_neutro_options.append(
                                {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if sil_neutro_options:
                        sil_neutro_value = sil_neutro_options[0]["value"]
                    # Fallback para o cálculo baseado no valor padrão
                    elif levels["nbi_neutro"] is not None:
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [
                            {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                        ]

            # Atualiza store
            store = store or {}

            # Obter dados atuais do MCP para garantir que temos todos os dados
            if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
                mcp_data = app_instance.mcp.get_data("transformer-inputs-store")
                if mcp_data and isinstance(mcp_data, dict):
                    # Usar os dados do MCP como base para garantir que não perdemos dados
                    for key, value in mcp_data.items():
                        if key not in store:
                            store[key] = value

            # Atualizar apenas os campos de isolamento
            isolation_update = {
                "classe_tensao_at": um,
                "nbi_at": levels["nbi"],
                "sil_at": levels["sil_im"],
                "nbi_neutro_at": levels["nbi_neutro"],
                "sil_neutro_at": sil_neutro_value,
                "norma_iso": norma,
                # Adicionar listas completas para compatibilidade com outros módulos
                "nbi_at_list": levels.get("nbi_list", []),
                "sil_at_list": levels.get("sil_im_list", []),
                "nbi_neutro_at_list": levels.get("nbi_neutro_list", []),
            }

            # Atualizar o store com os dados de isolamento
            store.update(isolation_update)

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(
                f"Níveis de isolamento AT calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}"
            )

            return (
                um,  # value para classe_tensao_at
                False,  # disabled para classe_tensao_at (agora permitimos edição)
                nbi_options,  # options para nbi_at
                levels["nbi"],  # value para nbi_at
                sil_options,  # options para sil_at
                levels["sil_im"],  # value para sil_at
                nbi_neutro_options,  # options para nbi_neutro_at
                levels["nbi_neutro"],  # value para nbi_neutro_at
                sil_neutro_options,  # options para sil_neutro_at
                sil_neutro_value,  # value para sil_neutro_at
                store,  # data para transformer-inputs-store
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
        prevent_initial_call=True,
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

            # Obter os níveis de isolamento e opções (ignoramos as opções padrão)
            levels, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI
            nbi_options = []
            for nbi_value in levels.get("nbi_list", []):
                if nbi_value is not None:
                    nbi_options.append({"label": f"{nbi_value} kVp", "value": nbi_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not nbi_options and levels["nbi"] is not None:
                nbi_options = [{"label": f"{levels['nbi']} kVp", "value": levels["nbi"]}]

            # Criar opções para o dropdown de SIL/IM
            sil_options = []
            for sil_value in levels.get("sil_im_list", []):
                if sil_value is not None:
                    sil_options.append({"label": f"{sil_value} kVp", "value": sil_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not sil_options and levels["sil_im"] is not None:
                sil_options = [{"label": f"{levels['sil_im']} kVp", "value": levels["sil_im"]}]

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(
                        neutro_um, conexao_mapped, norma or "IEC"
                    )

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    for neutro_nbi in neutro_levels.get("nbi_list", []):
                        if neutro_nbi is not None:
                            nbi_neutro_options.append(
                                {"label": f"{neutro_nbi} kVp", "value": neutro_nbi}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if nbi_neutro_options:
                        levels["nbi_neutro"] = nbi_neutro_options[0]["value"]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for neutro_nbi in neutro_levels.get("nbi_list", []):
                            if neutro_nbi is not None:
                                neutro_sil = round(neutro_nbi * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro BT: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            nbi_neutro_options.append(
                                {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                            )

                    # Se não temos opções da lista, mas temos um valor padrão, usar ele
                    if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [
                            {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                        ]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for nbi_neutro in levels.get("nbi_neutro_list", []):
                            if nbi_neutro is not None:
                                neutro_sil = round(nbi_neutro * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                        # Fallback para o cálculo baseado no valor padrão
                        elif levels["nbi_neutro"] is not None:
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [
                                {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                            ]
            else:
                # Cálculo padrão (60% do NBI principal)
                for nbi_neutro in levels.get("nbi_neutro_list", []):
                    if nbi_neutro is not None:
                        nbi_neutro_options.append(
                            {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                        )

                # Se não temos opções da lista, mas temos um valor padrão, usar ele
                if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [
                        {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                    ]

                # Calcular SIL/IM do neutro (75% do NBI do neutro)
                if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            neutro_sil = round(nbi_neutro * 0.75)
                            sil_neutro_options.append(
                                {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if sil_neutro_options:
                        sil_neutro_value = sil_neutro_options[0]["value"]
                    # Fallback para o cálculo baseado no valor padrão
                    elif levels["nbi_neutro"] is not None:
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [
                            {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                        ]

            # Atualiza store
            store = store or {}

            # Obter dados atuais do MCP para garantir que temos todos os dados
            if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
                mcp_data = app_instance.mcp.get_data("transformer-inputs-store")
                if mcp_data and isinstance(mcp_data, dict):
                    # Usar os dados do MCP como base para garantir que não perdemos dados
                    for key, value in mcp_data.items():
                        if key not in store:
                            store[key] = value

            # Atualizar apenas os campos de isolamento
            isolation_update = {
                "classe_tensao_bt": um,
                "nbi_bt": levels["nbi"],
                "sil_bt": levels["sil_im"],
                "nbi_neutro_bt": levels["nbi_neutro"],
                "sil_neutro_bt": sil_neutro_value,
                "norma_iso": norma,
                # Adicionar listas completas para compatibilidade com outros módulos
                "nbi_bt_list": levels.get("nbi_list", []),
                "sil_bt_list": levels.get("sil_im_list", []),
                "nbi_neutro_bt_list": levels.get("nbi_neutro_list", []),
            }

            # Atualizar o store com os dados de isolamento
            store.update(isolation_update)

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(
                f"Níveis de isolamento BT calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}"
            )

            return (
                um,  # value para classe_tensao_bt
                False,  # disabled para classe_tensao_bt (agora permitimos edição)
                nbi_options,  # options para nbi_bt
                levels["nbi"],  # value para nbi_bt
                sil_options,  # options para sil_bt
                levels["sil_im"],  # value para sil_bt
                nbi_neutro_options,  # options para nbi_neutro_bt
                levels["nbi_neutro"],  # value para nbi_neutro_bt
                sil_neutro_options,  # options para sil_neutro_bt
                sil_neutro_value,  # value para sil_neutro_bt
                store,  # data para transformer-inputs-store
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
        prevent_initial_call=True,
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

            # Obter os níveis de isolamento e opções (ignoramos as opções padrão)
            levels, _ = get_isolation_levels(um, conexao_mapped, norma or "IEC")

            # Criar opções para o dropdown de NBI
            nbi_options = []
            for nbi_value in levels.get("nbi_list", []):
                if nbi_value is not None:
                    nbi_options.append({"label": f"{nbi_value} kVp", "value": nbi_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not nbi_options and levels["nbi"] is not None:
                nbi_options = [{"label": f"{levels['nbi']} kVp", "value": levels["nbi"]}]

            # Criar opções para o dropdown de SIL/IM
            sil_options = []
            for sil_value in levels.get("sil_im_list", []):
                if sil_value is not None:
                    sil_options.append({"label": f"{sil_value} kVp", "value": sil_value})

            # Se não temos opções da lista, mas temos um valor padrão, usar ele
            if not sil_options and levels["sil_im"] is not None:
                sil_options = [{"label": f"{levels['sil_im']} kVp", "value": levels["sil_im"]}]

            # Criar opções para o dropdown de NBI neutro
            nbi_neutro_options = []
            sil_neutro_options = []
            sil_neutro_value = None

            # Se temos uma classe de tensão para o neutro e a conexão tem neutro
            if neutro_classe and conexao_mapped in ["YN", "ZN"]:
                try:
                    # Usar a classe de tensão do neutro para buscar valores
                    neutro_um = float(neutro_classe)
                    neutro_levels, _ = get_isolation_levels(
                        neutro_um, conexao_mapped, norma or "IEC"
                    )

                    # Usar o NBI do neutro baseado na classe de tensão do neutro
                    for neutro_nbi in neutro_levels.get("nbi_list", []):
                        if neutro_nbi is not None:
                            nbi_neutro_options.append(
                                {"label": f"{neutro_nbi} kVp", "value": neutro_nbi}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if nbi_neutro_options:
                        levels["nbi_neutro"] = nbi_neutro_options[0]["value"]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if neutro_um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for neutro_nbi in neutro_levels.get("nbi_list", []):
                            if neutro_nbi is not None:
                                neutro_sil = round(neutro_nbi * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                except Exception as e:
                    log.warning(f"Erro ao calcular níveis de isolamento para neutro terciário: {e}")
                    # Fallback para o cálculo padrão (60% do NBI principal)
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            nbi_neutro_options.append(
                                {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                            )

                    # Se não temos opções da lista, mas temos um valor padrão, usar ele
                    if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                        nbi_neutro_options = [
                            {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                        ]

                    # Calcular SIL/IM do neutro (75% do NBI do neutro)
                    if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                        for nbi_neutro in levels.get("nbi_neutro_list", []):
                            if nbi_neutro is not None:
                                neutro_sil = round(nbi_neutro * 0.75)
                                sil_neutro_options.append(
                                    {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                                )

                        # Se temos opções, usar a primeira como valor padrão
                        if sil_neutro_options:
                            sil_neutro_value = sil_neutro_options[0]["value"]
                        # Fallback para o cálculo baseado no valor padrão
                        elif levels["nbi_neutro"] is not None:
                            sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                            sil_neutro_options = [
                                {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                            ]
            else:
                # Cálculo padrão (60% do NBI principal)
                for nbi_neutro in levels.get("nbi_neutro_list", []):
                    if nbi_neutro is not None:
                        nbi_neutro_options.append(
                            {"label": f"{nbi_neutro} kVp", "value": nbi_neutro}
                        )

                # Se não temos opções da lista, mas temos um valor padrão, usar ele
                if not nbi_neutro_options and levels["nbi_neutro"] is not None:
                    nbi_neutro_options = [
                        {"label": f"{levels['nbi_neutro']} kVp", "value": levels["nbi_neutro"]}
                    ]

                # Calcular SIL/IM do neutro (75% do NBI do neutro)
                if um >= 300:  # SIL/IM só existe para Um ≥ 300 kV
                    for nbi_neutro in levels.get("nbi_neutro_list", []):
                        if nbi_neutro is not None:
                            neutro_sil = round(nbi_neutro * 0.75)
                            sil_neutro_options.append(
                                {"label": f"{neutro_sil} kVp", "value": neutro_sil}
                            )

                    # Se temos opções, usar a primeira como valor padrão
                    if sil_neutro_options:
                        sil_neutro_value = sil_neutro_options[0]["value"]
                    # Fallback para o cálculo baseado no valor padrão
                    elif levels["nbi_neutro"] is not None:
                        sil_neutro_value = round(levels["nbi_neutro"] * 0.75)
                        sil_neutro_options = [
                            {"label": f"{sil_neutro_value} kVp", "value": sil_neutro_value}
                        ]

            # Atualiza store
            store = store or {}

            # Obter dados atuais do MCP para garantir que temos todos os dados
            if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
                mcp_data = app_instance.mcp.get_data("transformer-inputs-store")
                if mcp_data and isinstance(mcp_data, dict):
                    # Usar os dados do MCP como base para garantir que não perdemos dados
                    for key, value in mcp_data.items():
                        if key not in store:
                            store[key] = value

            # Atualizar apenas os campos de isolamento
            isolation_update = {
                "classe_tensao_terciario": um,
                "nbi_terciario": levels["nbi"],
                "sil_terciario": levels["sil_im"],
                "nbi_neutro_terciario": levels["nbi_neutro"],
                "sil_neutro_terciario": sil_neutro_value,
                "norma_iso": norma,
                # Adicionar listas completas para compatibilidade com outros módulos
                "nbi_terciario_list": levels.get("nbi_list", []),
                "sil_terciario_list": levels.get("sil_im_list", []),
                "nbi_neutro_terciario_list": levels.get("nbi_neutro_list", []),
            }

            # Atualizar o store com os dados de isolamento
            store.update(isolation_update)

            # Converter para tipos serializáveis
            store = convert_numpy_types(store)

            log.info(
                f"Níveis de isolamento terciário calculados: Um={um}, NBI={levels['nbi']}, SIL={levels['sil_im']}, NBI_neutro={levels['nbi_neutro']}, SIL_neutro={sil_neutro_value}"
            )

            return (
                um,  # value para classe_tensao_terciario
                False,  # disabled para classe_tensao_terciario (agora permitimos edição)
                nbi_options,  # options para nbi_terciario
                levels["nbi"],  # value para nbi_terciario
                sil_options,  # options para sil_terciario
                levels["sil_im"],  # value para sil_terciario
                nbi_neutro_options,  # options para nbi_neutro_terciario
                levels["nbi_neutro"],  # value para nbi_neutro_terciario
                sil_neutro_options,  # options para sil_neutro_terciario
                sil_neutro_value,  # value para sil_neutro_terciario
                store,  # data para transformer-inputs-store
            )
        except Exception as e:
            log.error(f"Erro ao calcular níveis de isolamento terciário: {e}")
            raise PreventUpdate
