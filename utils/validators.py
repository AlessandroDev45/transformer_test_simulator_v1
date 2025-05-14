"""
Utilitários para validação de dados em callbacks.
Centraliza funções de validação para evitar duplicação de código.
"""
import logging
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


def validate_positive_float(value: Any, field_name: str = None) -> Optional[str]:
    """
    Valida se um valor é um número de ponto flutuante positivo.

    Args:
        value: Valor a ser validado
        field_name: Nome do campo (para mensagem de erro)

    Returns:
        None se válido, mensagem de erro se inválido
    """
    if value is None:
        return f"{field_name} não pode ser vazio." if field_name else "Valor não pode ser vazio."

    try:
        float_value = float(value)
        if float_value <= 0:
            return (
                f"{field_name} deve ser maior que zero."
                if field_name
                else "Valor deve ser maior que zero."
            )
        return None
    except (ValueError, TypeError):
        return (
            f"{field_name} deve ser um número válido."
            if field_name
            else "Valor deve ser um número válido."
        )


def validate_non_negative_float(value: Any, field_name: str = None) -> Optional[str]:
    """
    Valida se um valor é um número de ponto flutuante não negativo.

    Args:
        value: Valor a ser validado
        field_name: Nome do campo (para mensagem de erro)

    Returns:
        None se válido, mensagem de erro se inválido
    """
    if value is None:
        return f"{field_name} não pode ser vazio." if field_name else "Valor não pode ser vazio."

    try:
        float_value = float(value)
        if float_value < 0:
            return (
                f"{field_name} não pode ser negativo."
                if field_name
                else "Valor não pode ser negativo."
            )
        return None
    except (ValueError, TypeError):
        return (
            f"{field_name} deve ser um número válido."
            if field_name
            else "Valor deve ser um número válido."
        )


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
    """
    Valida se todos os campos obrigatórios estão presentes e não vazios.

    Args:
        data: Dicionário com os dados a serem validados
        required_fields: Lista de nomes de campos obrigatórios

    Returns:
        Dicionário com mensagens de erro por campo (vazio se todos válidos)
    """
    errors = {}
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            errors[field] = f"Campo '{field}' é obrigatório."
    return errors


def validate_dict_inputs(
    inputs: Dict[str, Any], validators: Dict[str, Callable[[Any, str], Optional[str]]]
) -> Dict[str, str]:
    """
    Valida múltiplos campos usando validadores específicos.

    Args:
        inputs: Dicionário com os valores a serem validados
        validators: Dicionário mapeando nomes de campos para funções validadoras

    Returns:
        Dicionário com mensagens de erro por campo (vazio se todos válidos)
    """
    errors = {}
    for field_name, validator in validators.items():
        if field_name in inputs:
            error = validator(inputs[field_name], field_name)
            if error:
                errors[field_name] = error
    return errors


def require_fields(locals_dict: Dict[str, Any], field_names: List[str]) -> Dict[str, str]:
    """
    Função de conveniência para validar campos obrigatórios a partir de locals().

    Args:
        locals_dict: Dicionário locals() do callback
        field_names: Lista de nomes de campos obrigatórios

    Returns:
        Dicionário com mensagens de erro por campo (vazio se todos válidos)
    """
    data = {name: locals_dict.get(name) for name in field_names}
    return validate_required_fields(data, field_names)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Converte um valor para float de forma segura.

    Args:
        value: Valor a ser convertido
        default: Valor padrão se a conversão falhar

    Returns:
        Valor convertido ou default
    """
    if value is None or value == "":
        return default

    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned_value = value.strip().replace(",", ".")
            # Tentar extrair a parte real se for um número complexo como string
            if "j" in cleaned_value or "J" in cleaned_value:
                try:
                    # Remover parênteses se existirem (ex: "(1+2j)")
                    if cleaned_value.startswith("(") and cleaned_value.endswith(")"):
                        cleaned_value = cleaned_value[1:-1]
                    complex_num = complex(cleaned_value)
                    return float(complex_num.real)
                except ValueError:
                    # Se falhar como complexo, tenta como float normal
                    pass
            return float(cleaned_value)
        # Tentar converter outros tipos
        return float(value)
    except (ValueError, TypeError):
        return default


# --- Funções de validação adicionais (migradas de components/validators.py) ---


def is_valid_number(
    value, min_val=None, max_val=None, allow_none=False, field_name="Campo"
) -> Tuple[bool, str]:
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
        num = float(value)  # Tenta converter para float
        if math.isnan(num) or math.isinf(num):
            return False, f"{field_name}: Valor numérico inválido (NaN ou Infinito)."
    except (ValueError, TypeError):
        return False, f"{field_name}: '{value}' não é um número válido."

    if min_val is not None and num < min_val:
        return False, f"{field_name}: Valor ({num}) abaixo do mínimo permitido ({min_val})."
    if max_val is not None and num > max_val:
        return False, f"{field_name}: Valor ({num}) acima do máximo permitido ({max_val})."

    return True, ""


def is_positive_number(
    value, allow_zero=False, allow_none=False, field_name="Campo"
) -> Tuple[bool, str]:
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
        return True, ""  # Já validado por is_valid_number

    # Se chegou aqui, value é um número válido (não None, NaN, Inf)
    num = float(value)

    if allow_zero:
        if num < 0:
            return False, f"{field_name}: Valor ({num}) não pode ser negativo."
    else:
        if num <= 0:
            return False, f"{field_name}: Valor ({num}) deve ser estritamente positivo."

    return True, ""


def is_required(value, field_name="Campo") -> Tuple[bool, str]:
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


def validate_transformer_inputs(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Valida os dados de entrada do transformador.

    Args:
        data: Dicionário com os dados do transformador

    Returns:
        Dict[str, List[str]]: Dicionário com mensagens de erro por campo
    """
    # Define validation rules specific to transformer inputs
    rules = {
        "potencia_mva": {"required": True, "positive": True, "label": "Potência"},
        "tensao_at": {"required": True, "positive": True, "label": "Tensão AT"},
        "tensao_bt": {"required": True, "positive": True, "label": "Tensão BT"},
        "frequencia": {"required": True, "min": 50, "max": 60, "label": "Frequência"},
        "impedancia": {
            "required": False,
            "min": 0.1,
            "max": 30,
            "label": "Impedância Nom.",
        },  # Allow None/empty
        # Add more rules for other fields as needed
    }

    # Validate using the enhanced validate_dict_inputs function
    errors_list = validate_dict_inputs_enhanced(data, rules)

    # Convert list of errors to dictionary format expected by MCP
    errors_dict = {}
    for error in errors_list:
        field = error.split(":", 1)[0].strip()
        message = error
        if field not in errors_dict:
            errors_dict[field] = []
        errors_dict[field].append(message)

    return errors_dict


def validate_dict_inputs_enhanced(
    data: Dict[str, Any], validations: Dict[str, Dict[str, Any]]
) -> List[str]:
    """
    Valida múltiplos campos dentro de um dicionário com base em regras especificadas.
    Versão melhorada que combina funcionalidades de ambas as implementações anteriores.

    Args:
        data: O dicionário contendo os dados a serem validados (ex: dados de um Store).
        validations: Um dicionário onde as chaves são os nomes dos campos em 'data'
                   e os valores são dicionários especificando as regras de validação.
                   Exemplo:
                   {
                       'potencia_mva': {'required': True, 'positive': True, 'label': 'Potência'},
                       'tensao_at': {'required': True, 'min': 0.1, 'label': 'Tensão AT'},
                       'frequencia': {'required': False, 'default': 60, 'min': 10, 'max': 500, 'label': 'Frequência'}
                       'tipo': {'required': True, 'allowed': ['Trifásico', 'Monofásico'], 'label': 'Tipo'}
                   }

    Returns:
        List[str]: Uma lista de mensagens de erro. Lista vazia se tudo for válido.
    """
    errors = []
    if not isinstance(data, dict):
        return ["Erro interno: Dados de entrada para validação não são um dicionário."]
    if not isinstance(validations, dict):
        return ["Erro interno: Definição de validação inválida."]

    for field, rules in validations.items():
        value = data.get(field)  # Pega o valor do dicionário de dados
        label = rules.get("label", field)  # Usa label fornecido ou o nome do campo

        # 1. Validação de Obrigatoriedade
        if rules.get("required", False):
            is_valid, msg = is_required(value, field_name=label)
            if not is_valid:
                errors.append(msg)
                continue  # Pula outras validações se for obrigatório e ausente

        # Pula validações adicionais se o valor for None e não for obrigatório
        if value is None and not rules.get("required", False):
            continue

        # 2. Validação de Tipo (Exemplo: número)
        is_numeric_type = (
            "min" in rules
            or "max" in rules
            or rules.get("positive", False)
            or rules.get("allow_zero", False)
        )
        if is_numeric_type:
            # Pode ser positivo ou apenas número com range
            if rules.get("positive", False):
                is_valid, msg = is_positive_number(
                    value,
                    allow_zero=rules.get("allow_zero", False),
                    allow_none=not rules.get("required", False),  # Permite None se não obrigatório
                    field_name=label,
                )
            else:  # Apenas verifica se é número e dentro do range
                is_valid, msg = is_valid_number(
                    value,
                    min_val=rules.get("min"),
                    max_val=rules.get("max"),
                    allow_none=not rules.get("required", False),  # Permite None se não obrigatório
                    field_name=label,
                )
            if not is_valid:
                errors.append(msg)
                continue  # Pula outras validações numéricas se esta falhar

        # 3. Validação de Valores Permitidos (Dropdowns, RadioItems)
        allowed_values = rules.get("allowed")
        if allowed_values and isinstance(allowed_values, list):
            # Converte valor para string para comparação segura se não for None
            value_str = str(value) if value is not None else None
            if value_str not in map(str, allowed_values):  # Compara como strings
                allowed_str = ", ".join(map(str, allowed_values))
                errors.append(f"{label}: Valor '{value}' inválido. Permitidos: {allowed_str}.")
                continue

        # Adicionar mais tipos de validação aqui (regex, etc.)

    return errors
