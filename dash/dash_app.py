import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# On utilise un thème BOOTSTRAP pour que ce soit joli tout de suite
app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Cette ligne est CRUCIALE pour le déploiement

# --- LE STYLE CSS (Pour placer la sidebar à gauche) ---
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa", # Gris très clair
}

CONTENT_STYLE = {
    "margin-left": "20rem", # Pour ne pas être caché par la sidebar
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# --- LA BARRE LATÉRALE (Menu) ---
sidebar = html.Div(
    [
        html.H3("Météo & Climat", className="display-6"),
        html.Hr(),
        html.P(
            "Navigation", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink(
                    f"{page['name']}",
                    href=page["relative_path"],
                    active="exact"
                )
                for page in dash.page_registry.values()
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

# --- L'ORGANISATION GÉNÉRALE ---
app.layout = html.Div([
    sidebar,
    html.Div(dash.page_container, style=CONTENT_STYLE)
])

if __name__ == '__main__':
    app.run(debug=True)