# utils/styles.py
"""
Centraliza todas as definições de estilo Python para a aplicação.
"""
import math

from utils.theme_colors import DARK_COLORS  # Importa as paletas

# --- Paleta de Cores ---
# Define o tema padrão (pode ser alterado dinamicamente se necessário)
COLORS = DARK_COLORS  # Usar DARK_COLORS como padrão inicial

# --- Tipografia ---
TYPOGRAPHY = {
    "title": {
        "fontSize": "1.1rem",  # Um pouco maior
        "fontWeight": "bold",
        "color": COLORS["text_light"],
        "letterSpacing": "0.04rem",
    },
    "card_header": {
        "fontSize": "0.9rem",
        "fontWeight": "bold",
        "color": COLORS["text_header"],  # Usar cor específica para header
        "letterSpacing": "0.03rem",
        "textTransform": "uppercase",  # Adicionado para padronizar
    },
    "section_title": {
        "fontSize": "0.8rem",  # Menor para menos destaque
        "fontWeight": "bold",
        "color": COLORS["text_light"],
        "backgroundColor": COLORS["primary"],  # Adicionado fundo
        "padding": "4px 8px",
        "borderRadius": "3px",
        "textAlign": "center",
        "marginBottom": "0.5rem",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.1)",
    },
    "label": {
        "fontSize": "0.75rem",
        "fontWeight": "500",
        "color": COLORS["text_light"],
        "marginBottom": "0.1rem",  # Pequena margem abaixo
        "display": "block",  # Garante que o label fique em cima
    },
    "input": {"fontSize": "0.75rem", "color": COLORS["text_light"]},
    "button": {
        "fontSize": "0.75rem",
        "fontWeight": "500",  # Um pouco menos bold que títulos
    },
    "small_text": {"fontSize": "0.7rem", "color": COLORS["text_muted"]},
    "error_text": {
        "fontSize": "0.7rem",
        "fontWeight": "bold",
        "color": COLORS["danger"],
        "marginTop": "0.5rem",
        "padding": "0.2rem",
        "backgroundColor": COLORS["fail_bg"],  # Adiciona fundo sutil
        "borderRadius": "3px",
    },
}

# --- Estilos de Componentes ---
COMPONENTS = {
    # Cards
    "card": {
        "backgroundColor": COLORS["background_card"],
        "border": f'1px solid {COLORS["border"]}',
        "borderRadius": "4px",
        "boxShadow": "0 2px 5px rgba(0,0,0,0.25)",  # Sombra mais pronunciada
        "marginBottom": "0.75rem",
        "overflow": "hidden",  # Garante que conteúdo arredondado não vaze
    },
    "card_header": {
        "backgroundColor": COLORS["background_card_header"],
        "color": COLORS["text_header"],
        "padding": "0.4rem 0.75rem",  # Padding ajustado
        "fontSize": TYPOGRAPHY["card_header"]["fontSize"],
        "fontWeight": TYPOGRAPHY["card_header"]["fontWeight"],
        "letterSpacing": TYPOGRAPHY["card_header"]["letterSpacing"],
        "textTransform": TYPOGRAPHY["card_header"]["textTransform"],
        "borderBottom": f'1px solid {COLORS["border_strong"]}',  # Borda mais forte
    },
    "card_body": {
        "padding": "0.75rem",  # Padding padrão para corpo
        "backgroundColor": COLORS["background_card"],
    },
    # Inputs & Dropdowns
    "input": {
        "backgroundColor": COLORS["background_input"],
        "color": COLORS["text_light"],
        "border": f'1px solid {COLORS["border"]}',
        "borderRadius": "3px",
        "height": "28px",  # Altura padrão aumentada
        "padding": "0.2rem 0.4rem",  # Padding ajustado
        "fontSize": "0.75rem",
    },
    "dropdown": {
        # Estilos base são aplicados via className="dash-dropdown-dark" ou CSS
        # Aqui definimos apenas a altura e tamanho da fonte se necessário override
        "height": "28px",
        "minHeight": "28px",
        "fontSize": "0.75rem",
        # Cores são definidas no CSS para lidar com estados (hover, selected)
    },
    "read_only": {
        "backgroundColor": COLORS["background_card_header"],  # Fundo mais escuro
        "color": COLORS["text_muted"],  # Texto atenuado
        "border": f'1px solid {COLORS["border"]}',
        "borderRadius": "3px",
        "height": "28px",
        "padding": "0.2rem 0.4rem",
        "fontSize": "0.75rem",
        "cursor": "default",  # Alterado de not-allowed para default
    },
    # Botões (Estilos base, cores via tipo abaixo)
    "button_base": {
        "borderRadius": "3px",
        "padding": "0.3rem 0.6rem",  # Padding padrão
        "fontSize": TYPOGRAPHY["button"]["fontSize"],
        "fontWeight": TYPOGRAPHY["button"]["fontWeight"],
        "border": "none",
        "cursor": "pointer",
        "transition": "background-color 0.2s ease",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.2)",
        "height": "28px",  # Altura padrão
        "display": "inline-flex",  # Para alinhar ícone e texto
        "alignItems": "center",
        "justifyContent": "center",
    },
    # Cores específicas dos botões
    "button_primary": {
        "backgroundColor": COLORS["primary"],
        "color": COLORS["text_header"],  # Texto branco para contraste
    },
    "button_secondary": {"backgroundColor": COLORS["secondary"], "color": COLORS["text_header"]},
    "button_success": {"backgroundColor": COLORS["success"], "color": COLORS["text_header"]},
    "button_danger": {"backgroundColor": COLORS["danger"], "color": COLORS["text_header"]},
    "button_warning": {
        "backgroundColor": COLORS["warning"],
        "color": COLORS["text_dark"],  # Texto escuro para contraste com amarelo
    },
    "button_info": {"backgroundColor": COLORS["info"], "color": COLORS["text_header"]},
    # Abas
    "tab": {
        "backgroundColor": COLORS["background_card_header"],
        "color": COLORS["text_muted"],  # Cor mais suave para inativa
        "border": f'1px solid {COLORS["border"]}',
        "borderBottom": "none",  # Remove borda inferior da inativa
        "borderRadius": "4px 4px 0 0",
        "padding": "0.3rem 0.6rem",
        "fontSize": "0.75rem",
        "marginRight": "2px",
        "fontWeight": "500",
    },
    "tab_selected": {
        "backgroundColor": COLORS["background_card"],  # Fundo do card para ativa
        "color": COLORS["accent"],  # Cor de destaque para ativa
        "border": f'1px solid {COLORS["border"]}',
        "borderBottom": f'2px solid {COLORS["accent"]}',  # Destaque inferior
        "borderRadius": "4px 4px 0 0",
        "padding": "0.3rem 0.6rem",
        "fontSize": "0.75rem",
        "marginRight": "2px",
        "fontWeight": "bold",  # Mais destaque para ativa
    },
    # Alertas
    "alert": {
        "fontSize": "0.75rem",
        "padding": "0.6rem 0.8rem",
        "marginBottom": "0.75rem",
        "borderRadius": "4px",
        "borderWidth": "1px",
        "borderStyle": "solid",
    },
    # Container principal
    "container": {
        "backgroundColor": COLORS["background_main"],
        "color": COLORS["text_light"],
        "padding": "0.5rem",  # Padding geral
        "minHeight": "calc(100vh - 120px)",  # Altura mínima considerando navbar/footer
    },
}

# --- Estilos de Tabela (Centralizados) ---
TABLE_STYLES = {
    "header_sm": {
        "backgroundColor": COLORS["background_header"],
        "color": COLORS["text_header"],
        "textAlign": "center",
        "fontSize": "0.7rem",  # Menor para SM
        "padding": "0.2rem 0.3rem",
        "fontWeight": "bold",
    },
    "header_md": {
        "backgroundColor": COLORS["background_header"],
        "color": COLORS["text_header"],
        "textAlign": "center",
        "fontSize": "0.75rem",  # Padrão MD
        "padding": "0.3rem 0.5rem",
        "fontWeight": "bold",
    },
    "param_sm": {
        "fontSize": "0.7rem",
        "padding": "0.2rem 0.3rem",
        "fontWeight": "500",  # Menos bold que header
        "textAlign": "left",
        "backgroundColor": COLORS["background_card_header"],  # Fundo sutilmente diferente
        "color": COLORS["text_light"],
        "borderRight": f'1px solid {COLORS["border"]}',  # Linha separadora
    },
    "param_md": {
        "fontSize": "0.75rem",
        "padding": "0.3rem 0.5rem",
        "fontWeight": "500",
        "textAlign": "left",
        "backgroundColor": COLORS["background_card_header"],
        "color": COLORS["text_light"],
        "borderRight": f'1px solid {COLORS["border"]}',
    },
    "value_sm": {
        "fontSize": "0.7rem",
        "padding": "0.2rem 0.3rem",
        "textAlign": "center",
        "color": COLORS["text_light"],
        "backgroundColor": COLORS["background_card"],  # Fundo padrão do card
    },
    "value_md": {
        "fontSize": "0.75rem",
        "padding": "0.3rem 0.5rem",
        "textAlign": "center",
        "color": COLORS["text_light"],
        "backgroundColor": COLORS["background_card"],
    },
    "status": {  # Estilo base para célula de status
        "fontSize": "0.7rem",
        "padding": "0.2rem 0.3rem",
        "textAlign": "center",
        "fontWeight": "bold",
        # Cores são aplicadas dinamicamente
    },
    "wrapper": {  # Para tabelas que precisam rolar horizontalmente
        "overflowX": "auto",
        "marginBottom": "0.5rem",
    },
}

# --- Estilos de Mensagem ---
MESSAGE_STYLES = {
    "placeholder": {
        "fontSize": "0.8rem",
        "color": COLORS["text_muted"],
        "textAlign": "center",
        "padding": "2rem 1rem",
        "fontStyle": "italic",
    },
    "error": {
        "fontSize": "0.75rem",
        "color": COLORS["danger"],
        "backgroundColor": COLORS["fail_bg"],
        "padding": "0.5rem",
        "borderRadius": "4px",
        "border": f'1px solid {COLORS["danger"]}',
        "marginTop": "0.5rem",
    },
}

# --- Espaçamento (Classes CSS são preferíveis, mas úteis para inline) ---
SPACING = {
    "row_margin": "mb-2",  # Margem padrão para linhas
    "row_gutter": "g-2",  # Espaçamento padrão entre colunas
    "col_padding": "px-1",  # Padding padrão para colunas
    "section_margin": "mb-3",  # Margem padrão para seções/cards
}

# --- Constantes Físicas (Incluídas aqui para centralização) ---
PI = math.pi
EPSILON_0 = 8.854187817e-12
MU_0 = 4 * PI * 1e-7
