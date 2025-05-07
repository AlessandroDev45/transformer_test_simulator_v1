# test_import_fix.py
"""
Script para testar a importação do módulo transformer_inputs_fix.
"""
import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

def main():
    """Função principal."""
    log.info("Iniciando teste de importação...")
    
    try:
        # Importar o módulo
        from callbacks import transformer_inputs_fix
        log.info("Módulo transformer_inputs_fix importado com sucesso!")
        
        # Verificar se a função register_transformer_inputs_callbacks existe
        if hasattr(transformer_inputs_fix, 'register_transformer_inputs_callbacks'):
            log.info("Função register_transformer_inputs_callbacks encontrada!")
        else:
            log.error("Função register_transformer_inputs_callbacks NÃO encontrada!")
        
        # Verificar se o módulo transformer_inputs.py também pode ser importado
        try:
            from callbacks import transformer_inputs
            log.info("Módulo transformer_inputs importado com sucesso!")
        except ImportError as e:
            log.error(f"Erro ao importar transformer_inputs: {e}")
        
        log.info("Teste concluído com sucesso!")
        return True
    except Exception as e:
        log.error(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
