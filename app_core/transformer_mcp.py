# app_core/transformer_mcp.py
import logging
import json
import copy
import math
from typing import Dict, Any, List, Optional

from utils.store_diagnostics import convert_numpy_types, is_json_serializable, fix_store_data
from utils.db_manager import save_test_session, get_test_session_details as db_get_session_details, session_name_exists, delete_test_session as db_delete_session # Alias para evitar conflito
from utils.mcp_disk_persistence import save_mcp_state_to_disk, load_mcp_state_from_disk
# REMOVIDA A IMPORTAÇÃO CIRCULAR: from .transformer_mcp import STORE_IDS, DEFAULT_TRANSFORMER_INPUTS

log = logging.getLogger(__name__)

# Lista de todos os store IDs usados na aplicação
STORE_IDS = [
    'transformer-inputs-store',
    'losses-store',
    'impulse-store',
    'dieletric-analysis-store',
    'applied-voltage-store',
    'induced-voltage-store',
    'short-circuit-store',
    'temperature-rise-store',
    'comprehensive-analysis-store',
    'front-resistor-data',
    'tail-resistor-data',
    'calculated-inductance',
    'simulation-status'
]

# Valores padrão para transformer inputs
DEFAULT_TRANSFORMER_INPUTS = {
    'tipo_transformador': 'Trifásico',
    'frequencia': 60.0,
    'conexao_at': 'estrela',
    'conexao_bt': 'triangulo',
    'conexao_terciario': '',
    'liquido_isolante': 'Mineral',
    'tipo_isolamento': 'uniforme',
    'potencia_mva': None,
    'grupo_ligacao': None,
    'elevacao_oleo_topo': None,
    'elevacao_enrol': None,
    'tensao_at': None,
    'classe_tensao_at': None,
    'elevacao_enrol_at': None,
    'impedancia': None,
    'nbi_at': None,
    'sil_at': None,
    'tensao_at_tap_maior': None,
    'impedancia_tap_maior': None,
    'tensao_at_tap_menor': None,
    'impedancia_tap_menor': None,
    'teste_tensao_aplicada_at': None,
    'teste_tensao_induzida_at': None,
    'teste_tensao_induzida': None,  # Mantido para compatibilidade
    'tensao_bt': None,
    'classe_tensao_bt': None,
    'elevacao_enrol_bt': None,
    'nbi_bt': None,
    'sil_bt': None,
    'teste_tensao_aplicada_bt': None,
    'tensao_terciario': None,
    'classe_tensao_terciario': None,
    'elevacao_enrol_terciario': None,
    'nbi_terciario': None,
    'sil_terciario': None,
    'teste_tensao_aplicada_terciario': None,
    'tensao_bucha_neutro_at': None,
    'tensao_bucha_neutro_bt': None,
    'tensao_bucha_neutro_terciario': None,
    'nbi_neutro_at': None,
    'nbi_neutro_bt': None,
    'nbi_neutro_terciario': None,
    'peso_total': None,
    'peso_parte_ativa': None,
    'peso_oleo': None,
    'peso_tanque_acessorios': None,
    'corrente_nominal_at': None,
    'corrente_nominal_at_tap_maior': None,
    'corrente_nominal_at_tap_menor': None,
    'corrente_nominal_bt': None,
    'corrente_nominal_terciario': None
}

class TransformerMCP:
    def __init__(self, load_from_disk=False):
        log.info(f"Initializing Transformer MCP (load_from_disk={load_from_disk})")
        self._data = {}
        self._listeners = {}
        self.last_save_error = None # Para armazenar o último erro de salvamento
        self._initialize_stores()

        # Carregar dados do disco se solicitado
        if load_from_disk:
            self._load_from_disk()

    def _initialize_stores(self):
        """Inicializa todos os stores com valores padrão."""
        log.info("===============================================================")
        log.info("[MCP INITIALIZE] INICIALIZANDO STORES:")

        # Inicializar todos os stores com valores vazios
        for store_id in STORE_IDS:
            if store_id == 'transformer-inputs-store':
                # Para transformer-inputs-store, usar os valores padrão
                self._data[store_id] = DEFAULT_TRANSFORMER_INPUTS.copy()
                log.info("===============================================================")
                log.info("[MCP INITIALIZE] DADOS INICIAIS DO TRANSFORMER-INPUTS-STORE:")
                log.info(f"DADOS COMPLETOS INICIAIS: {json.dumps(self._data[store_id], indent=2)}")
                log.info("===============================================================")
            else:
                # Para outros stores, inicializar com dicionário vazio
                self._data[store_id] = {}

        log.info("===============================================================")
        log.info(f"MCP Initialized {len(STORE_IDS)} data stores")
        log.info("===============================================================")

    def get_data(self, store_id: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Obtém os dados de um store específico.

        Args:
            store_id: ID do store
            force_reload: Se True, tenta recarregar os dados do disco antes de retornar

        Returns:
            Cópia dos dados do store ou dicionário vazio se o store não existir
        """
        # Se force_reload for True, tenta recarregar os dados do disco
        if force_reload:
            log.info(f"[MCP GET] Forçando recarga dos dados do disco para store '{store_id}'")
            self._load_from_disk()

        if store_id not in self._data:
            log.warning(f"[MCP GET] Store ID '{store_id}' não encontrado. Retornando dicionário vazio.")
            return {}

        # Retorna uma cópia profunda para evitar modificações acidentais
        return copy.deepcopy(self._data.get(store_id, {}))

    def set_data(self, store_id: str, data: Dict[str, Any]) -> None:
        """
        Define os dados de um store específico.

        Args:
            store_id: ID do store
            data: Dados a serem definidos
        """
        if store_id not in STORE_IDS:
            log.warning(f"[MCP SET] Store ID '{store_id}' não é um store conhecido. Ignorando.")
            return

        # Converter tipos numpy para tipos Python nativos
        serializable_data = convert_numpy_types(data, debug_path=f"mcp_set.{store_id}")

        # Atualizar os dados
        self._data[store_id] = serializable_data

        # Notificar listeners
        self._notify_listeners(store_id, serializable_data)

        log.debug(f"[MCP SET] Dados definidos para store '{store_id}'.")

    def get_all_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém todos os dados de todos os stores.

        Returns:
            Cópia de todos os dados
        """
        # Retorna uma cópia profunda para evitar modificações acidentais
        return copy.deepcopy(self._data)

    def clear_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Limpa todos os dados de todos os stores, redefinindo-os para os valores padrão.

        Returns:
            Cópia dos dados após a limpeza
        """
        # Reinicializar todos os stores
        self._initialize_stores()

        # Notificar listeners
        for store_id in STORE_IDS:
            self._notify_listeners(store_id, self._data[store_id])

        log.info("[MCP CLEAR] Todos os stores foram limpos e redefinidos para os valores padrão.")

        # Retornar uma cópia dos dados após a limpeza
        return self.get_all_data()

    def _notify_listeners(self, store_id: str, data: Dict[str, Any]) -> None:
        """
        Notifica os listeners de um store específico.

        Args:
            store_id: ID do store
            data: Dados atualizados
        """
        if store_id in self._listeners:
            for listener in self._listeners[store_id]:
                try:
                    listener(data)
                except Exception as e:
                    log.error(f"[MCP NOTIFY] Erro ao notificar listener para store '{store_id}': {e}")

    def add_listener(self, store_id: str, listener: callable) -> None:
        """
        Adiciona um listener para um store específico.

        Args:
            store_id: ID do store
            listener: Função a ser chamada quando o store for atualizado
        """
        if store_id not in self._listeners:
            self._listeners[store_id] = []

        self._listeners[store_id].append(listener)
        log.debug(f"[MCP ADD_LISTENER] Listener adicionado para store '{store_id}'.")

    def remove_listener(self, store_id: str, listener: callable) -> None:
        """
        Remove um listener de um store específico.

        Args:
            store_id: ID do store
            listener: Função a ser removida
        """
        if store_id in self._listeners and listener in self._listeners[store_id]:
            self._listeners[store_id].remove(listener)
            log.debug(f"[MCP REMOVE_LISTENER] Listener removido de store '{store_id}'.")

    def save_to_disk(self, force: bool = False) -> bool:
        """
        Salva o estado atual do MCP em disco.

        Args:
            force: Se True, força o salvamento mesmo que não haja alterações

        Returns:
            bool: True se o salvamento foi bem-sucedido, False caso contrário
        """
        log.info("[MCP SAVE_TO_DISK] Salvando estado do MCP em disco...")

        # Obter dados de todos os stores
        all_data = self.get_all_data()

        # Verificar se há dados para salvar
        if not all_data and not force:
            log.warning("[MCP SAVE_TO_DISK] Nenhum dado para salvar. Abortando.")
            return False

        # Verificar se há dados essenciais no transformer-inputs-store
        transformer_data = all_data.get('transformer-inputs-store', {})
        if not transformer_data and not force:
            log.warning("[MCP SAVE_TO_DISK] Dados do transformer-inputs-store vazios. Abortando.")
            return False

        # Salvar dados em disco
        success = save_mcp_state_to_disk(all_data, create_backup=True)

        if success:
            log.info("[MCP SAVE_TO_DISK] Estado do MCP salvo em disco com sucesso.")
        else:
            log.error("[MCP SAVE_TO_DISK] Falha ao salvar estado do MCP em disco.")

        return success

    def _load_from_disk(self) -> bool:
        """
        Carrega o estado do MCP a partir do disco.

        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário
        """
        log.info("Carregando dados do MCP a partir do disco")

        # Carregar dados do disco
        stores_data, success = load_mcp_state_from_disk()

        if not success:
            log.warning("Falha ao carregar dados do MCP do disco. Mantendo valores padrão.")
            return False

        # Atualizar dados do MCP
        for store_id, data in stores_data.items():
            if store_id in STORE_IDS:
                # Converter tipos numpy para tipos Python nativos
                serializable_data = convert_numpy_types(data, debug_path=f"mcp_init_load.{store_id}")

                # Verificar se o store atual já tem dados
                current_store_data = self._data.get(store_id, {})

                # Se o store atual já tem dados e os dados carregados também são um dicionário,
                # mesclar os dados em vez de substituir
                if current_store_data and isinstance(current_store_data, dict) and isinstance(serializable_data, dict):
                    # Verificar se há dados específicos no store carregado
                    has_specific_inputs = any(key.startswith('inputs_') for key in serializable_data.keys())

                    if has_specific_inputs:
                        log.debug(f"[MCP LOAD FROM DISK] Mesclando dados específicos para o store '{store_id}'")
                        # Mesclar os dados, dando prioridade aos dados carregados
                        merged_data = {**current_store_data, **serializable_data}
                        serializable_data = merged_data
                        log.debug(f"[MCP LOAD FROM DISK] Dados mesclados para o store '{store_id}': {list(serializable_data.keys())}")

                # Atualizar dados
                self._data[store_id] = serializable_data
                log.info(f"Dados carregados do disco para store: {store_id}")
            else:
                log.warning(f"Store ID '{store_id}' do disco não é um store conhecido. Ignorando.")

        return True

    def save_session(self, session_name: str, notes: str = "", stores_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Salva uma sessão de teste no banco de dados.
        Se stores_data for fornecido (eg., vindo de callback States), usa esses dados.
        Se stores_data for None, usa o estado interno do MCP (self._data).

        Args:
            session_name: Nome da sessão
            notes: Notas da sessão
            stores_data: Opcional. Dicionário {store_id: data} com os dados a serem salvos.

        Returns:
            int: O ID da sessão salva (> 0) ou um código de erro (< 0):
                 -1: Erro genérico ou falha no DB
                 -2: Nome da sessão já existe
                 -3: Erro de serialização crítico (após fix_store_data)
        """
        self.last_save_error = None
        log.info(f"[MCP SAVE SESSION] Tentando salvar sessão: '{session_name}'")

        # Verifica nome duplicado PRIMEIRO
        if session_name_exists(session_name):
            log.warning(f"[MCP SAVE SESSION] Nome da sessão '{session_name}' já existe.")
            self.last_save_error = f"Nome de sessão '{session_name}' já existe."
            return -2

        # 1. Obter dados de todos os stores. Use stores_data se fornecido, senão use o estado interno do MCP.
        if stores_data is not None:
            log.debug("[MCP SAVE SESSION] Usando dados fornecidos para salvamento.")
            data_to_process = copy.deepcopy(stores_data) # Sempre trabalhar com uma cópia
            # Verificar se os dados fornecidos incluem pelo menos os stores básicos
            if not any(sid in data_to_process for sid in STORE_IDS):
                 log.warning("[MCP SAVE SESSION] Os dados fornecidos parecem incompletos (não contêm IDs de store conhecidos). Fallback para estado interno do MCP.")
                 data_to_process = self.get_all_data() # Fallback para o estado interno
            else:
                 log.debug(f"[MCP SAVE SESSION] Dados fornecidos contêm {len(data_to_process)} stores: {list(data_to_process.keys())}")

        else:
            log.debug("[MCP SAVE SESSION] Usando dados do estado interno do MCP para salvamento.")
            data_to_process = self.get_all_data() # Já retorna uma deepcopy

        # Verificar se há dados para salvar (após determinar a fonte)
        if not data_to_process:
             log.warning("[MCP SAVE SESSION] Nenhuma dado disponível para salvar. Abortando.")
             self.last_save_error = "Nenhum dado disponível para salvar."
             return -1 # Ou outro código para "sem dados"


        # 2. Verificação de serializabilidade e correção em TODOS os dados
        log.debug("[MCP SAVE SESSION] Realizando verificação e preparação dos dados para DB...")
        data_prepared_for_db = fix_store_data(data_to_process) # fix_store_data já chama convert_numpy_types

        # 3. Verificar se algum store teve falha crítica na conversão
        for store_id_check, store_content_check in data_prepared_for_db.items():
            # fix_store_data pode retornar um dicionário especial para indicar falha
            if isinstance(store_content_check, dict) and store_content_check.get("_conversion_failed"):
                err_msg = store_content_check.get("_error", "Erro desconhecido na conversão.")
                log.error(f"[MCP SAVE SESSION] Falha crítica ao preparar store '{store_id_check}' para salvamento: {err_msg}")
                self.last_save_error = f"Erro ao preparar dados do store '{store_id_check}': {err_msg}"
                return -3 # Erro de serialização crítico

        # 4. Chamar o db_manager para salvar
        log.debug("[MCP SAVE SESSION] Chamando db_manager.save_test_session com dados preparados...")
        # db_manager.save_test_session espera um dicionário {store_id: json_string_data}
        # No entanto, fix_store_data já retorna {store_id: processed_data}, onde processed_data
        # é o objeto serializável ou o dict de erro. save_test_session serializa isso para JSON.
        # So we pass the output of fix_store_data directly.
        session_id = save_test_session(data_prepared_for_db, session_name, notes)

        if session_id <= 0:
            # save_test_session já loga o erro do DB
            self.last_save_error = self.last_save_error or "Erro no banco de dados ao salvar."
            return -1 # Erro genérico do DB (inclui nome duplicado se DB impõe UNIQUE)


        log.info(f"[MCP SAVE SESSION] Sessão '{session_name}' salva com sucesso (ID: {session_id})!")
        return session_id

    def load_session(self, session_id: int) -> bool:
        """
        Carrega uma sessão do banco de dados para o MCP.
        Atualiza self._data com os dados carregados e notifica listeners.
        Retorna True se bem-sucedido, False caso contrário.
        """
        self.last_save_error = None # Limpa qualquer erro anterior
        log.info(f"[MCP LOAD SESSION] Tentando carregar sessão ID: {session_id}")

        session_details_raw = db_get_session_details(session_id) # Usa o alias
        if not session_details_raw or "mcp_stores_raw_json" not in session_details_raw:
            log.error(f"[MCP LOAD SESSION] Sessão ID {session_id} não encontrada ou dados de store ausentes.")
            self.last_save_error = f"Sessão ID {session_id} não encontrada ou dados corrompidos."
            return False

        mcp_stores_raw_json = session_details_raw["mcp_stores_raw_json"]

        # Limpar o estado atual do MCP antes de carregar novos dados
        self._initialize_stores() # Isso redefine para os defaults
        log.info("[MCP LOAD SESSION] Estado atual do MCP limpo (resetado para defaults).")

        loaded_successfully = True
        for store_id, json_data_str in mcp_stores_raw_json.items():
            if store_id not in STORE_IDS:
                log.warning(f"[MCP LOAD SESSION] Store ID '{store_id}' do DB não é um store conhecido. Ignorando.")
                continue

            try:
                if json_data_str:
                    # Desserializa o JSON string
                    data_content = json.loads(json_data_str)

                    # Verificar se o store atual já tem dados
                    current_store_data = self.get_data(store_id)

                    # Se o store atual já tem dados e os dados carregados também são um dicionário,
                    # mesclar os dados em vez de substituir
                    if current_store_data and isinstance(current_store_data, dict) and isinstance(data_content, dict):
                        # Verificar se há dados específicos no store carregado
                        has_specific_inputs = any(key.startswith('inputs_') for key in data_content.keys())

                        if has_specific_inputs:
                            log.debug(f"[MCP LOAD SESSION] Mesclando dados específicos para o store '{store_id}'")
                            # Mesclar os dados, dando prioridade aos dados carregados
                            merged_data = {**current_store_data, **data_content}
                            data_content = merged_data
                            log.debug(f"[MCP LOAD SESSION] Dados mesclados para o store '{store_id}': {list(data_content.keys())}")

                    # O método set_data do MCP fará a conversão numpy e outras validações.
                    # No entanto, os dados do DB já deveriam estar "limpos".
                    # Uma chamada a convert_numpy_types aqui pode ser uma segurança extra,
                    # especialmente se os dados no DB puderem ter sido salvos por uma versão
                    # mais antiga do código.
                    data_final_for_store = convert_numpy_types(data_content, debug_path=f"mcp_load.{store_id}")

                    self.set_data(store_id, data_final_for_store) # Usa o set_data do MCP
                    log.debug(f"[MCP LOAD SESSION] Dados do store '{store_id}' carregados e definidos no MCP.")
                else:
                    # Store estava vazio no DB, set_data com {} para limpar/resetar
                    self.set_data(store_id, {})
                    log.debug(f"[MCP LOAD SESSION] Store '{store_id}' estava vazio no DB, resetado no MCP.")

            except json.JSONDecodeError as e_json:
                log.error(f"[MCP LOAD SESSION] Erro ao desserializar JSON para store '{store_id}': {e_json}", exc_info=True)
                self.set_data(store_id, {"_load_error": f"JSON Inválido: {e_json}"}) # Guarda info do erro
                loaded_successfully = False
            except Exception as e_set:
                log.error(f"[MCP LOAD SESSION] Erro ao definir dados para store '{store_id}' no MCP: {e_set}", exc_info=True)
                self.set_data(store_id, {"_load_error": f"Erro MCP: {e_set}"})
                loaded_successfully = False

        if loaded_successfully:
            # Notificar listeners para todos os stores atualizados
            # O set_data já notifica, mas podemos fazer um log geral aqui
            log.info(f"[MCP LOAD SESSION] Sessão ID {session_id} carregada com sucesso para o MCP.")
            # Opcional: Salvar no disco local (mcp_state.json) após carregar do DB?
            # self.save_to_disk()
            return True
        else:
            self.last_save_error = "Erro ao carregar um ou mais stores da sessão."
            log.error(f"[MCP LOAD SESSION] Falha ao carregar completamente a sessão ID {session_id}.")
            return False

    def delete_session(self, session_id: int) -> bool:
        """Deleta uma sessão do banco de dados."""
        log.info(f"[MCP DELETE SESSION] Tentando deletar sessão ID: {session_id}")
        return db_delete_session(session_id)

    def calculate_nominal_currents(self, transformer_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula as correntes nominais do transformador com base nos dados fornecidos.

        Args:
            transformer_data: Dados do transformador

        Returns:
            Dicionário com as correntes nominais calculadas
        """
        log.info("[MCP CALCULATE] Calculando correntes nominais...")

        # Inicializar dicionário de resultados
        result = {
            "corrente_nominal_at": None,
            "corrente_nominal_bt": None,
            "corrente_nominal_terciario": None,
            "corrente_nominal_at_tap_maior": None,
            "corrente_nominal_at_tap_menor": None
        }

        try:
            # Verificar se os dados necessários estão presentes
            potencia_mva = transformer_data.get("potencia_mva")
            tensao_at = transformer_data.get("tensao_at")
            tensao_bt = transformer_data.get("tensao_bt")
            tensao_terciario = transformer_data.get("tensao_terciario")
            tensao_at_tap_maior = transformer_data.get("tensao_at_tap_maior")
            tensao_at_tap_menor = transformer_data.get("tensao_at_tap_menor")
            tipo_transformador = transformer_data.get("tipo_transformador", "Trifásico")

            # Verificar se os dados essenciais estão presentes
            if not potencia_mva or not tensao_at:
                log.warning("[MCP CALCULATE] Dados insuficientes para calcular correntes nominais.")
                return result

            # Converter para números se necessário
            potencia_mva = float(potencia_mva)
            tensao_at = float(tensao_at)

            # Fator de multiplicação baseado no tipo de transformador
            fator = 1.0
            if tipo_transformador == "Monofásico":
                fator = 1.0
            else:  # Trifásico
                fator = math.sqrt(3)

            # Calcular corrente nominal AT
            corrente_nominal_at = (potencia_mva * 1000) / (tensao_at * fator)
            result["corrente_nominal_at"] = corrente_nominal_at

            # Calcular corrente nominal BT se tensão BT estiver presente
            if tensao_bt:
                tensao_bt = float(tensao_bt)
                corrente_nominal_bt = (potencia_mva * 1000) / (tensao_bt * fator)
                result["corrente_nominal_bt"] = corrente_nominal_bt

            # Calcular corrente nominal terciário se tensão terciário estiver presente
            if tensao_terciario:
                tensao_terciario = float(tensao_terciario)
                corrente_nominal_terciario = (potencia_mva * 1000) / (tensao_terciario * fator)
                result["corrente_nominal_terciario"] = corrente_nominal_terciario

            # Calcular correntes nominais para taps se presentes
            if tensao_at_tap_maior:
                tensao_at_tap_maior = float(tensao_at_tap_maior)
                corrente_nominal_at_tap_maior = (potencia_mva * 1000) / (tensao_at_tap_maior * fator)
                result["corrente_nominal_at_tap_maior"] = corrente_nominal_at_tap_maior

            if tensao_at_tap_menor:
                tensao_at_tap_menor = float(tensao_at_tap_menor)
                corrente_nominal_at_tap_menor = (potencia_mva * 1000) / (tensao_at_tap_menor * fator)
                result["corrente_nominal_at_tap_menor"] = corrente_nominal_at_tap_menor

            log.info(f"[MCP CALCULATE] Correntes nominais calculadas: {result}")
            return result

        except Exception as e:
            log.error(f"[MCP CALCULATE] Erro ao calcular correntes nominais: {e}", exc_info=True)
            return result