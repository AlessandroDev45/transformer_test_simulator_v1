# utils/mcp_diagnostics.py
"""
Utilitários para diagnóstico do MCP (Master Control Program).
Fornece funções para verificar o estado do MCP e seus dados.
"""
import datetime
import logging

from utils.mcp_utils import patch_mcp  # Importar função patch_mcp

log = logging.getLogger(__name__)


def diagnose_mcp(app_instance, verbose=True):
    """
    Realiza um diagnóstico completo do MCP e seus dados.

    Args:
        app_instance: Instância da aplicação Dash
        verbose: Se True, imprime informações detalhadas no log

    Returns:
        Dict: Resultado do diagnóstico
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    result = {
        "timestamp": timestamp,
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "info": [],
        "data_summary": {},
    }

    # Verificar se o MCP está disponível
    if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
        result["status"] = "error"
        result["errors"].append("MCP não inicializado ou não disponível")
        if verbose:
            log.error("[MCP Diagnostics] MCP não inicializado ou não disponível")
        return result

    result["status"] = "ok"
    result["info"].append("MCP inicializado e disponível")
    if verbose:
        log.info("[MCP Diagnostics] MCP inicializado e disponível")

    # Verificar os stores disponíveis
    try:
        all_data = app_instance.mcp.get_all_data()
        result["data_summary"]["stores_count"] = len(all_data)
        result["data_summary"]["stores"] = {}

        for store_id, store_data in all_data.items():
            store_info = {
                "empty": store_data is None
                or (isinstance(store_data, dict) and len(store_data) == 0),
                "type": type(store_data).__name__,
                "keys_count": len(store_data) if isinstance(store_data, dict) else 0,
            }

            if isinstance(store_data, dict) and len(store_data) > 0:
                store_info["keys"] = list(store_data.keys())

                # Verificações específicas para transformer-inputs-store
                if store_id == "transformer-inputs-store":
                    # Verificar dados essenciais
                    essential_keys = [
                        "potencia_mva",
                        "tensao_at",
                        "tensao_bt",
                        "corrente_nominal_at",
                        "corrente_nominal_bt",
                    ]
                    missing_keys = [
                        k for k in essential_keys if k not in store_data or store_data[k] is None
                    ]

                    if missing_keys:
                        result["warnings"].append(
                            f"Dados essenciais ausentes em {store_id}: {missing_keys}"
                        )
                        store_info["missing_essential"] = missing_keys
                        if verbose:
                            log.warning(
                                f"[MCP Diagnostics] Dados essenciais ausentes em {store_id}: {missing_keys}"
                            )

                    # Verificar valores de corrente
                    if (
                        "corrente_nominal_at" in store_data
                        and store_data["corrente_nominal_at"] is not None
                    ):
                        store_info["corrente_at"] = store_data["corrente_nominal_at"]
                    else:
                        store_info["corrente_at"] = None

                    if (
                        "corrente_nominal_bt" in store_data
                        and store_data["corrente_nominal_bt"] is not None
                    ):
                        store_info["corrente_bt"] = store_data["corrente_nominal_bt"]
                    else:
                        store_info["corrente_bt"] = None

            result["data_summary"]["stores"][store_id] = store_info

            if verbose:
                if store_info["empty"]:
                    log.warning(f"[MCP Diagnostics] Store {store_id} está vazio")
                else:
                    log.info(
                        f"[MCP Diagnostics] Store {store_id} contém {store_info['keys_count']} chaves"
                    )

        # Verificar se há dados no transformer-inputs-store
        if "transformer-inputs-store" not in all_data or not all_data["transformer-inputs-store"]:
            result["status"] = "warning"
            result["warnings"].append("transformer-inputs-store vazio ou não inicializado")
            if verbose:
                log.warning("[MCP Diagnostics] transformer-inputs-store vazio ou não inicializado")

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Erro ao acessar dados do MCP: {str(e)}")
        if verbose:
            log.error(f"[MCP Diagnostics] Erro ao acessar dados do MCP: {e}", exc_info=True)

    return result


def fix_mcp_data(app_instance, verbose=True):
    """
    Tenta corrigir problemas comuns nos dados do MCP.

    Args:
        app_instance: Instância da aplicação Dash
        verbose: Se True, imprime informações detalhadas no log

    Returns:
        Dict: Resultado da correção
    """
    result = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "status": "unknown",
        "actions": [],
        "errors": [],
    }

    # Verificar se o MCP está disponível
    if not hasattr(app_instance, "mcp") or app_instance.mcp is None:
        result["status"] = "error"
        result["errors"].append("MCP não inicializado ou não disponível")
        if verbose:
            log.error("[MCP Fix] MCP não inicializado ou não disponível")
        return result

    try:
        # Verificar transformer-inputs-store
        transformer_data = app_instance.mcp.get_data("transformer-inputs-store")

        # Verificar se os dados estão vazios ou incompletos
        if not transformer_data or not isinstance(transformer_data, dict):
            # Inicializar apenas a estrutura, sem valores padrão
            transformer_data = {}
            if patch_mcp("transformer-inputs-store", transformer_data, app_instance):
                result["actions"].append(
                    "Inicializado transformer-inputs-store com estrutura vazia"
                )
                if verbose:
                    log.info("[MCP Fix] Inicializado transformer-inputs-store com estrutura vazia")
            else:
                result["errors"].append("Falha ao inicializar transformer-inputs-store")
                if verbose:
                    log.error("[MCP Fix] Falha ao inicializar transformer-inputs-store")

        # Verificar se as correntes estão calculadas
        # Sempre recalcular as correntes para garantir consistência
        if (
            "potencia_mva" in transformer_data
            and transformer_data["potencia_mva"] is not None
            and "tensao_at" in transformer_data
            and transformer_data["tensao_at"] is not None
        ):
            # Calcular correntes
            calculated_currents = app_instance.mcp.calculate_nominal_currents(transformer_data)

            # Log detalhado dos resultados do cálculo
            log.info(
                f"[MCP Fix] Correntes calculadas: AT={calculated_currents.get('corrente_nominal_at')}A, "
                + f"BT={calculated_currents.get('corrente_nominal_bt')}A, "
                + f"Terciário={calculated_currents.get('corrente_nominal_terciario')}A"
            )

            # Atualizar os dados com as correntes calculadas
            transformer_data.update(
                {
                    "corrente_nominal_at": calculated_currents.get("corrente_nominal_at"),
                    "corrente_nominal_at_tap_maior": calculated_currents.get(
                        "corrente_nominal_at_tap_maior"
                    ),
                    "corrente_nominal_at_tap_menor": calculated_currents.get(
                        "corrente_nominal_at_tap_menor"
                    ),
                    "corrente_nominal_bt": calculated_currents.get("corrente_nominal_bt"),
                    "corrente_nominal_terciario": calculated_currents.get(
                        "corrente_nominal_terciario"
                    ),
                }
            )

            # Atualizar o MCP com os dados atualizados usando patch_mcp
            if patch_mcp("transformer-inputs-store", transformer_data, app_instance):
                result["actions"].append(
                    f"Recalculadas correntes: AT={calculated_currents.get('corrente_nominal_at')}A, BT={calculated_currents.get('corrente_nominal_bt')}A"
                )
                if verbose:
                    log.info(
                        f"[MCP Fix] Calculadas e atualizadas correntes nominais: AT={calculated_currents.get('corrente_nominal_at')}A, BT={calculated_currents.get('corrente_nominal_bt')}A"
                    )
            else:
                result["warnings"] = result.get("warnings", []) + [
                    "Falha ao atualizar correntes no MCP"
                ]
                if verbose:
                    log.warning("[MCP Fix] Falha ao atualizar correntes no MCP")
        else:
            log.warning(
                "[MCP Fix] Não foi possível calcular correntes: potência ou tensão AT ausentes"
            )
            result["warnings"] = result.get("warnings", []) + [
                "Não foi possível calcular correntes: potência ou tensão AT ausentes"
            ]

            # Atualizar o MCP mesmo sem correntes calculadas
            app_instance.mcp.set_data("transformer-inputs-store", transformer_data)
            result["actions"].append("Atualizado MCP com dados disponíveis (sem correntes)")

        # Propagar dados para outros stores usando o novo utilitário
        try:
            if verbose:
                log.info(
                    "[MCP Fix] Propagando dados do transformer-inputs-store para outros stores..."
                )

            # Importar o utilitário de persistência do MCP
            from utils.mcp_persistence import ensure_mcp_data_propagation

            # Lista de stores para os quais propagar os dados
            target_stores = [
                "losses-store",
                "impulse-store",
                "dieletric-analysis-store",
                "applied-voltage-store",
                "induced-voltage-store",
                "short-circuit-store",
                "temperature-rise-store",
                "comprehensive-analysis-store",
            ]

            # Propagar dados para todos os stores
            propagation_results = ensure_mcp_data_propagation(
                app_instance, "transformer-inputs-store", target_stores
            )

            # Registrar resultados
            for store, success in propagation_results.items():
                if success:
                    result["actions"].append(f"Dados propagados para {store}")
                    if verbose:
                        log.info(f"[MCP Fix] Dados propagados para {store}")
        except Exception as e:
            log.error(f"[MCP Fix] Erro ao propagar dados para outros stores: {e}", exc_info=True)
            result["errors"].append(f"Erro ao propagar dados para outros stores: {str(e)}")

        # Set status to ok if no errors occurred
        if not result.get("errors"):
            result["status"] = "ok"
        else:
            result["status"] = "error"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(f"Erro ao corrigir dados do MCP: {str(e)}")
        if verbose:
            log.error(f"[MCP Fix] Erro ao corrigir dados do MCP: {e}", exc_info=True)

    return result
