# layouts/history.py
"""
Define o layout para a seção de Histórico de Sessões.
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
import logging

# Importar estilos padronizados
from layouts import COLORS, TYPOGRAPHY, COMPONENTS, SPACING

log = logging.getLogger(__name__)

def create_history_layout():
    """
    Cria o layout da página de histórico de sessões com estilo aprimorado.

    Returns:
        dash.html.Div: O layout completo da seção de Histórico
    """
    log.info("Criando layout de Histórico de Sessões (v2 - Aprimorado)")
    print("[DEBUG] Iniciando criação do layout de Histórico de Sessões (v2)")

    # <<< REMOVIDOS dcc.Store definidos aqui >>>
    # Os stores globais ('transformer-inputs-store', etc.)
    # JÁ ESTÃO definidos em components/global_stores.py e incluídos no layout principal
    # O store local 'history-temp-store' também deve ser definido globalmente.

    # Estilos locais (como antes)
    stats_card_style = {**COMPONENTS['card'], "padding": "0.75rem", "textAlign": "center", "boxShadow": "none", "border": "none", "backgroundColor": "transparent"}
    stats_icon_style = {"fontSize": "1.8rem", "marginBottom": "0.5rem"}
    stats_value_style = {"fontSize": "1.4rem", "fontWeight": "bold", "margin": "0", "color": COLORS['text_light']}
    stats_label_style = {"fontSize": "0.75rem", "margin": "0", "color": COLORS['text_muted']}
    table_header_style = {'backgroundColor': COLORS['background_card_header'], 'color': COLORS['text_header'], 'padding': '8px 12px', 'fontWeight': '600', 'textAlign': 'center', 'fontSize': '0.8rem', 'border': f'1px solid {COLORS["border"]}', 'borderBottomWidth': '2px'}
    table_cell_style = {'padding': '8px 12px', 'textAlign': 'center', 'fontSize': '0.75rem', 'verticalAlign': 'middle', 'color': COLORS['text_light']}
    action_button_style = {"fontSize": "0.7rem", "padding": "2px 6px", "margin": "0 2px", "minWidth": "60px"}

    layout = dbc.Container([
        # <<< ADICIONADOS STORES LOCAIS AQUI (se não definidos globalmente) >>>
        # É MELHOR defini-los em components/global_stores.py
        dcc.Store(id='history-temp-store', storage_type='memory'), # Temporário para carregar
        dcc.Store(id='delete-session-id-store', storage_type='memory'), # Para ID de exclusão

        # Divs ocultas para compatibilidade com o callback global_updates
        html.Div(html.Div(), id="transformer-info-losses", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-impulse", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-dieletric", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-applied", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-induced", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-short-circuit", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-temperature-rise", style={"display": "none"}),
        html.Div(html.Div(), id="transformer-info-comprehensive", style={"display": "none"}),

        # Título da Página (como antes)
        dbc.Row([dbc.Col(html.Div([html.I(className="fas fa-history me-2", style={"fontSize": "1.8rem", "color": COLORS['accent']}), html.H4("Histórico de Sessões", className="d-inline align-middle", style=TYPOGRAPHY['title'])], className="d-flex align-items-center"), width=12)], className=f"{SPACING['row_margin']} pt-2"),

        # Gerenciamento de Sessões (como antes)
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-tasks me-2"), "Gerenciar Sessões"], style={**COMPONENTS['card_header'], "textAlign": "left"}), dbc.CardBody([dbc.Row([dbc.Col(dbc.InputGroup([dbc.InputGroupText(html.I(className="fas fa-search"), style={"backgroundColor": COLORS['background_input'], "borderColor": COLORS['border']}), dbc.Input(id="search-input", placeholder="Filtrar por nome ou notas...", style=COMPONENTS['input']), dbc.Button("Buscar", id="search-button", color="primary", className="ms-2", style=COMPONENTS['button_primary'])]), md=7, lg=8, className="mb-2 mb-md-0"), dbc.Col(dbc.Button([html.I(className="fas fa-save me-2"), "Salvar Sessão Atual"], id="save-current-session-button", color="success", className="w-100", style=COMPONENTS['button_success']), md=5, lg=4)], align="center")], style=COMPONENTS['card_body'])], style=COMPONENTS['card']), width=12)], className=SPACING['row_margin']),

        # Estatísticas (como antes)
        dbc.Card([dbc.CardBody(dbc.Row([dbc.Col(html.Div([html.I(className="fas fa-database", style={**stats_icon_style, "color": COLORS['primary']}), html.Div([html.H5(id="stats-total-sessions", children="--", style=stats_value_style), html.P("Sessões Salvas", style=stats_label_style)])]), style=stats_card_style, md=4), dbc.Col(html.Div([html.I(className="far fa-clock", style={**stats_icon_style, "color": COLORS['info']}), html.Div([html.H5(id="stats-last-session", children="--", style=stats_value_style), html.P("Última Sessão Salva", style=stats_label_style)])]), style=stats_card_style, md=4), dbc.Col(html.Div([html.I(className="fas fa-file-alt", style={**stats_icon_style, "color": COLORS['accent']}), html.Div([html.H5(id="stats-current-session", children="Nova Sessão", style=stats_value_style), html.P("Sessão em Edição", style=stats_label_style)])]), style=stats_card_style, md=4)], className="g-0"))], style={**COMPONENTS['card'], "backgroundColor": COLORS['background_card_header'], "marginBottom": "1rem", "padding": "0.5rem"}),

        # Tabela de Sessões (como antes)
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-list-alt me-2"), "Sessões Armazenadas"], style=COMPONENTS['card_header']), dbc.CardBody([dcc.Loading(id="loading-history-table", type="circle", color=COLORS['primary'], children=[html.Div([html.Div([html.Div(html.Span([html.I(className="fas fa-calendar-alt me-1"), "Data/Hora"]), className="col-3", style=table_header_style), html.Div(html.Span([html.I(className="fas fa-tag me-1"), "Nome"]), className="col-4", style=table_header_style), html.Div(html.Span([html.I(className="fas fa-sticky-note me-1"), "Notas"]), className="col-3", style=table_header_style), html.Div(html.Span([html.I(className="fas fa-cogs me-1"), "Ações"]), className="col-2", style=table_header_style)], className="row g-0", style={'position': 'sticky', 'top': 0, 'zIndex': 1}), html.Div(id="history-table-body", className="history-table-body", style={'maxHeight': '45vh', 'overflowY': 'auto', 'border': f'1px solid {COLORS["border"]}', 'borderTop': 'none', 'borderRadius': '0 0 5px 5px', 'backgroundColor': COLORS['background_card']}), html.Div(id="no-sessions-message", className="text-center p-3", style={'display': 'none', 'color': COLORS['text_muted'], 'border': f'1px solid {COLORS["border"]}', 'borderTop': 'none', 'borderRadius': '0 0 5px 5px'}, children=[html.I(className="fas fa-info-circle me-2"), "Nenhuma sessão salva ainda."])], id="history-table", style={'width': '100%'})]), html.Div(id="history-message", className="mt-3", style={'minHeight': '40px'})], style=COMPONENTS['card_body'])], style=COMPONENTS['card']), width=12)], className=SPACING['row_margin']),

        # Dicas de Uso (como antes)
        dbc.Row([dbc.Col(dbc.Card([dbc.CardHeader([html.I(className="fas fa-question-circle me-2"), "Dicas de Uso"], style=COMPONENTS['card_header']), dbc.CardBody([dbc.Row([dbc.Col(html.Div([html.I(className="fas fa-save me-2", style={"color": COLORS['success'], "width": "16px"}), html.Strong("Salvar:"), " Guarda os dados da sessão atual com um nome único."]), md=6, className="mb-2"), dbc.Col(html.Div([html.I(className="fas fa-upload me-2", style={"color": COLORS['primary'], "width": "16px"}), html.Strong("Carregar:"), " Restaura os dados de uma sessão salva."]), md=6, className="mb-2"), dbc.Col(html.Div([html.I(className="fas fa-trash-alt me-2", style={"color": COLORS['danger'], "width": "16px"}), html.Strong("Excluir:"), " Remove permanentemente a sessão selecionada."]), md=6, className="mb-2"), dbc.Col(html.Div([html.I(className="fas fa-search me-2", style={"color": COLORS['info'], "width": "16px"}), html.Strong("Buscar:"), " Filtra a lista por nome ou notas."]), md=6, className="mb-2")])], style=COMPONENTS['card_body'])], style=COMPONENTS['card']), width=12)], className=SPACING['row_margin']),

        # Modais (como antes)
        dbc.Modal([dbc.ModalHeader("Salvar Sessão Atual", style={'backgroundColor': COLORS['background_card_header'], 'color': COLORS['text_header']}), dbc.ModalBody([dbc.Label("Nome da Sessão:", html_for="session-name-input", style=TYPOGRAPHY['label']), dbc.Input(id="session-name-input", placeholder="Identificador único para a sessão", type="text", className="mb-3", style=COMPONENTS['input']), dbc.Label("Notas (Opcional):", html_for="session-notes-input", style=TYPOGRAPHY['label']), dbc.Textarea(id="session-notes-input", placeholder="Detalhes sobre o teste, equipamento, etc.", style={**COMPONENTS['input'], 'height': '100px'}), html.Div([html.I(className="fas fa-exclamation-triangle me-1", style={"color": COLORS['warning']}), " Escolha um nome único. Nomes duplicados não são permitidos."], className="small mt-2", style={'color': COLORS['warning']})], style={'backgroundColor': COLORS['background_card'], 'color': COLORS['text_light']}), dbc.ModalFooter([dbc.Button("Cancelar", id="save-session-cancel", color="secondary", outline=True, style=COMPONENTS['button_secondary']), dbc.Button(html.Span([html.I(className="fas fa-save me-1"), "Salvar"]), id="save-session-confirm", color="success", style=COMPONENTS['button_success'])], style={'backgroundColor': COLORS['background_card_header'], 'borderTop': f'1px solid {COLORS["border"]}'})], id="save-session-modal", is_open=False, backdrop="static", centered=True),
        dbc.Modal([dbc.ModalHeader("Confirmar Exclusão", style={'backgroundColor': COLORS['background_card_header'], 'color': COLORS['text_header']}), dbc.ModalBody([html.P("Tem certeza que deseja excluir esta sessão?"), html.P("Esta ação não pode ser desfeita.", className="fw-bold", style={'color': COLORS['danger']})], style={'backgroundColor': COLORS['background_card'], 'color': COLORS['text_light']}), dbc.ModalFooter([dbc.Button("Cancelar", id="delete-session-cancel", color="secondary", outline=True, style=COMPONENTS['button_secondary']), dbc.Button(html.Span([html.I(className="fas fa-trash-alt me-1"), "Excluir"]), id="delete-session-confirm", color="danger", style=COMPONENTS['button_danger'])], style={'backgroundColor': COLORS['background_card_header'], 'borderTop': f'1px solid {COLORS["border"]}'})], id="delete-session-modal", is_open=False, backdrop="static", centered=True),

    ], fluid=True, style={"backgroundColor": COLORS['background_main'], "padding": "1rem", "color": COLORS['text_light'], "minHeight": "calc(100vh - 120px)"})

    print("[DEBUG] Layout de Histórico de Sessões (v2) criado com sucesso")
    return layout