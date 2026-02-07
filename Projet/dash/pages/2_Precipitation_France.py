import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import calendar
import os

dash.register_page(__name__, path='/pluie', name='2. Précipitations')

# --- 1. CONFIGURATION ET CHEMINS ---
print("🚀 Initialisation de la page Précipitations...")
# On remonte l'arborescence pour trouver le dossier Donnees
dossier_data = Path(__file__).resolve().parent.parent.parent / "Donnees"
dossier_cache = dossier_data / "DonneesTempPrecipitation"
fichier_cache = dossier_cache / "historique_pluie_v2_light.parquet"

# --- 2. CHARGEMENT DES VILLES ---
chemin_villes = dossier_data / "DonneesVilles" / "villes_avec_regions.parquet"
df_villes = pd.read_parquet(chemin_villes)
df_villes["Region_Assignee"] = df_villes["Region_Assignee"].fillna("Hors Region").astype(str).str.strip()
# Suppression des doublons (Vital pour correspondre au cache)
df_villes = df_villes.drop_duplicates(subset=['label'])

# --- 3. CHARGEMENT DU CACHE OPTIMISÉ (118 Mo) ---
df_historique_complet = None
annees_dispo = []

if fichier_cache.exists():
    print(f"   📂 Chargement du cache optimisé : {fichier_cache.name}")
    try:
        # Lecture du fichier compressé (c'est très rapide)
        df_historique_complet = pd.read_parquet(fichier_cache)

        # Récupération des années disponibles depuis l'index du fichier
        annees_dispo = sorted(df_historique_complet.index.year.unique())
        print(f"   ✅ Succès ! {len(df_historique_complet)} mois chargés en mémoire.")
    except Exception as e:
        print(f"   ❌ Erreur de lecture du cache : {e}")
        df_historique_complet = None
else:
    print(f"   ⚠️ Cache introuvable ici : {fichier_cache}")
    print("   👉 Lancez 'python generecachepluie.py' pour le créer.")

# --- 4. CHARGEMENT DE SECOURS (XARRAY) ---
# Sert uniquement si on veut des détails précis non présents dans le cache
# ou si le cache est absent.
dossier_chunks = dossier_data / "DonneesTempPrecipitation"

ds = xr.Dataset()
if df_historique_complet is None:
    # On n'ouvre Xarray que si on n'a pas le cache (fallback)
    try:
        if dossier_chunks.exists() and any(dossier_chunks.glob("*.nc")):
            print("   🐢 Mode secours : Connexion aux fichiers NetCDF...")
            ds = xr.open_mfdataset(str(dossier_chunks / "*.nc"), combine='by_coords', chunks={'time': 500})

            # Renommage standard
            renommage = {}
            if 'valid_time' in ds.dims or 'valid_time' in ds.coords: renommage['valid_time'] = 'time'
            if 'latitude' in ds.dims or 'latitude' in ds.coords: renommage['latitude'] = 'lat'
            if 'longitude' in ds.dims or 'longitude' in ds.coords: renommage['longitude'] = 'lon'
            if renommage: ds = ds.rename(renommage)

            # Récupération variable pluie pour plus tard
            var_pluie = 'tp' if 'tp' in ds else 'total_precipitation'
            if var_pluie in ds:
                ds['pluie_mm'] = ds[var_pluie] # On garde le lien lazy

                # Si pas de cache, on tente de deviner les années depuis le NetCDF
                if not annees_dispo:
                    try:
                        annees_dispo = sorted(np.unique(ds['time'].dt.year.compute().values))
                    except:
                        annees_dispo = []
    except:
        pass

# --- 5. PREPARATION DES MENUS ---
liste_regions = sorted(df_villes["Region_Assignee"].unique())
liste_regions.insert(0, "Toutes les regions")
mois_options = [{'label': calendar.month_name[i], 'value': i} for i in range(1, 13)]
# Si aucune année trouvée, on met une valeur vide
annee_options = [{'label': str(a), 'value': a} for a in annees_dispo] if annees_dispo else [{'label': "Aucune donnée", 'value': None}]
valeur_annee_defaut = annee_options[-1]['value'] if annees_dispo else None

THEME_COLOR = "#2980b9"

# --- 6. INTERFACE (LAYOUT) ---
layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1("Analyse des Précipitations", className="fw-bold", style={"color": THEME_COLOR}), width=12),
    ]),

    dbc.Row([
        # Sidebar
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Paramètres", className="text-white fw-bold", style={"backgroundColor": THEME_COLOR}),
                dbc.CardBody([
                    html.Label("1. Région :", className="fw-bold"),
                    dcc.Dropdown(id='dd-region-p', options=[{'label': r, 'value': r} for r in liste_regions], value="Toutes les regions", clearable=False, className="mb-3"),
                    html.Label("2. Ville :", className="fw-bold"),
                    dcc.Dropdown(id='dd-ville-p', options=[], value=None, placeholder="Choix de la ville...", clearable=False, className="mb-3"),

                    html.Hr(),
                    html.Label("Date à analyser (Top Ville) :", className="fw-bold text-success"),
                    dbc.Row([
                        dbc.Col(dcc.Dropdown(id='dd-mois-kpi', options=mois_options, value=11, clearable=False, placeholder="Mois"), width=7),
                        dbc.Col(dcc.Dropdown(id='dd-annee-kpi', options=annee_options, value=valeur_annee_defaut, clearable=False, placeholder="Année"), width=5),
                    ], className="mb-3"),

                    html.Hr(),
                    html.Label("Seuil Sécheresse (mm/an) :", className="fw-bold text-danger"),
                    dcc.Slider(id='slider-secheresse', min=300, max=1000, step=50, value=600, marks={i: str(i) for i in range(300, 1001, 200)}),
                ])
            ], className="shadow sticky-top", style={"top": "20px"})
        ], width=12, lg=3),

        # Contenu Principal
        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6("Moyenne Annuelle (Ville)", className="text-muted small fw-bold"),
                    html.H2(id="kpi-pluie-mean", className="text-primary fw-bold")
                ])), width=12, md=6),

                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6(id="titre-kpi-top-mois", className="text-muted small fw-bold"),
                    html.H2(id="kpi-top-mois-val", className="text-success fw-bold"),
                    html.Small(id="kpi-top-mois-nom", className="text-muted")
                ]), style={"borderLeft": "5px solid #27ae60"}), width=12, md=6),
            ], className="mb-3"),

            dbc.Card([
                dbc.CardHeader("Saisons : Quand pleut-il le plus ?"),
                dbc.CardBody(dcc.Graph(id='g-pluie-saison'))
            ], className="mb-4 shadow-sm border-0"),

            dbc.Card([
                dbc.CardHeader("Historique Annuel (Barres Rouges = Sécheresse)"),
                dbc.CardBody(dcc.Graph(id='g-pluie-annuelle'))
            ], className="mb-4 shadow-sm border-0"),

        ], width=12, lg=9)
    ])
])

# --- 7. CALLBACKS ---

@dash.callback(
    [Output('dd-ville-p', 'options'), Output('dd-ville-p', 'value')],
    [Input('dd-region-p', 'value')],
    [State('dd-ville-p', 'value')]
)
def update_cities_pluie(region, current):
    if not region: return [], None
    df_f = df_villes if region == "Toutes les regions" else df_villes[df_villes["Region_Assignee"] == region]
    df_f = df_f.sort_values("label")
    opts = [{'label': r['label'], 'value': r['label']} for _, r in df_f.iterrows()]
    vals = [o['value'] for o in opts]
    val = current if current in vals else (vals[0] if vals else None)
    return opts, val

@dash.callback(
    [Output('g-pluie-annuelle', 'figure'), Output('g-pluie-saison', 'figure'),
     Output('kpi-pluie-mean', 'children'),
     Output('kpi-top-mois-val', 'children'), Output('kpi-top-mois-nom', 'children'), Output('titre-kpi-top-mois', 'children')],
    [Input('dd-ville-p', 'value'), Input('slider-secheresse', 'value'),
     Input('dd-mois-kpi', 'value'), Input('dd-annee-kpi', 'value'), Input('dd-region-p', 'value')]
)
def update_charts_pluie(ville, seuil_sech, mois_choisi, annee_choisie, region_filter):

    # --- A. KPI TOP VILLE (Via Cache) ---
    kpi_titre, kpi_val, kpi_nom = "Données indisponibles (Lancez le générateur)", "-", "-"

    if df_historique_complet is not None and mois_choisi and annee_choisie:
        # On filtre le cache par date
        mask = (df_historique_complet.index.year == annee_choisie) & (df_historique_complet.index.month == mois_choisi)
        df_target = df_historique_complet[mask]

        if not df_target.empty:
            row_vals = df_target.iloc[0]

            # Filtre par région
            if region_filter != "Toutes les regions":
                villes_region = df_villes[df_villes["Region_Assignee"] == region_filter]['label'].values
                # Intersection des villes du cache et des villes de la région
                cols_valid = [v for v in villes_region if v in row_vals.index]
                row_vals = row_vals[cols_valid] if cols_valid else pd.Series(dtype='float32')

            if not row_vals.empty:
                max_val = row_vals.max()
                max_ville = row_vals.idxmax()
                nom_mois = calendar.month_name[mois_choisi]
                kpi_titre = f"Ville la + Humide en {nom_mois} {annee_choisie}"
                kpi_val = f"{int(max_val)} mm"
                kpi_nom = f"{max_ville} ({region_filter if region_filter != 'Toutes les regions' else 'France'})"

    # --- B. GRAPHIQUES VILLE ---
    if not ville:
        return go.Figure(), go.Figure(), "-", kpi_val, kpi_nom, kpi_titre

    ts_ville = pd.DataFrame()

    # 1. Essai lecture RAPIDE depuis le cache
    if df_historique_complet is not None and ville in df_historique_complet.columns:
        ts_ville = df_historique_complet[[ville]].rename(columns={ville: 'pluie'})

    # 2. Essai lecture LENTE depuis NetCDF (Secours)
    elif 'pluie_mm' in ds:
        try:
            row = df_villes[df_villes['label'] == ville].iloc[0]
            subset = ds['pluie_mm'].sel(lat=row['lat'], lon=row['lon'], method='nearest')
            ts_ville = subset.to_dataframe()
            if 'pluie_mm' in ts_ville.columns: ts_ville = ts_ville.rename(columns={'pluie_mm': 'pluie'})
            else: ts_ville.columns = ['pluie']
            ts_ville['pluie'] = ts_ville['pluie'] * 1000
        except:
            pass

    if ts_ville.empty:
        return go.Figure(), go.Figure(), "Err Données", kpi_val, kpi_nom, kpi_titre

    # --- C. CALCULS ET AFFICHAGE ---

    # Moyenne annuelle
    try:
        df_yearly = ts_ville.resample('YE')['pluie'].sum()
    except:
        df_yearly = ts_ville.resample('Y').sum() # Compatibilité anciennes versions pandas

    if df_yearly.empty: return go.Figure(), go.Figure(), "0 mm", kpi_val, kpi_nom, kpi_titre
    moyenne = int(df_yearly.mean())

    # Préparation Graphique Saison
    ts_ville['Mois'] = ts_ville.index.month
    ts_ville['Annee'] = ts_ville.index.year
    cumul_mensuel = ts_ville.groupby(['Annee', 'Mois'])['pluie'].sum().reset_index()
    saisonnalite = cumul_mensuel.groupby('Mois')['pluie'].mean()

    # Couleurs Saisons
    colors_saison = ['#85C1E9'] * 12
    if mois_choisi: colors_saison[mois_choisi - 1] = '#27ae60'
    mois_noms = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']

    fig_s = go.Figure(data=[go.Bar(x=mois_noms, y=saisonnalite.values, marker_color=colors_saison)])
    fig_s.update_layout(title=f"Saisonnalité : {ville}", template="plotly_white", yaxis_title="Pluie (mm)")

    # Couleurs Historique
    couleurs_hist = ['#D4AC0D' if x < seuil_sech else '#3498db' for x in df_yearly.values]

    fig_p = go.Figure(data=[go.Bar(x=df_yearly.index.year, y=df_yearly.values, marker_color=couleurs_hist)])
    fig_p.add_hline(y=seuil_sech, line_dash="dot", line_color="red", annotation_text="Seuil")
    fig_p.update_layout(template="plotly_white", xaxis_title="Année", yaxis_title="Cumul (mm)", title=f"Pluie Annuelle : {ville}")

    return fig_p, fig_s, f"{moyenne} mm/an", kpi_val, kpi_nom, kpi_titre