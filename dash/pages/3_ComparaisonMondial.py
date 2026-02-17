import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from pathlib import Path

# Enregistrement de la page
dash.register_page(__name__, path='/comparateur-pays', name='3. Comparateur International')

# =============================================================================
# 1. CHARGEMENT DES DONNÉES (LOCAL À LA PAGE)
# =============================================================================

# Définition du chemin relatif vers le CSV
# On remonte : pages -> dash -> Projet -> Donnees
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PATH_DATA = BASE_DIR / "Donnees" / "DonneesTemperaturePays" / "GlobalLandTemperaturesByCountry.csv"

def load_data():
    """ Charge et nettoie les données internationales """
    if not PATH_DATA.exists():
        print(f"[ERREUR] Fichier introuvable : {PATH_DATA}")
        return pd.DataFrame(columns=['dt', 'AverageTemperature', 'Country', 'Annee'])

    print(f">> [Page 3] Chargement du CSV International...")
    # On ne charge que les colonnes utiles pour optimiser la mémoire
    df = pd.read_csv(PATH_DATA, usecols=['dt', 'AverageTemperature', 'Country'])
    df['dt'] = pd.to_datetime(df['dt'])
    df['Annee'] = df['dt'].dt.year
    return df

# Chargement unique au démarrage
df_monde = load_data()
pays_disponibles = sorted(df_monde['Country'].unique()) if not df_monde.empty else []

THEME_COLOR = "#2C3E50"

# =============================================================================
# 2. LAYOUT (INTERFACE)
# =============================================================================

layout = dbc.Container([
    # En-tête
    dbc.Row([
        dbc.Col(html.H1("Comparateur Climatique International", className="mt-4 fw-bold", style={"color": THEME_COLOR}), width=12),
        dbc.Col(html.P("Analysez les tendances de température à travers le monde (Source: Berkeley Earth).", className="text-muted"), width=12)
    ]),

    # Contrôles
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Paramètres de Comparaison", className="bg-primary text-white fw-bold"),
                dbc.CardBody([
                    html.Label("1. Sélectionner les pays :", className="fw-bold"),
                    dcc.Dropdown(
                        id='selection-pays',
                        options=[{'label': p, 'value': p} for p in pays_disponibles],
                        multi=True,
                        value=['France', 'Spain', 'United States', 'China'], # Valeurs par défaut
                        className="mb-3"
                    ),

                    html.Label("2. Période :", className="fw-bold"),
                    dcc.RangeSlider(
                        id='slider-periode',
                        min=1850,
                        max=2018,
                        step=10,
                        value=[1900, 2018],
                        marks={i: str(i) for i in range(1850, 2020, 15)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ])
            ], className="shadow-sm mb-4")
        ], width=12)
    ]),

    # KPIs Dynamiques
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Pays le + Chaud (Moyenne)", className="text-muted small fw-bold"),
            html.H2(id="kpi-pays-chaud", className="text-danger fw-bold"),
            html.Small(id="kpi-val-chaud", className="text-muted")
        ])), width=12, md=4),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Pays le + Froid (Moyenne)", className="text-muted small fw-bold"),
            html.H2(id="kpi-pays-froid", className="text-info fw-bold"),
            html.Small(id="kpi-val-froid", className="text-muted")
        ])), width=12, md=4),

        dbc.Col(dbc.Card(dbc.CardBody([
            html.H6("Tendance Globale (Sélection)", className="text-muted small fw-bold"),
            html.H2(id="kpi-pays-trend", className="text-warning fw-bold"),
            html.Small("Hausse moyenne sur la période", className="text-muted")
        ])), width=12, md=4),
    ], className="mb-4"),

    # Graphique Principal
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody(dcc.Graph(id='graphique-pays-temp'))
            ], className="shadow-sm")
        ], width=12)
    ])

], fluid=True, className="bg-light pb-5")


# =============================================================================
# 3. CALLBACKS
# =============================================================================

@callback(
    [Output('graphique-pays-temp', 'figure'),
     Output('kpi-pays-chaud', 'children'), Output('kpi-val-chaud', 'children'),
     Output('kpi-pays-froid', 'children'), Output('kpi-val-froid', 'children'),
     Output('kpi-pays-trend', 'children')],
    [Input('selection-pays', 'value'),
     Input('slider-periode', 'value')]
)
def update_graph_and_kpis(pays_selectionnes, periode):
    # Sécurité : Si données vides ou pas de pays
    if df_monde.empty:
        return px.line(title="Erreur : Données introuvables"), "-", "-", "-", "-", "-"

    if not pays_selectionnes:
        return px.line(title="Veuillez sélectionner au moins un pays"), "-", "-", "-", "-", "-"

    # 1. Filtrage (Pays + Dates)
    mask = (df_monde['Country'].isin(pays_selectionnes)) & \
           (df_monde['Annee'] >= periode[0]) & \
           (df_monde['Annee'] <= periode[1])

    df_filtre = df_monde[mask].copy()

    if df_filtre.empty:
        return px.line(title="Pas de données pour cette période"), "-", "-", "-", "-", "-"

    # 2. Aggrégation annuelle pour le graphique (plus léger que mensuel)
    df_annuel = df_filtre.groupby(['Country', 'Annee'])['AverageTemperature'].mean().reset_index()

    # 3. Calcul des KPIs
    # Moyenne globale par pays sur la période sélectionnée
    moyennes_pays = df_annuel.groupby('Country')['AverageTemperature'].mean()

    # Pays le plus chaud
    if not moyennes_pays.empty:
        top_hot = moyennes_pays.idxmax()
        val_hot = moyennes_pays.max()
        top_cold = moyennes_pays.idxmin()
        val_cold = moyennes_pays.min()
    else:
        top_hot, val_hot, top_cold, val_cold = "-", 0, "-", 0

    # Tendance (Moyenne des 5 dernières années - Moyenne des 5 premières années de la sélection)
    # On prend la moyenne de tous les pays sélectionnés pour avoir une tendance globale
    debut = df_annuel[df_annuel['Annee'] <= periode[0] + 5]['AverageTemperature'].mean()
    fin = df_annuel[df_annuel['Annee'] >= periode[1] - 5]['AverageTemperature'].mean()
    delta = fin - debut
    txt_delta = f"{delta:+.1f}°C"

    # 4. Graphique
    fig = px.line(
        df_annuel,
        x='Annee',
        y='AverageTemperature',
        color='Country',
        title=f"Évolution Comparée ({periode[0]} - {periode[1]})",
        labels={'AverageTemperature': 'Temp. Moyenne (°C)', 'Annee': 'Année'},
    )
    # Utilisation d'un template standard inclus dans Plotly
    fig.update_layout(template='plotly_white', margin=dict(l=40, r=20, t=40, b=40), hovermode="x unified")

    return fig, top_hot, f"{val_hot:.1f}°C", top_cold, f"{val_cold:.1f}°C", txt_delta