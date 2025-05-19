# utils/pdf_generator.py
import datetime
import html  # For escaping text in paragraphs
import logging
from io import BytesIO

from reportlab.lib import colors as reportlab_colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Importar configurações e cores
import config

log = logging.getLogger(__name__)


# --- Helper Flowable for Horizontal Line ---
class HRFlowable(Flowable):
    """Draws a horizontal line"""

    def __init__(
        self, width, thickness=0.5, color=reportlab_colors.grey, spaceBefore=2, spaceAfter=2
    ):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color
        self.spaceBefore = spaceBefore * mm  # Convert mm to points
        self.spaceAfter = spaceAfter * mm  # Convert mm to points

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        y = -self.spaceBefore  # Start drawing below the current line position
        self.canv.line(0, y, self.width, y)

    def wrap(self, availWidth, availHeight):
        # The space it occupies vertically
        return (self.width, self.spaceBefore + self.thickness + self.spaceAfter)


# --- Funções Auxiliares para Geração do PDF ---


def add_page_number(canvas, doc):
    """Adiciona número da página, data/hora e título no rodapé de cada página."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)  # Slightly smaller font for footer
    page_num_text = f"Página {doc.page}"
    # Draw page number on the right, slightly higher
    canvas.drawRightString(doc.width + doc.leftMargin - 0.5 * inch, 0.5 * inch, page_num_text)
    # Draw generation time on the left
    generation_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    canvas.drawString(doc.leftMargin, 0.5 * inch, f"Gerado em: {generation_time}")
    # Optionally add App Title in the center (can be omitted if too busy)
    # canvas.drawCentredString(doc.width/2 + doc.leftMargin, 0.5*inch, config.APP_TITLE)
    canvas.restoreState()


def create_styled_paragraph(text, style):
    """Creates a ReportLab Paragraph, handling None and escaping HTML."""
    text_str = str(text) if text is not None else ""
    # Escape HTML chars and replace newlines with <br/> for ReportLab
    escaped_text = html.escape(text_str).replace("\n", "<br/>")
    return Paragraph(escaped_text, style)


def create_pdf_table(table_data, col_widths=None, title="Tabela", styles=None, doc_width=None):
    """
    Creates a ReportLab Table with consistent styling from list-of-lists or dict.

    Args:
        table_data (list or dict): Data for the table. List-of-lists (header first) or Dict (Param:Val).
        col_widths (list, optional): List of column widths. Defaults to reasonable distribution.
        title (str): Title used for logging errors.
        styles (dict): Dictionary containing paragraph styles ('TableHeader', 'TableCellLeft', etc.).
        doc_width(float): Available width from the document (needed for default col widths).

    Returns:
        Table object or None if error.
    """
    if not table_data:
        log.warning(f"Tentando criar tabela '{title}' sem conteúdo.")
        return None
    if not styles or not doc_width:
        log.error("Styles ou doc_width faltando para create_pdf_table.")
        return None  # Cannot create table without styles/width

    table_header_style = styles.get("TableHeader")
    table_cell_style_left = styles.get("TableCellLeft")
    table_cell_style_right = styles.get("TableCellRight")
    if not all([table_header_style, table_cell_style_left, table_cell_style_right]):
        log.error("Estilos de parágrafo da tabela ausentes.")
        return None

    formatted_table_data = []
    num_cols = 0

    # Handle Dictionary (Parameter-Value pairs)
    if isinstance(table_data, dict):
        num_cols = 2
        # Add standard headers
        headers = [
            create_styled_paragraph("Parâmetro", table_header_style),
            create_styled_paragraph("Valor", table_header_style),
        ]
        formatted_table_data.append(headers)
        # Sort items for consistent order (optional)
        sorted_items = sorted(table_data.items())
        for k, v in sorted_items:
            # Format key and value using the styles
            key_p = create_styled_paragraph(k, table_cell_style_left)
            val_p = create_styled_paragraph(
                v, table_cell_style_right
            )  # Assume values are right-aligned
            formatted_table_data.append([key_p, val_p])

    # Handle List of Lists (assuming first row is header)
    elif (
        isinstance(table_data, list)
        and table_data
        and all(isinstance(row, list) for row in table_data)
    ):
        if not table_data[0]:  # Check if header row is empty
            log.warning(f"Cabeçalho vazio para tabela '{title}'.")
            return None
        num_cols = len(table_data[0])
        # Format header row
        headers = [create_styled_paragraph(h, table_header_style) for h in table_data[0]]
        formatted_table_data.append(headers)
        # Format data rows
        for row_idx, row in enumerate(table_data[1:]):
            if len(row) == num_cols:
                # Left-align first column, right-align others
                formatted_row = [create_styled_paragraph(row[0], table_cell_style_left)]
                formatted_row.extend(
                    [create_styled_paragraph(cell, table_cell_style_right) for cell in row[1:]]
                )
                formatted_table_data.append(formatted_row)
            else:
                log.warning(
                    f"Linha {row_idx+1} com {len(row)} colunas (esperado {num_cols}) ignorada na tabela '{title}': {row}"
                )

    else:
        log.error(f"Formato de dados inesperado para tabela '{title}': {type(table_data)}")
        return None

    if len(formatted_table_data) <= 1:  # Only header or empty
        log.warning(f"Tabela '{title}' não contém dados válidos.")
        return None

    # --- Column Width Calculation ---
    if col_widths:
        if len(col_widths) != num_cols:
            log.warning(
                f"Número de col_widths ({len(col_widths)}) != colunas ({num_cols}) para '{title}'. Usando distribuição padrão."
            )
            col_widths = None  # Force recalculation
        elif sum(col_widths) > doc_width + 1:  # Allow small tolerance
            log.warning(
                f"Soma de col_widths ({sum(col_widths)}) excede largura da página ({doc_width}) para '{title}'. Usando distribuição padrão."
            )
            col_widths = None

    if not col_widths:  # Calculate default widths if needed
        if num_cols == 2:
            col_widths = [doc_width * 0.45, doc_width * 0.55]  # Default for Param-Value
        elif num_cols > 0:
            col_widths = [doc_width / num_cols] * num_cols  # Equal distribution
        else:
            return None  # Should not happen

    # --- Create and Style Table ---
    table = Table(formatted_table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    reportlab_colors.HexColor(config.colors.get("reportlab_header_bg", "#26427A")),
                ),
                ("TEXTCOLOR", (0, 0), (-1, 0), reportlab_colors.white),  # Use white directly
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    reportlab_colors.HexColor(config.colors.get("reportlab_cell_bg", "#F8F9FA")),
                ),
                ("TEXTCOLOR", (0, 1), (-1, -1), reportlab_colors.black),  # Use black directly
                ("ALIGN", (0, 1), (0, -1), "LEFT"),  # First column left
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),  # Other columns right
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),  # Slightly smaller cell font
                ("TOPPADDING", (0, 1), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    reportlab_colors.HexColor(config.colors.get("reportlab_grid", "#ADB5BD")),
                ),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


# --- Função Principal de Geração de PDF ---


def generate_pdf(report_data_formatted: dict, buffer: BytesIO):
    """
    Gera o relatório PDF a partir dos dados já formatados pelos formatters.

    Args:
        report_data_formatted (dict): Dicionário onde chaves são títulos de seção
                                      e valores são os dados formatados (dict ou list-of-lists)
                                      ou outro dicionário para subseções.
        buffer (BytesIO): Objeto BytesIO onde o PDF será escrito.
    """
    log.info("Iniciando construção do documento PDF...")
    if not isinstance(report_data_formatted, dict):
        log.error("Erro: Dados para PDF (report_data_formatted) não são um dicionário.")
        # Tentativa de escrever erro no buffer
        try:
            doc_err = SimpleDocTemplate(buffer, pagesize=portrait(letter))
            elements_err = [Paragraph("Erro interno: Formato de dados inválido para gerar PDF.")]
            doc_err.build(elements_err)
        except Exception:
            pass  # Ignora se nem isso funcionar
        return

    try:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=portrait(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.75 * inch,
            bottomMargin=1.0 * inch,
        )  # Margem inferior maior para footer
        elements = []
        styles = getSampleStyleSheet()
        doc_width = doc.width  # Largura útil (pagesize - margins)

        # --- Definir Estilos do PDF ---
        # (Usar cores do config.py)
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["h1"],
            alignment=TA_CENTER,
            spaceAfter=12,
            fontSize=16,
            textColor=reportlab_colors.HexColor(config.colors.get("reportlab_primary", "#26427A")),
        )
        section_title_style = ParagraphStyle(
            name="SectionTitle",
            parent=styles["h2"],
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=4,
            fontSize=12,
            leading=14,
            textColor=reportlab_colors.HexColor(config.colors.get("reportlab_primary", "#26427A")),
            borderPadding=2,
        )
        subsection_title_style = ParagraphStyle(
            name="SubsectionTitle",
            parent=styles["h3"],
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=3,
            fontSize=10,
            leading=12,
            textColor=reportlab_colors.HexColor(
                config.colors.get("reportlab_secondary", "#495057")
            ),
            leftIndent=10,  # Indenta subseções
        )
        normal_style = ParagraphStyle(
            name="Normal",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            textColor=reportlab_colors.HexColor(config.colors.get("text_dark", "#212529")),
        )
        # Estilos para tabelas (passados para create_pdf_table)
        pdf_styles = {
            "TableHeader": ParagraphStyle(
                name="TableHeader",
                parent=normal_style,
                fontName="Helvetica-Bold",
                alignment=TA_CENTER,
                textColor=reportlab_colors.white,
                fontSize=9,
            ),
            "TableCellLeft": ParagraphStyle(
                name="TableCellLeft", parent=normal_style, alignment=TA_LEFT, fontSize=8
            ),
            "TableCellRight": ParagraphStyle(
                name="TableCellRight", parent=normal_style, alignment=TA_RIGHT, fontSize=8
            ),
        }
        hr_line = HRFlowable(
            width=doc_width,
            thickness=0.5,
            color=reportlab_colors.HexColor(config.colors.get("reportlab_grid", "#ADB5BD")),
            spaceBefore=1,
            spaceAfter=5,
        )
        # --- Fim da Definição de Estilos ---

        # --- Função Recursiva para Adicionar Seções e Subseções ---
        def add_report_content(content_dict, level=1):
            """Adiciona conteúdo (tabelas, parágrafos, subseções) recursivamente."""
            section_elements = []
            title_style_map = {1: section_title_style, 2: subsection_title_style}
            current_title_style = title_style_map.get(
                level, subsection_title_style
            )  # Default a subseção

            for title, content in content_dict.items():
                if not content:  # Pula se o conteúdo for vazio
                    log.debug(f"Conteúdo vazio para '{title}' (Nível {level}), pulando.")
                    continue

                # Adiciona Título da Seção/Subseção
                section_elements.append(create_styled_paragraph(title, current_title_style))
                # Adiciona linha horizontal após títulos de seção principal
                if level == 1:
                    section_elements.append(hr_line)

                # Processa o conteúdo
                if isinstance(content, dict):
                    # Se for um dicionário e contiver sub-dicionários ou listas, trata como subseção
                    if any(isinstance(v, (dict, list)) for v in content.values()):
                        log.debug(f"Processando subseções dentro de '{title}' (Nível {level+1})")
                        # Chama recursivamente para as subseções
                        subsection_elements = add_report_content(content, level + 1)
                        section_elements.extend(subsection_elements)
                    # Se for um dicionário simples (Param:Val), cria uma tabela
                    else:
                        log.debug(f"Criando tabela Parameter-Value para '{title}'")
                        table = create_pdf_table(
                            content, title=title, styles=pdf_styles, doc_width=doc_width
                        )
                        if table:
                            section_elements.append(table)
                            section_elements.append(Spacer(1, 4 * mm))  # Espaço após tabela
                        else:
                            log.warning(f"Não foi possível criar tabela para '{title}'.")

                # Se for uma lista (assume dados tabulares)
                elif isinstance(content, list):
                    log.debug(f"Criando tabela List-of-Lists para '{title}'")
                    table = create_pdf_table(
                        content, title=title, styles=pdf_styles, doc_width=doc_width
                    )
                    if table:
                        section_elements.append(table)
                        section_elements.append(Spacer(1, 4 * mm))
                    else:
                        log.warning(f"Não foi possível criar tabela para '{title}'.")

                # Se for uma string (texto simples)
                elif isinstance(content, str):
                    log.debug(f"Adicionando parágrafo para '{title}'")
                    section_elements.append(create_styled_paragraph(content, normal_style))
                    section_elements.append(Spacer(1, 4 * mm))

                else:
                    log.warning(
                        f"Tipo de conteúdo não suportado em add_report_content para '{title}': {type(content)}"
                    )

            # Retorna elementos para o nível atual (para chamadas recursivas)
            return section_elements

        # --- Construir Documento PDF ---
        elements.append(
            create_styled_paragraph(
                "Relatório de Simulação de Ensaios de Transformador", title_style
            )
        )
        elements.append(Spacer(1, 6 * mm))

        # Ordem das seções no PDF (Chaves principais do dict report_data_formatted)
        section_order = [
            "Dados Nominais e Características",  # Vem de formatar_dados_basicos
            "Resultados de Perdas",
            "Elevação de Temperatura",
            "Suportabilidade a Curto-Circuito",
            "Análise Dielétrica",  # Header para testes dielétricos
            "Tensão Aplicada",
            "Tensão Induzida",
            "Resultados de Impulso",
        ]

        # Adiciona cabeçalho especial antes dos ensaios dielétricos
        dielectric_tests_started = False
        for section_title in section_order:
            section_data = report_data_formatted.get(section_title)
            if section_data:
                # Adiciona Page Break e Título antes do primeiro teste dielétrico
                if (
                    section_title
                    in [
                        "Análise Dielétrica",
                        "Tensão Aplicada",
                        "Tensão Induzida",
                        "Resultados de Impulso",
                    ]
                    and not dielectric_tests_started
                ):
                    elements.append(PageBreak())
                    elements.append(
                        create_styled_paragraph("Resultados dos Ensaios Dielétricos", title_style)
                    )
                    elements.append(Spacer(1, 6 * mm))
                    dielectric_tests_started = True

                log.info(f"Adicionando seção ao PDF: {section_title}")
                # Chama a função recursiva para adicionar a seção e suas subseções/tabelas
                section_content_elements = add_report_content(
                    {section_title: section_data}, level=1
                )
                # KeepTogether tenta manter a seção inteira junta, se possível
                elements.append(KeepTogether(section_content_elements))
                elements.append(Spacer(1, 2 * mm))  # Espaço menor entre seções principais
            else:
                log.info(
                    f"Seção '{section_title}' não encontrada ou vazia nos dados formatados. Pulando."
                )

        # Constrói o PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        log.info("Construção do documento PDF concluída.")

    except Exception as e:
        log.exception(f"Erro crítico durante a geração do PDF: {e}")
        # Tenta escrever uma mensagem de erro no PDF se possível
        try:
            # Cria um novo doc para a mensagem de erro
            doc_err = SimpleDocTemplate(buffer, pagesize=portrait(letter))
            elements_err = [
                Paragraph(
                    f"ERRO AO GERAR PDF: {html.escape(str(e))}<br/><br/>Verifique os logs do servidor para detalhes."
                )
            ]
            doc_err.build(elements_err)
            log.info("Mensagem de erro escrita no buffer do PDF.")
        except Exception as e2:
            log.error(f"Não foi possível nem mesmo escrever a mensagem de erro no PDF: {e2}")
        # Não re-levanta a exceção, permite que o callback retorne o buffer com o erro (ou vazio)
