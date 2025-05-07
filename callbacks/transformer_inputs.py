# callbacks/transformer_inputs.py
import dash
from dash import Input, Output, State, callback, ctx, no_update
import dash_bootstrap_components as dbc
import numpy as np
import logging
from dash.exceptions import PreventUpdate

from app import app
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

    # Calcular correntes e estilos usando os métodos do MCP
    log.info("[Load UI Callback] Calculando correntes nominais...")

    # Garantir que temos dados mínimos para o cálculo
    if not transformer_data:
        log.warning("[Load UI Callback] Dados vazios! Criando dicionário com valores padrão")
        transformer_data = {
            'tipo_transformador': 'Trifásico',
            'potencia_mva': 10.0,
            'tensao_at': 138.0,
            'tensao_bt': 13.8,
            'tensao_terciario': 0.0
        }

    # Garantir que temos os campos necessários
    if 'tipo_transformador' not in transformer_data:
        transformer_data['tipo_transformador'] = 'Trifásico'
    if 'potencia_mva' not in transformer_data or not transformer_data['potencia_mva']:
        transformer_data['potencia_mva'] = 10.0
    if 'tensao_at' not in transformer_data or not transformer_data['tensao_at']:
        transformer_data['tensao_at'] = 138.0
    if 'tensao_bt' not in transformer_data or not transformer_data['tensao_bt']:
        transformer_data['tensao_bt'] = 13.8

    # Calcular correntes
    calculated_currents = app.mcp.calculate_nominal_currents(transformer_data)
    log.info(f"[Load UI Callback] Correntes calculadas: {calculated_currents}")

    # Sempre atualizar o MCP com as correntes calculadas
    # Adicionar os valores calculados de corrente ao dicionário de dados do transformador
    updated_transformer_data = transformer_data.copy()
    updated_transformer_data.update({
        'corrente_nominal_at': calculated_currents.get('corrente_nominal_at'),
        'corrente_nominal_at_tap_maior': calculated_currents.get('corrente_nominal_at_tap_maior'),
        'corrente_nominal_at_tap_menor': calculated_currents.get('corrente_nominal_at_tap_menor'),
        'corrente_nominal_bt': calculated_currents.get('corrente_nominal_bt'),
        'corrente_nominal_terciario': calculated_currents.get('corrente_nominal_terciario')
    })

    # Serializar e salvar no MCP
    serializable_data = convert_numpy_types(updated_transformer_data, debug_path="load_ui_with_currents")
    app.mcp.set_data('transformer-inputs-store', serializable_data)
    log.info("[Load UI Callback] MCP atualizado com correntes calculadas.")
    log.info(f"[Load UI Callback] Valores de corrente salvos: AT={updated_transformer_data.get('corrente_nominal_at')}A, BT={updated_transformer_data.get('corrente_nominal_bt')}A")

    # Usar os dados atualizados para calcular os estilos
    visibility_styles_mcp = app.mcp.calculate_visibility_styles(updated_transformer_data)

    # Usar os dados atualizados para a UI
    transformer_data = updated_transformer_data

    # Extrair valores para a UI (lógica igual ao callback anterior)
    # Garantir que temos valores válidos para as correntes
    corrente_at = calculated_currents.get('corrente_nominal_at')
    corrente_at_tap_maior = calculated_currents.get('corrente_nominal_at_tap_maior')
    corrente_at_tap_menor = calculated_currents.get('corrente_nominal_at_tap_menor')
    corrente_bt = calculated_currents.get('corrente_nominal_bt')
    corrente_terciario = calculated_currents.get('corrente_nominal_terciario')

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

    # Log detalhado dos valores retornados
    log.info("===============================================================")
    log.info("[Load UI Callback] VALORES RETORNADOS PARA UI:")
    log.info(f"Corrente AT: {corrente_at}")
    log.info(f"Corrente BT: {corrente_bt}")
    log.info(f"Corrente Terciário: {corrente_terciario}")
    log.info(f"Corrente AT Tap Maior: {corrente_at_tap_maior}")
    log.info(f"Corrente AT Tap Menor: {corrente_at_tap_menor}")
    log.info("===============================================================")

    return return_values

# --- Callback Principal de Atualização (MODIFICADO - Usa allow_duplicate=True) ---
@app.callback(
    [ # Outputs: 5 Correntes + 12 Estilos = 17 Outputs da UI (COM allow_duplicate=True)
     Output("corrente_nominal_at", "value", allow_duplicate=True), Output("corrente_nominal_at_tap_maior", "value", allow_duplicate=True), Output("corrente_nominal_at_tap_menor", "value", allow_duplicate=True), Output("corrente_nominal_bt", "value", allow_duplicate=True), Output("corrente_nominal_terciario", "value", allow_duplicate=True),
     Output("conexao_at_col", "style", allow_duplicate=True), Output("conexao_bt_col", "style", allow_duplicate=True), Output("conexao_terciario_col", "style", allow_duplicate=True), Output("tensao_bucha_neutro_at_col", "style", allow_duplicate=True), Output("tensao_bucha_neutro_bt_col", "style", allow_duplicate=True), Output("tensao_bucha_neutro_terciario_col", "style", allow_duplicate=True), Output("nbi_neutro_at_col", "style", allow_duplicate=True), Output("nbi_neutro_bt_col", "style", allow_duplicate=True), Output("nbi_neutro_terciario_col", "style", allow_duplicate=True), Output("sil_at_col", "style", allow_duplicate=True), Output("sil_bt_col", "style", allow_duplicate=True), Output("sil_terciario_col", "style", allow_duplicate=True),
     # Output("transformer-inputs-store", "data") # REMOVIDO - Atualização via MCP
     ],
    [Input(id, "value") for id in [ # 45 Inputs
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao", "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento", "elevacao_enrol",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia", "nbi_at", "sil_at", "tensao_at_tap_maior", "impedancia_tap_maior", "tensao_at_tap_menor", "impedancia_tap_menor", "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario", "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]],
    prevent_initial_call=True # Roda apenas quando um Input muda
)
def update_transformer_calculations_and_mcp(*args):
    """
    Processa inputs da UI, atualiza o MCP, e retorna os valores calculados
    e estilos para a UI.
    """
    triggered_input = ctx.triggered_id
    log.debug(f"[Update Callback] Disparado por input: {triggered_input}")
    log.info(f"[Update Callback] Argumentos recebidos: {args}")

    if app.mcp is None:
        log.error("[Update Callback] MCP não inicializado. Abortando.")
        return [no_update] * 17

    input_ids = [
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao", "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento", "elevacao_enrol",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia", "nbi_at", "sil_at", "tensao_at_tap_maior", "impedancia_tap_maior", "tensao_at_tap_menor", "impedancia_tap_menor", "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt", "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario", "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]
    inputs_dict = dict(zip(input_ids, args))
    log.debug(f"[Update Callback] Valores de entrada da UI: {inputs_dict}")

    try:
        # Verificar se temos os dados mínimos necessários para o cálculo
        if 'potencia_mva' in inputs_dict and inputs_dict['potencia_mva'] and 'tensao_at' in inputs_dict and inputs_dict['tensao_at'] and 'tensao_bt' in inputs_dict and inputs_dict['tensao_bt']:
            log.info("[Update Callback] Dados mínimos para cálculo de correntes estão presentes.")
        else:
            log.warning("[Update Callback] Dados mínimos para cálculo de correntes NÃO estão presentes. Verificando valores:")
            log.warning(f"Potência MVA: {inputs_dict.get('potencia_mva')}")
            log.warning(f"Tensão AT: {inputs_dict.get('tensao_at')}")
            log.warning(f"Tensão BT: {inputs_dict.get('tensao_bt')}")

            # Garantir valores mínimos para cálculo
            if 'potencia_mva' not in inputs_dict or not inputs_dict['potencia_mva']:
                inputs_dict['potencia_mva'] = 10.0
                log.warning(f"[Update Callback] Usando valor padrão para potencia_mva: {inputs_dict['potencia_mva']}")
            if 'tensao_at' not in inputs_dict or not inputs_dict['tensao_at']:
                inputs_dict['tensao_at'] = 138.0
                log.warning(f"[Update Callback] Usando valor padrão para tensao_at: {inputs_dict['tensao_at']}")
            if 'tensao_bt' not in inputs_dict or not inputs_dict['tensao_bt']:
                inputs_dict['tensao_bt'] = 13.8
                log.warning(f"[Update Callback] Usando valor padrão para tensao_bt: {inputs_dict['tensao_bt']}")
            if 'tipo_transformador' not in inputs_dict or not inputs_dict['tipo_transformador']:
                inputs_dict['tipo_transformador'] = 'Trifásico'
                log.warning(f"[Update Callback] Usando valor padrão para tipo_transformador: {inputs_dict['tipo_transformador']}")

        # Primeiro, serializar e salvar os dados básicos no MCP
        serializable_inputs = convert_numpy_types(inputs_dict, debug_path="update_transformer_inputs")
        log.debug("[Update Callback] Dados da UI serializados.")
        app.mcp.set_data('transformer-inputs-store', serializable_inputs)
        log.info("[Update Callback] MCP atualizado com dados da UI.")

        # Sempre calcular as correntes, mesmo com dados incompletos
        # O método calculate_nominal_currents foi modificado para lidar com dados ausentes
        log.info("[Update Callback] Calculando correntes nominais...")
        calculated_currents = app.mcp.calculate_nominal_currents(inputs_dict)
        log.info(f"[Update Callback] Correntes calculadas: {calculated_currents}")

        # Verificar se as correntes foram calculadas corretamente
        if calculated_currents and 'corrente_nominal_at' in calculated_currents and calculated_currents['corrente_nominal_at']:
            log.info(f"[Update Callback] Corrente AT calculada com sucesso: {calculated_currents['corrente_nominal_at']}A")
        else:
            log.error("[Update Callback] Falha no cálculo da corrente AT. Tentando recalcular...")
            # Forçar recálculo com valores garantidos
            temp_data = {
                'tipo_transformador': inputs_dict.get('tipo_transformador', 'Trifásico'),
                'potencia_mva': float(inputs_dict.get('potencia_mva', 10.0)),
                'tensao_at': float(inputs_dict.get('tensao_at', 138.0)),
                'tensao_bt': float(inputs_dict.get('tensao_bt', 13.8)),
                'tensao_terciario': float(inputs_dict.get('tensao_terciario', 0.0))
            }
            calculated_currents = app.mcp.calculate_nominal_currents(temp_data)
            log.info(f"[Update Callback] Correntes recalculadas: {calculated_currents}")

        # Adicionar os valores calculados de corrente ao dicionário de inputs
        inputs_dict.update({
            'corrente_nominal_at': calculated_currents.get('corrente_nominal_at'),
            'corrente_nominal_at_tap_maior': calculated_currents.get('corrente_nominal_at_tap_maior'),
            'corrente_nominal_at_tap_menor': calculated_currents.get('corrente_nominal_at_tap_menor'),
            'corrente_nominal_bt': calculated_currents.get('corrente_nominal_bt'),
            'corrente_nominal_terciario': calculated_currents.get('corrente_nominal_terciario')
        })

        # Serializar e salvar no MCP novamente com as correntes calculadas
        serializable_inputs = convert_numpy_types(inputs_dict, debug_path="update_transformer_inputs_with_currents")
        log.debug("[Update Callback] Dados da UI serializados (incluindo correntes calculadas).")
        app.mcp.set_data('transformer-inputs-store', serializable_inputs)
        log.info("[Update Callback] MCP atualizado com dados da UI e correntes calculadas.")

        # Recalcular estilos de visibilidade
        visibility_styles_mcp = app.mcp.calculate_visibility_styles()

        # Obter os valores calculados de corrente
        corrente_nominal_at = calculated_currents.get('corrente_nominal_at')
        corr_at_maior = calculated_currents.get('corrente_nominal_at_tap_maior')
        corr_at_menor = calculated_currents.get('corrente_nominal_at_tap_menor')
        corrente_nominal_bt = calculated_currents.get('corrente_nominal_bt')
        corrente_nominal_terciario = calculated_currents.get('corrente_nominal_terciario')

        # Verificar se os valores são válidos
        if corrente_nominal_at is None or corrente_nominal_at == 0:
            log.warning("[Update Callback] Corrente AT inválida ou zero. Recalculando...")
            # Tentar recalcular com valores garantidos
            temp_data = {
                'tipo_transformador': inputs_dict.get('tipo_transformador', 'Trifásico'),
                'potencia_mva': float(inputs_dict.get('potencia_mva', 10.0)),
                'tensao_at': float(inputs_dict.get('tensao_at', 138.0)),
                'tensao_bt': float(inputs_dict.get('tensao_bt', 13.8)),
                'tensao_terciario': float(inputs_dict.get('tensao_terciario', 0.0))
            }
            recalculated_currents = app.mcp.calculate_nominal_currents(temp_data)
            corrente_nominal_at = recalculated_currents.get('corrente_nominal_at')
            corr_at_maior = recalculated_currents.get('corrente_nominal_at_tap_maior')
            corr_at_menor = recalculated_currents.get('corrente_nominal_at_tap_menor')
            corrente_nominal_bt = recalculated_currents.get('corrente_nominal_bt')
            corrente_nominal_terciario = recalculated_currents.get('corrente_nominal_terciario')
            log.info(f"[Update Callback] Correntes recalculadas: AT={corrente_nominal_at}A, BT={corrente_nominal_bt}A")

            # Atualizar o MCP com os valores recalculados
            inputs_dict.update({
                'corrente_nominal_at': corrente_nominal_at,
                'corrente_nominal_at_tap_maior': corr_at_maior,
                'corrente_nominal_at_tap_menor': corr_at_menor,
                'corrente_nominal_bt': corrente_nominal_bt,
                'corrente_nominal_terciario': corrente_nominal_terciario
            })

            # Salvar novamente no MCP
            serializable_inputs = convert_numpy_types(inputs_dict, debug_path="update_transformer_inputs_with_recalculated_currents")
            app.mcp.set_data('transformer-inputs-store', serializable_inputs)
            log.info("[Update Callback] MCP atualizado com correntes recalculadas.")
        conexao_at_style = visibility_styles_mcp.get('conexao_at_style')
        conexao_bt_style = visibility_styles_mcp.get('conexao_bt_style')
        conexao_terciario_style = visibility_styles_mcp.get('conexao_terciario_style')
        neutro_at_style = visibility_styles_mcp.get('neutro_at_style')
        neutro_bt_style = visibility_styles_mcp.get('neutro_bt_style')
        neutro_ter_style = visibility_styles_mcp.get('neutro_ter_style')
        nbi_neutro_at_style = visibility_styles_mcp.get('nbi_neutro_at_style')
        nbi_neutro_bt_style = visibility_styles_mcp.get('nbi_neutro_bt_style')
        nbi_neutro_ter_style = visibility_styles_mcp.get('nbi_neutro_ter_style')
        sil_at_style = visibility_styles_mcp.get('sil_at_style')
        sil_bt_style = visibility_styles_mcp.get('sil_bt_style')
        sil_terciario_style = visibility_styles_mcp.get('sil_terciario_style')

    except Exception as e:
        log.error(f"[Update Callback] Erro: {e}", exc_info=True)
        return [no_update] * 17

    log.info(f"[Update Callback] Dados processados e prontos para UI.")

    # Criar a tupla de retorno
    return_values = (
        corrente_nominal_at, corr_at_maior, corr_at_menor,
        corrente_nominal_bt, corrente_nominal_terciario,
        conexao_at_style, conexao_bt_style, conexao_terciario_style,
        neutro_at_style, neutro_bt_style, neutro_ter_style,
        nbi_neutro_at_style, nbi_neutro_bt_style, nbi_neutro_ter_style,
        sil_at_style, sil_bt_style, sil_terciario_style
    )

    # Log detalhado dos valores retornados
    log.info("===============================================================")
    log.info("[Update Callback] VALORES RETORNADOS PARA UI:")
    log.info(f"Corrente AT: {corrente_nominal_at}")
    log.info(f"Corrente BT: {corrente_nominal_bt}")
    log.info(f"Corrente Terciário: {corrente_nominal_terciario}")
    log.info(f"Corrente AT Tap Maior: {corr_at_maior}")
    log.info(f"Corrente AT Tap Menor: {corr_at_menor}")
    log.info("===============================================================")

    return return_values

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
    app.mcp.set_data('transformer-inputs-store', serializable_data)
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

# Função de registro explícito
def register_transformer_inputs_callbacks(app_instance):
    """
    Função de registro explícito para callbacks de transformer_inputs.
    Esta função é chamada por app.py durante a inicialização.

    Como os callbacks já estão registrados via decorador @app.callback,
    esta função apenas registra esse fato no log.
    """
    log.info(f"Callbacks do módulo transformer_inputs já registrados via decoradores @app.callback para app {app_instance.title}.")
    # Não é necessário registrar novamente os callbacks, pois já foram registrados via decorador @app.callback
    return True