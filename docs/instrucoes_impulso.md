# Detalhamento dos Cálculos de Impulso 

Este documento detalha as fórmulas e parâmetros usados nos cálculos de impulso atmosférico (LI) e impulso cortado (LIC) para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de impulso:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`                 |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                          |
| Classe de Tensão AT           | Classe de tensão do lado de Alta Tensão| kV      | `classe_tensao_at`                   |
| Nível Básico de Isolamento    | Nível de isolamento (BIL)              | kV      | `bil`                                |
| Resistor Frontal              | Valor do resistor frontal              | Ω       | `resistor_frontal`                   |
| Resistor de Cauda             | Valor do resistor de cauda             | Ω       | `resistor_cauda`                     |
| Capacitância do Gerador       | Capacitância do gerador de impulso     | nF      | `capacitancia_gerador`               |
| Capacitância do Objeto        | Capacitância do objeto de teste        | pF      | `capacitancia_objeto`                |
| Indutância                    | Indutância do circuito                 | μH      | `indutancia`                         |
| Tempo de Corte                | Tempo de corte para impulso cortado    | μs      | `tempo_corte`                        |

## 2. Fundamentos Teóricos

### 2.1. Forma de Onda de Impulso Atmosférico

A forma de onda de impulso atmosférico é descrita pela equação:

* `V(t) = V₀ * (e^(-αt) - e^(-βt))`

Onde:
* `V(t)` é a tensão no tempo t
* `V₀` é a amplitude da tensão
* `α` e `β` são constantes que determinam os tempos de frente e cauda
* `t` é o tempo

### 2.2. Parâmetros da Forma de Onda

* **Tempo de Frente (T₁)**: Tempo para a onda atingir o valor de pico, normalmente 1.2 μs ± 30%
* **Tempo de Cauda (T₂)**: Tempo para a onda cair a 50% do valor de pico, normalmente 50 μs ± 20%
* **Eficiência (η)**: Razão entre a tensão de pico e a tensão de carga do gerador

## 3. Cálculos do Circuito de Impulso

### 3.1. Cálculo dos Parâmetros α e β

* `α = 1 / (R₂ * C₂)`
* `β = 1 / (R₁ * C₁)`

Onde:
* `R₁` é o resistor frontal
* `R₂` é o resistor de cauda
* `C₁` é a capacitância do gerador
* `C₂` é a capacitância do objeto de teste

### 3.2. Cálculo da Eficiência

* `η = (β - α) / β * e^(-αT₁)`

### 3.3. Cálculo da Tensão de Carga

* `V_carga = V_pico / η`

Onde:
* `V_pico` é a tensão de pico desejada (geralmente o BIL)
* `η` é a eficiência calculada

### 3.4. Cálculo da Energia do Impulso

* `E = 0.5 * C₁ * V_carga²`

Onde:
* `E` é a energia em Joules
* `C₁` é a capacitância do gerador em Farads
* `V_carga` é a tensão de carga em Volts

## 4. Impulso Cortado (LIC)

### 4.1. Tempo de Corte

O tempo de corte é o tempo após o início da onda em que ocorre o corte da tensão. Normalmente entre 2 e 6 μs.

### 4.2. Tensão de Corte

* `V_corte = V₀ * (e^(-α*t_corte) - e^(-β*t_corte))`

Onde:
* `V_corte` é a tensão no momento do corte
* `t_corte` é o tempo de corte

### 4.3. Sobretensão de Corte

Devido à indutância do circuito, pode ocorrer uma sobretensão no momento do corte:

* `V_sobretensao = V_corte * (1 + k)`

Onde:
* `k` é o fator de sobretensão, que depende da indutância e da impedância do circuito
