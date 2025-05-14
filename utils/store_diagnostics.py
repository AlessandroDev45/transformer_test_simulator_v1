# utils/store_diagnostics.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para diagnóstico e verificação dos stores da aplicação.
Fornece funções para verificar a consistência dos dados e ajudar a identificar problemas.
"""

import datetime  # Para datetime objects
import json
import logging
from typing import Any, Dict, List

import numpy as np

log = logging.getLogger(__name__)

# Lista de todos os stores esperados na aplicação (pode ser importada se definida centralmente)
EXPECTED_STORES = [
    "transformer-inputs-store",
    "losses-store",
    "impulse-store",
    "dieletric-analysis-store",
    "applied-voltage-store",
    "induced-voltage-store",
    "short-circuit-store",
    "temperature-rise-store",
]


def is_json_serializable(obj: Any, attempt_conversion: bool = False) -> bool:
    """
    Verifica se um objeto pode ser serializado para JSON,
    opcionalmente tentando converter tipos numpy antes.

    Args:
        obj: Objeto a ser verificado
        attempt_conversion: Se True, tenta converter tipos numpy antes de verificar.

    Returns:
        bool: True se o objeto pode ser serializado, False caso contrário
    """
    try:
        # Se tentar conversão, chama a função de conversão primeiro
        if attempt_conversion:
            obj_to_check = convert_numpy_types(obj, debug_path="is_json_serializable")
        else:
            obj_to_check = obj
        # Usa um default handler para tipos comuns não serializáveis como datetime
        json.dumps(obj_to_check, default=str)
        return True
    except (TypeError, OverflowError) as e:
        if attempt_conversion:
            # Se falhou mesmo após conversão, loga o erro para diagnóstico
            log.warning(f"[JSON CHECK] Falha na serialização mesmo após conversão: {e}")
            print(f"[JSON CHECK] Falha na serialização mesmo após conversão: {e}")
        return False


def convert_numpy_types(obj: Any, debug_path: str = "") -> Any:
    """
    Converte tipos numpy e outros tipos comuns não serializáveis para JSON.
    Percorre dicionários, listas e tuplas recursivamente.

    Args:
        obj: Objeto a ser convertido
        debug_path: Caminho atual na estrutura aninhada (para debug)

    Returns:
        Objeto convertido
    """

    # Função para log detalhado (apenas em casos específicos para evitar poluição)
    def debug_log(msg, level="debug"):
        if debug_path:  # Só loga se tiver um caminho (evita logar a raiz)
            if level == "warning":
                log.warning(f"[CONVERT] {msg} (em {debug_path})")
                print(f"[CONVERT DEBUG] {msg} (em {debug_path})")
            else:
                log.debug(f"[CONVERT] {msg} (em {debug_path})")

    # Verificar se o objeto é None
    if obj is None:
        debug_log("Convertendo None -> None")
        return None

    # Estruturas de dados aninhadas
    if isinstance(obj, dict):
        debug_log(f"Convertendo dict com {len(obj)} chaves")
        return {
            k: convert_numpy_types(v, f"{debug_path}.{k}" if debug_path else k)
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        debug_log(f"Convertendo lista com {len(obj)} itens")
        return [
            convert_numpy_types(item, f"{debug_path}[{i}]" if debug_path else f"[{i}]")
            for i, item in enumerate(obj)
        ]
    elif isinstance(obj, tuple):
        debug_log(f"Convertendo tupla com {len(obj)} itens")
        return tuple(
            convert_numpy_types(item, f"{debug_path}[{i}]" if debug_path else f"[{i}]")
            for i, item in enumerate(obj)
        )

    # Tipos numpy básicos
    elif isinstance(obj, np.integer):
        debug_log(f"Convertendo np.integer {obj} -> int")
        return int(obj)
    elif isinstance(obj, (np.floating, float, int)):
        # Trata NaN e Infinito para np.floating
        if isinstance(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            debug_log("Convertendo np.nan/np.inf -> None")
            return None  # Converte NaN/Inf para None (serializável)
        # Para float e int normais, retorna diretamente sem conversão
        debug_log(f"Mantendo/convertendo número {obj} -> {type(obj).__name__}")
        return obj if isinstance(obj, (float, int)) else float(obj)
    elif isinstance(obj, np.ndarray):
        # Converte array para lista, aplicando recursivamente a conversão
        debug_log(f"Convertendo np.ndarray shape={obj.shape}, dtype={obj.dtype}")
        try:
            return convert_numpy_types(obj.tolist(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao converter np.ndarray para lista: {e}", "warning")
            # Tenta converter elemento por elemento
            try:
                result = []
                for i, item in enumerate(obj):
                    result.append(
                        convert_numpy_types(item, f"{debug_path}[{i}]" if debug_path else f"[{i}]")
                    )
                return result
            except Exception as e2:
                debug_log(f"ERRO na conversão elemento por elemento: {e2}", "warning")
                return str(obj)
    elif isinstance(obj, np.bool_):
        debug_log(f"Convertendo np.bool_ {obj} -> bool")
        return bool(obj)

    # Tipos datetime
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        # Converte data/datetime para string ISO 8601
        debug_log("Convertendo datetime -> string ISO")
        return obj.isoformat()

    # Outros tipos comuns
    elif isinstance(obj, set):
        debug_log(f"Convertendo set com {len(obj)} itens -> lista")
        return list(obj)  # Converte set para lista
    elif isinstance(obj, complex) or (hasattr(obj, "imag") and hasattr(obj, "real")):
        # Para números complexos, retorna apenas a parte real se a parte imaginária for zero
        if hasattr(obj, "imag") and obj.imag == 0:
            debug_log("Convertendo complex com imag=0 -> float")
            return float(obj.real)
        # Caso contrário, converte para string
        debug_log("Convertendo complex -> string")
        return f"{obj.real}+{obj.imag}j"

    # Objetos com métodos de conversão
    elif hasattr(obj, "to_dict") and callable(obj.to_dict):
        # Para objetos com método to_dict (como pandas DataFrame/Series)
        debug_log("Convertendo objeto com to_dict() -> dict")
        try:
            return convert_numpy_types(obj.to_dict(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao usar to_dict(): {e}", "warning")
            return str(obj)
    elif hasattr(obj, "to_list") and callable(obj.to_list):
        # Para objetos com método to_list
        debug_log("Convertendo objeto com to_list() -> lista")
        try:
            return convert_numpy_types(obj.to_list(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao usar to_list(): {e}", "warning")
            return str(obj)
    elif hasattr(obj, "to_numpy") and callable(obj.to_numpy):
        # Para objetos com método to_numpy (como pandas Series/DataFrame)
        debug_log("Convertendo objeto com to_numpy() -> array -> lista")
        try:
            return convert_numpy_types(obj.to_numpy().tolist(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao usar to_numpy(): {e}", "warning")
            return str(obj)
    elif hasattr(obj, "tolist") and callable(obj.tolist):
        # Para objetos com método tolist (como arrays numpy)
        debug_log("Convertendo objeto com tolist() -> lista")
        try:
            return convert_numpy_types(obj.tolist(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao usar tolist(): {e}", "warning")
            return str(obj)

    # Objetos customizados
    elif hasattr(obj, "__dict__"):
        # Para objetos customizados com __dict__
        debug_log("Convertendo objeto customizado via __dict__")
        try:
            # Verifica se o __dict__ não está vazio
            if not obj.__dict__:
                debug_log("__dict__ vazio, usando str(obj)", "warning")
                return str(obj)
            return convert_numpy_types(obj.__dict__, debug_path)
        except Exception as e:
            debug_log(f"ERRO ao converter via __dict__: {e}", "warning")
            return str(obj)

    # Tipos específicos que podem estar causando problemas
    elif str(type(obj).__module__).startswith("numpy"):
        # Qualquer outro tipo numpy não tratado acima
        debug_log(f"Convertendo tipo numpy genérico: {type(obj).__name__}")
        try:
            return convert_numpy_types(np.asarray(obj).tolist(), debug_path)
        except Exception as e:
            debug_log(f"ERRO ao converter tipo numpy genérico: {e}", "warning")
            return str(obj)
    elif str(type(obj).__module__).startswith("pandas"):
        # Qualquer outro tipo pandas não tratado acima
        debug_log(f"Convertendo tipo pandas genérico: {type(obj).__name__}")
        try:
            return str(obj)
        except Exception as e:
            debug_log(f"ERRO ao converter tipo pandas genérico: {e}", "warning")
            return f"<Objeto pandas não serializável: {type(obj).__name__}>"

    # Verificação final de serializabilidade
    else:
        # Tenta verificar se o objeto já é serializável
        try:
            json.dumps(obj)
            debug_log(f"Objeto já é serializável: {type(obj).__name__}")
            return obj
        except (TypeError, OverflowError):
            # Se não for serializável, converte para string
            debug_log(
                f"Objeto não serializável, convertendo para string: {type(obj).__name__}", "warning"
            )
            try:
                return str(obj)
            except Exception as e:
                debug_log(f"ERRO ao converter para string: {e}", "warning")
                return f"<Objeto não serializável: {type(obj).__name__}>"


def check_store_data(store_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Verifica os dados dos stores e identifica problemas.

    Args:
        store_data: Dicionário com os dados dos stores

    Returns:
        Dict: Relatório com informações sobre cada store
    """
    report = {}
    log.debug("[STORE CHECK] Iniciando verificação dos stores...")

    # Verificar cada store esperado
    for store_name in EXPECTED_STORES:
        store_content = store_data.get(store_name)
        serializable_after_conversion = is_json_serializable(store_content, attempt_conversion=True)
        original_type = type(store_content).__name__ if store_content is not None else "None"

        store_report = {
            "exists": store_name in store_data,
            "is_empty": store_content is None
            or (isinstance(store_content, dict) and not store_content),
            "type": original_type,
            "serializable_as_is": is_json_serializable(store_content),  # Verifica sem conversão
            "serializable_after_conversion": serializable_after_conversion,
            "keys": list(store_content.keys()) if isinstance(store_content, dict) else [],
            "problems": [],
        }

        # Verificar problemas específicos
        if not store_report["exists"]:
            store_report["problems"].append(f"Store '{store_name}' não existe nos dados recebidos")
        elif store_report["is_empty"]:
            store_report["problems"].append(f"Store '{store_name}' está vazio ou None")
        elif not store_report["serializable_after_conversion"]:
            store_report["problems"].append(
                f"Store '{store_name}' contém dados não serializáveis (mesmo após tentativa de conversão)"
            )

            # Tentar identificar chaves problemáticas após a conversão
            if isinstance(store_content, dict):
                converted_content = convert_numpy_types(store_content)  # Converte primeiro
                for key, value in converted_content.items():
                    if not is_json_serializable(value):  # Verifica o valor já convertido
                        store_report["problems"].append(
                            f"  - Chave '{key}' ainda contém valor não serializável: {type(value)}"
                        )

        # Log para cada store verificado
        log.debug(
            f"[STORE CHECK] {store_name}: Existe={store_report['exists']}, Vazio={store_report['is_empty']}, Tipo={store_report['type']}, Ser.(Original)={store_report['serializable_as_is']}, Ser.(Conv.)={store_report['serializable_after_conversion']}, Chaves={len(store_report['keys'])}"
        )
        if store_report["problems"]:
            for problem in store_report["problems"]:
                log.warning(f"[STORE CHECK] Problema em {store_name}: {problem}")

        report[store_name] = store_report

    log.debug("[STORE CHECK] Verificação dos stores concluída.")
    return report


def find_non_serializable_path(obj: Any, path: str = "") -> List[str]:
    """
    Encontra caminhos para valores não serializáveis em um objeto aninhado.

    Args:
        obj: Objeto a ser verificado
        path: Caminho atual na estrutura aninhada

    Returns:
        Lista de caminhos para valores não serializáveis
    """
    problem_paths = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if not is_json_serializable(v):
                if isinstance(v, (dict, list, tuple)):
                    # Se for uma estrutura aninhada, continua a busca
                    nested_problems = find_non_serializable_path(v, current_path)
                    problem_paths.extend(nested_problems)
                else:
                    # Se for um valor simples não serializável
                    problem_paths.append(f"{current_path} (tipo: {type(v).__name__})")
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            if not is_json_serializable(item):
                if isinstance(item, (dict, list, tuple)):
                    # Se for uma estrutura aninhada, continua a busca
                    nested_problems = find_non_serializable_path(item, current_path)
                    problem_paths.extend(nested_problems)
                else:
                    # Se for um valor simples não serializável
                    problem_paths.append(f"{current_path} (tipo: {type(item).__name__})")

    return problem_paths


def fix_store_data(store_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tenta corrigir problemas nos dados dos stores para permitir serialização.
    Converte tipos numpy e datetime. Se a conversão falhar, inclui informações
    de diagnóstico no resultado em vez de retornar um dict vazio.

    Args:
        store_data: Dicionário com os dados dos stores

    Returns:
        Dict: Dados dos stores corrigidos
    """
    fixed_data = {}
    log.debug("[STORE FIX] Iniciando correção dos dados dos stores...")
    print(f"\n{'='*40} CORREÇÃO DOS DADOS DOS STORES {'='*40}")

    # Log detalhado dos stores recebidos
    print(f"Stores recebidos: {list(store_data.keys())}")
    for store_name, store_content in store_data.items():
        if store_content is None:
            print(f"Store '{store_name}': None")
        elif isinstance(store_content, dict):
            print(
                f"Store '{store_name}': Dict com {len(store_content)} chaves: {list(store_content.keys())}"
            )
        else:
            print(f"Store '{store_name}': {type(store_content).__name__}")

    for store_name, store_content in store_data.items():
        print(f"\n--- Processando store: {store_name} ---")
        log.debug(
            f"[STORE FIX] Processando store: {store_name} (Tipo original: {type(store_content).__name__})"
        )

        if store_content is None:
            fixed_data[store_name] = {}  # Trata None como dict vazio
            log.debug(f"[STORE FIX] {store_name} era None, definido como {{}}.")
            print("Store vazio (None), definido como {}.")
            continue

        try:
            # Tenta converter tipos problemáticos
            print("Convertendo tipos não serializáveis...")
            converted_content = convert_numpy_types(store_content)
            log.debug(
                f"[STORE FIX] Tipo após conversão numpy/datetime: {type(converted_content).__name__}"
            )
            print(f"Tipo após conversão: {type(converted_content).__name__}")

            # Verifica se AGORA é serializável
            if is_json_serializable(converted_content):
                fixed_data[store_name] = converted_content
                log.info(f"[STORE FIX] Dados para '{store_name}' corrigidos e serializáveis.")
                print("✓ Dados corrigidos e serializáveis com sucesso.")
            else:
                # Se ainda não for serializável, identifica os problemas
                print("⚠ Dados ainda não serializáveis após conversão inicial.")
                log.warning(
                    f"[STORE FIX] Dados para '{store_name}' ainda não serializáveis após conversão."
                )

                # Encontrar caminhos para valores problemáticos
                problem_paths = find_non_serializable_path(converted_content)

                if problem_paths:
                    log.warning(f"[STORE FIX] Problemas encontrados em '{store_name}':")
                    print("Problemas encontrados:")
                    for path in problem_paths:
                        log.warning(f"[STORE FIX]   - {path}")
                        print(f"  - {path}")

                # Tenta uma conversão mais agressiva - converte para string qualquer objeto problemático
                try:
                    print("Tentando conversão mais agressiva (str para objetos complexos)...")

                    # Função recursiva local para converter objetos problemáticos para string
                    def deep_convert_fallback(obj, path=""):
                        """Função de conversão agressiva para último recurso"""

                        # Função para log detalhado
                        def debug_log(msg, level="debug"):
                            if path:  # Só loga se tiver um caminho (evita logar a raiz)
                                if level == "warning":
                                    log.warning(f"[DEEP CONVERT] {msg} (em {path})")
                                    print(f"[DEEP CONVERT] {msg} (em {path})")
                                else:
                                    log.debug(f"[DEEP CONVERT] {msg} (em {path})")

                        # Verificar se o objeto é None
                        if obj is None:
                            return None

                        # Estruturas de dados aninhadas
                        if isinstance(obj, dict):
                            debug_log(f"Convertendo dict com {len(obj)} chaves")
                            return {
                                k: deep_convert_fallback(v, f"{path}.{k}" if path else k)
                                for k, v in obj.items()
                            }
                        elif isinstance(obj, list):
                            debug_log(f"Convertendo lista com {len(obj)} itens")
                            return [
                                deep_convert_fallback(item, f"{path}[{i}]" if path else f"[{i}]")
                                for i, item in enumerate(obj)
                            ]
                        elif isinstance(obj, tuple):
                            debug_log(f"Convertendo tupla com {len(obj)} itens")
                            return tuple(
                                deep_convert_fallback(item, f"{path}[{i}]" if path else f"[{i}]")
                                for i, item in enumerate(obj)
                            )
                        elif isinstance(obj, np.ndarray):
                            # Tenta converter arrays numpy diretamente para listas
                            debug_log(
                                f"Convertendo np.ndarray shape={obj.shape}, dtype={obj.dtype}"
                            )
                            try:
                                return deep_convert_fallback(obj.tolist(), path)
                            except Exception as e:
                                debug_log(
                                    f"ERRO ao converter np.ndarray para lista: {e}", "warning"
                                )
                                return str(obj)
                        elif isinstance(obj, complex) or (
                            hasattr(obj, "imag") and hasattr(obj, "real")
                        ):
                            # Para números complexos, retorna apenas a parte real se a parte imaginária for zero
                            if hasattr(obj, "imag") and obj.imag == 0:
                                debug_log("Convertendo complex com imag=0 -> float")
                                return float(obj.real)
                            # Caso contrário, converte para string
                            debug_log("Convertendo complex -> string")
                            return f"{obj.real}+{obj.imag}j"
                        elif str(type(obj).__module__).startswith("numpy"):
                            # Qualquer outro tipo numpy
                            debug_log(f"Convertendo tipo numpy genérico: {type(obj).__name__}")
                            try:
                                return deep_convert_fallback(np.asarray(obj).tolist(), path)
                            except Exception as e:
                                debug_log(f"ERRO ao converter tipo numpy genérico: {e}", "warning")
                                return str(obj)

                        # Verificação final de serializabilidade
                        try:
                            # Tenta verificar se o objeto já é serializável
                            json.dumps(obj)
                            return obj
                        except (TypeError, OverflowError):
                            # Se não for serializável, converte para string com informações de tipo
                            debug_log(
                                f"Objeto não serializável, convertendo para string: {type(obj).__name__}",
                                "warning",
                            )
                            try:
                                return f"{str(obj)} (tipo: {type(obj).__name__})"
                            except Exception as e:
                                debug_log(f"ERRO ao converter para string: {e}", "warning")
                                return f"<Objeto não serializável: {type(obj).__name__}>"

                    aggressive_converted = deep_convert_fallback(converted_content)

                    # Verifica se a conversão agressiva funcionou
                    if is_json_serializable(aggressive_converted):
                        fixed_data[store_name] = aggressive_converted
                        log.info(
                            f"[STORE FIX] Dados para '{store_name}' corrigidos com conversão agressiva."
                        )
                        print("✓ Dados corrigidos com conversão agressiva.")
                    else:
                        # Se mesmo assim falhar, salva um diagnóstico em vez de um dict vazio
                        error_info = {
                            "_conversion_failed": True,
                            "_error": "Falha na serialização mesmo após conversão agressiva",
                            "_problematic_paths": problem_paths,
                            "_original_type": type(store_content).__name__,
                        }
                        fixed_data[store_name] = error_info
                        log.error(
                            f"[STORE FIX] Falha na serialização para '{store_name}' mesmo após conversão agressiva."
                        )
                        print("✗ Falha na serialização mesmo após conversão agressiva.")
                except Exception as conv_err:
                    # Se a conversão agressiva falhar, salva informações de diagnóstico
                    error_info = {
                        "_conversion_failed": True,
                        "_error": f"Erro na conversão agressiva: {str(conv_err)}",
                        "_problematic_paths": problem_paths,
                        "_original_type": type(store_content).__name__,
                    }
                    fixed_data[store_name] = error_info
                    log.error(
                        f"[STORE FIX] Erro na conversão agressiva para '{store_name}': {conv_err}"
                    )
                    print(f"✗ Erro na conversão agressiva: {conv_err}")
        except Exception as e:
            # Erro durante a conversão, salva informações de diagnóstico
            error_info = {
                "_conversion_failed": True,
                "_error": f"Erro inesperado: {str(e)}",
                "_original_type": type(store_content).__name__,
            }
            fixed_data[store_name] = error_info
            log.error(
                f"[STORE FIX] Erro inesperado ao tentar corrigir '{store_name}': {e}", exc_info=True
            )
            print(f"✗ Erro inesperado: {e}")

    log.debug("[STORE FIX] Correção dos dados dos stores concluída.")
    print(f"\n{'='*40} CORREÇÃO CONCLUÍDA {'='*40}")
    return fixed_data


def log_store_diagnostics(store_data: Dict[str, Any]) -> None:
    """
    Registra informações de diagnóstico sobre os stores no log.

    Args:
        store_data: Dicionário com os dados dos stores
    """
    log.info("[STORE DIAGNOSTICS] Iniciando diagnóstico dos stores")
    print(f"\n\n{'='*80}")
    print("DIAGNÓSTICO DOS STORES")
    print(f"{'='*80}")

    # Verifica os dados ANTES de tentar corrigir
    report = check_store_data(store_data)

    # Registrar resumo
    log.info(f"[STORE DIAGNOSTICS] Resumo: {len(store_data)} stores recebidos para diagnóstico")
    print(f"Resumo: {len(store_data)} stores recebidos para diagnóstico")

    # Registrar detalhes de cada store
    for store_name, store_report in report.items():
        print(f"\n{'-'*30} STORE: {store_name} {'-'*30}")
        log_msg = (
            f"{store_name}: Existe={store_report['exists']}, "
            f"Vazio={store_report['is_empty']}, Tipo={store_report['type']}, "
            f"Ser.(Original)={store_report['serializable_as_is']}, "
            f"Ser.(Conv.)={store_report['serializable_after_conversion']}, "
            f"Chaves={len(store_report['keys'])}"
        )
        log.info(f"[STORE DIAGNOSTICS] {log_msg}")
        print(log_msg)

        if store_report["keys"]:
            log.info(f"[STORE DIAGNOSTICS] {store_name} contém as chaves: {store_report['keys']}")
            print(f"Chaves: {store_report['keys']}")

    # Registrar problemas encontrados
    problems_found = False
    print(f"\n{'-'*30} PROBLEMAS ENCONTRADOS {'-'*30}")
    for store_name, store_report in report.items():
        if store_report["problems"]:
            problems_found = True
            print(f"Problemas em '{store_name}':")
            for problem in store_report["problems"]:
                log.warning(f"[STORE DIAGNOSTICS] Problema: {problem}")
                print(f"  - {problem}")

    if not problems_found:
        log.info("[STORE DIAGNOSTICS] Nenhum problema óbvio encontrado nos stores")
        print("Nenhum problema óbvio encontrado nos stores")

    log.info("[STORE DIAGNOSTICS] Diagnóstico concluído")
    print(f"{'='*80}\n\n")


def prepare_session_data(store_data_list: List[Any], store_names: List[str]) -> Dict[str, Any]:
    """
    Prepara os dados da sessão para salvamento, realizando diagnóstico e correção.

    Args:
        store_data_list: Lista com os dados dos stores na ordem dos States.
        store_names: Lista com os nomes dos stores na mesma ordem.

    Returns:
        Dict: Dados da sessão preparados (corrigidos e prontos para serialização).
    """
    print(f"\n{'='*80}")
    print("PREPARE_SESSION_DATA INICIADO")
    print(f"{'='*80}")
    print(f"Recebidos {len(store_data_list)} stores e {len(store_names)} nomes")

    # 1. Cria dicionário inicial
    session_data = {name: data for name, data in zip(store_names, store_data_list)}
    print(f"Dicionário inicial criado com {len(session_data)} stores")

    # Verificação rápida de serializabilidade antes de qualquer processamento
    print(f"\n{'='*40} VERIFICAÇÃO INICIAL DE SERIALIZABILIDADE {'='*40}")
    for name, data in session_data.items():
        serializable_as_is = is_json_serializable(data)
        serializable_after_conversion = is_json_serializable(data, attempt_conversion=True)
        print(
            f"{name}: Serializável como está: {serializable_as_is}, Após conversão: {serializable_after_conversion}"
        )

        # Se não for serializável mesmo após conversão, tenta identificar o problema
        if not serializable_after_conversion and data is not None:
            print("  ⚠ AVISO: Dados não serializáveis mesmo após conversão!")
            if isinstance(data, dict) and data:
                # Verifica cada chave individualmente
                print("  Verificando chaves problemáticas:")
                for key, value in data.items():
                    if not is_json_serializable(value, attempt_conversion=True):
                        print(
                            f"    - Chave '{key}' contém valor não serializável: {type(value).__name__}"
                        )
                        # Se for um dicionário aninhado, tenta identificar mais profundamente
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if not is_json_serializable(subvalue, attempt_conversion=True):
                                    print(
                                        f"      - Subchave '{key}.{subkey}' contém valor não serializável: {type(subvalue).__name__}"
                                    )

    # 2. Realiza e Loga o Diagnóstico
    log_store_diagnostics(session_data)

    # 3. Tenta Corrigir os Dados
    fixed_data = fix_store_data(session_data)

    # 4. Verificação final de serializabilidade após correção
    print(f"\n{'='*40} VERIFICAÇÃO FINAL DE SERIALIZABILIDADE {'='*40}")
    all_serializable = True
    for name, data in fixed_data.items():
        try:
            json_str = json.dumps(data, default=str)
            print(f"{name}: ✓ Serializável ({len(json_str)} bytes)")
        except Exception as e:
            all_serializable = False
            print(f"{name}: ✗ AINDA NÃO SERIALIZÁVEL: {e}")
            log.error(
                f"[PREPARE] Store {name} ainda não é serializável após todas as correções: {e}"
            )

    if all_serializable:
        print("\n✓ TODOS OS STORES ESTÃO SERIALIZÁVEIS APÓS CORREÇÃO")
    else:
        print("\n⚠ AVISO: ALGUNS STORES AINDA NÃO ESTÃO SERIALIZÁVEIS APÓS CORREÇÃO!")

    print(f"\n{'='*80}")
    print("PREPARE_SESSION_DATA CONCLUÍDO")
    print(f"{'='*80}")

    # 5. Retorna os dados corrigidos
    return fixed_data
