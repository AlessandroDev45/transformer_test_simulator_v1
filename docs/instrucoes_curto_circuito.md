# Detalhamento dos Cálculos de Curto-Circuito

Este documento detalha as fórmulas e parâmetros usados nos cálculos de curto-circuito para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de curto-circuito:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               |
| Potência Nominal              | Potência nominal do transformador      | MVA     | `potencia_nominal`                 |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                        |
| Tensão Nominal BT             | Tensão nominal do lado de Baixa Tensão | kV      | `tensao_bt`                        |
| Impedância Percentual         | Impedância de curto-circuito           | %       | `impedancia_percentual`            |
| Potência de Curto-Circuito    | Potência de curto-circuito da rede     | MVA     | `potencia_cc_rede`                 |
| Fator X/R                     | Relação entre reatância e resistência  | -       | `fator_xr`                         |
| Duração do Curto-Circuito     | Tempo de duração do curto-circuito     | s       | `duracao_cc`                       |

## 2. Cálculos de Correntes de Curto-Circuito

### 2.1. Corrente Nominal

#### 2.1.1. Para Transformadores Monofásicos

* `I_nom_at = (S_nom * 1000) / V_at` (A)
* `I_nom_bt = (S_nom * 1000) / V_bt` (A)

#### 2.1.2. Para Transformadores Trifásicos

* `I_nom_at = (S_nom * 1000) / (√3 * V_at)` (A)
* `I_nom_bt = (S_nom * 1000) / (√3 * V_bt)` (A)

Onde:
* `I_nom_at` e `I_nom_bt` são as correntes nominais nos lados AT e BT
* `S_nom` é a potência nominal em MVA
* `V_at` e `V_bt` são as tensões nominais em kV

### 2.2. Impedância de Curto-Circuito

* `Z_pu = Z_percentual / 100`
* `Z_ohm_at = Z_pu * (V_at^2 * 1000) / S_nom` (Ω)
* `Z_ohm_bt = Z_pu * (V_bt^2 * 1000) / S_nom` (Ω)

Onde:
* `Z_pu` é a impedância em p.u.
* `Z_ohm_at` e `Z_ohm_bt` são as impedâncias em ohms referidas aos lados AT e BT

### 2.3. Corrente de Curto-Circuito Simétrica

#### 2.3.1. Considerando Apenas o Transformador

* `I_cc_at = I_nom_at / Z_pu` (A)
* `I_cc_bt = I_nom_bt / Z_pu` (A)

#### 2.3.2. Considerando a Rede

* `Z_rede_pu = S_nom / S_cc_rede`
* `Z_total_pu = Z_pu + Z_rede_pu`
* `I_cc_at_rede = I_nom_at / Z_total_pu` (A)
* `I_cc_bt_rede = I_nom_bt / Z_total_pu` (A)

Onde:
* `Z_rede_pu` é a impedância da rede em p.u.
* `S_cc_rede` é a potência de curto-circuito da rede em MVA

### 2.4. Corrente de Curto-Circuito Assimétrica

* `I_cc_assim = I_cc_sim * √(1 + 2*e^(-2*π*f*R/X*t))`

Onde:
* `I_cc_assim` é a corrente de curto-circuito assimétrica
* `I_cc_sim` é a corrente de curto-circuito simétrica
* `f` é a frequência em Hz
* `R/X` é o inverso do fator X/R
* `t` é o tempo em segundos

### 2.5. Corrente de Pico

* `I_pico = I_cc_sim * √2 * κ`
* `κ = 1.02 + 0.98 * e^(-3*R/X)`

Onde:
* `I_pico` é a corrente de pico
* `κ` é o fator de assimetria

## 3. Esforços Mecânicos

### 3.1. Força Axial

* `F_axial = (μ₀ * I₁ * I₂) / (2 * π * r) * L` (N)

Onde:
* `F_axial` é a força axial em Newtons
* `μ₀` é a permeabilidade do vácuo (4π × 10⁻⁷ H/m)
* `I₁` e `I₂` são as correntes nos enrolamentos em Amperes
* `r` é o raio médio entre os enrolamentos em metros
* `L` é o comprimento axial em metros

### 3.2. Força Radial

* `F_radial = (μ₀ * I₁² * N₁²) / (2 * π * r * h)` (N/m²)

Onde:
* `F_radial` é a força radial por unidade de área
* `N₁` é o número de espiras
* `h` é a altura do enrolamento

### 3.3. Tensão de Compressão Radial

* `σ_radial = F_radial * r / t` (N/m²)

Onde:
* `σ_radial` é a tensão de compressão radial
* `t` é a espessura do enrolamento

### 3.4. Tensão de Tração Circunferencial

* `σ_circ = F_radial * r` (N/m²)

Onde:
* `σ_circ` é a tensão de tração circunferencial

## 4. Efeitos Térmicos

### 4.1. Elevação de Temperatura

* `ΔT = (I_cc / I_nom)² * t / C` (°C)

Onde:
* `ΔT` é a elevação de temperatura
* `I_cc` é a corrente de curto-circuito
* `I_nom` é a corrente nominal
* `t` é o tempo em segundos
* `C` é a capacidade térmica específica do condutor

### 4.2. Integral de Joule (I²t)

* `I²t = I_cc² * t` (A²s)

Onde:
* `I²t` é a integral de Joule
* `I_cc` é a corrente de curto-circuito eficaz
* `t` é o tempo em segundos

### 4.3. Verificação da Capacidade Térmica

* `I²t ≤ K² * S²`

Onde:
* `K` é uma constante que depende do material do condutor
* `S` é a seção transversal do condutor em mm²

## 5. Análise de Suportabilidade

### 5.1. Verificação Mecânica

* **Tensão Radial**: `σ_radial ≤ σ_radial_max`
* **Tensão Circunferencial**: `σ_circ ≤ σ_circ_max`

Onde:
* `σ_radial_max` e `σ_circ_max` são as tensões máximas admissíveis

### 5.2. Verificação Térmica

* **Elevação de Temperatura**: `ΔT ≤ ΔT_max`
* **Integral de Joule**: `I²t ≤ I²t_max`

Onde:
* `ΔT_max` é a elevação máxima de temperatura admissível
* `I²t_max` é a integral de Joule máxima admissível

## 6. Recomendações para Projeto

### 6.1. Margens de Segurança

* **Corrente de Curto-Circuito**: Considerar 10-20% acima do calculado
* **Esforços Mecânicos**: Aplicar fator de segurança de 1.5-2.0
* **Efeitos Térmicos**: Considerar tempo de atuação da proteção com margem

### 6.2. Considerações Especiais

* **Envelhecimento**: Considerar redução da capacidade mecânica e térmica com o envelhecimento
* **Múltiplos Curtos-Circuitos**: Considerar o efeito cumulativo de múltiplos eventos
* **Assimetria**: Considerar o efeito da componente DC na corrente de curto-circuito

---

## Notas Importantes

1. Os valores de impedância percentual são geralmente fornecidos pelo fabricante ou determinados por ensaios.
2. A potência de curto-circuito da rede deve ser obtida junto à concessionária de energia.
3. O fator X/R pode variar significativamente dependendo do projeto do transformador e da rede.
4. A duração do curto-circuito depende do tempo de atuação das proteções.
