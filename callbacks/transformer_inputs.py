# callbacks/transformer_inputs.py
"""
Módulo transformer_inputs que usa o padrão de registro centralizado.
"""
import logging

from dash import Input, Output, html, no_update # Adicionado no_update

# Não importar app diretamente para evitar importações circulares
from dash.exceptions import PreventUpdate
from utils.store_diagnostics import convert_numpy_types

log = logging.getLogger(__name__)
log.info("============ MÓDULO TRANSFORMER_INPUTS CARREGADO ============")
log.info(f"Nível de log: {logging.getLevelName(log.getEffectiveLevel())}")
log.info(f"Handlers configurados: {[h.__class__.__name__ for h in log.handlers]}")
log.info("=============================================================")

def register_transformer_inputs_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de transformer_inputs.
    Esta função é chamada por app.py durante a inicialização.
    """
    log.info(f"Registrando callbacks do módulo transformer_inputs para app {app_instance.title}...")

    @app_instance.callback(
        [
            Output("corrente_nominal_at", "value"),
            Output("corrente_nominal_bt", "value"),
            Output("corrente_nominal_terciario", "value"),
            Output("corrente_nominal_at_tap_maior", "value"),
            Output("corrente_nominal_at_tap_menor", "value"),
        ],
        [
            Input("potencia_mva", "value"), Input("frequencia", "value"),
            Input("grupo_ligacao", "value"), Input("liquido_isolante", "value"),
            Input("elevacao_oleo_topo", "value"), Input("elevacao_enrol", "value"),
            Input("tipo_transformador", "value"), Input("tipo_isolamento", "value"),
            Input("norma_iso", "value"), Input("peso_total", "value"),
            Input("peso_parte_ativa", "value"), Input("peso_oleo", "value"),
            Input("peso_tanque_acessorios", "value"), Input("tensao_at", "value"),
            Input("classe_tensao_at", "value"), Input("impedancia", "value"),
            Input("nbi_at", "value"), Input("sil_at", "value"), Input("conexao_at", "value"),
            Input("tensao_bucha_neutro_at", "value"), Input("nbi_neutro_at", "value"),
            Input("sil_neutro_at", "value"), Input("tensao_at_tap_maior", "value"),
            Input("impedancia_tap_maior", "value"), Input("tensao_at_tap_menor", "value"),
            Input("impedancia_tap_menor", "value"), Input("teste_tensao_aplicada_at", "value"),
            Input("teste_tensao_induzida_at", "value"), Input("tensao_bt", "value"),
            Input("classe_tensao_bt", "value"), Input("nbi_bt", "value"),
            Input("sil_bt", "value"), Input("conexao_bt", "value"),
            Input("tensao_bucha_neutro_bt", "value"), Input("nbi_neutro_bt", "value"),
            Input("sil_neutro_bt", "value"), Input("teste_tensao_aplicada_bt", "value"),
            Input("tensao_terciario", "value"), Input("classe_tensao_terciario", "value"),
            Input("nbi_terciario", "value"), Input("sil_terciario", "value"),
            Input("conexao_terciario", "value"), Input("tensao_bucha_neutro_terciario", "value"),
            Input("nbi_neutro_terciario", "value"), Input("sil_neutro_terciario", "value"),
            Input("teste_tensao_aplicada_terciario", "value"),
        ],
        prevent_initial_call=False, priority=1000,
    )
    def update_transformer_calculations_and_mcp(
        potencia_mva, frequencia, grupo_ligacao, liquido_isolante, elevacao_oleo_topo,
        elevacao_enrol, tipo_transformador, tipo_isolamento, norma_iso, peso_total,
        peso_parte_ativa, peso_oleo, peso_tanque_acessorios, tensao_at, classe_tensao_at,
        impedancia, nbi_at, sil_at, conexao_at, tensao_bucha_neutro_at, nbi_neutro_at,
        sil_neutro_at, tensao_at_tap_maior, impedancia_tap_maior, tensao_at_tap_menor,
        impedancia_tap_menor, teste_tensao_aplicada_at, teste_tensao_induzida_at,
        tensao_bt, classe_tensao_bt, nbi_bt, sil_bt, conexao_bt, tensao_bucha_neutro_bt,
        nbi_neutro_bt, sil_neutro_bt, teste_tensao_aplicada_bt, tensao_terciario,
        classe_tensao_terciario, nbi_terciario, sil_terciario, conexao_terciario,
        tensao_bucha_neutro_terciario, nbi_neutro_terciario, sil_neutro_terciario,
        teste_tensao_aplicada_terciario
    ):
        from dash import ctx
        log.debug(f"[UpdateTransformerCalc] Acionado por: {ctx.triggered_id if ctx.triggered else 'Inicial'}")

        corrente_at, corrente_bt, corrente_terciario = None, None, None
        corrente_at_tap_maior, corrente_at_tap_menor = None, None

        try:
            transformer_data_for_currents = {
                "tipo_transformador": tipo_transformador, "potencia_mva": potencia_mva,
                "tensao_at": tensao_at, "tensao_at_tap_maior": tensao_at_tap_maior,
                "tensao_at_tap_menor": tensao_at_tap_menor, "tensao_bt": tensao_bt,
                "tensao_terciario": tensao_terciario,
            }
            from utils.elec import calculate_nominal_currents
            calculated_currents = calculate_nominal_currents(transformer_data_for_currents)
            corrente_at = calculated_currents.get("corrente_nominal_at")
            corrente_bt = calculated_currents.get("corrente_nominal_bt")
            corrente_terciario = calculated_currents.get("corrente_nominal_terciario")
            corrente_at_tap_maior = calculated_currents.get("corrente_nominal_at_tap_maior")
            corrente_at_tap_menor = calculated_currents.get("corrente_nominal_at_tap_menor")

            if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
                mcp_snapshot_before_update = app_instance.mcp.get_data("transformer-inputs-store") or {}
                data_to_save_to_mcp = mcp_snapshot_before_update.copy()

                direct_input_fields_map = {
                    "potencia_mva": potencia_mva, "frequencia": frequencia, "grupo_ligacao": grupo_ligacao,
                    "liquido_isolante": liquido_isolante, "elevacao_oleo_topo": elevacao_oleo_topo,
                    "elevacao_enrol": elevacao_enrol, "tipo_transformador": tipo_transformador,
                    "tipo_isolamento": tipo_isolamento, "norma_iso": norma_iso,
                    "peso_total": peso_total, "peso_parte_ativa": peso_parte_ativa, "peso_oleo": peso_oleo,
                    "peso_tanque_acessorios": peso_tanque_acessorios, "tensao_at": tensao_at,
                    "classe_tensao_at": classe_tensao_at, "impedancia": impedancia, "conexao_at": conexao_at,
                    "tensao_bucha_neutro_at": tensao_bucha_neutro_at, "tensao_at_tap_maior": tensao_at_tap_maior,
                    "impedancia_tap_maior": impedancia_tap_maior, "tensao_at_tap_menor": tensao_at_tap_menor,
                    "impedancia_tap_menor": impedancia_tap_menor, "tensao_bt": tensao_bt,
                    "classe_tensao_bt": classe_tensao_bt, "conexao_bt": conexao_bt,
                    "tensao_bucha_neutro_bt": tensao_bucha_neutro_bt, "tensao_terciario": tensao_terciario,
                    "classe_tensao_terciario": classe_tensao_terciario, "conexao_terciario": conexao_terciario,
                    "tensao_bucha_neutro_terciario": tensao_bucha_neutro_terciario,
                }
                dynamic_fields_from_form_map = {
                    "nbi_at": nbi_at, "sil_at": sil_at, "nbi_neutro_at": nbi_neutro_at,
                    "sil_neutro_at": sil_neutro_at, "teste_tensao_aplicada_at": teste_tensao_aplicada_at,
                    "teste_tensao_induzida_at": teste_tensao_induzida_at, "nbi_bt": nbi_bt, "sil_bt": sil_bt,
                    "nbi_neutro_bt": nbi_neutro_bt, "sil_neutro_bt": sil_neutro_bt,
                    "teste_tensao_aplicada_bt": teste_tensao_aplicada_bt, "nbi_terciario": nbi_terciario,
                    "sil_terciario": sil_terciario, "nbi_neutro_terciario": nbi_neutro_terciario,
                    "sil_neutro_terciario": sil_neutro_terciario,
                    "teste_tensao_aplicada_terciario": teste_tensao_aplicada_terciario,
                }

                for key, form_value in direct_input_fields_map.items():
                    # Se o valor do formulário for uma string vazia, trata como None.
                    # Caso contrário, usa o valor do formulário.
                    # Isto permite limpar campos numéricos para None.
                    if isinstance(form_value, str) and form_value.strip() == "":
                        data_to_save_to_mcp[key] = None
                    elif form_value is not None:
                        data_to_save_to_mcp[key] = form_value
                    elif key not in data_to_save_to_mcp: # Se era None e não estava no store
                        data_to_save_to_mcp[key] = None
                    # Se era None e estava no store, mantém o valor do store (já copiado)
                    # ou permite que seja None se o objetivo é limpar.
                    # Para garantir que um campo possa ser explicitamente limpo para None:
                    elif form_value is None and key in data_to_save_to_mcp:
                         data_to_save_to_mcp[key] = None


                for key, form_value in dynamic_fields_from_form_map.items():
                    # Para campos dinâmicos (dropdowns de níveis de isolamento),
                    # Tratar da mesma forma que os campos diretos para garantir consistência
                    if isinstance(form_value, str) and form_value.strip() == "":
                        data_to_save_to_mcp[key] = None
                    elif form_value is not None:
                        data_to_save_to_mcp[key] = form_value  # Armazenar o valor diretamente, sem converter para string
                    elif key not in data_to_save_to_mcp:  # Se era None e não estava no store
                        data_to_save_to_mcp[key] = None
                    elif form_value is None and key in data_to_save_to_mcp:
                        data_to_save_to_mcp[key] = None

                    # Log para todos os campos de dropdown para melhor diagnóstico
                    log.info(f"[UpdateTransformerCalc] Salvando valor de dropdown: {key}={data_to_save_to_mcp.get(key)}")

                # Garantir que teste_tensao_induzida também seja mantido para compatibilidade
                if data_to_save_to_mcp.get("teste_tensao_induzida_at") is not None:
                    data_to_save_to_mcp["teste_tensao_induzida"] = data_to_save_to_mcp["teste_tensao_induzida_at"]
                    log.info(f"[UpdateTransformerCalc] Mantendo compatibilidade: teste_tensao_induzida={data_to_save_to_mcp['teste_tensao_induzida']}")

                data_to_save_to_mcp["corrente_nominal_at"] = corrente_at
                data_to_save_to_mcp["corrente_nominal_bt"] = corrente_bt
                data_to_save_to_mcp["corrente_nominal_terciario"] = corrente_terciario
                data_to_save_to_mcp["corrente_nominal_at_tap_maior"] = corrente_at_tap_maior
                data_to_save_to_mcp["corrente_nominal_at_tap_menor"] = corrente_at_tap_menor

                iac_at_calc, iac_bt_calc, iac_terciario_calc = None, None, None
                norma_para_iac = data_to_save_to_mcp.get("norma_iso")
                if norma_para_iac and "IEC" in norma_para_iac:
                    for winding_prefix_iac, nbi_key_iac in [("at", "nbi_at"), ("bt", "nbi_bt"), ("terciario", "nbi_terciario")]:
                        nbi_val_str = data_to_save_to_mcp.get(nbi_key_iac, "")
                        iac_val = None
                        if nbi_val_str and str(nbi_val_str).strip() != "":
                            try:
                                iac_val = round(1.1 * float(nbi_val_str), 2)
                            except (ValueError, TypeError):
                                log.warning(f"Não foi possível calcular IAC para {winding_prefix_iac} a partir de {nbi_key_iac}: {nbi_val_str}")
                        if winding_prefix_iac == "at": iac_at_calc = iac_val
                        elif winding_prefix_iac == "bt": iac_bt_calc = iac_val
                        elif winding_prefix_iac == "terciario": iac_terciario_calc = iac_val

                data_to_save_to_mcp["iac_at"] = iac_at_calc
                data_to_save_to_mcp["iac_bt"] = iac_bt_calc
                data_to_save_to_mcp["iac_terciario"] = iac_terciario_calc

                serializable_data = convert_numpy_types(data_to_save_to_mcp, debug_path="update_transformer_inputs_final")
                app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
                app_instance.mcp.save_to_disk(force=True)
                log.debug("[UpdateTransformerCalc] MCP atualizado e salvo no disco.")

                # Log para verificar os valores de todos os dropdowns após salvar no MCP
                saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                dropdown_keys = [
                    "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                    "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                    "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                    "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
                ]
                for key in dropdown_keys:
                    log.info(f"[UpdateTransformerCalc] Valor de dropdown após salvar no MCP: {key}={saved_data.get(key)}")

                try:
                    latest_data_for_propagation = app_instance.mcp.get_data("transformer-inputs-store")
                    if not latest_data_for_propagation or not any(latest_data_for_propagation.get(k) is not None for k in ["potencia_mva", "tensao_at", "tensao_bt"]):
                        log.warning("[UpdateTransformerCalc] Dados insuficientes para propagação. Abortando.")
                    else:
                        from utils.mcp_persistence import ensure_mcp_data_propagation
                        target_stores = [
                            "losses-store", "impulse-store", "dieletric-analysis-store",
                            "applied-voltage-store", "induced-voltage-store", "short-circuit-store",
                            "temperature-rise-store", "comprehensive-analysis-store",
                        ]
                        ensure_mcp_data_propagation(app_instance, "transformer-inputs-store", target_stores)
                except Exception as e_prop:
                    log.error(f"[UpdateTransformerCalc] Erro ao propagar dados: {e_prop}", exc_info=True)

        except Exception as e_main:
            log.error(f"[UpdateTransformerCalc] Erro geral no callback: {e_main}", exc_info=True)

        return (
            corrente_at, corrente_bt, corrente_terciario,
            corrente_at_tap_maior, corrente_at_tap_menor,
        )

    # NOVO CALLBACK C: Para popular os valores dos dropdowns NBI/SIL/TA/TI
    output_list_initial_values = [
        Output("nbi_at", "value", allow_duplicate=True),
        Output("sil_at", "value", allow_duplicate=True),
        Output("teste_tensao_aplicada_at", "value", allow_duplicate=True),
        Output("teste_tensao_induzida_at", "value", allow_duplicate=True),
        Output("nbi_neutro_at", "value", allow_duplicate=True),
        Output("sil_neutro_at", "value", allow_duplicate=True),
        Output("nbi_bt", "value", allow_duplicate=True),
        Output("sil_bt", "value", allow_duplicate=True),
        Output("teste_tensao_aplicada_bt", "value", allow_duplicate=True),
        Output("nbi_neutro_bt", "value", allow_duplicate=True),
        Output("sil_neutro_bt", "value", allow_duplicate=True),
        Output("nbi_terciario", "value", allow_duplicate=True),
        Output("sil_terciario", "value", allow_duplicate=True),
        Output("teste_tensao_aplicada_terciario", "value", allow_duplicate=True),
        Output("nbi_neutro_terciario", "value", allow_duplicate=True),
        Output("sil_neutro_terciario", "value", allow_duplicate=True),
    ]

    @app_instance.callback(
        output_list_initial_values,
        [Input("transformer-inputs-store", "data"), Input("url", "pathname")],
        prevent_initial_call=False
    )
    def populate_dynamic_dropdown_values_on_load(store_data, pathname):
        from dash import ctx
        try:
            from utils.routes import ROUTE_HOME, normalize_pathname
        except ImportError:
            log.error("[PopulateDynamicValues] Falha ao importar utils.routes.")
            ROUTE_HOME = "/" # Fallback
            normalize_pathname = lambda p: p

        triggered_id = ctx.triggered_id
        log.debug(f"[PopulateDynamicValues] Acionado por: {triggered_id}. Pathname: {pathname}")

        clean_path = normalize_pathname(pathname)
        if clean_path != ROUTE_HOME:
            log.debug(f"[PopulateDynamicValues] Não na página Dados Básicos ('{ROUTE_HOME}'). Path: {clean_path}. Abortando.")
            return [no_update] * len(output_list_initial_values)

        if not store_data or not isinstance(store_data, dict):
            log.warning("[PopulateDynamicValues] Store de Dados Básicos vazio ou inválido. Retornando no_update.")
            return [no_update] * len(output_list_initial_values)

        log.info(f"[PopulateDynamicValues] Populando valores dos dropdowns dinâmicos na página '{clean_path}'.")

        # Log dos valores de isolamento no store
        isolation_keys = ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]
        for key in isolation_keys:
            log.info(f"[PopulateDynamicValues] Valor de isolamento no store: {key}={store_data.get(key)}")

        def get_dropdown_val(key, default=""):
            """
            Obtém o valor do dropdown do store de forma consistente.
            Retorna o valor original sem conversão para garantir compatibilidade.
            """
            val = store_data.get(key)
            log.info(f"[PopulateDynamicValues] Obtendo valor para dropdown {key}: {val}")
            # Retornar o valor original sem conversão para string
            return val if val is not None else default

        values_tuple = (
            get_dropdown_val("nbi_at"), get_dropdown_val("sil_at"),
            get_dropdown_val("teste_tensao_aplicada_at"), get_dropdown_val("teste_tensao_induzida_at"),
            get_dropdown_val("nbi_neutro_at"), get_dropdown_val("sil_neutro_at"),
            get_dropdown_val("nbi_bt"), get_dropdown_val("sil_bt"),
            get_dropdown_val("teste_tensao_aplicada_bt"),
            get_dropdown_val("nbi_neutro_bt"), get_dropdown_val("sil_neutro_bt"),
            get_dropdown_val("nbi_terciario"), get_dropdown_val("sil_terciario"),
            get_dropdown_val("teste_tensao_aplicada_terciario"),
            get_dropdown_val("nbi_neutro_terciario"), get_dropdown_val("sil_neutro_terciario")
        )
        log.debug(f"[PopulateDynamicValues] Valores a serem definidos: {values_tuple}")
        return values_tuple

    # Callback para marcar o formulário como "sujo" quando qualquer campo for alterado
    @app_instance.callback(
        Output("dirty-flag", "data", allow_duplicate=True),
        [
            Input({"type": "transformer-input", "id": "ALL"}, "value"),
            # Incluir todos os inputs individuais também para garantir que todos os campos sejam capturados
            Input("potencia_mva", "value"),
            Input("tensao_at", "value"),
            Input("tensao_bt", "value"),
            Input("frequencia", "value"),
            # Adicione outros campos conforme necessário
        ],
        prevent_initial_call=True,
    )
    def mark_dirty(*_):
        """
        Marca o formulário como "sujo" quando qualquer campo for alterado.
        Isso aciona o callback de auto-save com debounce.
        """
        from datetime import datetime

        log.debug(
            f"[mark_dirty] Formulário marcado como sujo às {datetime.now().strftime('%H:%M:%S')}"
        )
        return True

    # Callback de auto-save com debounce
    @app_instance.callback(
        Output("last-save-ok", "children"),
        Input("dirty-flag", "data"),
        prevent_initial_call=True,
        # Usar debounce para evitar salvar a cada alteração
        # Aguardar 1 segundo após a última alteração antes de salvar
        debounce=True,
        interval=1000,  # 1 segundo
    )
    def autosave_with_debounce(dirty_flag):
        """
        Salva automaticamente os dados no MCP após um período de inatividade.
        Segue o padrão de "fonte única da verdade", onde transformer-inputs-store
        é a fonte autoritativa para todos os dados básicos do transformador.
        """
        if not dirty_flag:
            return ""

        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")

        try:
            # Obter os dados atuais do formulário
            # Aqui precisamos obter os valores diretamente do MCP, pois não temos acesso aos inputs
            current_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

            # Serializar dados para salvar no MCP
            from utils.store_diagnostics import convert_numpy_types
            serializable_data = convert_numpy_types(
                current_data, debug_path="autosave_with_debounce"
            )

            # Verificar se os dados essenciais estão presentes
            from utils.mcp_persistence import ESSENTIAL, _dados_ok
            if not _dados_ok(serializable_data):
                missing_fields = [k for k in ESSENTIAL if serializable_data.get(k) in (None, "", 0)]
                log.warning(f"[autosave_with_debounce] Dados essenciais ausentes: {missing_fields}")

                # Obter os dados atuais do MCP para mesclar
                mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

                # Mesclar dados essenciais
                for key in ESSENTIAL:
                    if serializable_data.get(key) in (None, "", 0) and mcp_data.get(key) not in (
                        None,
                        "",
                        0,
                    ):
                        serializable_data[key] = mcp_data.get(key)
                        log.info(
                            f"[autosave_with_debounce] Mantido valor existente para {key}: {mcp_data.get(key)}"
                        )

            # Garantir que teste_tensao_induzida também seja mantido para compatibilidade
            if serializable_data.get("teste_tensao_induzida_at") is not None:
                serializable_data["teste_tensao_induzida"] = serializable_data["teste_tensao_induzida_at"]
                log.info(f"[autosave_with_debounce] Mantendo compatibilidade: teste_tensao_induzida={serializable_data['teste_tensao_induzida']}")

            # Salvar no MCP usando set_data diretamente
            app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
            log.info(f"[autosave_with_debounce] MCP atualizado automaticamente às {now}")

            # Verificar se os dados foram salvos corretamente
            saved_data = app_instance.mcp.get_data("transformer-inputs-store")
            log.info(
                f"[autosave_with_debounce] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
            )

            # Log para verificar os valores de todos os dropdowns após salvar no MCP
            dropdown_keys = [
                "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
            ]
            for key in dropdown_keys:
                log.info(f"[autosave_with_debounce] Valor de dropdown após salvar no MCP: {key}={saved_data.get(key)}")

            # Propagar dados para outros stores usando o padrão de "fonte única da verdade"
            # transformer-inputs-store é a fonte autoritativa para todos os dados básicos
            from utils.mcp_persistence import ensure_mcp_data_propagation

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
            ensure_mcp_data_propagation(app_instance, "transformer-inputs-store", target_stores)

            return f"✓ Salvo automaticamente às {now}"
        except Exception as e:
            log.error(f"[autosave_with_debounce] Erro ao salvar automaticamente: {e}")
            return f"✗ Erro ao salvar às {now}"

    # Callback para salvar ao trocar de página
    @app_instance.callback(
        Output("dummy-output", "children", allow_duplicate=True),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )
    def flush_on_page_change(pathname):
        """
        Salva os dados no MCP quando o usuário navega para outra página.
        Segue o padrão de "fonte única da verdade", onde transformer-inputs-store
        é a fonte autoritativa para todos os dados básicos do transformador.
        """
        if pathname and not pathname.startswith("/transformer-inputs"):
            log.info(f"[flush_on_page_change] Navegando para {pathname}, salvando dados no MCP")
            try:
                # Obter os dados atuais do formulário
                current_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

                # Serializar dados para salvar no MCP
                from utils.store_diagnostics import convert_numpy_types
                serializable_data = convert_numpy_types(
                    current_data, debug_path="flush_on_page_change"
                )

                # Verificar se os dados essenciais estão presentes
                from utils.mcp_persistence import ESSENTIAL, _dados_ok
                if not _dados_ok(serializable_data):
                    missing_fields = [
                        k for k in ESSENTIAL if serializable_data.get(k) in (None, "", 0)
                    ]
                    log.warning(
                        f"[flush_on_page_change] Dados essenciais ausentes: {missing_fields}"
                    )

                    # Obter os dados atuais do MCP para mesclar
                    mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

                    # Mesclar dados essenciais
                    for key in ESSENTIAL:
                        if serializable_data.get(key) in (None, "", 0) and mcp_data.get(
                            key
                        ) not in (None, "", 0):
                            serializable_data[key] = mcp_data.get(key)
                            log.info(
                                f"[flush_on_page_change] Mantido valor existente para {key}: {mcp_data.get(key)}"
                            )

                # Garantir que teste_tensao_induzida também seja mantido para compatibilidade
                if serializable_data.get("teste_tensao_induzida_at") is not None:
                    serializable_data["teste_tensao_induzida"] = serializable_data["teste_tensao_induzida_at"]
                    log.info(f"[flush_on_page_change] Mantendo compatibilidade: teste_tensao_induzida={serializable_data['teste_tensao_induzida']}")

                # Salvar no MCP usando set_data diretamente
                app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
                log.info(f"[flush_on_page_change] MCP atualizado ao navegar para {pathname}")

                # Verificar se os dados foram salvos corretamente
                saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                log.info(
                    f"[flush_on_page_change] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
                )

                # Log para verificar os valores de todos os dropdowns após salvar no MCP
                dropdown_keys = [
                    "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                    "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                    "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                    "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
                ]
                for key in dropdown_keys:
                    log.info(f"[flush_on_page_change] Valor de dropdown após salvar no MCP: {key}={saved_data.get(key)}")

                # Propagar dados para outros stores usando o padrão de "fonte única da verdade"
                # transformer-inputs-store é a fonte autoritativa para todos os dados básicos
                from utils.mcp_persistence import ensure_mcp_data_propagation

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
                ensure_mcp_data_propagation(app_instance, "transformer-inputs-store", target_stores)
            except Exception as e:
                log.error(f"[flush_on_page_change] Erro ao salvar ao trocar de página: {e}")

        return ""

    # Adicionar um elemento dummy para o callback de flush_on_page_change
    app_instance.layout.children.append(html.Div(id="dummy-output", style={"display": "none"}))

    log.info(f"Todos os callbacks do módulo transformer_inputs registrados com sucesso para app {app_instance.title}.")
    return True
