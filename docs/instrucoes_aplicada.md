# Detalhamento dos Cálculos de Tensão Aplicada

Este documento detalha as fórmulas e parâmetros usados nos cálculos de tensão aplicada para transformadores.

---

## 1. Parâmetros de Entrada

Estes são os valores fornecidos pelo usuário ou obtidos de dados básicos para os cálculos de tensão aplicada:

| Parâmetro                     | Descrição                              | Unidade | Variável no Código                   |
| :---------------------------- | :------------------------------------- | :------ | :--------------------------------- |
| Tipo de Transformador         | Configuração (Monofásico/Trifásico)    | -       | `tipo_transformador`               |
| Tensão Nominal AT             | Tensão nominal do lado de Alta Tensão  | kV      | `tensao_at`                        |
| Tensão Nominal BT             | Tensão nominal do lado de Baixa Tensão | kV      | `tensao_bt`                        |
| Classe de Tensão AT           | Classe de tensão do lado de Alta Tensão| kV      | `classe_tensao_at`                 |
| Classe de Tensão BT           | Classe de tensão do lado de Baixa Tensão| kV     | `classe_tensao_bt`                 |
| Classe de Tensão Bucha Neutro | Classe de tensão da bucha de neutro    | kV      | `classe_tensao_bucha_neutro`       |
| Conexão AT                    | Tipo de conexão do lado de Alta Tensão | -       | `conexao_at`                       |
| Conexão BT                    | Tipo de conexão do lado de Baixa Tensão| -       | `conexao_bt`                       |
| Conexão Terciário             | Tipo de conexão do terciário (se houver)| -      | `conexao_terciario`                |

## 2. Cálculos de Tensão Aplicada

### 2.1. Determinação da Tensão de Teste

A tensão de teste para o ensaio de tensão aplicada é determinada com base na classe de tensão e no tipo de conexão definida em dados básicos:

#### 2.1.1. Para o Lado de Alta Tensão (AT)

* **Se a conexão for Yn (estrela com neutro acessível):**
  * `tensao_teste_at = classe_tensao_bucha_neutro`
* **Para outras conexões (Y, D):**
  * `tensao_teste_at = classe_tensao_at`

#### 2.1.2. Para o Lado de Baixa Tensão (BT)

* `tensao_teste_bt = classe_tensao_bt`

#### 2.1.3. Para o Terciário (se existir)

* `tensao_teste_terciario = classe_tensao_terciario`

# 2.2. Ajustes para Capacitância

Para tensões acima de 450 kV, é adicionado um valor de capacitância:
* Se tensão > 450 kV: Adicionar 330 pF
* Se tensão ≤ 450 kV: Adicionar 660 pF

## 3. Cálculo da Corrente de Teste

A corrente de teste é calculada com base na tensão de teste e na capacitância do transformador:

### 3.1. Fórmula da Corrente de Teste

* `I = 2 * π * f * C * V * 10^-6`

Onde:
* `I` é a corrente de teste em Amperes (A)
* `f` é a frequência em Hertz (Hz), geralmente 60 Hz
* `C` é a capacitância em picofarads (pF)
* `V` é a tensão de teste em Volts (V)
* `10^-6` é o fator de conversão de picofarads para farads

### 3.2. Potência Reativa

A potência reativa necessária para o teste é calculada como:

* `Q = V * I`

Onde:
* `Q` é a potência reativa em volt-amperes reativos (VAr)
* `V` é a tensão de teste em Volts (V)
* `I` é a corrente de teste em Amperes (A)

## 4. Recomendações para o Teste

### 4.1. Equipamento de Teste

* **Fonte de Tensão:** Capaz de fornecer a tensão de teste calculada
* **Capacidade de Corrente:** Suficiente para fornecer a corrente de teste calculada
* **Frequência:** Geralmente 60 Hz (ou conforme especificado)

### 4.2. Procedimento de Teste

1. Aplicar a tensão de teste gradualmente até atingir o valor calculado
2. Manter a tensão pelo tempo especificado na norma (geralmente 60 segundos)
3. Reduzir a tensão gradualmente até zero
4. Verificar se não houve descargas ou falhas durante o teste

### 4.3. Medidas de Segurança

* Garantir que todas as partes não testadas estejam devidamente aterradas
* Verificar a ausência de pessoas na área de teste
* Utilizar equipamentos de proteção individual adequados
* Seguir os procedimentos de segurança específicos para testes de alta tensão

---

## Notas Importantes

1. Os valores de tensão de teste são determinados pelas normas técnicas e podem variar conforme a edição da norma utilizada.
2. Para transformadores com múltiplos enrolamentos, cada enrolamento deve ser testado separadamente.
3. A capacitância do transformador pode variar conforme a temperatura e outras condições, o que pode afetar a corrente de teste.
4. O teste de tensão aplicada é um teste destrutivo e deve ser realizado com cuidado para evitar danos ao transformador.
