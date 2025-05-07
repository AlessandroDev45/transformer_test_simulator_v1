# app_core/transformer_mcp.py
"""
Master Control Program (MCP) for the Transformer Test Simulator.
Centralizes data management and logic between different modules.
"""
import copy
import logging
import math  # Para sqrt em calculate_nominal_currents
from typing import Any, Dict, List, Optional

# Import database functions
from utils.db_manager import get_test_session_details, save_test_session, session_name_exists

# Import utility functions for data preparation
from utils.store_diagnostics import convert_numpy_types, is_json_serializable

log = logging.getLogger(__name__)

# List of all store IDs used in the application
STORE_IDS = [
    "transformer-inputs-store",
    "losses-store",
    "impulse-store",
    "dieletric-analysis-store",
    "applied-voltage-store",
    "induced-voltage-store",
    "short-circuit-store",
    "temperature-rise-store",
    "comprehensive-analysis-store",  # Adicionado
    "front-resistor-data",
    "tail-resistor-data",
    "calculated-inductance",
    "simulation-status",
]

# Default values for transformer inputs
DEFAULT_TRANSFORMER_INPUTS = {
    "tipo_transformador": "Trifásico",
    "frequencia": 60.0,
    "conexao_at": "estrela",  # Mudado para estrela (comum para AT)
    "conexao_bt": "triangulo",  # Mantido triangulo (comum para BT)
    "conexao_terciario": "",
    "liquido_isolante": "Mineral",
    "tipo_isolamento": "uniforme",
    # Default other fields to None or appropriate defaults
    "potencia_mva": None,
    "grupo_ligacao": None,
    "elevacao_oleo_topo": None,
    "elevacao_enrol": None,
    "tensao_at": None,
    "classe_tensao_at": None,
    "elevacao_enrol_at": None,
    "impedancia": None,
    "nbi_at": None,
    "sil_at": None,
    "tensao_at_tap_maior": None,
    "impedancia_tap_maior": None,
    "tensao_at_tap_menor": None,
    "impedancia_tap_menor": None,
    "teste_tensao_aplicada_at": None,
    "teste_tensao_induzida": None,
    "tensao_bt": None,
    "classe_tensao_bt": None,
    "elevacao_enrol_bt": None,
    "nbi_bt": None,
    "sil_bt": None,
    "teste_tensao_aplicada_bt": None,
    "tensao_terciario": None,
    "classe_tensao_terciario": None,
    "elevacao_enrol_terciario": None,
    "nbi_terciario": None,
    "sil_terciario": None,
    "teste_tensao_aplicada_terciario": None,
    "tensao_bucha_neutro_at": None,
    "tensao_bucha_neutro_bt": None,
    "tensao_bucha_neutro_terciario": None,
    "nbi_neutro_at": None,
    "nbi_neutro_bt": None,
    "nbi_neutro_terciario": None,
    "peso_total": None,
    "peso_parte_ativa": None,
    "peso_oleo": None,
    "peso_tanque_acessorios": None,
    "corrente_nominal_at": None,
    "corrente_nominal_at_tap_maior": None,
    "corrente_nominal_at_tap_menor": None,
    "corrente_nominal_bt": None,
    "corrente_nominal_terciario": None,
}


class TransformerMCP:
    """
    Master Control Program for the Transformer Test Simulator.
    Centralizes data management and logic between different modules.
    """

    def __init__(self):
        """Initialize the MCP with empty data stores."""
        log.info("Initializing Transformer MCP")
        self._data = {}
        self._listeners = {}  # Dictionary to store event listeners
        self._initialize_stores()

    def _initialize_stores(self):
        """Initialize all data stores with empty dictionaries or defaults."""
        for store_id in STORE_IDS:
            if store_id == "transformer-inputs-store":
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
            elif store_id == "simulation-status":
                self._data[store_id] = {"running": False}
            else:
                self._data[store_id] = {}
        log.info(f"MCP Initialized {len(self._data)} data stores")

    def get_data(self, store_id: str) -> Dict[str, Any]:
        """
        Get data from a specific store. Returns a deep copy.
        """
        if store_id not in self._data:
            log.warning(f"[MCP GET] Attempted to access non-existent store: {store_id}")
            # Initialize the store with empty dict
            if store_id == "transformer-inputs-store":
                log.info("[MCP GET] Initializing transformer-inputs-store with empty dict")
                self._data[store_id] = {}
            else:
                # Return empty dict if store ID is invalid
                return {}

        # Return a deep copy to prevent external modification of internal state
        return copy.deepcopy(self._data.get(store_id, {}))

    def set_data(
        self, store_id: str, data: Dict[str, Any], validate: bool = False
    ) -> Dict[str, List[str]]:
        """
        Set data for a specific store after validation and serialization.
        Stores a deep copy. Notifies listeners.
        """
        if store_id not in STORE_IDS:
            log.warning(f"[MCP SET] Attempted to set data for non-registered store: {store_id}")
            return {}

        log.info(f"[MCP SET] Iniciando atualização de dados para store: {store_id}")
        log.info(f"[MCP SET] Dados recebidos: {data}")

        errors = {}
        if validate:
            errors = self.validate_data(store_id, data)
            if errors:
                log.warning(f"[MCP SET] Validation errors for store {store_id}: {errors}")
                # Decide if you want to store invalid data. For now, we store it.

        # --- IMPORTANT: Convert types BEFORE storing ---
        try:
            log.info(f"[MCP SET] Convertendo tipos para store: {store_id}")
            serializable_data = convert_numpy_types(data, debug_path=f"mcp_set.{store_id}")

            # Ensure the result is serializable (optional final check)
            if not is_json_serializable(serializable_data):
                log.error(
                    f"[MCP SET] Data for {store_id} FAILED serializability check AFTER conversion."
                )
                errors["_serialization"] = ["Dados não puderam ser serializados."]
                # Store diagnostic info instead? Or store the unconverted data? For now, store converted.

            # Store a deep copy of the serializable data
            self._data[store_id] = copy.deepcopy(serializable_data)

            # Registrar valores importantes quando for atualizado no transformer-inputs-store
            if store_id == "transformer-inputs-store":
                potencia = serializable_data.get("potencia_mva")
                tensao_at = serializable_data.get("tensao_at")
                tensao_bt = serializable_data.get("tensao_bt")

                # Não calculamos correntes automaticamente aqui
                # Apenas registramos os valores para diagnóstico
                log.info(
                    f"[MCP SET] Dados salvos no MCP: potencia={potencia}, tensao_at={tensao_at}, tensao_bt={tensao_bt}"
                )

            # NOTA: O cálculo automático de correntes foi removido daqui.
            # A responsabilidade de calcular as correntes e incluir nos dados
            # passados para set_data é agora do callback que origina a atualização.

            # Notificar listeners com os dados atualizados
            log.info(f"[MCP SET] Notificando listeners para store: {store_id}")
            self._notify_listeners(store_id, copy.deepcopy(self._data[store_id]))
            log.info(f"[MCP SET] Notificação de listeners concluída para store: {store_id}")

        except Exception as e:
            log.error(
                f"[MCP SET] Error during conversion/setting data for {store_id}: {e}", exc_info=True
            )
            errors["_conversion_error"] = [f"Erro interno ao processar dados: {e}"]
            # Keep the old data or set to empty? Keeping old for now.
            log.warning(f"[MCP SET] Mantendo dados antigos para {store_id} devido a erro.")

        return errors

    def clear_data(self, store_id: Optional[str] = None):
        """
        Clear data from a specific store or all stores, resetting to defaults.
        Returns a copy of the *entire* current MCP data state after clearing.
        """
        if store_id is None:
            log.info("MCP Clearing ALL data stores to defaults")
            self._initialize_stores()  # Resets all to defaults/empty
        elif store_id in self._data:
            log.info(f"MCP Clearing data store: {store_id} to default")
            if store_id == "transformer-inputs-store":
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
            elif store_id == "simulation-status":
                self._data[store_id] = {"running": False}
            else:
                self._data[store_id] = {}
            self._notify_listeners(
                store_id, copy.deepcopy(self._data[store_id])
            )  # Notify after clear
        else:
            log.warning(f"[MCP CLEAR] Attempted to clear non-existent store: {store_id}")

        # Return a copy of the entire current data state
        return copy.deepcopy(self._data)

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        """Get data from all stores. Returns a deep copy."""
        return copy.deepcopy(self._data)

    def load_session(self, session_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Load a session from the database into the MCP.
        Returns the complete loaded data from MCP.
        """
        try:
            log.info(f"[MCP LOAD] Loading session with ID: {session_id}")
            session_details = get_test_session_details(session_id)

            if not session_details or "store_data" not in session_details:
                log.error(f"[MCP LOAD] Failed to load session {session_id}: Invalid data from DB")
                return {}  # Return empty if load failed

            loaded_store_data = session_details["store_data"]
            for store_id in STORE_IDS:
                if store_id in loaded_store_data:
                    try:
                        # Convert data before setting to MCP internal state
                        converted_data = convert_numpy_types(
                            loaded_store_data[store_id], debug_path=f"mcp_load.{store_id}"
                        )
                        # Use internal assignment to avoid deepcopy overhead here
                        self._data[store_id] = converted_data
                    except Exception as e:
                        log.error(
                            f"[MCP LOAD] Error converting data for store {store_id}: {e}",
                            exc_info=True,
                        )
                        self._data[store_id] = {"_load_error": str(e)}  # Store error info
                else:
                    # Reset missing stores to defaults
                    if store_id == "transformer-inputs-store":
                        self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
                    elif store_id == "simulation-status":
                        self._data[store_id] = {"running": False}
                    else:
                        self._data[store_id] = {}
                    log.warning(
                        f"[MCP LOAD] Store '{store_id}' not found in loaded session {session_id}. Resetting to default."
                    )

            log.info(f"[MCP LOAD] Successfully loaded session {session_id} into MCP.")
            # Notify listeners that data might have changed
            for store_id_loaded in loaded_store_data.keys():
                if store_id_loaded in STORE_IDS:
                    self._notify_listeners(
                        store_id_loaded, copy.deepcopy(self._data[store_id_loaded])
                    )

            return self.get_all_data()  # Return the complete, current MCP state
        except Exception as e:
            log.error(f"[MCP LOAD] Error loading session {session_id}: {e}", exc_info=True)
            return {}

    def save_session(self, session_name: str, notes: str = "") -> int:
        """
        Save the current MCP state to the database.
        Returns the ID of the saved session or -1 if failed.
        """
        try:
            log.info(f"[MCP SAVE] Saving session: {session_name}")
            if session_name_exists(session_name):
                log.warning(f"Session name '{session_name}' already exists")
                return -1  # Indicate failure due to existing name

            # Get CURRENT data from MCP - this data should already be serializable
            # because set_data handles serialization. Perform a final check.
            data_to_save = {}
            preparation_errors = []
            for store_id in STORE_IDS:
                mcp_store_data = self.get_data(store_id)  # Gets a deep copy
                # Final check for serializability
                if not is_json_serializable(mcp_store_data):
                    log.error(
                        f"[MCP SAVE] Data in MCP for '{store_id}' is NOT serializable before saving! Trying to fix."
                    )
                    # Attempt to fix before saving
                    fixed_data = convert_numpy_types(
                        mcp_store_data, debug_path=f"mcp_save_fix.{store_id}"
                    )
                    if is_json_serializable(fixed_data):
                        data_to_save[store_id] = fixed_data
                        preparation_errors.append(f"'{store_id}' required fixing before save.")
                        log.warning(f"[MCP SAVE] Fixed non-serializable data for '{store_id}'.")
                    else:
                        data_to_save[store_id] = {"_save_error": "Data not serializable"}
                        preparation_errors.append(f"'{store_id}' FAILED serialization fix.")
                        log.error(
                            f"[MCP SAVE] CRITICAL: Could not fix non-serializable data for '{store_id}'."
                        )
                else:
                    data_to_save[store_id] = mcp_store_data  # Already serializable

            # Add preparation errors to notes if any occurred
            if preparation_errors:
                notes = (notes + "\n\n[AVISO SAVE]: " + "; ".join(preparation_errors)).strip()

            # Save to database
            session_id = save_test_session(data_to_save, session_name, notes)
            if session_id <= 0:
                log.error(
                    f"Failed to save session '{session_name}' to database. DB function returned: {session_id}"
                )
                return -1

            log.info(f"Successfully saved session '{session_name}' with ID: {session_id}")
            return session_id
        except Exception as e:
            log.error(f"Error saving session: {e}", exc_info=True)
            return -1

    # --- Business Logic Methods (Delegated Calculations) ---

    def calculate_nominal_currents(
        self, transformer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Optional[float]]:
        """Calculates nominal currents based on provided or internal transformer data."""
        if transformer_data is None:
            transformer_data = self.get_data("transformer-inputs-store")
            log.info("[MCP Calc Currents] Usando dados do MCP")
        else:
            log.info("[MCP Calc Currents] Usando dados fornecidos")

        log.debug("[MCP] Calculating nominal currents...")
        log.info(f"[MCP Calc Currents] Dados de entrada: {transformer_data}")

        # Se transformer_data for None ou vazio, retornar resultado vazio
        if not transformer_data:
            log.warning("[MCP Calc Currents] Dados vazios! Não é possível calcular correntes.")
            return {
                k: None
                for k in [
                    "corrente_nominal_at",
                    "corrente_nominal_at_tap_maior",
                    "corrente_nominal_at_tap_menor",
                    "corrente_nominal_bt",
                    "corrente_nominal_terciario",
                ]
            }

        # Extrair valores
        tipo = transformer_data.get("tipo_transformador", "Trifásico")  # Default para Trifásico
        potencia_str = transformer_data.get("potencia_mva")
        tensao_at_str = transformer_data.get("tensao_at")
        tensao_at_maior_str = transformer_data.get("tensao_at_tap_maior")
        tensao_at_menor_str = transformer_data.get("tensao_at_tap_menor")
        tensao_bt_str = transformer_data.get("tensao_bt")
        tensao_terciario_str = transformer_data.get("tensao_terciario")

        result = {
            k: None
            for k in [
                "corrente_nominal_at",
                "corrente_nominal_at_tap_maior",
                "corrente_nominal_at_tap_menor",
                "corrente_nominal_bt",
                "corrente_nominal_terciario",
            ]
        }

        def safe_float(value):
            if value is None or value == "":
                return 0  # Retorna 0 para garantir o cálculo se valor ausente
            try:
                if isinstance(value, (int, float)):  # Se já for numérico
                    return float(value)
                if isinstance(value, str):
                    cleaned_value = value.strip().replace(",", ".")
                    # Tentar extrair a parte real se for um número complexo como string
                    # (ex: "60.0+0.0j" que pode vir de stores persistidos)
                    if "j" in cleaned_value or "J" in cleaned_value:
                        try:
                            # Remover parênteses se existirem (ex: "(1+2j)")
                            if cleaned_value.startswith("(") and cleaned_value.endswith(")"):
                                cleaned_value = cleaned_value[1:-1]
                            complex_num = complex(cleaned_value)
                            log.debug(
                                f"[MCP Calc Currents] Convertendo string complexa: '{value}' -> real: {complex_num.real}"
                            )
                            return float(complex_num.real)
                        except ValueError:
                            # Se falhar como complexo, tenta como float normal (pode ser uma string com 'j' por acaso)
                            log.warning(
                                f"[MCP Calc Currents] Tentativa de converter como complexo falhou para '{value}', tentando como float."
                            )
                            pass  # Continua para tentar como float normal

                    log.debug(
                        f"[MCP Calc Currents] Convertendo string: '{value}' -> '{cleaned_value}'"
                    )
                    return float(cleaned_value)
                # Tentar converter outros tipos (ex: numpy types se não forem tratados antes por convert_numpy_types)
                return float(value)
            except (ValueError, TypeError) as e:
                log.warning(
                    f"[MCP Calc Currents] Erro final ao converter valor '{value}' para float: {e}"
                )
                return 0  # Retorna 0 em caso de falha de conversão

        potencia = safe_float(potencia_str)
        tensao_at = safe_float(tensao_at_str)
        tensao_at_maior = safe_float(tensao_at_maior_str)
        tensao_at_menor = safe_float(tensao_at_menor_str)
        tensao_bt = safe_float(tensao_bt_str)
        tensao_terciario = safe_float(tensao_terciario_str)

        # Registrar o valor de potência usado para cálculo
        log.debug(
            f"[MCP Calc Currents] Potência usada para cálculo: {potencia} (valor original: {potencia_str})"
        )

        # Verificação mais detalhada dos dados
        log.info(
            f"[MCP Calc Currents] Valores originais: tipo={tipo}, potencia_str={potencia_str}, "
            + f"tensao_at_str={tensao_at_str}, tensao_bt_str={tensao_bt_str}, tensao_terciario_str={tensao_terciario_str}"
        )
        log.info(
            f"[MCP Calc Currents] Valores convertidos: tipo={tipo}, potencia={potencia}, "
            + f"tensao_at={tensao_at}, tensao_bt={tensao_bt}, tensao_terciario={tensao_terciario}"
        )

        # Verificar se temos valores válidos para o cálculo
        if potencia <= 0:
            log.warning("[MCP Calc Currents] Potência inválida ou ausente.")
            return {
                k: None
                for k in [
                    "corrente_nominal_at",
                    "corrente_nominal_at_tap_maior",
                    "corrente_nominal_at_tap_menor",
                    "corrente_nominal_bt",
                    "corrente_nominal_terciario",
                ]
            }

        if tensao_at <= 0:
            log.warning("[MCP Calc Currents] Tensão AT inválida ou ausente.")
            result["corrente_nominal_at"] = None
            result["corrente_nominal_at_tap_maior"] = None
            result["corrente_nominal_at_tap_menor"] = None

        if tensao_bt <= 0:
            log.warning("[MCP Calc Currents] Tensão BT inválida ou ausente.")
            result["corrente_nominal_bt"] = None

        log.debug(
            f"[MCP Calc Currents] Valores finais para cálculo: Potencia: {potencia}, Tensao AT: {tensao_at}, Tensao BT: {tensao_bt}, Tensao Terciario: {tensao_terciario}"
        )

        try:
            # Fator para cálculo da corrente
            sqrt3 = math.sqrt(3)

            # Cálculo das correntes com base no tipo de transformador
            if tipo == "Trifásico":
                if tensao_at > 0:
                    result["corrente_nominal_at"] = round(
                        (potencia * 1000) / (sqrt3 * tensao_at), 2
                    )  # Já arredondado para 2 casas decimais
                    log.debug(
                        f"[MCP Calc Currents] Corrente AT calculada: {result['corrente_nominal_at']}A (Potência: {potencia}, Tensão AT: {tensao_at})"
                    )
                else:
                    log.warning(
                        "[MCP Calc Currents] Tensão AT é zero ou inválida. Não é possível calcular corrente AT."
                    )
                    result["corrente_nominal_at"] = None

                if tensao_at_maior > 0:
                    result["corrente_nominal_at_tap_maior"] = round(
                        (potencia * 1000) / (sqrt3 * tensao_at_maior), 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente AT tap maior calculada: {result['corrente_nominal_at_tap_maior']}A"
                    )
                else:
                    result["corrente_nominal_at_tap_maior"] = None

                if tensao_at_menor > 0:
                    result["corrente_nominal_at_tap_menor"] = round(
                        (potencia * 1000) / (sqrt3 * tensao_at_menor), 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente AT tap menor calculada: {result['corrente_nominal_at_tap_menor']}A"
                    )
                else:
                    result["corrente_nominal_at_tap_menor"] = None

                if tensao_bt > 0:
                    result["corrente_nominal_bt"] = round(
                        (potencia * 1000) / (sqrt3 * tensao_bt), 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente BT calculada: {result['corrente_nominal_bt']}A"
                    )
                else:
                    log.warning(
                        "[MCP Calc Currents] Tensão BT é zero ou inválida. Não é possível calcular corrente BT."
                    )
                    result["corrente_nominal_bt"] = None

                if tensao_terciario > 0:
                    result["corrente_nominal_terciario"] = round(
                        (potencia * 1000) / (sqrt3 * tensao_terciario), 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente Terciário calculada: {result['corrente_nominal_terciario']}A"
                    )
                else:
                    result["corrente_nominal_terciario"] = None
            else:  # Monofásico
                if tensao_at > 0:
                    result["corrente_nominal_at"] = round(
                        (potencia * 1000) / tensao_at, 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente AT calculada (monofásico): {result['corrente_nominal_at']}A"
                    )
                else:
                    log.warning(
                        "[MCP Calc Currents] Tensão AT é zero ou inválida (monofásico). Não é possível calcular corrente AT."
                    )
                    result["corrente_nominal_at"] = None

                if tensao_at_maior > 0:
                    result["corrente_nominal_at_tap_maior"] = round(
                        (potencia * 1000) / tensao_at_maior, 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente AT tap maior calculada (monofásico): {result['corrente_nominal_at_tap_maior']}A"
                    )
                else:
                    result["corrente_nominal_at_tap_maior"] = None

                if tensao_at_menor > 0:
                    result["corrente_nominal_at_tap_menor"] = round(
                        (potencia * 1000) / tensao_at_menor, 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente AT tap menor calculada (monofásico): {result['corrente_nominal_at_tap_menor']}A"
                    )
                else:
                    result["corrente_nominal_at_tap_menor"] = None

                if tensao_bt > 0:
                    result["corrente_nominal_bt"] = round(
                        (potencia * 1000) / tensao_bt, 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente BT calculada (monofásico): {result['corrente_nominal_bt']}A"
                    )
                else:
                    log.warning(
                        "[MCP Calc Currents] Tensão BT é zero ou inválida (monofásico). Não é possível calcular corrente BT."
                    )
                    result["corrente_nominal_bt"] = None

                if tensao_terciario > 0:
                    result["corrente_nominal_terciario"] = round(
                        (potencia * 1000) / tensao_terciario, 2
                    )  # Já arredondado para 2 casas decimais
                    log.info(
                        f"[MCP Calc Currents] Corrente Terciário calculada (monofásico): {result['corrente_nominal_terciario']}A"
                    )
                else:
                    result["corrente_nominal_terciario"] = None

            # Resumo dos resultados
            log.info(f"[MCP Calc Currents] Resumo das correntes calculadas: {result}")

        except Exception as e:
            log.error(f"[MCP Calc Currents] Erro inesperado no cálculo: {e}", exc_info=True)
            # Em caso de erro inesperado, retornar todos os valores nulos
            for key in result:
                result[key] = None
            log.warning(
                "[MCP Calc Currents] Não foi possível calcular as correntes devido a erro inesperado. Retornando valores nulos."
            )

        log.debug(f"[MCP] Correntes calculadas: {result}")
        return result

    def calculate_visibility_styles(
        self, transformer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, str]]:
        """Calculates visibility styles based on provided or internal transformer data."""
        if transformer_data is None:
            transformer_data = self.get_data("transformer-inputs-store")

        log.debug("[MCP] Calculating visibility styles...")
        # Estilos base
        style_hidden = {"display": "none"}
        style_visible_block = {"display": "block"}  # Usado para a maioria
        style_visible_flex = {"display": "flex", "alignItems": "center"}  # Para SIL

        # Valores default - agora todos visíveis por padrão
        styles = {
            "conexao_at_style": style_visible_block,
            "conexao_bt_style": style_visible_block,
            "conexao_terciario_style": style_visible_block,
            "neutro_at_style": style_visible_block,  # Referente à coluna/div da classe neutro - agora visível
            "neutro_bt_style": style_visible_block,  # Agora visível
            "neutro_ter_style": style_visible_block,  # Agora visível
            "nbi_neutro_at_style": style_visible_block,  # Referente à coluna/div do NBI neutro - agora visível
            "nbi_neutro_bt_style": style_visible_block,  # Agora visível
            "nbi_neutro_ter_style": style_visible_block,  # Agora visível
            "sil_at_style": style_visible_flex,  # Referente à coluna/div do SIL - agora visível
            "sil_bt_style": style_visible_flex,  # Agora visível
            "sil_terciario_style": style_visible_flex,  # Agora visível
        }

        tipo = transformer_data.get("tipo_transformador")
        conexao_at = transformer_data.get("conexao_at")  # e.g., 'estrela', 'triangulo'
        conexao_bt = transformer_data.get("conexao_bt")
        conexao_terciario = transformer_data.get("conexao_terciario")

        def safe_float(value):
            if value is None or value == "":
                return None
            try:
                return float(str(value).replace(",", "."))
            except (ValueError, TypeError):
                return None

        classe_at = safe_float(transformer_data.get("classe_tensao_at"))
        classe_bt = safe_float(transformer_data.get("classe_tensao_bt"))
        classe_terciario = safe_float(transformer_data.get("classe_tensao_terciario"))

        # Removemos a lógica que esconde campos para transformadores monofásicos
        # Todos os campos permanecem visíveis independentemente do tipo de transformador

        # Mantemos as conexões visíveis mesmo para monofásicos
        styles["conexao_at_style"] = style_visible_block
        styles["conexao_bt_style"] = style_visible_block
        styles["conexao_terciario_style"] = style_visible_block

        # Mantemos os campos de neutro visíveis independentemente da conexão
        styles["neutro_at_style"] = style_visible_block
        styles["neutro_bt_style"] = style_visible_block
        styles["neutro_ter_style"] = style_visible_block
        styles["nbi_neutro_at_style"] = style_visible_block
        styles["nbi_neutro_bt_style"] = style_visible_block
        styles["nbi_neutro_ter_style"] = style_visible_block

        # Mantemos os campos SIL/IM visíveis independentemente da classe de tensão
        styles["sil_at_style"] = style_visible_flex
        styles["sil_bt_style"] = style_visible_flex
        styles["sil_terciario_style"] = style_visible_flex

        log.debug(f"[MCP] Estilos calculados: {styles}")
        return styles

    # --- Event System Methods (Opcional, mas útil para desacoplamento) ---

    def add_listener(self, store_id: str, callback: callable) -> None:
        """Add a listener for changes to a specific store."""
        if store_id not in self._listeners:
            self._listeners[store_id] = []
        if callback not in self._listeners[store_id]:
            self._listeners[store_id].append(callback)
            log.debug(f"MCP Added listener for store: {store_id}")

    def remove_listener(self, store_id: str, callback: callable) -> None:
        """Remove a listener for changes to a specific store."""
        if store_id in self._listeners and callback in self._listeners[store_id]:
            self._listeners[store_id].remove(callback)
            log.debug(f"MCP Removed listener for store: {store_id}")

    def _notify_listeners(self, store_id: str, data: Dict[str, Any]) -> None:
        """Notify all listeners for a specific store."""
        if store_id in self._listeners:
            log.info(
                f"[MCP NOTIFY] Notificando {len(self._listeners[store_id])} listeners para store: {store_id}"
            )
            for callback_func in self._listeners[store_id]:
                try:
                    log.info(f"[MCP NOTIFY] Chamando listener para store: {store_id}")
                    callback_func(data)  # Passa os dados atuais do store
                    log.info(f"[MCP NOTIFY] Listener para store {store_id} executado com sucesso")
                except Exception as e:
                    log.error(
                        f"[MCP NOTIFY] Erro em listener para store {store_id}: {e}", exc_info=True
                    )

    # --- Data Validation Method Stub ---

    def validate_data(self, store_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Placeholder for data validation logic specific to each store."""
        errors = {}
        if store_id == "transformer-inputs-store":
            # Import validator only when needed
            from components.validators import validate_dict_inputs

            # Define validation rules specific to transformer inputs
            rules = {
                "potencia_mva": {"required": True, "positive": True, "label": "Potência"},
                "tensao_at": {"required": True, "positive": True, "label": "Tensão AT"},
                "tensao_bt": {"required": True, "positive": True, "label": "Tensão BT"},
                "frequencia": {"required": True, "min": 50, "max": 60, "label": "Frequência"},
                "impedancia": {
                    "required": False,
                    "min": 0.1,
                    "max": 30,
                    "label": "Impedância Nom.",
                },  # Allow None/empty
                # Add more rules for other fields as needed
            }
            # Ensure data is a dict before validating
            if isinstance(data, dict):
                errors = validate_dict_inputs(data, rules)
            else:
                errors["_data_format"] = ["Formato de dados inválido para validação."]
        # Add validation logic for other stores here
        return errors
