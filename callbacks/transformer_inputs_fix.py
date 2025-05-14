# callbacks/transformer_inputs_fix.py
"""
Versão corrigida do módulo transformer_inputs que usa o padrão de registro centralizado.
"""
import logging

from dash import Input, Output, html

# Não importar app diretamente para evitar importações circulares
# from app import app  # REMOVIDO
from utils.store_diagnostics import convert_numpy_types

log = logging.getLogger(__name__)
log.info("============ MÓDULO TRANSFORMER_INPUTS_FIX CARREGADO ============")
log.info(f"Nível de log: {logging.getLevelName(log.getEffectiveLevel())}")
log.info(f"Handlers configurados: {[h.__class__.__name__ for h in log.handlers]}")
log.info("=============================================================")


def register_transformer_inputs_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de transformer_inputs.
    Esta função é chamada por app.py durante a inicialização.

    Registra os callbacks que foram convertidos para o padrão de registro centralizado.
    """
    log.info(f"Registrando callbacks do módulo transformer_inputs para app {app_instance.title}...")

    # Registrar o callback para calcular todas as correntes
    @app_instance.callback(
        [
            Output("corrente_nominal_at", "value"),
            Output("corrente_nominal_bt", "value"),
            Output("corrente_nominal_terciario", "value"),
            Output("corrente_nominal_at_tap_maior", "value"),
            Output("corrente_nominal_at_tap_menor", "value"),
        ],
        [
            # Dados básicos
            Input("potencia_mva", "value"),
            Input("frequencia", "value"),
            Input("grupo_ligacao", "value"),
            Input("liquido_isolante", "value"),
            Input("elevacao_oleo_topo", "value"),
            Input("elevacao_enrol", "value"),
            Input("tipo_transformador", "value"),
            Input("tipo_isolamento", "value"),
            # Pesos
            Input("peso_total", "value"),
            Input("peso_parte_ativa", "value"),
            Input("peso_oleo", "value"),
            Input("peso_tanque_acessorios", "value"),
            # Alta Tensão (AT)
            Input("tensao_at", "value"),
            Input("classe_tensao_at", "value"),
            Input("impedancia", "value"),
            Input("nbi_at", "value"),
            Input("sil_at", "value"),
            Input("conexao_at", "value"),
            Input("tensao_bucha_neutro_at", "value"),
            Input("nbi_neutro_at", "value"),
            # Taps AT
            Input("tensao_at_tap_maior", "value"),
            Input("impedancia_tap_maior", "value"),
            Input("tensao_at_tap_menor", "value"),
            Input("impedancia_tap_menor", "value"),
            # Tensões de ensaio AT
            Input("teste_tensao_aplicada_at", "value"),
            Input("teste_tensao_induzida_at", "value"),
            # Baixa Tensão (BT)
            Input("tensao_bt", "value"),
            Input("classe_tensao_bt", "value"),
            Input("nbi_bt", "value"),
            Input("sil_bt", "value"),
            Input("conexao_bt", "value"),
            Input("tensao_bucha_neutro_bt", "value"),
            Input("nbi_neutro_bt", "value"),
            Input("teste_tensao_aplicada_bt", "value"),
            # Terciário
            Input("tensao_terciario", "value"),
            Input("classe_tensao_terciario", "value"),
            Input("nbi_terciario", "value"),
            Input("sil_terciario", "value"),
            Input("conexao_terciario", "value"),
            Input("tensao_bucha_neutro_terciario", "value"),
            Input("nbi_neutro_terciario", "value"),
            Input("teste_tensao_aplicada_terciario", "value"),
            # Removido o botão de salvar
        ],
        prevent_initial_call=False,  # Permite rodar na carga inicial para garantir que o MCP seja atualizado
        priority=1000,  # Alta prioridade para garantir que este callback seja executado antes de outros
    )
    def update_transformer_calculations_and_mcp(
        # Dados básicos
        potencia_mva,
        frequencia,
        grupo_ligacao,
        liquido_isolante,
        elevacao_oleo_topo,
        elevacao_enrol,
        tipo_transformador,
        tipo_isolamento,
        # Pesos
        peso_total,
        peso_parte_ativa,
        peso_oleo,
        peso_tanque_acessorios,
        # Alta Tensão (AT)
        tensao_at,
        classe_tensao_at,
        impedancia,
        nbi_at,
        sil_at,
        conexao_at,
        tensao_bucha_neutro_at,
        nbi_neutro_at,
        # Taps AT
        tensao_at_tap_maior,
        impedancia_tap_maior,
        tensao_at_tap_menor,
        impedancia_tap_menor,
        # Tensões de ensaio AT
        teste_tensao_aplicada_at,
        teste_tensao_induzida_at,
        # Baixa Tensão (BT)
        tensao_bt,
        classe_tensao_bt,
        nbi_bt,
        sil_bt,
        conexao_bt,
        tensao_bucha_neutro_bt,
        nbi_neutro_bt,
        teste_tensao_aplicada_bt,
        # Terciário
        tensao_terciario,
        classe_tensao_terciario,
        nbi_terciario,
        sil_terciario,
        conexao_terciario,
        tensao_bucha_neutro_terciario,
        nbi_neutro_terciario,
        teste_tensao_aplicada_terciario,
        # Botão de salvar removido
    ):
        """
        Calcula as correntes nominais do transformador e atualiza o MCP.
        """
        # Log resumido para o arquivo de log (nível DEBUG para reduzir volume de logs)
        log.debug(
            f"[Update Callback] ACIONADO! Potência: {potencia_mva}, Tensão AT: {tensao_at}, Tensão BT: {tensao_bt}, Tensão Terciário: {tensao_terciario}, Tipo: {tipo_transformador}"
        )

        # Auto-save: sempre salvar no MCP quando qualquer campo for alterado
        from dash import ctx

        trigger_id = ctx.triggered_id if ctx.triggered else None
        log.debug(f"[Update Callback] Trigger ID: {trigger_id}")

        # Com auto-save, sempre salvamos no MCP
        save_to_mcp = True
        log.debug("[Update Callback] Auto-save ativado: sempre salvar no MCP")

        # Verificar se os valores principais são numéricos
        try:
            if potencia_mva is not None:
                float(potencia_mva)
            if tensao_at is not None:
                float(tensao_at)
            if tensao_bt is not None:
                float(tensao_bt)
            if tensao_terciario is not None:
                float(tensao_terciario)
            if tensao_at_tap_maior is not None:
                float(tensao_at_tap_maior)
            if tensao_at_tap_menor is not None:
                float(tensao_at_tap_menor)
        except ValueError as e:
            log.error(f"[Update Callback] Erro ao converter valor para float: {e}")

        # Valores padrão para retorno
        corrente_at = None
        corrente_bt = None
        corrente_terciario = None
        corrente_at_tap_maior = None
        corrente_at_tap_menor = None

        # Cálculo das correntes usando a função centralizada
        try:
            # Criar um dicionário com os dados do transformador
            transformer_data = {
                "tipo_transformador": tipo_transformador,
                "potencia_mva": potencia_mva,
                "tensao_at": tensao_at,
                "tensao_at_tap_maior": tensao_at_tap_maior,
                "tensao_at_tap_menor": tensao_at_tap_menor,
                "tensao_bt": tensao_bt,
                "tensao_terciario": tensao_terciario,
            }

            # Importar a função centralizada
            from utils.elec import calculate_nominal_currents

            # Calcular as correntes
            calculated_currents = calculate_nominal_currents(transformer_data)

            # Extrair os valores calculados
            corrente_at = calculated_currents.get("corrente_nominal_at")
            corrente_bt = calculated_currents.get("corrente_nominal_bt")
            corrente_terciario = calculated_currents.get("corrente_nominal_terciario")
            corrente_at_tap_maior = calculated_currents.get("corrente_nominal_at_tap_maior")
            corrente_at_tap_menor = calculated_currents.get("corrente_nominal_at_tap_menor")

            # Log dos valores calculados com mais detalhes
            log.info(
                f"[Update Callback] CORRENTES CALCULADAS: AT={corrente_at}A, BT={corrente_bt}A, Terciário={corrente_terciario}A"
            )
            log.info(
                f"[Update Callback] CORRENTES TAPS AT: Tap Maior={corrente_at_tap_maior}A, Tap Menor={corrente_at_tap_menor}A"
            )
            log.info(
                f"[Update Callback] TENSÕES TAPS AT: Tap Nominal={tensao_at}kV, Tap Maior={tensao_at_tap_maior}kV, Tap Menor={tensao_at_tap_menor}kV"
            )

            # Atualizar o MCP com os valores calculados
            if hasattr(app_instance, "mcp") and app_instance.mcp is not None:
                # Obter os dados atuais do MCP
                current_data = app_instance.mcp.get_data("transformer-inputs-store")
                if current_data:
                    # Atualizar todos os valores do formulário no MCP

                    # Função keep para evitar sobrescrever valores válidos com None
                    def keep(new_value, key):
                        """
                        Usa o valor novo se não for None, caso contrário mantém o valor atual.

                        Args:
                            new_value: Novo valor a ser considerado
                            key: Chave no dicionário current_data

                        Returns:
                            O valor a ser usado (novo ou atual)
                        """
                        return new_value if new_value is not None else current_data.get(key)

                    # Dados básicos
                    current_data["potencia_mva"] = keep(potencia_mva, "potencia_mva")
                    current_data["frequencia"] = keep(frequencia, "frequencia")
                    current_data["grupo_ligacao"] = keep(grupo_ligacao, "grupo_ligacao")
                    current_data["liquido_isolante"] = keep(liquido_isolante, "liquido_isolante")
                    current_data["elevacao_oleo_topo"] = keep(
                        elevacao_oleo_topo, "elevacao_oleo_topo"
                    )
                    current_data["elevacao_enrol"] = keep(elevacao_enrol, "elevacao_enrol")
                    current_data["tipo_transformador"] = keep(
                        tipo_transformador, "tipo_transformador"
                    )
                    current_data["tipo_isolamento"] = keep(tipo_isolamento, "tipo_isolamento")

                    # Pesos
                    current_data["peso_total"] = keep(peso_total, "peso_total")
                    current_data["peso_parte_ativa"] = keep(peso_parte_ativa, "peso_parte_ativa")
                    current_data["peso_oleo"] = keep(peso_oleo, "peso_oleo")
                    current_data["peso_tanque_acessorios"] = keep(
                        peso_tanque_acessorios, "peso_tanque_acessorios"
                    )

                    # Alta Tensão (AT)
                    current_data["tensao_at"] = keep(tensao_at, "tensao_at")
                    current_data["classe_tensao_at"] = keep(classe_tensao_at, "classe_tensao_at")
                    current_data["impedancia"] = keep(impedancia, "impedancia")
                    current_data["nbi_at"] = keep(nbi_at, "nbi_at")
                    current_data["sil_at"] = keep(sil_at, "sil_at")
                    current_data["conexao_at"] = keep(conexao_at, "conexao_at")
                    current_data["tensao_bucha_neutro_at"] = keep(
                        tensao_bucha_neutro_at, "tensao_bucha_neutro_at"
                    )
                    current_data["nbi_neutro_at"] = keep(nbi_neutro_at, "nbi_neutro_at")

                    # Taps AT
                    current_data["tensao_at_tap_maior"] = keep(
                        tensao_at_tap_maior, "tensao_at_tap_maior"
                    )
                    current_data["impedancia_tap_maior"] = keep(
                        impedancia_tap_maior, "impedancia_tap_maior"
                    )
                    current_data["tensao_at_tap_menor"] = keep(
                        tensao_at_tap_menor, "tensao_at_tap_menor"
                    )
                    current_data["impedancia_tap_menor"] = keep(
                        impedancia_tap_menor, "impedancia_tap_menor"
                    )

                    # Tensões de ensaio AT
                    current_data["teste_tensao_aplicada_at"] = keep(
                        teste_tensao_aplicada_at, "teste_tensao_aplicada_at"
                    )
                    current_data["teste_tensao_induzida_at"] = keep(
                        teste_tensao_induzida_at, "teste_tensao_induzida_at"
                    )
                    # Garantir que teste_tensao_induzida também seja mantido para compatibilidade
                    current_data["teste_tensao_induzida"] = keep(
                        teste_tensao_induzida_at, "teste_tensao_induzida"
                    )

                    # Log para verificar os valores de isolamento sendo salvos
                    isolation_keys = ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]
                    for key in isolation_keys:
                        log.info(f"[Update Callback] Salvando valor de isolamento: {key}={current_data.get(key)}")

                    # Baixa Tensão (BT)
                    current_data["tensao_bt"] = keep(tensao_bt, "tensao_bt")
                    current_data["classe_tensao_bt"] = keep(classe_tensao_bt, "classe_tensao_bt")
                    current_data["nbi_bt"] = keep(nbi_bt, "nbi_bt")
                    current_data["sil_bt"] = keep(sil_bt, "sil_bt")
                    current_data["conexao_bt"] = keep(conexao_bt, "conexao_bt")
                    current_data["tensao_bucha_neutro_bt"] = keep(
                        tensao_bucha_neutro_bt, "tensao_bucha_neutro_bt"
                    )
                    current_data["nbi_neutro_bt"] = keep(nbi_neutro_bt, "nbi_neutro_bt")
                    current_data["teste_tensao_aplicada_bt"] = keep(
                        teste_tensao_aplicada_bt, "teste_tensao_aplicada_bt"
                    )

                    # Terciário
                    current_data["tensao_terciario"] = keep(tensao_terciario, "tensao_terciario")
                    current_data["classe_tensao_terciario"] = keep(
                        classe_tensao_terciario, "classe_tensao_terciario"
                    )
                    current_data["nbi_terciario"] = keep(nbi_terciario, "nbi_terciario")
                    current_data["sil_terciario"] = keep(sil_terciario, "sil_terciario")
                    current_data["conexao_terciario"] = keep(conexao_terciario, "conexao_terciario")
                    current_data["tensao_bucha_neutro_terciario"] = keep(
                        tensao_bucha_neutro_terciario, "tensao_bucha_neutro_terciario"
                    )
                    current_data["nbi_neutro_terciario"] = keep(
                        nbi_neutro_terciario, "nbi_neutro_terciario"
                    )
                    current_data["teste_tensao_aplicada_terciario"] = keep(
                        teste_tensao_aplicada_terciario, "teste_tensao_aplicada_terciario"
                    )

                    # Atualizar os valores de corrente calculados (sempre usar os calculados, pois são derivados)
                    current_data["corrente_nominal_at"] = corrente_at
                    current_data["corrente_nominal_bt"] = corrente_bt
                    current_data["corrente_nominal_terciario"] = corrente_terciario
                    current_data["corrente_nominal_at_tap_maior"] = corrente_at_tap_maior
                    current_data["corrente_nominal_at_tap_menor"] = corrente_at_tap_menor

                    # Log detalhado dos valores de corrente que serão salvos no MCP
                    log.info(f"[Update Callback] SALVANDO NO MCP - Corrente AT Nominal: {corrente_at}A")
                    log.info(f"[Update Callback] SALVANDO NO MCP - Corrente AT Tap Maior: {corrente_at_tap_maior}A")
                    log.info(f"[Update Callback] SALVANDO NO MCP - Corrente AT Tap Menor: {corrente_at_tap_menor}A")
                    log.info(f"[Update Callback] SALVANDO NO MCP - Tensão AT Nominal: {tensao_at}kV")
                    log.info(f"[Update Callback] SALVANDO NO MCP - Tensão AT Tap Maior: {tensao_at_tap_maior}kV")
                    log.info(f"[Update Callback] SALVANDO NO MCP - Tensão AT Tap Menor: {tensao_at_tap_menor}kV")

                    # Log dos valores principais após aplicar a função keep
                    log.debug(
                        f"[Update Callback] Após keep - Potência: {current_data.get('potencia_mva')}, Tensão AT: {current_data.get('tensao_at')}, Tensão BT: {current_data.get('tensao_bt')}"
                    )

                    # Log dos valores principais que serão salvos no MCP (apenas em nível debug)
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug("[Update Callback] Valores principais a serem salvos no MCP:")
                        log.debug(f"[Update Callback] Potência: {current_data.get('potencia_mva')}")
                        log.debug(f"[Update Callback] Tensão AT: {current_data.get('tensao_at')}")
                        log.debug(f"[Update Callback] Tensão BT: {current_data.get('tensao_bt')}")
                        log.debug(
                            f"[Update Callback] Corrente AT: {current_data.get('corrente_nominal_at')}"
                        )
                        log.debug(
                            f"[Update Callback] Corrente BT: {current_data.get('corrente_nominal_bt')}"
                        )
                        log.debug(f"[Update Callback] Impedância: {current_data.get('impedancia')}")

                    # Serializar dados para salvar no MCP
                    serializable_data = convert_numpy_types(
                        current_data, debug_path="update_transformer_inputs_with_currents"
                    )

                    # Se não foi acionado pelo botão de salvar, apenas retornar as correntes calculadas
                    if not save_to_mcp:
                        log.info(
                            "[Update Callback] Callback não acionado pelo botão de salvar. Apenas calculando correntes sem salvar no MCP."
                        )
                        return (
                            corrente_at,
                            corrente_bt,
                            corrente_terciario,
                            corrente_at_tap_maior,
                            corrente_at_tap_menor,
                        )

                    # Verificar se os dados principais estão presentes antes de salvar
                    log.debug(
                        f"[Update Callback] Verificando dados antes de salvar no MCP: potencia_mva={serializable_data.get('potencia_mva')}, tensao_at={serializable_data.get('tensao_at')}, tensao_bt={serializable_data.get('tensao_bt')}"
                    )

                    # Não vamos mais bloquear a atualização se faltar algum dado essencial
                    # Apenas registramos um aviso para fins de diagnóstico
                    from utils.mcp_persistence import ESSENTIAL, _dados_ok

                    if not _dados_ok(serializable_data):
                        missing_fields = [
                            k for k in ESSENTIAL if serializable_data.get(k) in (None, "", 0)
                        ]
                        log.warning(
                            f"[Update Callback] Dados essenciais ausentes: {missing_fields}"
                        )
                        log.warning(
                            "[Update Callback] Continuando com a atualização mesmo com dados essenciais ausentes"
                        )

                    # IMPORTANTE: Usar set_data diretamente em vez de patch_mcp
                    # Isso garante que todos os campos sejam salvos, mesmo os que são None → valor
                    log.info(
                        f"[Update Callback] Salvando {len(serializable_data)} campos no MCP via set_data"
                    )
                    app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
                    log.debug(
                        "[Update Callback] MCP atualizado com TODOS os valores do formulário via set_data"
                    )

                    # Verificar se os dados foram salvos corretamente
                    saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                    log.info(
                        f"[Update Callback] Verificação após salvar no MCP: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
                    )

                    # Log para verificar os valores de isolamento após salvar no MCP
                    isolation_keys = ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]
                    for key in isolation_keys:
                        log.info(f"[Update Callback] Valor de isolamento após salvar no MCP: {key}={saved_data.get(key)}")

                    # Propagar dados para outros stores usando o novo utilitário
                    try:
                        # Obter os dados mais recentes do MCP para garantir consistência
                        latest_data = app_instance.mcp.get_data("transformer-inputs-store")

                        # Verificar se temos dados válidos para propagar
                        if not latest_data or not any(
                            latest_data.get(key) is not None
                            for key in ["potencia_mva", "tensao_at", "tensao_bt"]
                        ):
                            log.warning(
                                "[Update Callback] Dados insuficientes para propagação. Abortando."
                            )
                            return (
                                corrente_at,
                                corrente_bt,
                                corrente_terciario,
                                corrente_at_tap_maior,
                                corrente_at_tap_menor,
                            )

                        log.info(f"[Update Callback] Dados para propagação: {latest_data}")

                        # Importar o utilitário de persistência do MCP
                        from utils.mcp_persistence import ensure_mcp_data_propagation

                        # Lista de stores para os quais propagar os dados
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

                        # Propagar dados para todos os stores
                        propagation_results = ensure_mcp_data_propagation(
                            app_instance, "transformer-inputs-store", target_stores
                        )

                        # Registrar resultados
                        for store, success in propagation_results.items():
                            if success:
                                log.info(f"[Update Callback] Dados propagados para {store}")
                            else:
                                log.debug(
                                    f"[Update Callback] Não foi necessário propagar dados para {store}"
                                )
                    except Exception as e:
                        log.error(
                            f"[Update Callback] Erro ao propagar dados para outros stores: {e}",
                            exc_info=True,
                        )

                    # Verificar se os valores principais foram salvos corretamente (apenas em nível debug)
                    if log.isEnabledFor(logging.DEBUG):
                        saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                        log.debug(
                            f"[Update Callback] Verificação final - Potência: {saved_data.get('potencia_mva')}, Tensão AT: {saved_data.get('tensao_at')}, Tensão BT: {saved_data.get('tensao_bt')}"
                        )
                        log.debug(f"[Update Callback] Total de campos no MCP: {len(saved_data)}")

        except Exception as e:
            log.error(f"[Update Callback] Erro: {e}")

        return (
            corrente_at,
            corrente_bt,
            corrente_terciario,
            corrente_at_tap_maior,
            corrente_at_tap_menor,
        )

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

            # Salvar no MCP usando set_data diretamente
            app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
            log.info(f"[autosave_with_debounce] MCP atualizado automaticamente às {now}")

            # Verificar se os dados foram salvos corretamente
            saved_data = app_instance.mcp.get_data("transformer-inputs-store")
            log.info(
                f"[autosave_with_debounce] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
            )

            # Log para verificar os valores de isolamento após salvar no MCP
            isolation_keys = ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]
            for key in isolation_keys:
                log.info(f"[autosave_with_debounce] Valor de isolamento após salvar no MCP: {key}={saved_data.get(key)}")

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

    # Callback para salvar ao trocar de página
    @app_instance.callback(
        Output("dummy-output", "children", allow_duplicate=True),
        Input("url", "pathname"),
        prevent_initial_call=True,
    )
    def flush_on_page_change(pathname):
        """
        Salva os dados no MCP quando o usuário navega para outra página.
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

                    # Função keep para evitar sobrescrever valores válidos com None
                    def keep(new_value, key):
                        return new_value if new_value is not None else mcp_data.get(key)

                    # Mesclar dados essenciais
                    for key in ESSENTIAL:
                        if serializable_data.get(key) in (None, "", 0) and mcp_data.get(
                            key
                        ) not in (None, "", 0):
                            serializable_data[key] = mcp_data.get(key)
                            log.info(
                                f"[flush_on_page_change] Mantido valor existente para {key}: {mcp_data.get(key)}"
                            )

                # Salvar no MCP usando set_data diretamente
                app_instance.mcp.set_data("transformer-inputs-store", serializable_data)
                log.info(f"[flush_on_page_change] MCP atualizado ao navegar para {pathname}")

                # Verificar se os dados foram salvos corretamente
                saved_data = app_instance.mcp.get_data("transformer-inputs-store")
                log.info(
                    f"[flush_on_page_change] Verificação após salvar: potencia_mva={saved_data.get('potencia_mva')}, tensao_at={saved_data.get('tensao_at')}"
                )

                # Log para verificar os valores de isolamento após salvar no MCP
                isolation_keys = ["nbi_at", "sil_at", "teste_tensao_aplicada_at", "teste_tensao_induzida_at"]
                for key in isolation_keys:
                    log.info(f"[flush_on_page_change] Valor de isolamento após salvar no MCP: {key}={saved_data.get(key)}")

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

    # Adicionar um elemento dummy para o callback de flush_on_page_change
    app_instance.layout.children.append(html.Div(id="dummy-output", style={"display": "none"}))

    # NOVO CALLBACK: Para popular os valores dos dropdowns NBI/SIL/TA/TI quando a página é carregada
    from dash import no_update

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

        def get_str_val(key, default=""):
            val = store_data.get(key, default)
            return str(val) if val is not None else default

        values_tuple = (
            get_str_val("nbi_at"), get_str_val("sil_at"),
            get_str_val("teste_tensao_aplicada_at"), get_str_val("teste_tensao_induzida_at"),
            get_str_val("nbi_neutro_at"), get_str_val("sil_neutro_at"),
            get_str_val("nbi_bt"), get_str_val("sil_bt"),
            get_str_val("teste_tensao_aplicada_bt"),
            get_str_val("nbi_neutro_bt"), get_str_val("sil_neutro_bt"),
            get_str_val("nbi_terciario"), get_str_val("sil_terciario"),
            get_str_val("teste_tensao_aplicada_terciario"),
            get_str_val("nbi_neutro_terciario"), get_str_val("sil_neutro_terciario")
        )
        log.debug(f"[PopulateDynamicValues] Valores a serem definidos: {values_tuple}")
        return values_tuple

    log.info(
        f"Todos os callbacks do módulo transformer_inputs registrados com sucesso para app {app_instance.title}."
    )
    return True
