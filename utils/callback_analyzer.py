"""
Utilitário para analisar callbacks e inputs em módulos do Dash.
"""
import importlib
import inspect
import logging

from dash.dependencies import Input, Output, State

log = logging.getLogger(__name__)


def get_module_callbacks(module_name):
    """
    Obtém todos os callbacks definidos em um módulo.

    Args:
        module_name (str): Nome do módulo (ex: 'callbacks.transformer_inputs')

    Returns:
        list: Lista de dicionários com informações sobre os callbacks
    """
    try:
        # Importa o módulo
        try:
            module = importlib.import_module(module_name)
        except Exception as import_error:
            log.error(f"Erro ao importar módulo {module_name}: {import_error}")
            return []

        # Lista para armazenar informações dos callbacks
        callbacks_info = []

        # Itera sobre todos os objetos no módulo
        for name, obj in inspect.getmembers(module):
            try:
                # Verifica se é uma função e tem atributos de callback
                if inspect.isfunction(obj):
                    callback_info = {
                        "name": name,
                        "function": obj,
                        "inputs": [],
                        "outputs": [],
                        "states": [],
                    }

                    # Verifica se é um callback do Dash
                    if hasattr(obj, "_callback_metadata"):
                        # Extrai informações do callback
                        metadata = obj._callback_metadata

                        # Processa outputs
                        for output in metadata.get("outputs", []):
                            if isinstance(output, Output):
                                callback_info["outputs"].append(
                                    {
                                        "component_id": str(output.component_id),
                                        "component_property": output.component_property,
                                        "allow_duplicate": getattr(
                                            output, "allow_duplicate", False
                                        ),
                                    }
                                )

                        # Processa inputs
                        for input in metadata.get("inputs", []):
                            if isinstance(input, Input):
                                callback_info["inputs"].append(
                                    {
                                        "component_id": str(input.component_id),
                                        "component_property": input.component_property,
                                    }
                                )

                        # Processa states
                        for state in metadata.get("state", []):
                            if isinstance(state, State):
                                callback_info["states"].append(
                                    {
                                        "component_id": str(state.component_id),
                                        "component_property": state.component_property,
                                    }
                                )

                        callbacks_info.append(callback_info)

                    # Verifica se a função tem um decorador de callback
                    elif hasattr(obj, "__closure__") and obj.__closure__:
                        for cell in obj.__closure__:
                            if hasattr(cell, "cell_contents") and callable(cell.cell_contents):
                                if hasattr(cell.cell_contents, "_callback_metadata"):
                                    metadata = cell.cell_contents._callback_metadata

                                    # Processa outputs
                                    for output in metadata.get("outputs", []):
                                        if isinstance(output, Output):
                                            callback_info["outputs"].append(
                                                {
                                                    "component_id": str(output.component_id),
                                                    "component_property": output.component_property,
                                                    "allow_duplicate": getattr(
                                                        output, "allow_duplicate", False
                                                    ),
                                                }
                                            )

                                    # Processa inputs
                                    for input in metadata.get("inputs", []):
                                        if isinstance(input, Input):
                                            callback_info["inputs"].append(
                                                {
                                                    "component_id": str(input.component_id),
                                                    "component_property": input.component_property,
                                                }
                                            )

                                    # Processa states
                                    for state in metadata.get("state", []):
                                        if isinstance(state, State):
                                            callback_info["states"].append(
                                                {
                                                    "component_id": str(state.component_id),
                                                    "component_property": state.component_property,
                                                }
                                            )

                                    callbacks_info.append(callback_info)
                                    break
            except Exception as obj_error:
                log.error(f"Erro ao processar objeto {name} no módulo {module_name}: {obj_error}")
                continue

        return callbacks_info

    except Exception as e:
        log.error(f"Erro ao analisar callbacks do módulo {module_name}: {e}")
        return []


def find_duplicate_callbacks(all_callbacks):
    """
    Encontra callbacks duplicados (que atualizam os mesmos outputs).

    Args:
        all_callbacks (list): Lista de informações de callbacks

    Returns:
        list: Lista de duplicidades encontradas
    """
    # Dicionário para rastrear outputs e seus callbacks
    output_map = {}
    duplicates = []

    for callback in all_callbacks:
        for output in callback["outputs"]:
            # Ignora outputs com allow_duplicate=True
            if output.get("allow_duplicate", False):
                continue

            # Cria uma chave única para o output
            output_key = f"{output['component_id']}:{output['component_property']}"

            # Verifica se já existe um callback para este output
            if output_key in output_map:
                duplicates.append(
                    {
                        "output": output_key,
                        "callbacks": [output_map[output_key]["callback_name"], callback["name"]],
                        "modules": [
                            output_map[output_key]["module"],
                            callback.get("module", "unknown"),
                        ],
                    }
                )
            else:
                output_map[output_key] = {
                    "callback_name": callback["name"],
                    "module": callback.get("module", "unknown"),
                }

    return duplicates


def analyze_module(module_name):
    """
    Analisa um módulo e retorna informações sobre seus callbacks e inputs.

    Args:
        module_name (str): Nome do módulo

    Returns:
        dict: Informações sobre o módulo
    """
    callbacks = get_module_callbacks(module_name)

    # Adiciona o nome do módulo a cada callback
    for callback in callbacks:
        callback["module"] = module_name

    # Coleta todos os inputs únicos
    unique_inputs = set()
    for callback in callbacks:
        for input in callback["inputs"]:
            unique_inputs.add(f"{input['component_id']}:{input['component_property']}")

    return {
        "module": module_name,
        "callbacks": callbacks,
        "unique_inputs": list(unique_inputs),
        "callback_count": len(callbacks),
    }


def analyze_all_modules():
    """
    Analisa todos os módulos de callback da aplicação.

    Returns:
        dict: Informações sobre todos os módulos
    """
    # Lista de módulos de callback
    callback_modules = [
        "callbacks.transformer_inputs",
        "callbacks.losses",
        "callbacks.impulse",
        "callbacks.dieletric_analysis",
        "callbacks.applied_voltage",
        "callbacks.induced_voltage",
        "callbacks.short_circuit",
        "callbacks.temperature_rise",
        "callbacks.global_updates",
        "callbacks.history",
        "callbacks.global_actions",
        "callbacks.client_side_callbacks",
    ]

    all_modules_info = {}
    all_callbacks = []

    for module_name in callback_modules:
        module_info = analyze_module(module_name)
        all_modules_info[module_name] = module_info
        all_callbacks.extend(module_info["callbacks"])

    # Encontra duplicidades
    duplicates = find_duplicate_callbacks(all_callbacks)

    return {
        "modules": all_modules_info,
        "duplicates": duplicates,
        "total_callbacks": len(all_callbacks),
    }


def get_module_info_by_pathname(pathname):
    """
    Obtém informações do módulo com base no pathname.

    Args:
        pathname (str): Pathname da URL

    Returns:
        dict: Informações do módulo
    """
    # Normaliza o pathname
    if pathname is None:
        pathname = "/"

    # Remove parâmetros de consulta
    if "?" in pathname:
        pathname = pathname.split("?")[0]

    # Remove barras extras
    pathname = pathname.rstrip("/")
    if not pathname:
        pathname = "/"

    # Mapeamento de pathname para módulo
    pathname_to_module = {
        "/": "callbacks.transformer_inputs",
        "/dados-basicos": "callbacks.transformer_inputs",
        "/perdas": "callbacks.losses",
        "/impulso": "callbacks.impulse",
        "/analise-dieletrica": "callbacks.dieletric_analysis",
        "/tensao-aplicada": "callbacks.applied_voltage",
        "/tensao-induzida": "callbacks.induced_voltage",
        "/curto-circuito": "callbacks.short_circuit",
        "/elevacao-temperatura": "callbacks.temperature_rise",
        "/historico": "callbacks.history",
        "/consulta-normas": "callbacks.standards_consultation",
        "/gerenciar-normas": "callbacks.standards_management",
    }

    module_name = pathname_to_module.get(pathname)
    if not module_name:
        log.warning(f"Nenhum módulo encontrado para o pathname: {pathname}")
        return {"module": "Desconhecido", "callbacks": [], "unique_inputs": [], "callback_count": 0}

    return analyze_module(module_name)


def format_module_info_html(module_info):
    """
    Formata as informações do módulo como HTML.

    Args:
        module_info (dict): Informações do módulo

    Returns:
        str: HTML formatado
    """
    if not module_info:
        return "<p>Módulo não encontrado</p>"

    html = f"<h3>Módulo: {module_info['module']}</h3>"
    html += f"<p>Total de callbacks: {module_info['callback_count']}</p>"

    html += "<h4>Inputs Únicos:</h4>"
    html += "<ul>"
    for input in module_info["unique_inputs"]:
        html += f"<li>{input}</li>"
    html += "</ul>"

    html += "<h4>Callbacks:</h4>"
    html += "<ul>"
    for callback in module_info["callbacks"]:
        html += f"<li><strong>{callback['name']}</strong>"

        html += "<ul>"
        html += "<li>Outputs:"
        html += "<ul>"
        for output in callback["outputs"]:
            allow_duplicate = " (allow_duplicate)" if output.get("allow_duplicate", False) else ""
            html += (
                f"<li>{output['component_id']}:{output['component_property']}{allow_duplicate}</li>"
            )
        html += "</ul></li>"

        html += "<li>Inputs:"
        html += "<ul>"
        for input in callback["inputs"]:
            html += f"<li>{input['component_id']}:{input['component_property']}</li>"
        html += "</ul></li>"

        if callback["states"]:
            html += "<li>States:"
            html += "<ul>"
            for state in callback["states"]:
                html += f"<li>{state['component_id']}:{state['component_property']}</li>"
            html += "</ul></li>"

        html += "</ul>"
        html += "</li>"
    html += "</ul>"

    return html


if __name__ == "__main__":
    # Exemplo de uso direto do script
    result = analyze_all_modules()
    print(f"Total de callbacks: {result['total_callbacks']}")
    print(f"Duplicidades encontradas: {len(result['duplicates'])}")

    if result["duplicates"]:
        print("\nDuplicidades:")
        for dup in result["duplicates"]:
            print(f"  Output: {dup['output']}")
            print(f"  Callbacks: {', '.join(dup['callbacks'])}")
            print(f"  Módulos: {', '.join(dup['modules'])}")
            print()
