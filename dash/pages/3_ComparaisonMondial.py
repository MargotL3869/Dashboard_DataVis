import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import pandas as pd
from pathlib import Path

# Enregistrement de la page
dash.register_page(__name__, path='/comparateur-pays', name='3.Comparateur International')

# 1. Gestion du chemin robuste
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PATH_DATA = BASE_DIR / "Donnees" / "DonneesTemperaturePays" / "GlobalLandTemperaturesByCountry.csv"

def load_data():
    if not PATH_DATA.exists():
        print(f"ERREUR : Fichier introuvable à {PATH_DATA}")
        return pd.DataFrame(columns=['dt', 'AverageTemperature', 'Country', 'Annee'])

    df = pd.read_csv(PATH_DATA)
    df['dt'] = pd.to_datetime(df['dt'])
    df['Annee'] = df['dt'].dt.year
    return df

layout = html.Div([
    html.H1("Analyse Climatique Internationale", style={'textAlign': 'center'}),

    html.Div([
        html.Label("1. Sélectionnez les pays :"),
        dcc.Dropdown(
            id='selection-pays',
            options=[], # Sera rempli par le callback ci-dessous
            multi=True,
            value=['France', 'Russia', 'Canada', 'Spain'],
            className="mb-3"
        ),

        html.Label("2. Choisir la période de comparaison :"),
        dcc.RangeSlider(
            id='slider-periode',
            min=1750, # Berkeley Earth commence souvent très tôt
            max=2025,
            step=1,
            value=[1900, 1950],
            marks={i: str(i) for i in range(1750, 2050, 25)},
            tooltip={"placement": "bottom", "always_visible": True}
        ),
    ], style={'width': '80%', 'margin': 'auto', 'padding': '20px'}),

    dcc.Graph(id='graphique-pays-temp'),
])

# CALLBACK 1 : Pour remplir la liste des pays au chargement de la page
@callback(
    Output('selection-pays', 'options'),
    Input('selection-pays', 'id') # Se déclenche une fois à l'apparition du dropdown
)
def fill_dropdown(_):
    df = load_data()
    if df.empty:
        return []
    pays_disponibles = sorted(df['Country'].unique())
    return [{'label': p, 'value': p} for p in pays_disponibles]

# CALLBACK 2 : Pour mettre à jour le graphique
@callback(
    Output('graphique-pays-temp', 'figure'),
    [Input('selection-pays', 'value'),
     Input('slider-periode', 'value')]
)
def update_graph(pays_selectionnes, periode):
    df = load_data()

    if df.empty or not pays_selectionnes:
        return px.line(title="Aucune donnée ou aucun pays sélectionné")

    # Masques
    mask = (df['Country'].isin(pays_selectionnes)) & \
           (df['Annee'] >= periode[0]) & \
           (df['Annee'] <= periode[1])

    df_filtre = df[mask]

    # Aggrégation annuelle
    df_annuel = df_filtre.groupby(['Country', 'Annee'])['AverageTemperature'].mean().reset_index()

    fig = px.line(
        df_annuel,
        x='Annee',
        y='AverageTemperature',
        color='Country',
        title=f"Évolution des températures ({periode[0]} - {periode[1]})",
        labels={'AverageTemperature': 'Temp. Moyenne (°C)', 'Annee': 'Année'},
        template='plotly_white'
    )

    return fig