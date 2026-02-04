import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr
import pandas as pd
from pathlib import Path

# --- 1. ENREGISTREMENT DE LA PAGE ---
dash.register_page(__name__, path='/pluie', name='2. Précipitations')

# --- 2. CHARGEMENT DES DONNÉES ---
dossier_data = Path(__file__).resolve().parent.parent.parent / "Donnees"

# A. Chargement des Villes
chemin_villes = dossier_data / "DonneesVilles" / "villes_avec_regions.parquet"
df_villes = pd.read_parquet(chemin_villes)
df_villes["Region_Assignee"] = df_villes["Region_Assignee"].fillna("Hors Region").astype(str).str.strip()

# B. Chargement "Intelligent" de la Météo
# On cherche d'abord dans le dossier "DonneesTempPrecipitation"
dossier_chunks = dossier_data / "DonneesTempPrecipitation"
fichier_unique = dossier_data / "DonneesTemperaturePays" / "meteo_france_1950_2025.nc"

try:
    if dossier_chunks.exists() and any(dossier_chunks.glob("*.nc")):
        print("Chargement des fichiers par morceaux (Chunks)...")
        ds = xr.open_mfdataset(str(dossier_chunks / "*.nc"), parallel=True)
    else:
        print("Chargement du fichier unique...")
        ds = xr.open_dataset(fichier_unique)

    # --- C. TRAITEMENT PLUIE (Mètres -> Millimètres) ---
    var_pluie = 'tp' if 'tp' in ds else 'total_precipitation'

    # Conversion : Copernicus donne des Mètres. On veut des Millimètres (x1000)
    # On remplace les valeurs négatives (erreurs de capteur possibles) par 0
    ds['pluie_mm'] = ds[var_pluie] * 1000
    ds['pluie_mm'] = ds['pluie_mm'].where(ds['pluie_mm'] >= 0, 0)

except Exception as e:
    print(f"ERREUR CRITIQUE CHARGEMENT DONNÉES : {e}")
    # On crée un dataset vide pour ne pas faire planter l'appli au démarrage
    ds = xr.Dataset()

liste_regions = sorted(df_villes["Region_Assignee"].unique())
liste_regions.insert(0, "Toutes les regions")
THEME_COLOR = "#2980b9"

# --- 3. LAYOUT (INTERFACE) ---
layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1("Analyse des Précipitations & Sécheresses", className="fw-bold", style={"color": THEME_COLOR}), width=12),
    ]),

    dbc.Row([
        # Sidebar (Filtres spécifiques Pluie)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Paramètres Hydrologiques", className="text-white fw-bold", style={"backgroundColor": THEME_COLOR}),
                dbc.CardBody([
                    html.Label("1. Région :", className="fw-bold"),
                    dcc.Dropdown(id='dd-region-p', options=[{'label': r, 'value': r} for r in liste_regions], value="Toutes les regions", clearable=False, className="mb-3"),
                    html.Label("2. Ville :", className="fw-bold"),
                    dcc.Dropdown(id='dd-ville-p', options=[], value=None, placeholder="Choix de la ville...", clearable=False, className="mb-3"),
                    html.Hr(),
                    html.Label("Seuil Sécheresse (mm/an) :", className="fw-bold text-danger"),
                    dcc.Slider(id='slider-secheresse', min=300, max=1000, step=50, value=600, marks={i: str(i) for i in range(300, 1001, 200)}),
                    html.Div("Si le cumul annuel est inférieur à ce seuil, l'année est considérée comme sèche.", className="text-muted small mb-3"),

                    html.Label("Seuil Pluie Intense (mm/jour) :", className="fw-bold text-primary"),
                    dcc.Slider(id='slider-inondation', min=10, max=100, step=5, value=30, marks={i: str(i) for i in range(10, 101, 20)}),
                ])
            ], className="shadow sticky-top", style={"top": "20px"})
        ], width=12, lg=3),

        # Graphiques
        dbc.Col([
            # KPIs
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([html.H6("Pluie Moyenne / An", className="text-muted small fw-bold"), html.H2(id="kpi-pluie-mean", className="text-primary fw-bold")])), width=12, md=6),
                dbc.Col(dbc.Card(dbc.CardBody([html.H6("Année la plus sèche", className="text-muted small fw-bold"), html.H2(id="kpi-pluie-min", className="text-danger fw-bold"), html.Small(id="kpi-pluie-min-date", className="text-muted")])), width=12, md=6),
            ], className="mb-3"),

            # Graphiques principaux
            dbc.Card([
                dbc.CardHeader("Cumul Annuel des Précipitations (Alerte Sécheresse)"),
                dbc.CardBody(dcc.Graph(id='g-pluie-annuelle'))
            ], className="mb-4 shadow-sm border-0"),

            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Jours de Pluie Intense (> Seuil)"),
                    dbc.CardBody(dcc.Graph(id='g-pluie-intense'))
                ], className="shadow-sm border-0"), width=12, lg=6),

                dbc.Col(dbc.Card([
                    dbc.CardHeader("Saisonnalité des Pluies"),
                    dbc.CardBody(dcc.Graph(id='g-pluie-saison'))
                ], className="shadow-sm border-0"), width=12, lg=6),
            ])
        ], width=12, lg=9)
    ])
])

# --- 4. CALLBACKS ---

# Mise à jour de la liste des villes
@dash.callback(
    [Output('dd-ville-p', 'options'), Output('dd-ville-p', 'value')],
    [Input('dd-region-p', 'value')],
    [State('dd-ville-p', 'value')]
)
def update_cities_pluie(region, current):
    if not region: return [], None
    df_f = df_villes if region == "Toutes les regions" else df_villes[df_villes["Region_Assignee"] == region]
    df_f = df_f.sort_values("label").drop_duplicates(subset=["label"])
    opts = [{'label': r['label'], 'value': r['label']} for _, r in df_f.iterrows()]
    vals = [o['value'] for o in opts]
    val = current if current in vals else (vals[0] if vals else None)
    return opts, val

# Mise à jour des graphiques
@dash.callback(
    [Output('g-pluie-annuelle', 'figure'), Output('g-pluie-intense', 'figure'), Output('g-pluie-saison', 'figure'),
     Output('kpi-pluie-mean', 'children'), Output('kpi-pluie-min', 'children'), Output('kpi-pluie-min-date', 'children')],
    [Input('dd-ville-p', 'value'), Input('slider-secheresse', 'value'), Input('slider-inondation', 'value')]
)
def update_charts_pluie(ville, seuil_sech, seuil_inond):
    if not ville or 'pluie_mm' not in ds:
        return [go.Figure()]*3 + ["-", "-", "-"]

    # Extraction des données pour la ville
    row = df_villes[df_villes['label'] == ville].iloc[0]
    # On prend un petit carré autour de la ville
    subset = ds['pluie_mm'].sel(lat=slice(row['lat'] - 0.25, row['lat'] + 0.25), lon=slice(row['lon'] - 0.25, row['lon'] + 0.25))
    ts_ville = subset.mean(['lat', 'lon']).to_dataframe(name='pluie')

    # Calculs annuels (Somme des pluies)
    df_yearly = ts_ville.resample('YE')['pluie'].sum()

    # KPIS
    moyenne = df_yearly.mean()
    annee_min_val = df_yearly.min()
    annee_min_date = df_yearly.idxmin().year

    kpi_mean = f"{int(moyenne)} mm"
    kpi_min = f"{int(annee_min_val)} mm"
    kpi_date = f"en {annee_min_date}"

    # G1 : Cumul Annuel (Bar Chart avec couleur conditionnelle)
    # Si pluie < seuil sécheresse => JAUNE OCRE, sinon BLEU
    couleurs = ['#D4AC0D' if x < seuil_sech else '#3498db' for x in df_yearly.values]

    fig_p = go.Figure(data=[go.Bar(
        x=df_yearly.index.year,
        y=df_yearly.values,
        marker_color=couleurs
    )])
    fig_p.add_hline(y=seuil_sech, line_dash="dot", line_color="red", annotation_text="Seuil Sécheresse")
    fig_p.update_layout(template="plotly_white", xaxis_title="Année", yaxis_title="Cumul Pluie (mm)", title=f"Historique Pluviométrie : {ville}")

    # G2 : Jours Pluie Intense
    # On compte les jours où il a plu plus que le seuil (ex: > 30mm)
    days_intense = ts_ville[ts_ville['pluie'] > seuil_inond].resample('YE')['pluie'].count().reindex(df_yearly.index, fill_value=0)
    fig_i = px.bar(x=days_intense.index.year, y=days_intense.values, title=f"Jours > {seuil_inond}mm de pluie")
    fig_i.update_traces(marker_color="#2c3e50")
    fig_i.update_layout(template="plotly_white", xaxis_title="Année", yaxis_title="Nombre de jours")

    # G3 : Saisonnalité
    # Moyenne par mois
    df_mois = ts_ville.groupby(ts_ville.index.month)['pluie'].mean() # Moyenne mensuelle cumulée ? Non attention l'unité est mm/jour dans ERA5 souvent ou mm/h
    # ERA5 'tp' est un cumul depuis le début de la step. Ici on a pris des points quotidiens ou 6h.
    # Pour avoir des mm/mois cohérents, il faut sommer sur le mois, PUIS faire la moyenne sur les 75 ans.

    ts_ville['Mois'] = ts_ville.index.month
    ts_ville['Annee'] = ts_ville.index.year
    # On calcule d'abord le cumul total de chaque mois de chaque année
    cumul_mensuel = ts_ville.groupby(['Annee', 'Mois'])['pluie'].sum().reset_index()
    # Puis on fait la moyenne de ces cumuls pour avoir une "saisonnalité moyenne"
    saisonnalite = cumul_mensuel.groupby('Mois')['pluie'].mean()

    mois_noms = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
    fig_s = px.bar(x=mois_noms, y=saisonnalite.values, title="Saisonnalité Moyenne (mm/mois)")
    fig_s.update_traces(marker_color="#2980b9")
    fig_s.update_layout(template="plotly_white", yaxis_title="Pluie Moyenne (mm)")

    return fig_p, fig_i, fig_s, kpi_mean, kpi_min, kpi_date