# Análise de Módulos, Dependências e Implementação do dcc.Store

Este documento detalha as variáveis de input de cada módulo, as dependências entre módulos, a estrutura de dados para geração de relatórios, e a implementação do dcc.Store como fonte única da verdade no sistema de simulação de testes de transformadores.

## 1. Transformer Inputs (Dados Básicos)

### Variáveis de Input:
- **Dados Básicos**:
  - `potencia_mva`: Potência nominal em MVA
  - `frequencia`: Frequência nominal em Hz
  - `grupo_ligacao`: Grupo de ligação (ex: Dyn11)
  - `liquido_isolante`: Tipo de líquido isolante
  - `elevacao_oleo_topo`: Elevação do óleo no topo em K
  - `elevacao_enrol`: Elevação do enrolamento em K
  - `tipo_transformador`: Monofásico ou Trifásico
  - `tipo_isolamento`: Tipo de isolamento (uniforme/não-uniforme)
  - `norma_iso`: Norma de isolamento (IEC/IEEE/ABNT)

- **Pesos**:
  - `peso_total`: Peso total em kg
  - `peso_parte_ativa`: Peso da parte ativa em kg
  - `peso_oleo`: Peso do óleo em kg
  - `peso_tanque_acessorios`: Peso do tanque e acessórios em kg

- **Alta Tensão (AT)**:
  - `tensao_at`: Tensão nominal AT em kV
  - `classe_tensao_at`: Classe de tensão AT em kV
  - `impedancia`: Impedância percentual
  - `nbi_at`: Nível Básico de Impulso AT em kV
  - `sil_at`: Nível de Impulso de Manobra AT em kV
  - `conexao_at`: Tipo de conexão AT (Y, D, YN)
  - `tensao_bucha_neutro_at`: Tensão da bucha de neutro AT em kV
  - `nbi_neutro_at`: NBI do neutro AT em kV
  - `sil_neutro_at`: SIL do neutro AT em kV

- **Taps AT**:
  - `tensao_at_tap_maior`: Tensão AT no tap maior em kV
  - `impedancia_tap_maior`: Impedância no tap maior em %
  - `tensao_at_tap_menor`: Tensão AT no tap menor em kV
  - `impedancia_tap_menor`: Impedância no tap menor em %

- **Tensões de Ensaio AT**:
  - `teste_tensao_aplicada_at`: Tensão de ensaio aplicada AT em kV
  - `teste_tensao_induzida_at`: Tensão de ensaio induzida AT em kV

- **Baixa Tensão (BT)**:
  - `tensao_bt`: Tensão nominal BT em kV
  - `classe_tensao_bt`: Classe de tensão BT em kV
  - `nbi_bt`: Nível Básico de Impulso BT em kV
  - `sil_bt`: Nível de Impulso de Manobra BT em kV
  - `conexao_bt`: Tipo de conexão BT (Y, D, YN)
  - `tensao_bucha_neutro_bt`: Tensão da bucha de neutro BT em kV
  - `nbi_neutro_bt`: NBI do neutro BT em kV
  - `sil_neutro_bt`: SIL do neutro BT em kV
  - `teste_tensao_aplicada_bt`: Tensão de ensaio aplicada BT em kV

- **Terciário**:
  - `tensao_terciario`: Tensão nominal terciário em kV
  - `classe_tensao_terciario`: Classe de tensão terciário em kV
  - `nbi_terciario`: Nível Básico de Impulso terciário em kV
  - `sil_terciario`: Nível de Impulso de Manobra terciário em kV
  - `conexao_terciario`: Tipo de conexão terciário (Y, D, YN)
  - `tensao_bucha_neutro_terciario`: Tensão da bucha de neutro terciário em kV
  - `nbi_neutro_terciario`: NBI do neutro terciário em kV
  - `sil_neutro_terciario`: SIL do neutro terciário em kV
  - `teste_tensao_aplicada_terciario`: Tensão de ensaio aplicada terciário em kV

### Variáveis Calculadas:
- **Correntes Nominais**:
  - `corrente_nominal_at`: Corrente nominal AT em A
  - `corrente_nominal_bt`: Corrente nominal BT em A
  - `corrente_nominal_terciario`: Corrente nominal terciário em A
  - `corrente_nominal_at_tap_maior`: Corrente nominal AT no tap maior em A
  - `corrente_nominal_at_tap_menor`: Corrente nominal AT no tap menor em A

### Dependências de Outros Módulos:
- Nenhuma (este é o módulo base)

## 2. Losses (Perdas)

### Variáveis de Input:
- **Perdas em Vazio**:
  - `perdas_vazio_kw`: Perdas em vazio em kW
  - `peso_projeto_Ton`: Peso do projeto em toneladas
  - `corrente_excitacao`: Corrente de excitação em %
  - `inducao_nucleo`: Indução do núcleo em T
  - `corrente_excitacao_1_1`: Corrente de excitação 1.1 em %
  - `corrente_excitacao_1_2`: Corrente de excitação 1.2 em %

- **Perdas em Carga**:
  - `perdas_carga_kw_U_nom`: Perdas em carga no tap nominal em kW
  - `perdas_carga_kw_U_min`: Perdas em carga no tap mínimo em kW
  - `perdas_carga_kw_U_max`: Perdas em carga no tap máximo em kW
  - `temperatura_referencia`: Temperatura de referência em °C

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `tipo_transformador`: Monofásico ou Trifásico
  - `potencia_mva`: Potência nominal em MVA
  - `tensao_at`: Tensão nominal AT em kV
  - `tensao_bt`: Tensão nominal BT em kV
  - `corrente_nominal_at`: Corrente nominal AT em A
  - `corrente_nominal_bt`: Corrente nominal BT em A
  - `impedancia`: Impedância percentual
  - `tensao_at_tap_maior`: Tensão AT no tap maior em kV
  - `impedancia_tap_maior`: Impedância no tap maior em %
  - `tensao_at_tap_menor`: Tensão AT no tap menor em kV
  - `impedancia_tap_menor`: Impedância no tap menor em %
  - `corrente_nominal_at_tap_maior`: Corrente nominal AT no tap maior em A
  - `corrente_nominal_at_tap_menor`: Corrente nominal AT no tap menor em A

### Cálculos Principais:
- **Perdas em Vazio**: Cálculo de perdas no núcleo, corrente de excitação e potência magnética
- **Perdas em Carga**: Cálculo de perdas em carga, tensão de curto-circuito e potência de teste

### Impeditivos de Realização:
- **Perdas em Vazio**:
  - Potência do transformador não informada
  - Tensão nominal não informada
  - Corrente de excitação excessiva (> 10%)
  - Indução do núcleo muito alta (> 1.9T)
  - Potência da fonte insuficiente para excitar o transformador

- **Perdas em Carga**:
  - Potência do transformador não informada
  - Impedância não informada
  - Temperatura de referência fora da faixa (< 0°C ou > 120°C)
  - Potência da fonte insuficiente para o ensaio (< potência nominal * impedância/100)

## 3. Impulse (Impulso)

### Variáveis de Input:
- `test_voltage`: Tensão de teste em kV
- `generator_config`: Configuração do gerador
- `simulation_model_type`: Tipo de modelo de simulação
- `test_object_capacitance`: Capacitância do objeto de teste em pF
- `stray_capacitance`: Capacitância parasita em pF
- `shunt_resistor`: Resistor shunt em Ohms
- `front_resistor_expression`: Expressão do resistor frontal
- `tail_resistor_expression`: Expressão do resistor de cauda
- `inductance_adjustment_factor`: Fator de ajuste da indutância
- `tail_resistance_adjustment_factor`: Fator de ajuste da resistência de cauda
- `external_inductance`: Indutância externa em μH
- `transformer_inductance`: Indutância do transformador em H
- `impulse_type`: Tipo de impulso (lightning, switching)
- `gap_distance`: Distância do gap em cm

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `tensao_at`: Tensão nominal AT em kV
  - `potencia_mva`: Potência nominal em MVA
  - `impedancia`: Impedância percentual
  - `frequencia`: Frequência nominal em Hz
  - `nbi_at`: Nível Básico de Impulso AT em kV
  - `nbi_bt`: Nível Básico de Impulso BT em kV
  - `nbi_terciario`: Nível Básico de Impulso terciário em kV (se existir)

### Cálculos Principais:
- Simulação do circuito de impulso
- Cálculo da indutância do transformador
- Cálculo da eficiência do circuito

## 4. Dieletric Analysis (Análise Dielétrica)

### Variáveis de Input:
- **Para cada enrolamento (AT, BT, Terciário)**:
  - `um`: Tensão máxima do sistema em kV
  - `conexao`: Tipo de conexão
  - `neutro_um`: Tensão máxima do neutro em kV
  - `ia`: Impulso atmosférico em kV
  - `impulso_atm_neutro`: Impulso atmosférico do neutro em kV
  - `im`: Impulso de manobra em kV
  - `tensao_curta`: Tensão de curta duração em kV
  - `tensao_induzida`: Tensão induzida em kV
- `tipo_isolamento`: Tipo de isolamento

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `tipo_transformador`: Monofásico ou Trifásico
  - `tensao_at`: Tensão nominal AT em kV
  - `tensao_bt`: Tensão nominal BT em kV
  - `tensao_terciario`: Tensão nominal terciário em kV
  - `conexao_at`: Tipo de conexão AT
  - `conexao_bt`: Tipo de conexão BT
  - `conexao_terciario`: Tipo de conexão terciário
  - `classe_tensao_at`: Classe de tensão AT em kV
  - `classe_tensao_bt`: Classe de tensão BT em kV
  - `classe_tensao_terciario`: Classe de tensão terciário em kV
  - `nbi_at`: Nível Básico de Impulso AT em kV
  - `nbi_bt`: Nível Básico de Impulso BT em kV
  - `nbi_terciario`: Nível Básico de Impulso terciário em kV
  - `teste_tensao_aplicada_at`: Tensão de ensaio aplicada AT em kV
  - `teste_tensao_aplicada_bt`: Tensão de ensaio aplicada BT em kV
  - `teste_tensao_aplicada_terciario`: Tensão de ensaio aplicada terciário em kV
  - `teste_tensao_induzida_at`: Tensão de ensaio induzida AT em kV

### Cálculos Principais:
- Verificação de níveis de isolamento conforme normas
- Análise de compatibilidade entre níveis de isolamento

## 5. Applied Voltage (Tensão Aplicada)

### Variáveis de Input:
- `cap_at`: Capacitância AT em pF
- `cap_bt`: Capacitância BT em pF
- `cap_ter`: Capacitância Terciário em pF

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `teste_tensao_aplicada_at`: Tensão de ensaio aplicada AT em kV
  - `teste_tensao_aplicada_bt`: Tensão de ensaio aplicada BT em kV
  - `teste_tensao_aplicada_terciario`: Tensão de ensaio aplicada terciário em kV
  - `frequencia`: Frequência nominal em Hz

### Cálculos Principais:
- Cálculo de impedância capacitiva (Zc)
- Cálculo de corrente e potência reativa
- Análise de viabilidade com sistema ressonante
- Recomendação de fonte de ensaio

### Impeditivos de Realização:
- Tensão de ensaio aplicada não informada
- Capacitância do objeto de teste muito baixa (< 100 pF)
- Capacitância do objeto de teste muito alta (> 50000 pF)
- Potência reativa calculada excede capacidade da fonte disponível
- Frequência de teste fora da faixa operacional da fonte

## 6. Induced Voltage (Tensão Induzida)

### Variáveis de Input:
- `frequencia_teste`: Frequência de teste em Hz
- `capacitancia`: Capacitância em pF
- `tipo-transformador`: Tipo de transformador (redundante, já está em transformer-inputs)

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `tipo_transformador`: Monofásico ou Trifásico
  - `tensao_bt`: Tensão nominal BT em kV
  - `frequencia`: Frequência nominal em Hz
  - `teste_tensao_induzida_at`: Tensão de ensaio induzida AT em kV

- **De Losses**:
  - `perdas_vazio_kw`: Perdas em vazio em kW
  - `peso_projeto_Ton`: Peso do projeto em toneladas
  - `inducao_nucleo`: Indução do núcleo em T

### Cálculos Principais:
- Cálculo de potência ativa e magnética
- Cálculo de componente indutiva
- Cálculo de fator de potência magnética e fator de perdas
- Análise de viabilidade com diferentes frequências

### Impeditivos de Realização:
- Tensão de ensaio induzida não informada
- Frequência de teste muito baixa (< 100 Hz)
- Frequência de teste muito alta (> 400 Hz)
- Potência calculada excede capacidade da fonte disponível
- Indução do núcleo muito alta (> 1.9T) para a frequência selecionada

## 7. Short Circuit (Curto-Circuito)

### Variáveis de Input:
- `impedance_before`: Impedância antes do ensaio em %
- `impedance_after`: Impedância após o ensaio em %
- `peak_factor`: Fator de pico
- `isc_side`: Lado do curto-circuito (AT/BT/Terciário)
- `power_category`: Categoria de potência (I/II/III)

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `potencia_mva`: Potência nominal em MVA
  - `tensao_at`: Tensão nominal AT em kV
  - `tensao_bt`: Tensão nominal BT em kV
  - `tensao_terciario`: Tensão nominal terciário em kV
  - `impedancia`: Impedância percentual

### Cálculos Principais:
- Cálculo de corrente de curto-circuito simétrica
- Cálculo de corrente de pico
- Verificação de variação de impedância

### Impeditivos de Realização:
- Potência do transformador não informada
- Impedância não informada
- Impedância antes e após o ensaio iguais (impossível calcular variação)
- Variação de impedância excessiva (> 10%)
- Corrente de curto-circuito calculada excede capacidade da fonte disponível

## 8. Temperature Rise (Elevação de Temperatura)

### Variáveis de Input:
- `temp_amb`: Temperatura ambiente em °C
- `winding_material`: Material do enrolamento
- `res_cold`: Resistência a frio em Ohms
- `temp_cold`: Temperatura a frio em °C
- `res_hot`: Resistência a quente em Ohms
- `temp_top_oil`: Temperatura do topo do óleo em °C
- `delta_theta_oil_max`: Elevação máxima do óleo em K

### Variáveis Usadas de Outros Módulos:
- **De Transformer Inputs**:
  - `elevacao_oleo_topo`: Elevação do óleo no topo em K
  - `elevacao_enrol`: Elevação do enrolamento em K

- **De Losses**:
  - `perdas_vazio_kw`: Perdas em vazio em kW
  - `perdas_carga_kw_U_nom`: Perdas em carga no tap nominal em kW

### Cálculos Principais:
- Cálculo de temperatura média do enrolamento
- Cálculo de elevação do enrolamento
- Cálculo de elevação do topo do óleo
- Cálculo de constante de tempo térmica

### Impeditivos de Realização:
- Resistências a frio e a quente não informadas
- Temperatura a frio não informada
- Temperatura do topo do óleo não informada
- Material do enrolamento não especificado
- Perdas em carga não informadas
- Temperatura ambiente fora da faixa (< -10°C ou > 50°C)

## 9. Estrutura de Dados para Relatórios

Cada módulo deve fornecer dados estruturados para a geração de relatórios. A seguir, apresentamos a estrutura de dados esperada para cada módulo:

### 1. Transformer Inputs (Dados Básicos)

```json
{
  "Dados Básicos": {
    "Tipo de Transformador": "Trifásico",
    "Potência Nominal": "10.0 MVA",
    "Frequência": "60 Hz",
    "Tensão AT": "138 kV",
    "Corrente Nominal AT": "41.8 A",
    "Impedância": "10.5 %",
    "Conexão AT": "YN",
    "NBI AT": "650 kV",
    "Tensão BT": "13.8 kV",
    "Corrente Nominal BT": "418.4 A",
    "Conexão BT": "D",
    "NBI BT": "110 kV",
    "Peso Total": "15000 kg"
  }
}
```

### 2. Losses (Perdas)

```json
{
  "Resultados de Perdas": {
    "Perdas em Vazio": {
      "Perdas em Vazio (kW)": "10.5 kW",
      "Corrente de excitação": "0.5 %",
      "Indução do núcleo": "1.7 T",
      "Potência Mag. (kVAr)": "21.0 kVAr",
      "Fator de perdas (W/kg)": "1.2 W/kg"
    },
    "Perdas em Carga": {
      "Parâmetro": ["Tap Nominal", "Tap Menor", "Tap Maior"],
      "Tensão": ["138 kV", "124.2 kV", "151.8 kV"],
      "Corrente": ["41.8 A", "46.4 A", "38.0 A"],
      "Vcc (%)": ["10.5 %", "9.5 %", "11.5 %"],
      "Vcc (kV)": ["14.49 kV", "11.8 kV", "17.46 kV"],
      "Perdas Totais": ["85 kW", "82 kW", "88 kW"]
    }
  }
}
```

### 3. Impulse (Impulso)

```json
{
  "Resultados de Impulso": {
    "Parâmetros de Simulação": {
      "Tipo de Impulso": "Atmosférico (Lightning)",
      "Tensão de Teste": "650 kV",
      "Resistor Frontal": "15 Ω",
      "Resistor de Cauda": "100 Ω",
      "Capacitância do Objeto": "3000 pF",
      "Indutância Total": "0.05 H"
    },
    "Resultados da Simulação": {
      "Tempo de Frente": "1.2 μs",
      "Tempo de Cauda": "50.0 μs",
      "Tensão de Pico": "650.5 kV",
      "Eficiência": "0.85"
    }
  }
}
```

### 4. Dieletric Analysis (Análise Dielétrica)

```json
{
  "Análise Dielétrica": {
    "Enrolamento AT": {
      "Tensão Máxima (Um)": "145 kV",
      "Conexão": "YN",
      "Impulso Atmosférico (BIL)": "650 kV",
      "Impulso de Manobra (SIL)": "550 kV",
      "Tensão Aplicada": "275 kV",
      "Tensão Induzida": "230 kV"
    },
    "Enrolamento BT": {
      "Tensão Máxima (Um)": "15 kV",
      "Conexão": "D",
      "Impulso Atmosférico (BIL)": "110 kV",
      "Tensão Aplicada": "38 kV"
    },
    "Verificação de Normas": {
      "Status": "APROVADO",
      "Observações": "Todos os níveis de isolamento estão de acordo com as normas."
    }
  }
}
```

### 5. Applied Voltage (Tensão Aplicada)

```json
{
  "Tensão Aplicada": {
    "Dados Calculados": {
      "Parâmetro": ["AT", "BT", "Terciário"],
      "Tensão Ensaio": ["275 kV", "38 kV", "N/A"],
      "Cap. Ensaio": ["2000 pF", "10000 pF", "N/A"],
      "Corrente": ["20.7 mA", "14.3 mA", "N/A"],
      "Zc": ["21.2 kΩ", "2.9 kΩ", "N/A"],
      "Potência Reativa": ["5.7 kVAr", "0.54 kVAr", "N/A"]
    },
    "Recomendação de Fonte": {
      "Sistema Ressonante": "Recomendado para AT",
      "Fonte Convencional": "Adequada para BT"
    }
  }
}
```

### 6. Induced Voltage (Tensão Induzida)

```json
{
  "Tensão Induzida": {
    "Resultados Calculados (Trifásico)": {
      "Tensão Aplicada BT": "13.8 kV",
      "Potência Magnética": "25.0 kVA",
      "Fator Perdas": "1.2 W/kg",
      "Fator Pot. Mag.": "2.5 VAr/kg",
      "Corrente Excitação": "1.05 A",
      "Potência de Teste": "25.1 kVA"
    },
    "Análise de Frequências": {
      "Frequência": ["100 Hz", "120 Hz", "150 Hz", "180 Hz", "200 Hz"],
      "Potência Ativa": ["10.5 kW", "10.8 kW", "11.2 kW", "11.5 kW", "11.8 kW"],
      "Potência Magnética": ["25.0 kVA", "22.5 kVA", "20.0 kVA", "18.5 kVA", "17.0 kVA"]
    }
  }
}
```

### 7. Short Circuit (Curto-Circuito)

```json
{
  "Suportabilidade a Curto-Circuito": {
    "Dados de Entrada": {
      "Impedância Antes": "10.5 %",
      "Impedância Após": "10.8 %",
      "Fator de Pico": "2.55",
      "Lado do Curto": "AT",
      "Categoria": "II"
    },
    "Resultados Calculados": {
      "Isc Simétrica (Isc)": "5.2 kA",
      "Corrente de Pico (ip)": "13.3 kA",
      "Variação Impedância (ΔZ)": "2.86 %",
      "Limite Normativo": "±5 %",
      "Status Verificação": "APROVADO"
    }
  }
}
```

### 8. Temperature Rise (Elevação de Temperatura)

```json
{
  "Elevação de Temperatura": {
    "Dados de Entrada": {
      "Temperatura Ambiente": "25.0 °C",
      "Material do Enrolamento": "Cobre",
      "Resistência a Frio": "0.5 Ω",
      "Temperatura a Frio": "20.0 °C",
      "Resistência a Quente": "0.6 Ω",
      "Temperatura do Topo do Óleo": "75.0 °C"
    },
    "Resultados Calculados": {
      "Constante Material (C)": "235",
      "Temp. Média Enrol. Final (Θw)": "95.0 °C",
      "Elevação Média Enrol. (ΔΘw)": "70.0 K",
      "Elevação Topo Óleo (ΔΘoil)": "50.0 K",
      "Perdas Totais Tap- Wt (Ptot)": "95.5 kW",
      "Const. Tempo Térmica (τ₀)": "3.5 h"
    }
  }
}
```

## 10. Tabela JSON para Classes de Tensão e Níveis de Isolamento

O arquivo `assets/tabela.json` contém dados de referência para classes de tensão e níveis de isolamento, que são usados principalmente no módulo Transformer Inputs para preencher automaticamente valores de NBI, SIL, tensões de ensaio, etc. com base na classe de tensão selecionada.

### Estrutura da Tabela JSON

```json
{
  "info_normas": {
    "nbr_iec": [
      "NBR5356-1",
      "NBR5356-3",
      "IEC60076-1",
      "IEC60076-3",
      "IEC60060-1"
    ],
    "ieee": [
      "IEEE C57.12.00",
      "IEEE C57.12.80",
      "IEEE C57.12.90",
      "IEEE C57.98"
    ],
    "ultima_atualizacao": "2024-08-28"
  },
  "insulation_levels": [
    {
      "id": "IEC_NBR_72.5",
      "standard": "IEC/NBR",
      "um_kv": 72.5,
      "bil_kvp": [325, 350],
      "sil_kvp": null,
      "lic_kvp": [358, 385],
      "bsl_kvp": null,
      "acsd_kv_rms": [140],
      "acld_kv_rms": null,
      "pd_required": true,
      "pd_limits_pc": { "U2_ACSD_Unif": 300, "Upre_ACSD_Unif": 100, "U2_ACSD_Prog": 500, "Upre_ACSD_Prog": 100 },
      "aplicable_pd_profiles": ["ACSD_FaseTerra", "ACSD_FaseFase"],
      "distancias_min_ar_mm": {
        "BIL_325": { "fase_terra": 630, "fase_fase": 630 },
        "BIL_350": { "fase_terra": 630, "fase_fase": 630 }
      },
      "method_ti_applicable": true,
      "classification_li": "Tipo",
      "classification_lic": "Tipo",
      "classification_si": "NA",
      "classification_acsd": "Rotina",
      "classification_acld": "NA",
      "notes": "Níveis IEC/NBR para Um=72.5kV."
    }
  ]
}
```

### Uso da Tabela JSON

A tabela JSON é usada principalmente para:

1. **Preencher Dropdowns de Classes de Tensão**: Os valores de `um_kv` são extraídos para criar as opções dos dropdowns de classe de tensão para AT, BT e terciário.

2. **Sugerir Níveis de Isolamento**: Quando uma classe de tensão é selecionada, os valores de `bil_kvp`, `sil_kvp`, etc. são usados para sugerir níveis de isolamento apropriados.

3. **Validar Níveis de Isolamento**: Os valores da tabela são usados para validar se os níveis de isolamento selecionados estão de acordo com as normas.

### Implementação no Código

```python
# Carregar dados do JSON para as classes de tensão
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'assets', 'tabela.json'), 'r', encoding='utf-8') as f:
        insulation_data = json.load(f)

    # Extrair valores únicos de um_kv e criar opções para o dropdown
    um_kv_values = sorted(list(set([level['um_kv'] for level in insulation_data.get('insulation_levels', []) if 'um_kv' in level])))
    voltage_class_options = [{'label': str(val), 'value': val} for val in um_kv_values]

except FileNotFoundError:
    log.error("Arquivo assets/tabela.json não encontrado. Usando opções vazias para classes de tensão.")
    voltage_class_options = []
```

## 11. Implementação do dcc.Store como Fonte Única da Verdade

### Estrutura de Stores

#### 1. Stores Globais

```python
# components/global_stores.py
def create_global_stores():
    """Cria os stores globais para a aplicação."""
    stores = [
        # Store principal para dados básicos do transformador
        dcc.Store(
            id="transformer-inputs-store",
            storage_type="session",
            data={}
        ),

        # Stores específicos para cada módulo
        dcc.Store(id="losses-store", storage_type="session", data={}),
        dcc.Store(id="impulse-store", storage_type="session", data={}),
        dcc.Store(id="dieletric-analysis-store", storage_type="session", data={}),
        dcc.Store(id="applied-voltage-store", storage_type="session", data={}),
        dcc.Store(id="induced-voltage-store", storage_type="session", data={}),
        dcc.Store(id="short-circuit-store", storage_type="session", data={}),
        dcc.Store(id="temperature-rise-store", storage_type="session", data={}),

        # Store para estado temporário da UI
        dcc.Store(id="ui-state-store", storage_type="memory", data={}),

        # Store para backup/restauração completa
        dcc.Store(id="backup-store", storage_type="memory", data={}),
    ]
    return stores
```

#### 2. Estrutura Padronizada para Cada Store

Cada store deve seguir uma estrutura padronizada para facilitar a manutenção e a geração de relatórios:

```python
{
    "inputs": {
        # Dados de entrada específicos do módulo
    },
    "resultados": {
        # Resultados calculados
    },
    "metadata": {
        "timestamp": "2023-06-01T12:00:00",
        "version": "1.0"
    }
}
```

### Padrões de Implementação

#### 1. Atualização de Dados

Para cada módulo, crie callbacks específicos para atualizar seu store:

```python
@app.callback(
    Output("losses-store", "data"),
    [
        Input("perdas-vazio-kw", "value"),
        Input("peso-projeto-Ton", "value"),
        # outros inputs...
    ],
    State("losses-store", "data"),
    prevent_initial_call=True
)
def atualizar_losses_store(perdas_vazio, peso_projeto, *args, current_data):
    """Atualiza o store de losses com os valores dos inputs."""
    # Identifica qual input foi alterado
    trigger = dash.callback_context.triggered[0]
    input_id = trigger["prop_id"].split(".")[0]

    # Cria uma cópia dos dados atuais
    updated_data = copy.deepcopy(current_data) if current_data else {"inputs": {}, "resultados": {}, "metadata": {}}

    # Inicializa seções se não existirem
    if "inputs" not in updated_data:
        updated_data["inputs"] = {}
    if "vazio" not in updated_data["inputs"]:
        updated_data["inputs"]["vazio"] = {}

    # Atualiza apenas o campo relevante
    if input_id == "perdas-vazio-kw":
        updated_data["inputs"]["vazio"]["perdas_vazio_kw"] = perdas_vazio
    elif input_id == "peso-projeto-Ton":
        updated_data["inputs"]["vazio"]["peso_projeto_Ton"] = peso_projeto
    # outros campos...

    # Atualiza metadata
    updated_data["metadata"] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0"
    }

    return updated_data
```

#### 2. Carregamento de Dados nos Componentes

Para cada componente, crie callbacks para carregar dados do store:

```python
@app.callback(
    [
        Output("perdas-vazio-kw", "value"),
        Output("peso-projeto-Ton", "value"),
        # outros outputs...
    ],
    [
        Input("losses-store", "data"),
        Input("url", "pathname")
    ]
)
def carregar_dados_perdas_vazio(losses_data, pathname):
    """Carrega os dados do store para os componentes."""
    # Verifica se estamos na página de losses
    if not pathname or not pathname.startswith("/losses"):
        raise PreventUpdate

    # Se não houver dados, retorna valores padrão
    if not losses_data or "inputs" not in losses_data or "vazio" not in losses_data["inputs"]:
        return [None, None, ...]  # valores padrão

    # Retorna os valores do store
    vazio_data = losses_data["inputs"]["vazio"]
    return [
        vazio_data.get("perdas_vazio_kw"),
        vazio_data.get("peso_projeto_Ton"),
        # outros valores...
    ]
```

#### 3. Cálculo de Resultados

Para cada módulo, crie callbacks para calcular resultados com base nos inputs:

```python
@app.callback(
    [
        Output("losses-store", "data", allow_duplicate=True),
        Output("resultados-perdas-vazio", "children")
    ],
    Input("calcular-perdas-vazio-btn", "n_clicks"),
    [
        State("losses-store", "data"),
        State("transformer-inputs-store", "data")
    ],
    prevent_initial_call=True
)
def calcular_resultados_perdas_vazio(n_clicks, losses_data, transformer_data):
    """Calcula resultados de perdas em vazio e atualiza o store."""
    if not n_clicks:
        raise PreventUpdate

    # Extrai dados necessários
    vazio_data = losses_data.get("inputs", {}).get("vazio", {})
    perdas_vazio = vazio_data.get("perdas_vazio_kw")
    peso_projeto = vazio_data.get("peso_projeto_Ton")

    # Extrai dados do transformer-inputs
    potencia = transformer_data.get("inputs", {}).get("dados_basicos", {}).get("potencia_mva")
    tensao_bt = transformer_data.get("inputs", {}).get("baixa_tensao", {}).get("tensao_bt")

    # Realiza cálculos
    if perdas_vazio and peso_projeto and potencia and tensao_bt:
        fator_perdas = perdas_vazio / peso_projeto
        potencia_mag = potencia * 0.2  # exemplo simplificado

        # Atualiza resultados no store
        updated_data = copy.deepcopy(losses_data)
        if "resultados" not in updated_data:
            updated_data["resultados"] = {}
        if "vazio" not in updated_data["resultados"]:
            updated_data["resultados"]["vazio"] = {}

        updated_data["resultados"]["vazio"] = {
            "fator_perdas": fator_perdas,
            "potencia_mag": potencia_mag,
            # outros resultados...
        }

        # Atualiza metadata
        updated_data["metadata"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0"
        }

        # Cria componentes para exibir resultados
        resultados_children = [
            html.Div(f"Fator de Perdas: {fator_perdas:.2f} W/kg"),
            html.Div(f"Potência Magnética: {potencia_mag:.2f} kVAr"),
            # outros resultados...
        ]

        return updated_data, resultados_children

    return losses_data, html.Div("Preencha todos os campos para calcular os resultados.")
```

#### 4. Acesso a Dados de Outros Módulos

Em vez de propagar dados entre stores, leia diretamente do store apropriado quando necessário:

```python
@app.callback(
    Output("induced-voltage-store", "data"),
    [
        Input("frequencia-teste", "value"),
        Input("capacitancia", "value"),
        # outros inputs...
    ],
    [
        State("induced-voltage-store", "data"),
        State("transformer-inputs-store", "data"),
        State("losses-store", "data")
    ],
    prevent_initial_call=True
)
def atualizar_induced_voltage_store(frequencia_teste, capacitancia, *args):
    """Atualiza o store de tensão induzida com os valores dos inputs."""
    current_data, transformer_data, losses_data = args[-3:]

    # Extrai dados necessários do transformer-inputs
    tipo_transformador = transformer_data.get("inputs", {}).get("dados_basicos", {}).get("tipo_transformador")
    tensao_bt = transformer_data.get("inputs", {}).get("baixa_tensao", {}).get("tensao_bt")

    # Extrai dados necessários do losses
    perdas_vazio = losses_data.get("inputs", {}).get("vazio", {}).get("perdas_vazio_kw")
    inducao_nucleo = losses_data.get("inputs", {}).get("vazio", {}).get("inducao_nucleo")

    # Atualiza o store
    updated_data = copy.deepcopy(current_data) if current_data else {"inputs": {}, "resultados": {}, "metadata": {}}

    # Atualiza inputs
    if "inputs" not in updated_data:
        updated_data["inputs"] = {}

    updated_data["inputs"]["frequencia_teste"] = frequencia_teste
    updated_data["inputs"]["capacitancia"] = capacitancia

    # Atualiza metadata
    updated_data["metadata"] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0"
    }

    return updated_data
```

### Geração de Relatórios

A geração de relatórios pode ser simplificada com a estrutura padronizada dos stores:

```python
@app.callback(
    Output("download-pdf", "data"),
    Input("generate-report-btn", "n_clicks"),
    [
        State("transformer-inputs-store", "data"),
        State("losses-store", "data"),
        State("impulse-store", "data"),
        State("dieletric-analysis-store", "data"),
        State("applied-voltage-store", "data"),
        State("induced-voltage-store", "data"),
        State("short-circuit-store", "data"),
        State("temperature-rise-store", "data"),
    ],
    prevent_initial_call=True
)
def generate_report(n_clicks, *store_data):
    """Gera o relatório PDF com os dados de todos os stores."""
    if not n_clicks:
        raise PreventUpdate

    # Coleta os dados de todos os stores
    all_data = {
        "basic": store_data[0],
        "losses": store_data[1],
        "impulse": store_data[2],
        "dieletric": store_data[3],
        "applied": store_data[4],
        "induced": store_data[5],
        "short_circuit": store_data[6],
        "temp_rise": store_data[7],
    }

    # Formata os dados para o relatório
    report_data_formatted = {}
    for section, formatter_func in SECTION_FORMATTERS.items():
        try:
            formatted_section = formatter_func(all_data[section])
            if formatted_section:
                report_data_formatted[section] = formatted_section
        except Exception as e:
            log.error(f"Erro ao formatar seção {section}: {e}")

    # Gera o PDF
    pdf_buffer = BytesIO()
    generate_pdf(report_data_formatted, pdf_buffer)
    pdf_buffer.seek(0)

    # Retorna o PDF para download
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_simulacao_{timestamp}.pdf"
    return dcc.send_bytes(pdf_buffer.getvalue(), filename)
```

### Prós e Contras desta Abordagem

#### Vantagens

1. **Estrutura Clara e Consistente**: Cada store tem uma estrutura padronizada com seções para inputs, resultados e metadata.

2. **Separação de Responsabilidades**: Cada módulo é responsável por seus próprios dados, sem depender de propagação de dados entre stores.

3. **Acesso Direto aos Dados**: Quando um módulo precisa de dados de outro módulo, ele lê diretamente do store apropriado.

4. **Facilidade de Manutenção**: A estrutura padronizada facilita a manutenção e a adição de novos módulos.

5. **Geração de Relatórios Simplificada**: A estrutura padronizada facilita a geração de relatórios.

#### Desvantagens

1. **Refatoração Inicial**: Requer refatoração do código existente para adotar a nova estrutura.

2. **Potencial para Duplicação de Dados**: Se não for bem gerenciado, pode haver duplicação de dados entre stores.

3. **Complexidade de Callbacks**: Ainda requer callbacks para atualizar e ler dados dos stores.
