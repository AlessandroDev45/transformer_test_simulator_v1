# components/transformer_info_template.py
# Nenhuma mudança necessária aqui, pois este componente apenas *exibe* os dados
# que já foram salvos no store pelos callbacks. Os campos de conexão e neutro
# já estão previstos na linha inferior opcional.
import logging

import dash_bootstrap_components as dbc
from dash import html

from utils.styles import COLORS

logger = logging.getLogger(__name__)


# --- Helper Function ---
def _create_info_item(label, value, unit="", label_style_override=None, value_style_override=None):
    """Cria um item de informação (label: valor unidade) compacto."""
    base_label_style = {
        "fontFamily": "var(--bs-body-font-family, Segoe UI, Arial, sans-serif)",
        "fontSize": "0.73125rem",  # Increased by 12.5% from 0.65rem
        "fontWeight": "normal",
        "color": COLORS["text_muted"],
        "whiteSpace": "nowrap",
        "lineHeight": "1.1",
        "display": "inline-block",
        "marginRight": "4px",  # Adicionado para espaço entre label e value
    }
    base_value_style = {
        "fontFamily": "var(--bs-body-font-family, Segoe UI, Arial, sans-serif)",
        "fontSize": "0.73125rem",  # Increased by 12.5% from 0.65rem
        "fontWeight": "600",
        "color": COLORS["text_light"],
        "lineHeight": "1.1",
        "display": "inline-block",
        "letterSpacing": "0.01rem",
    }
    final_label_style = {**base_label_style, **(label_style_override or {})}
    final_value_style = {**base_value_style, **(value_style_override or {})}
    if value is None or value == "" or str(value).upper() in ["NA", "N/A"]:
        display_value = "-"
    # Tratar especificamente conexões para exibir D, Yn, Y em vez de triangulo, estrela...
    elif label.lower() == "conexão:" and isinstance(value, str):
        if value == "triangulo":
            display_value = "D"
        elif value == "estrela":
            display_value = "Yn"
        elif value == "estrela_sem_neutro":
            display_value = "Y"
        elif value == " ":
            display_value = "-"  # Terciário vazio
        else:
            display_value = value  # Caso inesperado
    else:
        display_value = value

    # Remove colon from label if it exists
    if label and label.endswith(':'):
        label = label[:-1]

    formatted_label = label[0].upper() + label[1:] if label and len(label) > 0 else label
    content = [
        html.Span(f"{formatted_label} ", style=final_label_style),  # Space without colon
        html.Span(f"{display_value} {unit}".strip(), style=final_value_style),  # No leading space
    ]
    div_style = {
        "marginBottom": "3px",
        "lineHeight": "1.2",
        "padding": "0 2px",
        "borderBottom": f"1px solid {COLORS['border']}",
        "textAlign": "left",
        "width": "100%",
    }  # Mudado para textAlign left
    return html.Div(content, style=div_style)


def create_transformer_info_panel(transformer_data):
    """Cria um painel de informações do transformador compacto com estrutura de 2+1 linhas."""
    if not isinstance(transformer_data, dict) or not transformer_data:
        logger.warning(f"transformer_data inválido ou vazio: {transformer_data}")
        return html.Div(
            "Dados do transformador não disponíveis ou inválidos.",
            style={
                "fontSize": "0.7rem",
                "color": COLORS["danger"],
                "padding": "10px",
                "border": f"1px solid {COLORS['danger']}",
                "borderRadius": "4px",
                "backgroundColor": COLORS["background_card"],
            },
        )

    col_base_style = {
        "padding": "4px 6px",
        "overflow": "hidden",
        "backgroundColor": COLORS["background_card"],
    }
    col_style_with_border = {
        **col_base_style,
        "borderRight": f"1px solid {COLORS['border']}",
        "boxShadow": "inset -1px 0 0 rgba(0,0,0,0.1)",
    }
    col_style_last = col_base_style
    title_style_base = {
        "fontSize": "0.68rem",
        "fontWeight": "bold",
        "color": COLORS["text_light"],
        "padding": "4px 4px",
        "borderRadius": "3px",
        "textAlign": "center",
        "marginBottom": "6px",
        "lineHeight": "1.2",
        "width": "100%",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.1)",
        "borderBottom": f"1px solid {COLORS['border']}",
        "letterSpacing": "0.02rem",
        "textTransform": "uppercase",
        "textShadow": "0px 1px 1px rgba(0,0,0,0.1)",
    }
    subtitle_style = {
        **title_style_base,
        "fontSize": "0.63rem",
        "fontWeight": "normal",
        "backgroundColor": COLORS["background_card_header"],
        "color": COLORS["text_muted"],
        "marginTop": "6px",
        "marginBottom": "4px",
        "boxShadow": "none",
        "borderTop": f"1px solid {COLORS['border']}",
        "borderBottom": f"1px solid {COLORS['border']}",
        "textTransform": "none",
        "textAlign": "center",
    }  # Centralizado subtitle

    bg_color_header = COLORS["background_card_header"]
    bg_color_tap = COLORS["primary"]
    bg_color_nominal = COLORS["info"]
    bg_color_default = COLORS["secondary"]

    try:
        # --- Linha Superior: Informações Básicas ---
        top_row_style = {
            "backgroundColor": bg_color_header,
            "color": COLORS["text_light"],
            "borderBottom": f"1px solid {COLORS['border']}",
            "fontSize": "0.65rem",
            "borderRadius": "3px 3px 0 0",
        }

        # Extrair valores principais para exibição e log
        potencia_valor = transformer_data.get("potencia_mva")
        frequencia_valor = transformer_data.get("frequencia")
        grupo_ligacao_valor = transformer_data.get("grupo_ligacao")
        tipo_isolamento_valor = transformer_data.get("tipo_isolamento")
        liquido_isolante_valor = transformer_data.get("liquido_isolante")

        # Valores de tensão
        tensao_at_valor = transformer_data.get("tensao_at")
        tensao_at_tap_maior_valor = transformer_data.get("tensao_at_tap_maior")
        tensao_at_tap_menor_valor = transformer_data.get("tensao_at_tap_menor")
        tensao_bt_valor = transformer_data.get("tensao_bt")
        tensao_terciario_valor = transformer_data.get("tensao_terciario")

        # Valores de classe de tensão
        classe_tensao_at_valor = transformer_data.get("classe_tensao_at")
        classe_tensao_bt_valor = transformer_data.get("classe_tensao_bt")
        classe_tensao_terciario_valor = transformer_data.get("classe_tensao_terciario")

        # Valores de corrente
        corrente_at_valor = transformer_data.get("corrente_nominal_at")
        corrente_at_tap_maior_valor = transformer_data.get("corrente_nominal_at_tap_maior")
        corrente_at_tap_menor_valor = transformer_data.get("corrente_nominal_at_tap_menor")
        corrente_bt_valor = transformer_data.get("corrente_nominal_bt")
        corrente_terciario_valor = transformer_data.get("corrente_nominal_terciario")

        # Valores de impedância
        impedancia_valor = transformer_data.get("impedancia")
        impedancia_tap_maior_valor = transformer_data.get("impedancia_tap_maior")
        impedancia_tap_menor_valor = transformer_data.get("impedancia_tap_menor")

        # Valores de conexão
        conexao_at_valor = transformer_data.get("conexao_at")
        conexao_bt_valor = transformer_data.get("conexao_bt")
        conexao_terciario_valor = transformer_data.get("conexao_terciario")

        # Valores de neutro
        tensao_bucha_neutro_at_valor = transformer_data.get("tensao_bucha_neutro_at")
        tensao_bucha_neutro_bt_valor = transformer_data.get("tensao_bucha_neutro_bt")
        tensao_bucha_neutro_terciario_valor = transformer_data.get("tensao_bucha_neutro_terciario")

        # Valores de NBI e SIL
        nbi_at_valor = transformer_data.get("nbi_at")
        sil_at_valor = transformer_data.get("sil_at")
        nbi_neutro_at_valor = transformer_data.get("nbi_neutro_at")
        sil_neutro_at_valor = transformer_data.get("sil_neutro_at")

        nbi_bt_valor = transformer_data.get("nbi_bt")
        sil_bt_valor = transformer_data.get("sil_bt")
        nbi_neutro_bt_valor = transformer_data.get("nbi_neutro_bt")
        sil_neutro_bt_valor = transformer_data.get("sil_neutro_bt")

        nbi_terciario_valor = transformer_data.get("nbi_terciario")
        sil_terciario_valor = transformer_data.get("sil_terciario")
        nbi_neutro_terciario_valor = transformer_data.get("nbi_neutro_terciario")
        sil_neutro_terciario_valor = transformer_data.get("sil_neutro_terciario")

        # Valores de tensão de ensaio
        teste_tensao_aplicada_at_valor = transformer_data.get("teste_tensao_aplicada_at")
        teste_tensao_aplicada_bt_valor = transformer_data.get("teste_tensao_aplicada_bt")
        teste_tensao_aplicada_terciario_valor = transformer_data.get("teste_tensao_aplicada_terciario")
        teste_tensao_induzida_valor = transformer_data.get("teste_tensao_induzida")

        # Valores de elevação de temperatura
        elevacao_oleo_topo_valor = transformer_data.get("elevacao_oleo_topo")
        elevacao_enrol_valor = transformer_data.get("elevacao_enrol")
        elevacao_enrol_at_valor = transformer_data.get("elevacao_enrol_at")
        elevacao_enrol_bt_valor = transformer_data.get("elevacao_enrol_bt")
        elevacao_enrol_terciario_valor = transformer_data.get("elevacao_enrol_terciario")

        # Valores de peso
        peso_total_valor = transformer_data.get("peso_total")
        peso_parte_ativa_valor = transformer_data.get("peso_parte_ativa")
        peso_oleo_valor = transformer_data.get("peso_oleo")
        peso_tanque_acessorios_valor = transformer_data.get("peso_tanque_acessorios")

        # Outros valores
        norma_valor = transformer_data.get("norma_iso")
        tipo_transformador = transformer_data.get("tipo_transformador")

        # Log detalhado dos valores principais
        logger.info("=================== DADOS DO TRANSFORMADOR NO PAINEL ===================")
        logger.info(f"POTÊNCIA: {potencia_valor} MVA")
        logger.info(f"TIPO: {tipo_transformador}")
        logger.info(f"FREQUÊNCIA: {frequencia_valor} Hz")
        logger.info(f"GRUPO DE LIGAÇÃO: {grupo_ligacao_valor}")
        logger.info(f"TIPO DE ISOLAMENTO: {tipo_isolamento_valor}")
        logger.info(f"LÍQUIDO ISOLANTE: {liquido_isolante_valor}")
        logger.info(f"NORMA: {norma_valor}")

        # Log detalhado das tensões
        logger.info("TENSÕES:")
        logger.info("  AT:")
        logger.info(f"    - Tap Nominal: {tensao_at_valor} kV")
        logger.info(f"    - Tap Maior: {tensao_at_tap_maior_valor} kV")
        logger.info(f"    - Tap Menor: {tensao_at_tap_menor_valor} kV")
        logger.info(f"    - Classe de Tensão: {classe_tensao_at_valor} kV")
        logger.info(f"  BT: {tensao_bt_valor} kV (Classe: {classe_tensao_bt_valor} kV)")
        logger.info(f"  TERCIÁRIO: {tensao_terciario_valor} kV (Classe: {classe_tensao_terciario_valor} kV)")

        # Log detalhado das correntes
        logger.info("CORRENTES:")
        logger.info("  AT:")
        logger.info(f"    - Tap Nominal: {corrente_at_valor} A")
        logger.info(f"    - Tap Maior: {corrente_at_tap_maior_valor} A")
        logger.info(f"    - Tap Menor: {corrente_at_tap_menor_valor} A")
        logger.info(f"  BT: {corrente_bt_valor} A")
        logger.info(f"  TERCIÁRIO: {corrente_terciario_valor} A")

        # Log detalhado das impedâncias
        logger.info("IMPEDÂNCIAS:")
        logger.info(f"  - Nominal: {impedancia_valor} %")
        logger.info(f"  - Tap Maior: {impedancia_tap_maior_valor} %")
        logger.info(f"  - Tap Menor: {impedancia_tap_menor_valor} %")

        # Log detalhado das conexões
        logger.info("CONEXÕES:")
        logger.info(f"  - AT: {conexao_at_valor}")
        logger.info(f"  - BT: {conexao_bt_valor}")
        logger.info(f"  - TERCIÁRIO: {conexao_terciario_valor}")

        # Log detalhado dos neutros
        logger.info("NEUTROS:")
        logger.info(f"  - AT: Classe {tensao_bucha_neutro_at_valor} kV")
        logger.info(f"  - BT: Classe {tensao_bucha_neutro_bt_valor} kV")
        logger.info(f"  - TERCIÁRIO: Classe {tensao_bucha_neutro_terciario_valor} kV")

        # Log detalhado dos níveis de isolamento
        logger.info("NÍVEIS DE ISOLAMENTO:")
        logger.info("  AT:")
        logger.info(f"    - NBI: {nbi_at_valor} kVp")
        logger.info(f"    - SIL/IM: {sil_at_valor} kVp")
        logger.info(f"    - NBI Neutro: {nbi_neutro_at_valor} kVp")
        logger.info(f"    - SIL/IM Neutro: {sil_neutro_at_valor} kVp")
        logger.info("  BT:")
        logger.info(f"    - NBI: {nbi_bt_valor} kVp")
        logger.info(f"    - SIL/IM: {sil_bt_valor} kVp")
        logger.info(f"    - NBI Neutro: {nbi_neutro_bt_valor} kVp")
        logger.info(f"    - SIL/IM Neutro: {sil_neutro_bt_valor} kVp")
        logger.info("  TERCIÁRIO:")
        logger.info(f"    - NBI: {nbi_terciario_valor} kVp")
        logger.info(f"    - SIL/IM: {sil_terciario_valor} kVp")
        logger.info(f"    - NBI Neutro: {nbi_neutro_terciario_valor} kVp")
        logger.info(f"    - SIL/IM Neutro: {sil_neutro_terciario_valor} kVp")

        # Log detalhado das tensões de ensaio
        logger.info("TENSÕES DE ENSAIO:")
        logger.info("  APLICADA:")
        logger.info(f"    - AT: {teste_tensao_aplicada_at_valor} kV")
        logger.info(f"    - BT: {teste_tensao_aplicada_bt_valor} kV")
        logger.info(f"    - TERCIÁRIO: {teste_tensao_aplicada_terciario_valor} kV")
        logger.info("  INDUZIDA:")
        logger.info(f"    - AT: {teste_tensao_induzida_valor} kV")

        # Log detalhado das elevações de temperatura
        logger.info("ELEVAÇÕES DE TEMPERATURA:")
        logger.info(f"  - Óleo Topo: {elevacao_oleo_topo_valor} °C")
        logger.info(f"  - Enrolamento (Geral): {elevacao_enrol_valor} °C")
        logger.info(f"  - AT: {elevacao_enrol_at_valor} °C")
        logger.info(f"  - BT: {elevacao_enrol_bt_valor} °C")
        logger.info(f"  - TERCIÁRIO: {elevacao_enrol_terciario_valor} °C")

        # Log detalhado dos pesos
        logger.info("PESOS:")
        logger.info(f"  - Total: {peso_total_valor} ton")
        logger.info(f"  - Parte Ativa: {peso_parte_ativa_valor} ton")
        logger.info(f"  - Óleo: {peso_oleo_valor} ton")
        logger.info(f"  - Tanque e Acessórios: {peso_tanque_acessorios_valor} ton")

        logger.info("======================================================================")

        top_items = [
            ("Potência:", "potencia_mva", "MVA"),
            ("Tipo:", "tipo_transformador", ""),
            ("Freq:", "frequencia", "Hz"),
            ("Grupo:", "grupo_ligacao", ""),
            ("Tipo Isolamento:", "tipo_isolamento", ""),
            ("Norma:", "norma_iso", ""),
        ]
        col_width = 12 // 6
        top_col_style = {
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "padding": "0.25rem 0.5rem",
            "height": "100%",
        }
        top_row = dbc.Row(
            [
                dbc.Col(
                    _create_info_item(label, transformer_data.get(key), unit),
                    width=col_width,
                    className="text-center px-0",
                    style={
                        **top_col_style,
                        "borderRight": f"1px solid {COLORS['border']}"
                        if i < len(top_items) - 1
                        else None,
                        "paddingLeft": "0.5rem" if i == 0 else "0.25rem",
                        "paddingRight": "0.5rem" if i == len(top_items) - 1 else "0.25rem",
                    },
                )
                for i, (label, key, unit) in enumerate(top_items)
            ],
            className="g-0 py-1 align-items-stretch justify-content-between",
            style=top_row_style,
        )  # align-items-stretch

        # --- Linha Principal: Detalhes Técnicos (7 Colunas) ---
        main_row_style = {
            "borderBottom": f"1px solid {COLORS['border']}",
            "width": "100%",
            "backgroundColor": COLORS["background_card"],
            "color": COLORS["text_light"],
        }
        main_columns = [
            {
                "title": "AT Tap-",
                "bg_color": bg_color_tap,
                "items": [
                    ("Tensão:", "tensao_at_tap_menor", "kV"),
                    ("Corrente:", "corrente_nominal_at_tap_menor", "A"),
                    ("Z:", "impedancia_tap_menor", "%"),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "AT Nominal",
                "bg_color": bg_color_nominal,
                "items": [
                    ("Tensão:", "tensao_at", "kV"),
                    ("Classe:", "classe_tensao_at", "kV"),
                    ("Corrente:", "corrente_nominal_at", "A"),
                    ("Z:", "impedancia", "%"),
                    ("NBI:", "nbi_at", "kVp"),
                    ("IM / SIL:", "sil_at", "kVp"),
                    ("Elev. Enrol.:", "elevacao_enrol_at", "°C"),
                    ("Conexão:", "conexao_at", ""),
                    ("Classe Neutro:", "tensao_bucha_neutro_at", "kV"),
                    ("NBI Neutro:", "nbi_neutro_at", "kVp"),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "AT Tap+",
                "bg_color": bg_color_tap,
                "items": [
                    ("Tensão:", "tensao_at_tap_maior", "kV"),
                    ("Corrente:", "corrente_nominal_at_tap_maior", "A"),
                    ("Z:", "impedancia_tap_maior", "%"),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "Baixa Tensão",
                "bg_color": bg_color_default,
                "items": [
                    ("Tensão:", "tensao_bt", "kV"),
                    ("Classe:", "classe_tensao_bt", "kV"),
                    ("Corrente:", "corrente_nominal_bt", "A"),
                    ("NBI:", "nbi_bt", "kVp"),
                    ("IM / SIL:", "sil_bt", "kVp"),
                    ("Elev. Enrol.:", "elevacao_enrol_bt", "°C"),
                    ("Conexão:", "conexao_bt", ""),
                    ("Classe Neutro:", "tensao_bucha_neutro_bt", "kV"),
                    ("NBI Neutro:", "nbi_neutro_bt", "kVp"),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "Terciário",
                "bg_color": bg_color_default,
                "items": [
                    ("Tensão:", "tensao_terciario", "kV"),
                    ("Classe:", "classe_tensao_terciario", "kV"),
                    ("Corrente:", "corrente_nominal_terciario", "A"),
                    ("NBI:", "nbi_terciario", "kVp"),
                    ("IM / SIL:", "sil_terciario", "kVp"),
                    ("Elev. Enrol.:", "elevacao_enrol_terciario", "°C"),
                    ("Conexão:", "conexao_terciario", ""),
                    ("Classe Neutro:", "tensao_bucha_neutro_terciario", "kV"),
                    ("NBI Neutro:", "nbi_neutro_terciario", "kVp"),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "Tensões de Ensaio",
                "bg_color": bg_color_default,
                "items": [
                    (None, None, None, "Aplicada (kV)"),
                    ("AT:", "teste_tensao_aplicada_at", ""),
                    ("BT:", "teste_tensao_aplicada_bt", ""),
                    ("Ter.:", "teste_tensao_aplicada_terciario", ""),
                    (None, None, None, "Induzida (kV)"),
                    ("AT:", "teste_tensao_induzida", ""),
                ],
                "style": col_style_with_border,
            },
            {
                "title": "Pesos (ton)",
                "bg_color": bg_color_default,
                "items": [
                    ("Total:", "peso_total", ""),
                    ("Parte Ativa:", "peso_parte_ativa", ""),
                    ("Óleo:", "peso_oleo", ""),
                    ("Tanque/Acess.:", "peso_tanque_acessorios", ""),
                    (None, None, None, "Líq. Isolante"),
                    ("Tipo:", "liquido_isolante", ""),
                ],
                "style": col_style_last,
            },
        ]
        main_row = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            col["title"],
                            style={**title_style_base, "backgroundColor": col["bg_color"]},
                        ),  # Corrigido para backgroundColor
                        *[
                            html.Div(extra[0], style=subtitle_style)
                            if len(extra) > 0 and label is None
                            else _create_info_item(label, transformer_data.get(key), unit)
                            for label, key, unit, *extra in col["items"]
                        ],
                    ],
                    style=col["style"],
                    className="d-flex flex-column",
                )  # Added flex column
                for col in main_columns
            ],
            className="row-cols-7 g-0 py-1",
            style=main_row_style,
        )

        # --- Layout Final ---
        layout_children = [top_row, main_row]

        return html.Div(
            layout_children,
            className="border rounded shadow-sm",
            style={
                "backgroundColor": COLORS["background_card"],
                "borderColor": COLORS["border"],
                "color": COLORS["text_light"],
                "width": "100%",
                "boxShadow": "0 4px 8px rgba(0,0,0,0.15), 0 1px 3px rgba(0,0,0,0.1)",
                "overflow": "hidden",
                "marginBottom": "5px",
            },
        )

    except Exception as e:
        logger.error(f"Erro ao criar painel de informações do transformador: {e}", exc_info=True)
        error_style = {
            "fontSize": "0.7rem",
            "color": COLORS["danger"],
            "padding": "10px",
            "border": f"1px solid {COLORS['danger']}",
            "borderRadius": "4px",
            "backgroundColor": COLORS["background_card"],
        }
        return html.Div(f"Erro ao exibir informações: {str(e)}", style=error_style)
