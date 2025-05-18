# Detalhamento dos Cálculos de Tensão Induzida

Este documento detalha as fórmulas e parâmetros usados nos cálculos de tensão induzida para transformadores monofásicos e trifásicos.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de tensão induzida:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   | Status |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- | :----- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               | OK     |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                        | OK     |
| Tensão Nominal BT             | Tensão nominal do lado de Baixa Tensão | kV      | `tensao_bt`                        | OK     |
| Frequência Nominal            | Frequência nominal da rede             | Hz      | `freq_nominal`                     | OK     |
| Frequência de Teste           | Frequência do ensaio de tensão induzida| Hz      | `freq_teste`                       | OK     |
| Tensão de Prova               | Tensão de ensaio aplicada              | kV      | `tensao_prova`                     | OK     |
| Capacitância AT-GND           | Capacitância entre AT e terra          | pF      | `capacitancia`                     | OK     |
| Indução Nominal               | Nível de indução magnética nominal     | T       | `inducao_nominal`                  | OK     |
| Peso do Núcleo                | Peso do núcleo do transformador        | Ton     | `peso_nucleo`                      | OK     |
| Perdas em Vazio               | Perdas no núcleo                       | kW      | `perdas_vazio`                     | OK     |

## 2. Tabelas de Referência Usadas

* **`potencia_magnet`**: Tabela com dados de potência magnetizante específica (VAr/kg) vs. Indução (T) e Frequência (Hz).
* **`perdas_nucleo`**: Tabela com dados de perdas específicas (W/kg) vs. Indução (T) e Frequência (Hz).

## 3. Cálculos Intermediários

### 3.1. Relações Básicas

* **Relação entre frequência de teste e frequência nominal:** `fp_fn = freq_teste / freq_nominal`
* **Relação entre tensão de prova e tensão nominal (Up/Un):**
  * Para transformadores monofásicos: `up_un = tensao_prova / tensao_at`
  * Para transformadores trifásicos: `up_un = tensao_prova / (tensao_at / sqrt(3))`
  * os dados up_un = tensao_prova deverão ser os dados de tenão de ensaio induzida informados em dados básicos

### 3.2. Indução no Núcleo na Frequência de Teste

* **Fórmula:** `inducao_teste = inducao_nominal * (tensao_induzida / tensao_at) * (freq_nominal / freq_teste)`
* **Limitação:** Se `inducao_teste > 1.9 T`, então `inducao_teste = 1.9 T` (limite físico típico)

### 3.3. Tensão Aplicada no Lado BT

* **Para transformadores monofásicos:** `tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova`
* **Para transformadores trifásicos:** `tensao_aplicada_bt = (tensao_bt / tensao_at) * tensao_prova`

### 3.4. Interpolação de Fatores das Tabelas

* **Fator de Potência Magnética:** Obtido por interpolação bilinear da tabela `potencia_magnet` usando `inducao_teste` e `freq_teste`
* **Fator de Perdas:** Obtido por interpolação bilinear da tabela `perdas_nucleo` usando `inducao_teste` e `freq_teste`

## 4. Cálculos para Transformadores Monofásicos

### 4.1. Potência Ativa (Pw)

* **Fórmula:** `pot_ativa = fator_perdas * peso_nucleo_kg / 1000.0` (kW)

### 4.2. Potência Magnética (Sm)

* **Fórmula:** `pot_magnetica = fator_potencia_mag * peso_nucleo_kg / 1000.0` (kVA)

### 4.3. Componente Indutiva (Sind)

* **Fórmula:** `pot_induzida = sqrt(pot_magnetica^2 - pot_ativa^2)` (kVAr ind)
* **Verificação:** Se `pot_magnetica^2 < pot_ativa^2`, então `pot_induzida = 0`

### 4.4. Tensão para Cálculo de Scap (U_calc_scap)

* **Fórmula:** `u_calc_scap = tensao_prova - (up_un * tensao_bt)` (kV)

### 4.5. Potência Capacitiva (Scap)

* **Fórmula:** `pcap = -((u_calc_scap * 1000)^2 * 2 * π * freq_teste * capacitancia * 10^-12) / 3 / 1000` (kVAr cap)
* O sinal negativo indica potência reativa capacitiva
* Divisão por 3 para ajustar o valor da potência capacitiva para transformadores monofásicos
* Conversão de kV para V (multiplicação por 1000) e de VAr para kVAr (divisão por 1000)

### 4.6. Razão Scap/Sind

* **Fórmula:** `scap_sind_ratio = abs(pcap) / pot_induzida` (adimensional)
* **Verificação:** Se `pot_induzida = 0`, então `scap_sind_ratio = 0`

## 5. Cálculos para Transformadores Trifásicos

### 5.1. Potência Ativa Total (Pw)

* **Fórmula:** `pot_ativa_total = fator_perdas * peso_nucleo_kg / 1000.0` (kW)

### 5.2. Potência Magnética Total (Sm)

* **Fórmula:** `pot_magnetica_total = fator_potencia_mag * peso_nucleo_kg / 1000.0` (kVA)

### 5.3. Corrente de Excitação (Iexc)

* **Fórmula:** `corrente_excitacao = pot_magnetica_total / (tensao_aplicada_bt * sqrt(3))` (A)

### 5.4. Potência de Teste Total

* **Fórmula:** `potencia_teste = corrente_excitacao * tensao_aplicada_bt * sqrt(3)` (kVA)

## 6. Tabela de Frequências

A tabela de frequências calcula os parâmetros acima para diferentes frequências de teste (100, 120, 150, 180, 200, 240 Hz) e apresenta os resultados em formato tabular e gráfico.

### 6.1. Visualização Gráfica

* **Escala Linear:** Apresenta as potências (Ativa, Magnética, Indutiva para monofásicos, Capacitiva) em função da frequência
* **Escala Logarítmica:** Mesmos dados em escala logarítmica para melhor visualização quando há grandes diferenças de magnitude

### 6.2. Diferenças entre Monofásico e Trifásico

* **Monofásico:** Exibe Frequência, Potência Ativa, Potência Magnética, Componente Indutiva, Potência Capacitiva e razão Scap/Sind
* **Trifásico:** Exibe Frequência, Potência Ativa, Potência Magnética e Potência Capacitiva

## 7. Recomendações para o Teste

### 7.1. Para Transformadores Monofásicos

* **Potência Total Recomendada:** `max(pot_magnetica, pot_ativa + pcap) * 1.2` (kVA)
* **Tensão de Saída Recomendada:** `tensao_aplicada_bt * 1.1` (kV)
* **Potência Ativa Mínima:** `pot_ativa * 1.2` (kW)
* **Potência Reativa Indutiva:** `pot_induzida * 1.2` (kVAr ind)
* **Potência Reativa Capacitiva:** `pcap * 1.2` (kVAr cap)

### 7.2. Para Transformadores Trifásicos

* **Potência Total Recomendada:** `potencia_teste * 1.2` (kVA)
* **Tensão de Saída Recomendada:** `tensao_aplicada_bt * 1.1` (kV)
* **Corrente Nominal Mínima:** `corrente_excitacao * 1.5` (A)
* **Potência Magnética:** `pot_magnetica_total` (kVA)

---

## Notas Importantes

1. A indução no núcleo durante o teste é limitada a 1.9 T para evitar saturação excessiva.
2. Para transformadores trifásicos, a tensão de fase (tensão de linha dividida por √3) é usada como referência para alguns cálculos.
3. A potência capacitiva é calculada com sinal negativo para indicar que é uma potência reativa capacitiva.
4. A tabela de frequências permite analisar o comportamento do transformador em diferentes frequências de teste.
5. Os gráficos em escala logarítmica são úteis quando há grandes diferenças entre os valores das potências.
