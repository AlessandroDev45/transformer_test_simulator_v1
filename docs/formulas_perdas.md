# Detalhamento dos Cálculos de Perdas em Transformadores

## Sumário do Documento

* **Introdução**:

  * **Definição de Perdas em Vazio (**

  ```
  PFe
  ```

  ) e Perdas em Carga (

  ```
  PCu
  ```

  ).
* **Limites e Parâmetros do Sistema de Teste**:

  * **EPS (Electronic Power Supply)**.
* **SUT (Step-Up Transformer)**.
* **Perdas em Vazio (No-Load Losses)**:

  * **Parâmetros de Entrada.**
* **Tabelas de Referência para Aço M4.**
* **Variáveis Calculadas (Base Aço M4 e Base Projeto).**
* **Análise SUT/EPS para Perdas em Vazio.**
* **Exemplo Numérico Detalhado de Perdas em Vazio.**
* **Perdas em Carga (Load Losses)**:

  * **Parâmetros de Entrada.**
* **Cenários de Cálculo.**
* **Variáveis Calculadas (Por Tap e Cenário).**
* **Cálculo do Banco de Capacitores** **Requerido** **(**calculate_cap_bank**).**
* **Configuração do Banco de Capacitores (Disponível/Sugerido) e Lógica de Seleção.**
* **Análise SUT/EPS para Perdas em Carga (Corrente Compensada com** **calculate_sut_eps_current_compensated**).
* **Exemplo Numérico Detalhado de Perdas em Carga.**
* **Configuração Detalhada dos Bancos de Capacitores**:

  * **Capacitores Disponíveis por Nível de Tensão Nominal.**
* **Potência das Chaves Q.**
* **Lógica de Seleção Implementada.**
* **Potências Mínima e Máxima Teóricas por Nível de Tensão.**

---

## 1. Introdução

**As perdas em transformadores são um fator crucial no projeto e operação desses equipamentos. Elas são tipicamente divididas em duas categorias principais (outros tipos de perdas não são abordados neste documento):**

* **Perdas em Vazio (Perdas no Núcleo ou Perdas em Ferro -**

  <pre _ngcontent-ng-c1554618750=""><strong _ngcontent-ng-c2459883256="" class="ng-star-inserted"><code _ngcontent-ng-c1554618750="" class="rendered"><span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>P</mi><mrow><mi>F</mi><mi>e</mi></mrow></msub></mrow></semantics></math></span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut"></span><span class="mord"><span class="mord mathnormal">P</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">F</span><span class="mord mathnormal mtight">e</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span></span></span></span></code></strong></pre>

  **):** **Ocorrem devido à histerese e correntes parasitas no núcleo magnético quando o transformador está energizado, mesmo sem carga conectada ao secundário. São dependentes da tensão e frequência aplicadas.**
* **Perdas em Carga (Perdas nos Enrolamentos ou Perdas no Cobre -**

  <pre _ngcontent-ng-c1554618750=""><strong _ngcontent-ng-c2459883256="" class="ng-star-inserted"><code _ngcontent-ng-c1554618750="" class="rendered"><span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>P</mi><mrow><mi>C</mi><mi>u</mi></mrow></msub></mrow></semantics></math></span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut"></span><span class="mord"><span class="mord mathnormal">P</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">C</span><span class="mord mathnormal mtight">u</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span></span></span></span></code></strong></pre>

  **):** **Ocorrem devido à resistência ôhmica dos enrolamentos primário e secundário quando o transformador está sob carga. São proporcionais ao quadrado da corrente de carga.**

**Este documento detalha as fórmulas, parâmetros e lógicas de decisão utilizados nos cálculos de perdas em vazio e em carga, conforme implementado no sistema de análise (**losses.py**).**

---

## 2. Limites e Parâmetros do Sistema de Teste

### 2.1. Limites do EPS (Electronic Power Supply)

**O EPS é a fonte de alimentação eletrônica que alimenta o SUT (Transformador Elevador de Teste).**

| **Parâmetro**                  | **Valor** | **Unidade** | **Variável no Código (**utils.constants**)** |
| ------------------------------------- | --------------- | ----------------- | ---------------------------------------------------------- |
| Tensão Máxima de Saída (BT do SUT) | 480             | V                 | SUT_BT_VOLTAGE                                             |
| Corrente Máxima de Saída            | 2000            | A                 | EPS_CURRENT_LIMIT                                          |
| Potência Ativa Máxima (para o DUT)  | 1350            | kW                | DUT_POWER_LIMIT                                            |

### 2.2. Parâmetros do SUT (Step-Up Transformer)

**O SUT é utilizado para elevar a tensão do EPS aos níveis necessários para testar o DUT (Device Under Test).**

| **Parâmetro**    | **Valor** | **Unidade** | **Variável no Código (**utils.constants**)** |
| ----------------------- | --------------- | ----------------- | ---------------------------------------------------------- |
| Tensão Nominal Lado BT | 480             | V                 | SUT_BT_VOLTAGE                                             |
| Tensão Mínima Lado AT | 14000           | V                 | SUT_AT_MIN_VOLTAGE                                         |
| Tensão Máxima Lado AT | 140000          | V                 | SUT_AT_MAX_VOLTAGE                                         |
| Passo de Tensão AT     | 3000            | V                 | SUT_AT_STEP_VOLTAGE                                        |

---

## 3. Perdas em Vazio (No-Load Losses)

**Cálculos referentes às perdas no núcleo do DUT quando energizado em sua tensão nominal (ou variações como 1.1 pu e 1.2 pu) e frequência nominal, sem carga. Testes são realizados aplicando tensão no lado de Baixa Tensão (BT) do DUT.**

### 3.1. Parâmetros de Entrada (UI e Dados do Transformador)

| **Parâmetro**  | **Descrição**                               | **Unidade** | **Variável Python (**losses.py**)** | **Origem** |
| --------------------- | --------------------------------------------------- | ----------------- | ------------------------------------------------ | ---------------- |
| perdas_vazio_ui       | Perdas em vazio (no-load) de projeto                | kW                | perdas_vazio_ui                                  | UI               |
| peso_nucleo_ui        | Peso do núcleo de projeto                          | Ton               | peso_nucleo_ui                                   | UI               |
| corrente_excitacao_ui | Corrente de excitação nominal de projeto          | %                 | corrente_excitacao_ui                            | UI               |
| inducao_ui            | Indução magnética nominal de projeto no núcleo  | T                 | inducao_ui                                       | UI               |
| corrente_exc_1_1_ui   | Corrente de excitação de projeto a 110% V nominal | %                 | corrente_exc_1_1_ui                              | UI (Opcional)    |
| corrente_exc_1_2_ui   | Corrente de excitação de projeto a 120% V nominal | %                 | corrente_exc_1_2_ui                              | UI (Opcional)    |
| frequencia            | Frequência nominal do DUT                          | Hz                | frequencia                                       | Dados Transf.    |
| tensao_bt_kv          | Tensão nominal BT do DUT                           | kV                | tensao_bt_kv                                     | Dados Transf.    |
| corrente_nominal_bt   | Corrente nominal BT do DUT                          | A                 | corrente_nominal_bt                              | Dados Transf.    |
| tipo_transformador    | Monofásico ou Trifásico                           | -                 | tipo_transformador                               | Dados Transf.    |

### 3.2. Tabelas de Referência para Aços

#### 3.2.1. Aço M4 (Referência)

##### 3.2.1.1. Tabela de Perdas Específicas do Núcleo (W/kg)

**Valores de perdas específicas (W/kg) em função da indução magnética (T) e frequência (Hz). Estes dados são armazenados em** **perdas_nucleo_data**.

| **Indução (T)** | **50 Hz** | **60 Hz** | **100 Hz** | **120 Hz** | **150 Hz** | **200 Hz** | **240 Hz** | **250 Hz** | **300 Hz** | **350 Hz** | **400 Hz** | **500 Hz** |
| ----------------------- | --------------- | --------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| **0.5**           | **0.10**  | **0.13**  | **0.25**   | **0.35**   | **0.50**   | **0.80**   | **1.10**   | **1.15**   | **1.30**   | **1.50**   | **1.70**   | **2.10**   |
| **0.6**           | **0.12**  | **0.18**  | **0.38**   | **0.48**   | **0.70**   | **1.10**   | **1.50**   | **1.60**   | **2.00**   | **2.40**   | **2.80**   | **3.50**   |
| **0.7**           | **0.15**  | **0.23**  | **0.50**   | **0.62**   | **0.95**   | **1.55**   | **2.10**   | **2.30**   | **3.00**   | **3.60**   | **4.20**   | **5.50**   |
| **0.8**           | **0.20**  | **0.30**  | **0.65**   | **0.80**   | **1.20**   | **2.00**   | **2.80**   | **3.00**   | **3.90**   | **4.70**   | **5.50**   | **7.50**   |
| **0.9**           | **0.25**  | **0.37**  | **0.82**   | **1.00**   | **1.50**   | **2.50**   | **3.50**   | **3.80**   | **4.80**   | **5.80**   | **6.80**   | **9.00**   |
| **1.0**           | **0.32**  | **0.46**  | **1.00**   | **1.25**   | **1.85**   | **3.10**   | **4.20**   | **4.50**   | **5.90**   | **7.00**   | **8.50**   | **11.00**  |
| **1.1**           | **0.41**  | **0.55**  | **1.21**   | **1.55**   | **2.20**   | **3.70**   | **5.00**   | **5.40**   | **6.90**   | **8.50**   | **10.00**  | **14.00**  |
| **1.2**           | **0.50**  | **0.65**  | **1.41**   | **1.90**   | **2.70**   | **4.50**   | **6.00**   | **6.40**   | **8.10**   | **10.00**  | **12.00**  | **17.00**  |
| **1.3**           | **0.60**  | **0.80**  | **1.65**   | **2.30**   | **3.20**   | **5.20**   | **7.00**   | **7.50**   | **9.50**   | **11.50**  | **14.00**  | **20.00**  |
| **1.4**           | **0.71**  | **0.95**  | **1.95**   | **2.80**   | **3.80**   | **6.00**   | **8.50**   | **9.00**   | **11.00**  | **13.50**  | **16.00**  | **24.00**  |
| **1.5**           | **0.85**  | **1.10**  | **2.30**   | **3.30**   | **4.50**   | **7.00**   | **10.00**  | **10.60**  | **13.00**  | **15.50**  | **19.00**  | **29.00**  |
| **1.6**           | **1.00**  | **1.30**  | **2.80**   | **3.80**   | **5.30**   | **8.00**   | **12.00**  | **12.60**  | **15.00**  | **18.00**  | **23.00**  | **35.00**  |
| **1.7**           | **1.20**  | **1.55**  | **3.50**   | **4.40**   | **6.00**   | **9.00**   | **15.00**  | **15.60**  | **18.00**  | **22.00**  | **28.00**  | **42.00**  |

##### 3.2.1.2. Tabela de Potência Magnetizante Específica (VAR/kg)

**Valores de potência magnetizante específica (VAR/kg) em função da indução magnética (T) e frequência (Hz). Estes dados são armazenados em** **potencia_magnet_data**.

| **Indução (T)** | **50 Hz** | **60 Hz** | **100 Hz** | **120 Hz** | **150 Hz** | **200 Hz** | **240 Hz** | **250 Hz** | **300 Hz** | **350 Hz** | **400 Hz** | **500 Hz** |
| ----------------------- | --------------- | --------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| **0.5**           | **0.10**  | **0.15**  | **0.35**   | **0.45**   | **0.70**   | **1.00**   | **1.30**   | **1.40**   | **1.70**   | **2.10**   | **3.00**   | **4.00**   |
| **0.6**           | **0.15**  | **0.20**  | **0.45**   | **0.60**   | **0.90**   | **1.40**   | **1.80**   | **1.90**   | **2.50**   | **3.30**   | **4.00**   | **5.50**   |
| **0.7**           | **0.23**  | **0.28**  | **0.60**   | **0.80**   | **1.10**   | **1.70**   | **2.30**   | **2.50**   | **3.40**   | **4.20**   | **5.20**   | **7.50**   |
| **0.8**           | **0.30**  | **0.35**  | **0.80**   | **1.00**   | **1.40**   | **2.20**   | **3.00**   | **3.30**   | **4.50**   | **5.50**   | **7.00**   | **9.50**   |
| **0.9**           | **0.38**  | **0.45**  | **0.95**   | **1.30**   | **1.70**   | **2.80**   | **3.80**   | **4.00**   | **5.60**   | **7.00**   | **8.80**   | **12.00**  |
| **1.0**           | **0.45**  | **0.55**  | **1.10**   | **1.60**   | **2.20**   | **3.50**   | **4.50**   | **4.80**   | **6.90**   | **8.50**   | **11.00**  | **15.00**  |
| **1.1**           | **0.55**  | **0.70**  | **1.50**   | **2.00**   | **2.80**   | **4.10**   | **5.50**   | **5.80**   | **8.10**   | **10.00**  | **13.00**  | **18.00**  |
| **1.2**           | **0.65**  | **0.85**  | **2.00**   | **2.40**   | **3.30**   | **5.00**   | **6.50**   | **7.00**   | **9.50**   | **12.00**  | **15.00**  | **22.00**  |
| **1.3**           | **0.80**  | **1.00**  | **2.20**   | **2.85**   | **3.80**   | **6.00**   | **7.50**   | **8.00**   | **11.20**  | **13.50**  | **17.00**  | **26.00**  |
| **1.4**           | **0.95**  | **1.20**  | **2.50**   | **3.30**   | **4.50**   | **7.00**   | **9.00**   | **9.90**   | **13.50**  | **16.00**  | **20.00**  | **30.00**  |
| **1.5**           | **1.10**  | **1.40**  | **3.00**   | **4.00**   | **5.50**   | **9.00**   | **11.00**  | **12.00**  | **15.50**  | **18.00**  | **24.00**  | **37.00**  |
| **1.6**           | **1.30**  | **1.60**  | **3.50**   | **4.80**   | **6.50**   | **12.00**  | **14.00**  | **15.00**  | **18.00**  | **22.00**  | **30.00**  | **45.00**  |
| **1.7**           | **1.60**  | **2.00**  | **4.00**   | **5.50**   | **7.00**   | **15.00**  | **17.00**  | **18.00**  | **22.00**  | **28.00**  | **38.00**  | **55.00**  |

#### 3.2.2. Aço H110-27

##### 3.2.2.1. Tabela de Perdas Específicas do Núcleo (W/kg)

**Valores de perdas específicas (W/kg) em função da indução magnética (T) e frequência (Hz). Estes dados são armazenados em** **perdas_nucleo_data_H110_27**.

| **Indução (T)** | **50 Hz** | **60 Hz** |
| --------------- | --------- | --------- |
| **0.2**         | **0.018** | **0.023** |
| **0.3**         | **0.038** | **0.050** |
| **0.4**         | **0.065** | **0.086** |
| **0.5**         | **0.097** | **0.128** |
| **0.6**         | **0.135** | **0.178** |
| **0.7**         | **0.178** | **0.236** |
| **0.8**         | **0.228** | **0.301** |
| **0.9**         | **0.284** | **0.377** |
| **1.0**         | **0.346** | **0.459** |
| **1.1**         | **0.414** | **0.549** |
| **1.2**         | **0.488** | **0.648** |
| **1.3**         | **0.569** | **0.755** |
| **1.4**         | **0.658** | **0.873** |
| **1.5**         | **0.760** | **1.006** |
| **1.6**         | **0.882** | **1.165** |
| **1.7**         | **1.052** | **1.383** |
| **1.8**         | **1.398** | **1.816** |
| **1.9**         | **2.010** | **2.595** |

**Nota: Para o aço H110-27, os dados estão disponíveis apenas para as frequências de 50 Hz e 60 Hz.**

##### 3.2.2.2. Tabela de Potência Magnetizante Específica (VA/kg)

**Valores de potência magnetizante específica (VA/kg) em função da indução magnética (T) e frequência (Hz). Estes dados são armazenados em** **potencia_magnet_data_H110_27**.

| **Indução (T)** | **50 Hz** | **60 Hz** |
| --------------- | --------- | --------- |
| **0.2**         | **0.032** | **0.040** |
| **0.3**         | **0.064** | **0.081** |
| **0.4**         | **0.103** | **0.130** |
| **0.5**         | **0.147** | **0.186** |
| **0.6**         | **0.196** | **0.249** |
| **0.7**         | **0.250** | **0.319** |
| **0.8**         | **0.308** | **0.395** |
| **0.9**         | **0.372** | **0.477** |
| **1.0**         | **0.441** | **0.568** |
| **1.1**         | **0.517** | **0.667** |
| **1.2**         | **0.602** | **0.777** |
| **1.3**         | **0.698** | **0.900** |
| **1.4**         | **0.812** | **1.045** |
| **1.5**         | **0.962** | **1.230** |
| **1.6**         | **1.188** | **1.507** |
| **1.7**         | **1.661** | **2.070** |
| **1.8**         | **3.438** | **4.178** |
| **1.9**         | **14.434**| **17.589**|

**Nota: Para o aço H110-27, os dados estão disponíveis apenas para as frequências de 50 Hz e 60 Hz.**

### 3.3. Variáveis Calculadas para Perdas em Vazio

**Constante:** **sqrt_3 = math.sqrt(3)** **(para trifásicos, 1.0 para monofásicos, usado como** **sqrt_3_factor** **no código).**

#### 3.3.1. Fatores de Correção para Aço H110-27

Ao utilizar os dados do aço H110-27, os seguintes fatores de correção devem ser aplicados:

* **Fator de Construção (Build Factor - BF):** Este fator compensa as perdas adicionais devido ao corte das chapas e à distribuição do fluxo nos cantos.
  * **Fator para perdas (W/kg):** **1.15** - Multiplicar os valores de perdas específicas por 1.15
  * **Fator para potência magnetizante (VA/kg):** **1.2** - Multiplicar os valores de VA/kg por 1.2

* **Divisor para Potência Magnetizante:** Na implementação em callbacks/losses.py, o fator de potência magnetizante (VAR/kg) para o aço H110-27 deve ser dividido por **1000** (não por 1.000.000 como em algumas implementações anteriores).

* **Implementação no Código:** No arquivo callbacks/losses.py, os fatores são aplicados da seguinte forma:

```python
# Aplicar fatores construtivos
fator_perdas_H110_27 = fator_perdas_H110_27_base * 1.15 if fator_perdas_H110_27_base is not None else None
fator_potencia_mag_H110_27 = fator_potencia_mag_H110_27_base * 1.2 if fator_potencia_mag_H110_27_base is not None else None

# Cálculo da potência magnética
# 1. Multiplicar por peso_nucleo_calc_h110_27 em toneladas
# 2. Multiplicar por 1000 para converter toneladas para kg
# 3. Dividir por 1000 para converter VA para kVA (ou VAR para kVAR)
potencia_mag_h110_27 = (fator_potencia_mag_H110_27 * peso_nucleo_calc_h110_27 * 1000) / 1000 if h110_27_valid else 0  # kVAR
```

* **Observações Importantes:**
  * Os fatores de construção (1.15 para perdas e 1.2 para potência magnetizante) devem ser sempre aplicados aos valores base do aço H110-27.
  * Estes fatores compensam as perdas nas bordas por perda de propriedade em função do corte e distribuição de fluxo nas quinas.
  * Ao comparar resultados entre diferentes tipos de aço, certifique-se de que os fatores de correção foram aplicados corretamente.

#### 3.3.2. Cálculos Baseados em Aço M4 (Estimativa)

* **perdas_vazio** **(kW):** **safe_float(perdas_vazio_ui, 0.0)**
* **inducao** **(T):** **safe_float(inducao_ui, 0.0)**
* **inducao_arredondada** **(T):** **round(inducao * 10) / 10**
* **frequencia_arredondada** **(Hz): Frequência da tabela mais próxima de** **frequencia**.
* **lookup_key**: **(inducao_arredondada, frequencia_arredondada)**
* **fator_perdas** **(W/kg): Valor de** **df_perdas_nucleo** **para** **lookup_key**.
* **fator_potencia_mag** **(VAR/kg): Valor de** **df_potencia_magnet** **para** **lookup_key**.
* **peso_nucleo_calc** **(Ton):** **perdas_vazio / fator_perdas**. (Se **perdas_vazio** **é kW e** **fator_perdas** **W/kg, esta fórmula resulta em kTon. Para Ton, seria** **(perdas_vazio * 1000) / fator_perdas / 1000**). **O código usa esta fórmula, implicando que** **fator_perdas** **é tratado como kW/Ton neste contexto ou as unidades da tabela são interpretadas como tal para este cálculo específico.**
* **potencia_mag** **(kVAR):** **fator_potencia_mag * peso_nucleo_calc**. (Se **fator_potencia_mag** **é VAR/kg e** **peso_nucleo_calc** **é Ton, então** **potencia_mag** **[kVAR] =** **fator_potencia_mag** ***** **peso_nucleo_calc** *** 1000 [** kg/Ton **] / 1000 [VAR/kVAR] =** **fator_potencia_mag** ***** **peso_nucleo_calc**).
* **corrente_excitacao_calc** **(A):** **potencia_mag / (tensao_bt_kv * sqrt_3)**
* **corrente_excitacao_percentual_calc** **(%):** **(corrente_excitacao_calc / corrente_nominal_bt) * 100**
* **tensao_teste_1_1_kv** **(kV):** **tensao_bt_kv * 1.1**
* **tensao_teste_1_2_kv** **(kV):** **tensao_bt_kv * 1.2**
* **corrente_excitacao_1_1_calc** **(A):** **2 * corrente_excitacao_calc**
* **corrente_excitacao_1_2_calc** **(A):** **4 * corrente_excitacao_calc**
* **potencia_ensaio_1pu_calc_kva** **(kVA):** **tensao_bt_kv * corrente_excitacao_calc * sqrt_3**
* **potencia_ensaio_1_1pu_calc_kva** **(kVA):** **tensao_teste_1_1_kv * corrente_excitacao_1_1_calc * sqrt_3**
* **potencia_ensaio_1_2pu_calc_kva** **(kVA):** **tensao_teste_1_2_kv * corrente_excitacao_1_2_calc * sqrt_3**

#### 3.3.2. Cálculos Baseados em Dados de Projeto

* **perdas_vazio** **(kW):** **safe_float(perdas_vazio_ui, 0.0)**
* **peso_nucleo** **(Ton):** **safe_float(peso_nucleo_ui, 0.0)**
* **corrente_excitacao_percentual** **(%):** **safe_float(corrente_excitacao_ui, 0.0)**
* **corrente_exc_1_1_input** **(%):** **safe_float(corrente_exc_1_1_ui)**
* **corrente_exc_1_2_input** **(%):** **safe_float(corrente_exc_1_2_ui)**
* **fator_perdas_projeto** **(kW/Ton):** **perdas_vazio / peso_nucleo**. Para W/kg: **(perdas_vazio * 1000) / (peso_nucleo * 1000)**.
* **corrente_excitacao_projeto** **(A):** **corrente_nominal_bt * (corrente_excitacao_percentual / 100.0)**
* **potencia_ensaio_1pu_projeto_kva** **(kVA):** **tensao_bt_kv * corrente_excitacao_projeto * sqrt_3**
* **potencia_mag_projeto_kvar** **(kVAR):** **potencia_ensaio_1pu_projeto_kva**
* **fator_potencia_mag_projeto** **(VAR/kg):** **(potencia_mag_projeto_kvar * 1000) / (peso_nucleo * 1000)**
* **fator_excitacao_default**: 3 (Trifásico) ou 5 (Monofásico).
* **corrente_excitacao_1_1** **(A): Se** **corrente_exc_1_1_input** **não nulo,** **corrente_nominal_bt * (corrente_exc_1_1_input / 100.0)**. Senão, **fator_excitacao_default * corrente_excitacao_projeto**.
* **corrente_excitacao_1_2** **(A): Se** **corrente_exc_1_2_input** **não nulo,** **corrente_nominal_bt * (corrente_exc_1_2_input / 100.0)**. Senão, **None**.
* **potencia_ensaio_1_1pu_projeto_kva** **(kVA):** **tensao_teste_1_1_kv * corrente_excitacao_1_1 * sqrt_3**
* **potencia_ensaio_1_2pu_projeto_kva** **(kVA): Se** **corrente_excitacao_1_2** **não nulo,** **tensao_teste_1_2_kv * corrente_excitacao_1_2 * sqrt_3**.

### 3.4. Análise SUT/EPS para Perdas em Vazio (Valores de Projeto)

 **Para níveis pu de 1.0, 1.1, 1.2 do DUT, usando tensões (**V_teste_dut_lv_kv**) e correntes (**I_exc_dut_lv**) de** **projeto**:

* **V_target_sut_hv** **(V):** **V_teste_dut_lv_kv * 1000**.
* **taps_sut_hv** **(V): Array de** **SUT_AT_MIN_VOLTAGE** **a** **SUT_AT_MAX_VOLTAGE** **com passo** **SUT_AT_STEP_VOLTAGE**.
* **Top 5 taps do SUT (**V_sut_hv_tap **em V) mais próximos e adequados a** **V_target_sut_hv**.
* **Para cada** **V_sut_hv_tap**:

  * **ratio_sut**: **V_sut_hv_tap / SUT_BT_VOLTAGE**
  * **I_sut_lv** **(A) (Corrente no EPS):** **I_exc_dut_lv * ratio_sut**
  * **percent_limite** **(%):** **(I_sut_lv / EPS_CURRENT_LIMIT) * 100**

### 3.5. Exemplo Numérico Detalhado de Perdas em Vazio

**Dados de Entrada (UI e Transformador):**

* **perdas_vazio_ui**: 10 kW
* **peso_nucleo_ui**: 5 Ton
* **corrente_excitacao_ui**: 0.5 %
* **inducao_ui**: 1.6 T
* **corrente_exc_1_1_ui**: 1.0 %
* **corrente_exc_1_2_ui**: 2.5 % (Exemplo, se fornecido)
* **frequencia**: 60 Hz
* **tensao_bt_kv** **(DUT): 13.8 kV**
* **corrente_nominal_bt** **(DUT): 418 A**
* **tipo_transformador**: Trifásico (**sqrt_3** **= 1.732)**
* **SUT_BT_VOLTAGE**: 480 V = 0.48 kV
* **EPS_CURRENT_LIMIT**: 2000 A

**Cálculos Baseados em Aço M4:**

* **perdas_vazio** **= 10 kW**
* **inducao** **= 1.6 T**
* **inducao_arredondada** **= 1.6 T**
* **frequencia_arredondada** **= 60 Hz**
* **lookup_key** **= (1.6, 60)**
* **fator_perdas** **(da tabela** **perdas_nucleo_data** **para 1.6T @ 60Hz) = 1.30 W/kg**
* **fator_potencia_mag** **(da tabela** **potencia_magnet_data** **para 1.6T @ 60Hz) = 1.60 VAR/kg**
* **peso_nucleo_calc** **= 10 kW / 1.30 W/kg = 10000 W / 1.30 W/kg = 7692.31 kg = 7.692 Ton**
* **potencia_mag** **= 1.60 VAR/kg * 7692.31 kg = 12307.69 VAR = 12.31 kVAR**
* **corrente_excitacao_calc** **= 12.31 kVAR / (13.8 kV * 1.732) = 12.31 / 23.9016 = 0.515 A**
* **corrente_excitacao_percentual_calc** **= (0.515 A / 418 A) * 100 = 0.123 %**
* **tensao_teste_1_1_kv** **= 13.8 kV * 1.1 = 15.18 kV**
* **tensao_teste_1_2_kv** **= 13.8 kV * 1.2 = 16.56 kV**
* **corrente_excitacao_1_1_calc** **= 2 * 0.515 A = 1.03 A**
* **corrente_excitacao_1_2_calc** **= 4 * 0.515 A = 2.06 A**
* **potencia_ensaio_1pu_calc_kva** **= 13.8 kV * 0.515 A * 1.732 = 12.31 kVA**
* **potencia_ensaio_1_1pu_calc_kva** **= 15.18 kV * 1.03 A * 1.732 = 27.08 kVA**
* **potencia_ensaio_1_2pu_calc_kva** **= 16.56 kV * 2.06 A * 1.732 = 59.12 kVA**

**Cálculos Baseados em Dados de Projeto:**

* **perdas_vazio** **= 10 kW**
* **peso_nucleo** **= 5 Ton**
* **corrente_excitacao_percentual** **= 0.5 %**
* **corrente_exc_1_1_input** **= 1.0 %**
* **corrente_exc_1_2_input** **= 2.5 %**
* **fator_perdas_projeto** **= (10 kW * 1000) / (5 Ton * 1000) = 2.0 W/kg (ou 10kW/5Ton = 2 kW/Ton)**
* **corrente_excitacao_projeto** **= 418 A * (0.5 / 100.0) = 2.09 A**
* **potencia_ensaio_1pu_projeto_kva** **= 13.8 kV * 2.09 A * 1.732 = 49.87 kVA**
* **potencia_mag_projeto_kvar** **= 49.87 kVAR**
* **fator_potencia_mag_projeto** **= (49.87 kVAR * 1000) / (5 Ton * 1000) = 9.974 VAR/kg**
* **fator_excitacao_default** **= 3**
* **corrente_excitacao_1_1** **= 418 A * (1.0 / 100.0) = 4.18 A (pois** **corrente_exc_1_1_input** **foi fornecido)**
* **corrente_excitacao_1_2** **= 418 A * (2.5 / 100.0) = 10.45 A (pois** **corrente_exc_1_2_input** **foi fornecido)**
* **potencia_ensaio_1_1pu_projeto_kva** **= 15.18 kV * 4.18 A * 1.732 = 109.93 kVA**
* **potencia_ensaio_1_2pu_projeto_kva** **= 16.56 kV * 10.45 A * 1.732 = 299.71 kVA**

**Análise SUT/EPS para 1.0 pu do DUT (Projeto):**

* **V_teste_dut_lv_kv** **= 13.8 kV**
* **I_exc_dut_lv** **= 2.09 A**
* **V_target_sut_hv** **= 13800 V**
* **taps_sut_hv** **(V): [14000, 17000, 20000, ...]**
* **Tap SUT mais próximo e adequado: 14000 V (**V_sut_hv_tap **= 14000 V)**

  * **ratio_sut** **= 14000 V / 480 V = 29.167**
  * **I_sut_lv** **= 2.09 A * 29.167 = 61.06 A**
  * **percent_limite** **= (61.06 A / 2000 A) * 100 = 3.05 %**
* **Outro Tap SUT (ex: 20000 V):**

  * **ratio_sut** **= 20000 V / 480 V = 41.667**
  * **I_sut_lv** **= 2.09 A * 41.667 = 87.08 A**
  * **percent_limite** **= (87.08 A / 2000 A) * 100 = 4.35 %**

---

## 4. Perdas em Carga (Load Losses)

**Cálculos das perdas nos enrolamentos do DUT sob carga.**

### 4.1. Parâmetros de Entrada

| **Parâmetro**                                     | **Descrição**                              | **Unidade** | **Variável Python (**losses.py**)** |
| -------------------------------------------------------- | -------------------------------------------------- | ----------------- | ------------------------------------------------ |
| **p**erdas_carga_nom_ui                                 | Perdas totais em carga no tap Nominal @ Tref       | kW                | perdas_totais_nom_input                          |
| perdas_carga_min_ui                                      | Perdas totais em carga no tap Menor @ Tref         | kW                | perdas_totais_min_input                          |
| perdas_carga_max_ui                                      | Perdas totais em carga no tap Maior @ Tref         | kW                | perdas_totais_max_input                          |
| temperatura_referencia_ui                                | Temperatura de referência para as perdas em carga | °C               | temperatura_ref                                  |
| perdas_vazio_nom                                         | Perdas em vazio nominais (do cálculo anterior)    | kW                | perdas_vazio_nom                                 |
| potencia (DUT)                                           | Potência nominal do DUT                           | MVA               | potencia                                         |
| tensao_nominal_at (DUT)                                  | Tensão nominal AT do DUT (Tap Nominal)            | kV                | tensao_nominal_at                                |
| ... (demais tensões e impedâncias dos taps do DUT) ... |                                                    |                   |                                                  |
| corrente_at_nom/min/max (DUT)                            | Correntes AT nominais para os taps                 | A                 | corrente_at_nom, etc.                            |

### 4.2. Cenários de Cálculo

**Realizados para taps Nominal, Menor, Maior do DUT:**

* **Energização a Frio (Total)**
* **Condição a Quente (Perdas Carga @ Tref)**
* **Condição a 25°C (Perdas Carga @ 25°C)**
* **Sobrecarga 1.2 pu / 1.4 pu** **(se** **tensao_nominal_at >= 230kV**)

### 4.3. Variáveis Calculadas (Por Tap DUT e Por Cenário de Ensaio)

**Para um tap DUT com** **tensao** **(kV),** **corrente** **(A),** **imp** **(%):**

* **vcc** **(kV) (Tensão de CC do tap):** **tensao * (imp / 100.0)**
* **perdas_carga_sem_vazio** **(kW @** **temperatura_ref**): **perdas_totais_input_tap - perdas_vazio_nom**
* **temp_factor**: **(235.0 + 25.0) / (235.0 + temperatura_ref)**
* **perdas_cc_a_frio** **(kW @ 25°C):** **perdas_carga_sem_vazio * temp_factor**

**Para cada cenário de ensaio (Frio, Quente, 25C, Sobrecarga):**

* **Cálculo de** **tensao_ensaio**, **corrente_ensaio** **(no DUT).**
* **pteste_..._kva** **(kVA):** **tensao_ensaio * corrente_ensaio * sqrt_3_factor**
* **pteste_..._mva** **(MVA):** **pteste_..._kva / 1000.0**
* **potencia_ativa_eps_..._kw** **(kW): Potência ativa que o EPS deve fornecer ao DUT.**

  * **Energização a Frio:** **perdas_totais_input_tap**
  * **Condição a Quente:** **perdas_carga_sem_vazio**
  * **Condição a 25°C:** **perdas_cc_a_frio**
  * **Sobrecarga (e.g., 1.2pu):** **perdas_carga_sem_vazio * (1.2^2)**
* **pteste_..._mvar** **(MVAr) (Reativo do DUT):** **sqrt(max(0, pteste_..._kva^2 - potencia_ativa_eps_..._kw^2)) / 1000.0**

### 4.4. Cálculo do Banco de Capacitores **Requerido** **(**calculate_cap_bank**)**

* **Entradas:** **voltage** **(kV, e.g.,** **tensao_frio**), **power** **(MVA, e.g.,** **pteste_frio_mva** **- potência aparente do DUT no ensaio).**
* **Saídas (para C/F e S/F):** **cap_bank_voltage_..._fator** **(kV, tensão nominal do banco selecionado) e** **pot_cap_bank_..._fator** **(MVAr, potência nominal que este banco precisaria ter para compensar a potência reativa do DUT na tensão de ensaio).**
* **A função** **calculate_cap_bank** **internamente deveria usar a componente reativa** **pteste_..._mvar** **(e não a aparente** **pteste_..._mva**) como base para **power_f** **para dimensionar o banco para compensação reativa.** **O código atual passa** **pteste_..._mva** **(aparente).**

  * **Fórmula se** **power_f** **fosse**

    ```
    QDUT
    ```

    : **Q_requerida_banco_nominal = Q_{DUT} / ( (V_{ensaio} / V_{banco_nominal})^2 * Cap_Correct_factor )**
  * **Onde** **Cap_Correct_factor** **é 1.0 nesta função.**

### 4.5. Configuração do Banco de Capacitores (Disponível/Sugerido)

**Detalhado na Seção 5. Para cada cenário, após calcular o** **Q Power Provided ... (MVAr)** **(potência efetiva do banco configurado), este valor é usado na compensação.**

### 4.6. Análise SUT/EPS para Perdas em Carga (Corrente Compensada)

**Função** **calculate_sut_eps_current_compensated**:

* **Entradas:**

  * **tensao_ref_dut_kv**: e.g., **tensao_frio**
  * **corrente_ref_dut_a**: e.g., **corrente_frio** **(corrente total do DUT no ensaio)**
  * **q_power_scenario_sf/cf_mvar**: Potência **fornecida** **pelo banco S/F ou C/F (e.g.,** **Q Power Provided Frio S/F (MVAr)**), na sua tensão nominal.
  * **cap_bank_voltage_scenario_sf/cf_kv**: Tensão **nominal** **do banco S/F ou C/F.**
  * **... (outros parâmetros SUT).**
* **Cálculos (exemplo para S/F):**

  * **ratio_sut** **=** **V_sut_hv_tap_v / tensao_sut_bt_v**.
  * **I_dut_reflected** **(A) =** **corrente_ref_dut_a * ratio_sut** **(Corrente** **total** **do DUT refletida para BT SUT).**
  * **Cap_Correct_factor_sf**: 0.25 (banco 13.8/23.9kV), 0.75 (banco 41.4/71.7kV), 1.0 (outros). Para C/F, sempre 1.0.
  * **pteste_mvar_corrected_sf** **(MVAr):**

    ```
    Qbanco_efetiva=Qbanco_fornecida_nominal×(Vbanco_nominalVensaio_DUT)2×Cap_Correct_factor_sf
    ```
  * **I_cap_base_sf** **(A) (Corrente capacitiva no lado DUT):**

    ```
    (Qbanco_efetiva×1000)/(Vensaio_DUT×3)
    ```
  * **I_cap_adjustment_sf** **(A) (Corrente capacitiva refletida para BT SUT):** **I_cap_base_sf * ratio_sut**
  * **I_eps_sf_net** **(A) (Corrente no EPS):** **I_dut_reflected - I_cap_adjustment_sf**. **Esta é uma subtração escalar direta, o que implica que** **I_dut_reflected** **é tratada como puramente reativa ou que as fases são tais que a subtração escalar é uma aproximação válida. Uma análise vetorial completa seria**

    <pre _ngcontent-ng-c1554618750=""><strong _ngcontent-ng-c2459883256="" class="ng-star-inserted"><code _ngcontent-ng-c1554618750="" class="rendered"><span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>I</mi><mrow><mi>n</mi><mi>e</mi><mi>t</mi></mrow></msub><mo>=</mo><msqrt><mrow><msubsup><mi>I</mi><mrow><mi>P</mi><mi>a</mi></mrow><mn>2</mn></msubsup><mo>+</mo><mo stretchy="false">(</mo><msub><mi>I</mi><mrow><mi>P</mi><mi>r</mi></mrow></msub><mo>−</mo><msub><mi>I</mi><mrow><mi>c</mi><mi>a</mi><mi>p</mi><mi mathvariant="normal">_</mi><mi>a</mi><mi>d</mi><mi>j</mi></mrow></msub><msup><mo stretchy="false">)</mo><mn>2</mn></msup></mrow></msqrt></mrow></semantics></math></span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut"></span><span class="mord"><span class="mord mathnormal">I</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">n</span><span class="mord mathnormal mtight">e</span><span class="mord mathnormal mtight">t</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span><span class="mspace"></span><span class="mrel">=</span><span class="mspace"></span></span><span class="base"><span class="strut"></span><span class="mord sqrt"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class="svg-align"><span class="pstrut"></span><span class="mord"><span class="mord"><span class="mord mathnormal">I</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">P</span><span class="mord mathnormal mtight">a</span></span></span></span><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight">2</span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span><span class="mspace"></span><span class="mbin">+</span><span class="mspace"></span><span class="mopen">(</span><span class="mord"><span class="mord mathnormal">I</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">P</span><span class="mord mathnormal mtight">r</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span><span class="mspace"></span><span class="mbin">−</span><span class="mspace"></span><span class="mord"><span class="mord mathnormal">I</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">c</span><span class="mord mathnormal mtight">a</span><span class="mord mathnormal mtight">p</span><span class="mord mtight">_</span><span class="mord mathnormal mtight">a</span><span class="mord mathnormal mtight">d</span><span class="mord mathnormal mtight">j</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span><span class="mclose"><span class="mclose">)</span><span class="msupsub"><span class="vlist-t"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight">2</span></span></span></span></span></span></span></span></span></span><span class=""><span class="pstrut"></span><span class="hide-tail"><svg width="400em" height="1.88em" viewBox="0 0 400000 1944" preserveAspectRatio="xMinYMin slice"><path d="M983 90
    l0 -0
    c4,-6.7,10,-10,18,-10 H400000v40
    H1013.1s-83.4,268,-264.1,840c-180.7,572,-277,876.3,-289,913c-4.7,4.7,-12.7,7,-24,7
    s-12,0,-12,0c-1.3,-3.3,-3.7,-11.7,-7,-25c-35.3,-125.3,-106.7,-373.3,-214,-744
    c-10,12,-21,25,-33,39s-32,39,-32,39c-6,-5.3,-15,-14,-27,-26s25,-30,25,-30
    c26.7,-32.7,52,-63,76,-91s52,-60,52,-60s208,722,208,722
    c56,-175.3,126.3,-397.3,211,-666c84.7,-268.7,153.8,-488.2,207.5,-658.5
    c53.7,-170.3,84.5,-266.8,92.5,-289.5z
    M1001 80h400000v40h-400000z"></path></svg></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span></span></span></code></strong></pre>

    **, onde

    ```
    IPa
    ```

    **e**

    ```
    IPr
    ```

    **são as componentes da** **I_dut_reflected**.**
  * **percent_limite_sf** **(%):** **(abs(I_eps_sf_net) / EPS_CURRENT_LIMIT) * 100**.

### 4.7. Exemplo Numérico Detalhado de Perdas em Carga

**Dados Iniciais:**

* **DUT Trifásico: Potência = 10 MVA, Tensão AT (Nominal) = 69 kV, Taps AT: Menor 65kV, Maior 72kV.**
* **Impedâncias (%): Nominal 8%, Menor 7.5%, Maior 8.5%.**
* **Entrada UI:** **perdas_carga_nom_ui**=80kW, **perdas_carga_min_ui**=75kW, **perdas_carga_max_ui**=85kW. **temperatura_referencia_ui**=85°C.
* **Calculado:** **perdas_vazio_nom** **= 12 kW.**
* **SUT:** **SUT_BT_VOLTAGE**=480V. **EPS_CURRENT_LIMIT**=2000A.

**Cálculos para TAP NOMINAL (69 kV):**

* **tensao**=69kV, **imp**=8%, **perdas_totais_input_tap**=80kW.
* **corrente_at_nom** **= (10000 kVA) / (69 kV * 1.732) = 83.67 A.**
* **vcc** **= 69 kV * (8/100) = 5.52 kV.**
* **perdas_carga_sem_vazio** **(@85°C) = 80 kW - 12 kW = 68 kW.**
* **temp_factor** **= (235+25) / (235+85) = 260 / 320 = 0.8125.**
* **perdas_cc_a_frio** **(@25°C) = 68 kW * 0.8125 = 55.25 kW.**

**Cenário: Energização a Frio (Tap Nominal DUT):**

* **frio_ratio_sqrt** **= sqrt(80 kW / 55.25 kW) = sqrt(1.4479) = 1.2033.**
* **tensao_frio** **= 1.2033 * 5.52 kV = 6.642 kV (Tensão ensaio DUT).**
* **corrente_frio** **= 1.2033 * 83.67 A = 100.68 A (Corrente ensaio DUT).**
* **pteste_frio_kva** **= 6.642 kV * 100.68 A * 1.732 = 1158.2 kVA.**
* **pteste_frio_mva** **= 1.1582 MVA.**
* **potencia_ativa_eps_frio_kw** **= 80 kW.**
* **pteste_frio_mvar** **= sqrt(1158.2^2 - 80^2)/1000 = sqrt(1341427 - 6400)/1000 = 1.1554 MVAr (Reativo DUT).**

**Banco de Capacitores** **Requerido** **(Cenário Frio, C/F, Tap Nominal):**

* **voltage** **= 6.642 kV (ensaio DUT).**
* **Usando**

  <pre _ngcontent-ng-c1554618750=""><strong _ngcontent-ng-c2459883256="" class="ng-star-inserted"><code _ngcontent-ng-c1554618750="" class="rendered"><span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow><msub><mi>Q</mi><mrow><mi>D</mi><mi>U</mi><mi>T</mi></mrow></msub></mrow></semantics></math></span><span class="katex-html" aria-hidden="true"><span class="base"><span class="strut"></span><span class="mord"><span class="mord mathnormal">Q</span><span class="msupsub"><span class="vlist-t vlist-t2"><span class="vlist-r"><span class="vlist"><span class=""><span class="pstrut"></span><span class="sizing reset-size6 size3 mtight"><span class="mord mtight"><span class="mord mathnormal mtight">D</span><span class="mord mathnormal mtight">U</span><span class="mord mathnormal mtight">T</span></span></span></span></span><span class="vlist-s"></span></span><span class="vlist-r"><span class="vlist"><span class=""></span></span></span></span></span></span></span></span></span></code></strong></pre>

  ** **para** **power** **(corrigido):**** **power_reativa_a_compensar** **= 1.1554 MVAr.**
* **select_target_bank_voltage(6.642)** **->** **target_v_cf_key**="13.8" (Assumindo 6.642 <= 13.8 * 1.1). **cap_bank_voltage_com_fator** **= 13.8 kV.**
* **pot_cap_bank_com_fator** **(MVAr requerido do banco) = 1.1554 / ((6.642 / 13.8)^2 * 1.0) = 1.1554 / 0.2319 = 4.982 MVAr.**

  * **Este é** **res_dict["Cap Bank Power Frio Com Fator (MVAr)"]**.

**Seleção Configuração Banco (Cenário Frio, C/F, Tap Nominal):**

* **target_bank_voltage_key** **= "13.8".** **required_power_mvar** **= 4.982 MVAr.**
* **Grupo 1 para 13.8kV: 3 unidades, máx 11.7 MVAr.** **use_group1_only** **= True.**
* **available_caps** **= 3 unidades (CP2A1, CP2B1, CP2C1).**
* **find_best_q_configuration("13.8", 4.982, True)**:

  * **Necessário ~1.66 MVAr/unidade (4.982 / 3).**
  * **Q5 (1.6 MVAr) é menor. Q4+Q1 (1.2+0.1=1.3) é menor. Q3+Q4 (0.8+1.2=2.0) é > 1.66.**
  * **Combinação "Q3, Q4" (2.0 MVAr/unidade).**
  * **Potência total fornecida pelo banco = 2.0 MVAr/unidade * 3 unidades = 6.0 MVAr.**
  * **res_dict["Q Config Frio"]** **= "Q3, Q4".**
  * **res_dict["Q Power Provided Frio (MVAr)"]** **= 6.0 MVAr.**
  * **res_dict["Cap Bank Voltage Frio Com Fator (kV)"]** **= 13.8 kV.**

**Análise SUT/EPS (Cenário Frio, C/F, Tap Nominal DUT, Tap SUT AT = 14kV):**

* **tensao_ref_dut_kv** **= 6.642 kV.**
* **corrente_ref_dut_a** **= 100.68 A.**
* **q_power_scenario_cf_mvar** **= 6.0 MVAr (Potência** **fornecida** **pelo banco 13.8kV).**
* **cap_bank_voltage_scenario_cf_kv** **= 13.8 kV (Tensão** **nominal** **do banco).**
* **V_sut_hv_tap_v** **= 14000 V.** **tensao_sut_bt_v** **= 480 V.**
* **Cap_Correct_factor_cf** **para** **calculate_sut_eps_current_compensated** **= 1.0.**
* **Cálculos:**

  * **ratio_sut** **= 14000 / 480 = 29.167.**
  * **I_dut_reflected** **= 100.68 A * 29.167 = 2936.5 A.**
  * **pteste_mvar_corrected_cf** **= 6.0 MVAr * ((6.642 / 13.8)^2 * 1.0) = 6.0 * 0.2319 = 1.391 MVAr.**
  * **I_cap_base_cf** **= (1.391 * 1000) / (6.642 * 1.732) = 120.85 A.**
  * **I_cap_adjustment_cf** **= 120.85 A * 29.167 = 3524.8 A.**
  * **I_eps_cf_net** **= 2936.5 A - 3524.8 A = -588.3 A.**
  * **percent_limite_cf** **= (588.3 / 2000) * 100 * (-1) = -29.4 % (Excesso de compensação).**

---

## 5. Configuração Detalhada dos Bancos de Capacitores

### 5.1. Capacitores Disponíveis por Nível de Tensão Nominal do Banco

**Conforme** **utils.constants.CAPACITORS_BY_VOLTAGE**:

| **Tensão Nominal Banco (kV)** | **Capacitores Físicos Disponíveis (**CAPACITORS_BY_VOLTAGE[chave]**)**                                                                                                                                     |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| "13.8"                               | ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2"]                                                                                                                                                                   |
| "23.9"                               | ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2"]                                                                                                                                                                   |
| "27.6"                               | ["CP1A1", "CP1A2", "CP1B1", "CP1B2", "CP1C1", "CP1C2", "CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"] |
| "41.4"                               | ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"]                                                       |
| "47.8"                               | ["CP1A1", "CP1A2", "CP1B1", "CP1B2", "CP1C1", "CP1C2", "CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"] |
| "55.2"                               | ["CP1A1", "CP1A2", "CP1B1", "CP1B2", "CP1C1", "CP1C2", "CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"] |
| "71.7"                               | ["CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"]                                                       |
| "95.6"                               | ["CP1A1", "CP1A2", "CP1B1", "CP1B2", "CP1C1", "CP1C2", "CP2A1", "CP2A2", "CP2B1", "CP2B2", "CP2C1", "CP2C2", "CP3A1", "CP3A2", "CP3B1", "CP3B2", "CP3C1", "CP3C2", "CP4A1", "CP4A2", "CP4B1", "CP4B2", "CP4C1", "CP4C2"] |

**Nomenclatura** **CPxAy**: **x**=posição (1-4), **A**=Fase (A,B,C), **y**=Grupo (1 ou 2).

### 5.2. Potência das Chaves Q por Unidade de Capacitor

**Conforme** **utils.constants.Q_SWITCH_POWERS["generic_cp"]**:

| **Chave** | **Potência (MVAr)** |
| --------------- | -------------------------- |
| Q1              | 0.1                        |
| Q2              | 0.2                        |
| Q3              | 0.8                        |
| Q4              | 1.2                        |
| Q5              | 1.6                        |
| Total (Q1-Q5)   | 3.9                        |

### 5.3. Lógica de Seleção Implementada

**A lógica em** **losses.py** **(**find_best_q_configuration**,** **suggest_capacitor_bank_config**) opera como descrito na Seção 2.5.2 e 2.5.3. A potência fornecida por uma combinação de chaves Q em um conjunto de **available_caps** **(unidades monofásicas) é** **sum(Q_potencias_individuais) * len(available_caps)**.


### 5.4. Potências Mínima e Máxima Teóricas por Nível de Tensão (Continuacão)

  **Estas são as potências trifásicas totais que podem ser obtidas, considerando o uso apenas do Grupo 1 de capacitores (CPxy**1**) ou de todos os capacitores disponíveis (Grupo 1 + Grupo 2, i.e., CPxy**1 **+ CPxy**2**), aplicando a mesma configuração de chaves Q (Q1 para mínima, Q1 a Q5 para máxima) em todas as unidades monofásicas selecionadas.**

* **13.8 kV** **(**CAPACITORS_BY_VOLTAGE["13.8"] **= 6 unidades no total, 3 unidades no Grupo 1)**
* **Grupo 1 Apenas (**len(available_caps)**=3):**

  * **Mínima (Q1): 0.1 MVAr/unid * 3 unid =** **0.3 MVAr**
  * **Máxima (Q1-Q5): 3.9 MVAr/unid * 3 unid =** **11.7 MVAr**
* **Grupo 1 + Grupo 2 (**len(available_caps)**=6):**

  * **Mínima (Q1): 0.1 MVAr/unid * 6 unid =** **0.6 MVAr**
  * **Máxima (Q1-Q5): 3.9 MVAr/unid * 6 unid =** **23.4 MVAr**
* **23.9 kV** **(**CAPACITORS_BY_VOLTAGE["23.9"] **= 6 unidades no total, 3 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=3):**

    * **Mínima (Q1): 0.1 MVAr/unid * 3 unid =** **0.3 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 3 unid =** **11.7 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=6):**

    * **Mínima (Q1): 0.1 MVAr/unid * 6 unid =** **0.6 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 6 unid =** **23.4 MVAr**
* **27.6 kV** **(**CAPACITORS_BY_VOLTAGE["27.6"] **= 24 unidades no total, 12 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=12):**

    * **Mínima (Q1): 0.1 MVAr/unid * 12 unid =** **1.2 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 12 unid =** **46.8 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=24):**

    * **Mínima (Q1): 0.1 MVAr/unid * 24 unid =** **2.4 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 24 unid =** **93.6 MVAr**
* **41.4 kV** **(**CAPACITORS_BY_VOLTAGE["41.4"] **= 18 unidades no total, 9 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=9):**

    * **Mínima (Q1): 0.1 MVAr/unid * 9 unid =** **0.9 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 9 unid =** **35.1 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=18):**

    * **Mínima (Q1): 0.1 MVAr/unid * 18 unid =** **1.8 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 18 unid =** **70.2 MVAr**
* **47.8 kV** **(**CAPACITORS_BY_VOLTAGE["47.8"] **= 24 unidades no total, 12 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=12):**

    * **Mínima (Q1): 0.1 MVAr/unid * 12 unid =** **1.2 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 12 unid =** **46.8 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=24):**

    * **Mínima (Q1): 0.1 MVAr/unid * 24 unid =** **2.4 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 24 unid =** **93.6 MVAr**
* **55.2 kV** **(**CAPACITORS_BY_VOLTAGE["55.2"] **= 24 unidades no total, 12 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=12):**

    * **Mínima (Q1): 0.1 MVAr/unid * 12 unid =** **1.2 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 12 unid =** **46.8 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=24):**

    * **Mínima (Q1): 0.1 MVAr/unid * 24 unid =** **2.4 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 24 unid =** **93.6 MVAr**
* **71.7 kV** **(**CAPACITORS_BY_VOLTAGE["71.7"] **= 18 unidades no total, 9 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=9):**

    * **Mínima (Q1): 0.1 MVAr/unid * 9 unid =** **0.9 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 9 unid =** **35.1 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=18):**

    * **Mínima (Q1): 0.1 MVAr/unid * 18 unid =** **1.8 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 18 unid =** **70.2 MVAr**
* **95.6 kV** **(**CAPACITORS_BY_VOLTAGE["95.6"] **= 24 unidades no total, 12 unidades no Grupo 1)**

  * **Grupo 1 Apenas (**len(available_caps)**=12):**

    * **Mínima (Q1): 0.1 MVAr/unid * 12 unid =** **1.2 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 12 unid =** **46.8 MVAr**
  * **Grupo 1 + Grupo 2 (**len(available_caps)**=24):**

    * **Mínima (Q1): 0.1 MVAr/unid * 24 unid =** **2.4 MVAr**
    * **Máxima (Q1-Q5): 3.9 MVAr/unid * 24 unid =** **93.6 MVAr**

**(Nota: "Unidade" refere-se a uma unidade monofásica de capacitor. Para um sistema trifásico,** **len(available_caps)** **será um múltiplo de 3 se os capacitores estiverem distribuídos igualmente entre as fases, como é o caso na constante** **CAPACITORS_BY_VOLTAGE**.)

### 5.5. Considerações para Seleção Avançada de Capacitores (Lógica Desejada vs. Implementada)

**A solicitação original incluía uma lógica mais complexa para seleção de capacitores, com apresentação de múltiplas opções (exata, acima, abaixo) e a possibilidade de configurações desequilibradas se aceito pelo usuário.**

**Lógica Desejada (Resumo da Solicitação):**

* **Receber potência desejada e nível de tensão.**
* **Verificar se a potência desejada está dentro do intervalo mínimo/máximo possível para o nível de tensão.**
* **Identificar os grupos de capacitores (Grupo 1: CPxy1; Grupo 1+2: CPxy1 + CPxy2).**
* **Priorizar Grupo 1:** **Se a potência desejada puder ser alcançada apenas com o Grupo 1, usar este grupo.**
* **Senão, usar Grupo 1+2.**
* **Método Equilibrado:**

  * **Gerar todas as 31 combinações de chaves Q.**
  * **Para cada combinação, calcular a potência total por unidade e multiplicar pelo número de unidades** **por fase** **(assumindo equilíbrio).**
  * **Ordenar as potências trifásicas resultantes.**
  * **Selecionar opções: Exata (se houver), melhor acima, melhor abaixo.**
* **Método Desequilibrado (Opcional):** **Se o método equilibrado não fornecer uma solução exata ou satisfatória, e o usuário permitir, considerar configurações onde diferentes unidades de capacitor (mesmo dentro da mesma fase, ou entre fases se o número de unidades por fase for diferente) podem ter diferentes combinações de Q. Isso é significativamente mais complexo.**
* **Apresentar opções ao usuário.**

**Comparação com a Lógica Implementada em** **losses.py**:

* **Verificação de Intervalo:** **Não é feita explicitamente no início;** **find_best_q_configuration** **retorna "N/A" se não encontrar solução.**
* **Priorização Grupo 1:** **Implementada através do parâmetro** **use_group1_only** **passado para** **find_best_q_configuration**.
* **Método Equilibrado:** **A função** **find_best_q_configuration** **aplica a** **mesma** **combinação de chaves Q a** **todas** **as** **available_caps** **selecionadas. Se** **available_caps** **representa um conjunto equilibrado de unidades por fase, o resultado é equilibrado.**
* **Seleção de Opções:** **Apenas a "melhor acima ou igual" é retornada. Não há opções "exata" ou "melhor abaixo" distintas.**
* **Método Desequilibrado:** **Não implementado.**

**A lógica atual é uma simplificação funcional do algoritmo mais detalhado solicitado. A implementação de um método desequilibrado e a apresentação de múltiplas opções exigiriam uma refatoração significativa das funções de busca e seleção de configuração do banco.**

---

## 6. Considerações Finais sobre Fórmulas e Implementação

* **Unidades:** **É crucial a consistência nas unidades (kW vs W, Ton vs kg, kV vs V) ao longo dos cálculos. O** **formulas_perdas.md** **tenta esclarecer as unidades usadas em cada etapa conforme interpretado do código.**
* **Compensação de Corrente (**calculate_sut_eps_current_compensated**):** **A subtração escalar direta da corrente do capacitor da corrente refletida do DUT é uma aproximação. Uma análise vetorial completa, considerando as componentes ativa e reativa da corrente do DUT, seria mais precisa, especialmente se o fator de potência do ensaio não for muito baixo.**
* **Dimensionamento do Banco (**calculate_cap_bank**):** **A função** **calculate_cap_bank** **recebe a potência** **aparente** **(**

  ```
  SDUT
  ```
  ) do ensaio no DUT como entrada **power**. Para dimensionar um banco para compensação **reativa**, a entrada **power** **para esta função deveria ser a potência** **reativa** **(**

  ```
  QDUT
  ```
  ) do ensaio (e.g., **pteste_frio_mvar**). O resultado (**pot_cap_bank_..._fator**) seria então a potência nominal reativa que o banco selecionado precisaria ter. O código atual, ao passar

  ```
  SDUT
  ```
  , pode estar calculando uma potência de banco nominal que compensaria a potência aparente total, o que não é o objetivo usual da compensação por bancos de capacitores. Esta é uma área potencial para revisão no código para garantir que o banco seja dimensionado para compensar

  ```
  QDUT
  ```
  .
