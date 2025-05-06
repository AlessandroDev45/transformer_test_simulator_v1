# components/validators.py
"""
Funções para validar dados de entrada da interface do usuário.
"""
import logging
import math

log = logging.getLogger(__name__)

def is_valid_number(value, min_val=None, max_val=None, allow_none=False, field_name="Campo") -> tuple[bool, str]:
    """
    Verifica se um valor é um número válido (int ou float), não NaN/Inf,
    e opcionalmente dentro de um intervalo [min_val, max_val].

    Args:
        value: O valor a ser validado.
        min_val: Valor mínimo permitido (inclusive).
        max_val: Valor máximo permitido (inclusive).
        allow_none: Se True, permite que o valor seja None.
        field_name: Nome do campo para mensagens de erro.

    Returns:
        tuple[bool, str]: (True se válido, Mensagem de erro ou string vazia).
    """
    if value is None:
        if allow_none:
            return True, ""
        else:
            return False, f"{field_name}: Valor é obrigatório."

    try:
        num = float(value) # Tenta converter para float
        if math.isnan(num) or math.isinf(num):
            return False, f"{field_name}: Valor numérico inválido (NaN ou Infinito)."
    except (ValueError, TypeError):
        return False, f"{field_name}: '{value}' não é um número válido."

    if min_val is not None and num < min_val:
        return False, f"{field_name}: Valor ({num}) abaixo do mínimo permitido ({min_val})."
    if max_val is not None and num > max_val:
        return False, f"{field_name}: Valor ({num}) acima do máximo permitido ({max_val})."

    return True, ""

def is_positive_number(value, allow_zero=False, allow_none=False, field_name="Campo") -> tuple[bool, str]:
    """
    Verifica se um valor é um número positivo (ou opcionalmente não negativo).

    Args:
        value: O valor a ser validado.
        allow_zero: Se True, permite que o valor seja zero.
        allow_none: Se True, permite que o valor seja None.
        field_name: Nome do campo para mensagens de erro.

    Returns:
        tuple[bool, str]: (True se válido, Mensagem de erro ou string vazia).
    """
    is_num, msg = is_valid_number(value, allow_none=allow_none, field_name=field_name)
    if not is_num:
        # Se for None e allow_none=True, is_valid_number retorna True, msg=""
        # Se is_valid_number retornou False, a mensagem já está em 'msg'
        return is_num, msg

    if value is None and allow_none:
        return True, "" # Já validado por is_valid_number

    # Se chegou aqui, value é um número válido (não None, NaN, Inf)
    num = float(value)

    if allow_zero:
        if num < 0:
            return False, f"{field_name}: Valor ({num}) não pode ser negativo."
    else:
        if num <= 0:
            return False, f"{field_name}: Valor ({num}) deve ser estritamente positivo."

    return True, ""

def is_required(value, field_name="Campo") -> tuple[bool, str]:
    """
    Verifica se um valor obrigatório foi fornecido (não None e não string vazia/whitespace).

    Args:
        value: O valor a ser validado.
        field_name: Nome do campo para mensagens de erro.

    Returns:
        tuple[bool, str]: (True se válido, Mensagem de erro ou string vazia).
    """
    if value is None:
        return False, f"{field_name}: Campo obrigatório não preenchido."
    if isinstance(value, str) and not value.strip():
        return False, f"{field_name}: Campo obrigatório não pode ser vazio."
    # Adicionar outras verificações se necessário (ex: lista vazia?)

    return True, ""

def validate_dict_inputs(data: dict, validations: dict) -> list[str]:
    """
    Valida múltiplos campos dentro de um dicionário com base em regras especificadas.

    Args:
        data (dict): O dicionário contendo os dados a serem validados (ex: dados de um Store).
        validations (dict): Um dicionário onde as chaves são os nomes dos campos em 'data'
                           e os valores são dicionários especificando as regras de validação.
                           Exemplo:
                           {
                               'potencia_mva': {'required': True, 'positive': True, 'label': 'Potência'},
                               'tensao_at': {'required': True, 'min': 0.1, 'label': 'Tensão AT'},
                               'frequencia': {'required': False, 'default': 60, 'min': 10, 'max': 500, 'label': 'Frequência'}
                               'tipo': {'required': True, 'allowed': ['Trifásico', 'Monofásico'], 'label': 'Tipo'}
                           }

    Returns:
        list[str]: Uma lista de mensagens de erro. Lista vazia se tudo for válido.
    """
    errors = []
    if not isinstance(data, dict):
        return ["Erro interno: Dados de entrada para validação não são um dicionário."]
    if not isinstance(validations, dict):
         return ["Erro interno: Definição de validação inválida."]

    for field, rules in validations.items():
        value = data.get(field) # Pega o valor do dicionário de dados
        label = rules.get('label', field) # Usa label fornecido ou o nome do campo

        # 1. Validação de Obrigatoriedade
        if rules.get('required', False):
            is_valid, msg = is_required(value, field_name=label)
            if not is_valid:
                errors.append(msg)
                continue # Pula outras validações se for obrigatório e ausente

        # Pula validações adicionais se o valor for None e não for obrigatório
        if value is None and not rules.get('required', False):
             continue

        # 2. Validação de Tipo (Exemplo: número)
        is_numeric_type = 'min' in rules or 'max' in rules or rules.get('positive', False) or rules.get('allow_zero', False)
        if is_numeric_type:
            # Pode ser positivo ou apenas número com range
            if rules.get('positive', False):
                is_valid, msg = is_positive_number(value,
                                                   allow_zero=rules.get('allow_zero', False),
                                                   allow_none=not rules.get('required', False), # Permite None se não obrigatório
                                                   field_name=label)
            else: # Apenas verifica se é número e dentro do range
                is_valid, msg = is_valid_number(value,
                                                min_val=rules.get('min'),
                                                max_val=rules.get('max'),
                                                allow_none=not rules.get('required', False), # Permite None se não obrigatório
                                                field_name=label)
            if not is_valid:
                errors.append(msg)
                continue # Pula outras validações numéricas se esta falhar

        # 3. Validação de Valores Permitidos (Dropdowns, RadioItems)
        allowed_values = rules.get('allowed')
        if allowed_values and isinstance(allowed_values, list):
             # Converte valor para string para comparação segura se não for None
             value_str = str(value) if value is not None else None
             if value_str not in map(str, allowed_values): # Compara como strings
                 allowed_str = ", ".join(map(str, allowed_values))
                 errors.append(f"{label}: Valor '{value}' inválido. Permitidos: {allowed_str}.")
                 continue

        # Adicionar mais tipos de validação aqui (regex, etc.)

    return errors

# Exemplo de uso da função validate_dict_inputs em um callback:
#
# errors = validate_dict_inputs(
#     transformer_data, # Dados do dcc.Store
#     {
#         'potencia_mva': {'required': True, 'positive': True, 'label': 'Potência (MVA)'},
#         'tensao_at': {'required': True, 'positive': True, 'label': 'Tensão AT (kV)'},
#         'impedancia': {'required': True, 'min': 0.1, 'max': 30, 'label': 'Impedância (%)'},
#         'tipo_transformador': {'required': True, 'allowed': ['Trifásico', 'Monofásico'], 'label':'Tipo'}
#     }
# )
# if errors:
#     # Exibir erros para o usuário
#     error_message = html.Ul([html.Li(e) for e in errors])
#     return ..., error_message # Retorna mensagem de erro para um Output
# else:
#     # Prosseguir com os cálculos
#     ...