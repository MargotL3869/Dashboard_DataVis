import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# On l'enregistre comme la page d'accueil (path='/')
dash.register_page(__name__, path='/contexte', name='Accueil & Contexte', order=0)

layout = html.Div([
    # Titre Principal
    html.H1("Contexte du Projet : Analyse Climatique", className="mb-4"),

    # BLOC 1 : LA PROBLÉMATIQUE
    dbc.Card(
        dbc.CardBody([
            html.H4("🎯 La Problématique", className="card-title"),
            html.P(
                "Au-delà du constat local, comment l'analyse comparative multi-échelles (entre villes et entre pays)"
                "et le croisement des indicateurs (température/pluie) permettent-ils de diagnostiquer la vulnérabilité "
                "spécifique d'un territoire pour mieux cibler ses stratégies d'adaptation ?",
                className="card-text",
                style={"font-style": "italic", "font-size": "1.1rem"}
            ),
        ]),
        className="mb-4 shadow-sm" # Ajoute une petite ombre et de la marge
    ),

    # BLOC 2 : LE PERSONA
    dbc.Card(
        dbc.CardBody([
            html.H4("👤 Le Persona", className="card-title"),
            html.H6("Profil : Marc, Chargé de Mission Plan Climat", className="text-muted"),
            html.Ul([
               html.Li("Besoin : Disposer d'indicateurs fiables pour justifier les actions politiques."),
                html.Li("Contrainte : Doit pouvoir communiquer ces chiffres au grand public et aux élus simplement."),
                html.Li("Objectif : Identifier les seuils critiques (canicules, sécheresses) pour prioriser les actions."),
            ]),
        ]),
        className="mb-4 shadow-sm"
    ),

    html.Hr(),

    # BLOC 3 : GUIDE DES PAGES (Réponse à la problématique)
    html.H3("🧭 Comment ce dashboard répond à la problématique :"),
    html.Br(),

    dbc.Row([
        # Page 1
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("1. Climat Local", className="text-primary"),
            html.P("Diagnostic immédiat : Fait-il vraiment plus chaud qu'avant ici ? Analyse des températures historiques.")
        ])), width=6),

        # Page 2
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("2. Précipitations", className="text-primary"),
            html.P("Gestion de l'eau : Analyse des pluies pour anticiper les périodes de sécheresse ou d'inondation de 2010 à 2024.")
        ])), width=6),
    ], className="mb-3"),

    dbc.Row([
        # Page 3
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("3. Comparateur", className="text-primary"),
            html.P("Benchmarking : Comment notre ville se situe-t-elle par rapport aux autres villes françaises ?")
        ])), width=6),

        # Page 4
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H5("4. International", className="text-primary"),
            html.P("Perspective globale : Mise en regard des données locales avec les tendances mondiales.")
        ])), width=6),
    ])
])