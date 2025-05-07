# analyze_callbacks_detailed.py
"""
Script para analisar callbacks e identificar duplicidades e conflitos.
Executa uma análise detalhada de todos os callbacks registrados na aplicação.
"""
import importlib
import inspect
import logging

from dash.dependencies import Input, Output, State

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)


def get_callbacks_from_module(module_name):
    """
    Obtém todos os callbacks definidos em um módulo.

    Args:
        module_name (str): Nome do módulo (ex: 'callbacks.transformer_inputs')

    Returns:
        list: Lista de dicionários com informações sobre os callbacks
    """
    try:
        # Importa o módulo
        module = importlib.import_module(module_name)

        # Lista para armazenar informações dos callbacks
        callbacks_info = []

        # Itera sobre todos os objetos no módulo
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Verifica se é um callback do Dash
                if hasattr(obj, "_callback_metadata"):
                    callback_info = {
                        "name": name,
                        "module": module_name,
                        "outputs": [],
                        "inputs": [],
                        "states": [],
                        "prevent_initial_call": obj._callback_metadata.get(
                            "prevent_initial_call", False
                        ),
                    }

                    # Processa outputs
                    for output in obj._callback_metadata.get("outputs", []):
                        if isinstance(output, Output):
                            callback_info["outputs"].append(
                                {
                                    "component_id": str(output.component_id),
                                    "component_property": output.component_property,
                                    "allow_duplicate": getattr(output, "allow_duplicate", False),
                                }
                            )

                    # Processa inputs
                    for input in obj._callback_metadata.get("inputs", []):
                        if isinstance(input, Input):
                            callback_info["inputs"].append(
                                {
                                    "component_id": str(input.component_id),
                                    "component_property": input.component_property,
                                }
                            )

                    # Processa states
                    for state in obj._callback_metadata.get("state", []):
                        if isinstance(state, State):
                            callback_info["states"].append(
                                {
                                    "component_id": str(state.component_id),
                                    "component_property": state.component_property,
                                }
                            )

                    callbacks_info.append(callback_info)

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
                        "modules": [output_map[output_key]["module"], callback["module"]],
                    }
                )
            else:
                output_map[output_key] = {
                    "callback_name": callback["name"],
                    "module": callback["module"],
                }

    return duplicates


def find_missing_components(all_callbacks, layout_components):
    """
    Encontra componentes referenciados em callbacks que não existem no layout.

    Args:
        all_callbacks (list): Lista de informações de callbacks
        layout_components (list): Lista de IDs de componentes no layout

    Returns:
        list: Lista de componentes ausentes
    """
    missing_components = []

    # Coleta todos os IDs de componentes referenciados em callbacks
    referenced_components = set()
    for callback in all_callbacks:
        for output in callback["outputs"]:
            referenced_components.add(output["component_id"])
        for input in callback["inputs"]:
            referenced_components.add(input["component_id"])
        for state in callback["states"]:
            referenced_components.add(state["component_id"])

    # Encontra componentes referenciados que não existem no layout
    for component_id in referenced_components:
        if component_id not in layout_components:
            missing_components.append(component_id)

    return missing_components


def analyze_callbacks():
    """
    Analisa todos os callbacks da aplicação.

    Returns:
        dict: Resultados da análise
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
        "callbacks.dielectric_analysis_comprehensive",
        "callbacks.report_generation",
        "callbacks.standards_consultation",
        "callbacks.standards_management",
    ]

    all_callbacks = []
    module_info = {}

    # Coleta informações de todos os callbacks
    for module_name in callback_modules:
        callbacks = get_callbacks_from_module(module_name)
        all_callbacks.extend(callbacks)
        module_info[module_name] = {"callback_count": len(callbacks), "callbacks": callbacks}

    # Encontra duplicidades
    duplicates = find_duplicate_callbacks(all_callbacks)

    # Analisa callbacks que não usam prevent_initial_call
    no_prevent_initial = []
    for callback in all_callbacks:
        if not callback["prevent_initial_call"]:
            no_prevent_initial.append({"name": callback["name"], "module": callback["module"]})

    return {
        "total_callbacks": len(all_callbacks),
        "module_info": module_info,
        "duplicates": duplicates,
        "no_prevent_initial": no_prevent_initial,
    }


def main():
    """Função principal."""
    print("Analisando callbacks...")
    results = analyze_callbacks()

    print(f"\nTotal de callbacks: {results['total_callbacks']}")

    print("\nCallbacks por módulo:")
    for module_name, info in results["module_info"].items():
        print(f"  {module_name}: {info['callback_count']} callbacks")

    print("\nDuplicidades encontradas:")
    if results["duplicates"]:
        for dup in results["duplicates"]:
            print(f"  Output: {dup['output']}")
            print(f"  Callbacks: {', '.join(dup['callbacks'])}")
            print(f"  Módulos: {', '.join(dup['modules'])}")
            print()
    else:
        print("  Nenhuma duplicidade encontrada.")

    print("\nCallbacks sem prevent_initial_call:")
    if results["no_prevent_initial"]:
        for callback in results["no_prevent_initial"]:
            print(f"  {callback['module']}.{callback['name']}")
    else:
        print("  Todos os callbacks usam prevent_initial_call.")


if __name__ == "__main__":
    main()
