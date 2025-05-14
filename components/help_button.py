"""
Componente de botão de ajuda para exibir documentação específica de cada módulo.
"""
import dash_bootstrap_components as dbc
from dash import html


def create_help_button(module_name, tooltip_text="Ajuda sobre este módulo"):
    """
    Cria um botão de ajuda que abre a documentação HTML específica do módulo
    em uma nova guia.

    Args:
        module_name (str): Nome do módulo (ex: 'perdas', 'induced_voltage')
        tooltip_text (str): Texto do tooltip ao passar o mouse sobre o botão

    Returns:
        html.Div: Componente do botão de ajuda como um link.
    """
    # Mapear nomes de módulos para nomes de arquivos HTML (sem a extensão .md)
    # O MkDocs gera arquivos .html com o mesmo nome base.
    module_to_html = {
        "perdas": "formulas_perdas",
        "induced_voltage": "formulas_induzida",
        "applied_voltage": "formulas_aplicada",
        "impulse": "formulas_impulso",
        "dielectric_analysis": "formulas_dieletrica",
        "short_circuit": "formulas_curto_circuito",
        "temperature_rise": "formulas_temperatura",
    }

    html_file_base = module_to_html.get(module_name)

    if not html_file_base:
        # Se o módulo não for encontrado, pode retornar um botão desabilitado ou nada
        return html.Div(
            dbc.Button(
                html.I(className="fas fa-question-circle"),
                color="secondary",
                outline=True,
                size="sm",
                disabled=True,
                style={
                    "borderRadius": "50%",
                    "width": "32px",
                    "height": "32px",
                    "padding": "4px 0px",
                    "marginLeft": "10px",
                },
            ),
            style={"display": "inline-block"},
        )

    # Construir a URL relativa para o arquivo HTML dentro de assets/help_docs
    # O Dash serve automaticamente o conteúdo da pasta 'assets'
    help_url = f"/assets/help_docs/{html_file_base}.html"

    # Usar um ID único para o tooltip, mesmo que seja um link
    tooltip_id = f"help-link-tooltip-{module_name}"

    # Criar um link estilizado como botão
    help_link = html.A(
        html.I(className="fas fa-question-circle", style={"color": "#FFFFFF"}),  # Ícone branco
        id=tooltip_id,  # ID para o tooltip
        href=help_url,
        target="_blank",  # Abre em nova guia
        className="btn btn-info btn-sm",  # Classes Bootstrap para aparência de botão
        style={
            "borderRadius": "50%",
            "width": "32px",
            "height": "32px",
            "padding": "4px 0px",  # Ajuste padding para centralizar ícone
            "marginLeft": "10px",
            "lineHeight": "1",  # Garante alinhamento vertical do ícone
            "textAlign": "center",
            "display": "inline-flex",  # Para centralizar ícone
            "alignItems": "center",
            "justifyContent": "center",
            "textDecoration": "none",  # Remove sublinhado do link
            "backgroundColor": "#17a2b8",  # Cor info explícita
            "borderColor": "#17a2b8",
        },
    )

    # Adicionar tooltip ao link
    tooltip = dbc.Tooltip(tooltip_text, target=tooltip_id, placement="top")

    # Envolver link e tooltip em um Div
    return html.Div(
        [help_link, tooltip], style={"display": "inline-block", "verticalAlign": "middle"}
    )
