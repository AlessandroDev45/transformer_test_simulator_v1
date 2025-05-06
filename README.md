# Simulador de Testes de Transformadores

Um aplicativo web interativo para simulação e análise de testes em transformadores de potência, baseado nas normas IEC, IEEE e ABNT.

## Descrição

O Simulador de Testes de Transformadores é uma ferramenta desenvolvida para engenheiros e técnicos que trabalham com transformadores de potência. Ele permite simular diversos tipos de testes e ensaios, calcular parâmetros importantes e verificar a conformidade com as normas técnicas internacionais e brasileiras.

## Funcionalidades

O simulador oferece os seguintes módulos de análise:

- **Dados Básicos do Transformador**: Entrada e cálculo de parâmetros fundamentais do transformador
- **Perdas**: Cálculo e análise de perdas em vazio e em carga
- **Impulso**: Simulação de ensaios de impulso atmosférico (LI) e impulso cortado (LIC)
- **Análise Dielétrica**: Verificação de espaçamentos e níveis de isolamento
- **Tensão Aplicada**: Cálculo de parâmetros para ensaios de tensão aplicada
- **Tensão Induzida**: Simulação de ensaios de tensão induzida com análise de frequências variáveis
- **Curto-Circuito**: Cálculo de correntes de curto-circuito e verificação de suportabilidade
- **Elevação de Temperatura**: Análise de aquecimento e elevação de temperatura

## Tecnologias Utilizadas

- **Python**: Linguagem principal de desenvolvimento
- **Dash**: Framework para criação de aplicações web interativas
- **Dash Bootstrap Components**: Componentes de UI responsivos
- **Plotly**: Biblioteca para visualização de dados e gráficos interativos
- **Pandas**: Manipulação e análise de dados
- **NumPy**: Computação numérica e científica

## Estrutura do Projeto

```
transformer_test_simulator/
├── app.py                  # Ponto de entrada da aplicação
├── config.py               # Configurações globais
├── app_core/               # Núcleo da aplicação
│   ├── calculations.py     # Funções de cálculo principais
│   ├── standards.py        # Implementação das normas técnicas
│   └── ...
├── assets/                 # Arquivos estáticos (CSS, imagens)
│   └── tables/             # Tabelas de dados das normas
├── callbacks/              # Callbacks Dash para interatividade
│   ├── transformer_inputs.py
│   ├── losses.py
│   ├── impulse.py
│   ├── dieletric_analysis.py
│   ├── applied_voltage.py
│   ├── induced_voltage.py
│   ├── short_circuit.py
│   ├── temperature_rise.py
│   └── ...
├── components/             # Componentes reutilizáveis
│   ├── formatters.py
│   ├── ui_elements.py
│   ├── validators.py
│   └── ...
├── layouts/                # Layouts das diferentes seções
│   ├── main_layout.py
│   ├── transformer_inputs.py
│   ├── losses.py
│   └── ...
├── logs/                   # Diretório para logs da aplicação
└── utils/                  # Utilitários diversos
    ├── constants.py
    └── ...
```

## Requisitos

- Python 3.9 ou superior
- Dash 3.0.0 ou superior
- Dash Bootstrap Components
- Plotly
- Pandas
- NumPy
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/transformer_test_simulator.git
   cd transformer_test_simulator
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```
   python app.py
   ```

5. Acesse a aplicação no navegador:
   ```
   http://127.0.0.1:8050/
   ```

## Uso

1. Comece preenchendo os dados básicos do transformador na primeira aba.
2. Navegue pelas diferentes seções para realizar análises específicas.
3. Os resultados são atualizados automaticamente e podem ser visualizados em tabelas e gráficos interativos.
4. Os dados são armazenados localmente no navegador para persistência entre sessões.

## Normas Técnicas Implementadas

- **ABNT NBR 5356**: Norma brasileira para transformadores de potência
- **IEEE C57.12.00**: Norma americana para transformadores de potência
- **IEC 60060-1**: Norma internacional para técnicas de ensaios de alta tensão

**Instruções Detalhadas:**

1.  **Varredura:** Examine todos os arquivos `.py` dentro do diretório `callbacks/`.
2.  **Identificação:** Encontre todas as definições de função que são imediatamente precedidas pelo decorador `@app.callback(...)` ou `app.callback(...)`.
3.  **Extração de Informações:** Para cada função de callback encontrada:
    *   Identifique o nome atual da função Python.
    *   Determine o `nome_do_modulo` a partir do nome do arquivo (ex: `callbacks/losses.py` -> `losses`).
    *   Analise os `Output(...)` definidos no decorador para entender o propósito principal do callback. Se houver múltiplos Outputs, foque no mais significativo ou descreva a ação geral (ex: `update_page_layout`, `handle_user_input`).
4.  **Verificação da Convenção:** Compare o nome atual da função com o nome esperado pela convenção `[nome_do_modulo]_[output_principal_ou_proposito_geral]`.
5.  **Renomeação (se necessário):**
    *   Se o nome atual *não* seguir a convenção, construa o novo nome padronizado.
    *   Renomeie a função Python para o novo nome padronizado. (Ex: `def update_graph(...)` em `callbacks/impulse.py` se torna `def impulse_update_graph(...)`).
6.  **Relatório:** Apresente um resumo das funções de callback encontradas e quais foram renomeadas, mostrando o nome antigo e o novo nome. Ex:
    *   `callbacks/losses.py`:
        *   `handle_perdas_vazio` -> `losses_handle_perdas_vazio` (ou `losses_update_vazio_results`)
        *   `handle_perdas_carga` -> `losses_handle_perdas_carga` (ou `losses_update_carga_results`)
        *   `display_transformer_info` -> `losses_display_transformer_info`
    *   `callbacks/impulse.py`:
        *   `toggle_simulation` -> `impulse_toggle_simulation`
        *   `display_transformer_info_impulse` -> `impulse_display_transformer_info` (Removido sufixo redundante)
        *   `update_impulse_simulation` (se existisse) -> `impulse_update_simulation_outputs`

**Considerações Adicionais:**

*   Se um nome de função já segue a convenção, não o altere.
*   Se a determinação do `[output_principal_ou_proposito_geral]` for ambígua (ex: muitos Outputs não relacionados), use um nome que descreva a ação geral (ex: `impulse_update_main_display`).
*   Priorize a clareza sobre a brevidade excessiva.
*   Esta renomeação foca nos nomes das *funções Python*, não nos IDs dos componentes HTML/Dash.

Por favor, execute esta auditoria e aplique as renomeações necessárias em todos os arquivos relevantes no diretório `callbacks/`.

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato através de [aaswiel@gmail.com].
