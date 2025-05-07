"""
Utilitários para validação de dados em callbacks.
Centraliza funções de validação para evitar duplicação de código.
"""
import logging
from typing import Dict, List, Any, Optional, Union, Callable

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
            return f"{field_name} deve ser maior que zero." if field_name else "Valor deve ser maior que zero."
        return None
    except (ValueError, TypeError):
        return f"{field_name} deve ser um número válido." if field_name else "Valor deve ser um número válido."

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
            return f"{field_name} não pode ser negativo." if field_name else "Valor não pode ser negativo."
        return None
    except (ValueError, TypeError):
        return f"{field_name} deve ser um número válido." if field_name else "Valor deve ser um número válido."

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

def validate_dict_inputs(inputs: Dict[str, Any], 
                        validators: Dict[str, Callable[[Any, str], Optional[str]]]) -> Dict[str, str]:
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
            cleaned_value = value.strip().replace(',', '.')
            # Tentar extrair a parte real se for um número complexo como string
            if 'j' in cleaned_value or 'J' in cleaned_value:
                try:
                    # Remover parênteses se existirem (ex: "(1+2j)")
                    if cleaned_value.startswith('(') and cleaned_value.endswith(')'):
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
