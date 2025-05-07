# callbacks/transformer_inputs.py
import dash
from dash import Input, Output, State, callback, ctx, no_update
import dash_bootstrap_components as dbc
import numpy as np
import logging
from dash.exceptions import PreventUpdate

print("\n\n")
print("*" * 100)
print("*" * 100)
print("**** IMPORTANDO MÓDULO TRANSFORMER_INPUTS - ESTE LOG DEVE APARECER SE O MÓDULO FOR CARREGADO ****")
print("*" * 100)
print("*" * 100)
print("\n\n")

# Não importar app diretamente para evitar importações circulares
# from app import app  # REMOVIDO

from app_core.standards import TabelaTransformadorNBR
from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS
from utils.store_diagnostics import convert_numpy_types
from utils.routes import normalize_pathname, ROUTE_HOME

log = logging.getLogger(__name__)
log.info("============ MÓDULO TRANSFORMER_INPUTS CARREGADO ============")
log.info(f"Nível de log: {logging.getLevelName(log.getEffectiveLevel())}")
log.info(f"Handlers configurados: {[h.__class__.__name__ for h in log.handlers]}")
log.info("=============================================================")
tabela_nbr = TabelaTransformadorNBR()

# --- Callbacks para OPTIONS (sem mudança) ---
# ... (update_nbi_sil_options, update_nbi_neutro_options, update_tensao_aplicada_options, update_tensao_induzida_options) ...
# Callback para preencher os dropdowns de NBI e SIL com base na classe de tensão
@app.callback(
    [
        Output("nbi_at", "options"), Output("sil_at", "options"),
        Output("nbi_bt", "options"), Output("sil_bt", "options"),
        Output("nbi_terciario", "options"), Output("sil_terciario", "options")
    ],
    [
        Input("classe_tensao_at", "value"), Input("classe_tensao_bt", "value"), Input("classe_tensao_terciario", "value")
    ],
    prevent_initial_call=False # Este pode rodar inicialmente para preencher opções vazias
)
def update_nbi_sil_options(classe_at, classe_bt, classe_terciario):
    def values_to_options(values):
        # Garante que 'value' seja string para consistência
        return [{'label': str(v), 'value': str(v) if v is not None else None} for v in values] if values else []

    nbi_at_options, sil_at_options = [], []
    nbi_bt_options, sil_bt_options = [], []
    nbi_terciario_options, sil_terciario_options = [], []

    if classe_at is not None:
        try:
            valores_at = tabela_nbr.get_nbi_sil_values(classe_at)
            nbi_at_options = values_to_options(valores_at.get("nbi", []))
            sil_at_options = values_to_options(valores_at.get("sil", []))
        except Exception as e: log.error(f"[NBI/SIL Options CB AT] Erro: {e}")

    if classe_bt is not None:
        try:
            valores_bt = tabela_nbr.get_nbi_sil_values(classe_bt)
            nbi_bt_options = values_to_options(valores_bt.get("nbi", []))
            sil_bt_options = values_to_options(valores_bt.get("sil", []))
        except Exception as e: log.error(f"[NBI/SIL Options CB BT] Erro: {e}")

    if classe_terciario is not None:
        try:
            valores_terciario = tabela_nbr.get_nbi_sil_values(classe_terciario)
            nbi_terciario_options = values_to_options(valores_terciario.get("nbi", []))
            sil_terciario_options = values_to_options(valores_terciario.get("sil", []))
        except Exception as e: log.error(f"[NBI/SIL Options CB Ter] Erro: {e}")

    return nbi_at_options, sil_at_options, nbi_bt_options, sil_bt_options, nbi_terciario_options, sil_terciario_options


# --- Callback para preencher os dropdowns de NBI Neutro (sem mudanças) ---
@app.callback(
    [
        Output("nbi_neutro_at", "options"), Output("nbi_neutro_bt", "options"), Output("nbi_neutro_terciario", "options")
    ],
    [
        Input("tensao_bucha_neutro_at", "value"), Input("tensao_bucha_neutro_bt", "value"), Input("tensao_bucha_neutro_terciario", "value")
    ],
    prevent_initial_call=False # Pode rodar inicialmente
)
def update_nbi_neutro_options(classe_neutro_at, classe_neutro_bt, classe_neutro_terciario):
    def values_to_options(values):
        # Garante que 'value' seja string
        return [{'label': str(v), 'value': str(v) if v is not None else None} for v in values] if values else []
    nbi_neutro_at_options, nbi_neutro_bt_options, nbi_neutro_terciario_options = [], [], []
    if classe_neutro_at is not None:
        try: nbi_neutro_at_options = values_to_options(tabela_nbr.get_nbi_neutro_values(classe_neutro_at))
        except Exception as e: log.error(f"[NBI Neutro Options CB AT] Erro: {e}")
    if classe_neutro_bt is not None:
        try: nbi_neutro_bt_options = values_to_options(tabela_nbr.get_nbi_neutro_values(classe_neutro_bt))
        except Exception as e: log.error(f"[NBI Neutro Options CB BT] Erro: {e}")
    if classe_neutro_terciario is not None:
        try: nbi_neutro_terciario_options = values_to_options(tabela_nbr.get_nbi_neutro_values(classe_neutro_terciario))
        except Exception as e: log.error(f"[NBI Neutro Options CB Ter] Erro: {e}")
    return nbi_neutro_at_options, nbi_neutro_bt_options, nbi_neutro_terciario_options

# --- Callback para preencher os dropdowns de Tensão Aplicada (sem mudanças) ---
@app.callback(
    [
        Output("teste_tensao_aplicada_at", "options"), Output("teste_tensao_aplicada_bt", "options"), Output("teste_tensao_aplicada_terciario", "options")
    ],
    [
        Input("classe_tensao_at", "value"), Input("classe_tensao_bt", "value"), Input("classe_tensao_terciario", "value"),
        Input("tensao_bucha_neutro_at", "value"), Input("tensao_bucha_neutro_bt", "value"), Input("tensao_bucha_neutro_terciario", "value"),
        Input("conexao_at", "value"), Input("conexao_bt", "value"), Input("conexao_terciario", "value")
    ],
    prevent_initial_call=False # Pode rodar inicialmente
)
def update_tensao_aplicada_options(classe_at, classe_bt, classe_ter,
                                  tn_neutro_at, tn_neutro_bt, tn_neutro_ter,
                                  con_at, con_bt, con_ter):
    def values_to_options(values):
        # Garante que 'value' seja string
        return [{'label': f"{v} kV", 'value': str(v) if v is not None else None} for v in values] if values else []
    def safe_float(v):
        if v is None or v == '': return None
        try: return float(v)
        except (ValueError, TypeError): return None

    tap_at_opts, tap_bt_opts, tap_ter_opts = [], [], []

    def get_options_for_winding(classe, tn_neutro, conexao):
        if classe is None: return []
        classe_f = safe_float(classe)
        if classe_f is None: return []
        try:
            um_para_busca = None
            if conexao == 'estrela' and tn_neutro is not None: # 'estrela' é Yn
                tn_neutro_f = safe_float(tn_neutro)
                if tn_neutro_f is not None:
                    um_para_busca = tn_neutro_f
            if um_para_busca is None:
                um_para_busca = classe_f
            return values_to_options(tabela_nbr.get_tensao_aplicada_values(um_para_busca))
        except Exception as e:
            log.error(f"[Tensão Aplicada Options CB] Erro: {e}")
            return []

    tap_at_opts = get_options_for_winding(classe_at, tn_neutro_at, con_at)
    tap_bt_opts = get_options_for_winding(classe_bt, tn_neutro_bt, con_bt)
    tap_ter_opts = get_options_for_winding(classe_ter, tn_neutro_ter, con_ter)

    return tap_at_opts, tap_bt_opts, tap_ter_opts

# --- Callback para preencher o dropdown de Tensão Induzida (sem mudanças) ---
@app.callback(
    Output("teste_tensao_induzida", "options"),
    Input("classe_tensao_at", "value"),
    prevent_initial_call=False # Pode rodar inicialmente
)
def update_tensao_induzida_options(classe_at):
    def values_to_options(values):
        # Garante que 'value' seja string
        return [{'label': f"{v} kV", 'value': str(v) if v is not None else None} for v in values] if values else []
    tensao_induzida_options = []
    if classe_at is not None:
        try: tensao_induzida_options = values_to_options(tabela_nbr.get_tensao_induzida_values(classe_at))
        except Exception as e: log.error(f"[Tensão Induzida Options CB] Erro: {e}")
    return tensao_induzida_options


# --- Callback para sincronizar elevação dos enrolamentos ---
@app.callback(
    [
        Output("elevacao_enrol_at", "value", allow_duplicate=True),
        Output("elevacao_enrol_bt", "value", allow_duplicate=True),
        Output("elevacao_enrol_terciario", "value", allow_duplicate=True),
        Output("transformer-inputs-store", "data", allow_duplicate=True)
    ],
    Input("elevacao_enrol", "value"),
    prevent_initial_call=True
)
def sync_elevacao_enrolamentos(valor_comum):
    """Sincroniza o valor de elevação de enrolamento comum para todos os enrolamentos."""
    if valor_comum is None:
        return no_update, no_update, no_update, no_update

    log.info(f"[Sync Elevação] Sincronizando valor de elevação de enrolamento: {valor_comum}")

    # Atualiza o MCP com o novo valor
    if app.mcp is None:
        log.error("[Sync Elevação] MCP não inicializado. Abortando.")
        return no_update, no_update, no_update, no_update

    mcp_data = app.mcp.get_data('transformer-inputs-store')
    if not mcp_data:
        mcp_data = DEFAULT_TRANSFORMER_INPUTS.copy()

    # Atualiza os valores de elevação para todos os enrolamentos
    updated_mcp_data = mcp_data.copy()
    updated_mcp_data.update({
        'elevacao_enrol': valor_comum,
        'elevacao_enrol_at': valor_comum,
        'elevacao_enrol_bt': valor_comum,
        'elevacao_enrol_terciario': valor_comum
    })

    serializable_data = convert_numpy_types(updated_mcp_data, debug_path="sync_elevacao_enrolamentos")
    app.mcp.set_data('transformer-inputs-store', serializable_data)
    log.info(f"[Sync Elevação] MCP atualizado com valor comum de elevação: {valor_comum}")

    # Forçar atualização dos painéis de informação
    try:
        from callbacks.global_updates import global_updates_all_transformer_info_panels
        log.info("[Sync Elevação] Forçando atualização dos painéis de informação")
        # Chamar a função diretamente com os dados atualizados
        global_updates_all_transformer_info_panels(serializable_data)
        log.info("[Sync Elevação] Painéis de informação atualizados com sucesso")
    except Exception as e:
        log.error(f"[Sync Elevação] Erro ao forçar atualização dos painéis: {e}", exc_info=True)

    return valor_comum, valor_comum, valor_comum, serializable_data

# --- Callback para carregar valor inicial de elevação comum ---
@app.callback(
    Output("elevacao_enrol", "value"),
    Input("url", "pathname"),
    prevent_initial_call=False
)
def load_elevacao_comum_initial(pathname):
    """Carrega o valor inicial de elevação comum a partir do MCP."""
    # Só executa na página correta
    if pathname is None:
        raise PreventUpdate

    clean_path = normalize_pathname(pathname)
    if clean_path != ROUTE_HOME:
        log.debug(f"[Load Elevação Comum] Não na página '{ROUTE_HOME}'. Prevenindo update.")
        raise PreventUpdate

    if app.mcp is None:
        log.error("[Load Elevação Comum] MCP não inicializado. Abortando.")
        return no_update

    # Obter dados do MCP
    transformer_data = app.mcp.get_data('transformer-inputs-store')
    if not transformer_data:
        log.warning("[Load Elevação Comum] Dados do MCP estão vazios. Usando defaults.")
        return no_update

    # Primeiro verifica se já existe um valor comum armazenado
    elevacao_comum = transformer_data.get('elevacao_enrol')

    # Se não existir, prioriza o valor de AT, depois BT, depois Terciário
    if elevacao_comum is None:
        elevacao_comum = transformer_data.get('elevacao_enrol_at')
    if elevacao_comum is None:
        elevacao_comum = transformer_data.get('elevacao_enrol_bt')
    if elevacao_comum is None:
        elevacao_comum = transformer_data.get('elevacao_enrol_terciario')

    log.info(f"[Load Elevação Comum] Valor carregado: {elevacao_comum}")
    return elevacao_comum

# --- Callbacks para atualizar VALORES de dropdowns (REMOVIDOS) ---
# Estes callbacks individuais foram removidos para evitar redundância e conflitos.
# O callback principal update_transformer_calculations_and_mcp é o único responsável
# por atualizar o MCP com todos os valores do formulário, incluindo os dropdowns.
# Isso simplifica o fluxo de dados e evita atualizações múltiplas e desordenadas do MCP.
#
# Os callbacks removidos eram:
# - update_mcp_from_nbi_sil_values
# - update_mcp_from_nbi_neutro_values
# - update_mcp_from_tensao_aplicada_values
# - update_mcp_from_tensao_induzida_value
#
# Agora, quando qualquer valor do formulário muda, o callback principal
# update_transformer_calculations_and_mcp é acionado, coleta todos os valores
# atuais da UI e atualiza o MCP de uma só vez.
#
# A UI é atualizada pelo callback load_ui_on_page_load quando necessário.

# --- Callback de Carregamento Inicial da UI (só roda na carga da página) ---
@app.callback(
    [ # 36 Outputs da UI (NÃO usa allow_duplicate)
        Output("corrente_nominal_at", "value"), Output("corrente_nominal_at_tap_maior", "value"), Output("corrente_nominal_at_tap_menor", "value"), Output("corrente_nominal_bt", "value"), Output("corrente_nominal_terciario", "value"),
        Output("tensao_bucha_neutro_at_col", "style"), Output("tensao_bucha_neutro_bt_col", "style"), Output("tensao_bucha_neutro_terciario_col", "style"), Output("nbi_neutro_at_col", "style"), Output("nbi_neutro_bt_col", "style"), Output("nbi_neutro_terciario_col", "style"), Output("sil_at_col", "style"), Output("sil_bt_col", "style"), Output("sil_terciario_col", "style"), Output("conexao_at_col", "style"), Output("conexao_bt_col", "style"), Output("conexao_terciario_col", "style"),
        Output("nbi_at", "value"), Output("nbi_bt", "value"), Output("nbi_terciario", "value"), Output("sil_at", "value"), Output("sil_bt", "value"), Output("sil_terciario", "value"),
        Output("nbi_neutro_at", "value"), Output("nbi_neutro_bt", "value"), Output("nbi_neutro_terciario", "value"),
        Output("teste_tensao_aplicada_at", "value"), Output("teste_tensao_aplicada_bt", "value"), Output("teste_tensao_aplicada_terciario", "value"), Output("teste_tensao_induzida", "value"),
        Output("conexao_at", "value"), Output("conexao_bt", "value"), Output("conexao_terciario", "value"),
        Output("tensao_bucha_neutro_at", "value"), Output("tensao_bucha_neutro_bt", "value"), Output("tensao_bucha_neutro_terciario", "value"),
    ],
    Input("url", "pathname"),
    # State("transformer-inputs-store", "data"), # Usar MCP em vez de State
    prevent_initial_call=False # <<< RODA na carga inicial >>>
)
def load_ui_on_page_load(pathname):
    """
    Carrega os valores iniciais dos componentes da UI lendo do MCP QUANDO a página é carregada.
    Este callback é o ÚNICO que roda com prevent_initial_call=False para esta página.
    """
    log.info("===============================================================")
    log.info("[Load UI Callback] INICIANDO CALLBACK DE CARREGAMENTO DA UI...")
    log.info("===============================================================")

    # Verificar o contexto do callback
    triggered = ctx.triggered
    triggered_id = ctx.triggered_id
    triggered_prop_ids = ctx.triggered_prop_ids

    log.info(f"[Load UI Callback] Disparado por: {triggered_id}")
    log.info(f"[Load UI Callback] Triggered: {triggered}")
    log.info(f"[Load UI Callback] Triggered Prop IDs: {triggered_prop_ids}")
    log.info(f"[Load UI Callback] Pathname: {pathname}")

    if app.mcp is None:
        log.error("[Load UI Callback] MCP não inicializado. Abortando.")
        return [no_update] * 36

    # IMPORTANTE: Este callback DEVE executar na inicialização da aplicação
    # Só executa na página correta
    if pathname is None:
        log.warning("[Load UI Callback] Pathname é None. Continuando mesmo assim para garantir inicialização.")
        # NÃO usar PreventUpdate aqui para garantir que o callback execute

    clean_path = normalize_pathname(pathname) if pathname else ""
    log.info(f"[Load UI Callback] Pathname normalizado: '{clean_path}'")

    # Aceita pathname vazio, '/', ou o route específico
    # Modificado para ser mais permissivo e garantir execução
    if clean_path != ROUTE_HOME and clean_path != '' and clean_path != '/' and clean_path != 'dados':
        log.debug(f"[Load UI Callback] Não na página '{ROUTE_HOME}'. Continuando mesmo assim.")
        # NÃO usar PreventUpdate aqui para garantir que o callback execute

    log.info(f"[Load UI Callback] Pathname: '{clean_path}'. Continuando execução.")

    log.debug("[Load UI Callback] Na página correta. Obtendo dados do MCP para carga inicial.")

    # Obter dados ATUALIZADOS do MCP
    transformer_data = app.mcp.get_data('transformer-inputs-store')
    if not transformer_data:
        log.warning("[Load UI Callback] Dados do MCP estão vazios. Usando defaults e salvando no MCP.")
        transformer_data = DEFAULT_TRANSFORMER_INPUTS.copy()
        serializable_data = convert_numpy_types(transformer_data, debug_path="load_ui_defaults")
        app.mcp.set_data('transformer-inputs-store', serializable_data)
        log.info("[Load UI Callback] MCP atualizado com valores padrão.")
        log.debug(f"[Load UI Callback] Valores padrão salvos no MCP: {serializable_data}")

    # NOTA: O cálculo de correntes e a atualização do MCP foram simplificados/removidos daqui.
    # Este callback agora foca-se em carregar os valores da UI a partir do estado atual do MCP.
    # Os valores persistidos na UI (pelo browser) serão capturados pelo
    # callback update_transformer_calculations_and_mcp quando o utilizador interagir.

    log.info("[Load UI Callback] Lendo dados do MCP para popular a UI.")
    # transformer_data já contém os dados do MCP (provavelmente os defaults no primeiro carregamento)

    # As correntes e estilos serão baseados nos dados do MCP.
    # Se forem defaults (None), os campos de corrente na UI serão None.
    calculated_currents = {
        'corrente_nominal_at': transformer_data.get('corrente_nominal_at'),
        'corrente_nominal_at_tap_maior': transformer_data.get('corrente_nominal_at_tap_maior'),
        'corrente_nominal_at_tap_menor': transformer_data.get('corrente_nominal_at_tap_menor'),
        'corrente_nominal_bt': transformer_data.get('corrente_nominal_bt'),
        'corrente_nominal_terciario': transformer_data.get('corrente_nominal_terciario')
    }
    log.info(f"[Load UI Callback] Usando correntes do MCP: {calculated_currents}")

    # Não é necessário chamar set_data no MCP aqui, pois estamos apenas a ler.
    # A atualização do MCP com dados da UI (incluindo persistidos) ocorrerá
    # através do callback update_transformer_calculations_and_mcp.

    # Forçar atualização dos painéis de informação com os dados atuais do MCP
    # Esta chamada pode ser redundante se global_updates_all_transformer_info_panels
    # já for acionado pela inicialização do store, mas garante que os painéis
    # reflitam o estado inicial do MCP.
    try:
        from callbacks.global_updates import global_updates_all_transformer_info_panels
        log.info("[Load UI Callback] Forçando atualização dos painéis de informação com dados do MCP.")
        global_updates_all_transformer_info_panels(transformer_data) # Passa os dados lidos do MCP
        log.info("[Load UI Callback] Painéis de informação (potencialmente) atualizados.")
    except Exception as e:
        log.error(f"[Load UI Callback] Erro ao tentar atualizar painéis: {e}", exc_info=True)

    visibility_styles_mcp = app.mcp.calculate_visibility_styles(transformer_data) # Usa os dados lidos do MCP

    # Extrair valores para a UI a partir do transformer_data (que veio do MCP)
    corrente_at = transformer_data.get('corrente_nominal_at')
    corrente_at_tap_maior = transformer_data.get('corrente_nominal_at_tap_maior')
    corrente_at_tap_menor = transformer_data.get('corrente_nominal_at_tap_menor')
    corrente_bt = transformer_data.get('corrente_nominal_bt')
    corrente_terciario = transformer_data.get('corrente_nominal_terciario')

    # Log detalhado dos valores que serão exibidos na UI
    log.info(f"[Load UI Callback] Valores de corrente para UI: AT={corrente_at}A, BT={corrente_bt}A, Terciário={corrente_terciario}A")
    neutro_at_col_style = visibility_styles_mcp.get('neutro_at_style')
    neutro_bt_col_style = visibility_styles_mcp.get('neutro_bt_style')
    neutro_ter_col_style = visibility_styles_mcp.get('neutro_ter_style')
    nbi_neutro_at_col_style = visibility_styles_mcp.get('nbi_neutro_at_style')
    nbi_neutro_bt_col_style = visibility_styles_mcp.get('nbi_neutro_bt_style')
    nbi_neutro_ter_col_style = visibility_styles_mcp.get('nbi_neutro_ter_style')
    sil_at_col_style = visibility_styles_mcp.get('sil_at_style')
    sil_bt_col_style = visibility_styles_mcp.get('sil_bt_style')
    sil_terciario_col_style = visibility_styles_mcp.get('sil_terciario_style')
    conexao_at_col_style = visibility_styles_mcp.get('conexao_at_style')
    conexao_bt_col_style = visibility_styles_mcp.get('conexao_bt_style')
    conexao_terciario_col_style = visibility_styles_mcp.get('conexao_terciario_style')
    nbi_at = transformer_data.get('nbi_at')
    nbi_bt = transformer_data.get('nbi_bt')
    nbi_terciario = transformer_data.get('nbi_terciario')
    sil_at = transformer_data.get('sil_at')
    sil_bt = transformer_data.get('sil_bt')
    sil_terciario = transformer_data.get('sil_terciario')
    nbi_neutro_at = transformer_data.get('nbi_neutro_at')
    nbi_neutro_bt = transformer_data.get('nbi_neutro_bt')
    nbi_neutro_terciario = transformer_data.get('nbi_neutro_terciario')
    teste_tensao_aplicada_at = transformer_data.get('teste_tensao_aplicada_at')
    teste_tensao_aplicada_bt = transformer_data.get('teste_tensao_aplicada_bt')
    teste_tensao_aplicada_terciario = transformer_data.get('teste_tensao_aplicada_terciario')
    teste_tensao_induzida = transformer_data.get('teste_tensao_induzida')
    conexao_at_val = transformer_data.get('conexao_at')
    conexao_bt_val = transformer_data.get('conexao_bt')
    conexao_terciario_val = transformer_data.get('conexao_terciario')
    tensao_bucha_neutro_at = transformer_data.get('tensao_bucha_neutro_at')
    tensao_bucha_neutro_bt = transformer_data.get('tensao_bucha_neutro_bt')
    tensao_bucha_neutro_terciario = transformer_data.get('tensao_bucha_neutro_terciario')

    log.info("[Load UI Callback] Dados do MCP carregados e processados para carga inicial da UI.")

    # Criar a tupla de retorno
    return_values = (
        corrente_at, corrente_at_tap_maior, corrente_at_tap_menor, corrente_bt, corrente_terciario,
        neutro_at_col_style, neutro_bt_col_style, neutro_ter_col_style,
        nbi_neutro_at_col_style, nbi_neutro_bt_col_style, nbi_neutro_ter_col_style,
        sil_at_col_style, sil_bt_col_style, sil_terciario_col_style,
        conexao_at_col_style, conexao_bt_col_style, conexao_terciario_col_style,
        nbi_at, nbi_bt, nbi_terciario, sil_at, sil_bt, sil_terciario,
        nbi_neutro_at, nbi_neutro_bt, nbi_neutro_terciario,
        teste_tensao_aplicada_at, teste_tensao_aplicada_bt, teste_tensao_aplicada_terciario, teste_tensao_induzida,
        conexao_at_val, conexao_bt_val, conexao_terciario_val,
        tensao_bucha_neutro_at, tensao_bucha_neutro_bt, tensao_bucha_neutro_terciario
    )

    # Log resumido dos valores retornados
    log.info(f"[Load UI Callback] Valores retornados para UI: AT={corrente_at}A, BT={corrente_bt}A, Terciário={corrente_terciario}A")

    return return_values

# --- Callback Principal de Atualização (Usando padrão de registro centralizado) ---
def register_transformer_calculations_callback(app_instance):
    """
    Registra o callback principal de cálculos do transformador.
    Esta função é chamada por app.py durante a inicialização.
    """
    @app_instance.callback(
        Output("corrente_nominal_at", "value"),
        [Input("potencia_mva", "value"), Input("tensao_at", "value")],
        prevent_initial_call=False # Permite rodar na carga inicial para garantir que o MCP seja atualizado
    )
    def update_transformer_calculations_and_mcp(potencia_mva, tensao_at):
        """
        Versão simplificada do callback para teste.
        """
        print("\n\n")
        print("!" * 100)
        print("!" * 100)
        print("!!!! CALLBACK UPDATE_TRANSFORMER_CALCULATIONS_AND_MCP ACIONADO !!!!")
        print("!" * 100)
        print("!" * 100)
        print("\n\n")

        print(f"[Update Callback] Potência MVA: {potencia_mva}")
        print(f"[Update Callback] Tensão AT: {tensao_at}")

        log.info(f"[Update Callback] ACIONADO! Potência: {potencia_mva}, Tensão AT: {tensao_at}")

        # Cálculo simplificado da corrente
        try:
            if potencia_mva is not None and tensao_at is not None and float(potencia_mva) > 0 and float(tensao_at) > 0:
                potencia = float(potencia_mva)
                tensao = float(tensao_at)
                corrente = round((potencia * 1000) / (tensao * 1.732), 2)  # Arredondado para 2 casas decimais
                log.info(f"[Update Callback] Corrente calculada: {corrente}A")
                return corrente
        except Exception as e:
            log.error(f"[Update Callback] Erro: {e}")

        return None

    log.info("Callback update_transformer_calculations_and_mcp registrado com sucesso!")
    return True

# --- Callback para Limpar Campos (MODIFICADO - Usa allow_duplicate=True) ---
@app.callback(
    [Output(id, "value", allow_duplicate=True) for id in [
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao", "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento", "elevacao_enrol",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia", "nbi_at", "sil_at", "tensao_at_tap_maior", "impedancia_tap_maior", "tensao_at_tap_menor", "impedancia_tap_menor", "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario", "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios",
        "corrente_nominal_at", "corrente_nominal_at_tap_maior", "corrente_nominal_at_tap_menor", "corrente_nominal_bt", "corrente_nominal_terciario"
    ]] +
    [Output(id, "style", allow_duplicate=True) for id in [
        "conexao_at_col", "conexao_bt_col", "conexao_terciario_col", "tensao_bucha_neutro_at_col", "tensao_bucha_neutro_bt_col", "tensao_bucha_neutro_terciario_col", "nbi_neutro_at_col", "nbi_neutro_bt_col", "nbi_neutro_terciario_col", "sil_at_col", "sil_bt_col", "sil_terciario_col",
    ]],
    [Input("limpar-transformer-inputs", "n_clicks")],
    prevent_initial_call=True
)
def limpar_transformer_inputs_trigger(n_clicks):
    """ Limpa todos os campos do formulário e reseta o MCP e a UI. """
    if n_clicks is None or n_clicks == 0: raise PreventUpdate
    log.info(f"Callback limpar_transformer_inputs_trigger disparado (n_clicks={n_clicks})")

    if app.mcp is None:
        log.error("[Clear Callback] MCP não inicializado. Abortando.")
        return tuple([no_update] * 61)

    app.mcp.clear_data('transformer-inputs-store')
    log.info("[Clear Callback] Dados limpos no MCP.")
    cleaned_mcp_data = app.mcp.get_data('transformer-inputs-store')

    # Calcular correntes com base nos dados limpos
    log.info("[Clear Callback] Calculando correntes nominais após limpeza...")
    calculated_currents_cleared = app.mcp.calculate_nominal_currents(cleaned_mcp_data)
    log.info(f"[Clear Callback] Correntes calculadas após limpeza: {calculated_currents_cleared}")

    # Adicionar os valores calculados de corrente ao dicionário de dados limpos
    updated_cleaned_data = cleaned_mcp_data.copy()
    updated_cleaned_data.update({
        'corrente_nominal_at': calculated_currents_cleared.get('corrente_nominal_at'),
        'corrente_nominal_at_tap_maior': calculated_currents_cleared.get('corrente_nominal_at_tap_maior'),
        'corrente_nominal_at_tap_menor': calculated_currents_cleared.get('corrente_nominal_at_tap_menor'),
        'corrente_nominal_bt': calculated_currents_cleared.get('corrente_nominal_bt'),
        'corrente_nominal_terciario': calculated_currents_cleared.get('corrente_nominal_terciario')
    })

    # Salvar os dados atualizados no MCP
    serializable_data = convert_numpy_types(updated_cleaned_data, debug_path="limpar_transformer_inputs_trigger")
    app.mcp.set_data('transformer-inputs-store', serializable_data, validate=True)
    log.info("[Clear Callback] MCP atualizado com correntes calculadas após limpeza.")

    # Usar os dados atualizados para a UI
    cleaned_mcp_data = updated_cleaned_data

    default_ui_values = []
    input_ids_for_clear = [
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao", "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento", "elevacao_enrol",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia", "nbi_at", "sil_at", "tensao_at_tap_maior", "impedancia_tap_maior", "tensao_at_tap_menor", "impedancia_tap_menor", "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario", "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]
    for field_id in input_ids_for_clear:
        default_ui_values.append(cleaned_mcp_data.get(field_id, None))

    # Usar os valores de corrente já calculados e armazenados no MCP
    cleared_current_values = [
        cleaned_mcp_data.get('corrente_nominal_at'),
        cleaned_mcp_data.get('corrente_nominal_at_tap_maior'),
        cleaned_mcp_data.get('corrente_nominal_at_tap_menor'),
        cleaned_mcp_data.get('corrente_nominal_bt'),
        cleaned_mcp_data.get('corrente_nominal_terciario')
    ]

    visibility_styles_cleared = app.mcp.calculate_visibility_styles()
    cleared_style_values = [
        visibility_styles_cleared.get('conexao_at_style'), visibility_styles_cleared.get('conexao_bt_style'), visibility_styles_cleared.get('conexao_terciario_style'),
        visibility_styles_cleared.get('neutro_at_style'), visibility_styles_cleared.get('neutro_bt_style'), visibility_styles_cleared.get('neutro_ter_style'),
        visibility_styles_cleared.get('nbi_neutro_at_style'), visibility_styles_cleared.get('nbi_neutro_bt_style'), visibility_styles_cleared.get('nbi_neutro_ter_style'),
        visibility_styles_cleared.get('sil_at_style'), visibility_styles_cleared.get('sil_bt_style'), visibility_styles_cleared.get('sil_terciario_style')
    ]

    all_output_values = default_ui_values + cleared_current_values + cleared_style_values
    log.info("[Clear Callback] Valores e estilos padrão para UI preparados.")

    return tuple(all_output_values)

# As funções de registro de callbacks para forçar atualização do MCP e limpar cache local foram removidas

# Função de registro explícito
def register_transformer_inputs_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de transformer_inputs.
    Esta função é chamada por app.py durante a inicialização.

    Registra os callbacks que foram convertidos para o padrão de registro centralizado.
    """
    log.info(f"Registrando callbacks do módulo transformer_inputs para app {app_instance.title}...")

    # Registrar os callbacks que foram convertidos para o padrão de registro centralizado
    register_transformer_calculations_callback(app_instance)
    # Os callbacks para forçar atualização do MCP e limpar cache local foram removidos

    log.info(f"Todos os callbacks do módulo transformer_inputs registrados com sucesso para app {app_instance.title}.")
    return True
