# test_callback.py
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Create a simple app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create a simple layout
app.layout = html.Div([
    html.H1("Test Callback"),
    html.Div([
        html.Label("Potência (MVA):"),
        dcc.Input(id="potencia_mva", type="number", value=10),
    ]),
    html.Div([
        html.Label("Tensão AT (kV):"),
        dcc.Input(id="tensao_at", type="number", value=138),
    ]),
    html.Div([
        html.Label("Tensão BT (kV):"),
        dcc.Input(id="tensao_bt", type="number", value=13.8),
    ]),
    html.Div([
        html.Label("Tipo Transformador:"),
        dcc.Dropdown(id="tipo_transformador", options=[
            {"label": "Trifásico", "value": "Trifásico"},
            {"label": "Monofásico", "value": "Monofásico"}
        ], value="Trifásico"),
    ]),
    html.Div([
        html.Label("Corrente AT (A):"),
        html.Div(id="corrente_nominal_at"),
    ]),
    html.Div([
        html.Label("Corrente BT (A):"),
        html.Div(id="corrente_nominal_bt"),
    ]),
])

# Create a simple callback
@app.callback(
    [Output("corrente_nominal_at", "children"), Output("corrente_nominal_bt", "children")],
    [Input("potencia_mva", "value"), Input("tensao_at", "value"), Input("tensao_bt", "value"), Input("tipo_transformador", "value")]
)
def update_currents(potencia_mva, tensao_at, tensao_bt, tipo_transformador):
    log.info(f"Callback triggered with: potencia_mva={potencia_mva}, tensao_at={tensao_at}, tensao_bt={tensao_bt}, tipo_transformador={tipo_transformador}")
    
    # Calculate currents
    try:
        if tipo_transformador == "Trifásico":
            sqrt3 = 1.732
            corrente_at = round((potencia_mva * 1000) / (sqrt3 * tensao_at), 2) if tensao_at else None
            corrente_bt = round((potencia_mva * 1000) / (sqrt3 * tensao_bt), 2) if tensao_bt else None
        else:  # Monofásico
            corrente_at = round((potencia_mva * 1000) / tensao_at, 2) if tensao_at else None
            corrente_bt = round((potencia_mva * 1000) / tensao_bt, 2) if tensao_bt else None
        
        log.info(f"Calculated currents: AT={corrente_at}A, BT={corrente_bt}A")
        return f"{corrente_at} A", f"{corrente_bt} A"
    except Exception as e:
        log.error(f"Error calculating currents: {e}")
        return "Error", "Error"

if __name__ == "__main__":
    log.info("Starting test app...")
    app.run_server(debug=True, port=8051)
