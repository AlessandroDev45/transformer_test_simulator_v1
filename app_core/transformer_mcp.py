# --- START OF FILE app_core/transformer_mcp.py ---

# app_core/transformer_mcp.py
"""
Master Control Program (MCP) for the Transformer Test Simulator.
Centralizes data management and logic between different modules.
"""
import logging
import json
import datetime
from typing import Dict, Any, List, Optional, Union
import copy
import math # Para sqrt em calculate_nominal_currents

# Import utility functions for data preparation
from utils.store_diagnostics import prepare_session_data, convert_numpy_types, is_json_serializable
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
        """Initialize all data stores with empty dictionaries."""
        for store_id in STORE_IDS:
            if store_id == 'transformer-inputs-store':
                # Use default values for transformer inputs
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
            elif store_id == 'simulation-status':
                # Default simulation status
                self._data[store_id] = {"running": False}
            else:
                # Empty dict for other stores
                self._data[store_id] = {}

        log.info(f"Initialized {len(self._data)} data stores")

    def get_data(self, store_id: str) -> Dict[str, Any]:
        """
        Get data from a specific store.

        Args:
            store_id: ID of the store to retrieve

        Returns:
            Dict containing the store data or empty dict if not found
        """
        if store_id not in self._data:
            log.warning(f"Attempted to access non-existent store: {store_id}")
            return {}

        return copy.deepcopy(self._data.get(store_id, {}))

    def set_data(self, store_id: str, data: Dict[str, Any], validate: bool = True) -> Dict[str, List[str]]:
        """
        Set data for a specific store.

        Args:
            store_id: ID of the store to update
            data: Data to store
            validate: Whether to validate the data before storing

        Returns:
            Dict mapping field names to lists of error messages if validation is enabled,
            empty dict otherwise
        """
        if store_id not in STORE_IDS:
            log.warning(f"Attempted to set data for non-registered store: {store_id}")
            return {}

        # Validate data if requested
        errors = {}
        if validate:
            errors = self.validate_data(store_id, data)
            if errors:
                log.warning(f"Validation errors for store {store_id}: {errors}")
                # Still store the data even if there are validation errors

        # Make a deep copy to avoid reference issues
        # Convert numpy types BEFORE storing
        try:
            self._data[store_id] = convert_numpy_types(copy.deepcopy(data), debug_path=f"set_data.{store_id}")
        except Exception as e:
             log.error(f"Erro ao converter dados para o store {store_id}: {e}")
             self._data[store_id] = {} # Fallback para dicionário vazio
             errors = {'_conversion_error': [f"Erro ao converter dados: {e}"]}

        log.debug(f"Updated data for store: {store_id}")

        # Notify listeners
        self._notify_listeners(store_id, copy.deepcopy(self._data[store_id]))

        return errors

    def clear_data(self, store_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Clear data from a specific store or all stores.

        Args:
            store_id: ID of the store to clear, or None to clear all stores

        Returns:
            Dict with updated store data
        """
        if store_id is None:
            # Clear all stores
            log.info("Clearing all data stores")
            self._initialize_stores()
        elif store_id in self._data:
            # Clear specific store
            log.info(f"Clearing data store: {store_id}")
            if store_id == 'transformer-inputs-store':
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
            elif store_id == 'simulation-status':
                self._data[store_id] = {"running": False}
            else:
                self._data[store_id] = {}
        else:
            log.warning(f"Attempted to clear non-existent store: {store_id}")

        # Return a copy of the current data state
        return {store_id: copy.deepcopy(data) for store_id, data in self._data.items()}

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Get data from all stores.

        Returns:
            Dict containing all store data
        """
        return copy.deepcopy(self._data)

    def get_all_stores(self) -> Dict[str, Dict[str, Any]]:
        """
        Get data from all stores (alias for get_all_data).

        Returns:
            Dict containing all store data
        """
        return self.get_all_data()

    def load_session(self, session_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Load a session from the database.

        Args:
            session_id: ID of the session to load

        Returns:
            Dict containing the loaded session data
        """
        try:
            log.info(f"Loading session with ID: {session_id}")
            session_data = get_test_session_details(session_id)

            if not session_data or 'store_data' not in session_data:
                log.error(f"Failed to load session {session_id}: Invalid data format")
                return {}

            # Update internal data stores with loaded data
            store_data = session_data['store_data']
            for store_id in STORE_IDS:
                if store_id in store_data:
                    # Perform conversion before setting to MCP to handle potential old data formats
                    try:
                        self._data[store_id] = convert_numpy_types(store_data[store_id], debug_path=f"load_session.{store_id}")
                    except Exception as e:
                         log.error(f"Erro ao converter dados carregados para o store {store_id}: {e}")
                         self._data[store_id] = {} # Fallback
                else:
                     # If a store ID is missing in the saved data, reset it to default
                    if store_id == 'transformer-inputs-store':
                        self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
                    elif store_id == 'simulation-status':
                        self._data[store_id] = {"running": False}
                    else:
                        self._data[store_id] = {}
                    log.warning(f"Store '{store_id}' not found in loaded session {session_id}. Resetting to default.")


            log.info(f"Successfully loaded session {session_id}")
            return copy.deepcopy(self._data)
        except Exception as e:
            log.error(f"Error loading session {session_id}: {e}")
            return {}

    def save_session(self, session_name: str, notes: str = "") -> int:
        """
        Save the current session to the database.

        Args:
            session_name: Name for the session
            notes: Optional notes for the session

        Returns:
            ID of the saved session or -1 if failed
        """
        try:
            log.info(f"Saving session: {session_name}")

            # Check if session name already exists
            if session_name_exists(session_name):
                log.warning(f"Session name '{session_name}' already exists")
                return -1

            # Prepare data for saving (get data from internal MCP stores)
            data_to_save = {}
            for store_id in STORE_IDS:
                 # Get data and ensure it's serializable BEFORE saving
                 raw_data = self.get_data(store_id)
                 try:
                      # Use the prepare_session_data logic (which includes conversion)
                      # but apply it individually to each store's data
                      prepared_store_data = prepare_session_data([raw_data], [store_id]).get(store_id, {})
                      data_to_save[store_id] = prepared_store_data
                 except Exception as e:
                      log.error(f"Erro ao preparar/converter dados do store '{store_id}' para salvar: {e}")
                      # Salva um diagnóstico de erro no lugar
                      data_to_save[store_id] = {"_save_error": True, "_error_message": str(e)}

            # Save to database using the centralized function
            session_id = save_test_session(data_to_save, session_name, notes or "")
            if session_id <= 0:
                log.error(f"Failed to save session '{session_name}' to database. ID returned: {session_id}")
                return -1

            log.info(f"Successfully saved session with ID: {session_id}")
            return session_id
        except Exception as e:
            log.error(f"Error saving session: {e}", exc_info=True)
            return -1

    def update_from_dash_store(self, store_id: str, dash_store_data: Dict[str, Any]) -> None:
        """
        Update internal data from a Dash store component.

        Args:
            store_id: ID of the store to update
            dash_store_data: Data from the Dash store component
        """
        if store_id in STORE_IDS:
            # Convert numpy types before storing
            try:
                self._data[store_id] = convert_numpy_types(copy.deepcopy(dash_store_data), debug_path=f"update_dash.{store_id}")
            except Exception as e:
                 log.error(f"Erro ao converter dados do Dash store {store_id}: {e}")
                 self._data[store_id] = {} # Fallback
            log.debug(f"Updated internal data from Dash store: {store_id}")
        else:
            log.warning(f"Attempted to update from unknown Dash store: {store_id}")

    def sync_all_from_dash_stores(self, dash_stores_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Sync all internal data from Dash store components.

        Args:
            dash_stores_data: Dict mapping store IDs to their data
        """
        for store_id, data in dash_stores_data.items():
            if store_id in STORE_IDS:
                # Convert numpy types before storing
                try:
                    self._data[store_id] = convert_numpy_types(copy.deepcopy(data), debug_path=f"sync_dash.{store_id}")
                except Exception as e:
                    log.error(f"Erro ao converter dados do Dash store (sync) {store_id}: {e}")
                    self._data[store_id] = {} # Fallback

        log.info(f"Synced {len(dash_stores_data)} stores from Dash components")

    # --- Business Logic Methods ---

    def calculate_nominal_currents(self, transformer_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Calculate nominal currents based on transformer data.

        Args:
            transformer_data: Transformer data dictionary. If None, uses internal data.

        Returns:
            Dict with calculated currents
        """
        if transformer_data is None:
            transformer_data = self.get_data('transformer-inputs-store')

        log.info("Calculating nominal currents")

        # Extract values from transformer data
        tipo = transformer_data.get('tipo_transformador')
        potencia_str = transformer_data.get('potencia_mva')
        tensao_at_str = transformer_data.get('tensao_at')
        tensao_at_maior_str = transformer_data.get('tensao_at_tap_maior')
        tensao_at_menor_str = transformer_data.get('tensao_at_tap_menor')
        tensao_bt_str = transformer_data.get('tensao_bt')
        tensao_terciario_str = transformer_data.get('tensao_terciario')

        # Initialize result dictionary
        result = {
            'corrente_nominal_at': None,
            'corrente_nominal_at_tap_maior': None,
            'corrente_nominal_at_tap_menor': None,
            'corrente_nominal_bt': None,
            'corrente_nominal_terciario': None
        }

        # Safe conversion to float
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        # Convert values to float
        potencia = safe_float(potencia_str)
        tensao_at = safe_float(tensao_at_str)
        tensao_at_maior = safe_float(tensao_at_maior_str)
        tensao_at_menor = safe_float(tensao_at_menor_str)
        tensao_bt = safe_float(tensao_bt_str)
        tensao_terciario = safe_float(tensao_terciario_str)

        # Calculate currents if we have valid values
        if potencia is not None and potencia > 0:
             # For three-phase transformers
            if tipo == 'Trifásico':
                sqrt3 = math.sqrt(3)
                if tensao_at and tensao_at > 0:
                     result['corrente_nominal_at'] = float(f"{(potencia * 1000) / (tensao_at * sqrt3):.2f}")
                if tensao_at_maior and tensao_at_maior > 0:
                    result['corrente_nominal_at_tap_maior'] = float(f"{(potencia * 1000) / (tensao_at_maior * sqrt3):.2f}")
                if tensao_at_menor and tensao_at_menor > 0:
                    result['corrente_nominal_at_tap_menor'] = float(f"{(potencia * 1000) / (tensao_at_menor * sqrt3):.2f}")
                if tensao_bt and tensao_bt > 0:
                    result['corrente_nominal_bt'] = float(f"{(potencia * 1000) / (tensao_bt * sqrt3):.2f}")
                if tensao_terciario and tensao_terciario > 0:
                    result['corrente_nominal_terciario'] = float(f"{(potencia * 1000) / (tensao_terciario * sqrt3):.2f}")
            # For single-phase transformers
            elif tipo == 'Monofásico':
                if tensao_at and tensao_at > 0:
                    result['corrente_nominal_at'] = float(f"{(potencia * 1000) / tensao_at:.2f}")
                if tensao_at_maior and tensao_at_maior > 0:
                    result['corrente_nominal_at_tap_maior'] = float(f"{(potencia * 1000) / tensao_at_maior:.2f}")
                if tensao_at_menor and tensao_at_menor > 0:
                    result['corrente_nominal_at_tap_menor'] = float(f"{(potencia * 1000) / tensao_at_menor:.2f}")
                if tensao_bt and tensao_bt > 0:
                    result['corrente_nominal_bt'] = float(f"{(potencia * 1000) / tensao_bt:.2f}")
                if tensao_terciario and tensao_terciario > 0:
                    result['corrente_nominal_terciario'] = float(f"{(potencia * 1000) / tensao_terciario:.2f}")
            else:
                 log.warning(f"Tipo de transformador inválido '{tipo}' para cálculo de correntes.")

        log.info(f"Calculated currents: {result}")
        return result

    # --- Event System Methods ---

    def add_listener(self, store_id: str, callback: callable) -> None:
        """
        Add a listener for changes to a specific store.

        Args:
            store_id: ID of the store to listen for changes
            callback: Function to call when the store changes
        """
        if store_id not in self._listeners:
            self._listeners[store_id] = []

        if callback not in self._listeners[store_id]:
            self._listeners[store_id].append(callback)
            log.debug(f"Added listener for store: {store_id}")

    def remove_listener(self, store_id: str, callback: callable) -> None:
        """
        Remove a listener for changes to a specific store.

        Args:
            store_id: ID of the store
            callback: Function to remove from listeners
        """
        if store_id in self._listeners and callback in self._listeners[store_id]:
            self._listeners[store_id].remove(callback)
            log.debug(f"Removed listener for store: {store_id}")

    def _notify_listeners(self, store_id: str, data: Dict[str, Any]) -> None:
        """
        Notify all listeners for a specific store.

        Args:
            store_id: ID of the store that changed
            data: New data for the store
        """
        if store_id in self._listeners:
            for callback in self._listeners[store_id]:
                try:
                    callback(data)
                except Exception as e:
                    log.error(f"Error in listener for store {store_id}: {e}")

    # --- Data Validation Methods ---

    def validate_transformer_inputs(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate transformer input data.

        Args:
            data: Transformer input data to validate

        Returns:
            Dict mapping field names to lists of error messages
        """
        errors = {}

        # Required fields
        required_fields = [
            'tipo_transformador',
            'potencia_mva',
            'tensao_at',
            'tensao_bt',
            'frequencia'
        ]

        # Check required fields
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                if field not in errors:
                    errors[field] = []
                errors[field].append("Campo obrigatório")

        # Validate numeric fields
        numeric_fields = [
            'potencia_mva',
            'tensao_at',
            'tensao_at_tap_maior',
            'tensao_at_tap_menor',
            'tensao_bt',
            'tensao_terciario',
            'frequencia',
            'classe_tensao_at',
            'classe_tensao_bt',
            'classe_tensao_terciario',
            'nbi_at',
            'nbi_bt',
            'nbi_terciario',
            'nbi_neutro_at',
            'nbi_neutro_bt',
            'nbi_neutro_terciario',
            'sil_at',
            'sil_bt',
            'sil_terciario'
        ]

        for field in numeric_fields:
            if field in data and data[field] not in (None, ''):
                try:
                    value = float(data[field])

                    # Check for negative values
                    if value < 0:
                        if field not in errors:
                            errors[field] = []
                        errors[field].append("Valor não pode ser negativo")

                    # Check specific ranges
                    if field == 'frequencia' and (value < 50 or value > 60):
                        if field not in errors:
                            errors[field] = []
                        errors[field].append("Frequência deve estar entre 50 e 60 Hz")

                except (ValueError, TypeError):
                    if field not in errors:
                        errors[field] = []
                    errors[field].append("Valor deve ser numérico")

        # Validate transformer type
        if 'tipo_transformador' in data and data['tipo_transformador'] not in ('Monofásico', 'Trifásico'):
            if 'tipo_transformador' not in errors:
                errors['tipo_transformador'] = []
            errors['tipo_transformador'].append("Tipo deve ser 'Monofásico' ou 'Trifásico'")

        # Validate connection types
        connection_fields = ['conexao_at', 'conexao_bt', 'conexao_terciario']
        # Updated valid connections to match Dropdown options
        valid_connections = ['estrela', 'estrela_sem_neutro', 'triangulo', ' ', ''] # Added space for Tertiary empty default

        for field in connection_fields:
            if field in data and data[field] not in (None, '') and data[field] not in valid_connections:
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"Conexão inválida: '{data[field]}'. Válidos: {', '.join(valid_connections)}")

        return errors

    def validate_data(self, store_id: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data for a specific store.

        Args:
            store_id: ID of the store
            data: Data to validate

        Returns:
            Dict mapping field names to lists of error messages
        """
        if store_id == 'transformer-inputs-store':
            return self.validate_transformer_inputs(data)

        # Add validation for other stores as needed

        return {}

    def calculate_visibility_styles(self, transformer_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
        """
        Calculate visibility styles for transformer inputs based on transformer data.

        Args:
            transformer_data: Transformer data dictionary. If None, uses internal data.

        Returns:
            Dict with visibility styles for different fields
        """
        if transformer_data is None:
            transformer_data = self.get_data('transformer-inputs-store')

        log.info("Calculating visibility styles")

        # Initialize styles
        style_hidden = {'display': 'none'}
        style_visible = {'display': 'block'}
        style_flex_visible = {'display': 'flex', 'alignItems': 'center'} # For SIL

        # Initialize result dictionary
        result = {
            'conexao_at_style': style_visible,
            'conexao_bt_style': style_visible,
            'conexao_terciario_style': style_visible,
            'neutro_at_style': style_hidden,
            'neutro_bt_style': style_hidden,
            'neutro_ter_style': style_hidden,
            'nbi_neutro_at_style': style_hidden,
            'nbi_neutro_bt_style': style_hidden,
            'nbi_neutro_ter_style': style_hidden,
            'sil_at_style': style_hidden,
            'sil_bt_style': style_hidden,
            'sil_terciario_style': style_hidden
        }

        # Extract values from transformer data
        tipo = transformer_data.get('tipo_transformador')
        conexao_at = transformer_data.get('conexao_at')
        conexao_bt = transformer_data.get('conexao_bt')
        conexao_terciario = transformer_data.get('conexao_terciario')

        # Safe conversion to float
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        # Extract class values
        classe_tensao_at = safe_float(transformer_data.get('classe_tensao_at'))
        classe_tensao_bt = safe_float(transformer_data.get('classe_tensao_bt'))
        classe_tensao_terciario = safe_float(transformer_data.get('classe_tensao_terciario'))

        # Set visibility based on transformer type
        if tipo == 'Monofásico':
            # For single-phase transformers, hide connection fields
            result['conexao_at_style'] = style_hidden
            result['conexao_bt_style'] = style_hidden
            result['conexao_terciario_style'] = style_hidden
            # Also hide neutro fields
            result['neutro_at_style'] = style_hidden
            result['nbi_neutro_at_style'] = style_hidden
            result['neutro_bt_style'] = style_hidden
            result['nbi_neutro_bt_style'] = style_hidden
            result['neutro_ter_style'] = style_hidden
            result['nbi_neutro_ter_style'] = style_hidden
        else: # Trifásico
            # Set visibility based on connection type
            if conexao_at == 'estrela': # Assuming 'estrela' is YN from Dropdown
                result['neutro_at_style'] = style_visible
                result['nbi_neutro_at_style'] = style_visible
            # For estrela_sem_neutro or triangulo, keep hidden (default)

            if conexao_bt == 'estrela':
                result['neutro_bt_style'] = style_visible
                result['nbi_neutro_bt_style'] = style_visible
            # For estrela_sem_neutro or triangulo, keep hidden

            if conexao_terciario == 'estrela':
                result['neutro_ter_style'] = style_visible
                result['nbi_neutro_ter_style'] = style_visible
            # For estrela_sem_neutro, triangulo or ' ', keep hidden


        # Set SIL field visibility based on voltage class
        if classe_tensao_at is not None and classe_tensao_at >= 170:
            result['sil_at_style'] = style_flex_visible

        if classe_tensao_bt is not None and classe_tensao_bt >= 170:
            result['sil_bt_style'] = style_flex_visible

        if classe_tensao_terciario is not None and classe_tensao_terciario >= 170:
            result['sil_terciario_style'] = style_flex_visible

        log.info(f"Calculated visibility styles")
        return result
# --- END OF FILE app_core/transformer_mcp.py ---

