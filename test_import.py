# test_import.py
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the callback module directly
    log.info("Importing callbacks.transformer_inputs...")
    import callbacks.transformer_inputs
    log.info("Import successful")
    
    # Check if the module has the update_transformer_calculations_and_mcp function
    if hasattr(callbacks.transformer_inputs, 'update_transformer_calculations_and_mcp'):
        log.info("update_transformer_calculations_and_mcp function found")
    else:
        log.error("update_transformer_calculations_and_mcp function not found")
    
except Exception as e:
    log.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
