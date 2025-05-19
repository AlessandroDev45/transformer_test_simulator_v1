# utils/tabela_utils.py

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

# Configuração básica do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variável global para armazenar os dados carregados
_TABELA_DADOS: Optional[Dict[str, Any]] = None
_CAMINHO_ARQUIVO = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "tabela.json"
)  # Assume que tabela.json está na raiz


def carregar_tabela(caminho_arquivo: str = _CAMINHO_ARQUIVO) -> Dict[str, Any]:
    """
    Carrega os dados do arquivo tabela.json.

    Args:
        caminho_arquivo (str): O caminho para o arquivo tabela.json.

    Returns:
        Dict[str, Any]: Um dicionário contendo os dados da tabela.

    Raises:
        FileNotFoundError: Se o arquivo tabela.json não for encontrado.
        json.JSONDecodeError: Se o arquivo não for um JSON válido.
    """
    global _TABELA_DADOS
    if _TABELA_DADOS is not None:
        logging.debug("Tabela já carregada, retornando dados cacheados.")
        return _TABELA_DADOS

    logging.info(f"Carregando tabela de isolamento de: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            _TABELA_DADOS = json.load(f)
        logging.info("Tabela de isolamento carregada com sucesso.")
        return _TABELA_DADOS
    except FileNotFoundError:
        logging.error(f"Erro: Arquivo tabela.json não encontrado em {caminho_arquivo}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar JSON do arquivo {caminho_arquivo}: {e}")
        raise
    except Exception as e:
        logging.error(f"Erro inesperado ao carregar a tabela: {e}")
        raise


def _get_dados() -> Dict[str, Any]:
    """Função auxiliar para garantir que os dados estão carregados."""
    if _TABELA_DADOS is None:
        return carregar_tabela()
    return _TABELA_DADOS


def listar_combinacoes_por_um(um_valor: float, norma_prefix: str) -> List[Dict[str, Any]]:
    """
    Lista todas as combinações de níveis de isolamento padronizadas para uma
    dada tensão Um e norma (prefixo 'IEC' ou 'IEEE').

    Esta função substitui a busca ambígua anterior, retornando todas as
    opções válidas conforme as tabelas normativas.

    Args:
        um_valor (float): O valor da tensão máxima do equipamento (Um) em kV.
        norma_prefix (str): O prefixo da norma ('IEC' para IEC/NBR, 'IEEE' para IEEE).

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, onde cada dicionário
                              representa uma combinação padronizada válida.
                              Retorna lista vazia se nenhuma combinação for encontrada.
    """
    dados = _get_dados()
    combinacoes_encontradas = []
    norma_prefix = norma_prefix.upper()

    if "insulation_levels" not in dados:
        logging.warning("Seção 'insulation_levels' não encontrada na tabela.")
        return []

    try:
        for nivel in dados.get("insulation_levels", []):
            # Verifica se a chave 'standard' e 'um_kv' existem e não são None
            if nivel.get("standard") and nivel.get("um_kv") is not None:
                # Compara como string para evitar problemas de float vs int
                um_kv_str = str(nivel.get("um_kv", ""))
                um_valor_str = str(um_valor)

                if nivel["standard"].upper().startswith(norma_prefix) and um_kv_str == um_valor_str:
                    combinacoes_encontradas.append(nivel)

        if not combinacoes_encontradas:
            logging.warning(
                f"Nenhuma combinação encontrada para Um={um_valor} kV e norma {norma_prefix}."
            )
        else:
            logging.info(
                f"{len(combinacoes_encontradas)} combinação(ões) encontrada(s) para Um={um_valor} kV e norma {norma_prefix}."
            )

        return combinacoes_encontradas
    except Exception as e:
        logging.error(f"Erro ao listar combinações por Um: {e}")
        return []


def buscar_combinacao_por_id(id_combinacao: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma combinação específica de nível de isolamento pelo seu ID único.

    Args:
        id_combinacao (str): O ID único da combinação (ex: 'IEC_72.5_325_NA', 'IEEE_115_550_460').

    Returns:
        Optional[Dict[str, Any]]: O dicionário da combinação encontrada ou None se não encontrada.
    """
    dados = _get_dados()
    id_busca = id_combinacao.upper()

    if "insulation_levels" not in dados:
        logging.warning("Seção 'insulation_levels' não encontrada na tabela.")
        return None

    try:
        for nivel in dados.get("insulation_levels", []):
            if nivel.get("id", "").upper() == id_busca:
                logging.info(f"Combinação encontrada para ID: {id_combinacao}")
                return nivel
        logging.warning(f"Nenhuma combinação encontrada para o ID: {id_combinacao}")
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar combinação por ID: {e}")
        return None


# --- Funções para obter valores específicos (usando o ID único) ---


def obter_valor_por_id(id_combinacao: str, chave: str) -> Optional[Any]:
    """
    Obtém um valor específico de uma combinação de isolamento usando seu ID e a chave desejada.

    Args:
        id_combinacao (str): O ID único da combinação.
        chave (str): A chave do valor desejado (ex: 'bil_kvp', 'acsd_kv_rms').

    Returns:
        Optional[Any]: O valor correspondente à chave ou None se a combinação ou a chave não forem encontradas.
    """
    combinacao = buscar_combinacao_por_id(id_combinacao)
    if combinacao:
        valor = combinacao.get(chave)
        if valor is not None:
            # logging.info(f"Valor '{chave}' para ID {id_combinacao}: {valor}")
            return valor
        else:
            logging.warning(f"Chave '{chave}' não encontrada para o ID: {id_combinacao}")
            return None
    return None


def obter_bil_por_id(id_combinacao: str) -> Optional[Union[int, float]]:
    """Obtém o BIL (kVp) para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "bil_kvp")


def obter_sil_por_id(id_combinacao: str) -> Optional[Union[int, float]]:
    """Obtém o SIL/BSL (kVp) para um ID de combinação específico."""
    # Tenta 'sil_kvp' primeiro, depois 'bsl_kvp' para compatibilidade
    valor = obter_valor_por_id(id_combinacao, "sil_kvp")
    if valor is None:
        valor = obter_valor_por_id(id_combinacao, "bsl_kvp")
    return valor


def obter_lic_por_id(id_combinacao: str) -> Optional[Union[int, float]]:
    """Obtém o LIC (kVp) para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "lic_kvp")


def obter_acsd_por_id(id_combinacao: str) -> Optional[Union[int, float]]:
    """Obtém o ACSD (kVrms) para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "acsd_kv_rms")


def obter_acld_por_id(id_combinacao: str) -> Optional[Union[int, float]]:
    """Obtém o ACLD (kVrms) para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "acld_kv_rms")


def obter_distancias_por_id(id_combinacao: str) -> Optional[Dict[str, float]]:
    """Obtém as distâncias mínimas no ar para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "distancias_min_ar_mm")


def obter_limites_dp_por_id(id_combinacao: str) -> Optional[Dict[str, int]]:
    """Obtém os limites de DP (pC) para um ID de combinação específico."""
    return obter_valor_por_id(id_combinacao, "pd_limits_pc")


def is_pd_requerido_por_id(id_combinacao: str) -> Optional[bool]:
    """Verifica se a medição de DP é requerida para um ID de combinação."""
    return obter_valor_por_id(id_combinacao, "pd_required")


def obter_perfis_dp_aplicaveis_por_id(id_combinacao: str) -> Optional[List[str]]:
    """Obtém a lista de perfis de DP aplicáveis para um ID de combinação."""
    return obter_valor_por_id(id_combinacao, "aplicable_pd_profiles")


# --- Funções de consulta adicionais (mantidas/adaptadas da estrutura anterior) ---





def obter_perfil_dp(nome_perfil: str) -> Optional[Dict[str, Any]]:
    """
    Obtém os detalhes de um perfil específico de Descarga Parcial (DP).

    Args:
        nome_perfil (str): O nome do perfil de DP (chave no JSON).

    Returns:
        Optional[Dict[str, Any]]: Dicionário com detalhes do perfil ou None.
    """
    dados = _get_dados()
    try:
        perfil = dados.get("perfis_dp", {}).get(nome_perfil)
        if perfil:
            logging.info(f"Perfil DP encontrado: {nome_perfil}")
        else:
            logging.warning(f"Nenhum perfil DP encontrado para: {nome_perfil}")
        return perfil
    except Exception as e:
        logging.error(f"Erro ao obter perfil DP: {e}")
        return None






