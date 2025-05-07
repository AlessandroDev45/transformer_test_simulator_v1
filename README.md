# Simulador de Testes de Transformadores

![CI/CD Pipeline](https://github.com/AlessandroDev45/transformer_test_simulator_v1/actions/workflows/ci.yml/badge.svg)

Um aplicativo web interativo para simulação e análise de testes em transformadores de potência, baseado nas normas IEC, IEEE e ABNT.

## Descrição

O Simulador de Testes de Transformadores é uma ferramenta desenvolvida para engenheiros e técnicos que trabalham com transformadores de potência. Ele permite simular diversos tipos de testes e ensaios, calcular parâmetros importantes e verificar a conformidade com as normas técnicas internacionais e brasileiras.

## Funcionalidades

O simulador oferece os seguintes módulos de análise:

- **Dados Básicos do Transformador**: Entrada e cálculo de parâmetros fundamentais do transformador
- **Perdas**: Cálculo e análise de perdas em vazio e em carga
- **Impulso**: Simulação de ensaios de impulso atmosférico (LI), impulso de manobra (SI) e impulso cortado (LIC)
- **Análise Dielétrica**: Verificação de espaçamentos e níveis de isolamento
- **Tensão Aplicada**: Cálculo de parâmetros para ensaios de tensão aplicada
- **Tensão Induzida**: Simulação de ensaios de tensão induzida com análise de frequências variáveis
- **Curto-Circuito**: Cálculo de correntes de curto-circuito e verificação de suportabilidade
- **Elevação de Temperatura**: Análise de aquecimento e elevação de temperatura
- **Histórico de Testes**: Armazenamento e recuperação de sessões de teste anteriores
- **Consulta de Normas**: Interface para consulta rápida de normas técnicas relevantes

## Tecnologias Utilizadas

- **Python**: Linguagem principal de desenvolvimento
- **Dash**: Framework para criação de aplicações web interativas
- **Dash Bootstrap Components**: Componentes de UI responsivos
- **Plotly**: Biblioteca para visualização de dados e gráficos interativos
- **Pandas**: Manipulação e análise de dados
- **NumPy/SciPy**: Computação numérica e científica
- **SQLite**: Armazenamento local de dados

## Estrutura do Projeto

```bash
transformer_test_simulator_v1/
├── app.py                  # Ponto de entrada da aplicação
├── server.py               # Ponto de entrada alternativo com inicialização do MCP
├── config.py               # Configurações globais
├── schemas.py              # Esquemas Pydantic para validação de dados
├── app_core/               # Núcleo da aplicação
│   ├── calculations.py     # Funções de cálculo principais
│   ├── data_models.py      # Modelos de dados
│   ├── standards.py        # Implementação das normas técnicas
│   ├── startup.py          # Inicialização do MCP com dados padrão
│   └── transformer_mcp.py  # Model-Controller-Presenter para transformadores
├── assets/                 # Arquivos estáticos (CSS, imagens)
│   ├── help_docs/          # Documentação de ajuda
│   └── standards_data/     # Dados das normas técnicas
├── callbacks/              # Callbacks Dash para interatividade
│   ├── transformer_inputs.py
│   ├── losses.py
│   ├── impulse.py
│   ├── dieletric_analysis.py
│   ├── applied_voltage.py
│   ├── induced_voltage.py
│   ├── short_circuit.py
│   ├── temperature_rise.py
│   ├── history.py
│   └── standards_consultation.py
├── components/             # Componentes reutilizáveis
│   ├── formatters.py
│   ├── ui_elements.py
│   ├── validators.py
│   ├── global_stores.py
│   └── help_button.py
├── defaults/               # Valores padrão para inicialização
│   └── transformer.json    # Dados padrão do transformador
├── layouts/                # Layouts das diferentes seções
│   ├── main_layout.py
│   ├── transformer_inputs.py
│   ├── losses.py
│   └── ...
├── tests/                  # Testes automatizados
│   ├── test_transformer_mcp.py
│   ├── test_startup.py
│   └── test_schemas.py
├── utils/                  # Utilitários diversos
│   ├── constants.py        # Constantes globais
│   ├── db_manager.py       # Gerenciamento de banco de dados
│   ├── logger.py           # Configuração de logs
│   ├── store_diagnostics.py # Diagnóstico de armazenamento
│   ├── mcp_utils.py        # Utilitários para o MCP
│   └── styles.py           # Estilos e temas
├── data/                   # Diretório para armazenamento de dados
│   ├── standards.db        # Banco de dados de normas
│   ├── test_sessions.db    # Banco de dados de sessões de teste
│   └── mcp_state/          # Estado do MCP persistido em disco
├── docs/                   # Documentação adicional
│   └── formulas_*.md       # Documentação de fórmulas
├── .github/workflows/      # Configuração de CI/CD
│   └── ci.yml              # Workflow de CI/CD
├── Dockerfile              # Configuração para build Docker
├── docker-compose.yml      # Configuração para Docker Compose
├── pytest.ini              # Configuração para testes com pytest
└── requirements.txt        # Dependências do projeto
```

## Requisitos

- Python 3.9 ou superior
- Dash 2.5.0 ou superior
- Dash Bootstrap Components 1.0.0 ou superior
- Plotly 5.0.0 ou superior
- NumPy 1.20.0 ou superior
- SciPy 1.7.0 ou superior
- Pandas 1.3.0 ou superior
- SQLite 3.35.0 ou superior
- Outras dependências listadas em `requirements.txt`

## Instalação

### Método 1: Instalação Local

1. Clone o repositório:

   ```bash
   git clone https://github.com/AlessandroDev45/transformer_test_simulator_v1.git
   cd transformer_test_simulator_v1
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação:

   ```bash
   python server.py  # Usa o ponto de entrada com inicialização do MCP
   # ou
   python app.py     # Ponto de entrada tradicional
   ```

5. Acesse a aplicação no navegador:

   ```text
   http://127.0.0.1:8050/
   ```

### Método 2: Usando Docker

1. Clone o repositório:

   ```bash
   git clone https://github.com/AlessandroDev45/transformer_test_simulator_v1.git
   cd transformer_test_simulator_v1
   ```

2. Construa e inicie o contêiner com Docker Compose:

   ```bash
   docker-compose up -d
   ```

3. Acesse a aplicação no navegador:

   ```text
   http://127.0.0.1:8050/
   ```

4. Para parar a aplicação:

   ```bash
   docker-compose down
   ```

## Uso

1. Comece preenchendo os dados básicos do transformador na primeira aba.
2. Navegue pelas diferentes seções para realizar análises específicas.
3. Os resultados são atualizados automaticamente e podem ser visualizados em tabelas e gráficos interativos.
4. Os dados são armazenados localmente no navegador e podem ser salvos em sessões para uso futuro.
5. Utilize a aba de histórico para recuperar sessões de teste anteriores.
6. Consulte as normas técnicas relevantes na aba de consulta de normas.

## Características Principais

- **Interface Responsiva**: Adaptável a diferentes tamanhos de tela
- **Tema Claro/Escuro**: Suporte a temas de interface para melhor experiência do usuário
- **Cálculos em Tempo Real**: Resultados atualizados instantaneamente conforme entrada de dados
- **Visualização Gráfica**: Gráficos interativos para melhor compreensão dos resultados
- **Persistência de Dados**: Armazenamento local de dados para continuidade entre sessões
- **Exportação de Relatórios**: Geração de relatórios em formato PDF
- **Validação de Entrada**: Verificação de dados de entrada para evitar erros de cálculo
- **Conformidade com Normas**: Verificação automática de conformidade com normas técnicas

## Normas Técnicas Implementadas

- **ABNT NBR 5356**: Norma brasileira para transformadores de potência
- **ABNT NBR IEC 60060-1**: Norma brasileira para técnicas de ensaios de alta tensão
- **IEEE C57.12.00**: Norma americana para transformadores de potência
- **IEC 60076**: Norma internacional para transformadores de potência

## Testes

O projeto utiliza pytest para testes automatizados. Para executar os testes:

```bash
# Instalar dependências de teste
pip install pytest pytest-cov

# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=. --cov-report=html

# Executar testes específicos
pytest tests/test_transformer_mcp.py
```

Os relatórios de cobertura de testes são gerados na pasta `htmlcov/`.

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

Certifique-se de que seus testes passam e que a cobertura de testes é mantida ou melhorada.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato através de [aaswiel@gmail.com].
