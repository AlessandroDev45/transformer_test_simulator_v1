# --- START OF FILE app_core/standards.py ---

# app_core/standards.py
"""
Contém classes e lógica para carregar, interpretar e comparar
dados das normas ABNT NBR 5356-3 e IEEE C57.12.00 relacionadas
a ensaios dielétricos e espaçamentos de transformadores.
"""
import json  # Adicionado para carregar tabela.json
import logging
import math  # Para isnan
from typing import Any, Dict, List, Optional, Union  # Adicionar Optional e Union

import numpy as np
import pandas as pd

# Importar configurações, especialmente caminhos de arquivo
import config

log = logging.getLogger(__name__)


# --- Função Auxiliar (Específica para leitura de tabelas NBR) ---
def safe_float_convert(value):
    """Tenta converter um valor para float, lidando com strings e None.
    Especificamente trata strings com '/' pegando o primeiro valor.
    Retorna None em caso de falha.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Trata NaN e Infinito explicitamente
        if math.isnan(value) or math.isinf(value):
            log.warning(f"Valor float inválido encontrado: {value}. Retornando None.")
            return None
        return float(value)
    if isinstance(value, str):
        value_cleaned = value.strip()
        if not value_cleaned:  # String vazia
            return None
        # Se for 'NA', retorna None ou um marcador especial? Por enquanto None.
        if value_cleaned.upper() == "NA":
            return None
        try:
            # Tenta converter diretamente
            return float(value_cleaned.replace(",", "."))  # Adiciona replace para vírgula decimal
        except ValueError:
            # Tenta tratar o formato 'X/Y'
            if "/" in value_cleaned:
                try:
                    return float(value_cleaned.split("/")[0].strip().replace(",", "."))
                except ValueError:
                    log.error(
                        f"Erro ao converter parte antes de '/' em '{value_cleaned}' para float."
                    )
                    return None
            else:
                # Se não for float direto nem tiver '/', loga o erro
                log.error(f"Não foi possível converter a string '{value_cleaned}' para float.")
                return None
    # Se for outro tipo não conversível (ex: booleano, lista)
    log.error(f"Tipo de valor não suportado para conversão float: {type(value)}, valor: {value}")
    return None


# --- Classes Base e Específicas das Normas ---


class NormaBase:
    """Classe base para representação de dados de normas."""

    def __init__(self, nome_norma: str, arquivo: str = None, arquivo_json: str = None):
        self.nome_norma = nome_norma
        self.arquivo = arquivo  # Pode ser None se os dados forem hardcoded
        self.arquivo_json = arquivo_json  # Arquivo JSON com dados das normas
        self.tabelas = {}
        self.dados_json = None  # Armazenará os dados do JSON
        log.debug(
            f"Inicializando base para norma {self.nome_norma}"
            + (f" com arquivo {arquivo}" if arquivo else "")
            + (f" e JSON {arquivo_json}" if arquivo_json else "")
        )

        # Garante que o método de carregamento específico seja chamado
        self._carregar_dados()

    def _carregar_dados(self):
        """Carrega os dados da norma (Excel ou JSON)."""
        json_loaded = self._carregar_json()
        if not json_loaded:
            log.info(
                f"Falha ao carregar JSON para {self.nome_norma}. Tentando carregar Excel (se definido)..."
            )
            import os

            if self.arquivo and os.path.exists(self.arquivo):
                self._carregar_excel()
            else:
                log.warning(
                    f"Nem JSON nem arquivo Excel ({self.arquivo}) encontrados ou definidos para {self.nome_norma}."
                )
                # Considerar carregar dados hardcoded como fallback final aqui se necessário
                self._carregar_hardcoded_fallback()  # Adicionar um método de fallback

    def _carregar_excel(self):
        """Carrega dados do arquivo Excel (método antigo)."""
        try:
            log.info(f"Tentando carregar dados Excel de {self.arquivo} para {self.nome_norma}")
            excel_data = pd.ExcelFile(self.arquivo)
            for sheet_name in excel_data.sheet_names:
                try:
                    df = excel_data.parse(sheet_name)
                    # Limpa nomes das colunas
                    df.columns = [str(col).strip() for col in df.columns]
                    # Preenche NaNs com None para consistência
                    self.tabelas[sheet_name] = df.where(pd.notnull(df), None)
                    log.debug(f"Planilha '{sheet_name}' carregada do Excel para {self.nome_norma}.")
                except Exception as e_sheet:
                    log.error(
                        f"Erro ao carregar planilha '{sheet_name}' do Excel ({self.arquivo}): {e_sheet}"
                    )
            log.info(f"Dados Excel para {self.nome_norma} carregados.")
        except FileNotFoundError:
            log.error(f"Arquivo Excel {self.arquivo} não encontrado para {self.nome_norma}.")
            self.tabelas = {}
        except Exception as e:
            log.exception(f"Erro ao carregar dados Excel para {self.nome_norma}: {e}")
            self.tabelas = {}

    def _carregar_json(self) -> bool:
        """Carrega dados do arquivo JSON."""
        if not self.arquivo_json:
            log.warning(f"Arquivo JSON para {self.nome_norma} não definido.")
            return False

        try:
            import os

            # Verifica se o caminho completo já foi fornecido
            if not os.path.isabs(self.arquivo_json):
                # Assume que está na raiz do projeto se não for absoluto
                json_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), self.arquivo_json
                )
            else:
                json_path = self.arquivo_json

            if not os.path.exists(json_path):
                log.error(f"Arquivo JSON '{json_path}' não encontrado.")
                return False

            with open(json_path, "r", encoding="utf-8") as f:
                self.dados_json = json.load(f)

            # Validação básica da estrutura JSON
            if not isinstance(self.dados_json, dict) or not self.dados_json:
                log.error(f"Arquivo JSON {json_path} está vazio ou não é um dicionário válido.")
                self.dados_json = None
                return False

            # Verificar se a estrutura principal (insulation_levels) existe
            if "insulation_levels" not in self.dados_json:
                log.warning(f"Estrutura 'insulation_levels' não encontrada no JSON {json_path}.")
                # Poderia tentar converter formatos antigos aqui se necessário
                # self.dados_json = self._converter_formato_antigo(self.dados_json) # Exemplo
                # if 'insulation_levels' not in self.dados_json: # Revalida após conversão
                #    log.error("Falha ao converter para formato esperado. JSON inválido.")
                #    self.dados_json = None
                #    return False

            log.info(f"Dados JSON para {self.nome_norma} carregados com sucesso de {json_path}")
            self.tabelas[
                "json_loaded"
            ] = True  # Indica que JSON foi carregado (para compatibilidade)
            return True

        except json.JSONDecodeError as e:
            log.error(f"Erro de decodificação JSON em {json_path}: {e}")
            self.dados_json = None
            return False
        except Exception as e:
            log.exception(
                f"Erro inesperado ao carregar dados JSON para {self.nome_norma} de {self.arquivo_json}: {e}"
            )
            self.dados_json = None
            return False

    def _carregar_hardcoded_fallback(self):
        """Método de fallback para carregar dados hardcoded se arquivos falharem."""
        log.warning(f"Usando dados hardcoded como fallback para {self.nome_norma}.")
        # Aqui você colocaria os dicionários/estruturas de dados definidos diretamente no código
        # Exemplo:
        # if self.nome_norma == "IEEE C57.12.00":
        #     self.tabelas['Table_4'] = pd.DataFrame(...) # Dados hardcoded da Tabela 4 IEEE
        #     # ... etc ...
        # elif self.nome_norma == "NBR 5356-3":
        #     # Carregar dados JSON hardcoded ou estrutura similar
        #     self.dados_json = {...} # Estrutura JSON hardcoded
        #     self.tabelas["json_loaded"] = True
        pass  # Implementar se necessário

    # Métodos restantes mantidos (converter, get_nome_completo, etc.)
    def _converter_novo_formato_json(self, json_data):
        """Converte o novo formato JSON para o formato esperado pelo código existente."""
        try:
            log.info("Convertendo novo formato JSON para formato compatível")

            # Extrai as informações de levels e distance_mm
            levels = json_data.get("levels", {})
            distances = json_data.get("distance_mm", {})

            # Cria uma lista de faixas de tensão no formato esperado
            faixas = []

            # Cria faixas de tensão para cada valor de Um
            for um_valor_str, level_data in levels.items():
                um_float = safe_float_convert(um_valor_str)
                if um_float is None:
                    log.warning(f"Valor de Um inválido: {um_valor_str}")
                    continue

                # Define os limites da faixa
                # Para valores menores que 100kV, usamos uma margem de 5%
                # Para valores maiores, usamos faixas mais específicas
                if um_float < 100:
                    um_min = um_float * 0.95
                    um_max = um_float * 1.05
                else:
                    # Encontra o próximo valor de Um na lista
                    valores_um = sorted(
                        [
                            safe_float_convert(k)
                            for k in levels.keys()
                            if safe_float_convert(k) is not None
                        ]
                    )
                    idx = valores_um.index(um_float)

                    if idx == 0:  # Primeiro valor
                        um_min = 0
                        um_max = (
                            (um_float + valores_um[idx + 1]) / 2
                            if idx + 1 < len(valores_um)
                            else um_float * 1.1
                        )
                    elif idx == len(valores_um) - 1:  # Último valor
                        um_min = (um_float + valores_um[idx - 1]) / 2
                        um_max = 9999  # Valor especial para "infinito"
                    else:  # Valor intermediário
                        um_min = (um_float + valores_um[idx - 1]) / 2
                        um_max = (um_float + valores_um[idx + 1]) / 2

                # Cria a faixa
                faixa = {
                    "um_min_kv": um_min,
                    "um_max_kv": um_max,
                    "norma_principal": "NBR/IEC",  # Valor padrão
                    "testes": {},
                    "niveis_pd_verificacao_u2": {
                        "fase_terra_kv_eficaz": um_float * 0.8,  # Aproximação para U2 fase-terra
                        "fase_fase_kv_eficaz": um_float * 1.2,  # Aproximação para U2 fase-fase
                    },
                }

                # Mapeia os testes
                for teste_key, teste_data in level_data.items():
                    if teste_key in ["li", "lic", "si", "acsd", "acld", "applied"]:
                        # Mapeia os nomes dos testes para o formato esperado
                        teste_map = {
                            "li": "LI",
                            "lic": "LIC",
                            "si": "SI",
                            "acsd": "TAF_TI_ACSD",
                            "acld": "ACLD",
                            "applied": "TAF",
                        }

                        teste_nome = teste_map.get(teste_key, teste_key.upper())

                        # Determina a classificação do teste
                        classificacao = "Rotina" if teste_data.get("sel_req", False) else "Tipo"

                        # Cria a estrutura do teste
                        teste_obj = {
                            "nome_completo": self._get_nome_completo_teste(teste_nome),
                            "classificacao_nbr_iec": classificacao,
                            "classificacao_ieee": "Rotina"
                            if teste_data.get("sel_req", False)
                            else "Design/Other",
                            "nbr_ref": "NBR 5356-3",
                            "ieee_ref": "IEEE C57.12.00",
                        }

                        # Adiciona os valores de tensão
                        if teste_nome in ["LI", "LIC", "SI"]:
                            teste_obj["ocr_kv_crista"] = {}
                            # Adiciona valores NBR
                            for valor in teste_data.get("nbr", []):
                                teste_obj["ocr_kv_crista"][str(um_float)] = teste_data.get(
                                    "nbr", []
                                )
                        else:
                            teste_obj["ocr_kv_eficaz"] = {}
                            # Adiciona valores NBR
                            for valor in teste_data.get("nbr", []):
                                teste_obj["ocr_kv_eficaz"][str(um_float)] = teste_data.get(
                                    "nbr", []
                                )

                        faixa["testes"][teste_nome] = teste_obj

                # Adiciona informações de distâncias
                faixa["distancias_min_ar_mm"] = self._extrair_distancias(distances, um_float)

                faixas.append(faixa)

            log.info(f"Conversão concluída: {len(faixas)} faixas de tensão criadas")
            return faixas

        except Exception as e:
            log.exception(f"Erro ao converter formato JSON: {e}")
            return []

    def _get_nome_completo_teste(self, teste_nome):
        """Retorna o nome completo do teste com base no código."""
        nomes = {
            "LI": "Tensão Suportável a Impulso Atmosférico (BIL)",
            "LIC": "Tensão Suportável a Impulso Atmosférico Cortado",
            "SI": "Tensão Suportável a Impulso de Manobra (BSL)",
            "TAF_TI_ACSD": "Tensão Suportável Aplicada / Induzida Curta Duração",
            "ACLD": "Tensão Induzida Longa Duração",
            "TAF": "Tensão Aplicada",
        }
        return nomes.get(teste_nome, teste_nome)

    def _get_classificacao_teste(self, teste_data):
        """Determina a classificação do teste com base nos dados."""
        if teste_data.get("sel_req", False):
            return "Rotina"
        return "Tipo"

    def _extrair_distancias(self, distances, um_float):
        """Extrai as informações de distâncias para a faixa de tensão."""
        result = {
            "fase_terra": {"ocr_mm": {}},
            "fase_fase": {"ocr_mm": {}},
            "outro_enrolamento": {"ocr_mm": {}},
        }

        # Extrai distâncias para BIL
        nbr_bil = distances.get("nbr_bil", {})
        for bil, dist_data in nbr_bil.items():
            if "ph_gnd" in dist_data:
                result["fase_terra"]["ocr_mm"][bil] = dist_data["ph_gnd"]
            if "ph_ph" in dist_data:
                result["fase_fase"]["ocr_mm"][bil] = dist_data["ph_ph"]
            if "ph_other" in dist_data and dist_data["ph_other"] is not None:
                result["outro_enrolamento"]["ocr_mm"][bil] = dist_data["ph_other"]

        # Extrai distâncias para BSL (para tensões altas)
        if um_float >= 170:
            nbr_bsl = distances.get("nbr_bsl", {})
            for bsl, dist_data in nbr_bsl.items():
                if "ph_gnd" in dist_data:
                    result["fase_terra"]["ocr_mm"][bsl] = dist_data["ph_gnd"]
                if "ph_ph" in dist_data:
                    result["fase_fase"]["ocr_mm"][bsl] = dist_data["ph_ph"]
                if "ph_other" in dist_data and dist_data["ph_other"] is not None:
                    result["outro_enrolamento"]["ocr_mm"][bsl] = dist_data["ph_other"]

        return result

    def get_norma(self) -> str:
        """Retorna o nome da norma."""
        log.info(f"Retornando nome da norma: {self.nome_norma}")
        return self.nome_norma

    # --- Métodos de Acesso aos Dados (Novos - Usando JSON) ---

    def _encontrar_nivel_isolamento(self, um_valor: float) -> List[Dict]:
        """Encontra todas as entradas de nível de isolamento correspondentes a um Um."""
        if not self.dados_json or "insulation_levels" not in self.dados_json:
            return []
        try:
            return [
                nivel
                for nivel in self.dados_json["insulation_levels"]
                if nivel.get("um_kv") is not None
                and math.isclose(safe_float_convert(nivel["um_kv"]), um_valor)
            ]
        except Exception as e:
            log.error(f"Erro ao encontrar nível de isolamento para Um={um_valor}: {e}")
            return []

    def get_nbi_sil_values(self, classe_tensao: Union[str, float]) -> dict:
        """Retorna valores de NBI e SIL para uma classe de tensão, buscando no JSON."""
        resultado = {"nbi": [], "sil": []}
        um_valor = safe_float_convert(classe_tensao)
        if um_valor is None:
            return resultado

        niveis_encontrados = self._encontrar_nivel_isolamento(um_valor)
        if not niveis_encontrados:
            return resultado

        for nivel in niveis_encontrados:
            bil = nivel.get("bil_kvp")
            sil = nivel.get("sil_kvp") or nivel.get("bsl_kvp")  # Tenta ambos os nomes
            if bil is not None and bil not in resultado["nbi"]:
                resultado["nbi"].append(bil)
            # Adiciona SIL apenas se for aplicável (não None e não 'NA')
            if sil is not None and str(sil).upper() != "NA":
                if sil not in resultado["sil"]:
                    resultado["sil"].append(sil)

        # Adiciona 'NA' explicitamente para SIL se nenhum valor numérico foi encontrado
        if not resultado["sil"] and um_valor < 300:  # Limiar pode variar conforme norma exata
            resultado["sil"] = ["NA"]

        resultado["nbi"] = sorted([v for v in resultado["nbi"] if v is not None])
        # Tratar 'NA' antes de ordenar
        sil_numeric = sorted([v for v in resultado["sil"] if isinstance(v, (int, float))])
        resultado["sil"] = (["NA"] if "NA" in resultado["sil"] else []) + sil_numeric

        return resultado

    def get_tensao_aplicada_values(
        self, classe_tensao: Union[str, float]
    ) -> List[Union[int, float]]:
        """Retorna valores de Tensão Aplicada para uma classe de tensão."""
        valores = []
        um_valor = safe_float_convert(classe_tensao)
        if um_valor is None:
            return valores
        niveis_encontrados = self._encontrar_nivel_isolamento(um_valor)
        for nivel in niveis_encontrados:
            acsd = nivel.get("acsd_kv_rms")
            if acsd is not None and acsd not in valores:
                valores.append(acsd)
        return sorted(valores)

    def get_tensao_induzida_values(
        self, classe_tensao: Union[str, float]
    ) -> List[Union[int, float]]:
        """Retorna valores de Tensão Induzida (ACLD e ACSD) para uma classe de tensão."""
        valores = []
        um_valor = safe_float_convert(classe_tensao)
        if um_valor is None:
            return valores
        niveis_encontrados = self._encontrar_nivel_isolamento(um_valor)
        for nivel in niveis_encontrados:
            # Prioriza ACLD se existir
            acld = nivel.get("acld_kv_rms")
            if acld is not None and acld not in valores:
                valores.append(acld)
            # Adiciona ACSD se diferente do ACLD já adicionado
            acsd = nivel.get("acsd_kv_rms")
            if acsd is not None and acsd not in valores:
                # Verifica se já existe um valor ACLD igual
                if not any(math.isclose(acsd, v) for v in valores if isinstance(v, (int, float))):
                    valores.append(acsd)

        return sorted([v for v in valores if v is not None])  # Garante ordenação e remove None

    # Adicionar métodos get_impulso_atm_values, get_impulso_man_values, etc., usando a mesma lógica
    # de buscar no JSON via _encontrar_nivel_isolamento e extrair a chave correta ('bil_kvp', 'sil_kvp', etc.).


class TabelaTransformadorNBR(NormaBase):
    """Implementação específica para NBR (usa dados JSON carregados pela base)."""

    def __init__(self):
        super().__init__("NBR 5356-3", config.PATH_NBR_DATA, "tabela.json")
        # _carregar_dados() já foi chamado no __init__ da classe base

    def get_impulso_atm_values(self, classe_tensao: Union[str, float]) -> List[Union[int, float]]:
        """Retorna valores de Impulso Atmosférico (BIL) para uma classe de tensão."""
        valores = []
        um_valor = safe_float_convert(classe_tensao)
        if um_valor is None:
            return valores
        niveis_encontrados = self._encontrar_nivel_isolamento(um_valor)
        for nivel in niveis_encontrados:
            if nivel.get("standard") == "IEC/NBR":
                bil = nivel.get("bil_kvp")
                if bil is not None and bil not in valores:
                    valores.append(bil)
        return sorted(valores)

    def get_nbi_neutro_values(self, classe_tensao: Union[str, float]) -> List[Union[int, float]]:
        """
        Retorna valores de NBI para o neutro com base na classe de tensão.
        Normalmente, o NBI do neutro é 60% do NBI principal para a mesma classe.
        """
        valores = []
        um_valor = safe_float_convert(classe_tensao)
        if um_valor is None:
            return valores

        # Obter valores de NBI principal para esta classe
        valores_nbi_principal = self.get_impulso_atm_values(um_valor)

        # Calcular valores de NBI para o neutro (60% do NBI principal)
        for nbi in valores_nbi_principal:
            nbi_neutro = round(
                nbi * 0.6, 1
            )  # 60% do NBI principal, arredondado para 1 casa decimal
            if nbi_neutro not in valores:
                valores.append(nbi_neutro)

        return sorted(valores)


class TabelaTransformadorIEEE(NormaBase):
    """Implementação específica para IEEE (usa dados JSON carregados pela base)."""

    def __init__(self):
        super().__init__("IEEE C57.12.00", config.PATH_IEEE_DATA, "tabela.json")
        # _carregar_dados() já foi chamado no __init__ da classe base

    # Métodos get_* específicos da IEEE podem ser adicionados aqui.
    # Por enquanto, os métodos da classe base que leem do JSON são suficientes.

    def encontrar_tensao_proxima(self, voltage: float) -> Optional[float]:
        """Encontra a tensão nominal do sistema IEEE mais próxima da tensão fornecida (do JSON)."""
        if not self.dados_json or "insulation_levels" not in self.dados_json:
            return None
        voltage_float = safe_float_convert(voltage)
        if voltage_float is None:
            return None

        all_ieee_voltages = set()
        for nivel in self.dados_json["insulation_levels"]:
            if nivel.get("standard") == "IEEE" and nivel.get("um_kv") is not None:
                um_f = safe_float_convert(nivel["um_kv"])
                if um_f is not None:
                    all_ieee_voltages.add(um_f)
            # Adicionar 'nominal_system_voltage_kv' se existir na estrutura JSON
            nom_v = nivel.get("nominal_system_voltage_kv")
            if nom_v is not None:
                nom_f = safe_float_convert(nom_v)
                if nom_f is not None:
                    all_ieee_voltages.add(nom_f)

        if not all_ieee_voltages:
            return None
        sorted_voltages = sorted(list(all_ieee_voltages))
        idx = np.abs(np.array(sorted_voltages) - voltage_float).argmin()
        return sorted_voltages[idx]

    def get_bil_values(self, voltage: float) -> List[Union[int, float]]:
        """Obtém valores de BIL IEEE para a tensão nominal mais próxima (do JSON)."""
        tensao_proxima = self.encontrar_tensao_proxima(voltage)
        if tensao_proxima is None:
            return []
        bil_values = set()
        for nivel in self.dados_json.get("insulation_levels", []):
            um_f = safe_float_convert(nivel.get("um_kv"))
            if (
                nivel.get("standard") == "IEEE"
                and um_f is not None
                and math.isclose(um_f, tensao_proxima)
            ):
                bil = nivel.get("bil_kvp")
                if bil is not None:
                    bil_values.add(bil)
        return sorted(list(bil_values))

    def get_test_levels(self, voltage: float) -> Optional[Dict]:
        """Obtém níveis de teste IEEE para a tensão nominal mais próxima (do JSON)."""
        tensao_proxima = self.encontrar_tensao_proxima(voltage)
        if tensao_proxima is None:
            return None
        # Encontra o primeiro nível correspondente (pode haver múltiplos BILs)
        niveis = self._encontrar_nivel_isolamento(tensao_proxima)
        ieee_niveis = [n for n in niveis if n.get("standard") == "IEEE"]
        if not ieee_niveis:
            return None
        # Pode retornar o primeiro encontrado ou o com maior BIL? Retornando o primeiro.
        level_data = ieee_niveis[0]
        return {
            "bil": level_data.get("bil_kvp"),
            "chopped": level_data.get("lic_kvp"),  # Assume LIC é chopped
            "switching": level_data.get("sil_kvp") or level_data.get("bsl_kvp"),
            "applied": level_data.get("acsd_kv_rms"),  # Assume ACSD é applied
            "induced": level_data.get("acld_kv_rms"),  # Assume ACLD é induced
            "norma": "IEEE",
            "tensao_nominal": tensao_proxima,  # Ou usar nominal_system_voltage_kv se disponível
        }

    # Adicionar get_clearances e determinar_ensaios_requeridos para IEEE se necessário


class VerificadorTransformador:
    """
    Classe para verificar e comparar dados de transformadores
    com base nas normas NBR e IEEE carregadas.
    """

    def __init__(self):
        log.info("Inicializando VerificadorTransformador...")
        try:
            # Passa explicitamente os caminhos definidos em config.py
            self.nbr = TabelaTransformadorNBR()
            self.ieee = TabelaTransformadorIEEE()
            # Verifica se o JSON foi carregado em ambas
            if not self.nbr.dados_json or not self.ieee.dados_json:
                # Tenta recarregar se falhou inicialmente
                log.warning("JSON não carregado inicialmente, tentando recarregar.")
                self.nbr._carregar_dados()
                self.ieee._carregar_dados()
                if not self.nbr.dados_json or not self.ieee.dados_json:
                    raise RuntimeError("Falha ao carregar dados JSON para NBR ou IEEE.")
            log.info(
                "Instâncias das normas NBR e IEEE criadas e dados JSON carregados com sucesso."
            )
        except Exception as e:
            log.critical(f"Falha CRÍTICA ao inicializar as classes das normas: {e}", exc_info=True)
            self.nbr = None
            self.ieee = None

    def is_valid(self) -> bool:
        """Verifica se as instâncias das normas foram carregadas corretamente (JSON)."""
        return (
            self.nbr is not None
            and self.ieee is not None
            and self.nbr.dados_json is not None
            and self.ieee.dados_json is not None
        )

    def get_nearest_um_value(self, tensao: float) -> Optional[str]:
        """Obtém o valor de Um padronizado mais próximo (considerando ambas normas)."""
        if not self.is_valid():
            return None
        um_valor = safe_float_convert(tensao)
        if um_valor is None:
            return None

        all_um_values = set()
        for nivel in self.nbr.dados_json.get("insulation_levels", []):
            um_f = safe_float_convert(nivel.get("um_kv"))
            if um_f is not None:
                all_um_values.add(um_f)

        if not all_um_values:
            return str(tensao)  # Fallback

        sorted_ums = sorted(list(all_um_values))
        idx = np.abs(np.array(sorted_ums) - um_valor).argmin()
        closest_um_float = sorted_ums[idx]
        # Retorna como string, tratando inteiros
        return (
            str(int(closest_um_float))
            if math.isclose(closest_um_float, round(closest_um_float))
            else str(closest_um_float)
        )

    def _find_closest_um_key(self, voltage_kv: float) -> Optional[str]:
        """[DEPRECADO] Encontra a chave Um mais próxima (usava estrutura antiga)."""
        # Esta função provavelmente não é mais necessária com a busca por _encontrar_nivel_isolamento
        log.warning("_find_closest_um_key está deprecada.")
        return self.get_nearest_um_value(voltage_kv)  # Usa a nova lógica

    def get_all_insulation_options(self, voltage_class: Union[str, float]) -> List[Dict[str, Any]]:
        """Retorna todas as opções de isolamento (NBR e IEEE) para uma classe Um."""
        all_options = []
        if not self.is_valid():
            return all_options
        um_valor = safe_float_convert(voltage_class)
        if um_valor is None:
            return all_options

        niveis_encontrados = self._encontrar_nivel_isolamento(um_valor)
        if not niveis_encontrados:
            return all_options

        for nivel in niveis_encontrados:
            norma_prefix = nivel.get("standard", "Desconhecida")
            option = {
                "norma": norma_prefix,
                "um_kv": nivel.get("um_kv"),
                "id": nivel.get("id"),  # ID único é crucial
                "bil_kvp": nivel.get("bil_kvp"),
                "lic_kvp": nivel.get("lic_kvp"),
                "acsd_kv_rms": nivel.get("acsd_kv_rms"),
                "acld_kv_rms": nivel.get("acld_kv_rms"),
                "sil_kvp": nivel.get("sil_kvp") or nivel.get("bsl_kvp") or "NA",  # Trata 'NA'
                "pd_requerido": nivel.get("pd_required", False),
                "distancias_mm": nivel.get("distancias_min_ar_mm"),
                # Adicionar outros campos relevantes se existirem no JSON
            }
            # Limpar Nones ou valores irrelevantes se necessário
            option = {k: v for k, v in option.items() if v is not None}
            # Converter SIL para string 'NA' se apropriado
            if "sil_kvp" in option and option["sil_kvp"] is None:
                option["sil_kvp"] = "NA"
            elif "sil_kvp" not in option:
                option["sil_kvp"] = "NA"  # Garante que existe

            all_options.append(option)

        return all_options

    def get_clearances(
        self,
        voltage: Union[str, float],
        transformer_type: str = "distribution",
        ia: Union[str, float] = None,
        im: Union[str, float] = None,
    ) -> dict:
        """Obtém espaçamentos comparativos de ambas as normas (usando JSON)."""
        results = {"NBR": None, "IEEE": None}
        if not self.is_valid():
            return results
        um_valor = safe_float_convert(voltage)
        if um_valor is None:
            return results
        ia_valor = safe_float_convert(ia)
        im_valor = safe_float_convert(im)  # Pode ser None ou 'NA' convertido para None

        niveis_um = self._encontrar_nivel_isolamento(um_valor)

        # --- NBR ---
        # Tenta encontrar a combinação NBR/IEC que casa com IA e IM fornecidos (ou o primeiro se não casar)
        best_match_nbr = None
        for nivel in niveis_um:
            if nivel.get("standard") == "IEC/NBR":
                bil_nivel = nivel.get("bil_kvp")
                sil_nivel = nivel.get("sil_kvp") or nivel.get("bsl_kvp")
                # Match perfeito de BIL e SIL (se SIL aplicável)
                match_bil = (
                    ia_valor is not None
                    and bil_nivel is not None
                    and math.isclose(bil_nivel, ia_valor)
                )
                match_sil = (im_valor is None and sil_nivel is None) or (
                    im_valor is not None
                    and sil_nivel is not None
                    and math.isclose(sil_nivel, im_valor)
                )

                if match_bil and match_sil:
                    best_match_nbr = nivel
                    break
                elif best_match_nbr is None:  # Guarda o primeiro encontrado como fallback
                    best_match_nbr = nivel

        if best_match_nbr and "distancias_min_ar_mm" in best_match_nbr:
            results["NBR"] = best_match_nbr["distancias_min_ar_mm"]
            results["NBR"]["ref_norma"] = "NBR/IEC"  # Adiciona referência
            results["NBR"]["id_ref"] = best_match_nbr.get("id")  # Adiciona ID usado

        # --- IEEE ---
        # Lógica similar para IEEE
        best_match_ieee = None
        for nivel in niveis_um:
            if nivel.get("standard") == "IEEE":
                bil_nivel = nivel.get("bil_kvp")
                sil_nivel = nivel.get("sil_kvp") or nivel.get("bsl_kvp")
                match_bil = (
                    ia_valor is not None
                    and bil_nivel is not None
                    and math.isclose(bil_nivel, ia_valor)
                )
                match_sil = (im_valor is None and sil_nivel is None) or (
                    im_valor is not None
                    and sil_nivel is not None
                    and math.isclose(sil_nivel, im_valor)
                )
                if match_bil and match_sil:
                    best_match_ieee = nivel
                    break
                elif best_match_ieee is None:
                    best_match_ieee = nivel

        if best_match_ieee and "distancias_min_ar_mm" in best_match_ieee:
            results["IEEE"] = best_match_ieee["distancias_min_ar_mm"]
            results["IEEE"]["ref_norma"] = "IEEE"
            results["IEEE"]["id_ref"] = best_match_ieee.get("id")

        return results

    def get_test_levels_comparison(
        self, voltage: Union[str, float], conexao=None, neutro_um=None
    ) -> dict:
        """Obtém níveis de teste comparativos (Tensão Aplicada/ACSD) usando JSON."""
        results = {
            "NBR": {"valores": [], "norma": "NBR 5356-3"},
            "IEEE": {"valores": [], "norma": "IEEE C57.12.00"},
        }
        if not self.is_valid():
            return results

        # Determina qual Um usar (principal ou neutro)
        um_busca = (
            safe_float_convert(neutro_um)
            if conexao == "YN" and neutro_um
            else safe_float_convert(voltage)
        )
        if um_busca is None:
            return results

        niveis_um = self._encontrar_nivel_isolamento(um_busca)

        for nivel in niveis_um:
            acsd = nivel.get("acsd_kv_rms")
            if acsd is not None:
                if nivel.get("standard") == "IEC/NBR":
                    if acsd not in results["NBR"]["valores"]:
                        results["NBR"]["valores"].append(acsd)
                elif nivel.get("standard") == "IEEE":
                    if acsd not in results["IEEE"]["valores"]:
                        results["IEEE"]["valores"].append(acsd)

        results["NBR"]["valores"] = sorted(results["NBR"]["valores"])
        results["IEEE"]["valores"] = sorted(results["IEEE"]["valores"])

        return results

    def get_required_tests_comparison(
        self, voltage: Union[str, float], tipo_isolamento: str = "uniforme"
    ) -> dict:
        """Obtém ensaios requeridos comparativos (do JSON)."""
        results = {"NBR": {}, "IEEE": {}}
        if not self.is_valid():
            return results
        um_valor = safe_float_convert(voltage)
        if um_valor is None:
            return results

        niveis_um = self._encontrar_nivel_isolamento(um_valor)
        if not niveis_um:
            return results

        # Assume o primeiro nível encontrado para simplificar (pode precisar refinar)
        nbr_nivel = next((n for n in niveis_um if n.get("standard") == "IEC/NBR"), None)
        ieee_nivel = next((n for n in niveis_um if n.get("standard") == "IEEE"), None)

        # Mapeamento simplificado - A estrutura JSON deveria ter isso idealmente
        def get_requirements(nivel_data):
            req = {}
            if nivel_data:
                req["impulso_atmosferico"] = "Requerido"  # Assume BIL sempre requerido
                req["impulso_atmosferico_onda_cortada"] = (
                    "Requerido" if nivel_data.get("lic_kvp") else "Não Aplicável"
                )
                req["impulso_manobra"] = (
                    "Requerido"
                    if nivel_data.get("sil_kvp") or nivel_data.get("bsl_kvp")
                    else "Não Aplicável"
                )
                req["tensao_aplicada"] = (
                    "Requerido" if nivel_data.get("acsd_kv_rms") else "Não Aplicável"
                )  # Mapeia para ACSD
                req["tensao_induzida_curta"] = (
                    "Requerido" if nivel_data.get("acsd_kv_rms") else "Não Aplicável"
                )
                req["tensao_induzida_longa"] = (
                    "Requerido" if nivel_data.get("acld_kv_rms") else "Não Aplicável"
                )
                # DP requerido pode ser lido diretamente
                req["descargas_parciais"] = (
                    "Requerido" if nivel_data.get("pd_required") else "Não Aplicável"
                )
            return req

        results["NBR"] = get_requirements(nbr_nivel)
        results["IEEE"] = get_requirements(ieee_nivel)

        # Adiciona sequências (pode precisar buscar por ID se não estiver no nível)
        # results["sequencias_ensaio_nbr"] = self.get_test_sequences_from_profiles(???) # Precisa de um ID ou perfil

        return results

    def get_chopped_impulse_comparison(
        self, voltage: Union[str, float], ia: Union[str, float]
    ) -> dict:
        """Calcula e compara valores de impulso cortado (LIC) usando JSON."""
        results = {"NBR": None, "IEEE": None}
        if not self.is_valid():
            return results
        um_valor = safe_float_convert(voltage)
        ia_valor = safe_float_convert(ia)
        if um_valor is None or ia_valor is None:
            return results

        niveis_um = self._encontrar_nivel_isolamento(um_valor)

        # --- NBR ---
        nbr_nivel = next(
            (
                n
                for n in niveis_um
                if n.get("standard") == "IEC/NBR"
                and n.get("bil_kvp") is not None
                and math.isclose(n["bil_kvp"], ia_valor)
            ),
            None,
        )
        if nbr_nivel:
            results["NBR"] = nbr_nivel.get("lic_kvp")  # Pega LIC diretamente
        else:  # Fallback: Calcula 1.1 * BIL
            results["NBR"] = round(ia_valor * 1.1, 1)

        # --- IEEE ---
        ieee_nivel = next(
            (
                n
                for n in niveis_um
                if n.get("standard") == "IEEE"
                and n.get("bil_kvp") is not None
                and math.isclose(n["bil_kvp"], ia_valor)
            ),
            None,
        )
        if ieee_nivel:
            results["IEEE"] = ieee_nivel.get("lic_kvp")
        else:  # Fallback: Calcula 1.15 * BIL (aproximação IEEE)
            results["IEEE"] = round(ia_valor * 1.15, 1)

        return results

    def get_test_sequences_from_profiles(self, id_combinacao: str) -> Optional[Dict[str, Any]]:
        """Obtém as sequências de teste de DP aplicáveis para um ID de combinação."""
        if not self.is_valid():
            return None

        from utils.tabela_utils import obter_perfis_dp_aplicaveis_por_id

        perfis_aplicaveis = obter_perfis_dp_aplicaveis_por_id(id_combinacao)
        if not perfis_aplicaveis:
            return None

        sequencias_completas = {}
        for nome_perfil in perfis_aplicaveis:
            perfil_data = self.obter_perfil_dp(nome_perfil)
            if perfil_data:
                sequencias_completas[nome_perfil] = perfil_data  # Inclui detalhes do perfil

        return sequencias_completas if sequencias_completas else None

    def obter_perfil_dp(self, nome_perfil: str) -> Optional[Dict[str, Any]]:
        """Obtém os detalhes de um perfil de DP do JSON."""
        if not self.is_valid():
            return None
        return self.nbr.dados_json.get("perfis_dp", {}).get(nome_perfil)


# --- END OF FILE app_core/standards.py ---
