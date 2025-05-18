# Instruções para Transformer Input

Este documento descreve o funcionamento do módulo de entrada de dados do transformador (Transformer Input), com foco especial nos dropdowns de níveis de isolamento (NBI, SIL, TA, TI).

## Estrutura do Transformer Input

O módulo de entrada de dados do transformador é responsável por coletar todas as informações básicas necessárias para os cálculos do sistema, incluindo:

1. Dados gerais do transformador (potência, frequência, etc.)
2. Dados dos enrolamentos (tensão, corrente, conexão, etc.)
3. Níveis de isolamento (NBI, SIL, TA, TI)
4. Dados de refrigeração e temperatura
5. Dados de perdas

Todos esses dados são armazenados no `transformer-inputs-store`, que serve como fonte única de verdade para o sistema.

## Dropdowns de Níveis de Isolamento (NBI, SIL, TA, TI)

### Tabela JSON

Os valores disponíveis para os dropdowns de níveis de isolamento são carregados da tabela JSON localizada em `assets/tabela.json`. Esta tabela contém todos os níveis de isolamento padronizados de acordo com as normas IEC/NBR e IEEE.

#### Estrutura da Tabela JSON

A tabela JSON tem a seguinte estrutura:

```json
{
  "insulation_levels": [
    {
      "id": "1",
      "standard": "IEC/NBR",
      "um_kv": "3.6",
      "bil_kvp": [40, 60],
      "sil_kvp": ["NA_SIL"],
      "acsd_kv_rms": [10],
      "acld_kv_rms": []
    },
    {
      "id": "2",
      "standard": "IEC/NBR",
      "um_kv": "7.2",
      "bil_kvp": [60, 75],
      "sil_kvp": ["NA_SIL"],
      "acsd_kv_rms": [20],
      "acld_kv_rms": []
    },
    // ... mais níveis de isolamento
  ]
}
```

Onde:

- `standard`: Norma aplicável (IEC/NBR ou IEEE)
- `um_kv`: Classe de tensão (kV)
- `bil_kvp`: Valores de NBI disponíveis (kVp)
- `sil_kvp`: Valores de SIL disponíveis (kVp)
- `acsd_kv_rms`: Valores de TA disponíveis (kVrms)
- `acld_kv_rms`: Valores de TI disponíveis (kVrms)

#### Tabela Completa de Níveis de Isolamento (Estilo Excel)

A tabela abaixo apresenta os níveis de isolamento padronizados de acordo com as normas IEC/NBR e IEEE:

##### Norma IEC/NBR

| ID | Um (kV) | NBI (kVp) | SIL (kVp) | TA (kVrms) | TI (kVrms) | Classificação |
|----|---------|-----------|-----------|------------|------------|---------------|
| 1  | 3.6     | 40, 60    | NA_SIL    | 10         | -          | Rotina        |
| 2  | 7.2     | 60, 75    | NA_SIL    | 20         | -          | Rotina        |
| 3  | 12      | 75, 95    | NA_SIL    | 28         | -          | Rotina        |
| 4  | 17.5    | 95, 125   | NA_SIL    | 38         | -          | Rotina        |
| 5  | 24      | 125, 145  | NA_SIL    | 50         | -          | Rotina        |
| 6  | 36      | 145, 170  | NA_SIL    | 70         | -          | Rotina        |
| 7  | 52      | 250       | NA_SIL    | 95         | -          | Rotina        |
| 8  | 72.5    | 325, 450  | NA_SIL    | 140        | 140        | Rotina        |
| 9  | 123     | 450, 550  | NA_SIL    | 230        | 230        | Rotina        |
| 10 | 145     | 550, 650  | NA_SIL    | 275        | 275        | Rotina        |
| 11 | 170     | 650, 750  | NA_SIL    | 325        | 325        | Rotina        |
| 12 | 245     | 850, 950, 1050 | NA_SIL | 395, 460  | 395, 460   | Rotina        |
| 13 | 300     | 950, 1050, 1175 | 750, 850 | 460, 510 | 460, 510 | Rotina        |
| 14 | 362     | 1050, 1175, 1300, 1425 | 850, 950, 1050 | 510, 570 | 510, 570 | Rotina |
| 15 | 420     | 1300, 1425, 1550 | 1050, 1175 | 570, 630, 680 | 570, 630, 680 | Rotina |
| 16 | 550     | 1425, 1550, 1675, 1800 | 1175, 1300, 1425 | 680, 800 | 680, 800 | Rotina |
| 17 | 800     | 1800, 1950, 2100 | 1300, 1425, 1550 | 975, 1100 | 975, 1100 | Rotina |

##### Norma IEEE

| ID | Um (kV) | NBI (kVp) | SIL/BSL (kVp) | TA (kVrms) | TI (kVrms) | Classificação |
|----|---------|-----------|---------------|------------|------------|---------------|
| 18 | 1.2     | 30        | NA_SIL        | 10         | -          | Rotina        |
| 19 | 2.5     | 45        | NA_SIL        | 15         | -          | Rotina        |
| 20 | 5.0     | 60        | NA_SIL        | 19         | -          | Rotina        |
| 21 | 8.7     | 75        | NA_SIL        | 26         | -          | Rotina        |
| 22 | 15.0    | 95, 110   | NA_SIL        | 34, 40     | -          | Rotina        |
| 23 | 25.0    | 150       | NA_SIL        | 50         | -          | Rotina        |
| 24 | 34.5    | 200       | NA_SIL        | 70         | -          | Rotina        |
| 25 | 46.0    | 250       | NA_SIL        | 95         | -          | Rotina        |
| 26 | 69.0    | 350       | NA_SIL        | 140        | 140        | Rotina        |
| 27 | 115.0   | 450, 550  | NA_SIL        | 230        | 230        | Rotina        |
| 28 | 138.0   | 550, 650  | NA_SIL        | 275        | 275        | Rotina        |
| 29 | 161.0   | 650, 750  | NA_SIL        | 325        | 325        | Rotina        |
| 30 | 230.0   | 825, 900, 1050 | NA_SIL   | 395, 460   | 395, 460   | Rotina        |
| 31 | 345.0   | 1050, 1175, 1300 | 825, 900, 975 | 555 | 555 | Rotina |
| 32 | 500.0   | 1425, 1550, 1675, 1800 | 1050, 1175, 1300 | 860 | 860 | Rotina |
| 33 | 765.0   | 1800, 1950, 2050, 2100 | 1300, 1425, 1550 | 970 | 970 | Rotina |

Notas:

1. Para classes de tensão até 72.5 kV (IEC/NBR) ou 69.0 kV (IEEE), o SIL não é aplicável (NA_SIL).
2. Para classes de tensão até 52 kV (IEC/NBR) ou 46.0 kV (IEEE), a Tensão Induzida (TI) não é aplicável.
3. Quando múltiplos valores são listados (separados por vírgula), todos são opções válidas para aquela classe de tensão.
4. A classificação "Rotina" indica que estes são os níveis de isolamento padrão para uso rotineiro.

### Comportamento Esperado

Os dropdowns de níveis de isolamento (NBI, SIL, TA, TI) devem:

1. **Mostrar todas as opções disponíveis**: Quando a página é carregada, os dropdowns devem mostrar todas as opções disponíveis da tabela JSON, mesmo sem uma classe de tensão definida.

2. **Filtrar por classe de tensão**: Quando uma classe de tensão é selecionada, os dropdowns devem mostrar primeiro as opções específicas para aquela classe, seguidas pelas demais opções disponíveis.

3. **Manter valores selecionados**: Os valores selecionados nos dropdowns devem ser mantidos quando o usuário navega entre páginas.

4. **Carregar valores do MCP**: Quando a página é carregada, os dropdowns devem carregar os valores salvos no MCP.

### Fluxo de Funcionamento

#### Carregamento Inicial

1. Quando a página de transformer input é carregada, o callback `populate_dynamic_dropdown_values_on_load` em `transformer_inputs_fix.py` é acionado.
2. Este callback carrega os valores salvos no MCP para todos os campos, incluindo os dropdowns de níveis de isolamento.
3. Paralelamente, os callbacks em `insulation_level_callbacks.py` são acionados para popular as opções dos dropdowns.
4. Os callbacks em `isolation_callbacks.py` são acionados para calcular os níveis de isolamento com base na classe de tensão.

#### Seleção de Classe de Tensão

1. Quando o usuário seleciona uma classe de tensão, os callbacks em `isolation_callbacks.py` são acionados.
2. Estes callbacks calculam os níveis de isolamento apropriados para a classe de tensão selecionada.
3. Os callbacks em `insulation_level_callbacks.py` são acionados para atualizar as opções dos dropdowns, mostrando primeiro as opções específicas para a classe de tensão selecionada.
4. Os valores calculados são sugeridos nos dropdowns, mas não sobrescrevem valores já selecionados pelo usuário.

#### Navegação entre Páginas

1. Quando o usuário navega para outra página, os valores selecionados nos dropdowns são salvos no MCP através do callback `update_transformer_inputs_store` em `transformer_inputs_fix.py`.
2. Quando o usuário retorna à página de transformer input, o callback `populate_dynamic_dropdown_values_on_load` é acionado novamente.
3. Este callback carrega os valores salvos no MCP para todos os campos, incluindo os dropdowns de níveis de isolamento.

### Implementação Técnica

#### Carregamento de Opções

As opções dos dropdowns são carregadas a partir da tabela JSON usando as seguintes funções em `app_core/isolation_repo.py`:

- `get_distinct_values_for_norma`: Obtém valores distintos de uma coluna da tabela para uma norma específica.
- `create_options_for_key`: Cria opções para um dropdown a partir de valores distintos de uma coluna da tabela.

Os callbacks em `insulation_level_callbacks.py` usam essas funções para popular as opções dos dropdowns:

```python
# Carregar todas as opções disponíveis para a norma selecionada
options_nbi = create_options_for_key(standard_filter.split('/')[0], "bil_kvp", " kVp")

# Para SIL, é mais complexo devido ao "NA_SIL" e BSL
sil_distinct_raw = get_distinct_values_for_norma(standard_filter.split('/')[0], "sil_kvp")
# ... código para processar as opções de SIL ...

# Para Tensão Aplicada
options_ta = create_options_for_key(standard_filter.split('/')[0], "acsd_kv_rms", " kVrms")

# Para Tensão Induzida (apenas para AT)
options_ti = []
if winding_prefix == "at":
    # Para Tensão Induzida, podemos combinar ACLD e ACSD para as opções iniciais
    acld_distinct = get_distinct_values_for_norma(standard_filter.split('/')[0], "acld_kv_rms")
    acsd_distinct = get_distinct_values_for_norma(standard_filter.split('/')[0], "acsd_kv_rms")
    combined_ti_raw = sorted(list(set(acld_distinct + acsd_distinct)))
    options_ti = [{"label": f"{val} kVrms", "value": str(val)} for val in combined_ti_raw]
```

#### Filtragem de Opções

Quando uma classe de tensão é selecionada, as opções específicas para aquela classe são obtidas usando a função `get_isolation_levels` em `app_core/isolation_repo.py`:

```python
# Se temos um valor específico de Um, podemos filtrar as opções
if um_kv_val is not None:
    # Obter os níveis de isolamento específicos para esta classe de tensão
    levels_data_dict, _ = get_isolation_levels(um_kv_val, "", norma_para_opcoes)

    # Adicionar os valores específicos no início das listas de opções
    # NBI específico
    specific_nbi = [{"label": f"{val} kVp", "value": str(val)} for val in levels_data_dict.get("nbi_list", []) if val is not None]
    if specific_nbi:
        # Remover duplicatas mantendo a ordem
        seen_nbi = set(opt["value"] for opt in specific_nbi)
        options_nbi = specific_nbi + [opt for opt in options_nbi if opt["value"] not in seen_nbi]

    # ... código similar para SIL, TA e TI ...
```

#### Persistência de Valores

A persistência de valores é gerenciada pelo MCP (Memory Control Panel) e pelo mecanismo de persistência do Dash:

1. O callback `update_transformer_inputs_store` em `transformer_inputs_fix.py` salva os valores selecionados no MCP.
2. O callback `populate_dynamic_dropdown_values_on_load` em `transformer_inputs_fix.py` carrega os valores salvos no MCP.
3. Os componentes Dash têm a propriedade `persistence=True` para manter os valores selecionados no navegador.

### Troubleshooting

#### Dropdowns não mostram opções

Se os dropdowns não estiverem mostrando as opções corretamente:

1. Verifique se os callbacks em `insulation_level_callbacks.py` estão sendo acionados corretamente.
2. Verifique se a tabela JSON está sendo carregada corretamente.
3. Verifique se os callbacks têm `prevent_initial_call=False` para serem acionados quando a página é carregada.

#### Valores não são mantidos entre páginas

Se os valores não estiverem sendo mantidos quando o usuário navega entre páginas:

1. Verifique se os valores estão sendo salvos corretamente no MCP pelo callback `update_transformer_inputs_store`.
2. Verifique se os valores estão sendo carregados corretamente do MCP pelo callback `populate_dynamic_dropdown_values_on_load`.
3. Verifique se os callbacks em `isolation_callbacks.py` não estão sobrescrevendo os valores com `no_update`.

#### Valores são sobrescritos ao selecionar classe de tensão

Se os valores estiverem sendo sobrescritos ao selecionar uma classe de tensão:

1. Verifique se os callbacks em `isolation_callbacks.py` estão usando `no_update` para não sobrescrever valores já selecionados.
2. Verifique se os callbacks em `isolation_callbacks.py` estão verificando se já existem valores no MCP antes de sugerir novos valores.

## Referências

- `transformer_inputs_fix.py`: Callbacks para gerenciar os dados de entrada do transformador
- `insulation_level_callbacks.py`: Callbacks para carregar opções dos dropdowns de níveis de isolamento
- `isolation_callbacks.py`: Callbacks para calcular níveis de isolamento
- `app_core/isolation_repo.py`: Funções para obter níveis de isolamento da tabela JSON
- `assets/tabela.json`: Tabela com níveis de isolamento
