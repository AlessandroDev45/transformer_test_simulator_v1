# callbacks/transformer_inputs.py
"""
Módulo transformer_inputs que usa o padrão de registro centralizado.
"""
import logging

from dash import Input, Output, State, html, no_update, dcc # Adicionado State e dcc

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
                    # se o valor do formulário for None ou uma string vazia, guarda None.
                    # Caso contrário, guarda o valor como string.
                    if form_value is None or (isinstance(form_value, str) and form_value.strip() == ""):
                        data_to_save_to_mcp[key] = None
                    else:
                        data_to_save_to_mcp[key] = str(form_value)
                        # Log para verificar os valores de isolamento sendo salvos
                        if key in ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]:
                            log.info(f"[UpdateTransformerCalc] Salvando valor de isolamento: {key}={form_value}")

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

        # Converter valores para string para garantir que sejam exibidos corretamente
        corrente_at_str = str(corrente_at) if corrente_at is not None else None
        corrente_bt_str = str(corrente_bt) if corrente_bt is not None else None
        corrente_terciario_str = str(corrente_terciario) if corrente_terciario is not None else None
        corrente_at_tap_maior_str = str(corrente_at_tap_maior) if corrente_at_tap_maior is not None else None
        corrente_at_tap_menor_str = str(corrente_at_tap_menor) if corrente_at_tap_menor is not None else None

        log.info(f"[UpdateTransformerCalc] Retornando correntes: AT={corrente_at_str}, BT={corrente_bt_str}, Terciário={corrente_terciario_str}")

        return (
            corrente_at_str, corrente_bt_str, corrente_terciario_str,
            corrente_at_tap_maior_str, corrente_at_tap_menor_str,
        )

    # NOVO CALLBACK C: Para popular os valores dos dropdowns NBI/SIL/TA/TI
    # Adicionar um elemento para o callback de valores iniciais
    app_instance.layout.children.append(html.Div(id="initial-values-output", style={"display": "none"}))

    # Usar um único output para evitar conflitos com outros callbacks
    output_list_initial_values = Output("initial-values-output", "children")

    # NOVO CALLBACK D: Para carregar os valores de corrente do MCP quando a página é carregada
    @app_instance.callback(
        [
            Output("corrente_nominal_at", "value", allow_duplicate=True),
            Output("corrente_nominal_bt", "value", allow_duplicate=True),
            Output("corrente_nominal_terciario", "value", allow_duplicate=True),
            Output("corrente_nominal_at_tap_maior", "value", allow_duplicate=True),
            Output("corrente_nominal_at_tap_menor", "value", allow_duplicate=True),
        ],
        [
            Input("url", "pathname"),
        ],
        prevent_initial_call=False,
    )
    def load_currents_from_mcp(pathname):
        """
        Carrega os valores de corrente do MCP quando a página é carregada.
        """
        from dash import ctx
        log.info(f"[LoadCurrentsFromMCP] Acionado por: {ctx.triggered_id if ctx.triggered else 'Inicial'}. Pathname: {pathname}")

        # Verificar se estamos na página de dados básicos
        try:
            from utils.routes import ROUTE_HOME, normalize_pathname
            clean_path = normalize_pathname(pathname)
            if clean_path != ROUTE_HOME:
                log.debug(f"[LoadCurrentsFromMCP] Não na página inicial. Prevenindo update.")
                raise PreventUpdate
        except ImportError:
            log.error("[LoadCurrentsFromMCP] Falha ao importar utils.routes.")
            # Continuar mesmo sem a verificação de rota

        # Obter valores do MCP
        corrente_at, corrente_bt, corrente_terciario = None, None, None
        corrente_at_tap_maior, corrente_at_tap_menor = None, None

        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            mcp_data = app_instance.mcp.get_data("transformer-inputs-store")
            if mcp_data and isinstance(mcp_data, dict):
                corrente_at = mcp_data.get("corrente_nominal_at")
                corrente_bt = mcp_data.get("corrente_nominal_bt")
                corrente_terciario = mcp_data.get("corrente_nominal_terciario")
                corrente_at_tap_maior = mcp_data.get("corrente_nominal_at_tap_maior")
                corrente_at_tap_menor = mcp_data.get("corrente_nominal_at_tap_menor")

                log.info(f"[LoadCurrentsFromMCP] Valores obtidos do MCP: AT={corrente_at}, BT={corrente_bt}, Terciário={corrente_terciario}")

        # Converter valores para string para garantir que sejam exibidos corretamente
        corrente_at_str = str(corrente_at) if corrente_at is not None else None
        corrente_bt_str = str(corrente_bt) if corrente_bt is not None else None
        corrente_terciario_str = str(corrente_terciario) if corrente_terciario is not None else None
        corrente_at_tap_maior_str = str(corrente_at_tap_maior) if corrente_at_tap_maior is not None else None
        corrente_at_tap_menor_str = str(corrente_at_tap_menor) if corrente_at_tap_menor is not None else None

        return (
            corrente_at_str, corrente_bt_str, corrente_terciario_str,
            corrente_at_tap_maior_str, corrente_at_tap_menor_str,
        )

    # Registrar um clientside callback para definir os valores dos dropdowns
    # Isso evita conflitos com outros callbacks
    app_instance.clientside_callback(
        """
        function(store_data) {
            if (!store_data) return "";

            // Lista de campos de isolamento
            const isolation_keys = [
                "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
            ];

            // Definir os valores dos dropdowns
            for (const key of isolation_keys) {
                if (store_data[key]) {
                    // Encontrar o elemento pelo ID
                    const element = document.getElementById(key);
                    if (element) {
                        // Definir o valor
                        element.value = store_data[key];

                        // Disparar um evento de mudança para garantir que o Dash reconheça a alteração
                        const event = new Event('change', { bubbles: true });
                        element.dispatchEvent(event);

                        console.log("Definido valor para " + key + ": " + store_data[key]);
                    }
                }
            }

            return "Valores definidos";
        }
        """,
        output_list_initial_values,
        Input("transformer-inputs-store", "data"),
    )

    # Adicionar um output_manager para o callback update_isolation_values_on_load
    app_instance.layout.children.append(html.Div(id="update-isolation-output", style={"display": "none"}))

    # Registrar um clientside callback para atualizar o store com os dados do MCP
    # Isso é acionado quando o callback update_isolation_values_on_load é executado
    app_instance.clientside_callback(
        """
        function(trigger, store_data) {
            // Se não tiver dados no store, retornar
            if (!store_data) return store_data;

            // Retornar os dados do store
            return store_data;
        }
        """,
        Output("transformer-inputs-store", "data", allow_duplicate=True),
        Input("update-isolation-output", "children"),
        State("transformer-inputs-store", "data"),
    )

    @app_instance.callback(
        Output("update-isolation-output", "children"),
        [Input("url", "pathname")],
        [State("transformer-inputs-store", "data")],
        prevent_initial_call=True,
    )
    def update_isolation_values_on_load(pathname, store_data):
        """
        Atualiza os valores de isolamento no store quando a página é carregada.
        """
        from dash import ctx
        try:
            from utils.routes import ROUTE_HOME, normalize_pathname
        except ImportError:
            log.error("[UpdateIsolationValues] Falha ao importar utils.routes.")
            ROUTE_HOME = "/" # Fallback
            normalize_pathname = lambda p: p

        triggered_id = ctx.triggered_id
        log.info(f"[UpdateIsolationValues] Acionado por: {triggered_id}. Pathname: {pathname}")

        # Primeiro, tentar obter dados do MCP (fonte mais confiável)
        mcp_data = {}
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            mcp_data = app_instance.mcp.get_data("transformer-inputs-store")
            log.info(f"[UpdateIsolationValues] Dados obtidos do MCP: {len(mcp_data.keys()) if mcp_data else 0} campos")

        # Se não tiver dados do MCP, usar os dados do store
        if not mcp_data and (not store_data or not isinstance(store_data, dict)):
            log.warning("[UpdateIsolationValues] Nem MCP nem Store têm dados válidos. Retornando no_update.")
            return no_update

        # Mesclar dados do store com o MCP, priorizando o MCP
        merged_data = {}
        if store_data and isinstance(store_data, dict):
            merged_data.update(store_data)
        if mcp_data and isinstance(mcp_data, dict):
            merged_data.update(mcp_data)

        log.info(f"[UpdateIsolationValues] Dados mesclados: {len(merged_data.keys())} campos")

        # Lista de campos de isolamento
        isolation_keys = [
            "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
            "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
            "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
            "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
        ]

        # Log para todos os campos de isolamento para diagnóstico
        for key in isolation_keys:
            log.info(f"[UpdateIsolationValues] Valor mesclado: {key}={merged_data.get(key)}")

        # Função para preservar valores existentes
        def preserve_existing_value(store_dict, key, new_value):
            """Preserva o valor existente no store se o novo valor for None ou vazio."""
            existing_value = store_dict.get(key)

            # Se o novo valor for None ou string vazia, e o valor existente não for None ou vazio
            if (new_value is None or (isinstance(new_value, str) and new_value.strip() == "")) and \
               (existing_value is not None and not (isinstance(existing_value, str) and existing_value.strip() == "")):
                log.info(f"[UpdateIsolationValues] Preservando valor existente para {key}: {existing_value}")
                return existing_value

            # Se o novo valor não for None ou vazio, usá-lo
            if new_value is not None and not (isinstance(new_value, str) and new_value.strip() == ""):
                log.info(f"[UpdateIsolationValues] Usando novo valor para {key}: {new_value}")
                return new_value

            # Se ambos forem None ou vazios, retornar o existente (que pode ser None)
            log.debug(f"[UpdateIsolationValues] Ambos valores são None/vazios para {key}. Mantendo existente: {existing_value}")
            return existing_value

        # Atualizar o MCP com os valores mesclados para garantir persistência
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None and merged_data:
            # Obter dados atuais do MCP
            current_mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

            # Atualizar apenas os campos de isolamento
            for key in isolation_keys:
                current_mcp_data[key] = preserve_existing_value(current_mcp_data, key, merged_data.get(key))
                log.info(f"[UpdateIsolationValues] Valor final para {key}: {current_mcp_data.get(key)}")

            # Salvar de volta no MCP
            app_instance.mcp.set_data("transformer-inputs-store", current_mcp_data)
            log.info("[UpdateIsolationValues] MCP atualizado com valores mesclados")

            # Verificar se os dados foram salvos corretamente
            saved_data = app_instance.mcp.get_data("transformer-inputs-store")
            for key in isolation_keys:
                log.info(f"[UpdateIsolationValues] Valor após salvar no MCP: {key}={saved_data.get(key)}")

        return "Valores atualizados"

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

            # Verificar e preservar valores de isolamento
            isolation_keys = [
                "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
            ]

            # Função para preservar valores existentes
            def preserve_existing_value(store_dict, key, new_value):
                """Preserva o valor existente no store se o novo valor for None ou vazio."""
                existing_value = store_dict.get(key)

                # Se o novo valor for None ou string vazia, e o valor existente não for None ou vazio
                if (new_value is None or (isinstance(new_value, str) and new_value.strip() == "")) and \
                   (existing_value is not None and not (isinstance(existing_value, str) and existing_value.strip() == "")):
                    log.info(f"[autosave_with_debounce] Preservando valor existente para {key}: {existing_value}")
                    return existing_value

                # Se o novo valor não for None ou vazio, usá-lo
                if new_value is not None and not (isinstance(new_value, str) and new_value.strip() == ""):
                    return new_value

                # Se ambos forem None ou vazios, retornar o existente (que pode ser None)
                return existing_value

            # Verificar se há valores de isolamento no MCP que precisam ser preservados
            mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}
            for key in isolation_keys:
                serializable_data[key] = preserve_existing_value(mcp_data, key, serializable_data.get(key))
                log.info(f"[autosave_with_debounce] Valor final para {key}: {serializable_data.get(key)}")

            # Salvar no MCP usando set_data diretamente
            app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
            log.info(f"[autosave_with_debounce] MCP atualizado automaticamente às {now}")

            # Verificar se os dados foram salvos corretamente
            saved_data = app_instance.mcp.get_data("transformer-inputs-store")
            log.info(
                f"[autosave_with_debounce] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
            )

            # Log para todos os campos de isolamento
            for key in isolation_keys:
                log.info(f"[autosave_with_debounce] Valor após salvar: {key}={saved_data.get(key)}")

            # Propagar dados para outros stores
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

    # Adicionar um elemento para o callback de flush_on_page_change
    app_instance.layout.children.append(html.Div(id="flush-page-change-output", style={"display": "none"}))

    # Callback para salvar ao trocar de página
    @app_instance.callback(
        Output("flush-page-change-output", "children"),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )
    def flush_on_page_change(pathname):
        """
        Salva os dados no MCP quando o usuário navega para outra página.
        """
        if pathname:  # Executar para qualquer navegação, não apenas saindo da página de transformer-inputs
            log.info(f"[flush_on_page_change] Navegando para {pathname}, salvando dados no MCP")
            try:
                # Obter os dados atuais do MCP
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

                # Verificar e preservar valores de isolamento
                isolation_keys = [
                    "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
                    "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
                    "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
                    "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
                ]

                # Função para preservar valores existentes
                def preserve_existing_value(store_dict, key, new_value):
                    """Preserva o valor existente no store se o novo valor for None ou vazio."""
                    existing_value = store_dict.get(key)

                    # Se o novo valor for None ou string vazia, e o valor existente não for None ou vazio
                    if (new_value is None or (isinstance(new_value, str) and new_value.strip() == "")) and \
                       (existing_value is not None and not (isinstance(existing_value, str) and existing_value.strip() == "")):
                        log.info(f"[flush_on_page_change] Preservando valor existente para {key}: {existing_value}")
                        return existing_value

                    # Se o novo valor não for None ou vazio, usá-lo
                    if new_value is not None and not (isinstance(new_value, str) and new_value.strip() == ""):
                        log.info(f"[flush_on_page_change] Usando novo valor para {key}: {new_value}")
                        return new_value

                    # Se ambos forem None ou vazios, retornar o existente (que pode ser None)
                    log.debug(f"[flush_on_page_change] Ambos valores são None/vazios para {key}. Mantendo existente: {existing_value}")
                    return existing_value

                # Verificar se há valores de isolamento no MCP que precisam ser preservados
                # Obter os dados atuais do MCP novamente para garantir que temos os valores mais recentes
                mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

                # Verificar se há valores de isolamento nos elementos HTML
                try:
                    from dash import callback_context
                    from dash.dash import no_update

                    # Verificar se estamos na página de transformer-inputs
                    is_transformer_inputs_page = pathname and pathname.startswith("/transformer-inputs")

                    if is_transformer_inputs_page:
                        log.info("[flush_on_page_change] Estamos na página de transformer-inputs, tentando obter valores dos elementos HTML")

                        # Tentar obter valores dos elementos HTML
                        for key in isolation_keys:
                            # Verificar se o elemento existe no callback_context
                            if key in callback_context.inputs_list[0]:
                                element_value = callback_context.inputs_list[0][key]
                                if element_value is not None and element_value != no_update:
                                    log.info(f"[flush_on_page_change] Obtido valor do elemento HTML para {key}: {element_value}")
                                    serializable_data[key] = element_value
                except Exception as e:
                    log.warning(f"[flush_on_page_change] Erro ao tentar obter valores dos elementos HTML: {e}")

                # Preservar valores existentes
                for key in isolation_keys:
                    serializable_data[key] = preserve_existing_value(mcp_data, key, serializable_data.get(key))
                    log.info(f"[flush_on_page_change] Valor final para {key}: {serializable_data.get(key)}")

                # Salvar no MCP usando set_data diretamente
                app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
                log.info(f"[flush_on_page_change] MCP atualizado ao navegar para {pathname}")

                # Verificar se os dados foram salvos corretamente
                saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                log.info(
                    f"[flush_on_page_change] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
                )

                # Log para todos os campos de isolamento
                for key in isolation_keys:
                    log.info(f"[flush_on_page_change] Valor após salvar: {key}={saved_data.get(key)}")

                # Propagar dados para outros stores
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

    # Elemento dummy removido - agora cada callback tem seu próprio elemento de saída

    # Adicionar um elemento para o callback de verificação de persistência
    app_instance.layout.children.append(html.Div(id="persistence-check-output", style={"display": "none"}))

    # Callback para verificar a persistência dos dados ao carregar a página
    @app_instance.callback(
        Output("persistence-check-output", "children"),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )
    def verify_data_persistence_on_load(pathname):
        """
        Verifica a persistência dos dados ao carregar a página.
        """
        if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
            return ""

        log.info(f"[verify_data_persistence_on_load] Verificando persistência de dados ao carregar {pathname}")

        # Obter dados do MCP
        mcp_data = app_instance.mcp.get_data("transformer-inputs-store") or {}

        # Verificar campos de isolamento
        isolation_keys = [
            "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
            "nbi_neutro_at", "sil_neutro_at", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
            "nbi_neutro_bt", "sil_neutro_bt", "nbi_terciario", "sil_terciario",
            "teste_tensao_aplicada_terciario", "nbi_neutro_terciario", "sil_neutro_terciario"
        ]

        # Log para todos os campos de isolamento
        for key in isolation_keys:
            log.info(f"[verify_data_persistence_on_load] Valor no MCP: {key}={mcp_data.get(key)}")

        return ""

    # Callback para limpar os campos do formulário de dados básicos
    @app_instance.callback(
        [
            # Especificações Gerais
            Output("potencia_mva", "value"),
            Output("frequencia", "value"),
            Output("grupo_ligacao", "value"),
            Output("liquido_isolante", "value"),
            Output("elevacao_oleo_topo", "value"),
            Output("elevacao_enrol", "value"),
            Output("tipo_transformador", "value"),
            Output("tipo_isolamento", "value"),
            Output("norma_iso", "value"),

            # Pesos
            Output("peso_total", "value"),
            Output("peso_parte_ativa", "value"),
            Output("peso_oleo", "value"),
            Output("peso_tanque_acessorios", "value"),

            # Parâmetros dos Enrolamentos - AT
            Output("tensao_at", "value"),
            Output("conexao_at", "value"),
            Output("classe_tensao_at", "value"),
            Output("tensao_bucha_neutro_at", "value"),
            Output("impedancia", "value"),

            # Taps AT
            Output("tensao_at_tap_maior", "value"),
            Output("tensao_at_tap_menor", "value"),
            Output("impedancia_tap_maior", "value"),
            Output("impedancia_tap_menor", "value"),

            # Parâmetros dos Enrolamentos - BT
            Output("tensao_bt", "value"),
            Output("conexao_bt", "value"),
            Output("classe_tensao_bt", "value"),
            Output("tensao_bucha_neutro_bt", "value"),

            # Parâmetros dos Enrolamentos - Terciário
            Output("tensao_terciario", "value"),
            Output("conexao_terciario", "value"),
            Output("classe_tensao_terciario", "value"),
            Output("tensao_bucha_neutro_terciario", "value"),

            # Níveis de Isolamento - AT
            Output("nbi_at", "value"),
            Output("sil_at", "value"),
            Output("teste_tensao_aplicada_at", "value"),
            Output("teste_tensao_induzida_at", "value"),
            Output("nbi_neutro_at", "value"),
            Output("sil_neutro_at", "value"),

            # Níveis de Isolamento - BT
            Output("nbi_bt", "value"),
            Output("sil_bt", "value"),
            Output("teste_tensao_aplicada_bt", "value"),
            Output("nbi_neutro_bt", "value"),
            Output("sil_neutro_bt", "value"),

            # Níveis de Isolamento - Terciário
            Output("nbi_terciario", "value"),
            Output("sil_terciario", "value"),
            Output("teste_tensao_aplicada_terciario", "value"),
            Output("nbi_neutro_terciario", "value"),
            Output("sil_neutro_terciario", "value"),

            # Atualizar o store
            Output("transformer-inputs-store", "data", allow_duplicate=True),
        ],
        Input("limpar-transformer-inputs", "n_clicks"),
        [State("transformer-inputs-store", "data")],
        prevent_initial_call=True,
    )
    def limpar_transformer_inputs(n_clicks, current_store_data):
        """Limpa os campos do formulário de dados básicos."""
        if n_clicks is None:
            raise PreventUpdate

        log.info(f"[limpar_transformer_inputs] Limpando campos do formulário de dados básicos. n_clicks: {n_clicks}")

        # Criar uma cópia do store atual para manter alguns valores padrão
        store_data = {}
        if current_store_data:
            store_data = current_store_data.copy()

        # Limpar todos os campos relevantes no store
        campos_para_limpar = [
            # Especificações Gerais
            "potencia_mva", "grupo_ligacao", "liquido_isolante", "elevacao_oleo_topo",
            "elevacao_enrol", "tipo_transformador", "tipo_isolamento", "norma_iso",

            # Pesos
            "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios",

            # Parâmetros dos Enrolamentos - AT
            "tensao_at", "conexao_at", "classe_tensao_at", "tensao_bucha_neutro_at", "impedancia",

            # Taps AT
            "tensao_at_tap_maior", "tensao_at_tap_menor", "impedancia_tap_maior", "impedancia_tap_menor",
            "corrente_nominal_at_tap_maior", "corrente_nominal_at_tap_menor",

            # Parâmetros dos Enrolamentos - BT
            "tensao_bt", "conexao_bt", "classe_tensao_bt", "tensao_bucha_neutro_bt",

            # Parâmetros dos Enrolamentos - Terciário
            "tensao_terciario", "conexao_terciario", "classe_tensao_terciario", "tensao_bucha_neutro_terciario",

            # Níveis de Isolamento - AT
            "nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at",
            "nbi_neutro_at", "sil_neutro_at",

            # Níveis de Isolamento - BT
            "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt", "nbi_neutro_bt", "sil_neutro_bt",

            # Níveis de Isolamento - Terciário
            "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
            "nbi_neutro_terciario", "sil_neutro_terciario",
        ]

        # Limpar os campos no store
        for campo in campos_para_limpar:
            store_data[campo] = None

        # Definir valores padrão para alguns campos
        store_data["frequencia"] = 60
        store_data["liquido_isolante"] = "Mineral"
        store_data["tipo_transformador"] = "Trifásico"
        store_data["tipo_isolamento"] = "Uniforme"
        store_data["norma_iso"] = "IEC"

        # Atualizar o MCP se disponível
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            # Primeiro, limpar o store principal
            app_instance.mcp.set_data("transformer-inputs-store", store_data)
            log.info("[limpar_transformer_inputs] Store transformer-inputs-store atualizado via MCP")

            # Agora, propagar os dados limpos para todos os outros stores
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

            # Importar a função de propagação
            from utils.mcp_persistence import ensure_mcp_data_propagation

            # Propagar os dados limpos para todos os outros stores
            ensure_mcp_data_propagation(app_instance, "transformer-inputs-store", target_stores)
            log.info("[limpar_transformer_inputs] Dados limpos propagados para todos os outros stores")

        # Valores padrão para alguns campos e None para o resto
        return (
            # Especificações Gerais
            None, 60, None, "Mineral", None, None, "Trifásico", "Uniforme", "IEC",

            # Pesos
            None, None, None, None,

            # Parâmetros dos Enrolamentos - AT
            None, None, None, None, None,

            # Taps AT
            None, None, None, None,

            # Parâmetros dos Enrolamentos - BT
            None, None, None, None,

            # Parâmetros dos Enrolamentos - Terciário
            None, None, None, None,

            # Níveis de Isolamento - AT
            None, None, None, None, None, None,

            # Níveis de Isolamento - BT
            None, None, None, None, None,

            # Níveis de Isolamento - Terciário
            None, None, None, None, None,

            # Retornar o store atualizado
            store_data
        )

    # Função para obter os dados mais recentes do transformador
    def get_latest_transformer_data():
        """
        Obtém os dados mais recentes do transformador do MCP ou do cache.

        Returns:
            Dict: Dados do transformador
        """
        if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
            return app_instance.mcp.get_data("transformer-inputs-store")
        elif hasattr(app_instance, "transformer_data_cache"):
            return app_instance.transformer_data_cache
        return {}

    log.info(f"Todos os callbacks do módulo transformer_inputs registrados com sucesso para app {app_instance.title}.")
    return True
