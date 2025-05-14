# callbacks/short_circuit_debug.py
"""
Módulo para adicionar logs detalhados aos callbacks de curto-circuito.
Este arquivo deve ser importado em callbacks/short_circuit.py.
"""
import logging

log = logging.getLogger(__name__)


def add_short_circuit_debug_logs(original_inputs, results, current_store_data):
    """
    Adiciona logs detalhados para diagnóstico do store de curto-circuito.

    Args:
        original_inputs: Dicionário com os inputs originais
        results: Dicionário com os resultados calculados
        current_store_data: Dicionário com os dados atuais do store
    """
    print("\n--- [SHORT CIRCUIT STORE SAVE DEBUG] ---")
    log.info("--- [SHORT CIRCUIT STORE SAVE DEBUG] ---")

    print(f"  Tipo de original_inputs: {type(original_inputs)}")
    if isinstance(original_inputs, dict):
        print(f"  Chaves de original_inputs: {list(original_inputs.keys())}")
        for key, value in original_inputs.items():
            print(f"    {key}: {type(value).__name__} = {value}")

    print(f"  Tipo de results: {type(results)}")
    if isinstance(results, dict):
        print(f"  Chaves de results: {list(results.keys())}")
        for key, value in results.items():
            print(f"    {key}: {type(value).__name__} = {value}")

    # Atualizar o store com os novos dados
    current_store_data["inputs_curto_circuito"] = original_inputs
    current_store_data["resultados_curto_circuito"] = results
    import datetime

    current_store_data["timestamp"] = datetime.datetime.now().isoformat()

    print(f"  Tipo de current_store_data após update: {type(current_store_data)}")
    if isinstance(current_store_data, dict):
        print(f"  Chaves de current_store_data após update: {list(current_store_data.keys())}")
    else:
        print(f"  Conteúdo de current_store_data após update: {repr(current_store_data)[:100]}")

    print("--- Fim [SHORT CIRCUIT STORE SAVE DEBUG] ---")

    return current_store_data
