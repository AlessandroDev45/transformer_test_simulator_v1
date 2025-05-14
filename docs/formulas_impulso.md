# Detalhamento dos Cálculos de Impulso

Este documento detalha as fórmulas e parâmetros usados nos cálculos de impulso atmosférico (LI) e impulso cortado (LIC) para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de impulso:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                        |
| Classe de Tensão AT           | Classe de tensão do lado de Alta Tensão| kV      | `classe_tensao_at`                 |
| Nível Básico de Isolamento    | Nível de isolamento (BIL)              | kV      | `bil`                              |
| Resistor Frontal              | Valor do resistor frontal              | Ω       | `resistor_frontal`                 |
| Resistor de Cauda             | Valor do resistor de cauda             | Ω       | `resistor_cauda`                   |
| Capacitância do Gerador       | Capacitância do gerador de impulso     | nF      | `capacitancia_gerador`             |
| Capacitância do Objeto        | Capacitância do objeto de teste        | pF      | `capacitancia_objeto`              |
| Indutância                    | Indutância do circuito                 | μH      | `indutancia`                       |
| Tempo de Corte                | Tempo de corte para impulso cortado    | μs      | `tempo_corte`                      |

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

## 5. Simulação da Forma de Onda

### 5.1. Discretização do Tempo

Para simular a forma de onda, o tempo é discretizado em pequenos intervalos:

* `t = [0, Δt, 2Δt, ..., t_max]`

Onde:
* `Δt` é o passo de tempo (tipicamente 0.01 μs)
* `t_max` é o tempo máximo de simulação (tipicamente 100 μs)

### 5.2. Cálculo da Tensão em Cada Ponto

Para cada ponto de tempo `t[i]`:

* `V[i] = V₀ * (e^(-α*t[i]) - e^(-β*t[i]))` para `t[i] < t_corte` (impulso cortado)
* `V[i] = V_corte * (1 + k) * e^(-γ*(t[i]-t_corte))` para `t[i] ≥ t_corte` (impulso cortado)

Onde:
* `γ` é a constante de tempo da oscilação após o corte

## 6. Análise dos Resultados

### 6.1. Verificação dos Tempos T₁ e T₂

* **T₁ (Tempo de Frente)**: Deve estar entre 0.84 μs e 1.56 μs (1.2 μs ± 30%)
* **T₂ (Tempo de Cauda)**: Deve estar entre 40 μs e 60 μs (50 μs ± 20%)

### 6.2. Verificação da Eficiência

* A eficiência típica está entre 80% e 95%
* Eficiências muito baixas indicam um circuito mal dimensionado

### 6.3. Verificação da Energia

* A energia deve ser compatível com a capacidade do gerador de impulso
* Energias muito altas podem danificar o gerador

## 7. Recomendações para o Teste

### 7.1. Ajuste dos Parâmetros

* **Resistor Frontal (R₁)**: Afeta principalmente o tempo de frente
* **Resistor de Cauda (R₂)**: Afeta principalmente o tempo de cauda
* **Capacitância do Gerador (C₁)**: Afeta a energia disponível
* **Indutância (L)**: Afeta a sobretensão no corte

### 7.2. Procedimento de Teste

1. Iniciar com tensões reduzidas (50% do BIL)
2. Verificar a forma de onda
3. Ajustar os parâmetros se necessário
4. Aumentar gradualmente a tensão até o valor nominal (BIL)
5. Realizar o teste completo conforme a norma

---

## Notas Importantes

1. Os valores de BIL são determinados pelas normas técnicas e variam conforme a classe de tensão.
2. A forma de onda real pode diferir da simulação devido a efeitos não lineares e parasitas.
3. A indutância do circuito pode afetar significativamente a forma de onda, especialmente no caso de impulso cortado.
4. O teste de impulso é um teste destrutivo e deve ser realizado com cuidado para evitar danos ao transformador.
