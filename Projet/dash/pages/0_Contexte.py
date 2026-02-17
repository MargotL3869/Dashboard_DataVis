import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# On l'enregistre comme la page d'accueil (path='/')
dash.register_page(__name__, path='/Contexte', name='Accueil & Contexte', order=0)

layout = html.Div([
    # Titre Principal
    html.H1("Contexte du Projet : Analyse Climatique", className="mb-4"),

    # BLOC 1 : LA PROBLÉMATIQUE
    dbc.Card(
        dbc.CardBody([
            html.H4("🎯 La Problématique", className="card-title"),
            html.P(
                "Comment l'analyse comparative multi-échelles (entre villes et entre pays) "
                "permet-elle de diagnostiquer la vulnérabilité thermique d'un territoire et de situer "
                "le réchauffement local dans une perspective globale pour mieux cibler les stratégies d'adaptation ?",
                className="card-text",
                style={"font-style": "italic", "font-size": "1.1rem"}
            ),
        ]),
        className="mb-4 shadow-sm"
    ),

    # BLOC 2 : LE PERSONA
    dbc.Card(
        dbc.CardBody([
            html.H4("👤 Le Persona", className="card-title"),
            html.H6("Profil : Marc, Chargé de Mission Plan Climat", className="text-muted"),
            html.Ul([
               html.Li("Besoin : Disposer d'indicateurs de température fiables pour justifier les actions politiques."),
                html.Li("Contrainte : Doit pouvoir communiquer ces chiffres au grand public et aux élus simplement."),
                html.Li("Objectif : Comparer les trajectoires locales avec les tendances nationales et mondiales."),
            ]),
        ]),
        className="mb-4 shadow-sm"
    ),

    html.Hr(),

    # BLOC 3 : GUIDE DES PAGES
    html.H3("🧭 Parcours de l'analyse :"),
    html.Br(),

    dbc.Row([
        # Page 1
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🌡️ 1. Climat Local", className="text-primary"),
            html.P("Diagnostic territorial : Analyse précise des températures historiques pour confirmer le réchauffement à l'échelle locale.")
        ]), className="h-100"), width=4),

        # Page 2
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🏙️ 2. Comparaison Villes", className="text-primary"),
            html.P("Benchmarking National : Comment notre ville se situe-t-elle par rapport aux autres territoires français ?")
        ]), className="h-100"), width=4),

        # Page 3
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("🌍 3. International", className="text-primary"),
            html.P("Perspective Globale : Mise en regard des trajectoires climatiques françaises avec les grandes puissances mondiales.")
        ]), className="h-100"), width=4),
    ], className="mb-3"),

    html.Div([
        html.Small("⚠️ Note technique : Les données internationales sont basées sur les moyennes annuelles de température terrestre par pays.")
    ], style={'textAlign': 'center', 'color': 'gray', 'marginTop': '20px'})
])