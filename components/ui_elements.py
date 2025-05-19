# components/ui_elements.py
"""
Define funções reutilizáveis para criar elementos comuns da Interface do Usuário (UI)
usando Dash Bootstrap Components e Dash Core Components.
"""
import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

# Importar configurações, constantes e formatadores
import config
from utils import constants

# Importar formatador diretamente
from .formatters import format_parameter_value

log = logging.getLogger(__name__)

# --- Elementos de Input ---


def create_labeled_input(
    label_text: str,
    input_id,  # Aceita ID simples ou pattern-matching
    input_type: str = "number",  # 'number', 'text', 'dropdown'
    placeholder: str = "",
    label_width: int = 6,  # Largura da coluna do label (1-12)
    input_width: int = 6,  # Largura da coluna do input (1-12)
    step = "any",  # Para type="number"
    value = None,
    disabled: bool = False,
    readonly: bool = False,
    options = None,  # Para type="dropdown" [{'label': '...', 'value': '...'}]
    persistence: bool = True,
    persistence_type: str = "local",  # Default 'local'
    input_style = None,  # Estilo inline opcional para input/dropdown
    label_style = None,  # Estilo inline opcional para label
    row_classname: str = "g-1 mb-1 align-items-center",  # Classes Bootstrap para a Row
    **kwargs,  # Outros props para dbc.Input ou dcc.Dropdown
) -> dbc.Row:
    """
    Cria uma linha (dbc.Row) com um Label e um Input/Dropdown,
    usando estilos padronizados do layouts/__init__.py
    """
    # Importar estilos padronizados
    from layouts import COMPONENTS, TYPOGRAPHY

    # Estilos base
    default_label_style = TYPOGRAPHY["label"]
    default_input_style = COMPONENTS["input"]
    default_readonly_style = COMPONENTS["read_only"]

    # Aplicar estilos finais com overrides
    final_label_style = {**default_label_style, **(label_style or {})}

    # Garante que o ID seja string para html_for
    label_for_id = str(input_id) if isinstance(input_id, dict) else input_id

    # Componente de label
    label_component = dbc.Label(label_text, html_for=label_for_id, style=final_label_style)

    if input_type == "dropdown":
        str_value = str(value) if value is not None else None
        # Verifica se className já foi fornecido nos kwargs
        class_name = kwargs.pop("className", "dark-dropdown")
        # Remove style dos kwargs se estiver presente para evitar conflito
        if "style" in kwargs:
            log.warning(
                f"Style fornecido tanto via input_style quanto via kwargs para {input_id}. Usando input_style."
            )
            kwargs.pop("style")

        # Determina o estilo final para o dropdown
        final_input_style = {**default_input_style, **(input_style or {})}

        input_component = dcc.Dropdown(
            id=input_id,
            options=options or [],
            value=str_value,
            placeholder=placeholder,
            disabled=disabled,
            clearable=kwargs.pop("clearable", False),
            persistence=persistence,
            persistence_type=persistence_type,
            style=final_input_style,
            className=class_name,
            **kwargs,  # Usa a classe fornecida ou dark-dropdown por padrão
        )
    else:
        # Remove style dos kwargs se estiver presente para evitar conflito
        if "style" in kwargs:
            log.warning(
                f"Style fornecido tanto via input_style quanto via kwargs para {input_id}. Usando input_style."
            )
            kwargs.pop("style")

        # Determina o estilo final para o input baseado no tipo
        if readonly:
            # Para campos readonly, usa o estilo readonly como base
            final_input_style = {**default_readonly_style}
        else:
            # Para campos normais, usa o estilo padrão de input
            final_input_style = {**default_input_style}

        # Aplica os overrides de estilo por último
        if input_style:
            final_input_style.update(input_style)

        input_component = dbc.Input(
            id=input_id,
            type=input_type,
            placeholder=placeholder,
            step=step if input_type == "number" else None,
            value=value,
            disabled=disabled,
            readonly=readonly,
            persistence=persistence,
            persistence_type=persistence_type,
            style=final_input_style,
            className=kwargs.pop("className", ""),
            **kwargs,
        )

    return dbc.Row(
        [
            dbc.Col(
                label_component,
                width=label_width,
                className="d-flex align-items-center justify-content-end",
            ),
            dbc.Col(input_component, width=input_width),
        ],
        className=row_classname,
    )


# --- Elementos Específicos de Módulos ---

# == Dieletric Analysis ==


def create_dielectric_input_column(verificador_instance, label: str, identifier: str) -> dbc.Card:
    """
    Cria a coluna de inputs para um enrolamento na Análise Dielétrica.
    Busca opções 'Um' do verificador_instance, se disponível e válido.
    """
    # Não precisamos mais buscar opções do verificador, pois todos os campos são somente leitura
    if not verificador_instance:
        log.warning(f"Verificador não disponível ao criar coluna dielétrica ({label}).")
    elif not verificador_instance.is_valid():
        log.warning(f"Verificador inválido ao criar coluna dielétrica ({label}).")

    # IDs usando pattern-matching - IMPORTANTE: Estes IDs devem corresponder exatamente aos IDs esperados pelos callbacks
    um_id = {"type": "um", "index": identifier}
    conexao_id = {"type": "conexao", "index": identifier}
    neutro_div_id = {"type": "div-neutro", "index": identifier}
    neutro_um_id = {"type": "neutro-um", "index": identifier}
    ia_neutro_id = {"type": "impulso-atm-neutro", "index": identifier}
    ia_id = {"type": "ia", "index": identifier}  # ID para Impulso Atmosférico / BIL
    iac_id = {"type": "impulso-atm-cortado", "index": identifier}
    im_id = {"type": "im", "index": identifier}  # ID para Impulso de Manobra / SIL
    tc_id = {"type": "tensao-curta", "index": identifier}
    ti_id = {"type": "tensao-induzida", "index": identifier}  # ID para Tensão Induzida
    esp_nbr_id = {"type": "espacamentos-nbr", "index": identifier}
    esp_ieee_id = {"type": "espacamentos-ieee", "index": identifier}

    # Importar estilos padronizados
    from layouts import COMPONENTS, TYPOGRAPHY

    # Estilos e defaults
    card_header_style = COMPONENTS["card_header"]
    label_col_width = 5
    input_col_width = 7
    card_style = COMPONENTS["card"]

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Div(label, className="text-center fw-bold"), style=card_header_style
            ),
            dbc.CardBody(
                [
                    # Conexão (Campo de texto somente leitura, como os demais)
                    create_labeled_input(
                        "Conexão:",
                        conexao_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # Div Neutro - Estilo consistente com os demais campos
                    html.Div(
                        id=neutro_div_id,
                        style={"display": "block", "marginBottom": "0.5rem"},
                        children=[
                            create_labeled_input(
                                "Um Neutro (kV):",
                                neutro_um_id,
                                input_type="text",
                                placeholder="-",
                                label_width=label_col_width,
                                input_width=input_col_width,
                                readonly=True,
                                className="read-only-input",
                            ),
                            create_labeled_input(
                                "IA / BIL Neutro (kV):",
                                ia_neutro_id,
                                input_type="text",
                                placeholder="-",
                                label_width=label_col_width,
                                input_width=input_col_width,
                                readonly=True,
                                className="read-only-input",
                            ),
                        ],
                    ),
                    # Um
                    create_labeled_input(
                        "Um (kV):",
                        um_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # IA / BIL
                    create_labeled_input(
                        "IA / BIL (kV):",
                        ia_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # IAC
                    create_labeled_input(
                        "IAC (kV):",
                        iac_id,
                        input_type="text",
                        placeholder="",
                        readonly=True,
                        label_width=label_col_width,
                        input_width=input_col_width,
                        className="read-only-input",
                    ),
                    # IM / SIL
                    create_labeled_input(
                        "IM / SIL (kV):",
                        im_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # T.Aplicada
                    create_labeled_input(
                        "T.Aplicada (kV):",
                        tc_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # T.Induzida (agora como input text em vez de dropdown)
                    create_labeled_input(
                        "T.Induzida (kV):",
                        ti_id,
                        input_type="text",
                        placeholder="-",
                        label_width=label_col_width,
                        input_width=input_col_width,
                        readonly=True,
                        className="read-only-input",
                    ),
                    # Espaçamentos
                    html.Div(
                        [
                            html.Hr(className="my-2"),
                            html.Div(
                                "Distâncias Dielétricas:",
                                style={
                                    **TYPOGRAPHY["section_title"],
                                    "marginBottom": "4px",
                                    "textAlign": "center",
                                },
                            ),
                            dcc.Loading(
                                html.Div(
                                    [
                                        html.Div(id=esp_nbr_id, style=TYPOGRAPHY["small_text"]),
                                        html.Div(id=esp_ieee_id, style=TYPOGRAPHY["small_text"]),
                                    ]
                                )
                            ),
                        ]
                    ),
                ],
                style=COMPONENTS["card_body"],
            ),
        ],
        className="h-100",
        style=card_style,
    )


# == Tabelas de Resultados (Implementações restantes como na resposta anterior) ==


def create_test_sequence_table(
    title: str, data, tipo_isolamento = None
) -> html.Div:
    """Cria tabela formatada para sequências de ensaio (ex: Tensão Induzida NBR)."""
    bg_medium = config.colors.get("background_medium", "#e9ecef")
    base_style = {"fontSize": "0.7rem", "padding": "0.2rem"}
    header_style = {**base_style, "fontWeight": "bold", "backgroundColor": bg_medium}
    title_style = {
        "fontSize": "0.7rem",
        "fontWeight": "bold",
        "backgroundColor": bg_medium,
        "padding": "2px",
        "marginTop": "4px",
        "marginBottom": "4px",
        "textAlign": "center",
    }
    info_style = {
        "fontSize": "0.7rem",
        "fontStyle": "italic",
        "marginBottom": "5px",
        "color": config.colors.get("text_muted", "#6c757d"),
    }

    if not data or not isinstance(data, dict) or not data.get("patamares"):
        return html.Div(
            [
                html.Div(title, style=title_style),
                html.P(
                    "Dados da sequência não disponíveis.",
                    style={**base_style, "fontStyle": "italic"},
                ),
            ],
            className="mb-2",
        )

    patamares = data.get("patamares", [])
    parametros = data.get("parametros", {})
    medicao_dp = parametros.get("medicao_dp", {}).get("limites", {})

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Nível", style=header_style),
                    html.Th("Tensão (kV)", style=header_style),
                    html.Th("Tempo", style=header_style),
                ]
            )
        )
    ]
    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            format_parameter_value(p.get("nivel"), none_value="-"), style=base_style
                        ),
                        html.Td(
                            format_parameter_value(p.get("tensao"), 1, "kV", "-"), style=base_style
                        ),
                        html.Td(
                            format_parameter_value(p.get("tempo"), none_value="-"), style=base_style
                        ),
                    ]
                )
                for p in patamares
                if isinstance(p, dict)  # Verifica se p é dict
            ]
        )
    ]

    dp_info = []
    if medicao_dp and isinstance(medicao_dp, dict):  # Verifica se medicao_dp é dict
        dp_info.append(html.Strong("Medição de DP:", style={"fontSize": "0.7rem"}))
        dp_items = [
            html.Li(
                f"{k.replace('_',' ').title()}:   {format_parameter_value(v, 1, 'kV', '-')}",
                style={"fontSize": "0.7rem"},
            )
            for k, v in medicao_dp.items()
            if v is not None
        ]
        if dp_items:
            dp_info.append(
                html.Ul(dp_items, style={"marginBottom": "0.2rem", "paddingLeft": "1rem"})
            )

    # Adiciona informações sobre o tipo de isolamento
    isolamento_info = []
    if tipo_isolamento and "Trifásico Longa" in title:
        if tipo_isolamento == "progressivo":
            isolamento_info.append(
                html.Div(
                    "Nota: O ensaio de longa duração é especialmente importante para transformadores com isolamento progressivo, "
                    "pois verifica a integridade do isolamento sob estresse prolongado nas extremidades dos enrolamentos.",
                    style=info_style,
                )
            )
    elif tipo_isolamento and "Trifásico Curta" in title:
        if tipo_isolamento == "uniforme":
            isolamento_info.append(
                html.Div(
                    "Nota: Para transformadores com isolamento uniforme, o ensaio de curta duração é suficiente "
                    "para verificar a integridade do isolamento.",
                    style=info_style,
                )
            )

    return html.Div(
        [
            html.Div(title, style=title_style),
            *isolamento_info,  # Adiciona informações sobre o tipo de isolamento, se houver
            dbc.Table(table_header + table_body, bordered=True, size="sm", className="mb-1"),
            html.Div(dp_info),
        ],
        className="mb-2",
    )


def create_comparison_table(
    title: str, nbr_data, ieee_data, tipo_isolamento = None
) -> html.Div:
    """Cria tabela comparativa entre normas (NBR vs IEEE)."""
    bg_medium = config.colors.get("background_medium", "#e9ecef")
    base_style = {"fontSize": "0.7rem", "padding": "0.2rem"}
    header_style = {**base_style, "fontWeight": "bold", "backgroundColor": bg_medium}
    title_style = {
        "fontSize": "0.7rem",
        "fontWeight": "bold",
        "backgroundColor": bg_medium,
        "padding": "2px",
        "marginTop": "4px",
        "marginBottom": "4px",
        "textAlign": "center",
    }

    # Estilo para informações adicionais
    info_style = {
        "fontSize": "0.7rem",
        "fontStyle": "italic",
        "marginBottom": "5px",
        "color": config.colors.get("text_muted", "#6c757d"),
    }

    if not nbr_data and not ieee_data:
        return html.Div()

    rows = []
    mapping_req = {
        "Impulso Atmosférico": ("impulso_atmosferico", "bil_test"),
        "Impulso Onda Cortada": ("impulso_atmosferico_onda_cortada", "chopped_wave_test"),
        "Impulso Manobra": ("impulso_manobra", "switching_impulse_test"),
        "Tensão Induzida Curta": ("tensao_induzida_curta", "induced_voltage_test"),
        "Tensão Induzida Longa": ("tensao_induzida_longa", None),
        "Tensão Aplicada": ("tensao_aplicada", "applied_voltage_test"),
    }
    is_required_tests = title == "Ensaios Requeridos"

    if is_required_tests:
        for label, (nbr_key, ieee_key) in mapping_req.items():
            nbr_value = nbr_data.get(nbr_key, "-") if isinstance(nbr_data, dict) else "-"
            ieee_value = (
                ieee_data.get(ieee_key, "-") if isinstance(ieee_data, dict) and ieee_key else "-"
            )
            rows.append(
                html.Tr(
                    [
                        html.Td(label, style=base_style),
                        html.Td(str(nbr_value), style=base_style),
                        html.Td(str(ieee_value), style=base_style),
                    ]
                )
            )
    else:
        all_keys = set()
        if isinstance(nbr_data, dict):
            all_keys.update(nbr_data.keys())
        if isinstance(ieee_data, dict):
            all_keys.update(ieee_data.keys())
        common_keys = sorted(list(all_keys - {"norma", "tipo", "tensao_nominal"}))

        for key in common_keys:
            label = key.replace("_", " ").title()
            nbr_value = nbr_data.get(key, "-") if isinstance(nbr_data, dict) else "-"
            ieee_value = ieee_data.get(key, "-") if isinstance(ieee_data, dict) else "-"
            rows.append(
                html.Tr(
                    [
                        html.Td(label, style=base_style),
                        html.Td(str(nbr_value), style=base_style),
                        html.Td(str(ieee_value), style=base_style),
                    ]
                )
            )

    if not rows:
        return html.Div(
            [html.Div(title, style=title_style), html.P("Dados não disponíveis.", style=base_style)]
        )

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Parâmetro", style=header_style),
                    html.Th("NBR 5356-3", style=header_style),
                    html.Th("IEEE C57.12.00", style=header_style),
                ]
            )
        )
    ]
    table_body = [html.Tbody(rows)]

    # Adiciona informações sobre o tipo de isolamento se for a tabela de Ensaios Requeridos
    additional_info = []
    if is_required_tests and tipo_isolamento:
        isolamento_info = f"Tipo de Isolamento:  {tipo_isolamento.capitalize()}"
        if tipo_isolamento == "uniforme":
            isolamento_info += " - Distribuição uniforme de tensão ao longo do enrolamento."
        elif tipo_isolamento == "progressivo":
            isolamento_info += " - Maior reforço nas extremidades dos enrolamentos para otimizar resposta a impulsos."
        additional_info.append(html.Div(isolamento_info, style=info_style))

    return html.Div(
        [
            html.Div(title, style=title_style),
            *additional_info,  # Adiciona informações sobre o tipo de isolamento, se houver
            dbc.Table(table_header + table_body, bordered=True, size="sm", className="mb-1"),
        ]
    )


# == Tabelas de Resultados (Impulse) ==
# (As funções create_circuit_parameters_display, create_energy_details_table, create_waveform_analysis_table
#  permanecem como na resposta anterior, pois não foram a causa do erro htmlFor)


def create_circuit_parameters_display(params_data: dict | None) -> dbc.Table | dbc.Alert:
    """Cria uma tabela HTML formatada para os parâmetros do circuito de impulso."""
    if not params_data or not isinstance(params_data, dict):
        return dbc.Alert(
            "Dados de parâmetros do circuito indisponíveis.",
            color="warning",
            style={"fontSize": "0.7rem"},
        )
    if "error" in params_data:
        return dbc.Alert(
            f"Erro nos parâmetros: {params_data['error']}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )

    header = html.Thead(
        html.Tr(
            [
                html.Th("Parâmetro", style={"fontSize": "0.7rem"}),
                html.Th("Valor", style={"fontSize": "0.7rem"}),
            ]
        )
    )
    rows = []
    cell_style = {"fontSize": "0.7rem", "padding": "0.2rem"}
    label_style = {**cell_style, "fontWeight": "bold"}

    def add_row(label, value, unit="", precision=2):
        formatted_value = format_parameter_value(value, precision, unit)
        rows.append(
            html.Tr([html.Td(label, style=label_style), html.Td(formatted_value, style=cell_style)])
        )

    try:
        resistances = params_data.get("resistances", {})
        inductances = params_data.get("inductances", {})
        capacitances = params_data.get("capacitances", {})
        derived = params_data.get("derived_params", {})
        efficiency = params_data.get("efficiency", {})

        add_row("Config. Gerador", params_data.get("generator_config"))
        add_row("Cg Efetiva", capacitances.get("cg_eff"), "nF", 3)
        add_row("L Gerador Efetiva", inductances.get("gen_eff"), "µH", 1)
        add_row("L Externa", inductances.get("ext"), "µH", 1)
        add_row("L Adicional", inductances.get("add"), "µH", 1)
        add_row("L Carga (Trafo)", inductances.get("load"), "H", 4)
        add_row("L TOTAL AJUSTADA", inductances.get("total"), "mH", 3)
        add_row("Carga DUT", capacitances.get("c_dut", 0) * 1e12, "pF", 0)
        add_row("Carga Divisor", capacitances.get("c_divider", 0) * 1e12, "pF", 0)
        add_row("Carga Parasita", capacitances.get("c_stray", 0) * 1e12, "pF", 0)
        add_row("Capacitor SI", capacitances.get("c_si", 0) * 1e12, "pF", 0)
        add_row("Carga Extra (Gap/Ck)", capacitances.get("c_load_extra", 0) * 1e12, "pF", 0)
        add_row("Carga TOTAL (Cl)", capacitances.get("cload"), "nF", 2)
        add_row("Rf por Coluna", resistances.get("front_col"), "Ω", 2)
        add_row("Rt por Coluna", resistances.get("tail_col"), "Ω", 2)
        add_row("Rf Efetivo Total", resistances.get("rf_eff"), "Ω", 2)
        add_row("Rt Efetivo Total AJUSTADO", resistances.get("rt_eff"), "Ω", 2)
        add_row("C Equivalente (Ceq)", capacitances.get("ceq"), "nF", 3)
        add_row("Alpha Calculado (α)", derived.get("alpha"), "s⁻¹", 2)
        add_row("Beta Calculado (β)", derived.get("beta"), "s⁻¹", 2)
        add_row("Amortecimento (ζ)", derived.get("zeta"), "", 3)
        add_row("Eficiência Circuito", efficiency.get("circuit", 0) * 100, "%", 1)
        add_row("Eficiência Forma", efficiency.get("shape", 0) * 100, "%", 1)
        add_row("Eficiência TOTAL", efficiency.get("total", 0) * 100, "%", 1)
        add_row("Tensão Carga Gerador", params_data.get("charging_voltage"), "kV", 1)
        add_row("Tensão Pico/Corte Real", params_data.get("actual_test_voltage"), "kV", 1)

    except Exception as e:
        log.exception(f"Erro ao processar parâmetros do circuito para exibição: {e}")
        return dbc.Alert(
            f"Erro ao exibir parâmetros: {str(e)}", color="danger", style={"fontSize": "0.7rem"}
        )

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        striped=True,
        size="sm",
        className="mb-0",
    )


def create_energy_details_table(
    energy_required_kj: float | None,
    max_energy_kj: float | None,
    generator_config_label: str | None,
) -> dbc.Table | dbc.Alert:
    """Cria uma tabela com detalhes de energia requerida vs. disponível."""
    if energy_required_kj is None or max_energy_kj is None:
        return dbc.Alert(
            "Dados de energia indisponíveis.", color="warning", style={"fontSize": "0.7rem"}
        )
    try:
        rows = [
            html.Tr(
                [
                    html.Td("Energia Requerida (Carga):"),
                    html.Td(format_parameter_value(energy_required_kj, 2, "kJ")),
                ]
            ),
            html.Tr(
                [
                    html.Td("Energia Disponível (Gerador):"),
                    html.Td(format_parameter_value(max_energy_kj, 1, "kJ")),
                ]
            ),
            html.Tr([html.Td("Configuração Gerador:"), html.Td(generator_config_label or "N/A")]),
        ]
        energy_margin = (
            max_energy_kj / energy_required_kj if energy_required_kj > 1e-9 else float("inf")
        )
        margin_class = (
            "text-success"
            if energy_margin >= 1.2
            else "text-warning"
            if energy_margin >= 1.0
            else "text-danger"
        )
        margin_text = f"{energy_margin:.2f}x" if energy_margin != float("inf") else "∞"
        rows.append(
            html.Tr([html.Td("Margem de Energia:"), html.Td(margin_text, className=margin_class)])
        )
        cell_style = {"fontSize": "0.7rem", "padding": "0.2rem"}
        for row in rows:
            for cell in row.children:
                if isinstance(cell, html.Td):
                    cell.style = cell_style
        return dbc.Table(
            [html.Tbody(rows)], bordered=True, hover=True, striped=True, size="sm", className="mb-0"
        )
    except Exception as e:
        log.exception(f"Erro ao criar tabela de energia: {str(e)}")
        return dbc.Alert(
            f"Erro ao exibir energia: {str(e)}", color="danger", style={"fontSize": "0.7rem"}
        )


def create_waveform_analysis_table(
    analysis_results: dict | None, impulse_type: str
) -> dbc.Table | dbc.Alert:
    """Cria uma tabela com os resultados da análise da forma de onda e status de conformidade."""
    if not analysis_results or not isinstance(analysis_results, dict):
        return dbc.Alert(
            "Resultados da análise indisponíveis.", color="warning", style={"fontSize": "0.7rem"}
        )
    if "error" in analysis_results and analysis_results["error"]:
        return dbc.Alert(
            f"Erro na análise: {analysis_results['error']}",
            color="danger",
            style={"fontSize": "0.7rem"},
        )
    if constants is None:
        return dbc.Alert(
            "Erro interno: Não foi possível carregar constantes.",
            color="danger",
            style={"fontSize": "0.7rem"},
        )

    header = html.Thead(
        html.Tr(
            [
                html.Th("Parâmetro", style={"fontSize": "0.7rem"}),
                html.Th("Valor Simulado", style={"fontSize": "0.7rem"}),
                html.Th("Requisito Norma", style={"fontSize": "0.7rem"}),
                html.Th("Status", style={"fontSize": "0.7rem"}),
            ]
        )
    )
    rows = []
    cell_style = {"fontSize": "0.7rem", "padding": "0.2rem"}
    pass_style = {**cell_style, "backgroundColor": config.colors.get("pass_bg", "#d1e7dd")}
    fail_style = {**cell_style, "backgroundColor": config.colors.get("fail_bg", "#f8d7da")}
    warn_style = {**cell_style, "backgroundColor": config.colors.get("warning_bg", "#fff3cd")}

    def add_analysis_row(
        label, param_key, unit, req_min, req_max, conforme_key, precision=2, is_max_limit=False
    ):
        value = analysis_results.get(param_key)
        conforme = analysis_results.get(conforme_key, None)
        val_str = format_parameter_value(value, precision, unit)

        req_str = ""
        if is_max_limit and req_max is not None:
            req_str = f"≤ {format_parameter_value(req_max, precision, unit)}"
        elif req_min is not None and req_max is None:
            req_str = f"≥ {format_parameter_value(req_min, precision, unit)}"
        elif req_min is not None and req_max is not None:
            req_str = f"{format_parameter_value(req_min, precision, '')} - {format_parameter_value(req_max, precision, unit)}"
        else:
            req_str = "-"

        status_symbol = "❓"
        current_row_style = warn_style
        if conforme is True:
            status_symbol = "✔️"
            current_row_style = pass_style
        elif conforme is False:
            status_symbol = "❌"
            current_row_style = fail_style

        rows.append(
            html.Tr(
                [
                    html.Td(label, style=cell_style),
                    html.Td(val_str, style=cell_style),
                    html.Td(req_str, style=cell_style),
                    html.Td(status_symbol, style={"textAlign": "center", **cell_style}),
                ],
                style={"backgroundColor": current_row_style["backgroundColor"]},
            )
        )

    try:
        if impulse_type == "lightning":
            req = {
                "T1_min": constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 - constants.LIGHTNING_FRONT_TOLERANCE),
                "T1_max": constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 + constants.LIGHTNING_FRONT_TOLERANCE),
                "T2_min": constants.LIGHTNING_IMPULSE_TAIL_TIME_NOM
                * (1 - constants.LIGHTNING_TAIL_TOLERANCE),
                "T2_max": constants.LIGHTNING_IMPULSE_TAIL_TIME_NOM
                * (1 + constants.LIGHTNING_TAIL_TOLERANCE),
                "Beta_max": constants.LIGHTNING_OVERSHOOT_MAX * 100.0,
            }
            add_analysis_row(
                "Vt (Pico Ensaio)",
                "peak_value_test",
                "kV",
                None,
                None,
                "conforme_pico",
                precision=1,
            )
            add_analysis_row(
                "T₁ (Frente)", "t_front_us", "µs", req["T1_min"], req["T1_max"], "conforme_frente"
            )
            add_analysis_row(
                "T₂ (Cauda)",
                "t_tail_us",
                "µs",
                req["T2_min"],
                req["T2_max"],
                "conforme_cauda",
                precision=1,
            )
            add_analysis_row(
                "β (Overshoot)",
                "overshoot_percent",
                "%",
                None,
                req["Beta_max"],
                "conforme_overshoot",
                precision=1,
                is_max_limit=True,
            )
        elif impulse_type == "switching":
            req = {
                "Tp_min": constants.SWITCHING_IMPULSE_PEAK_TIME_NOM
                * (1 - constants.SWITCHING_PEAK_TIME_TOLERANCE),
                "Tp_max": constants.SWITCHING_IMPULSE_PEAK_TIME_NOM
                * (1 + constants.SWITCHING_PEAK_TIME_TOLERANCE),
                "T2_min": constants.SWITCHING_IMPULSE_TAIL_TIME_NOM
                * (1 - constants.SWITCHING_TAIL_TOLERANCE),
                "T2_max": constants.SWITCHING_IMPULSE_TAIL_TIME_NOM
                * (1 + constants.SWITCHING_TAIL_TOLERANCE),
                "Td_min": constants.SWITCHING_TIME_ABOVE_90_MIN,
                "Tz_min": constants.SWITCHING_TIME_TO_ZERO_MIN,
            }
            add_analysis_row(
                "Vp (Pico Medido)",
                "peak_value_measured",
                "kV",
                None,
                None,
                "conforme_pico",
                precision=1,
            )
            add_analysis_row(
                "Tp (Tempo Pico Norma)",
                "t_p_us",
                "µs",
                req["Tp_min"],
                req["Tp_max"],
                "conforme_tp",
                precision=0,
            )
            add_analysis_row(
                "T₂ (Meio Valor)",
                "t_2_us",
                "µs",
                req["T2_min"],
                req["T2_max"],
                "conforme_t2",
                precision=0,
            )
            add_analysis_row(
                "Td (>90%)", "td_us", "µs", req["Td_min"], None, "conforme_td", precision=0
            )
            add_analysis_row(
                "Tz (Zero)", "t_zero_us", "µs", req["Tz_min"], None, "conforme_tzero", precision=0
            )
        elif impulse_type == "chopped":
            req = {
                "T1_min": constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 - constants.CHOPPED_FRONT_TOLERANCE),
                "T1_max": constants.LIGHTNING_IMPULSE_FRONT_TIME_NOM
                * (1 + constants.CHOPPED_FRONT_TOLERANCE),
                "Tc_min": constants.CHOPPED_IMPULSE_CHOP_TIME_MIN,
                "Tc_max": constants.CHOPPED_IMPULSE_CHOP_TIME_MAX,
                "Undershoot_max": constants.CHOPPED_UNDERSHOOT_MAX * 100.0,
            }
            add_analysis_row(
                "Vc (Tensão Corte Teste)",
                "chop_voltage_test_kv",
                "kV",
                None,
                None,
                "conforme_pico_corte",
                precision=1,
            )
            add_analysis_row(
                "T₁ (Frente Subj.)",
                "t_front_us",
                "µs",
                req["T1_min"],
                req["T1_max"],
                "conforme_frente",
            )
            add_analysis_row(
                "Tc (Tempo Corte)",
                "chop_time_us",
                "µs",
                req["Tc_min"],
                req["Tc_max"],
                "conforme_corte",
            )
            add_analysis_row(
                "Undershoot",
                "undershoot_percent",
                "%",
                None,
                req["Undershoot_max"],
                "conforme_undershoot",
                precision=1,
                is_max_limit=True,
            )
        else:
            return dbc.Alert(
                f"Tipo de impulso desconhecido para análise: {impulse_type}", color="warning"
            )
    except AttributeError as e:
        log.error(f"Erro ao acessar constante em utils.constants: {e}")
        return dbc.Alert("Erro interno ao carregar limites da norma.", color="danger")
    except Exception as e:
        log.exception(f"Erro inesperado ao criar tabela de análise: {e}")
        return dbc.Alert("Erro inesperado ao formatar tabela de análise.", color="danger")

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        striped=True,
        size="sm",
        className="mb-0",
    )
