# components/formatters.py
"""
Funções para formatar dados para exibição na UI e, principalmente,
para a geração de relatórios PDF, convertendo dados dos Stores
em estruturas compatíveis com o pdf_generator.
"""
import logging
import math

log = logging.getLogger(__name__)

# --- Formatador Genérico de Valor (para UI e PDF) ---


def format_parameter_value(
    param_value, precision: int = 2, unit: str = "", none_value: str = "N/A"
) -> str:
    """
    Formata um valor numérico (ou outros tipos) para exibição, tratando None, NaN, Inf.
    Retorna uma string formatada.

    Args:
        param_value: O valor a ser formatado.
        precision: Número de casas decimais para floats.
        unit: Unidade a ser anexada (com espaço).
        none_value: String a ser retornada se o valor for None, NaN ou Inf.

    Returns:
        String formatada.
    """
    if param_value is None:
        return none_value
    if isinstance(param_value, bool):
        return "Sim" if param_value else "Não"
    if isinstance(param_value, (int, float)):
        if math.isnan(param_value) or math.isinf(param_value):
            return none_value
        val = float(param_value)

        # Format with specific precision first
        try:
            formatted_num = f"{val:.{precision}f}"
            # Remove trailing zeros if needed (e.g., 1.20 -> 1.2, 1.00 -> 1)
            if precision > 0 and "." in formatted_num:
                formatted_num = formatted_num.rstrip("0").rstrip(".")
            return f"{formatted_num}  {unit}".strip() if unit else formatted_num
        except (ValueError, TypeError):
            # Fallback for potential issues with f-string formatting
            return str(param_value)

    # For other types (string, etc.), return as string
    return str(param_value).strip() if str(param_value).strip() else none_value


# --- Formatadores Específicos para Relatório PDF ---


def formatar_dados_basicos(dados: dict) -> dict:
    """Formata dados básicos para estrutura de tabela PDF (parâmetro-valor)."""
    if not isinstance(dados, dict) or not dados:
        log.warning("Dados básicos ausentes para formatação PDF.")
        return {}  # Retorna dicionário vazio

    log.debug("Formatando dados básicos para PDF...")
    # Map internal keys to user-friendly labels
    nomes_amigaveis = {
        "tipo_transformador": "Tipo",
        "potencia_mva": "Potência (MVA)",
        "frequencia": "Frequência (Hz)",
        "tensao_at": "Tensão Nom. AT (kV)",
        "corrente_nominal_at": "Corrente Nom. AT (A)",
        "impedancia": "Impedância Nom. (%)",
        "conexao_at": "Conexão AT",
        "nbi_at": "NBI AT (kV)",
        "tensao_at_tap_maior": "Tensão Tap+ AT (kV)",
        "corrente_nominal_at_tap_maior": "Corrente Tap+ AT (A)",
        "impedancia_tap_maior": "Impedância Tap+ (%)",
        "tensao_at_tap_menor": "Tensão Tap- AT (kV)",
        "corrente_nominal_at_tap_menor": "Corrente Tap- AT (A)",
        "impedancia_tap_menor": "Impedância Tap- (%)",
        "tensao_bt": "Tensão Nom. BT (kV)",
        "corrente_nominal_bt": "Corrente Nom. BT (A)",
        "conexao_bt": "Conexão BT",
        "nbi_bt": "NBI BT (kV)",
        "tensao_terciario": "Tensão Nom. Terciário (kV)",
        "corrente_nominal_terciario": "Corrente Nom. Terciário (A)",
        "conexao_terciario": "Conexão Terciário",
        "nbi_terciario": "NBI Terciário (kV)",
        "tensao_bucha_neutro_at": "Tensão Bucha Neutro AT (kV)",
        "tensao_bucha_neutro_bt": "Tensão Bucha Neutro BT (kV)",
        "tensao_bucha_neutro_terciario": "Tensão Bucha Neutro Ter. (kV)",
        "peso_total": "Peso Total (kg)",
        "peso_parte_ativa": "Peso Parte Ativa (kg)",
        "peso_oleo": "Peso Óleo (kg)",
    }
    # Define the order of fields in the report
    ordem_campos = [
        "tipo_transformador",
        "potencia_mva",
        "frequencia",
        "tensao_at",
        "corrente_nominal_at",
        "impedancia",
        "conexao_at",
        "nbi_at",
        "tensao_bucha_neutro_at",
        "tensao_at_tap_maior",
        "corrente_nominal_at_tap_maior",
        "impedancia_tap_maior",
        "tensao_at_tap_menor",
        "corrente_nominal_at_tap_menor",
        "impedancia_tap_menor",
        "tensao_bt",
        "corrente_nominal_bt",
        "conexao_bt",
        "nbi_bt",
        "tensao_bucha_neutro_bt",
        "tensao_terciario",
        "corrente_nominal_terciario",
        "conexao_terciario",
        "nbi_terciario",
        "tensao_bucha_neutro_terciario",
        "peso_total",
        "peso_parte_ativa",
        "peso_oleo",
    ]

    # Create formatted dictionary (Parameter: Value)
    dados_formatados_pv = {}
    for k in ordem_campos:
        valor = dados.get(k)
        if valor is not None and str(valor).strip() != "":
            # Determine precision based on key
            precision = (
                0 if "peso" in k else (1 if "mva" in k or "tensao" in k or "nbi" in k else 2)
            )
            unit = (
                "kV"
                if "tensao" in k or "nbi" in k
                else (
                    "%"
                    if "impedancia" in k
                    else (
                        "kg"
                        if "peso" in k
                        else (
                            "Hz"
                            if "freq" in k
                            else ("A" if "corrente" in k else ("MVA" if "potencia" in k else ""))
                        )
                    )
                )
            )
            valor_formatado = format_parameter_value(valor, precision, unit)
            dados_formatados_pv[nomes_amigaveis.get(k, k)] = valor_formatado

    # Return in the structure expected by add_section {Title: {Param: Val}}
    return {"Dados Nominais e Características": dados_formatados_pv} if dados_formatados_pv else {}


def formatar_perdas_vazio(dados_vazio: dict | None) -> dict:
    """Formata dados de perdas em vazio para estrutura PDF (dicionários Parameter:Value)."""
    if not isinstance(dados_vazio, dict) or not dados_vazio:
        log.warning("Dados de perdas em vazio ausentes para formatação PDF.")
        return {}

    log.debug("Formatando perdas em vazio para PDF...")
    results_projeto = dados_vazio.get("resultados_projeto", {})
    results_m4 = dados_vazio.get("resultados_aco_m4", {})

    # Define precision and units for each key
    formatting_rules = {
        "Perdas em Vazio (kW)": {"prec": 2, "unit": "kW"},
        "Tensão nominal teste 1.0 pu (kV)": {"prec": 2, "unit": "kV"},
        "Corrente de excitação (A)": {"prec": 2, "unit": "A"},
        "Corrente de excitação calculada (A)": {"prec": 2, "unit": "A"},
        "Tensão de teste 1.1 pu (kV)": {"prec": 2, "unit": "kV"},
        "Corrente de excitação 1.1 pu (A)": {"prec": 2, "unit": "A"},
        "Tensão de teste 1.2 pu (kV)": {"prec": 2, "unit": "kV"},
        "Corrente de excitação 1.2 pu (A)": {"prec": 2, "unit": "A"},
        "Frequência (Hz)": {"prec": 2, "unit": "Hz"},
        "Potência Mag. (kVAr)": {"prec": 2, "unit": "kVAr"},
        "Fator de perdas Mag. (VAr/kg)": {"prec": 2, "unit": "VAr/kg"},
        "Fator de perdas (W/kg)": {"prec": 2, "unit": "W/kg"},
        "Peso do núcleo de projeto (Ton)": {"prec": 2, "unit": "Ton"},
        "Peso do núcleo Calculado(Ton)": {"prec": 2, "unit": "Ton"},
        "Potência de Ensaio (1 pu) (kVA)": {"prec": 2, "unit": "kVA"},
        "Potência de Ensaio (1.1 pu) (kVA)": {"prec": 2, "unit": "kVA"},
        "Potência de Ensaio (1.2 pu) (kVA)": {"prec": 2, "unit": "kVA"},
    }

    def format_section(data_dict):
        formatted = {}
        for key_orig, value in data_dict.items():
            if value is not None:
                rules = formatting_rules.get(
                    key_orig, {"prec": 2, "unit": ""}
                )  # Default formatting
                formatted[key_orig] = format_parameter_value(value, rules["prec"], rules["unit"])
        return formatted

    formatted_projeto = format_section(results_projeto)
    formatted_m4 = format_section(results_m4)

    final_data = {}
    if formatted_projeto:
        final_data["Resultados (Dados de Projeto)"] = formatted_projeto
    if formatted_m4:
        final_data["Resultados (Estimativa Aço M4)"] = formatted_m4

    return final_data if final_data else {}


def formatar_perdas_carga(dados_carga: dict | None) -> dict:
    """Formata dados de perdas em carga para estrutura PDF (tabelas list-of-lists)."""
    if not isinstance(dados_carga, dict) or "resultados" not in dados_carga:
        log.warning("Dados de perdas em carga ausentes para formatação PDF.")
        return {}

    log.debug("Formatando perdas em carga para PDF...")
    resultados = dados_carga.get("resultados", [])
    if not resultados or not isinstance(resultados, list):
        log.warning("Estrutura de 'resultados' em perdas carga inválida.")
        return {}

    # Mapas de chaves internas para nomes amigáveis e formatação
    # {'key': (Label, Precision, Unit)}
    map_nominal = {
        "tensao": ("Tensão", 2, "kV"),
        "corrente": ("Corrente", 2, "A"),
        "imp": ("Vcc (%)", 2, "%"),
        "vcc_kv": ("Vcc (kV)", 2, "kV"),
        "ptot_kw": ("Perdas Totais", 2, "kW"),
        "pc_frio_kw": ("Perdas CC Frio", 2, "kW"),
    }
    map_frio = {
        "vt_frio_kv": ("Tensão", 2, "kV"),
        "it_frio_a": ("Corrente", 2, "A"),
        "pteste_frio_mva": ("Pteste", 2, "MVA"),
        "vbanco_frio_kv": ("Cap Bank Tensão", 1, "kV"),
        "pbanco_frio_mvar": ("Cap Bank Pot.", 2, "MVAr"),
        "pa_eps_frio_kw": ("Pot. Ativa EPS", 1, "kW"),
    }
    map_quente = {
        "vt_quente_kv": ("Tensão", 2, "kV"),
        "it_quente_a": ("Corrente", 2, "A"),
        "pteste_quente_mva": ("Pteste", 2, "MVA"),
        "vbanco_quente_kv": ("Cap Bank Tensão", 1, "kV"),
        "pbanco_quente_mvar": ("Cap Bank Pot.", 2, "MVAr"),
        "pa_eps_quente_kw": ("Pot. Ativa EPS", 1, "kW"),
    }
    map_1_2 = {
        "vt_1.2_kv": ("Tensão", 2, "kV"),
        "it_1.2_a": ("Corrente", 2, "A"),
        "pteste_1.2_mva": ("Pteste", 2, "MVA"),
        "pc_1.2_kw": ("Perdas", 1, "kW"),
        "vbanco_1.2_kv": ("Cap Bank Tensão", 1, "kV"),
        "pbanco_1.2_mvar": ("Cap Bank Pot.", 2, "MVAr"),
        "pa_eps_1.2_kw": ("Pot. Ativa EPS", 1, "kW"),
    }
    map_1_4 = {
        "vt_1.4_kv": ("Tensão", 2, "kV"),
        "it_1.4_a": ("Corrente", 2, "A"),
        "pteste_1.4_mva": ("Pteste", 2, "MVA"),
        "pc_1.4_kw": ("Perdas", 1, "kW"),
        "vbanco_1.4_kv": ("Cap Bank Tensão", 1, "kV"),
        "pbanco_1.4_mvar": ("Cap Bank Pot.", 2, "MVAr"),
        "pa_eps_1.4_kw": ("Pot. Ativa EPS", 1, "kW"),
    }

    headers = ["Parâmetro", "Tap Nominal", "Tap Menor", "Tap Maior"]

    def build_pdf_table_data(mapping, results_list):
        """Constrói lista de listas para a tabela PDF, aplicando formatação."""
        table_data = []
        for data_key, (friendly_name, precision, unit) in mapping.items():
            row = [friendly_name]
            for i in range(3):  # Nominal, Menor, Maior
                val = results_list[i].get(data_key) if i < len(results_list) else None
                row.append(format_parameter_value(val, precision, unit))
            table_data.append(row)
        return table_data

    # Monta os dados para cada tabela
    data_nominal_pdf = [headers] + build_pdf_table_data(map_nominal, resultados)
    data_frio_pdf = [headers] + build_pdf_table_data(map_frio, resultados)
    data_quente_pdf = [headers] + build_pdf_table_data(map_quente, resultados)

    report_content = {
        "Condições Nominais": data_nominal_pdf,
        "Energização a Frio (Perdas Totais)": data_frio_pdf,
        "Condição a Quente": data_quente_pdf,
    }

    # Adiciona tabelas de sobrecarga se existirem
    has_overload = "vt_1.2_kv" in resultados[0] if resultados else False
    if has_overload:
        data_1_2_pdf = [headers] + build_pdf_table_data(map_1_2, resultados)
        data_1_4_pdf = [headers] + build_pdf_table_data(map_1_4, resultados)
        report_content["Sobrecarga 1.2 pu (4h)"] = data_1_2_pdf
        report_content["Sobrecarga 1.4 pu (0.5h)"] = data_1_4_pdf

    return report_content


def formatar_elevacao_temperatura(dados: dict | None) -> dict:
    """Formata dados de Elevação de Temperatura para estrutura PDF (Parameter:Value)."""
    if not isinstance(dados, dict):
        log.warning("Dados de elevação de temperatura ausentes para formatação PDF.")
        return {}

    log.debug("Formatando elevação temperatura para PDF...")
    inputs = dados.get("inputs_temp_rise", {})
    results = dados.get("resultados_temp_rise", {})

    # Map keys to friendly names and formatting rules {key: (Label, Precision, Unit)}
    input_map = {
        "input_ta": ("Temp. Ambiente (Θa)", 1, "°C"),
        "input_material": ("Material Enrolamento", 0, ""),
        "input_rc": ("Resistência Fria (Rc)", 3, "Ohm"),
        "input_tc": ("Temp. Ref. Fria (Θc)", 1, "°C"),
        "input_rw": ("Resistência Quente (Rw)", 3, "Ohm"),
        "input_t_oil": ("Temp. Topo Óleo Final (Θoil)", 1, "°C"),
        "input_delta_theta_oil_max": ("Elevação Máx Óleo (ΔΘoil_max)", 1, "K"),
    }
    result_map = {
        "constante_C": ("Constante Material (C)", 1, ""),
        "avg_winding_temp": ("Temp. Média Enrol. Final (Θw)", 1, "°C"),
        "avg_winding_rise": ("Elevação Média Enrol. (ΔΘw)", 1, "K"),
        "top_oil_rise": ("Elevação Topo Óleo (ΔΘoil)", 1, "K"),
        "ptot_used_kw": ("Perdas Totais Tap- Wt (Ptot)", 2, "kW"),
        "tau0_h": ("Const. Tempo Térmica (τ₀)", 2, "h"),
    }

    inputs_formatados = {}
    for key, (label, prec, unit) in input_map.items():
        value = inputs.get(key)  # Get value from inputs dict
        if value is not None:
            inputs_formatados[label] = format_parameter_value(value, prec, unit)

    resultados_formatados = {}
    for key, (label, prec, unit) in result_map.items():
        value = results.get(key)  # Get value from results dict
        if value is not None:
            resultados_formatados[label] = format_parameter_value(value, prec, unit)

    # Monta a estrutura final {Title: {Param: Val}}
    report_content = {}
    if inputs_formatados:
        report_content["Dados de Entrada"] = inputs_formatados
    if resultados_formatados:
        report_content["Resultados Calculados"] = resultados_formatados

    return report_content


def formatar_curto_circuito(dados: dict | None) -> dict:
    """Formata dados de Curto-Circuito para estrutura PDF (Parameter:Value)."""
    if not isinstance(dados, dict):
        log.warning("Dados de curto-circuito ausentes para formatação PDF.")
        return {}

    log.debug("Formatando curto-circuito para PDF...")
    inputs = dados.get("inputs_curto_circuito", {})
    results = dados.get("resultados_curto_circuito", {})

    # Map keys to friendly names and formatting rules {key: (Label, Precision, Unit)}
    input_map = {
        "impedance_before": ("Z Pré-Ensaio (Z_antes)", 4, "%"),
        "impedance_after": ("Z Pós-Ensaio (Z_depois)", 4, "%"),
        "peak_factor": ("Fator de Pico (k√2)", 2, ""),
        "category": ("Categoria (Potência)", 0, ""),
        "isc_side": ("Lado Cálculo Isc", 0, ""),
    }
    result_map = {
        "isc_sym_kA": ("Isc Simétrica (Isc)", 2, "kA"),
        "isc_peak_kA": ("Corrente de Pico (ip)", 2, "kA"),
        "delta_impedance_percent": ("Variação Impedância (ΔZ)", 2, "%"),
        "limit_used": ("Limite Normativo", 1, "%"),
        "status_text": ("Status Verificação", 0, ""),
    }

    inputs_formatados = {}
    for key, (label, prec, unit) in input_map.items():
        value = inputs.get(key)
        if value is not None:
            inputs_formatados[label] = format_parameter_value(value, prec, unit)

    resultados_formatados = {}
    for key, (label, prec, unit) in result_map.items():
        value = results.get(key)
        if value is not None:
            # Add ± sign for limit_used
            val_str = (
                f"±{format_parameter_value(value, prec, unit)}"
                if key == "limit_used"
                else format_parameter_value(value, prec, unit)
            )
            resultados_formatados[label] = val_str

    report_content = {}
    if inputs_formatados:
        report_content["Dados de Entrada"] = inputs_formatados
    if resultados_formatados:
        report_content["Resultados Calculados"] = resultados_formatados

    return report_content


def formatar_analise_dieletrica(dados: dict | None) -> dict:
    """Formata dados de Análise Dielétrica para estrutura PDF (múltiplas tabelas/seções)."""
    if not isinstance(dados, dict):
        log.warning("Dados de análise dielétrica ausentes para formatação PDF.")
        return {}

    log.debug("Formatando análise dielétrica para PDF...")
    params = dados.get("parametros", {})
    results = dados.get("resultados", {})
    enrolamentos_params = params.get("enrolamentos", [])
    enrolamentos_results = results.get("enrolamentos", [])
    ensaios_req = results.get("ensaios_requeridos", {})
    sequencias = results.get("sequencias_ensaio", {})

    report_content = {}

    # --- 1. Parâmetros Gerais e por Enrolamento ---
    general_params = {
        "Tipo Transformador": format_parameter_value(
            params.get("tipo_transformador"), none_value="N/A"
        ),
        "Tipo Isolamento": format_parameter_value(params.get("tipo_isolamento"), none_value="N/A"),
    }
    report_content["Parâmetros Gerais"] = general_params

    input_headers = [
        "Enrolamento",
        "Um (kV)",
        "Conexão",
        "IA (kV)",
        "IM (kV)",
        "T.Aplicada (kV)",
        "Um Neutro (kV)",
        "IA Neutro (kV)",
    ]
    input_table_data = [input_headers]
    has_input_data = False
    for enrol in enrolamentos_params:
        if enrol.get("um"):  # Inclui apenas se Um foi definido
            input_table_data.append(
                [
                    format_parameter_value(enrol.get("nome"), none_value="-"),
                    format_parameter_value(enrol.get("um"), 1, "kV", "-"),  # Precisão 1 para kV
                    format_parameter_value(enrol.get("conexao"), none_value="-"),
                    format_parameter_value(
                        enrol.get("ia"), 0, "kV", "-"
                    ),  # Precisão 0 para IA/IM/Aplicada
                    format_parameter_value(enrol.get("im"), 0, "kV", "-"),
                    format_parameter_value(enrol.get("tensao_curta"), 0, "kV", "-"),
                    format_parameter_value(enrol.get("neutro_um"), 1, "kV", "-")
                    if enrol.get("conexao") == "YN"
                    else "-",
                    format_parameter_value(enrol.get("ia_neutro"), 0, "kV", "-")
                    if enrol.get("conexao") == "YN"
                    else "-",
                ]
            )
            has_input_data = True
    if has_input_data:
        report_content["Parâmetros Dielétricos Definidos"] = input_table_data

    # --- 2. Resultados Calculados (Espaçamentos e IAC) ---
    results_headers = [
        "Enrolamento",
        "IAC (kV)",
        "Esp. F-T NBR (mm)",
        "Esp. F-F NBR (mm)",
        "Esp. Outro NBR (mm)",
        "Clearance IEEE (mm)",
    ]
    results_table_data = [results_headers]
    has_results_data = False
    for i, enrol_res in enumerate(enrolamentos_results):
        # Apenas adiciona se o enrolamento correspondente tinha dados de entrada
        if i < len(enrolamentos_params) and enrolamentos_params[i].get("um"):
            # IAC valor é string (pode ter NBR/IEEE), não formatar como número
            iac_str = enrol_res.get("impulso_cortado", {}).get("valor_str", "-")
            esp = enrol_res.get("espacamentos", {})
            esp_nbr = esp.get("NBR", {}) or {}
            esp_ieee = esp.get("IEEE", {}) or {}

            results_table_data.append(
                [
                    format_parameter_value(enrol_res.get("nome"), none_value="-"),
                    iac_str,  # Usa a string salva
                    format_parameter_value(esp_nbr.get("fase_terra"), 1, "mm", "-"),
                    format_parameter_value(esp_nbr.get("fase_fase"), 1, "mm", "-"),
                    format_parameter_value(esp_nbr.get("outro_enrolamento"), 1, "mm", "-"),
                    format_parameter_value(esp_ieee.get("clearance"), 1, "mm", "-"),
                ]
            )
            has_results_data = True
    if has_results_data:
        report_content["Resultados Calculados (Espaçamentos e IAC)"] = results_table_data

    # --- 3. Ensaios Requeridos (Comparativo) ---
    if ensaios_req and (ensaios_req.get("NBR") or ensaios_req.get("IEEE")):
        nbr_req = ensaios_req.get("NBR", {})
        ieee_req = ensaios_req.get("IEEE", {})
        mapping = {  # Label: (Chave NBR, Chave IEEE)
            "Impulso Atmosférico": ("impulso_atmosferico", "bil_test"),
            "Impulso Onda Cortada": ("impulso_atmosferico_onda_cortada", "chopped_wave_test"),
            "Impulso Manobra": ("impulso_manobra", "switching_impulse_test"),
            "Tensão Induzida Curta": ("tensao_induzida_curta", "induced_voltage_test"),
            "Tensão Induzida Longa": ("tensao_induzida_longa", None),
            "Tensão Aplicada": ("tensao_aplicada", "applied_voltage_test"),
        }
        req_headers = ["Ensaio", "NBR 5356-3", "IEEE C57.12.00"]
        req_table_data = [req_headers]
        for label, (nbr_key, ieee_key) in mapping.items():
            nbr_val = nbr_req.get(nbr_key, "-") if nbr_req else "-"
            ieee_val = ieee_req.get(ieee_key, "-") if ieee_req and ieee_key else "-"
            req_table_data.append([label, nbr_val, ieee_val])
        report_content["Ensaios Requeridos (Comparativo Normas)"] = req_table_data

    # --- 4. Sequências de Ensaio Induzido (NBR) ---
    seq_content = {}  # Usar dicionário para subseções
    if sequencias:

        def format_seq_table_pdf(seq_data):
            if not seq_data or not seq_data.get("patamares"):
                return None
            table_headers = ["Nível", "Tensão (kV)", "Tempo"]
            table_rows = []
            for p in seq_data["patamares"]:
                table_rows.append(
                    [
                        format_parameter_value(p.get("nivel"), none_value="-"),
                        format_parameter_value(p.get("tensao"), 1, "kV", "-"),  # Precisão 1 para kV
                        format_parameter_value(p.get("tempo"), none_value="-"),
                    ]
                )
            # Add DP limits if available
            dp_limits = seq_data.get("parametros", {}).get("medicao_dp", {}).get("limites", {})
            if dp_limits:
                table_rows.append(["Limites DP:", "", ""])  # Span visualmente no PDF
                for k, v in dp_limits.items():
                    label_k = k.replace("_", " ").title()
                    table_rows.append([f"- {label_k}", format_parameter_value(v, 1, "kV", "-"), ""])
            return [table_headers] + table_rows

        seq_mono = format_seq_table_pdf(sequencias.get("monofasico"))
        seq_tri_curta = format_seq_table_pdf(sequencias.get("trifasico_curta"))
        seq_tri_longa = format_seq_table_pdf(sequencias.get("trifasico_longa"))

        if seq_mono:
            seq_content["Ensaio Monofásico"] = seq_mono
        if seq_tri_curta:
            seq_content["Ensaio Trifásico Curta Duração"] = seq_tri_curta
        if seq_tri_longa:
            seq_content["Ensaio Trifásico Longa Duração"] = seq_tri_longa

    if seq_content:
        report_content[
            "Sequências de Ensaio Induzido (NBR)"
        ] = seq_content  # Cria seção com subseções

    return report_content


def formatar_tensao_aplicada(dados: dict | None) -> dict:
    """Formata dados de Tensão Aplicada para estrutura PDF (múltiplas tabelas)."""
    if not isinstance(dados, dict) or "resultados" not in dados:
        log.warning("Dados de tensão aplicada ausentes para formatação PDF.")
        return {}

    log.debug("Formatando tensão aplicada para PDF...")
    resultados = dados.get("resultados", {})
    dados_calculo = resultados.get("dados_calculo", {})
    analise_enrolamentos = dados_calculo.get("analise_enrolamentos", [])

    report_content = {}

    # --- Tabela de Dados Calculados ---
    # Estrutura: [ [Header], [Row AT], [Row BT], [Row Ter] ]
    calc_headers = ["Parâmetro", "AT", "BT", "Terciário"]
    calc_table_data = [calc_headers]
    # Parâmetros a extrair e formatar {internal_key: (Label, Precision, Unit)}
    params_to_extract = {
        "tensao_kv": ("Tensão Ensaio", 2, "kV"),
        "capacitancia_nf": ("Cap. Ensaio", 2, "nF"),
        "corrente_ma": ("Corrente", 2, "mA"),
        "zc_ohm": ("Zc", 1, "Ω"),
        "pot_kvar": ("Potência Reativa", 3, "kVAr"),
    }
    # Extrair dados por enrolamento da análise
    data_by_winding = {enr.get("enrolamento"): enr for enr in analise_enrolamentos}
    # Adiciona dados calculados que não estão na análise (ex: Zc, Pot)
    if "AT" in data_by_winding:
        data_by_winding["AT"]["corrente_ma"] = dados_calculo.get("i_at")
        data_by_winding["AT"]["zc_ohm"] = dados_calculo.get("zc_at")
        data_by_winding["AT"]["pot_kvar"] = dados_calculo.get("p_at")
    if "BT" in data_by_winding:
        data_by_winding["BT"]["corrente_ma"] = dados_calculo.get("i_bt")
        data_by_winding["BT"]["zc_ohm"] = dados_calculo.get("zc_bt")
        data_by_winding["BT"]["pot_kvar"] = dados_calculo.get("p_bt")
    if "Terciário" in data_by_winding:
        data_by_winding["Terciário"]["corrente_ma"] = dados_calculo.get("i_ter")
        data_by_winding["Terciário"]["zc_ohm"] = dados_calculo.get("zc_ter")
        data_by_winding["Terciário"]["pot_kvar"] = dados_calculo.get("p_ter")

    # Monta as linhas da tabela
    for key, (label, precision, unit) in params_to_extract.items():
        row = [label]
        for winding_name in ["AT", "BT", "Terciário"]:
            winding_data = data_by_winding.get(winding_name)
            value = winding_data.get(key) if winding_data else None
            row.append(format_parameter_value(value, precision, unit, "-"))
        calc_table_data.append(row)

    if len(calc_table_data) > 1:
        report_content["Dados Calculados"] = calc_table_data

    # --- Tabela de Análise de Viabilidade ---
    viab_headers = ["Enrolamento", "Config. Recomendada", "Viabilidade"]
    viab_table_data = [viab_headers]
    has_viab_data = False
    for enr in analise_enrolamentos:
        # Simplifica a tabela para o PDF, recomendação vai como nota talvez
        viab_table_data.append(
            [
                format_parameter_value(enr.get("enrolamento"), none_value="-"),
                format_parameter_value(enr.get("resonant_config"), none_value="-"),
                format_parameter_value(enr.get("viabilidade"), none_value="-"),
            ]
        )
        has_viab_data = True
    if has_viab_data:
        report_content["Análise de Viabilidade (Sistema Ressonante)"] = viab_table_data
        # Adiciona recomendações como texto extra (ou nota de rodapé no PDF)
        recommendations_text = "\n".join(
            [
                f"- {enr.get('enrolamento')}: {enr.get('recommendation', '')}"
                for enr in analise_enrolamentos
            ]
        )
        report_content["Notas de Viabilidade"] = recommendations_text  # Adiciona como texto simples

    return report_content


def formatar_tensao_induzida(dados: dict | None) -> dict:
    """Formata dados de Tensão Induzida para estrutura PDF (Parameter:Value)."""
    if not isinstance(dados, dict) or "resultados_tensao_induzida" not in dados:
        log.warning("Dados de tensão induzida ausentes para formatação PDF.")
        return {}

    log.debug("Formatando tensão induzida para PDF...")
    resultados = dados.get("resultados_tensao_induzida", {})
    dados_calculo = resultados.get("dados_calculo", {})
    tipo_transformador = dados.get("inputs_tensao_induzida", {}).get(
        "tipo_transformador", "Desconhecido"
    )

    report_content = {}
    calc_data_formatted = {}  # Dicionário para parâmetro-valor formatado

    # Define mapas com regras de formatação {key: (Label, Precision, Unit)}
    map_mono = {
        "tensao_aplicada_bt": ("Tensão Aplicada BT", 2, "kV"),
        "up_un": ("Up/Un", 3, ""),
        "fp_fn": ("Fp/fn", 3, ""),
        "beta_teste": ("βteste", 3, "T"),
        "pot_ativa": ("Potência Ativa Pw", 2, "kW"),
        "pot_magnetica": ("Pot. Aparente Magnética Sm", 2, "kVA"),
        "pot_induzida": ("Comp. Indutiva Qm", 2, "kVAr ind"),
        "u_dif": ("U p/ cálculo Scap", 2, "kV"),
        "pcap": ("Pot. Capacitiva Scap", 2, "kVAr cap"),
        "fator_potencia_mag": ("Fator Pot. Mag.", 3, "VAr/kg"),
        "fator_perdas": ("Fator Perdas", 3, "W/kg"),
    }
    map_tri = {
        "tensao_aplicada_bt": ("Tensão Aplicada BT", 2, "kV"),
        "pot_magnetica": ("Potência Magnética", 1, "kVA"),
        "fator_perdas": ("Fator Perdas", 3, "W/kg"),
        "fator_potencia_mag": ("Fator Pot. Mag.", 3, "VAr/kg"),  # Confirmar unidade
        "corrente_excitacao": ("Corrente Excitação", 3, "A"),
        "potencia_teste": ("Potência de Teste", 1, "kVA"),
    }

    current_map = map_mono if tipo_transformador == "Monofásico" else map_tri

    for key, (label, prec, unit) in current_map.items():
        value = dados_calculo.get(key)
        if value is not None:
            calc_data_formatted[label] = format_parameter_value(value, prec, unit)

    if calc_data_formatted:
        report_content[f"Resultados Calculados ({tipo_transformador})"] = calc_data_formatted

    return report_content


def formatar_impulso(dados: dict | None) -> dict:
    """Formata dados de Impulso para estrutura PDF (múltiplas seções Parameter:Value)."""
    if not isinstance(dados, dict) or "simulation" not in dados:
        log.warning("Dados de impulso ausentes ou incompletos para formatação PDF.")
        return {}

    log.debug("Formatando impulso para PDF...")
    sim_data = dados.get("simulation", {})
    sim_inputs = sim_data.get("inputs", {})
    sim_analysis = sim_data.get("analysis", {})
    sim_compliance_msg = sim_data.get("compliance_msg", "Indeterminado")
    sim_energy = sim_data.get("energy", {})
    sim_circuit = sim_data.get("circuit_params", {})
    sim_voltages = sim_data.get("voltages", {})
    sim_efficiency = sim_data.get("efficiency", {})
    sim_type = sim_inputs.get("type", "Desconhecido").capitalize()

    report_content = {}
    sub_sections = {}  # Dicionário para as subseções

    # --- Inputs da Simulação ---
    # {key: (Label, Precision, Unit)}
    input_map = {
        "gen": ("Config. Gerador", 0, ""),
        "v_test_target": ("V Teste Alvo", 1, "kV"),
        "c_dut": ("Carga DUT", 0, "pF"),
        "c_stray": ("Carga Parasita", 0, "pF"),
        "l_ext_h": ("L Externa Total", 1, "µH"),  # Converte H para µH
        "l_trafo_h": ("L Trafo", 4, "H"),
        "l_add_h": ("L Adicional", 1, "µH"),  # Converte H para µH
        "shunt": ("Shunt Medição", 3, "Ω"),
        "gap_cm": ("Distância Gap", 1, "cm"),
        "simulation_model": ("Modelo Simulação", 0, ""),
    }
    sim_section_inputs = {}
    for key_orig, (label, precision, unit) in input_map.items():
        value = sim_inputs.get(key_orig)
        # Conversão de unidades para µH
        if key_orig in ["l_ext_h", "l_add_h"] and value is not None:
            value *= 1e6
        if value is not None:
            sim_section_inputs[label] = format_parameter_value(value, precision, unit, "-")

    # Adiciona resistores (expressão original)
    sim_section_inputs["Resistor Frente"] = sim_inputs.get("rf_expr", "N/A")
    sim_section_inputs["Resistor Cauda"] = sim_inputs.get("rt_expr", "N/A")
    if sim_section_inputs:
        sub_sections["Inputs Simulação"] = sim_section_inputs

    # --- Parâmetros Simulados (Resultados da Análise) ---
    # {key: (Label, Precision, Unit)}
    analysis_map_li = {
        "peak_value_test": ("Vt (Pico Ensaio)", 1, "kV"),
        "t_front_us": ("T1 (Frente)", 2, "µs"),
        "t_tail_us": ("T2 (Cauda)", 1, "µs"),
        "overshoot_percent": ("Overshoot β", 1, "%"),
        "peak_time_test_us": ("Tempo Pico Vt", 2, "µs"),
        "t_0_virtual_us": ("Origem Virtual O1", 2, "µs"),
    }
    analysis_map_si = {
        "peak_value_measured": ("Vp (Pico Medido)", 1, "kV"),
        "t_p_us": ("Tp (Tempo Pico Norma)", 0, "µs"),
        "t_2_us": ("T2 (Meio Valor)", 0, "µs"),
        "td_us": ("Td (>90%)", 0, "µs"),
        "t_zero_us": ("Tz (Zero)", 0, "µs"),
        "peak_time_us": ("Tempo Pico Abs", 1, "µs"),
    }
    analysis_map_lic = {
        "chop_voltage_test_kv": ("Vc Teste", 1, "kV"),
        "t_front_us": ("T1 Subj", 2, "µs"),
        "chop_time_us": ("Tc", 2, "µs"),
        "undershoot_percent": ("Undershoot", 1, "%"),
        "peak_value_full_wave_test": ("Vt Subj", 1, "kV"),
        "chop_time_absolute_us": ("Tempo Corte Abs", 2, "µs"),
        "t_0_virtual_us": ("Origem Virtual O1", 2, "µs"),
    }
    analysis_map = {}
    if sim_type == "Lightning":
        analysis_map = analysis_map_li
    elif sim_type == "Switching":
        analysis_map = analysis_map_si
    elif sim_type == "Chopped":
        analysis_map = analysis_map_lic

    sim_section_analysis = {}
    for key_orig, (label, precision, unit) in analysis_map.items():
        value = sim_analysis.get(key_orig)
        if value is not None:
            sim_section_analysis[label] = format_parameter_value(value, precision, unit, "-")

    sim_section_analysis["Conformidade Geral"] = sim_compliance_msg  # Status textual
    if sim_section_analysis:
        sub_sections["Parâmetros Simulados"] = sim_section_analysis

    # --- Parâmetros do Circuito ---
    # {key: (Label, Precision, Unit)}
    circuit_map = {
        "cg_nf": ("Cg Efetiva", 3, "nF"),
        "cl_pf": ("Cl Total", 0, "pF"),
        "ceq_nf": ("Ceq", 3, "nF"),
        "rf_total_ohm": ("Rf Efetiva", 2, "Ω"),
        "rt_total_ohm": ("Rt Efetiva", 2, "Ω"),
        "l_total_h": ("L Total", 3, "mH"),  # Converte para mH
        "alpha": ("α Calculado", 2, "s⁻¹"),
        "beta": ("β Calculado", 2, "s⁻¹"),
        "zeta": ("ζ Calculado", 3, ""),
        "charge_kv": ("V Carga Gerador", 1, "kV"),
        "actual_kv_simulated": ("V Pico/Corte Real", 1, "kV"),
        "shunt_max_v": ("V Máx Shunt", 1, "V"),
    }
    sim_section_circuit = {}
    # Precisa buscar valores de diferentes sub-dicionários
    circuit_values = {**sim_circuit, **sim_voltages}  # Combina dicionários
    for key_orig, (label, precision, unit) in circuit_map.items():
        value = circuit_values.get(key_orig)
        # Conversão de L para mH
        if key_orig == "l_total_h" and value is not None:
            value *= 1000
        if value is not None:
            sim_section_circuit[label] = format_parameter_value(value, precision, unit, "-")
    if sim_circuit.get("is_oscillatory"):
        sim_section_circuit["Aviso Oscilação"] = "Circuito Subamortecido (ζ<1)"
    if sim_section_circuit:
        sub_sections["Parâmetros Circuito"] = sim_section_circuit

    # --- Eficiência ---
    eff_map = {
        "circuit": ("Eficiência Circuito", 1, "%"),
        "shape": ("Eficiência Forma", 1, "%"),
        "total": ("Eficiência TOTAL", 1, "%"),
    }
    sim_section_eff = {}
    for key, (label, prec, unit) in eff_map.items():
        value = sim_efficiency.get(key)
        if value is not None:
            sim_section_eff[label] = format_parameter_value(
                value * 100, prec, unit
            )  # Multiplica por 100
    if sim_section_eff:
        sub_sections["Eficiência"] = sim_section_eff

    # --- Energia ---
    energy_map = {
        "req_kj": ("Energia Requerida", 2, "kJ"),
        "avail_kj": ("Energia Disponível", 1, "kJ"),
        "ok": ("Energia Suficiente?", 0, ""),
    }
    sim_section_energy = {}
    for key_orig, (label, precision, unit) in energy_map.items():
        value = sim_energy.get(key_orig)
        if value is not None:
            sim_section_energy[label] = format_parameter_value(value, precision, unit, "-")
    if sim_section_energy:
        sub_sections["Energia"] = sim_section_energy

    # Adiciona a seção principal ao relatório final
    if sub_sections:
        report_content[f"Simulação {sim_type}"] = sub_sections

    return report_content
