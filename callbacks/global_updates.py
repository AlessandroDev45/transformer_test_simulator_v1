# callbacks/global_updates.py
"""
Callbacks globais para atualização de componentes em múltiplas seções.
Centraliza a atualização dos painéis de informação do transformador lendo do MCP.
"""
import logging
import time


import dash
from dash import Input, Output, callback, ctx, html

from app import app  # Import app instance to access MCP
from components.transformer_info_template import create_transformer_info_panel
from utils.mcp_diagnostics import diagnose_mcp, fix_mcp_data
from utils.mcp_utils import patch_mcp

# Importamos a função patch_mcp do módulo utils.mcp_utils

log = logging.getLogger(__name__)

# Lista de todos os IDs dos painéis de informação nas diferentes seções
info_panel_outputs = [
    Output("transformer-info-losses", "children", allow_duplicate=True),
    Output("transformer-info-impulse", "children", allow_duplicate=True),
    Output("transformer-info-dieletric", "children", allow_duplicate=True),
    Output("transformer-info-applied", "children", allow_duplicate=True),
    Output("transformer-info-induced", "children", allow_duplicate=True),
    Output("transformer-info-short-circuit", "children", allow_duplicate=True),
    Output("transformer-info-temperature-rise", "children", allow_duplicate=True),
    # Adicionar outros painéis se existirem
    Output("transformer-info-comprehensive", "children", allow_duplicate=True),  # Exemplo
]


# Callback para diagnosticar e corrigir o MCP quando a aplicação iniciar
@callback(
    Output("url", "search"),  # Output fictício, não usado
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def diagnose_and_fix_mcp(_):
    """
    Diagnostica e corrige o MCP quando a aplicação iniciar.
    Este callback é executado uma vez na inicialização.
    """
    log.info("[MCP Diagnostics] Iniciando diagnóstico do MCP...")

    # Executar diagnóstico
    diagnosis = diagnose_mcp(app, verbose=True)
    log.debug(f"[MCP Diagnostics] Resultado do diagnóstico: {diagnosis['status']}")

    if diagnosis["status"] != "ok":
        log.warning(
            f"[MCP Diagnostics] Problemas encontrados: {diagnosis['warnings']} {diagnosis['errors']}"
        )

        # Tentar corrigir problemas
        log.debug("[MCP Diagnostics] Tentando corrigir problemas...")
        fix_result = fix_mcp_data(app, verbose=True)
        log.debug(f"[MCP Diagnostics] Resultado da correção: {fix_result['status']}")

        if fix_result["status"] == "ok":
            log.debug(f"[MCP Diagnostics] Ações realizadas: {fix_result['actions']}")
        else:
            log.error(f"[MCP Diagnostics] Erros na correção: {fix_result['errors']}")
    else:
        log.debug("[MCP Diagnostics] MCP em bom estado. Nenhuma correção necessária.")

    # Retornar string vazia para o search da URL (não afeta a navegação)
    return ""


@callback(
    info_panel_outputs,
    Input("transformer-inputs-store", "data"),  # Acionado quando o store (e portanto o MCP) muda
    # Removido Input("url", "pathname") para evitar que o callback seja acionado na navegação
    # Adicionamos outros stores como Input para garantir que o painel recarregue quando qualquer store mudar
    Input("losses-store", "data"),
    Input("impulse-store", "data"),
    Input("dieletric-analysis-store", "data"),
    Input("applied-voltage-store", "data"),
    Input("induced-voltage-store", "data"),
    Input("short-circuit-store", "data"),
    Input("temperature-rise-store", "data"),
    prevent_initial_call="initial_duplicate",  # Permite rodar na carga inicial para exibir dados padrão/carregados
)
def global_updates_all_transformer_info_panels(
    transformer_store_data,
    # Removido parâmetro pathname
    losses_store_data,
    impulse_store_data,
    dieletric_store_data,
    applied_voltage_store_data,
    induced_voltage_store_data,
    short_circuit_store_data,
    temperature_rise_store_data,
):  # Recebe dados de todos os stores como trigger
    """
    Atualiza TODOS os painéis de informação do transformador lendo do MCP.
    """
    start_time = time.time()
    triggered_id = ctx.triggered_id if ctx.triggered else "Initial Load / No Trigger"
    module_name = "global_updates"

    # IMPORTANTE: Evitar execução quando o trigger for mudança de URL ou botão de calcular
    # Isso evita que o callback seja executado durante navegação entre páginas
    # ou durante o cálculo de perdas, o que poderia sobrescrever dados válidos
    if triggered_id == "url":
        log.debug(f"[{module_name}] Callback ignorado - trigger é mudança de URL")
        raise dash.exceptions.PreventUpdate

    # Evitar execução quando o trigger for botão de calcular
    if triggered_id in ["calcular-perdas-vazio", "calcular-perdas-carga"]:
        log.debug(f"[{module_name}] Callback ignorado - trigger é botão de calcular: {triggered_id}")
        raise dash.exceptions.PreventUpdate

    # Verificar se o store que acionou o callback tem dados válidos
    # Isso evita que dados vazios ou None sobrescrevam dados válidos
    if triggered_id and triggered_id.endswith("-store"):
        # Obter os dados do store que acionou o callback
        store_data = None
        if triggered_id == "transformer-inputs-store":
            store_data = transformer_store_data
        elif triggered_id == "losses-store":
            store_data = losses_store_data
        elif triggered_id == "impulse-store":
            store_data = impulse_store_data
        elif triggered_id == "dieletric-analysis-store":
            store_data = dieletric_store_data
        elif triggered_id == "applied-voltage-store":
            store_data = applied_voltage_store_data
        elif triggered_id == "induced-voltage-store":
            store_data = induced_voltage_store_data
        elif triggered_id == "short-circuit-store":
            store_data = short_circuit_store_data
        elif triggered_id == "temperature-rise-store":
            store_data = temperature_rise_store_data

        # Se o store que acionou o callback não tem dados válidos, ignorar a atualização
        if not store_data or not isinstance(store_data, dict) or not store_data:
            log.debug(f"[{module_name}] Callback ignorado - store {triggered_id} não tem dados válidos")
            raise dash.exceptions.PreventUpdate

    log.debug(f"[{module_name}] Iniciando atualização global de painéis. Trigger: {triggered_id}")

    # Verificar dados do store recebido como trigger
    if not transformer_store_data:
        log.debug(f"[{module_name}] Nenhum dado recebido do transformer-inputs-store como trigger")

    if app.mcp is None:
        log.error(f"[{module_name}] MCP não disponível. Não é possível atualizar painéis.")
        error_panel = html.Div(
            "Erro interno: MCP não inicializado.", className="alert alert-danger small"
        )
        return [error_panel] * len(info_panel_outputs)

    # --- Obter dados do MCP ---
    # SEMPRE obter os dados diretamente do MCP para garantir que estamos usando os dados mais atualizados
    # Este é o ponto principal onde o módulo global_updates lê os dados do MCP que foram salvos pelo transformer_inputs
    log.debug(f"[{module_name}] Obtendo dados diretamente do MCP")

    # Forçar uma leitura fresca do MCP após salvar
    transformer_data_mcp = app.mcp.get_data("transformer-inputs-store", force_reload=True)  # Lê os dados atualizados

    # Verificar se os dados são válidos
    if transformer_data_mcp.get('potencia_mva') is None or transformer_data_mcp.get('tensao_at') is None or transformer_data_mcp.get('tensao_bt') is None:
        log.warning(f"[{module_name}] Dados essenciais ausentes no MCP. Tentando recarregar do disco...")
        # Tentar recarregar do disco novamente
        # app.mcp.save_to_disk(force=True) # REMOVIDO: global_updates não deve salvar no disco
        transformer_data_mcp = app.mcp.get_data("transformer-inputs-store", force_reload=True)

    # Removida a correção para FLASH-BACK que usava dados fixos
    # Agora confiamos nos dados do MCP sem sobrescrever com valores fixos

    # Verificar se temos dados essenciais no MCP
    has_essential_data = (
        transformer_data_mcp
        and transformer_data_mcp.get("potencia_mva") is not None
        and transformer_data_mcp.get("tensao_at") is not None
        and transformer_data_mcp.get("tensao_bt") is not None
    )

    # Verificar se temos dados essenciais no store
    store_has_essential_data = (
        isinstance(transformer_store_data, dict)
        and transformer_store_data.get("potencia_mva") is not None
        and transformer_store_data.get("tensao_at") is not None
        and transformer_store_data.get("tensao_bt") is not None
    )

    # Sempre exibir os dados do MCP, mesmo que sejam None
    log.debug(
        f"[{module_name}] Dados do MCP: potencia={transformer_data_mcp.get('potencia_mva')}, tensao_at={transformer_data_mcp.get('tensao_at')}, tensao_bt={transformer_data_mcp.get('tensao_bt')}"
    )

    if has_essential_data:
        log.debug(
            f"[{module_name}] MCP contém dados essenciais: potencia={transformer_data_mcp.get('potencia_mva')}, tensao_at={transformer_data_mcp.get('tensao_at')}, tensao_bt={transformer_data_mcp.get('tensao_bt')}"
        )
    elif store_has_essential_data:
        log.debug(
            f"[{module_name}] Store contém dados essenciais: potencia={transformer_store_data.get('potencia_mva')}, tensao_at={transformer_store_data.get('tensao_at')}, tensao_bt={transformer_store_data.get('tensao_bt')}"
        )

        # Importar constantes de mcp_persistence
        from utils.mcp_persistence import AUTHORITATIVE_STORE, BASIC_FIELDS

        # IMPORTANTE: Não atualizar campos básicos na fonte-de-verdade a partir de outros stores
        # Isso evita que valores antigos sobrescrevam dados válidos no MCP
        if "transformer-inputs-store" == AUTHORITATIVE_STORE:
            log.info(
                f"[{module_name}] Não atualizando campos básicos na fonte-de-verdade (transformer-inputs-store)"
            )

            # Filtrar campos básicos do store antes de atualizar o MCP
            filtered_store_data = {
                k: v for k, v in transformer_store_data.items() if k not in BASIC_FIELDS
            }

            if filtered_store_data:
                if patch_mcp("transformer-inputs-store", filtered_store_data, app):
                    log.debug(
                        f"[{module_name}] MCP atualizado apenas com campos não-básicos do store"
                    )
                    # Forçar salvamento para garantir persistência
                    # app.mcp.save_to_disk(force=True) # REMOVIDO: global_updates não deve salvar no disco
                    # Obter os dados atualizados do MCP
                    transformer_data_mcp = app.mcp.get_data("transformer-inputs-store")
                    has_essential_data = True
                    log.debug(
                        f"[{module_name}] Dados atualizados no MCP (apenas campos não-básicos)"
                    )
            else:
                log.debug(f"[{module_name}] Nenhum campo não-básico para atualizar no MCP")
        else:
            # Se não for a fonte-de-verdade, pode atualizar normalmente
            if patch_mcp("transformer-inputs-store", transformer_store_data, app):
                log.debug(f"[{module_name}] MCP atualizado com dados não vazios do store")
                # Forçar salvamento para garantir persistência
                # app.mcp.save_to_disk(force=True) # REMOVIDO: global_updates não deve salvar no disco
                # Obter os dados atualizados do MCP
                transformer_data_mcp = app.mcp.get_data("transformer-inputs-store")
                has_essential_data = True
                log.debug(
                    f"[{module_name}] Dados atualizados no MCP"
                )
            else:
                log.debug(f"[{module_name}] Nenhum dado válido para atualizar no MCP")
    else:
        log.debug(f"[{module_name}] Dados essenciais ausentes no MCP e no store")

        # Verificar se temos dados no store que podemos usar
        if isinstance(transformer_store_data, dict) and transformer_store_data:
            # Usar os dados do store diretamente para exibição, mas NÃO atualizar o MCP
            transformer_data_mcp = transformer_store_data
            log.debug(
                f"[{module_name}] Usando dados do store apenas para exibição, sem atualizar o MCP"
            )
        else:
            log.debug(f"[{module_name}] Store não contém dados utilizáveis")

    # IMPORTANTE: NÃO atualizar o transformer-inputs-store com dados do store
    # Isso evita que valores None sobrescrevam dados válidos no MCP durante a navegação
    log.debug(
        f"[{module_name}] Ignorando atualização do transformer-inputs-store a partir do store para evitar perda de dados"
    )

    # Log detalhado dos dados obtidos do MCP (apenas em nível debug)
    if isinstance(transformer_data_mcp, dict):
        log.debug(f"[{module_name}] Chaves disponíveis no MCP: {list(transformer_data_mcp.keys())}")
        # Log de valores importantes apenas em nível debug
        log.debug(f"[{module_name}] Potência: {transformer_data_mcp.get('potencia_mva')}")
        log.debug(f"[{module_name}] Tensão AT: {transformer_data_mcp.get('tensao_at')}")
        log.debug(f"[{module_name}] Tensão BT: {transformer_data_mcp.get('tensao_bt')}")
        log.debug(f"[{module_name}] Corrente AT: {transformer_data_mcp.get('corrente_nominal_at')}")
        log.debug(f"[{module_name}] Corrente BT: {transformer_data_mcp.get('corrente_nominal_bt')}")
    else:
        log.warning(f"[{module_name}] Dados do MCP não são um dicionário: {transformer_data_mcp}")

    # Verificar se os dados são válidos (simples verificação se é um dict não vazio)
    if not isinstance(transformer_data_mcp, dict) or not transformer_data_mcp:
        log.warning(f"[{module_name}] Dados do MCP inválidos ou vazios. Exibindo mensagem padrão.")
        default_panel = create_transformer_info_panel({})  # Cria painel vazio/padrão
        return [default_panel] * len(info_panel_outputs)

    # NOTA: O recálculo de correntes foi removido daqui.
    # Este callback agora assume que os dados do MCP (transformer_data_mcp)
    # já contêm as correntes calculadas pelo callback de inputs.

    # Não propagamos dados aqui - isso é responsabilidade do callback update_transformer_calculations_and_mcp
    # Apenas verificamos se os dados são válidos para criar o painel
    if not transformer_data_mcp or not isinstance(transformer_data_mcp, dict):
        log.warning(
            f"[{module_name}] Dados do MCP insuficientes para criar painel. Exibindo painel vazio."
        )
        return [create_transformer_info_panel({})] * len(info_panel_outputs)

    # Verificar quais dados estão disponíveis para log (apenas em nível debug)
    if log.isEnabledFor(logging.DEBUG):
        available_keys = [
            key
            for key in [
                "potencia_mva",
                "tensao_at",
                "tensao_bt",
                "corrente_nominal_at",
                "corrente_nominal_bt",
            ]
            if transformer_data_mcp.get(key) is not None
        ]
        if available_keys:
            log.debug(f"[{module_name}] Dados disponíveis no MCP: {available_keys}")
        else:
            log.debug(f"[{module_name}] Nenhum dado principal disponível no MCP.")

    # Criar o painel HTML usando dados do MCP
    try:
        # Obter dados frescos do MCP com force_reload=True para garantir que estamos usando os dados mais recentes
        fresh_data = app.mcp.get_data("transformer-inputs-store", force_reload=True)

        # Verificar se os dados são válidos
        if not fresh_data or not isinstance(fresh_data, dict):
            log.warning(f"[{module_name}] Dados frescos do MCP são inválidos: {fresh_data}")
            fresh_data = transformer_data_mcp  # Usar os dados obtidos anteriormente

        # Verificar se os dados essenciais estão presentes
        if fresh_data.get('potencia_mva') is None or fresh_data.get('tensao_at') is None or fresh_data.get('tensao_bt') is None:
            log.warning(f"[{module_name}] Dados essenciais ausentes nos dados frescos. Tentando recarregar do disco...")
            # Tentar recarregar do disco novamente
            # app.mcp.save_to_disk(force=True) # REMOVIDO: global_updates não deve salvar no disco
            fresh_data = app.mcp.get_data("transformer-inputs-store", force_reload=True)

        log.debug(
            f"[{module_name}] Dados frescos obtidos para o painel"
        )

        # Verificar se os dados ainda estão ausentes após a recarga
        if fresh_data.get('potencia_mva') is None or fresh_data.get('tensao_at') is None or fresh_data.get('tensao_bt') is None:
            log.warning(f"[{module_name}] Dados essenciais ainda ausentes após recarga. Usando dados do transformer_inputs_fix...")
            # Tentar obter dados do transformer_inputs
            from callbacks.transformer_inputs import get_latest_transformer_data
            try:
                latest_data = get_latest_transformer_data()
                if latest_data and isinstance(latest_data, dict):
                    log.debug(f"[{module_name}] Obtidos dados do transformer_inputs_fix")
                    fresh_data = latest_data

                    # IMPORTANTE: Atualizar o MCP com os dados do transformer_inputs_fix
                    # Isso garante que os dados essenciais estejam disponíveis para outros módulos
                    if latest_data.get('potencia_mva') is not None and latest_data.get('tensao_at') is not None and latest_data.get('tensao_bt') is not None:
                        log.debug(f"[{module_name}] Atualizando MCP com dados essenciais do transformer_inputs_fix")
                        app.mcp.set_data("transformer-inputs-store", latest_data)

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
                        ensure_mcp_data_propagation(app, "transformer-inputs-store", target_stores)
                        log.debug(f"[{module_name}] Propagação de dados para outros stores concluída")
            except Exception as e:
                log.error(f"[{module_name}] Erro ao obter dados do transformer_inputs_fix: {e}", exc_info=True)

        # Removida a correção para FLASH-BACK que usava dados fixos
        # Agora confiamos nos dados do MCP sem sobrescrever com valores fixos

        # Criar o painel com os dados frescos do MCP
        panel_html = create_transformer_info_panel(fresh_data)
        execution_time = time.time() - start_time
        log.debug(
            f"[{module_name}] Painel de informações global criado em {round(execution_time * 1000, 2)}ms"
        )

        # Retorna o mesmo painel para todas as saídas
        return [panel_html] * len(info_panel_outputs)
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(f"[{module_name}] Erro ao criar painel de informações global: {e}", exc_info=True)
        log.error(f"[{module_name}] Tempo de execução: {round(execution_time * 1000, 2)}ms")

        # Criar painel de erro
        error_panel = html.Div(
            f"Erro ao exibir informações: {str(e)}", className="alert alert-danger small"
        )
        return [error_panel] * len(info_panel_outputs)
