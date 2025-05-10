"""
Script para testar o layout do transformer_inputs.py isoladamente.
"""
import sys
import os

# Adiciona o diretório raiz do projeto ao caminho de importação
sys.path.insert(0, os.path.abspath('.'))

import dash
from dash import html
import dash_bootstrap_components as dbc

# Agora podemos importar o layout
from layouts.transformer_inputs import create_transformer_inputs_layout

# Inicializa a aplicação Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Define o layout da aplicação
app.layout = html.Div([
    html.H1("Teste do Layout de Inputs do Transformador"),
    create_transformer_inputs_layout()
])

# Executa a aplicação
if __name__ == '__main__':
    app.run_server(debug=True)
