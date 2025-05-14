# layouts/__init__.py
# Torna o diretório 'layouts' um pacote Python.
# Reexporta estilos centralizados para uso nos layouts.

# Importar estilos centralizados de utils.styles
from utils.styles import COLORS, COMPONENTS, MESSAGE_STYLES, SPACING, TABLE_STYLES, TYPOGRAPHY

# Exportar para uso nos layouts
__all__ = ["COLORS", "COMPONENTS", "SPACING", "TYPOGRAPHY", "TABLE_STYLES", "MESSAGE_STYLES"]
