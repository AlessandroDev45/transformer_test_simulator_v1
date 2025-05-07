# callbacks/global_updates.py
"""
Callbacks globais para atualização de componentes em múltiplas seções.
Centraliza a atualização dos painéis de informação do transformador lendo do MCP.
"""
import logging
import time
from datetime import datetime

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
def diagnose_and_fix_mcp(pathname):
    """
    Diagnostica e corrige o MCP quando a aplicação iniciar.
    Este callback é executado uma vez na inicialização.
    """
    log.info("[MCP Diagnostics] Iniciando diagnóstico do MCP...")

    # Executar diagnóstico
    diagnosis = diagnose_mcp(app, verbose=True)
    log.info(f"[MCP Diagnostics] Resultado do diagnóstico: {diagnosis['status']}")

    if diagnosis["status"] != "ok":
        log.warning(
            f"[MCP Diagnostics] Problemas encontrados: {diagnosis['warnings']} {diagnosis['errors']}"
        )

        # Tentar corrigir problemas
        log.info("[MCP Diagnostics] Tentando corrigir problemas...")
        fix_result = fix_mcp_data(app, verbose=True)
        log.info(f"[MCP Diagnostics] Resultado da correção: {fix_result['status']}")

        if fix_result["status"] == "ok":
            log.info(f"[MCP Diagnostics] Ações realizadas: {fix_result['actions']}")
        else:
            log.error(f"[MCP Diagnostics] Erros na correção: {fix_result['errors']}")
    else:
        log.info("[MCP Diagnostics] MCP em bom estado. Nenhuma correção necessária.")

    # Retornar string vazia para o search da URL (não afeta a navegação)
    return ""


@callback(
    info_panel_outputs,
    Input("transformer-inputs-store", "data"),  # Acionado quando o store (e portanto o MCP) muda
    Input("url", "pathname"),  # Adicionado para detectar mudanças de rota
    prevent_initial_call="initial_duplicate",  # Permite rodar na carga inicial para exibir dados padrão/carregados
)
def global_updates_all_transformer_info_panels(
    store_data, pathname
):  # Recebe dados do store como trigger
    """
    Atualiza TODOS os painéis de informação do transformador lendo do MCP.
    """
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    triggered_id = ctx.triggered_id if ctx.triggered else "Initial Load / No Trigger"
    module_name = "global_updates"
    function_name = "global_updates_all_transformer_info_panels"

    # IMPORTANTE: Evitar execução quando o trigger for mudança de URL
    # Isso evita que o callback seja executado durante navegação entre páginas
    # e potencialmente sobrescreva dados válidos com None
    if triggered_id == "url":
        log.debug(f"[{module_name}] Callback ignorado - trigger é mudança de URL")
        raise dash.exceptions.PreventUpdate

    log.debug(f"[{module_name}] ========== INICIANDO ATUALIZAÇÃO GLOBAL DE PAINÉIS ==========")
    log.debug(f"[{module_name}] Trigger: {triggered_id}")

    # Verificar dados do store recebido como trigger
    if not store_data:
        log.debug(f"[{module_name}] Nenhum dado recebido do store como trigger")

    if app.mcp is None:
        log.error(f"[{module_name}] MCP não disponível. Não é possível atualizar painéis.")
        error_panel = html.Div(
            "Erro interno: MCP não inicializado.", className="alert alert-danger small"
        )
        return [error_panel] * len(info_panel_outputs)

    # --- Obter dados do MCP ---
    # SEMPRE obter os dados diretamente do MCP para garantir que estamos usando os dados mais atualizados
    log.info(f"[{module_name}] Obtendo dados diretamente do MCP")
    transformer_data_mcp = app.mcp.get_data("transformer-inputs-store")

    # Verificar se temos dados essenciais no MCP
    has_essential_data = (
        transformer_data_mcp
        and transformer_data_mcp.get("potencia_mva") is not None
        and transformer_data_mcp.get("tensao_at") is not None
        and transformer_data_mcp.get("tensao_bt") is not None
    )

    # Verificar se temos dados essenciais no store
    store_has_essential_data = (
        isinstance(store_data, dict)
        and store_data.get("potencia_mva") is not None
        and store_data.get("tensao_at") is not None
        and store_data.get("tensao_bt") is not None
    )

    if has_essential_data:
        log.debug(
            f"[{module_name}] MCP contém dados essenciais: potencia={transformer_data_mcp.get('potencia_mva')}, tensao_at={transformer_data_mcp.get('tensao_at')}, tensao_bt={transformer_data_mcp.get('tensao_bt')}"
        )
    elif store_has_essential_data:
        log.debug(
            f"[{module_name}] Store contém dados essenciais: potencia={store_data.get('potencia_mva')}, tensao_at={store_data.get('tensao_at')}, tensao_bt={store_data.get('tensao_bt')}"
        )

        # IMPORTANTE: Usar patch_mcp em vez de set_data para evitar sobrescrever dados válidos com None
        # Isso garante que apenas campos não vazios sejam atualizados
        if patch_mcp("transformer-inputs-store", store_data, app):
            log.debug(f"[{module_name}] MCP atualizado com dados não vazios do store")
            # Obter os dados atualizados do MCP
            transformer_data_mcp = app.mcp.get_data("transformer-inputs-store")
            has_essential_data = True
        else:
            log.debug(f"[{module_name}] Nenhum dado válido para atualizar no MCP")
    else:
        log.debug(f"[{module_name}] Dados essenciais ausentes no MCP e no store")

        # Verificar se temos dados no store que podemos usar
        if isinstance(store_data, dict) and store_data:
            # Usar os dados do store diretamente para exibição, mas NÃO atualizar o MCP
            transformer_data_mcp = store_data
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

    # Criar o painel HTML
    try:
        panel_html = create_transformer_info_panel(transformer_data_mcp)
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
