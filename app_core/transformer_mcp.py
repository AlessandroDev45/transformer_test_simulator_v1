# app_core/transformer_mcp.py
"""
Master Control Program (MCP) for the Transformer Test Simulator.
Centralizes data management and logic between different modules.
"""
import logging
import json  # Usado para serialização de logs
import copy
import math # Para sqrt em calculate_nominal_currents
from typing import Dict, Any, List, Optional

# Import utility functions for data preparation
from utils.store_diagnostics import convert_numpy_types, is_json_serializable
# Import database functions
from utils.db_manager import (
    save_test_session,
    get_test_session_details,
    session_name_exists
)

log = logging.getLogger(__name__)

# List of all store IDs used in the application
STORE_IDS = [
    'transformer-inputs-store',
    'losses-store',
    'impulse-store',
    'dieletric-analysis-store',
    'applied-voltage-store',
    'induced-voltage-store',
    'short-circuit-store',
    'temperature-rise-store',
    'comprehensive-analysis-store', # Adicionado
    'front-resistor-data',
    'tail-resistor-data',
    'calculated-inductance',
    'simulation-status'
]

# Default values for transformer inputs
DEFAULT_TRANSFORMER_INPUTS = {
    'tipo_transformador': 'Trifásico',
    'frequencia': 60.0,
    'conexao_at': 'estrela', # Mudado para estrela (comum para AT)
    'conexao_bt': 'triangulo', # Mantido triangulo (comum para BT)
    'conexao_terciario': '',
    'liquido_isolante': 'Mineral',
    'tipo_isolamento': 'uniforme',
    # Default other fields to None or appropriate defaults
    'potencia_mva': None, 'grupo_ligacao': None, 'elevacao_oleo_topo': None, 'elevacao_enrol': None,
    'tensao_at': None, 'classe_tensao_at': None, 'elevacao_enrol_at': None, 'impedancia': None,
    'nbi_at': None, 'sil_at': None,
    'tensao_at_tap_maior': None, 'impedancia_tap_maior': None,
    'tensao_at_tap_menor': None, 'impedancia_tap_menor': None,
    'teste_tensao_aplicada_at': None, 'teste_tensao_induzida': None,
    'tensao_bt': None, 'classe_tensao_bt': None, 'elevacao_enrol_bt': None, 'nbi_bt': None, 'sil_bt': None,
    'teste_tensao_aplicada_bt': None,
    'tensao_terciario': None, 'classe_tensao_terciario': None, 'elevacao_enrol_terciario': None,
    'nbi_terciario': None, 'sil_terciario': None, 'teste_tensao_aplicada_terciario': None,
    'tensao_bucha_neutro_at': None, 'tensao_bucha_neutro_bt': None, 'tensao_bucha_neutro_terciario': None,
    'nbi_neutro_at': None, 'nbi_neutro_bt': None, 'nbi_neutro_terciario': None,
    'peso_total': None, 'peso_parte_ativa': None, 'peso_oleo': None, 'peso_tanque_acessorios': None,
    'corrente_nominal_at': None, 'corrente_nominal_at_tap_maior': None, 'corrente_nominal_at_tap_menor': None,
    'corrente_nominal_bt': None, 'corrente_nominal_terciario': None
}

class TransformerMCP:
    """
    Master Control Program for the Transformer Test Simulator.
    Centralizes data management and logic between different modules.
    """
    def __init__(self, load_from_disk=False):
        """
        Initialize the MCP with empty data stores.

        Args:
            load_from_disk (bool): If True, attempts to load state from disk
        """
        log.info(f"Initializing Transformer MCP (load_from_disk={load_from_disk})")
        self._data = {}
        self._listeners = {}  # Dictionary to store event listeners

        # Inicializar stores com valores padrão
        self._initialize_stores()

        # Carregar dados do disco se solicitado
        if load_from_disk:
            try:
                from utils.mcp_disk_persistence import load_mcp_state_from_disk
                disk_data, success = load_mcp_state_from_disk()

                if success and disk_data:
                    log.info("Carregando dados do MCP a partir do disco")
                    # Atualizar stores com dados do disco
                    for store_id in STORE_IDS:
                        if store_id in disk_data:
                            try:
                                # Converter dados antes de definir no estado interno do MCP
                                from utils.store_diagnostics import convert_numpy_types
                                converted_data = convert_numpy_types(disk_data[store_id], debug_path=f"mcp_init_load.{store_id}")
                                # Usar atribuição interna para evitar overhead de deepcopy
                                self._data[store_id] = converted_data
                                log.info(f"Dados carregados do disco para store: {store_id}")
                            except Exception as e:
                                log.error(f"Erro ao converter dados do disco para store {store_id}: {e}", exc_info=True)
                else:
                    log.warning("Não foi possível carregar dados do MCP a partir do disco")
            except ImportError as e:
                log.error(f"Erro ao importar módulo de persistência em disco: {e}", exc_info=True)
            except Exception as e:
                log.error(f"Erro ao carregar dados do MCP a partir do disco: {e}", exc_info=True)

    def _initialize_stores(self):
        """Initialize all data stores with empty dictionaries or defaults."""
        log.info("===============================================================")
        log.info("[MCP INITIALIZE] INICIALIZANDO STORES:")

        for store_id in STORE_IDS:
            if store_id == 'transformer-inputs-store':
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()

                # Log detalhado dos dados iniciais do transformer-inputs-store
                import json
                initial_data = copy.deepcopy(self._data.get(store_id, {}))
                log.info("===============================================================")
                log.info("[MCP INITIALIZE] DADOS INICIAIS DO TRANSFORMER-INPUTS-STORE:")
                try:
                    # Tenta imprimir os dados completos
                    log_data = json.dumps(initial_data, indent=2)
                    log.info(f"DADOS COMPLETOS INICIAIS: {log_data}")
                except Exception as e:
                    # Se falhar, imprime apenas as chaves e alguns valores importantes
                    log.info(f"CHAVES INICIAIS: {list(initial_data.keys())}")
                    log.info(f"TIPO INICIAL: {initial_data.get('tipo_transformador')}")
                    log.info(f"POTÊNCIA INICIAL: {initial_data.get('potencia_mva')}")
                    log.info(f"TENSÃO AT INICIAL: {initial_data.get('tensao_at')}")
                    log.info(f"TENSÃO BT INICIAL: {initial_data.get('tensao_bt')}")
                    log.info(f"ERRO AO SERIALIZAR PARA LOG DADOS INICIAIS: {e}")
                log.info("===============================================================")
            elif store_id == 'simulation-status':
                self._data[store_id] = {"running": False}
            else:
                self._data[store_id] = {}

        log.info(f"MCP Initialized {len(self._data)} data stores")
        log.info("===============================================================")

    def get_data(self, store_id: str) -> Dict[str, Any]:
        """
        Get data from a specific store. Returns a deep copy.
        """
        if store_id not in self._data:
            log.warning(f"[MCP GET] Attempted to access non-existent store: {store_id}")
            return {} # Return empty dict if store ID is invalid

        # Log detalhado dos dados lidos do MCP
        if store_id == 'transformer-inputs-store':
            import json
            log.info("===============================================================")
            log.info("[MCP LEITURA] DADOS LIDOS DO MCP:")
            try:
                # Tenta imprimir os dados completos
                data_to_return = copy.deepcopy(self._data.get(store_id, {}))
                log_data = json.dumps(data_to_return, indent=2)
                log.info(f"DADOS COMPLETOS LIDOS DO MCP: {log_data}")
            except Exception as e:
                # Se falhar, imprime apenas as chaves e alguns valores importantes
                data_to_return = copy.deepcopy(self._data.get(store_id, {}))
                log.info(f"CHAVES LIDAS DO MCP: {list(data_to_return.keys())}")
                log.info(f"TIPO LIDO DO MCP: {data_to_return.get('tipo_transformador')}")
                log.info(f"POTÊNCIA LIDA DO MCP: {data_to_return.get('potencia_mva')}")
                log.info(f"TENSÃO AT LIDA DO MCP: {data_to_return.get('tensao_at')}")
                log.info(f"TENSÃO BT LIDA DO MCP: {data_to_return.get('tensao_bt')}")
                log.info(f"ERRO AO SERIALIZAR PARA LOG LEITURA DO MCP: {e}")
            log.info("===============================================================")
            return data_to_return
        else:
            # Return a deep copy to prevent external modification of internal state
            return copy.deepcopy(self._data.get(store_id, {}))

    def set_data(self, store_id: str, data: Dict[str, Any], validate: bool = False) -> Dict[str, List[str]]:
        """
        Set data for a specific store after validation and serialization.
        Stores a deep copy. Notifies listeners.
        """
        if store_id not in STORE_IDS:
            log.warning(f"[MCP SET] Attempted to set data for non-registered store: {store_id}")
            return {}

        errors = {}
        if validate:
            errors = self.validate_data(store_id, data)
            if errors:
                log.warning(f"[MCP SET] Validation errors for store {store_id}: {errors}")
                # Decide if you want to store invalid data. For now, we store it.

        # --- IMPORTANT: Convert types BEFORE storing ---
        try:
            serializable_data = convert_numpy_types(data, debug_path=f"mcp_set.{store_id}")
            # Ensure the result is serializable (optional final check)
            if not is_json_serializable(serializable_data):
                 log.error(f"[MCP SET] Data for {store_id} FAILED serializability check AFTER conversion.")
                 errors['_serialization'] = ["Dados não puderam ser serializados."]
                 # Store diagnostic info instead? Or store the unconverted data? For now, store converted.
            # Store a deep copy of the serializable data
            self._data[store_id] = copy.deepcopy(serializable_data)

            # Log detalhado dos dados armazenados no MCP
            if store_id == 'transformer-inputs-store':
                import json
                log.info("===============================================================")
                log.info("[MCP ARMAZENAMENTO] DADOS ARMAZENADOS NO MCP:")
                try:
                    # Tenta imprimir os dados completos
                    log_data = json.dumps(serializable_data, indent=2)
                    log.info(f"DADOS COMPLETOS NO MCP: {log_data}")
                except Exception as e:
                    # Se falhar, imprime apenas as chaves e alguns valores importantes
                    log.info(f"CHAVES NO MCP: {list(serializable_data.keys())}")
                    log.info(f"TIPO NO MCP: {serializable_data.get('tipo_transformador')}")
                    log.info(f"POTÊNCIA NO MCP: {serializable_data.get('potencia_mva')}")
                    log.info(f"TENSÃO AT NO MCP: {serializable_data.get('tensao_at')}")
                    log.info(f"TENSÃO BT NO MCP: {serializable_data.get('tensao_bt')}")
                    log.info(f"ERRO AO SERIALIZAR PARA LOG NO MCP: {e}")
                log.info("===============================================================")

            log.debug(f"[MCP SET] Updated data for store: {store_id}")
            self._notify_listeners(store_id, copy.deepcopy(self._data[store_id]))
        except Exception as e:
             log.error(f"[MCP SET] Error during conversion/setting data for {store_id}: {e}", exc_info=True)
             errors['_conversion_error'] = [f"Erro interno ao processar dados: {e}"]
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
            self._initialize_stores() # Resets all to defaults/empty
        elif store_id in self._data:
            log.info(f"MCP Clearing data store: {store_id} to default")

            # Log detalhado dos dados antes de limpar
            if store_id == 'transformer-inputs-store':
                import json
                old_data = copy.deepcopy(self._data.get(store_id, {}))
                log.info("===============================================================")
                log.info("[MCP CLEAR] DADOS ANTES DE LIMPAR:")
                try:
                    # Tenta imprimir os dados completos
                    log_data = json.dumps(old_data, indent=2)
                    log.info(f"DADOS COMPLETOS ANTES DE LIMPAR NO MCP: {log_data}")
                except Exception as e:
                    # Se falhar, imprime apenas as chaves e alguns valores importantes
                    log.info(f"CHAVES ANTES DE LIMPAR NO MCP: {list(old_data.keys())}")
                    log.info(f"TIPO ANTES DE LIMPAR NO MCP: {old_data.get('tipo_transformador')}")
                    log.info(f"POTÊNCIA ANTES DE LIMPAR NO MCP: {old_data.get('potencia_mva')}")
                    log.info(f"TENSÃO AT ANTES DE LIMPAR NO MCP: {old_data.get('tensao_at')}")
                    log.info(f"TENSÃO BT ANTES DE LIMPAR NO MCP: {old_data.get('tensao_bt')}")
                    log.info(f"ERRO AO SERIALIZAR PARA LOG ANTES DE LIMPAR NO MCP: {e}")
                log.info("===============================================================")

                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()

                # Log detalhado dos dados depois de limpar
                new_data = copy.deepcopy(self._data.get(store_id, {}))
                log.info("===============================================================")
                log.info("[MCP CLEAR] DADOS DEPOIS DE LIMPAR:")
                try:
                    # Tenta imprimir os dados completos
                    log_data = json.dumps(new_data, indent=2)
                    log.info(f"DADOS COMPLETOS DEPOIS DE LIMPAR NO MCP: {log_data}")
                except Exception as e:
                    # Se falhar, imprime apenas as chaves e alguns valores importantes
                    log.info(f"CHAVES DEPOIS DE LIMPAR NO MCP: {list(new_data.keys())}")
                    log.info(f"TIPO DEPOIS DE LIMPAR NO MCP: {new_data.get('tipo_transformador')}")
                    log.info(f"POTÊNCIA DEPOIS DE LIMPAR NO MCP: {new_data.get('potencia_mva')}")
                    log.info(f"TENSÃO AT DEPOIS DE LIMPAR NO MCP: {new_data.get('tensao_at')}")
                    log.info(f"TENSÃO BT DEPOIS DE LIMPAR NO MCP: {new_data.get('tensao_bt')}")
                    log.info(f"ERRO AO SERIALIZAR PARA LOG DEPOIS DE LIMPAR NO MCP: {e}")
                log.info("===============================================================")
            elif store_id == 'simulation-status':
                self._data[store_id] = {"running": False}
            else:
                self._data[store_id] = {}

            self._notify_listeners(store_id, copy.deepcopy(self._data[store_id])) # Notify after clear
        else:
            log.warning(f"[MCP CLEAR] Attempted to clear non-existent store: {store_id}")

        # Return a copy of the entire current data state
        return copy.deepcopy(self._data)

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        """ Get data from all stores. Returns a deep copy. """
        return copy.deepcopy(self._data)

    def load_session(self, session_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Load a session from the database into the MCP.
        Returns the complete loaded data from MCP.
        """
        try:
            log.info(f"[MCP LOAD] Loading session with ID: {session_id}")
            session_details = get_test_session_details(session_id)

            if not session_details or 'store_data' not in session_details:
                log.error(f"[MCP LOAD] Failed to load session {session_id}: Invalid data from DB")
                return {} # Return empty if load failed

            loaded_store_data = session_details['store_data']
            for store_id in STORE_IDS:
                if store_id in loaded_store_data:
                    try:
                        # Convert data before setting to MCP internal state
                        converted_data = convert_numpy_types(loaded_store_data[store_id], debug_path=f"mcp_load.{store_id}")
                        # Use internal assignment to avoid deepcopy overhead here
                        self._data[store_id] = converted_data
                    except Exception as e:
                         log.error(f"[MCP LOAD] Error converting data for store {store_id}: {e}", exc_info=True)
                         self._data[store_id] = {"_load_error": str(e)} # Store error info
                else:
                     # Reset missing stores to defaults
                    if store_id == 'transformer-inputs-store':
                        self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
                    elif store_id == 'simulation-status':
                        self._data[store_id] = {"running": False}
                    else:
                        self._data[store_id] = {}
                    log.warning(f"[MCP LOAD] Store '{store_id}' not found in loaded session {session_id}. Resetting to default.")

            log.info(f"[MCP LOAD] Successfully loaded session {session_id} into MCP.")
            # Notify listeners that data might have changed
            for store_id_loaded in loaded_store_data.keys():
                 if store_id_loaded in STORE_IDS:
                     self._notify_listeners(store_id_loaded, copy.deepcopy(self._data[store_id_loaded]))

            return self.get_all_data() # Return the complete, current MCP state
        except Exception as e:
            log.error(f"[MCP LOAD] Error loading session {session_id}: {e}", exc_info=True)
            return {}

    def save_to_disk(self, force=False):
        """
        Salva o estado atual do MCP em disco.

        Args:
            force (bool): Se True, força o salvamento mesmo se não houver alterações

        Returns:
            bool: True se o salvamento foi bem-sucedido, False caso contrário
        """
        try:
            log.info(f"Salvando estado do MCP em disco (force={force})")

            # Importar função de salvamento
            from utils.mcp_disk_persistence import save_mcp_state_to_disk

            # Obter dados atuais do MCP
            data_to_save = self.get_all_data()

            # Salvar dados em disco
            success = save_mcp_state_to_disk(data_to_save, create_backup=True)

            if success:
                log.info("Estado do MCP salvo em disco com sucesso")
            else:
                log.error("Falha ao salvar estado do MCP em disco")

            return success
        except ImportError as e:
            log.error(f"Erro ao importar módulo de persistência em disco: {e}", exc_info=True)
            return False
        except Exception as e:
            log.error(f"Erro ao salvar estado do MCP em disco: {e}", exc_info=True)
            return False

    def save_session(self, session_name: str, notes: str = "") -> int:
        """
        Save the current MCP state to the database.
        Returns the ID of the saved session or -1 if failed.
        """
        try:
            log.info(f"[MCP SAVE] Saving session: {session_name}")
            if session_name_exists(session_name):
                log.warning(f"Session name '{session_name}' already exists")
                return -1 # Indicate failure due to existing name

            # Get CURRENT data from MCP - this data should already be serializable
            # because set_data handles serialization. Perform a final check.
            data_to_save = {}
            preparation_errors = []
            for store_id in STORE_IDS:
                 mcp_store_data = self.get_data(store_id) # Gets a deep copy
                 # Final check for serializability
                 if not is_json_serializable(mcp_store_data):
                      log.error(f"[MCP SAVE] Data in MCP for '{store_id}' is NOT serializable before saving! Trying to fix.")
                      # Attempt to fix before saving
                      fixed_data = convert_numpy_types(mcp_store_data, debug_path=f"mcp_save_fix.{store_id}")
                      if is_json_serializable(fixed_data):
                           data_to_save[store_id] = fixed_data
                           preparation_errors.append(f"'{store_id}' required fixing before save.")
                           log.warning(f"[MCP SAVE] Fixed non-serializable data for '{store_id}'.")
                      else:
                           data_to_save[store_id] = {"_save_error": "Data not serializable"}
                           preparation_errors.append(f"'{store_id}' FAILED serialization fix.")
                           log.error(f"[MCP SAVE] CRITICAL: Could not fix non-serializable data for '{store_id}'.")
                 else:
                      data_to_save[store_id] = mcp_store_data # Already serializable

            # Add preparation errors to notes if any occurred
            if preparation_errors:
                 notes = (notes + "\n\n[AVISO SAVE]: " + "; ".join(preparation_errors)).strip()

            # Save to database
            session_id = save_test_session(data_to_save, session_name, notes)
            if session_id <= 0:
                log.error(f"Failed to save session '{session_name}' to database. DB function returned: {session_id}")
                return -1

            log.info(f"Successfully saved session '{session_name}' with ID: {session_id}")
            return session_id
        except Exception as e:
            log.error(f"Error saving session: {e}", exc_info=True)
            return -1

    # --- Business Logic Methods (Delegated Calculations) ---

    def calculate_nominal_currents(self, transformer_data: Optional[Dict[str, Any]] = None) -> Dict[str, Optional[float]]:
        """ Calculates nominal currents based on provided or internal transformer data. """
        if transformer_data is None:
            transformer_data = self.get_data('transformer-inputs-store')
            log.info("[MCP Calc Currents] Usando dados do MCP")
        else:
            log.info("[MCP Calc Currents] Usando dados fornecidos")

        # Log detalhado dos dados usados para calcular as correntes
        import json
        log.info("===============================================================")
        log.info("[MCP CALC CURRENTS] DADOS USADOS PARA CÁLCULO:")
        try:
            # Tenta imprimir os dados completos
            log_data = json.dumps(transformer_data, indent=2)
            log.info(f"DADOS COMPLETOS PARA CÁLCULO DE CORRENTES: {log_data}")
        except Exception as e:
            # Se falhar, imprime apenas as chaves e alguns valores importantes
            log.info(f"CHAVES PARA CÁLCULO DE CORRENTES: {list(transformer_data.keys())}")
            log.info(f"TIPO PARA CÁLCULO DE CORRENTES: {transformer_data.get('tipo_transformador')}")
            log.info(f"POTÊNCIA PARA CÁLCULO DE CORRENTES: {transformer_data.get('potencia_mva')}")
            log.info(f"TENSÃO AT PARA CÁLCULO DE CORRENTES: {transformer_data.get('tensao_at')}")
            log.info(f"TENSÃO BT PARA CÁLCULO DE CORRENTES: {transformer_data.get('tensao_bt')}")
            log.info(f"ERRO AO SERIALIZAR PARA LOG DADOS PARA CÁLCULO DE CORRENTES: {e}")
        log.info("===============================================================")

        log.debug("[MCP] Calculating nominal currents...")
        log.info(f"[MCP Calc Currents] Dados de entrada: {transformer_data}")

        # Se transformer_data for None ou vazio, criar um dicionário com valores padrão
        if not transformer_data:
            log.warning("[MCP Calc Currents] Dados vazios! Criando dicionário com valores padrão")
            transformer_data = {
                'tipo_transformador': 'Trifásico',
                'potencia_mva': 10.0,
                'tensao_at': 138.0,
                'tensao_bt': 13.8,
                'tensao_terciario': 0.0
            }

        # Extrair valores
        tipo = transformer_data.get('tipo_transformador', 'Trifásico')  # Default para Trifásico
        potencia_str = transformer_data.get('potencia_mva')
        tensao_at_str = transformer_data.get('tensao_at')
        tensao_at_maior_str = transformer_data.get('tensao_at_tap_maior')
        tensao_at_menor_str = transformer_data.get('tensao_at_tap_menor')
        tensao_bt_str = transformer_data.get('tensao_bt')
        tensao_terciario_str = transformer_data.get('tensao_terciario')

        result = {k: None for k in ['corrente_nominal_at', 'corrente_nominal_at_tap_maior', 'corrente_nominal_at_tap_menor', 'corrente_nominal_bt', 'corrente_nominal_terciario']}

        def safe_float(value):
            if value is None or value == '':
                return 0  # Retorna 0 em vez de None para garantir o cálculo
            try:
                # Tenta converter para float, substituindo vírgula por ponto se necessário
                if isinstance(value, str):
                    return float(value.replace(',','.'))
                return float(value)
            except (ValueError, TypeError):
                log.warning(f"[MCP Calc Currents] Erro ao converter valor: {value}")
                return 0  # Retorna 0 em vez de None para garantir o cálculo

        potencia = safe_float(potencia_str)
        tensao_at = safe_float(tensao_at_str)
        tensao_at_maior = safe_float(tensao_at_maior_str)
        tensao_at_menor = safe_float(tensao_at_menor_str)
        tensao_bt = safe_float(tensao_bt_str)
        tensao_terciario = safe_float(tensao_terciario_str)

        # Verificação mais detalhada dos dados
        log.info(f"[MCP Calc Currents] Valores convertidos: tipo={tipo}, potencia={potencia}, " +
                f"tensao_at={tensao_at}, tensao_bt={tensao_bt}, tensao_terciario={tensao_terciario}")

        # Usar valores padrão se necessário
        if potencia <= 0:
            log.warning("[MCP Calc Currents] Potência inválida ou ausente. Usando valor padrão de 10 MVA.")
            potencia = 10.0  # Valor padrão para permitir cálculo

        if tensao_at <= 0:
            log.warning("[MCP Calc Currents] Tensão AT inválida ou ausente. Usando valor padrão de 138 kV.")
            tensao_at = 138.0  # Valor padrão para permitir cálculo

        if tensao_at_maior <= 0:
            tensao_at_maior = tensao_at  # Usa tensão AT como fallback

        if tensao_at_menor <= 0:
            tensao_at_menor = tensao_at  # Usa tensão AT como fallback

        if tensao_bt <= 0:
            log.warning("[MCP Calc Currents] Tensão BT inválida ou ausente. Usando valor padrão de 13.8 kV.")
            tensao_bt = 13.8  # Valor padrão para permitir cálculo

        log.debug(f"[MCP Calc Currents] Valores finais para cálculo: Potencia: {potencia}, Tensao AT: {tensao_at}, Tensao BT: {tensao_bt}, Tensao Terciario: {tensao_terciario}")

        try:
            # Fator para cálculo da corrente
            sqrt3 = math.sqrt(3)

            # Cálculo das correntes com base no tipo de transformador
            if tipo == 'Trifásico':
                # Para transformadores trifásicos: I = S * 1000 / (√3 * V)
                # Agora sempre calculamos as correntes, pois garantimos que os valores são válidos
                result['corrente_nominal_at'] = round((potencia * 1000) / (sqrt3 * tensao_at), 2)
                log.info(f"[MCP Calc Currents] Corrente AT calculada: {result['corrente_nominal_at']}A")

                result['corrente_nominal_at_tap_maior'] = round((potencia * 1000) / (sqrt3 * tensao_at_maior), 2)
                log.info(f"[MCP Calc Currents] Corrente AT tap maior calculada: {result['corrente_nominal_at_tap_maior']}A")

                result['corrente_nominal_at_tap_menor'] = round((potencia * 1000) / (sqrt3 * tensao_at_menor), 2)
                log.info(f"[MCP Calc Currents] Corrente AT tap menor calculada: {result['corrente_nominal_at_tap_menor']}A")

                result['corrente_nominal_bt'] = round((potencia * 1000) / (sqrt3 * tensao_bt), 2)
                log.info(f"[MCP Calc Currents] Corrente BT calculada: {result['corrente_nominal_bt']}A")

                # Só calcula para terciário se a tensão for maior que zero
                if tensao_terciario > 0:
                    result['corrente_nominal_terciario'] = round((potencia * 1000) / (sqrt3 * tensao_terciario), 2)
                    log.info(f"[MCP Calc Currents] Corrente Terciário calculada: {result['corrente_nominal_terciario']}A")
            else:
                # Para transformadores monofásicos: I = S * 1000 / V
                # Agora sempre calculamos as correntes, pois garantimos que os valores são válidos
                result['corrente_nominal_at'] = round((potencia * 1000) / tensao_at, 2)
                log.info(f"[MCP Calc Currents] Corrente AT calculada (monofásico): {result['corrente_nominal_at']}A")

                result['corrente_nominal_at_tap_maior'] = round((potencia * 1000) / tensao_at_maior, 2)
                log.info(f"[MCP Calc Currents] Corrente AT tap maior calculada (monofásico): {result['corrente_nominal_at_tap_maior']}A")

                result['corrente_nominal_at_tap_menor'] = round((potencia * 1000) / tensao_at_menor, 2)
                log.info(f"[MCP Calc Currents] Corrente AT tap menor calculada (monofásico): {result['corrente_nominal_at_tap_menor']}A")

                result['corrente_nominal_bt'] = round((potencia * 1000) / tensao_bt, 2)
                log.info(f"[MCP Calc Currents] Corrente BT calculada (monofásico): {result['corrente_nominal_bt']}A")

                # Só calcula para terciário se a tensão for maior que zero
                if tensao_terciario > 0:
                    result['corrente_nominal_terciario'] = round((potencia * 1000) / tensao_terciario, 2)
                    log.info(f"[MCP Calc Currents] Corrente Terciário calculada (monofásico): {result['corrente_nominal_terciario']}A")

            # Resumo dos resultados
            log.info(f"[MCP Calc Currents] Resumo das correntes calculadas: {result}")

        except Exception as e:
            log.error(f"[MCP Calc Currents] Erro no cálculo: {e}", exc_info=True)
            # Em caso de erro, tenta um cálculo mais simples
            try:
                # Valores padrão para garantir algum resultado
                if tipo == 'Trifásico':
                    result['corrente_nominal_at'] = round((potencia * 1000) / (sqrt3 * tensao_at), 2)
                    result['corrente_nominal_bt'] = round((potencia * 1000) / (sqrt3 * tensao_bt), 2)
                else:
                    result['corrente_nominal_at'] = round((potencia * 1000) / tensao_at, 2)
                    result['corrente_nominal_bt'] = round((potencia * 1000) / tensao_bt, 2)

                log.warning(f"[MCP Calc Currents] Cálculo simplificado após erro: AT={result['corrente_nominal_at']}A, BT={result['corrente_nominal_bt']}A")
            except Exception as e2:
                log.error(f"[MCP Calc Currents] Erro no cálculo simplificado: {e2}", exc_info=True)
                # Valores fixos em caso de erro total
                result['corrente_nominal_at'] = 100.0
                result['corrente_nominal_bt'] = 1000.0
                log.warning("[MCP Calc Currents] Usando valores fixos após falha total: AT=100A, BT=1000A")

        log.debug(f"[MCP] Correntes calculadas: {result}")
        return result

    def calculate_visibility_styles(self, transformer_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
        """ Calculates visibility styles based on provided or internal transformer data. """
        if transformer_data is None:
            transformer_data = self.get_data('transformer-inputs-store')

        # Log detalhado dos dados usados para calcular os estilos de visibilidade
        log.info("===============================================================")
        log.info("[MCP VISIBILITY] DADOS USADOS PARA CÁLCULO DE ESTILOS:")
        try:
            # Tenta imprimir os dados completos
            log_data = json.dumps(transformer_data, indent=2)
            log.info(f"DADOS COMPLETOS PARA CÁLCULO DE ESTILOS: {log_data}")
        except Exception as e:
            # Se falhar, imprime apenas as chaves e alguns valores importantes
            log.info(f"CHAVES PARA CÁLCULO DE ESTILOS: {list(transformer_data.keys())}")
            log.info(f"TIPO PARA CÁLCULO DE ESTILOS: {transformer_data.get('tipo_transformador')}")
            log.info(f"CONEXÃO AT PARA CÁLCULO DE ESTILOS: {transformer_data.get('conexao_at')}")
            log.info(f"CONEXÃO BT PARA CÁLCULO DE ESTILOS: {transformer_data.get('conexao_bt')}")
            log.info(f"CLASSE AT PARA CÁLCULO DE ESTILOS: {transformer_data.get('classe_tensao_at')}")
            log.info(f"ERRO AO SERIALIZAR PARA LOG DADOS PARA CÁLCULO DE ESTILOS: {e}")
        log.info("===============================================================")

        log.debug("[MCP] Calculating visibility styles...")
        # Estilos base
        style_hidden = {'display': 'none'}
        style_visible_block = {'display': 'block'} # Usado para a maioria
        style_visible_flex = {'display': 'flex', 'alignItems': 'center'} # Para SIL

        # Valores default
        styles = {
            'conexao_at_style': style_visible_block,
            'conexao_bt_style': style_visible_block,
            'conexao_terciario_style': style_visible_block,
            'neutro_at_style': style_hidden, # Referente à coluna/div da classe neutro
            'neutro_bt_style': style_hidden,
            'neutro_ter_style': style_hidden,
            'nbi_neutro_at_style': style_hidden, # Referente à coluna/div do NBI neutro
            'nbi_neutro_bt_style': style_hidden,
            'nbi_neutro_ter_style': style_hidden,
            'sil_at_style': style_hidden, # Referente à coluna/div do SIL
            'sil_bt_style': style_hidden,
            'sil_terciario_style': style_hidden
        }

        tipo = transformer_data.get('tipo_transformador')
        conexao_at = transformer_data.get('conexao_at') # e.g., 'estrela', 'triangulo'
        conexao_bt = transformer_data.get('conexao_bt')
        conexao_terciario = transformer_data.get('conexao_terciario')

        def safe_float(value):
            if value is None or value == '': return None
            try: return float(str(value).replace(',','.'))
            except (ValueError, TypeError): return None

        classe_at = safe_float(transformer_data.get('classe_tensao_at'))
        classe_bt = safe_float(transformer_data.get('classe_tensao_bt'))
        classe_terciario = safe_float(transformer_data.get('classe_tensao_terciario'))

        if tipo == 'Monofásico':
            # Esconder tudo relacionado a conexões e neutros
            styles['conexao_at_style'] = style_hidden
            styles['conexao_bt_style'] = style_hidden
            styles['conexao_terciario_style'] = style_hidden
            styles['neutro_at_style'] = style_hidden
            styles['neutro_bt_style'] = style_hidden
            styles['neutro_ter_style'] = style_hidden
            styles['nbi_neutro_at_style'] = style_hidden
            styles['nbi_neutro_bt_style'] = style_hidden
            styles['nbi_neutro_ter_style'] = style_hidden
        else: # Trifásico
            # Mostrar campos de neutro se a conexão for Estrela COM Neutro ('estrela' no valor do dropdown)
            if conexao_at == 'estrela': styles['neutro_at_style'] = style_visible_block; styles['nbi_neutro_at_style'] = style_visible_block
            if conexao_bt == 'estrela': styles['neutro_bt_style'] = style_visible_block; styles['nbi_neutro_bt_style'] = style_visible_block
            if conexao_terciario == 'estrela': styles['neutro_ter_style'] = style_visible_block; styles['nbi_neutro_ter_style'] = style_visible_block

        # Mostrar SIL se classe >= 170 kV
        if classe_at is not None and classe_at >= 170: styles['sil_at_style'] = style_visible_flex
        if classe_bt is not None and classe_bt >= 170: styles['sil_bt_style'] = style_visible_flex
        if classe_terciario is not None and classe_terciario >= 170: styles['sil_terciario_style'] = style_visible_flex

        log.debug(f"[MCP] Estilos calculados: {styles}")
        return styles

    # --- Event System Methods (Opcional, mas útil para desacoplamento) ---

    def add_listener(self, store_id: str, callback: callable) -> None:
        """ Add a listener for changes to a specific store. """
        if store_id not in self._listeners: self._listeners[store_id] = []
        if callback not in self._listeners[store_id]:
            self._listeners[store_id].append(callback)
            log.debug(f"MCP Added listener for store: {store_id}")

    def remove_listener(self, store_id: str, callback: callable) -> None:
        """ Remove a listener for changes to a specific store. """
        if store_id in self._listeners and callback in self._listeners[store_id]:
            self._listeners[store_id].remove(callback)
            log.debug(f"MCP Removed listener for store: {store_id}")

    def _notify_listeners(self, store_id: str, data: Dict[str, Any]) -> None:
        """ Notify all listeners for a specific store. """
        if store_id in self._listeners:
            log.debug(f"MCP Notifying {len(self._listeners[store_id])} listeners for store: {store_id}")

            # Log detalhado dos dados enviados para os listeners
            if store_id == 'transformer-inputs-store':
                import json
                log.info("===============================================================")
                log.info("[MCP NOTIFY] DADOS ENVIADOS PARA LISTENERS:")
                try:
                    # Tenta imprimir os dados completos
                    log_data = json.dumps(data, indent=2)
                    log.info(f"DADOS COMPLETOS ENVIADOS PARA LISTENERS: {log_data}")
                except Exception as e:
                    # Se falhar, imprime apenas as chaves e alguns valores importantes
                    log.info(f"CHAVES ENVIADAS PARA LISTENERS: {list(data.keys())}")
                    log.info(f"TIPO ENVIADO PARA LISTENERS: {data.get('tipo_transformador')}")
                    log.info(f"POTÊNCIA ENVIADA PARA LISTENERS: {data.get('potencia_mva')}")
                    log.info(f"TENSÃO AT ENVIADA PARA LISTENERS: {data.get('tensao_at')}")
                    log.info(f"TENSÃO BT ENVIADA PARA LISTENERS: {data.get('tensao_bt')}")
                    log.info(f"ERRO AO SERIALIZAR PARA LOG DADOS ENVIADOS PARA LISTENERS: {e}")
                log.info("===============================================================")

            for callback_func in self._listeners[store_id]:
                try:
                    callback_func(data) # Passa os dados atuais do store
                    log.info(f"[MCP NOTIFY] Listener notificado com sucesso para store: {store_id}")
                except Exception as e:
                    log.error(f"MCP Error in listener for store {store_id}: {e}", exc_info=True)

    # --- Data Validation Method Stub ---

    def validate_data(self, store_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """ Placeholder for data validation logic specific to each store. """
        errors = {}
        if store_id == 'transformer-inputs-store':
            # Import validator only when needed
            from components.validators import validate_dict_inputs
            # Define validation rules specific to transformer inputs
            rules = {
                'potencia_mva': {'required': True, 'positive': True, 'label': 'Potência'},
                'tensao_at': {'required': True, 'positive': True, 'label': 'Tensão AT'},
                'tensao_bt': {'required': True, 'positive': True, 'label': 'Tensão BT'},
                'frequencia': {'required': True, 'min': 50, 'max': 60, 'label': 'Frequência'},
                'impedancia': {'required': False, 'min': 0.1, 'max': 30, 'label': 'Impedância Nom.'}, # Allow None/empty
                # Add more rules for other fields as needed
            }
            # Ensure data is a dict before validating
            if isinstance(data, dict):
                 errors = validate_dict_inputs(data, rules)
            else:
                 errors['_data_format'] = ["Formato de dados inválido para validação."]
        # Add validation logic for other stores here
        return errors