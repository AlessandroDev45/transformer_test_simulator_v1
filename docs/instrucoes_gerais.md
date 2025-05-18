# Instruções Gerais do Código Transformer Test Simulator

Este documento descreve a estrutura principal e os módulos de entrada de dados do programa Transformer Test Simulator.

## Programa Principal

O programa principal é constituído por 10 Módulos Principais, cada um focado em uma área específica dos testes e análises de transformadores. Estes módulos interagem entre si, utilizando dados de entrada para realizar cálculos e gerar resultados.

## Arquitetura de Dados e Dependências

O sistema utiliza uma arquitetura de "fonte única da verdade" (single source of truth) onde o módulo de Dados Básicos (transformer-inputs-store) serve como a fonte autoritativa para todos os dados fundamentais do transformador. Os demais módulos referenciam estes dados básicos em vez de duplicá-los, garantindo consistência e evitando redundâncias.

### Fluxo de Dados

1. Os dados básicos são inseridos no módulo "Transformer Inputs" e armazenados no `transformer-inputs-store`
2. Quando o usuário navega para outros módulos, os dados relevantes são propagados do `transformer-inputs-store` para os stores específicos de cada módulo
3. Cada módulo específico mantém apenas seus dados especializados, referenciando os dados básicos quando necessário

### Dependências Entre Módulos

Além das dependências com o transformer-inputs-store, existem dependências diretas entre alguns módulos:

1. **Tensão Induzida (Induced Voltage)** depende de:
   - **Perdas (Losses)**: Utiliza dados de indução nominal (`inducao`), peso do núcleo (`peso_nucleo`) e perdas em vazio (`perdas_vazio_kw`) para cálculos de potência magnética e indutiva

2. **Análise Dielétrica (Dielectric Analysis)** depende de:
   - **Dados Básicos (Transformer Inputs)**: Utiliza dados básicos do transformador como tensões nominais, tipo de transformador, tipo de isolamento e níveis de isolamento para realizar análises dielétricas

3. **Elevação de Temperatura (Temperature Rise)** depende de:
   - **Perdas (Losses)**: Utiliza dados de perdas em carga (`perdas_carga_min`) e perdas em vazio (`perdas_vazio_kw`) para cálculos de elevação de temperatura e constante de tempo térmica

4. **Histórico (History)** depende de:
   - Todos os outros módulos: Coleta e armazena dados de todos os módulos para consulta futura

### 1. Dados Básicos (Transformer Inputs)

Este módulo coleta as informações fundamentais do transformador e serve como a fonte autoritativa para todos os dados básicos.

**Entradas de Dados Básicos:**

*   Potência (MVA) - `potencia_mva`
*   Frequência (Hz) - `frequencia`
*   Tipo Trafo - `tipo_transformador`
*   Grupo Ligação - `grupo_ligacao`
*   Líquido Isolante - `liquido_isolante`
*   Tipo Isolamento - `tipo_isolamento`
*   Norma Aplicável - `norma_iso`
*   Elevação Óleo (°C) - `elevacao_oleo_topo`
*   Elevação Enrolamento (°C) - `elevacao_enrol`
*   Peso Parte Ativa (kg) - `peso_parte_ativa`
*   Peso Tanque (kg) - `peso_tanque_acessorios`
*   Peso Óleo (kg) - `peso_oleo`
*   Peso Total (kg) - `peso_total`

**Parâmetros dos Enrolamentos:**

Para cada enrolamento (Alta Tensão - AT, Baixa Tensão - BT, e Terciário, se existir), são necessários os seguintes parâmetros:

*   Tensão (kV) - `tensao_at`, `tensao_bt`, `tensao_terciario`
*   Classe Tensão (kV) - `classe_tensao_at`, `classe_tensao_bt`, `classe_tensao_terciario`
*   Corrente Nominal (A) - `corrente_nominal_at`, `corrente_nominal_bt`, `corrente_nominal_terciario` - **Valores Calculados** (baseados em Potência e Tensão)
*   Impedância Z (%) - `impedancia`
*   Conexão - `conexao_at`, `conexao_bt`, `conexao_terciario`

**Níveis de Isolamento (para AT, BT, Terciário):**

*   Teste Tensão Aplicada (kV) - `teste_tensao_aplicada_at`, `teste_tensao_aplicada_bt`, `teste_tensao_aplicada_terciario`
*   Teste Tensão Induzida (kV) - `teste_tensao_induzida_at`
*   BIL (kV - Nível Básico de Impulso) - `nbi_at`, `nbi_bt`, `nbi_terciario`
*   SIL (kV - Nível de Surtos de Manobra) - `sil_at`, `sil_bt`, `sil_terciario`
*   Classe de Neutro (se existir) - `tensao_bucha_neutro_at`, `tensao_bucha_neutro_bt`
*   NBI Neutro (se existir) (kV) - `nbi_neutro_at`, `nbi_neutro_bt`, `nbi_neutro_terciario`
*   SIL Neutro (se existir) (kV) - `sil_neutro_at`, `sil_neutro_bt`, `sil_neutro_terciario`

**TAP de Alta Tensão (se aplicável):**

*   **Tap + (Maior Tensão):**
    *   Tensão (kV) - `tensao_at_tap_maior`
    *   Corrente (A) - `corrente_nominal_at_tap_maior` - Calculada
    *   Impedância Z (%) - `impedancia_tap_maior`
*   **Tap - (Menor Tensão):**
    *   Tensão (kV) - `tensao_at_tap_menor`
    *   Corrente (A) - `corrente_nominal_at_tap_menor` - Calculada
    *   Impedância Z (%) - `impedancia_tap_menor`

### 2. Perdas (Losses)

Este módulo trata dos parâmetros relacionados às perdas do transformador.

**Dependências de Dados Básicos:**
* `tensao_bt` - Utilizado para cálculo de perdas em vazio
* `tipo_transformador` - Determina o fator de excitação para cálculos
* `corrente_nominal_at`, `corrente_nominal_bt`, `corrente_nominal_terciario` - Utilizados para cálculos de perdas em carga
* `tensao_at`, `tensao_bt`, `tensao_terciario` - Utilizados para cálculos de tensão de curto-circuito
* `impedancia`, `impedancia_tap_maior`, `impedancia_tap_menor` - Utilizados para cálculos de perdas em carga
* `potencia_mva` - Utilizado para cálculos de potência nominal e perdas

**Transformações Aplicadas:**
* Cálculo de perdas específicas do núcleo (W/kg) baseado na indução
* Correção de temperatura para perdas em carga
* Cálculo de potência magnética a partir do fator de potência magnética

**Perdas em Vazio:**

*   Perdas em Vazio (kW)
*   Peso Núcleo (toneladas)
*   Correntes de Excitação: Percentual (geral), 1.1 pU (percentual), 1.2 pU (percentual)
*   Indução do Núcleo (Tesla)

**Perdas em Carga:**

*   Temperatura Referência (°C)
*   Perdas Totais: Tap -, Nominal, Tap +

### 3. Impulso

Este módulo gerencia os dados para simulação ou análise de ensaios de impulso.

**Dependências de Dados Básicos:**
* `tensao_at` - Utilizado para cálculos de tensão de ensaio
* `potencia_mva` - Utilizado para cálculo de indutância do transformador
* `impedancia` - Utilizado para cálculo de indutância do transformador
* `frequencia` - Utilizado para cálculo de indutância do transformador
* `nbi_at`, `nbi_bt`, `nbi_terciario` - Utilizados como referência para tensões de ensaio

**Transformações Aplicadas:**
* Cálculo da indutância do transformador a partir de tensão, potência e impedância
* Conversão de unidades para simulação (pF para F, μH para H)

**Entradas:**

*   Tipo: Atmosférico (LI), Manobra (SI), Cortado (LIC)
*   Tensão (kV)
*   Configuração do ensaio
*   Modelo utilizado
*   Shunt (Ω)
*   Capacitância Parasita (pF)

**Resistores e Ajustes:**

*   Rf (por coluna) (Ω)
*   Rt (por coluna) (Ω)
*   Aj. L (fator de ajuste de indutância)
*   Aj. Rt (fator de ajuste de resistência)
*   L Extra (μH) - Indutância extra
*   Indutor Extra (Descrição/Nome)
*   L Carga/Trafo (H) - Indutância da carga ou do transformador

### 4. Análise Dielétrica (Dielectric Analysis)

Este módulo realiza análises dielétricas do transformador.

**Dependências de Dados Básicos:**
* `tipo_transformador` - Utilizado para determinar o tipo de análise
* `tipo_isolamento` - Utilizado para cálculos de isolamento
* `nbi_at`, `nbi_bt`, `nbi_terciario` - Utilizados para análise de impulso atmosférico
* `sil_at`, `sil_bt`, `sil_terciario` - Utilizados para análise de impulso de manobra
* `nbi_neutro_at`, `nbi_neutro_bt`, `nbi_neutro_terciario` - Utilizados para análise de neutro
* `sil_neutro_at`, `sil_neutro_bt`, `sil_neutro_terciario` - Utilizados para análise de neutro
* `teste_tensao_aplicada_at`, `teste_tensao_aplicada_bt`, `teste_tensao_aplicada_terciario` - Utilizados para análise de tensão aplicada
* `teste_tensao_induzida_at` - Utilizado para análise de tensão induzida

**Transformações Aplicadas:**
* Cálculo de espaçamentos conforme normas NBR e IEEE
* Derivação de valores de impulso cortado a partir de valores de BIL

### 5. Tensão Induzida (Induced Voltage)

Este módulo trata do ensaio de tensão induzida.

**Dependências de Dados Básicos:**
* `tipo_transformador` - Determina o tipo de análise (monofásico/trifásico)
* `frequencia` - Utilizado para cálculos de frequência de teste
* `tensao_at`, `tensao_bt` - Utilizados para cálculos de tensão de ensaio
* `teste_tensao_induzida_at` - Utilizado como tensão de ensaio

**Transformações Aplicadas:**
* Cálculo da indução no núcleo na frequência de teste
* Cálculo de potência ativa, magnética e indutiva
* Cálculo de potência capacitiva

**Entradas:**

*   Teste (fp - fator de ponta): Valor

**Parâmetros (Podem vir de Dados Básicos ou Análise Dielétrica):**

*   Capacitância AT-GND (pF)
*   Tensão de Ensaio AT, BT, Terciário (kV) - Vêm de Dados Básicos.
*   Frequência de Ensaio (Hz) - Vêm de Dados Básicos.

### 6. Tensão Aplicada (Applied Voltage)

Este módulo trata do ensaio de tensão aplicada.

**Dependências de Dados Básicos:**
* `teste_tensao_aplicada_at`, `teste_tensao_aplicada_bt`, `teste_tensao_aplicada_terciario` - Utilizados como tensões de ensaio
* `frequencia` - Utilizado para cálculos de impedância capacitiva

**Transformações Aplicadas:**
* Ajuste de capacitância baseado na tensão de ensaio
* Cálculo de impedância capacitiva, corrente e potência reativa

**Parâmetros Específicos:**
* Capacitância AT (pF)
* Capacitância BT (pF)
* Capacitância Terciário (pF)

**Parâmetros (Vêm de Dados Básicos):**

*   Tensão de Ensaio AT (kV)
*   Tensão de Ensaio BT (kV)
*   Tensão de Ensaio Terciário (kV)
*   Frequência de Ensaio (Hz)

### 7. Curto-Circuito (Short Circuit)

Este módulo lida com os ensaios de curto-circuito.

**Dependências de Dados Básicos:**
* `impedancia` - Utilizado como referência para impedância nominal
* `potencia_mva` - Utilizado para determinar categoria de potência e cálculos de corrente
* `tensao_at`, `tensao_bt`, `tensao_terciario` - Utilizados para cálculos de corrente de curto-circuito
* `corrente_nominal_at`, `corrente_nominal_bt`, `corrente_nominal_terciario` - Utilizados para cálculos de corrente de curto-circuito

**Transformações Aplicadas:**
* Cálculo de corrente de curto-circuito simétrica
* Cálculo de corrente de curto-circuito de pico
* Verificação de variação de impedância conforme limites normativos

**Entradas:**

*   Impedâncias Medidas (%):
    *   Pré-Ensaio (Z_antes)
    *   Pós-Ensaio (Z_depois)

**Parâmetros Adicionais:**

*   Fator Pico (k√2): Valor
*   Lado Cálculo Isc: AT / BT / Terciário (Seleção)
*   Categoria (Potência) - Vêm de Dados Básicos.

### 8. Elevação de Temperatura (Temperature Rise)

Este módulo trata da análise da elevação de temperatura.

**Dependências de Dados Básicos:**
* `elevacao_oleo_topo` - Utilizado como elevação máxima de óleo
* `potencia_mva` - Utilizado para cálculos de potência total
* `peso_parte_ativa`, `peso_oleo`, `peso_tanque_acessorios` - Utilizados para cálculos de constante de tempo térmica

**Transformações Aplicadas:**
* Cálculo de temperatura média do enrolamento
* Cálculo de elevação média do enrolamento
* Cálculo de elevação de topo de óleo
* Cálculo de constante de tempo térmica

**Entradas:**

*   **Condições Ambientais e Material:**
    *   Temp. Ambiente (Θa) (°C)
    *   Material Enrolamento (Cobre / Alumínio)
*   **Medições a Frio:**
    *   Res. Fria (Rc) (Ohm)
    *   Temp. Ref. Fria (Θc) (°C)
*   **Medições a Quente:**
    *   Res. Quente (Rw) (Ohm)
    *   Temp. Topo Óleo (Θoil) (°C)
*   **Parâmetro para Constante de Tempo Térmica:**
    *   Elevação Máx Óleo (ΔΘoil_max) (K) - Vêm de Dados Básicos.

### 9. Histórico de Seções (History)

**Função:** Permite salvar todos os dados de entrada e resultados dos módulos anteriores no banco de dados para consulta futura.

**Dependências de Dados:**
* Todos os stores do sistema, incluindo:
  * `transformer-inputs-store`
  * `losses-store`
  * `impulse-store`
  * `dieletric-analysis-store`
  * `applied-voltage-store`
  * `induced-voltage-store`
  * `short-circuit-store`
  * `temperature-rise-store`
  * `comprehensive-analysis-store`

**Transformações Aplicadas:**
* Serialização de dados para armazenamento em banco de dados
* Desserialização de dados ao carregar sessões salvas

### 10. Consulta de Normas (Standards)

Este módulo permite gerenciar e consultar normas técnicas.

**Função:** Permite a inclusão de novas normas técnicas e a consulta das normas já armazenadas no banco de dados. As entradas são para gerenciar o banco de dados de normas (inserir novos documentos, buscar por critérios, etc.).
