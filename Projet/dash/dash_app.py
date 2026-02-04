import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# 1. Activation du mode "Pages"
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.LUMEN])

# 2. Création du Menu latéral (Sidebar)
sidebar = dbc.Card([
    dbc.CardBody([
        html.H4("🌍 Observatoire", className="fw-bold text-primary mb-3"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page['name'], href=page['path'], active="exact", className="mb-2 text-dark fw-bold")
                for page in dash.page_registry.values()
            ],
            vertical=True,
            pills=True,
        ),
    ])
], className="vh-100 shadow-sm border-0", style={"backgroundColor": "#f8f9fa"})

# 3. Layout principal (Menu à gauche + Contenu de la page à droite)
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(sidebar, width=2, className="p-0 sticky-top"),

        dbc.Col(dash.page_container, width=10, className="p-4")
    ])
], fluid=True, className="g-0")

if __name__ == '__main__':
    app.run(debug=True)