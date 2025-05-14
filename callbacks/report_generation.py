# callbacks/report_generation.py
""" Callback para gerar o relatório PDF consolidado. """

import datetime
import logging
import traceback
from io import BytesIO

from dash import Input, Output, State, dcc

# Importações da aplicação
from app import app  # Apenas 'app' é necessário
from components.formatters import (
    formatar_analise_dieletrica,
    formatar_curto_circuito,
    formatar_dados_basicos,
    formatar_elevacao_temperatura,
    formatar_impulso,
    formatar_perdas_carga,
    formatar_perdas_vazio,
    formatar_tensao_aplicada,
    formatar_tensao_induzida,
)
from utils.pdf_generator import generate_pdf

log = logging.getLogger(__name__)


@app.callback(
    Output("download-pdf", "data"),
    Input("generate-report-btn", "n_clicks"),
    [
        State("transformer-inputs-store", "data"),
        State("losses-store", "data"),
        State("impulse-store", "data"),
        State("dieletric-analysis-store", "data"),
        State("applied-voltage-store", "data"),
        State("induced-voltage-store", "data"),
        State("short-circuit-store", "data"),
        State("temperature-rise-store", "data"),
        State("limit-status-store", "data"),
    ],  # State para o limite
    prevent_initial_call=True,
)
def report_generation_generate_pdf(
    n_clicks,
    basic_data,
    losses_data,
    impulse_data,
    dieletric_data,
    applied_data,
    induced_data,
    short_circuit_data,
    temp_rise_data,
    limit_status_data,
):  # Argumento para o limite
    """Gera o relatório PDF."""

    limite_atingido = True  # Default
    if isinstance(limit_status_data, dict):
        limite_atingido = limit_status_data.get("limite_atingido", True)
    else:
        log.warning("Formato inesperado para limit_status_data. Assumindo limite atingido.")
        print("[report_generation.py] WARN: limit_status_data não é dict.")  # PRINT

    print(
        f"[report_generation.py] Callback acionado. n_clicks={n_clicks}, limite_atingido={limite_atingido}"
    )  # PRINT
    log.debug(
        f"Generate report callback triggered. Clicks: {n_clicks}, Limit hit: {limite_atingido}"
    )

    if n_clicks is None or limite_atingido:
        log.warning(f"Geração PDF prevenida (clicks={n_clicks}, limite={limite_atingido}).")
        print("[report_generation.py] Geração prevenida.")  # PRINT
        return None

    log.info("=" * 50)
    log.info("=== INICIANDO GERAÇÃO PDF ===")
    log.info("=" * 50)
    print("[report_generation.py] Iniciando formatação...")  # PRINT

    all_data = {
        "basic": basic_data or {},
        "losses": losses_data or {},
        "impulse": impulse_data or {},
        "dieletric": dieletric_data or {},
        "applied": applied_data or {},
        "induced": induced_data or {},
        "short_circuit": short_circuit_data or {},
        "temp_rise": temp_rise_data or {},
    }

    report_data_formatted = {}
    format_errors = []

    def format_section(section_name, data, formatter_func, *args):
        # ... (lógica de format_section como antes, com logs) ...
        nonlocal format_errors
        if data and isinstance(data, dict):
            try:
                log.debug(f"Formatando seção '{section_name}'...")
                formatted_content = formatter_func(data, *args)
                if formatted_content and isinstance(formatted_content, dict):
                    report_data_formatted.update(formatted_content)
                    log.info(
                        f"Seção '{section_name}' formatada. Chaves: {list(formatted_content.keys())}"
                    )
                elif not formatted_content:
                    log.info(f"Seção '{section_name}' formatada, conteúdo vazio.")
                else:
                    log.warning(
                        f"Formatador '{section_name}' tipo inesperado: {type(formatted_content)}"
                    )
                    format_errors.append(f"Formatação '{section_name}': tipo retorno inesperado.")
            except Exception as e_fmt:
                log.exception(f"Erro formatando seção '{section_name}': {e_fmt}")
                format_errors.append(f"Erro formatação '{section_name}': {e_fmt}")
                report_data_formatted[f"Erro - {section_name}"] = {
                    "Erro": f"Falha formatar: {e_fmt}"
                }
        else:
            log.info(f"Dados seção '{section_name}' não disponíveis/inválidos.")

    # Formata todas as seções
    format_section("Dados Básicos", all_data["basic"], formatar_dados_basicos)
    # ... (formatação das outras seções, incluindo Perdas) ...
    losses_report_section = {}
    if all_data["losses"]:
        try:
            vazio = formatar_perdas_vazio(all_data["losses"])
            if vazio:
                losses_report_section.update(vazio)
        except Exception as e:
            log.exception(f"Erro formatando vazio: {e}")
            format_errors.append(f"Erro P.Vazio:{e}")
        try:
            carga = formatar_perdas_carga(all_data["losses"])
            if carga:
                losses_report_section.update(carga)
        except Exception as e:
            log.exception(f"Erro formatando carga: {e}")
            format_errors.append(f"Erro P.Carga:{e}")
    if losses_report_section:
        report_data_formatted["Resultados de Perdas"] = losses_report_section

    format_section("Elevação de Temperatura", all_data["temp_rise"], formatar_elevacao_temperatura)
    format_section(
        "Suportabilidade a Curto-Circuito", all_data["short_circuit"], formatar_curto_circuito
    )
    format_section("Análise Dielétrica", all_data["dieletric"], formatar_analise_dieletrica)
    format_section("Tensão Aplicada", all_data["applied"], formatar_tensao_aplicada)
    format_section("Tensão Induzida", all_data["induced"], formatar_tensao_induzida)
    format_section("Resultados de Impulso", all_data["impulse"], formatar_impulso)

    if not report_data_formatted:
        log.warning("Nenhum dado formatado para PDF.")
        print("[report_generation.py] Nenhum dado formatado.")  # PRINT
        return None

    if format_errors:
        log.warning(f"Erros durante formatação: {format_errors}")
        print(f"[report_generation.py] Erros de formatação: {format_errors}")  # PRINT

    # --- Geração do PDF ---
    try:
        log.info("--- Iniciando criação do buffer PDF ---")
        print("[report_generation.py] Iniciando generate_pdf...")  # PRINT
        pdf_buffer = BytesIO()
        generate_pdf(report_data_formatted, pdf_buffer)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()
        log.info(f"--- PDF Buffer preenchido. Tamanho: {len(pdf_bytes)} bytes ---")
        print(f"[report_generation.py] PDF gerado. Tamanho: {len(pdf_bytes)} bytes")  # PRINT

        if len(pdf_bytes) == 0:
            log.warning("!!! generate_pdf retornou buffer vazio! !!!")
            print("[report_generation.py] ERRO: PDF gerado está vazio!")  # PRINT
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_simulacao_{timestamp}.pdf"
        log.info(f"--- Enviando PDF: {filename} ---")
        print(f"[report_generation.py] Enviando arquivo: {filename}")  # PRINT
        return dcc.send_bytes(pdf_bytes, filename)

    except Exception as e:
        log.exception(f"!!! ERRO CRÍTICO GERAÇÃO PDF: {str(e)} !!!")
        print(f"[report_generation.py] ERRO CRÍTICO GERAÇÃO PDF: {e}")  # PRINT
        print(traceback.format_exc())  # PRINT traceback
        return None
    finally:
        log.info("=" * 50)
        log.info("=== FIM TENTATIVA GERAÇÃO PDF ===")
        log.info("=" * 50)
        print("[report_generation.py] Fim do callback.")  # PRINT
