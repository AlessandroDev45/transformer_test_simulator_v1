# Detalhamento da Análise Dielétrica

Este documento detalha as fórmulas e parâmetros usados na análise dielétrica para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para a análise dielétrica:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                        |
| Tensão Nominal BT             | Tensão nominal do lado de Baixa Tensão | kV      | `tensao_bt`                        |
| Classe de Tensão AT           | Classe de tensão do lado de Alta Tensão| kV      | `classe_tensao_at`                 |
| Classe de Tensão BT           | Classe de tensão do lado de Baixa Tensão| kV     | `classe_tensao_bt`                 |
| Nível Básico de Isolamento    | Nível de isolamento (BIL)              | kV      | `bil`                              |
| Nível de Isolamento AC        | Nível de isolamento AC                 | kV      | `ac_level`                         |
| Espaçamentos                  | Distâncias entre partes energizadas    | mm      | `espacamentos`                     |
| Meio Isolante                 | Tipo de meio isolante (óleo, ar, etc.) | -       | `meio_isolante`                    |
| Altitude de Instalação        | Altitude do local de instalação        | m       | `altitude`                         |

## 2. Fundamentos Teóricos

### 2.1. Rigidez Dielétrica

A rigidez dielétrica é a máxima intensidade de campo elétrico que um material isolante pode suportar sem sofrer ruptura:

* **Óleo Mineral**: 10-15 kV/mm
* **Papel Impregnado**: 40-60 kV/mm
* **Ar (nível do mar)**: 3 kV/mm
* **SF6**: 7-8 kV/mm

### 2.2. Correção para Altitude

A rigidez dielétrica do ar diminui com o aumento da altitude. O fator de correção é:

* `K_alt = e^(-h/8150)`

Onde:
* `K_alt` é o fator de correção para altitude
* `h` é a altitude em metros
* `8150` é uma constante derivada da pressão atmosférica

### 2.3. Distância de Isolamento

A distância mínima de isolamento é calculada como:

* `d_min = V_max / E_max`

Onde:
* `d_min` é a distância mínima em mm
* `V_max` é a tensão máxima em kV
* `E_max` é a rigidez dielétrica em kV/mm

## 3. Análise de Espaçamentos

### 3.1. Espaçamentos Fase-Fase

* **Tensão Máxima**: `V_max = V_linha * k_sobretensao`
* **Distância Mínima**: `d_min = V_max / (E_ar * K_alt)`

### 3.2. Espaçamentos Fase-Terra

* **Tensão Máxima**: `V_max = V_fase * k_sobretensao`
* **Distância Mínima**: `d_min = V_max / (E_ar * K_alt)`

### 3.3. Espaçamentos em Óleo

* **Distância Mínima**: `d_min = V_max / E_oleo`

## 4. Análise de Níveis de Isolamento

### 4.1. Verificação do BIL

* **BIL Mínimo**: Determinado pela classe de tensão conforme normas
* **BIL Corrigido para Altitude**: `BIL_corrigido = BIL / K_alt`
* **Verificação**: `BIL_especificado ≥ BIL_corrigido`

### 4.2. Verificação do Nível AC

* **AC Mínimo**: Determinado pela classe de tensão conforme normas
* **AC Corrigido para Altitude**: `AC_corrigido = AC / K_alt`
* **Verificação**: `AC_especificado ≥ AC_corrigido`

## 5. Análise de Coordenação de Isolamento

### 5.1. Fator de Coordenação

* `K_coord = BIL / (√2 * V_max)`

Onde:
* `K_coord` é o fator de coordenação
* `BIL` é o nível básico de isolamento
* `V_max` é a tensão máxima do sistema

### 5.2. Verificação da Coordenação

* **Fator Mínimo**: Tipicamente 1.2 para sistemas sem para-raios
* **Verificação**: `K_coord ≥ K_min`

## 6. Análise de Distribuição de Tensão em Enrolamentos

### 6.1. Distribuição Inicial

* `α = √(C_s / C_g)`
* `V(x) = V_0 * (cosh(αx) / cosh(α))`

Onde:
* `α` é o parâmetro de distribuição
* `C_s` é a capacitância série por unidade de comprimento
* `C_g` é a capacitância para terra por unidade de comprimento
* `V(x)` é a tensão na posição x do enrolamento
* `V_0` é a tensão aplicada
* `x` é a posição normalizada (0 a 1)

### 6.2. Fator de Distribuição Não-Uniforme

* `K_dist = V_max / V_avg`

Onde:
* `K_dist` é o fator de distribuição
* `V_max` é a tensão máxima no enrolamento
* `V_avg` é a tensão média no enrolamento

## 7. Recomendações para Projeto

### 7.1. Margens de Segurança

* **Espaçamentos**: Adicionar 10-20% à distância mínima calculada
* **BIL**: Especificar BIL pelo menos 10% acima do mínimo requerido
* **Coordenação**: Manter fator de coordenação acima de 1.3

### 7.2. Considerações Especiais

* **Contaminação**: Em ambientes com poluição, aumentar as distâncias de isolamento
* **Umidade**: Em ambientes úmidos, considerar tratamentos especiais para isolantes
* **Temperatura**: Considerar o efeito da temperatura na rigidez dielétrica dos isolantes

---

## Notas Importantes

1. Os valores de BIL e AC são determinados pelas normas técnicas e variam conforme a classe de tensão.
2. A rigidez dielétrica dos materiais pode variar conforme a qualidade, temperatura e envelhecimento.
3. A análise dielétrica deve considerar não apenas condições normais, mas também sobretensões transitórias.
4. A coordenação de isolamento deve ser verificada considerando a proteção por para-raios, quando aplicável.
