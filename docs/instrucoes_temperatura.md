# Detalhamento dos Cálculos de Elevação de Temperatura

Este documento detalha as fórmulas e parâmetros usados nos cálculos de elevação de temperatura para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de elevação de temperatura:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`                 |
| Potência Nominal              | Potência nominal do transformador      | MVA     | `potencia_nominal`                   |
| Perdas em Vazio               | Perdas no núcleo                       | kW      | `perdas_vazio`                       |
| Perdas em Carga               | Perdas nos enrolamentos a 75°C         | kW      | `perdas_carga`                       |
| Temperatura Ambiente          | Temperatura ambiente de referência     | °C      | `temp_ambiente`                      |
| Elevação de Temperatura       | Elevação de temperatura garantida      | K       | `elevacao_temp`                      |
| Tipo de Resfriamento          | Sistema de resfriamento (ONAN, ONAF, etc.) | -   | `tipo_resfriamento`                  |
| Constantes Térmicas           | Constantes de tempo térmico            | min     | `constantes_termicas`                |
| Peso do Óleo                  | Peso total do óleo isolante            | kg      | `peso_oleo`                          |
| Peso do Núcleo                | Peso do núcleo                         | kg      | `peso_nucleo`                        |
| Peso dos Enrolamentos         | Peso total dos enrolamentos            | kg      | `peso_enrolamentos`                  |

## 2. Fundamentos Teóricos

### 2.1. Equação de Balanço Térmico

* `P_perdas = C * dθ/dt + K * θ`

Onde:
* `P_perdas` é a potência de perdas em Watts
* `C` é a capacidade térmica em J/K
* `dθ/dt` é a taxa de variação da temperatura em K/s
* `K` é o coeficiente de transferência de calor em W/K
* `θ` é a elevação de temperatura acima da ambiente em K

### 2.2. Solução da Equação Diferencial

* `θ(t) = θ_final * (1 - e^(-t/τ))` (aquecimento)
* `θ(t) = θ_inicial * e^(-t/τ)` (resfriamento)

Onde:
* `θ(t)` é a elevação de temperatura no tempo t
* `θ_final` é a elevação de temperatura em regime permanente
* `θ_inicial` é a elevação de temperatura inicial
* `τ` é a constante de tempo térmica (τ = C/K)

## 3. Cálculos de Elevação de Temperatura

### 3.1. Elevação de Temperatura do Óleo

#### 3.1.1. Elevação de Temperatura do Óleo no Topo em Regime Permanente

* `Δθ_oleo_topo = Δθ_oleo_topo_nominal * (P_total / P_total_nominal)^n`

Onde:
* `Δθ_oleo_topo` é a elevação de temperatura do óleo no topo
* `Δθ_oleo_topo_nominal` é a elevação nominal (geralmente 55K para ONAN)
* `P_total` é a potência total de perdas
* `P_total_nominal` é a potência total de perdas nominal
* `n` é o expoente que depende do tipo de resfriamento (0.8 para ONAN, 0.9 para ONAF, 1.0 para OFAF)

#### 3.1.2. Elevação de Temperatura do Óleo Média

* `Δθ_oleo_media = 0.8 * Δθ_oleo_topo`

#### 3.1.3. Elevação de Temperatura do Óleo no Tempo

* `Δθ_oleo(t) = Δθ_oleo_final + (Δθ_oleo_inicial - Δθ_oleo_final) * e^(-t/τ_oleo)`

Onde:
* `τ_oleo` é a constante de tempo do óleo (tipicamente 150-200 minutos para ONAN)

### 3.2. Elevação de Temperatura dos Enrolamentos

#### 3.2.1. Gradiente de Temperatura Enrolamento-Óleo em Regime Permanente

* `Δθ_ew = Δθ_ew_nominal * (I / I_nominal)^2`

Onde:
* `Δθ_ew` é o gradiente de temperatura enrolamento-óleo
* `Δθ_ew_nominal` é o gradiente nominal (geralmente 20-25K)
* `I` é a corrente de carga
* `I_nominal` é a corrente nominal

#### 3.2.2. Elevação de Temperatura do Ponto Mais Quente

* `Δθ_hotspot = Δθ_oleo_topo + H * Δθ_ew`

Onde:
* `Δθ_hotspot` é a elevação de temperatura do ponto mais quente
* `H` é o fator de ponto quente (tipicamente 1.1-1.3)

#### 3.2.3. Elevação de Temperatura dos Enrolamentos no Tempo

* `Δθ_ew(t) = Δθ_ew_final + (Δθ_ew_inicial - Δθ_ew_final) * e^(-t/τ_ew)`

Onde:
* `τ_ew` é a constante de tempo dos enrolamentos (tipicamente 5-10 minutos)

### 3.3. Temperatura Absoluta

* `T_oleo_topo = T_ambiente + Δθ_oleo_topo`
* `T_hotspot = T_ambiente + Δθ_hotspot`

## 4. Cálculos de Capacidade de Sobrecarga

### 4.1. Fator de Carga Máximo em Regime Permanente

* `K_max = √((Δθ_oleo_max / Δθ_oleo_nominal)^(1/n))`

Onde:
* `K_max` é o fator de carga máximo
* `Δθ_oleo_max` é a elevação máxima permitida do óleo

### 4.2. Tempo Máximo de Sobrecarga

* `t_max = -τ_oleo * ln((Δθ_oleo_max - Δθ_oleo_final) / (Δθ_oleo_inicial - Δθ_oleo_final))`

Onde:
* `t_max` é o tempo máximo de sobrecarga
* `Δθ_oleo_max` é a elevação máxima permitida do óleo
* `Δθ_oleo_final` é a elevação final do óleo com a sobrecarga
* `Δθ_oleo_inicial` é a elevação inicial do óleo

### 4.3. Perda de Vida Útil

* `V = 2^((T_hotspot - 98) / 6)` (para papel Kraft)
* `V = 2^((T_hotspot - 110) / 6)` (para papel termoestabilizado)

Onde:
* `V` é a taxa relativa de envelhecimento
* `T_hotspot` é a temperatura do ponto mais quente em °C

## 5. Análise de Resfriamento

### 5.1. Capacidade de Dissipação de Calor

* `P_dissipacao = K * Δθ_oleo_topo`

Onde:
* `P_dissipacao` é a potência de dissipação em Watts
* `K` é o coeficiente de transferência de calor em W/K

### 5.2. Eficiência do Sistema de Resfriamento

* `η_resfriamento = P_dissipacao / P_total`

Onde:
* `η_resfriamento` é a eficiência do sistema de resfriamento

## 6. Recomendações para Projeto

### 6.1. Margens de Segurança

* **Elevação de Temperatura**: Considerar 5-10K abaixo do limite máximo
* **Capacidade de Sobrecarga**: Limitar a 1.3-1.5 vezes a potência nominal
* **Perda de Vida Útil**: Limitar a taxa relativa de envelhecimento a 2-3 vezes a normal

### 6.2. Considerações Especiais

* **Altitude**: Corrigir a capacidade de resfriamento para altitudes elevadas
* **Temperatura Ambiente**: Considerar variações sazonais e diárias
* **Ciclo de Carga**: Otimizar o projeto para o ciclo de carga específico

---

## Notas Importantes

1. Os valores de elevação de temperatura são geralmente especificados pelas normas técnicas (IEC, IEEE, ABNT).
2. As constantes de tempo térmicas podem variar significativamente dependendo do projeto e tamanho do transformador.
3. A perda de vida útil é cumulativa e deve ser considerada ao longo de toda a vida do transformador.
4. O sistema de resfriamento deve ser dimensionado considerando as condições ambientais mais desfavoráveis.
