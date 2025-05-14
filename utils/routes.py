"""
Definição centralizada de rotas para a aplicação.
Este arquivo contém constantes para todas as rotas da aplicação,
facilitando a manutenção e evitando inconsistências.
"""

# Rotas principais (pathnames sem barra inicial)
ROUTE_HOME = "dados"
ROUTE_LOSSES = "perdas"
ROUTE_IMPULSE = "impulso"
ROUTE_DIELETRIC = "analise-dieletrica"
ROUTE_DIELECTRIC_ANALYSIS = (
    "analise-dieletrica"  # Alias para manter compatibilidade com ambos os nomes
)
ROUTE_DIELECTRIC_COMPREHENSIVE = (
    "analise-dieletrica-completa"  # Nova rota para análise dielétrica completa
)
ROUTE_APPLIED_VOLTAGE = "tensao-aplicada"
ROUTE_INDUCED_VOLTAGE = "tensao-induzida"
ROUTE_SHORT_CIRCUIT = "curto-circuito"
ROUTE_TEMPERATURE_RISE = "elevacao-temperatura"
ROUTE_HISTORY = "historico"  # Nova rota para histórico de sessões
ROUTE_STANDARDS_CONSULTATION = "consulta-normas"  # Nova rota para consulta de normas
ROUTE_STANDARDS_MANAGEMENT = "gerenciar-normas"  # Nova rota para gerenciamento de normas

# Lista de todas as rotas válidas para o menu principal
VALID_ROUTES = [
    ROUTE_HOME,
    ROUTE_LOSSES,
    ROUTE_IMPULSE,
    ROUTE_DIELETRIC,
    ROUTE_APPLIED_VOLTAGE,
    ROUTE_INDUCED_VOLTAGE,
    ROUTE_SHORT_CIRCUIT,
    ROUTE_TEMPERATURE_RISE,
    ROUTE_HISTORY,  # Histórico de sessões
    ROUTE_STANDARDS_CONSULTATION,  # Consulta de normas
]

# Lista de todas as rotas válidas, incluindo as que não aparecem no menu
ALL_VALID_ROUTES = VALID_ROUTES + [
    ROUTE_DIELECTRIC_COMPREHENSIVE,
    ROUTE_STANDARDS_MANAGEMENT,  # Gerenciamento de normas (não aparece no menu principal)
]

# Mapeamento de rotas para rótulos de navegação
ROUTE_LABELS = {
    ROUTE_HOME: "1. Dados Básicos",
    ROUTE_LOSSES: "2. Perdas",
    ROUTE_IMPULSE: "3. Impulso",
    ROUTE_DIELETRIC: "4. Análise Dielétrica",
    ROUTE_DIELECTRIC_COMPREHENSIVE: "4.1 Análise Dielétrica Completa",
    ROUTE_APPLIED_VOLTAGE: "5. Tensão Aplicada",
    ROUTE_INDUCED_VOLTAGE: "6. Tensão Induzida",
    ROUTE_SHORT_CIRCUIT: "7. Curto-Circuito",
    ROUTE_TEMPERATURE_RISE: "8. Elevação de Temperatura",
    ROUTE_HISTORY: "9. Histórico de Sessões",
    ROUTE_STANDARDS_CONSULTATION: "10. Consulta de Normas",
    ROUTE_STANDARDS_MANAGEMENT: "Gerenciamento de Normas",  # Não numerado (acesso restrito)
}


# Função auxiliar para normalizar pathnames
def normalize_pathname(pathname):
    """
    Normaliza um pathname removendo barras iniciais e finais.

    Args:
        pathname (str): O pathname a ser normalizado

    Returns:
        str: O pathname normalizado
    """
    if not pathname:
        return ""
    return pathname.strip("/")


# Função auxiliar para obter o rótulo de uma rota
def get_route_label(route):
    """
    Retorna o rótulo de uma rota.

    Args:
        route (str): A rota

    Returns:
        str: O rótulo da rota ou None se a rota não existir
    """
    return ROUTE_LABELS.get(normalize_pathname(route))


# Função auxiliar para verificar se uma rota é válida
def is_valid_route(route):
    """
    Verifica se uma rota é válida.

    Args:
        route (str): A rota a ser verificada

    Returns:
        bool: True se a rota for válida, False caso contrário
    """
    return normalize_pathname(route) in ALL_VALID_ROUTES
