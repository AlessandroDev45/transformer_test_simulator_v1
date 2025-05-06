# callbacks/transformer_inputs.py
# Nenhuma mudança necessária nos callbacks de preenchimento de NBI/SIL/Neutro/Aplicada/Induzida.
# Apenas verificar os callbacks `load_current_values_from_store`, `update_transformer_calculations_and_store`,
# e `limpar_transformer_inputs_trigger` para garantir que os campos de conexão e neutro são
# corretamente lidos, salvos, limpos e usados para controlar a visibilidade.
# O código fornecido já inclui esses campos nos callbacks relevantes.
"""
Callbacks para a seção 'Dados Básicos do Transformador'.
Inclui cálculo de correntes nominais, controle de visibilidade
e salvamento/limpeza dos dados no dcc.Store.
"""
import dash
from dash import Input, Output, State, callback, ctx, no_update
import dash_bootstrap_components as dbc
import numpy as np
import logging
from dash.exceptions import PreventUpdate

# Importar a instância da aplicação
from app import app
# Importar a classe TabelaTransformadorNBR para obter valores de NBI e SIL
from app_core.standards import TabelaTransformadorNBR
# Importar DEFAULT_TRANSFORMER_INPUTS do módulo mcp
from app_core.transformer_mcp import DEFAULT_TRANSFORMER_INPUTS
# Importar utore_utils import prepare_data_for_store # Ainda pode ser útil para garantir serialização se MCP não o fizer completamente

log = logging.getLogger(__name__)

# Instância da classe TabelaTransformadorNBR
tabela_nbr = TabelaTransformadorNBR()

# Constantes para tipos de transformador
TIPO_TRIFASICO = 'Trifásico'
TIPO_MONOFASICO = 'Monofásico'

# --- Callback para preencher os dropdowns de NBI e SIL com base na classe de tensão ---
@callback(
    [
        Output("nbi_at", "options"), Output("sil_at", "options"),
        Output("nbi_bt", "options"), Output("sil_bt", "options"),
        Output("nbi_terciario", "options"), Output("sil_terciario", "options")
    ],
    [
        Input("classe_tensao_at", "value"), Input("classe_tensao_bt", "value"), Input("classe_tensao_terciario", "value")
    ],
    prevent_initial_call=False
)
def update_nbi_sil_options(classe_at, classe_bt, classe_terciario):
    def values_to_options(values):
        return [{'label': str(v), 'value': v} for v in values] if values else []
    nbi_at_options, sil_at_options = [], []
    nbi_bt_options, sil_bt_options = [], []
    nbi_terciario_options, sil_terciario_options = [], []
    if classe_at is not None:
        try:
            valores_at = tabela_nbr.get_nbi_sil_values(classe_at)
            nbi_at_options = values_to_options(valores_at["nbi"])
            sil_at_options = values_to_options(valores_at["sil"])
        except Exception as e: log.error(f"[NBI/SIL Options CB AT] Erro: {e}")
    if classe_bt is not None:
        try:
            valores_bt = tabela_nbr.get_nbi_sil_values(classe_bt)
            nbi_bt_options = values_to_options(valores_bt["nbi"])
            sil_bt_options = values_to_options(valores_bt["sil"])
        except Exception as e: log.error(f"[NBI/SIL Options CB BT] Erro: {e}")
    if classe_terciario is not None:
        try:
            valores_terciario = tabela_nbr.get_nbi_sil_values(classe_terciario)
            nbi_terciario_options = values_to_options(valores_terciario["nbi"])
            sil_terciario_options = values_to_options(valores_terciario["sil"])
        except Exception as e: log.error(f"[NBI/SIL Options CB Ter] Erro: {e}")
    return [nbi_at_options, sil_at_options, nbi_bt_options, sil_bt_options, nbi_terciario_options, sil_terciario_options]

# --- Callback para atualizar os valores dos dropdowns NBI/SIL ---
@callback(
    [
        Output("nbi_at", "value"), Output("sil_at", "value"),
        Output("nbi_bt", "value"), Output("sil_bt", "value"),
        Output("nbi_terciario", "value"), Output("sil_terciario", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True)
    ],
    [
        Input("nbi_at", "options"), Input("sil_at", "options"),
        Input("nbi_bt", "options"), Input("sil_bt", "options"),
        Input("nbi_terciario", "options"), Input("sil_terciario", "options")
    ],
    [
        State("transformer-inputs-store", "data"),
        State("nbi_at", "value"), State("sil_at", "value"),
        State("nbi_bt", "value"), State("sil_bt", "value"),
        State("nbi_terciario", "value"), State("sil_terciario", "value")
    ],
    prevent_initial_call=True
)
def update_nbi_sil_values(nbi_at_opts, sil_at_opts, nbi_bt_opts, sil_bt_opts, nbi_ter_opts, sil_ter_opts,
                         current_store_data_state, # Este é o State do store, usado para obter dados do MCP
                         nbi_at_val, sil_at_val, nbi_bt_val, sil_bt_val, nbi_ter_val, sil_ter_val):
    if app.mcp is None:
        log.error("[NBI/SIL Values CB] MCP não inicializado.")
        return [no_update] * 7

    # Obter dados atuais do MCP em vez de usar current_store_data_state diretamente
    mcp_data = app.mcp.get_data('transformer-inputs-store')
    if not mcp_data: # Se o MCP estiver vazio, inicialize com defaults para evitar erros
        mcp_data = DEFAULT_TRANSFORMER_INPUTS.copy()

    stored_nbi_at = mcp_data.get('nbi_at'); stored_sil_at = mcp_data.get('sil_at')
    stored_nbi_bt = mcp_data.get('nbi_bt'); stored_sil_bt = mcp_data.get('sil_bt')
    stored_nbi_ter = mcp_data.get('nbi_terciario'); stored_sil_ter = mcp_data.get('sil_terciario')

    def get_valid_value(target, current, options):
        if not options: return None
        opt_vals = [o['value'] for o in options]
        if target is not None and target in opt_vals: return target
        if current is not None and current in opt_vals: return current
        return options[0]['value'] if options else None

    new_nbi_at = get_valid_value(stored_nbi_at, nbi_at_val, nbi_at_opts)
    new_sil_at = get_valid_value(stored_sil_at, sil_at_val, sil_at_opts)
    new_nbi_bt = get_valid_value(stored_nbi_bt, nbi_bt_val, nbi_bt_opts)
    new_sil_bt = get_valid_value(stored_sil_bt, sil_bt_val, sil_bt_opts)
    new_nbi_ter = get_valid_value(stored_nbi_ter, nbi_ter_val, nbi_ter_opts)
    new_sil_ter = get_valid_value(stored_sil_ter, sil_ter_val, sil_ter_opts)

    # Verifica se houve alguma mudança real nos valores que serão atualizados na UI
    ui_changed = not (new_nbi_at == nbi_at_val and new_sil_at == sil_at_val and
                      new_nbi_bt == nbi_bt_val and new_sil_bt == sil_bt_val and
                      new_nbi_ter == nbi_ter_val and new_sil_ter == sil_ter_val)

    # Verifica se os dados no MCP precisam ser atualizados
    mcp_needs_update = (new_nbi_at != stored_nbi_at or new_sil_at != stored_sil_at or
                        new_nbi_bt != stored_nbi_bt or new_sil_bt != stored_sil_bt or
                        new_nbi_ter != stored_nbi_ter or new_sil_ter != stored_sil_ter)

    if not ui_changed and not mcp_needs_update:
        return [no_update] * 7

    updated_mcp_data = mcp_data.copy()
    updated_mcp_data.update({
        'nbi_at': new_nbi_at, 'sil_at': new_sil_at,
        'nbi_bt': new_nbi_bt, 'sil_bt': new_sil_bt,
        'nbi_terciario': new_nbi_ter, 'sil_terciario': new_sil_ter
    })

    app.mcp.set_data('transformer-inputs-store', updated_mcp_data)
    # O store será atualizado com os dados do MCP
    final_mcp_data_for_store = app.mcp.get_data('transformer-inputs-store')

    log.debug(f"[NBI/SIL Values CB] NBI/SIL atualizados no MCP e retornados para UI/Store.")
    return [new_nbi_at, new_sil_at, new_nbi_bt, new_sil_bt, new_nbi_ter, new_sil_ter, final_mcp_data_for_store]

# --- Callback para preencher os dropdowns de NBI Neutro ---
@callback(
    [
        Output("nbi_neutro_at", "options"), Output("nbi_neutro_bt", "options"), Output("nbi_neutro_terciario", "options")
    ],
    [
        Input("tensao_bucha_neutro_at", "value"), Input("tensao_bucha_neutro_bt", "value"), Input("tensao_bucha_neutro_terciario", "value")
    ],
    prevent_initial_call=False
)
def update_nbi_neutro_options(classe_neutro_at, classe_neutro_bt, classe_neutro_terciario):
    def values_to_options(values):
        return [{'label': str(v), 'value': v} for v in values] if values else []
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
    return [nbi_neutro_at_options, nbi_neutro_bt_options, nbi_neutro_terciario_options]

# --- Callback para atualizar os valores dos dropdowns NBI Neutro ---
@callback(
    [
        Output("nbi_neutro_at", "value"), Output("nbi_neutro_bt", "value"), Output("nbi_neutro_terciario", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True)
    ],
    [
        Input("nbi_neutro_at", "options"), Input("nbi_neutro_bt", "options"), Input("nbi_neutro_terciario", "options")
    ],
    [
        State("transformer-inputs-store", "data"),
        State("nbi_neutro_at", "value"), State("nbi_neutro_bt", "value"), State("nbi_neutro_terciario", "value")
    ],
    prevent_initial_call=True
)
def update_nbi_neutro_values(nbi_n_at_opts, nbi_n_bt_opts, nbi_n_ter_opts,
                           current_store_data_state, # State do store, para obter dados do MCP
                           nbi_n_at_val, nbi_n_bt_val, nbi_n_ter_val):
    if app.mcp is None:
        log.error("[NBI Neutro Values CB] MCP não inicializado.")
        return [no_update] * 4

    mcp_data = app.mcp.get_data('transformer-inputs-store')
    if not mcp_data:
        mcp_data = DEFAULT_TRANSFORMER_INPUTS.copy()

    stored_nbi_n_at = mcp_data.get('nbi_neutro_at')
    stored_nbi_n_bt = mcp_data.get('nbi_neutro_bt')
    stored_nbi_n_ter = mcp_data.get('nbi_neutro_terciario')

    def get_valid_value(target, current, options):
        if not options: return None
        opt_vals = [o['value'] for o in options]
        if target is not None and target in opt_vals: return target
        if current is not None and current in opt_vals: return current
        return options[0]['value'] if options else None

    new_nbi_n_at = get_valid_value(stored_nbi_n_at, nbi_n_at_val, nbi_n_at_opts)
    new_nbi_n_bt = get_valid_value(stored_nbi_n_bt, nbi_n_bt_val, nbi_n_bt_opts)
    new_nbi_n_ter = get_valid_value(stored_nbi_n_ter, nbi_n_ter_val, nbi_n_ter_opts)

    ui_changed = not (new_nbi_n_at == nbi_n_at_val and
                      new_nbi_n_bt == nbi_n_bt_val and
                      new_nbi_n_ter == nbi_n_ter_val)

    mcp_needs_update = (new_nbi_n_at != stored_nbi_n_at or
                        new_nbi_n_bt != stored_nbi_n_bt or
                        new_nbi_n_ter != stored_nbi_n_ter)

    if not ui_changed and not mcp_needs_update:
        return [no_update] * 4

    updated_mcp_data = mcp_data.copy()
    updated_mcp_data.update({
        'nbi_neutro_at': new_nbi_n_at,
        'nbi_neutro_bt': new_nbi_n_bt,
        'nbi_neutro_terciario': new_nbi_n_ter
    })

    app.mcp.set_data('transformer-inputs-store', updated_mcp_data)
    final_mcp_data_for_store = app.mcp.get_data('transformer-inputs-store')

    log.debug(f"[NBI Neutro Values CB] NBI Neutro atualizados no MCP e retornados para UI/Store.")
    return [new_nbi_n_at, new_nbi_n_bt, new_nbi_n_ter, final_mcp_data_for_store]

# --- Callback para preencher os dropdowns de Tensão Aplicada ---
@callback(
    [
        Output("teste_tensao_aplicada_at", "options"), Output("teste_tensao_aplicada_bt", "options"), Output("teste_tensao_aplicada_terciario", "options")
    ],
    [
        Input("classe_tensao_at", "value"), Input("classe_tensao_bt", "value"), Input("classe_tensao_terciario", "value"),
        Input("tensao_bucha_neutro_at", "value"), Input("tensao_bucha_neutro_bt", "value"), Input("tensao_bucha_neutro_terciario", "value"),
        Input("conexao_at", "value"), Input("conexao_bt", "value"), Input("conexao_terciario", "value")
    ],
    prevent_initial_call=False
)
def update_tensao_aplicada_options(classe_at, classe_bt, classe_ter,
                                  tn_neutro_at, tn_neutro_bt, tn_neutro_ter,
                                  con_at, con_bt, con_ter):
    def values_to_options(values):
        return [{'label': f"{v} kV", 'value': v} for v in values] if values else []
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
            if conexao == 'estrela' and tn_neutro is not None:
                tn_neutro_f = safe_float(tn_neutro)
                if tn_neutro_f is not None:
                    return values_to_options(tabela_nbr.get_tensao_aplicada_values(tn_neutro_f))
            return values_to_options(tabela_nbr.get_tensao_aplicada_values(classe_f))
        except Exception as e:
            log.error(f"[Tensão Aplicada Options CB] Erro: {e}")
            return []

    tap_at_opts = get_options_for_winding(classe_at, tn_neutro_at, con_at)
    tap_bt_opts = get_options_for_winding(classe_bt, tn_neutro_bt, con_bt)
    tap_ter_opts = get_options_for_winding(classe_ter, tn_neutro_ter, con_ter)

    return [tap_at_opts, tap_bt_opts, tap_ter_opts]

# --- Callback para atualizar os valores dos dropdowns de Tensão Aplicada ---
@callback(
    [
        Output("teste_tensao_aplicada_at", "value"), Output("teste_tensao_aplicada_bt", "value"), Output("teste_tensao_aplicada_terciario", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True)
    ],
    [
        Input("teste_tensao_aplicada_at", "options"), Input("teste_tensao_aplicada_bt", "options"), Input("teste_tensao_aplicada_terciario", "options")
    ],
    [
        State("transformer-inputs-store", "data"),
        State("teste_tensao_aplicada_at", "value"), State("teste_tensao_aplicada_bt", "value"), State("teste_tensao_aplicada_terciario", "value")
    ],
    prevent_initial_call=True
)
def update_tensao_aplicada_values(tap_at_opts, tap_bt_opts, tap_ter_opts,
                                current_store_data_state, # State do store
                                tap_at_val, tap_bt_val, tap_ter_val):
    if app.mcp is None:
        log.error("[Tensao Aplicada Values CB] MCP não inicializado.")
        return [no_update] * 4

    mcp_data = app.mcp.get_data('transformer-inputs-store')
    if not mcp_data:
        mcp_data = DEFAULT_TRANSFORMER_INPUTS.copy()

    stored_tap_at = mcp_data.get('teste_tensao_aplicada_at')
    stored_tap_bt = mcp_data.get('teste_tensao_aplicada_bt')
    stored_tap_ter = mcp_data.get('teste_tensao_aplicada_terciario')

    def get_valid_value(target, current, options):
        if not options: return None
        opt_vals = [o['value'] for o in options]
        if target is not None and target in opt_vals: return target
        if current is not None and current in opt_vals: return current
        return options[0]['value'] if options else None

    new_tap_at = get_valid_value(stored_tap_at, tap_at_val, tap_at_opts)
    new_tap_bt = get_valid_value(stored_tap_bt, tap_bt_val, tap_bt_opts)
    new_tap_ter = get_valid_value(stored_tap_ter, tap_ter_val, tap_ter_opts)

    ui_changed = not (new_tap_at == tap_at_val and
                      new_tap_bt == tap_bt_val and
                      new_tap_ter == tap_ter_val)

    mcp_needs_update = (new_tap_at != stored_tap_at or
                        new_tap_bt != stored_tap_bt or
                        new_tap_ter != stored_tap_ter)

    if not ui_changed and not mcp_needs_update:
        return [no_update] * 4

    updated_mcp_data = mcp_data.copy()
    updated_mcp_data.update({
        'teste_tensao_aplicada_at': new_tap_at,
        'teste_tensao_aplicada_bt': new_tap_bt,
        'teste_tensao_aplicada_terciario': new_tap_ter
    })

    app.mcp.set_data('transformer-inputs-store', updated_mcp_data)
    final_mcp_data_for_store = app.mcp.get_data('transformer-inputs-store')

    log.debug(f"[Tensao Aplicada Values CB] Valores atualizados no MCP e retornados para UI/Store.")
    return [new_tap_at, new_tap_bt, new_tap_ter, final_mcp_data_for_store]

# --- Callback para preencher o dropdown de Tensão Induzida ---
@callback(
    Output("teste_tensao_induzida", "options"),
    Input("classe_tensao_at", "value"),
    prevent_initial_call=False
)
def update_tensao_induzida_options(classe_at):
    def values_to_options(values):
        return [{'label': f"{v} kV", 'value': v} for v in values] if values else []
    tensao_induzida_options = []
    if classe_at is not None:
        try: tensao_induzida_options = values_to_options(tabela_nbr.get_tensao_induzida_values(classe_at))
        except Exception as e: log.error(f"[Tensão Induzida Options CB] Erro: {e}")
    return tensao_induzida_options

# --- Callback para atualizar o valor do dropdown de Tensão Induzida ---
@callback(
    [
        Output("teste_tensao_induzida", "value"),
        Output("transformer-inputs-store", "data", allow_duplicate=True)
    ],
    Input("teste_tensao_induzida", "options"),
    [
        State("transformer-inputs-store", "data"),
        State("teste_tensao_induzida", "value")
    ],
    prevent_initial_call=True
)
def update_tensao_induzida_value(ti_opts, current_store_data_state, ti_val):
    if app.mcp is None:
        log.error("[Tensao Induzida Value CB] MCP não inicializado.")
        return [no_update, no_update]

    mcp_data = app.mcp.get_data('transformer-inputs-store')
    if not mcp_data:
        mcp_data = DEFAULT_TRANSFORMER_INPUTS.copy()

    stored_ti = mcp_data.get('teste_tensao_induzida')

    def get_valid_value(target, current, options):
        if not options: return None
        opt_vals = [o['value'] for o in options]
        if target is not None and target in opt_vals: return target
        if current is not None and current in opt_vals: return current
        return options[0]['value'] if options else None

    new_ti = get_valid_value(stored_ti, ti_val, ti_opts)

    ui_changed = new_ti != ti_val
    mcp_needs_update = new_ti != stored_ti

    if not ui_changed and not mcp_needs_update:
        return [no_update, no_update]

    updated_mcp_data = mcp_data.copy()
    updated_mcp_data['teste_tensao_induzida'] = new_ti

    app.mcp.set_data('transformer-inputs-store', updated_mcp_data)
    final_mcp_data_for_store = app.mcp.get_data('transformer-inputs-store')

    log.debug(f"[Tensao Induzida Value CB] Valor atualizado no MCP e retornado para UI/Store.")
    return [new_ti, final_mcp_data_for_store]


# --- Callback para carregar dados iniciais do store ---
# Adicionadas saídas para os valores de conexão e classe de neutro
@callback(
    [
        # Correntes (5)
        Output("corrente_nominal_at", "value", allow_duplicate=True),
        Output("corrente_nominal_at_tap_maior", "value", allow_duplicate=True),
        Output("corrente_nominal_at_tap_menor", "value", allow_duplicate=True),
        Output("corrente_nominal_bt", "value", allow_duplicate=True),
        Output("corrente_nominal_terciario", "value", allow_duplicate=True),
        # Estilos Visibilidade (12)
        Output("tensao_bucha_neutro_at_col", "style", allow_duplicate=True),
        Output("tensao_bucha_neutro_bt_col", "style", allow_duplicate=True),
        Output("tensao_bucha_neutro_terciario_col", "style", allow_duplicate=True),
        Output("nbi_neutro_at_col", "style", allow_duplicate=True),
        Output("nbi_neutro_bt_col", "style", allow_duplicate=True),
        Output("nbi_neutro_terciario_col", "style", allow_duplicate=True),
        Output("sil_at_col", "style", allow_duplicate=True),
        Output("sil_bt_col", "style", allow_duplicate=True),
        Output("sil_terciario_col", "style", allow_duplicate=True),
        Output("conexao_at_col", "style", allow_duplicate=True), # Garantir que sempre seja visível
        Output("conexao_bt_col", "style", allow_duplicate=True), # Garantir que sempre seja visível
        Output("conexao_terciario_col", "style", allow_duplicate=True), # Garantir que sempre seja visível
        # Valores Dropdowns NBI/SIL (6)
        Output("nbi_at", "value", allow_duplicate=True),
        Output("nbi_bt", "value", allow_duplicate=True),
        Output("nbi_terciario", "value", allow_duplicate=True),
        Output("sil_at", "value", allow_duplicate=True),
        Output("sil_bt", "value", allow_duplicate=True),
        Output("sil_terciario", "value", allow_duplicate=True),
        # Valores Dropdowns NBI Neutro (3)
        Output("nbi_neutro_at", "value", allow_duplicate=True),
        Output("nbi_neutro_bt", "value", allow_duplicate=True),
        Output("nbi_neutro_terciario", "value", allow_duplicate=True),
        # Valores Dropdowns Tensões Ensaio (4)
        Output("teste_tensao_aplicada_at", "value", allow_duplicate=True),
        Output("teste_tensao_aplicada_bt", "value", allow_duplicate=True),
        Output("teste_tensao_aplicada_terciario", "value", allow_duplicate=True),
        Output("teste_tensao_induzida", "value", allow_duplicate=True),
        # Valores Conexão (3) - <<< NOVO
        Output("conexao_at", "value", allow_duplicate=True),
        Output("conexao_bt", "value", allow_duplicate=True),
        Output("conexao_terciario", "value", allow_duplicate=True),
        # Valores Classe Neutro (3) - <<< NOVO
        Output("tensao_bucha_neutro_at", "value", allow_duplicate=True),
        Output("tensao_bucha_neutro_bt", "value", allow_duplicate=True),
        Output("tensao_bucha_neutro_terciario", "value", allow_duplicate=True),
        # Total = 5 + 12 + 6 + 3 + 4 + 3 + 3 = 36 Outputs
    ],
    [Input("url", "pathname"), Input("transformer-inputs-store", "data")],
    prevent_initial_call=True
)
def load_current_values_from_store(pathname, store_data):
    """
    Carrega os valores dos componentes e atualiza a visibilidade dos campos de neutro/SIL.

    Usa o MCP para acessar os dados, evitando problemas com o store.
    """
    triggered_id = ctx.triggered_id
    log.info(f"[Load Callback] Disparado por: {triggered_id}")

    if app.mcp is None:
        log.error("[Load Callback] MCP não inicializado. Abortando.")
        raise PreventUpdate

    is_path_trigger = triggered_id == "url"
    if is_path_trigger:
        if pathname is None: raise PreventUpdate
        clean_path = pathname.strip('/')
        if clean_path != 'dados-basicos': raise PreventUpdate
        log.debug("[Load Callback] Carregando dados devido à mudança de URL para 'dados-basicos'.")
    # Se o trigger for o store, os dados já devem estar no MCP,
    # e este callback apenas re-renderiza a UI com base no estado do MCP.
    # O store_data como Input garante que o callback seja acionado quando o store muda.

    style_hidden = {'display': 'none'}
    style_visible = {'display': 'block'} # Usado para a maioria dos campos
    style_flex_visible = {'display': 'flex', 'alignItems': 'center'} # Para SIL

    # Obter dados do MCP
    transformer_data = app.mcp.get_data('transformer-inputs-store')
    if not transformer_data: # Se o MCP retornar vazio (ex: após clear_data ou erro)
        log.warning("[Load Callback] Dados do MCP para 'transformer-inputs-store' estão vazios. Usando defaults.")
        # Usar os defaults definidos no MCP para consistência
        transformer_data = DEFAULT_TRANSFORMER_INPUTS.copy()
        # Recalcular correntes e estilos com os defaults
        calculated_currents = app.mcp.calculate_nominal_currents(transformer_data)
        visibility_styles_mcp = app.mcp.calculate_visibility_styles(transformer_data)
    else:
        # Calcular correntes e estilos usando os métodos do MCP
        calculated_currents = app.mcp.calculate_nominal_currents(transformer_data)
        visibility_styles_mcp = app.mcp.calculate_visibility_styles(transformer_data)

    # Extrair valores do transformer_data (que veio do MCP)
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
    conexao_at_val = transformer_data.get('conexao_at', DEFAULT_TRANSFORMER_INPUTS.get('conexao_at'))
    conexao_bt_val = transformer_data.get('conexao_bt', DEFAULT_TRANSFORMER_INPUTS.get('conexao_bt'))
    conexao_terciario_val = transformer_data.get('conexao_terciario', DEFAULT_TRANSFORMER_INPUTS.get('conexao_terciario'))
    tensao_bucha_neutro_at = transformer_data.get('tensao_bucha_neutro_at')
    tensao_bucha_neutro_bt = transformer_data.get('tensao_bucha_neutro_bt')
    tensao_bucha_neutro_terciario = transformer_data.get('tensao_bucha_neutro_terciario')

    # Extrair correntes calculadas
    corrente_at = calculated_currents.get('corrente_nominal_at')
    corrente_at_tap_maior = calculated_currents.get('corrente_nominal_at_tap_maior')
    corrente_at_tap_menor = calculated_currents.get('corrente_nominal_at_tap_menor')
    corrente_bt = calculated_currents.get('corrente_nominal_bt')
    corrente_terciario = calculated_currents.get('corrente_nominal_terciario')

    # Extrair estilos de visibilidade do MCP
    # Os IDs dos componentes de coluna são:
    # tensao_bucha_neutro_at_col, nbi_neutro_at_col, sil_at_col, conexao_at_col (e para bt, terciario)
    # O MCP retorna estilos para: neutro_at_style, nbi_neutro_at_style, sil_at_style, conexao_at_style
    neutro_at_col_style = visibility_styles_mcp.get('neutro_at_style', style_hidden)
    neutro_bt_col_style = visibility_styles_mcp.get('neutro_bt_style', style_hidden)
    neutro_ter_col_style = visibility_styles_mcp.get('neutro_ter_style', style_hidden)
    nbi_neutro_at_col_style = visibility_styles_mcp.get('nbi_neutro_at_style', style_hidden)
    nbi_neutro_bt_col_style = visibility_styles_mcp.get('nbi_neutro_bt_style', style_hidden)
    nbi_neutro_ter_col_style = visibility_styles_mcp.get('nbi_neutro_ter_style', style_hidden)
    sil_at_col_style = visibility_styles_mcp.get('sil_at_style', style_hidden)
    sil_bt_col_style = visibility_styles_mcp.get('sil_bt_style', style_hidden)
    sil_terciario_col_style = visibility_styles_mcp.get('sil_terciario_style', style_hidden)
    # Conexões são sempre visíveis, mas o MCP pode fornecer o estilo correto
    conexao_at_col_style = visibility_styles_mcp.get('conexao_at_style', style_visible)
    conexao_bt_col_style = visibility_styles_mcp.get('conexao_bt_style', style_visible)
    conexao_terciario_col_style = visibility_styles_mcp.get('conexao_terciario_style', style_visible)

    log.info(f"[Load Callback] Dados do MCP carregados e processados para UI.")

    # Retorna todos os 36 valores na ordem correta dos Outputs
    return [
        # Correntes (5)
        corrente_at, corrente_at_tap_maior, corrente_at_tap_menor, corrente_bt, corrente_terciario,
        # Estilos Visibilidade (12)
        neutro_at_col_style, neutro_bt_col_style, neutro_ter_col_style,
        nbi_neutro_at_col_style, nbi_neutro_bt_col_style, nbi_neutro_ter_col_style,
        sil_at_col_style, sil_bt_col_style, sil_terciario_col_style,
        conexao_at_col_style, conexao_bt_col_style, conexao_terciario_col_style,
        # Valores Dropdowns NBI/SIL (6)
        nbi_at, nbi_bt, nbi_terciario, sil_at, sil_bt, sil_terciario,
        # Valores Dropdowns NBI Neutro (3)
        nbi_neutro_at, nbi_neutro_bt, nbi_neutro_terciario,
        # Valores Dropdowns Tensões Ensaio (4)
        teste_tensao_aplicada_at, teste_tensao_aplicada_bt, teste_tensao_aplicada_terciario, teste_tensao_induzida,
        # Valores Conexão (3)
        conexao_at_val, conexao_bt_val, conexao_terciario_val,
        # Valores Classe Neutro (3)
        tensao_bucha_neutro_at, tensao_bucha_neutro_bt, tensao_bucha_neutro_terciario
    ]


# --- Callback Principal: Calcula Correntes, Controla Visibilidade, Salva no Store ---
# A lista de Inputs e input_ids já contém os campos de conexão e neutro.
# A lógica de cálculo de correntes e visibilidade também já os considera.
# A atualização do store (`new_data.update(inputs_dict)`) já salva esses campos.
# Portanto, nenhuma mudança significativa é necessária aqui.
@callback(
    [ # Ordem dos Outputs: 5 Correntes + 12 Estilos + Store = 18 Outputs
     Output("corrente_nominal_at", "value"),
     Output("corrente_nominal_at_tap_maior", "value"),
     Output("corrente_nominal_at_tap_menor", "value"),
     Output("corrente_nominal_bt", "value"),
     Output("corrente_nominal_terciario", "value"),
     Output("conexao_at_col", "style"),
     Output("conexao_bt_col", "style"),
     Output("conexao_terciario_col", "style"),
     Output("tensao_bucha_neutro_at_col", "style"),
     Output("tensao_bucha_neutro_bt_col", "style"),
     Output("tensao_bucha_neutro_terciario_col", "style"),
     Output("nbi_neutro_at_col", "style"),
     Output("nbi_neutro_bt_col", "style"),
     Output("nbi_neutro_terciario_col", "style"),
     Output("sil_at_col", "style"),
     Output("sil_bt_col", "style"),
     Output("sil_terciario_col", "style"),
     Output("transformer-inputs-store", "data")],
    [Input(id, "value") for id in [ # 44 Inputs na ordem correta
        # Campos gerais (7)
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao",
        "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento",
        # Campos AT (12)
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia",
        "nbi_at", "sil_at",
        "tensao_at_tap_maior", "impedancia_tap_maior",
        "tensao_at_tap_menor", "impedancia_tap_menor",
        "teste_tensao_aplicada_at", "teste_tensao_induzida",
        # Campos BT (6)
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt",
        "teste_tensao_aplicada_bt",
        # Campos Terciário (6)
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario",
        "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        # Campos Conexão/Neutro (9)
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        # Campos Pesos (4)
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]],
    State("transformer-inputs-store", "data"),
    prevent_initial_call=True
)
def update_transformer_calculations_and_store(*args):
    """
    Calcula correntes nominais, controla visibilidade de campos
    e salva todos os dados básicos no dcc.Store quando qualquer input muda.

    Usa o MCP para acessar e atualizar os dados, evitando problemas com o store.
    """
    triggered_input = ctx.triggered_id
    log.debug(f"[Update Callback] Disparado por input: {triggered_input}")

    if app.mcp is None:
        log.error("[Update Callback] MCP não inicializado. Abortando.")
        return [no_update] * 18 # 17 UI Outputs + 1 Store Output

    # O último argumento é current_data (State do store), que não usaremos diretamente.
    # Em vez disso, obteremos os dados do MCP após atualizá-lo.
    *input_values, _ = args # Ignora o current_data do State

    input_ids = [ # 44 IDs na ordem correta dos Inputs
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao",
        "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia",
        "nbi_at", "sil_at",
        "tensao_at_tap_maior", "impedancia_tap_maior",
        "tensao_at_tap_menor", "impedancia_tap_menor",
        "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt",
        "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario",
        "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]
    inputs_dict = dict(zip(input_ids, input_values))
    log.debug(f"[Update Callback] Valores de entrada da UI: {inputs_dict}")

    try:
        # 1. Atualizar o MCP com os dados da UI
        # O método set_data do MCP já lida com a conversão de tipos numpy e deepcopy.
        # A validação pode ser ativada/desativada no MCP.
        app.mcp.set_data('transformer-inputs-store', inputs_dict)
        log.info("[Update Callback] MCP atualizado com dados da UI.")

        # 2. Obter os dados consolidados do MCP (que podem ter sido processados/validados)
        transformer_data_from_mcp = app.mcp.get_data('transformer-inputs-store')

        # 3. Calcular correntes usando o método do MCP
        calculated_currents = app.mcp.calculate_nominal_currents(transformer_data_from_mcp)
        corrente_nominal_at = calculated_currents.get('corrente_nominal_at')
        corr_at_maior = calculated_currents.get('corrente_nominal_at_tap_maior')
        corr_at_menor = calculated_currents.get('corrente_nominal_at_tap_menor')
        corrente_nominal_bt = calculated_currents.get('corrente_nominal_bt')
        corrente_nominal_terciario = calculated_currents.get('corrente_nominal_terciario')
        log.debug(f"[Update Callback] Correntes calculadas pelo MCP: {calculated_currents}")

        # 4. Calcular estilos de visibilidade usando o método do MCP
        visibility_styles_mcp = app.mcp.calculate_visibility_styles(transformer_data_from_mcp)
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
        log.debug(f"[Update Callback] Estilos de visibilidade calculados pelo MCP.")

        # O transformer_data_from_mcp já inclui os inputs originais e as correntes calculadas
        # se o método set_data ou calculate_nominal_currents os adicionar internamente.
        # Pela estrutura atual do MCP, calculate_nominal_currents retorna um dict separado.
        # O set_data apenas armazena. O get_data retorna o que foi armazenado.
        # Para o store, queremos salvar os inputs brutos e potencialmente os calculados.
        # O MCP.save_session salva o self._data, então é bom que self._data['transformer-inputs-store']
        # contenha tudo o que precisa ser persistido.
        # Vamos assumir que transformer_data_from_mcp é o que deve ir para o store.
        # Se o MCP não adicionar as correntes calculadas ao seu 'transformer-inputs-store' interno,
        # podemos precisar fazer isso aqui antes de retornar para o store.
        # No entanto, o MCP.set_data apenas armazena o que é passado.
        # O ideal é que o MCP gerencie a estrutura do seu 'transformer-inputs-store'.
        # Por agora, retornaremos transformer_data_from_mcp para o store.
        # Se as correntes não estiverem lá, o load_current_values_from_store as calculará.

    except Exception as e:
        log.error(f"[Update Callback] Erro: {e}", exc_info=True)
        # Retorna no_update para todos os 18 outputs (17 UI + 1 Store)
        return [no_update] * 18

    log.info(f"[Update Callback] Dados processados e prontos para UI e Store.")

    # Retorna valores e estilos calculados + dados para o store (18 outputs)
    return (
        corrente_nominal_at, corr_at_maior, corr_at_menor,
        corrente_nominal_bt, corrente_nominal_terciario,
        conexao_at_style, conexao_bt_style, conexao_terciario_style,
        neutro_at_style, neutro_bt_style, neutro_ter_style,
        nbi_neutro_at_style, nbi_neutro_bt_style, nbi_neutro_ter_style,
        sil_at_style, sil_bt_style, sil_terciario_style,
        transformer_data_from_mcp # Dados do MCP para o dcc.Store
    )


# --- Callback para Limpar Campos ---
# A lista de Outputs e os default_values/cleaned_data já incluem os campos
# de conexão e neutro. Os valores padrão no layout foram alterados para 'triangulo',
# mas a função de limpar manterá os defaults originais ('estrela', 'triangulo', ' ').
@callback(
    # 49 Outputs de valor + 1 Output de store = 50
    [Output(id, "value", allow_duplicate=True) for id in [
        # Campos Gerais (7)
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao",
        "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento",
        # Campos AT (12)
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia",
        "nbi_at", "sil_at",
        "tensao_at_tap_maior", "impedancia_tap_maior",
        "tensao_at_tap_menor", "impedancia_tap_menor",
        "teste_tensao_aplicada_at", "teste_tensao_induzida",
        # Campos BT (6)
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt",
        "teste_tensao_aplicada_bt",
        # Campos Terciário (6)
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario",
        "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        # Campos Conexão/Neutro (9)
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        # Campos Pesos (4)
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios",
        # Campos de Corrente Calculada (5)
        "corrente_nominal_at", "corrente_nominal_at_tap_maior", "corrente_nominal_at_tap_menor",
        "corrente_nominal_bt", "corrente_nominal_terciario"
    ]] +
    [Output("transformer-inputs-store", "data", allow_duplicate=True)],
    [Input("limpar-transformer-inputs", "n_clicks")],
    prevent_initial_call=True
)
def limpar_transformer_inputs_trigger(n_clicks):
    """
    Limpa todos os campos do formulário de dados básicos do transformador.

    Usa o MCP para limpar os dados, evitando problemas com o store.
    """
    if n_clicks is None or n_clicks == 0: raise PreventUpdate
    log.info(f"Callback limpar_transformer_inputs_trigger disparado (n_clicks={n_clicks})")

    if app.mcp is None:
        log.error("[Clear Callback] MCP não inicializado. Abortando.")
        # Retorna no_update para todos os 50 outputs
        return tuple([no_update] * 49 + [no_update])


    # 1. Limpar os dados no MCP para 'transformer-inputs-store'
    # O método clear_data do MCP deve resetar para DEFAULT_TRANSFORMER_INPUTS
    app.mcp.clear_data('transformer-inputs-store')
    log.info("[Clear Callback] Dados limpos no MCP para 'transformer-inputs-store'.")

    # 2. Obter os dados limpos do MCP
    cleaned_mcp_data = app.mcp.get_data('transformer-inputs-store')

    # 3. Obter os valores padrão para a UI a partir dos dados limpos do MCP
    # (ou usar os defaults definidos no MCP diretamente)
    default_ui_values = []
    input_ids_for_clear = [ # IDs dos campos da UI que precisam ser resetados (44 campos)
        "tipo_transformador", "potencia_mva", "frequencia", "grupo_ligacao",
        "liquido_isolante", "elevacao_oleo_topo", "tipo_isolamento",
        "tensao_at", "classe_tensao_at", "elevacao_enrol_at", "impedancia",
        "nbi_at", "sil_at",
        "tensao_at_tap_maior", "impedancia_tap_maior",
        "tensao_at_tap_menor", "impedancia_tap_menor",
        "teste_tensao_aplicada_at", "teste_tensao_induzida",
        "tensao_bt", "classe_tensao_bt", "elevacao_enrol_bt", "nbi_bt", "sil_bt",
        "teste_tensao_aplicada_bt",
        "tensao_terciario", "classe_tensao_terciario", "elevacao_enrol_terciario",
        "nbi_terciario", "sil_terciario", "teste_tensao_aplicada_terciario",
        "conexao_at", "conexao_bt", "conexao_terciario",
        "tensao_bucha_neutro_at", "tensao_bucha_neutro_bt", "tensao_bucha_neutro_terciario",
        "nbi_neutro_at", "nbi_neutro_bt", "nbi_neutro_terciario",
        "peso_total", "peso_parte_ativa", "peso_oleo", "peso_tanque_acessorios"
    ]
    for field_id in input_ids_for_clear:
        default_ui_values.append(cleaned_mcp_data.get(field_id, None)) # Pega do MCP ou None

    # 4. Calcular correntes com os dados limpos (devem ser None ou 0)
    calculated_currents_cleared = app.mcp.calculate_nominal_currents(cleaned_mcp_data)
    cleared_current_values = [
        calculated_currents_cleared.get('corrente_nominal_at'),
        calculated_currents_cleared.get('corrente_nominal_at_tap_maior'),
        calculated_currents_cleared.get('corrente_nominal_at_tap_menor'),
        calculated_currents_cleared.get('corrente_nominal_bt'),
        calculated_currents_cleared.get('corrente_nominal_terciario')
    ]

    # Combinar valores da UI e correntes calculadas para os Outputs
    all_output_values = default_ui_values + cleared_current_values

    log.info("[Clear Callback] Valores padrão para UI e correntes limpas preparados.")

    # Retorna os valores para os 49 campos da UI e os dados limpos do MCP para o store
    return tuple(all_output_values + [cleaned_mcp_data]) # 49 UI values + 1 store data

# Função para registrar callbacks explicitamente
def register_transformer_inputs_callbacks(app):
    """
    Registra os callbacks do módulo de transformer_inputs.
    Esta função é chamada por app.py para garantir que todos os callbacks sejam registrados.

    Args:
        app: A instância da aplicação Dash
    """
    log.info(f"Callbacks do módulo transformer_inputs já registrados via decoradores @dash.callback para app {app.title}.")
    # Nota: Os callbacks estão sendo refatorados para usar app.mcp.
