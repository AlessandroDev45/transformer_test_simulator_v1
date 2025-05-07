# test_callback_registration.py
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the app
    from app import app
    
    # Check if the app is initialized
    if app is None:
        log.error("App is None")
        sys.exit(1)
    
    # Check if the MCP is initialized
    if not hasattr(app, 'mcp') or app.mcp is None:
        log.error("MCP is not initialized")
        sys.exit(1)
    
    # Check if the callback map is initialized
    if not hasattr(app, 'callback_map') or app.callback_map is None:
        log.error("Callback map is not initialized")
        sys.exit(1)
    
    # Print the number of callbacks
    log.info(f"Number of callbacks registered: {len(app.callback_map)}")
    
    # Check if the update_transformer_calculations_and_mcp callback is registered
    update_callback_found = False
    for callback_id, callback_info in app.callback_map.items():
        if "update_transformer_calculations_and_mcp" in callback_id:
            update_callback_found = True
            log.info(f"Found update_transformer_calculations_and_mcp callback: {callback_id}")
            log.info(f"Callback info: {callback_info}")
            
            # Check the inputs
            inputs = callback_info.get('inputs', [])
            log.info(f"Number of inputs: {len(inputs)}")
            for i, input_info in enumerate(inputs):
                log.info(f"Input {i}: {input_info}")
            
            # Check the outputs
            outputs = callback_info.get('outputs', [])
            log.info(f"Number of outputs: {len(outputs)}")
            for i, output_info in enumerate(outputs):
                log.info(f"Output {i}: {output_info}")
    
    if not update_callback_found:
        log.error("update_transformer_calculations_and_mcp callback not found")
        
        # List all callbacks
        log.info("Listing all callbacks:")
        for callback_id in app.callback_map.keys():
            log.info(f"Callback: {callback_id}")
        
        sys.exit(1)
    
    log.info("Callback registration test completed successfully")
    
except Exception as e:
    log.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
