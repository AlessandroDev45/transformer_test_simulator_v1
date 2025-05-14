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


def obter_info_ensaio_dieletrico(tipo_ensaio: str) -> Optional[Dict[str, Any]]:
    """
    Obtém informações sobre um tipo específico de ensaio dielétrico.

    Args:
        tipo_ensaio (str): O nome do tipo de ensaio (chave no JSON).

    Returns:
        Optional[Dict[str, Any]]: Dicionário com informações do ensaio ou None.
    """
    dados = _get_dados()
    try:
        info = dados.get("ensaios_dieletricos", {}).get(tipo_ensaio)
        if info:
            logging.info(f"Informações encontradas para ensaio: {tipo_ensaio}")
        else:
            logging.warning(f"Nenhuma informação encontrada para ensaio: {tipo_ensaio}")
        return info
    except Exception as e:
        logging.error(f"Erro ao obter informações do ensaio dielétrico: {e}")
        return None


def obter_sequencia_ensaio(tipo_sequencia: str) -> Optional[List[Dict[str, Any]]]:
    """
    Obtém a sequência de passos para um tipo específico de ensaio.

    Args:
        tipo_sequencia (str): O nome da sequência de ensaio (chave no JSON).

    Returns:
        Optional[List[Dict[str, Any]]]: Lista de passos da sequência ou None.
    """
    dados = _get_dados()
    try:
        seq = dados.get("sequencias_ensaio", {}).get(tipo_sequencia)
        if seq:
            logging.info(f"Sequência encontrada para: {tipo_sequencia}")
        else:
            logging.warning(f"Nenhuma sequência encontrada para: {tipo_sequencia}")
        return seq
    except Exception as e:
        logging.error(f"Erro ao obter sequência de ensaio: {e}")
        return None


def listar_tipos_ensaios_dieletricos() -> List[str]:
    """
    Lista os nomes de todos os tipos de ensaios dielétricos definidos na tabela.

    Returns:
        List[str]: Uma lista com os nomes dos ensaios.
    """
    dados = _get_dados()
    try:
        return list(dados.get("ensaios_dieletricos", {}).keys())
    except Exception as e:
        logging.error(f"Erro ao listar tipos de ensaios dielétricos: {e}")
        return []


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


# --- Funções antigas (Deprecadas ou a serem removidas/adaptadas) ---
# Manter estas funções por compatibilidade pode ser necessário, mas idealmente
# o código que as usa deveria ser atualizado para o novo fluxo.


def buscar_valores_nbr_por_um(um_valor: float) -> List[Dict[str, Any]]:
    """
    [DEPRECADA] Use listar_combinacoes_por_um(um_valor, 'IEC') em vez disso.
    Lista todas as combinações NBR/IEC para um dado Um.
    """
    logging.warning(
        "Função 'buscar_valores_nbr_por_um' está deprecada. Use 'listar_combinacoes_por_um'."
    )
    return listar_combinacoes_por_um(um_valor, "IEC")


def buscar_valores_ieee_por_um(um_valor: float) -> List[Dict[str, Any]]:
    """
    [DEPRECADA] Use listar_combinacoes_por_um(um_valor, 'IEEE') em vez disso.
    Lista todas as combinações IEEE para um dado Um.
    """
    logging.warning(
        "Função 'buscar_valores_ieee_por_um' está deprecada. Use 'listar_combinacoes_por_um'."
    )
    return listar_combinacoes_por_um(um_valor, "IEEE")


# Exemplo de como usar as novas funções:
if __name__ == "__main__":
    try:
        # 1. Listar opções para IEC/NBR Um = 36kV
        print("\n--- Opções para IEC/NBR Um=36kV ---")
        opcoes_iec_36 = listar_combinacoes_por_um(36, "IEC")
        for opcao in opcoes_iec_36:
            print(
                f" ID: {opcao.get('id')}, BIL: {opcao.get('bil_kvp')}kVp, ACSD: {opcao.get('acsd_kv_rms')}kVrms"
            )

        # 2. Buscar detalhes de uma combinação específica pelo ID
        print("\n--- Detalhes para IEC_36_170_NA ---")
        detalhes_iec_36_170 = buscar_combinacao_por_id("IEC_36_170_NA")
        if detalhes_iec_36_170:
            print(json.dumps(detalhes_iec_36_170, indent=2))
            # Obter valores específicos
            bil = obter_bil_por_id("IEC_36_170_NA")
            acsd = obter_acsd_por_id("IEC_36_170_NA")
            dist = obter_distancias_por_id("IEC_36_170_NA")
            print(f"  Valores específicos -> BIL: {bil}, ACSD: {acsd}, Distâncias: {dist}")
        else:
            print("Combinação não encontrada.")

        # 3. Listar opções para IEEE Um = 115kV
        print("\n--- Opções para IEEE Um=115kV ---")
        opcoes_ieee_115 = listar_combinacoes_por_um(115, "IEEE")
        for opcao in opcoes_ieee_115:
            print(
                f" ID: {opcao.get('id')}, BIL: {opcao.get('bil_kvp')}kVp, SIL: {obter_sil_por_id(opcao.get('id'))}kVp, ACSD: {opcao.get('acsd_kv_rms')}kVrms, ACLD: {opcao.get('acld_kv_rms')}kVrms"
            )

        # 4. Buscar detalhes de uma combinação IEEE específica pelo ID
        print("\n--- Detalhes para IEEE_115_550_460 ---")
        detalhes_ieee_115_550 = buscar_combinacao_por_id("IEEE_115_550_460")
        if detalhes_ieee_115_550:
            print(json.dumps(detalhes_ieee_115_550, indent=2))
            sil = obter_sil_por_id("IEEE_115_550_460")
            acld = obter_acld_por_id("IEEE_115_550_460")
            print(f"  Valores específicos -> SIL: {sil}, ACLD: {acld}")

        # 5. Tentar buscar um ID inválido
        print("\n--- Buscar ID inválido ---")
        invalido = buscar_combinacao_por_id("ID_INEXISTENTE")
        if invalido is None:
            print("ID inexistente, como esperado.")

        # 6. Aplicar patch (apenas exemplo, não modifica o arquivo original)
        # Suponha que 'patch_data' seja o JSON fornecido no prompt
        patch_data = [
            {"id": "IEC_1.2_NA_NA", "acsd_kv_rms": 10, "acld_kv_rms": 10},
            {"id": "IEEE_1.2_30_NA", "acsd_kv_rms": 10, "acld_kv_rms": 10},
            {"id": "IEEE_115_350_280", "acld_kv_rms": 120},
            {"id": "IEEE_115_450_375", "acld_kv_rms": 120},
            {"id": "IEEE_115_550_460", "acld_kv_rms": 120},
            {"id": "IEEE_138_450_375", "acld_kv_rms": 145},
            {"id": "IEEE_138_550_460", "acld_kv_rms": 145},
            {"id": "IEEE_138_650_540", "acld_kv_rms": 145},
            {"id": "IEEE_161_550_460", "acld_kv_rms": 170},
            {"id": "IEEE_161_650_540", "acld_kv_rms": 170},
            {"id": "IEEE_161_750_620", "acld_kv_rms": 170},
            {"id": "IEEE_230_650_540", "acld_kv_rms": 240},
            {"id": "IEEE_230_750_620", "acld_kv_rms": 240},
            {"id": "IEEE_230_825_685", "acld_kv_rms": 240},
            {"id": "IEEE_230_900_745", "acld_kv_rms": 240},
            {"id": "IEEE_345_900_745", "acld_kv_rms": 360},
            {"id": "IEEE_345_1050_870", "acld_kv_rms": 360},
            {"id": "IEEE_345_1175_975", "acld_kv_rms": 360},
            {"id": "IEEE_500_1300_1080", "acsd_kv_rms": None, "acld_kv_rms": 550},
            {"id": "IEEE_500_1425_1180", "acsd_kv_rms": None, "acld_kv_rms": 550},
            {"id": "IEEE_500_1550_1290", "acsd_kv_rms": None, "acld_kv_rms": 550},
            {"id": "IEEE_500_1675_1390", "acsd_kv_rms": None, "acld_kv_rms": 550},
            {"id": "IEEE_500_1800_1500", "acsd_kv_rms": None, "acld_kv_rms": 550},
        ]

        print("\n--- Verificando valores após o patch (em memória) ---")
        # Criando um dicionário para acesso rápido pelo ID
        dados_atuais = _get_dados()
        niveis_por_id = {
            nivel.get("id"): nivel for nivel in dados_atuais.get("insulation_levels", [])
        }

        # Aplicando o patch
        for item_patch in patch_data:
            id_patch = item_patch.get("id")
            if id_patch in niveis_por_id:
                logging.info(f"Aplicando patch para ID: {id_patch}")
                niveis_por_id[id_patch].update({k: v for k, v in item_patch.items() if k != "id"})
            else:
                logging.warning(f"ID do patch não encontrado na tabela original: {id_patch}")

        # Verificando alguns valores após o patch
        print(
            f" IEEE_115_350_280 -> ACLD: {niveis_por_id.get('IEEE_115_350_280', {}).get('acld_kv_rms')}"
        )
        print(
            f" IEEE_230_900_745 -> ACLD: {niveis_por_id.get('IEEE_230_900_745', {}).get('acld_kv_rms')}"
        )
        print(
            f" IEEE_500_1300_1080 -> ACSD: {niveis_por_id.get('IEEE_500_1300_1080', {}).get('acsd_kv_rms')}"
        )
        print(
            f" IEEE_500_1800_1500 -> ACLD: {niveis_por_id.get('IEEE_500_1800_1500', {}).get('acld_kv_rms')}"
        )
        print(
            f" IEC_1.2_NA_NA -> ACSD: {niveis_por_id.get('IEC_1.2_NA_NA', {}).get('acsd_kv_rms')}"
        )
        print(
            f" IEEE_1.2_30_NA -> ACLD: {niveis_por_id.get('IEEE_1.2_30_NA', {}).get('acld_kv_rms')}"
        )

    except Exception as e:
        logging.exception(f"Erro no bloco de exemplo: {e}")
