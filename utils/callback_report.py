"""
Script para gerar um relatório completo de todos os callbacks e inputs em cada módulo.
"""
import os
import sys

from utils.callback_analyzer import analyze_all_modules


def generate_report():
    """
    Gera um relatório completo de todos os callbacks e inputs em cada módulo.

    Returns:
        str: Relatório em formato HTML
    """
    # Analisa todos os módulos
    result = analyze_all_modules()

    # Gera o relatório
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Callbacks</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            h1, h2, h3, h4 {{
                color: #0066cc;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .module {{
                margin-bottom: 30px;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                background-color: #f9f9f9;
            }}
            .callback {{
                margin-bottom: 20px;
                border-left: 3px solid #0066cc;
                padding-left: 15px;
            }}
            .inputs, .outputs, .states {{
                margin-left: 20px;
            }}
            .item {{
                margin-bottom: 5px;
            }}
            .duplicate {{
                color: #cc0000;
                font-weight: bold;
            }}
            .summary {{
                margin-bottom: 30px;
                padding: 15px;
                background-color: #e6f0ff;
                border-radius: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #0066cc;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Relatório de Callbacks</h1>

            <div class="summary">
                <h2>Resumo</h2>
                <p>Total de callbacks: <strong>{result['total_callbacks']}</strong></p>
                <p>Total de duplicidades: <strong>{len(result['duplicates'])}</strong></p>

                <h3>Callbacks por Módulo</h3>
                <table>
                    <tr>
                        <th>Módulo</th>
                        <th>Callbacks</th>
                    </tr>
    """

    # Adiciona a tabela de callbacks por módulo
    for module_name, module_info in result["modules"].items():
        html += f"""
                    <tr>
                        <td>{module_name}</td>
                        <td>{module_info['callback_count']}</td>
                    </tr>
        """

    html += """
                </table>

                <h3>Duplicidades</h3>
    """

    if result["duplicates"]:
        html += """
                <table>
                    <tr>
                        <th>Output</th>
                        <th>Callbacks</th>
                        <th>Módulos</th>
                    </tr>
        """

        for duplicate in result["duplicates"]:
            html += f"""
                    <tr>
                        <td>{duplicate['output']}</td>
                        <td>{', '.join(duplicate['callbacks'])}</td>
                        <td>{', '.join(duplicate['modules'])}</td>
                    </tr>
            """

        html += """
                </table>
        """
    else:
        html += "<p>Nenhuma duplicidade encontrada.</p>"

    html += """
            </div>

            <h2>Detalhes por Módulo</h2>
    """

    # Adiciona os detalhes de cada módulo
    for module_name, module_info in result["modules"].items():
        html += f"""
            <div class="module">
                <h3>{module_name}</h3>
                <p>Total de callbacks: <strong>{module_info['callback_count']}</strong></p>

                <h4>Inputs Únicos:</h4>
                <ul>
        """

        for input_item in module_info["unique_inputs"]:
            html += f"<li>{input_item}</li>"

        html += """
                </ul>

                <h4>Callbacks:</h4>
        """

        for callback in module_info["callbacks"]:
            html += f"""
                <div class="callback">
                    <h5>{callback['name']}</h5>

                    <div class="outputs">
                        <h6>Outputs:</h6>
                        <ul>
            """

            for output in callback["outputs"]:
                allow_duplicate = (
                    " (allow_duplicate)" if output.get("allow_duplicate", False) else ""
                )
                html += f"<li class='item'>{output['component_id']}:{output['component_property']}{allow_duplicate}</li>"

            html += """
                        </ul>
                    </div>

                    <div class="inputs">
                        <h6>Inputs:</h6>
                        <ul>
            """

            for input_item in callback["inputs"]:
                html += f"<li class='item'>{input_item['component_id']}:{input_item['component_property']}</li>"

            html += """
                        </ul>
                    </div>
            """

            if callback["states"]:
                html += """
                    <div class="states">
                        <h6>States:</h6>
                        <ul>
                """

                for state in callback["states"]:
                    html += f"<li class='item'>{state['component_id']}:{state['component_property']}</li>"

                html += """
                        </ul>
                    </div>
                """

            html += """
                </div>
            """

        html += """
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html


def save_report(html, output_path="callback_report.html"):
    """
    Salva o relatório em um arquivo HTML.

    Args:
        html (str): Relatório em formato HTML
        output_path (str): Caminho para salvar o relatório
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Relatório salvo em {os.path.abspath(output_path)}")


if __name__ == "__main__":
    # Gera o relatório
    html = generate_report()

    # Salva o relatório
    output_path = "callback_report.html"
    if len(sys.argv) > 1:
        output_path = sys.argv[1]

    save_report(html, output_path)
