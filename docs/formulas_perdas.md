# Perdas em Transformadores

## Introdução

As perdas em transformadores são divididas em duas categorias principais:

- Perdas em vazio (Fe)
- Perdas em carga (Cu)

# Detalhamento dos Cálculos de Perdas

Este documento detalha as fórmulas e parâmetros usados nos cálculos de perdas em vazio e em carga.

---

## 1. Perdas em Vazio (No-Load Losses)

Cálculos relacionados às perdas que ocorrem no núcleo do transformador quando energizado sem carga.

### 1.1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de perdas em vazio:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   | Status |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- | :----- |
| Perdas em Vazio               | Perdas medidas no núcleo               | kW      | `perdas_vazio`                     | OK     |
| Peso do Núcleo                | Peso estimado/real do núcleo           | Ton     | `peso_nucleo`                      | OK     |
| Corrente de Excitação (%)     | Corrente de excitação nominal          | %       | `corrente_excitacao_percentual`    | OK     |
| Indução do Núcleo             | Nível de indução magnética no núcleo   | T       | `inducao`                          | OK     |
| Frequência                    | Frequência nominal da rede             | Hz      | `frequencia`                       | OK     |
| Tensão BT                     | Tensão nominal do lado de Baixa Tensão | kV      | `tensao_bt`                        | OK     |
| Corrente Nominal BT           | Corrente nominal do lado de Baixa Tensão| A       | `corrente_nominal_bt`              | OK     |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               | OK     |
| Corrente Excitação 1.1pu (%)  | Corrente medida/esperada a 110% Vnom   | %       | `corrente_exc_1_1_input`         | OK     |
| Corrente Excitação 1.2pu (%)  | Corrente medida/esperada a 120% Vnom   | %       | `corrente_exc_1_2_input`         | OK     |

### 1.2. Tabelas de Referência Usadas

* **`perdas_nucleo`**: Tabela com dados de perdas específicas (W/kg) vs. Indução (T) para diferentes tipos de aço (ex: M4).
* **`potencia_magnet`**: Tabela com dados de potência magnetizante específica (VAR/kg) vs. Indução (T).

### 1.3. Comparações: Aço M4 (Referência) vs. Projeto (Dados Entrada)

Comparações entre os valores calculados com base nas tabelas de referência (Aço M4) e os valores derivados dos dados de entrada (Projeto).

* **Fator de Perdas (W/kg):**
  * Aço M4: `fator_perdas` (obtido da tabela `perdas_nucleo` baseado na `inducao`).
  * Projeto: `fator_perdas_projeto` = `perdas_vazio` / `peso_nucleo`.
* **Peso do Núcleo (Ton):**
  * Aço M4 (Estimado): `peso_nucleo_calc` = `perdas_vazio` / `fator_perdas`.
  * Projeto: `peso_nucleo` (Valor de entrada).
* **Fator de Potência Magnética (VAR/kg):**
  * Aço M4: `fator_potencia_mag` (obtido da tabela `potencia_magnet` baseado na `inducao`).
  * Projeto: `fator_potencia_mag_projeto` = `potencia_mag_projeto` / `peso_nucleo`.
* **Potência Magnética (kVAR):**
  * Aço M4 (Estimada): `potencia_mag` = `fator_potencia_mag` * `peso_nucleo_calc`.
  * Projeto: `potencia_mag_projeto` (calculada a partir da `potencia_ensaio_1pu_projeto`, veja abaixo).

### 1.4. Cálculo da Corrente de Excitação (Nominal - 1.0 pu)

* **Constante:** `sqrt_3` (√3, usado para trifásicos).
* **Aço M4 (Estimada):** `corrente_excitacao_calc` = `potencia_mag` / (`tensao_bt` * `sqrt_3`).
* **Projeto (Baseado na Entrada):** `corrente_excitacao_projeto` = `corrente_nominal_bt` * (`corrente_excitacao_percentual` / 100).

### 1.5. Cálculo da Potência Aparente de Ensaio (kVA)

#### 1.5.1. Tensão Nominal (1.0 pu)

* **Aço M4:** `potencia_ensaio_1pu` = `tensao_bt` *`corrente_excitacao_calc`* `sqrt_3`.
* **Projeto:** `potencia_ensaio_1pu_projeto` = `tensao_bt` *`corrente_excitacao_projeto`* `sqrt_3`.
  * *Nota: Este valor (`potencia_ensaio_1pu_projeto`) é usado para calcular a `potencia_mag_projeto` na seção 1.3.*

#### 1.5.2. Tensão Elevada (1.1 pu)

* **Tensão de Teste:** `tensao_teste_1_1` = `tensao_bt` * 1.1.
* **Corrente de Excitação (1.1 pu):**
  * Aço M4 (Estimada): `corrente_excitacao_1_1_calc` = 2 * `corrente_excitacao_calc`.
    * *(Correção: Implementação usa 2x a corrente nominal, não um fator complexo)*
  * Projeto: Usa `corrente_exc_1_1_input` se fornecido, senão estima com base em `corrente_excitacao_projeto` e `fator_excitacao` (3 para trifásico, 5 para monofásico).
* **Potência de Ensaio (1.1 pu):**
  * Aço M4: `potencia_ensaio_1_1pu` = `tensao_teste_1_1` *`corrente_excitacao_1_1_calc`* `sqrt_3`.
  * Projeto: `potencia_ensaio_1_1pu_projeto` (calculada usando a `corrente_excitacao_1_1` do Projeto).

#### 1.5.3. Tensão Elevada (1.2 pu)

* **Tensão de Teste:** `tensao_teste_1_2` = `tensao_bt` * 1.2.
* **Corrente de Excitação (1.2 pu):**
  * Aço M4 (Estimada): `corrente_excitacao_1_2_calc` = 4 * `corrente_excitacao_calc`.
  * Projeto: Usa `corrente_exc_1_2_input` se fornecido, senão estima com base em `corrente_excitacao_projeto` e `fator_excitacao`.
* **Potência de Ensaio (1.2 pu):**
  * Aço M4: `potencia_ensaio_1_2pu_calc` = `tensao_teste_1_2` *`corrente_excitacao_1_2_calc`* `sqrt_3`.
  * Projeto: `potencia_ensaio_1_2pu_projeto` (calculada usando a `corrente_excitacao_1_2` do Projeto).

---

## 2. Perdas em Carga (Load Losses)

Cálculos relacionados às perdas que ocorrem nos enrolamentos devido à corrente de carga.

### 2.1. Parâmetros de Entrada

Valores fornecidos ou obtidos para os cálculos de perdas em carga:

| Parâmetro                 | Descrição                                      | Unidade | Variável no Código         | Status |
| :------------------------ | :--------------------------------------------- | :------ | :------------------------- | :----- |
| Perdas Totais (Nominal)   | Perdas totais medidas no tap nominal           | kW      | `perdas_totais_nom_input`  | OK     |
| Perdas Totais (Menor Tap) | Perdas totais medidas no tap de menor tensão   | kW      | `perdas_totais_min_input`  | OK     |
| Perdas Totais (Maior Tap) | Perdas totais medidas no tap de maior tensão   | kW      | `perdas_totais_max_input`  | OK     |
| Perdas em Vazio           | Perdas no núcleo (resultado da Seção 1)        | kW      | `perdas_vazio_nom`         | OK     |
| Tensão AT Nominal         | Tensão nominal do lado de Alta Tensão          | kV      | `tensao_nominal_at`        | OK     |
| Tensão AT Tap Maior       | Tensão AT no tap de maior tensão               | kV      | `tensao_at_tap_maior`      | OK     |
| Tensão AT Tap Menor       | Tensão AT no tap de menor tensão               | kV      | `tensao_at_tap_menor`      | OK     |
| Impedância Nominal (%)    | Impedância no tap nominal                      | %       | `impedancia`               | OK     |
| Impedância Tap Maior (%)  | Impedância no tap de maior tensão              | %       | `impedancia_tap_maior`     | OK     |
| Impedância Tap Menor (%)  | Impedância no tap de menor tensão              | %       | `impedancia_tap_menor`     | OK     |
| Tipo de Transformador     | Configuração (Monofásico/Trifásico)            | -       | `tipo_transformador`       | OK     |
| Potência Nominal          | Potência Aparente Nominal                      | MVA     | `potencia`                 | OK     |

### 2.2. Cálculos Básicos (para cada Tap - Nominal, Maior, Menor)

* **Perdas em Carga (Pcc - sem vazio):** `perdas_carga_sem_vazio` = `perdas_totais` - `perdas_vazio_nom`.
* **Perdas CC a Frio (25°C):** `perdas_cc_a_frio` = `perdas_carga_sem_vazio` * ((235 + 25) / (235 + temperatura_ref)). *(Fator de correção para Cobre)*.
* **Tensão de Curto-Circuito (Vcc):** `vcc` = (`tensao_at` / 100) * `impedancia_percentual`.
* **Corrente Nominal AT:** `corrente_at` (calculada com base na `potencia` e `tensao_at`).

### 2.3. Cálculos para Condição a Frio (Referência 25°C)

* **Tensão de Ensaio (Frio):** `tensao_frio` = √(`perdas_totais` / `perdas_cc_a_frio`) * `vcc`.
* **Corrente de Ensaio (Frio):** `corrente_frio` = √(`perdas_totais` / `perdas_cc_a_frio`) * `corrente_at`.
* **Potência Aparente de Ensaio (Frio - kVA):** `pteste_frio` = `tensao_frio` *`corrente_frio`* `sqrt_3` / 1000.
* **Potência Ativa EPS (Frio - kW):** `potencia_ativa_eps_frio` = `perdas_totais`.

### 2.4. Cálculos para Condição a Quente (Referência 75°C)

* **Tensão de Ensaio (Quente):** `tensao_quente` = √(`perdas_carga_sem_vazio` / `perdas_cc_a_frio`) * `vcc`.
* **Corrente de Ensaio (Quente):** `corrente_quente` = √(`perdas_carga_sem_vazio` / `perdas_cc_a_frio`) * `corrente_at`.
* **Potência Aparente de Ensaio (Quente - kVA):** `pteste_quente` = `tensao_quente` *`corrente_quente`* `sqrt_3` / 1000.
* **Potência Ativa EPS (Quente - kW):** `potencia_ativa_eps_quente` = `perdas_carga_sem_vazio` * 1.1 *(Fator de segurança/margem)*.

### 2.5. Cálculos para Sobrecarga (Aplicável se Tensão AT ≥ 230kV)

#### 2.5.1. Sobrecarga 1.2 pu (120% Corrente Nominal)

* **Corrente de Sobrecarga:** `corrente_1_2` = `corrente_at` * 1.2.
* **Tensão de Ensaio (1.2 pu):** `tensao_1_2` = `vcc` * 1.2 *(Assumindo Vcc proporcional à corrente)*.
* **Potência Aparente de Ensaio (1.2 pu - kVA):** `pteste_1_2` = `tensao_1_2` *`corrente_1_2`* `sqrt_3` / 1000.
* **Perdas em Carga Estimadas (1.2 pu - kW):** `perdas_1_2` = `perdas_carga_sem_vazio` * (1.2**2).
  * **Correção:** A fórmula base não inclui correção adicional de temperatura para sobrecarga, apenas o fator quadrático da corrente.
* **Potência Ativa EPS (1.2 pu - kW):** `potencia_ativa_eps_1_2` = `perdas_1_2`.

#### 2.5.2. Sobrecarga 1.4 pu (140% Corrente Nominal)

* **Corrente de Sobrecarga:** `corrente_1_4` = `corrente_at` * 1.4.
* **Tensão de Ensaio (1.4 pu):** `tensao_1_4` = `vcc` * 1.4 *(Assumindo Vcc proporcional à corrente)*.
* **Potência Aparente de Ensaio (1.4 pu - kVA):** `pteste_1_4` = `tensao_1_4` *`corrente_1_4`* `sqrt_3` / 1000.
* **Perdas em Carga Estimadas (1.4 pu - kW):** `perdas_1_4` = `perdas_carga_sem_vazio` * (1.4**2).
  * **Correção:** Similar à 1.2 pu, sem correção adicional de temperatura na fórmula base.
* **Potência Ativa EPS (1.4 pu - kW):** `potencia_ativa_eps_1_4` = `perdas_1_4`.

---

## 3. Cálculos do Banco de Capacitores (Cap Bank)

Estimativa da necessidade de capacitores para compensar a reatância durante os ensaios (principalmente Perdas em Carga e Tensão Induzida). Para detalhes específicos sobre os cálculos de tensão induzida, consulte o arquivo `formulas_induzida.md`.

### 3.1. Tensões Disponíveis dos Bancos (kV)

* Lista padrão de tensões nominais dos bancos disponíveis: `cap_bank_voltages` = [13.8, 23.8, 27.6, 41.4, 47.8, 55.2, 71.7, 95.6].

### 3.2. Seleção da Tensão Nominal do Banco

Seleciona a menor tensão de banco que seja maior ou igual à `tensão_teste` calculada para a condição específica (frio, quente, sobrecarga, etc.), considerando ou não um fator de segurança.

* **Com Fator 1.1 (Segurança):** `cap_bank_voltage_com_fator` = Próxima tensão de banco ≥ (`tensão_teste` / 1.1).
* **Sem Fator 1.1:** `cap_bank_voltage_sem_fator` = Próxima tensão de banco ≥ `tensão_teste`.

### 3.3. Fator de Correção (Capacidade Efetiva)

Fator que ajusta a capacidade nominal do banco baseado na sua tensão nominal (bancos de menor tensão podem ter menor capacidade efetiva relativa).

* Fatores aplicados: 0.25 para 13.8kV, 0.75 para 23.8kV, 1.0 para os demais.

### 3.4. Cálculo da Potência Reativa Necessária do Banco (kVAR)

Calcula a potência reativa nominal que o banco selecionado precisa ter para fornecer a `potência_teste` (potência aparente reativa do ensaio) na `tensão_teste`.

* **Com Fator 1.1:**
    `pot_cap_bank_com_fator` = `potência_teste` / ((`tensão_teste` / `cap_bank_voltage_com_fator`)**2 * `factor_com_fator`).
* **Sem Fator 1.1:**
    `pot_cap_bank_sem_fator` = `potência_teste` / ((`tensão_teste` / `cap_bank_voltage_sem_fator`)**2 * `factor_sem_fator`). Status: OK
