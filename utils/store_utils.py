"""
Utility functions for working with dcc.Store components.
Provides functions for serializing data and ensuring consistency.
"""

import logging
from typing import Any, Dict

from utils.store_diagnostics import convert_numpy_types, is_json_serializable

log = logging.getLogger(__name__)


def prepare_data_for_store(data: Any, store_id: str = None) -> Any:
    """
    Prepares data for storage in a dcc.Store component by ensuring it's serializable.

    Args:
        data: The data to prepare
        store_id: Optional ID of the store (for logging purposes)

    Returns:
        The prepared data, ready for storage
    """
    if data is None:
        return {}

    store_name = store_id or "unknown-store"
    log.debug(f"[STORE UTILS] Preparing data for store: {store_name}")

    try:
        # First check if data is already serializable
        if is_json_serializable(data):
            log.debug(f"[STORE UTILS] Data for {store_name} is already serializable")
            return data

        # Convert numpy types and other non-serializable types
        converted_data = convert_numpy_types(data, debug_path=f"prepare_for_store.{store_name}")

        # Verify the conversion worked
        if is_json_serializable(converted_data):
            log.debug(f"[STORE UTILS] Data for {store_name} successfully converted")
            return converted_data
        else:
            # If conversion failed, log and return empty dict
            log.error(
                f"[STORE UTILS] Failed to convert data for {store_name} to serializable format"
            )
            return {"_error": "Data conversion failed", "_store_id": store_name}
    except Exception as e:
        log.error(f"[STORE UTILS] Error preparing data for {store_name}: {e}", exc_info=True)
        return {"_error": str(e), "_store_id": store_name}


def update_store_data(
    current_data: Dict[str, Any], new_data: Dict[str, Any], store_id: str = None
) -> Dict[str, Any]:
    """
    Updates store data by merging current data with new data and ensuring it's serializable.

    Args:
        current_data: The current data in the store
        new_data: The new data to merge
        store_id: Optional ID of the store (for logging purposes)

    Returns:
        The updated data, ready for storage
    """
    store_name = store_id or "unknown-store"
    log.debug(f"[STORE UTILS] Updating data for store: {store_name}")

    try:
        # Ensure current_data is a dict
        if not isinstance(current_data, dict):
            log.warning(
                f"[STORE UTILS] Current data for {store_name} is not a dict, creating new dict"
            )
            result = {}
        else:
            result = current_data.copy()

        # Ensure new_data is a dict
        if not isinstance(new_data, dict):
            log.warning(f"[STORE UTILS] New data for {store_name} is not a dict, cannot update")
            return prepare_data_for_store(result, store_id)

        # Update the data
        result.update(new_data)

        # Prepare for storage
        return prepare_data_for_store(result, store_id)
    except Exception as e:
        log.error(f"[STORE UTILS] Error updating data for {store_name}: {e}", exc_info=True)
        return {"_error": str(e), "_store_id": store_name}


def get_from_store(store_data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely gets a value from store data with a default if not found.

    Args:
        store_data: The store data
        key: The key to get
        default: The default value if key not found

    Returns:
        The value or default
    """
    if not isinstance(store_data, dict):
        return default

    return store_data.get(key, default)


def update_app_cache(data: Dict[str, Any], app=None) -> bool:
    """
    Updates the application cache with the provided data.

    Args:
        data: The data to store in the cache
        app: The application instance (if None, tries to import from app)

    Returns:
        True if successful, False otherwise
    """
    try:
        if app is None:
            from app import app

        app.transformer_data_cache = data.copy()
        log.debug("[STORE UTILS] Application cache updated successfully")
        return True
    except Exception as e:
        log.error(f"[STORE UTILS] Error updating application cache: {e}", exc_info=True)
        return False
