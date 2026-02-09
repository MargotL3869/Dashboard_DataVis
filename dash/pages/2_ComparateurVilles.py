import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import du Data Loader
from utils.data_loader import load_all_data

dash.register_page(__name__, path='/comparaison', name='2. Comparaison Villes')

# =============================================================================
# 1. CHARGEMENT DES DONNÉES
# =============================================================================
ds, _, df_villes = load_all_data()

liste_regions = sorted(df_villes["Region_Assignee"].unique())
liste_regions.insert(0, "Toutes les regions")

# Années disponibles pour le zoom
liste_annees = sorted(list(set(pd.to_datetime(ds.time.values).year)))

THEME_COLOR = "#64748B"  # Gris bleuté
COLOR_A = "#2980b9"      # Bleu (Ville A)
COLOR_B = "#c0392b"      # Rouge (Ville B)

# =============================================================================
# 2. LAYOUT
# =============================================================================
layout = dbc.Container([
    # En-tête
    dbc.Row([
        dbc.Col(html.H1("Duel de Villes", className="mt-4 fw-bold", style={"color": THEME_COLOR}), width=12),
        dbc.Col(html.P("Comparez le climat de deux villes sur 75 ans (1950-2025).", className="text-muted"), width=12)
    ]),

    dbc.Row([
        # --- SIDEBAR DE SÉLECTION ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Sélection", className="text-white fw-bold", style={"backgroundColor": THEME_COLOR}),
                dbc.CardBody([
                    html.Label("1. Région (Filtre) :", className="fw-bold"),
                    dcc.Dropdown(id='comp-region', options=[{'label': r, 'value': r} for r in liste_regions], value="Toutes les regions", clearable=False, className="mb-3"),

                    html.Label("2. Ville A (Bleu) :", className="fw-bold", style={"color": COLOR_A}),
                    dcc.Dropdown(id='comp-ville-a', placeholder="Ville A...", searchable=True, className="mb-3"),

                    html.Label("3. Ville B (Rouge) :", className="fw-bold", style={"color": COLOR_B}),
                    dcc.Dropdown(id='comp-ville-b', placeholder="Ville B...", searchable=True, className="mb-3"),

                    html.Hr(),

                    # NOUVEAU : Slider Canicule
                    html.Label("4. Seuil Canicule :", className="fw-bold text-danger"),
                    dcc.Slider(id='comp-slider-seuil', min=25, max=40, step=1, value=30, marks={i: str(i) for i in range(25, 41, 5)}),

                    html.Hr(),

                    # NOUVEAU : Dropdown Année Zoom
                    html.Label("5. Année à Zoomer :", className="fw-bold"),
                    dcc.Dropdown(id='comp-year-zoom', options=[{'label': str(a), 'value': a} for a in liste_annees], value=2003, clearable=False, className="mb-3"),
                ])
            ], className="shadow sticky-top", style={"top": "20px"})
        ], width=12, lg=3),

        # --- GRAPHIQUES (AVEC ONGLETS) ---
        dbc.Col([
            dbc.Tabs([
                # ONGLET 1 : VUE D'ENSEMBLE
                dbc.Tab(label="Vue d'ensemble (75 ans)", children=[
                    html.Br(),
                    # Graphique 1 : Chronologie
                    dbc.Card([
                        dbc.CardHeader("🌡️ Évolution de la Température Moyenne Annuelle"),
                        dbc.CardBody(dcc.Graph(id='g-comp-timeline'))
                    ], className="mb-4 shadow-sm border-0"),

                    dbc.Row([
                        # Graphique 2 : Saisonnalité
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("📅 Profil Saisonnier (Moyenne Mensuelle)"),
                            dbc.CardBody(dcc.Graph(id='g-comp-saison'))
                        ], className="h-100 shadow-sm border-0"), width=12, lg=6),

                        # Graphique 3 : Extrêmes (Canicule)
                        dbc.Col(dbc.Card([
                            dbc.CardHeader("🔥 Jours de Canicule (Variable selon seuil)"),
                            dbc.CardBody(dcc.Graph(id='g-comp-hot'))
                        ], className="h-100 shadow-sm border-0"), width=12, lg=6),
                    ])
                ]),

                # ONGLET 2 : ZOOM ANNÉE (NOUVEAU)
                dbc.Tab(label="Zoom Année", children=[
                    html.Br(),
                    dbc.Card([
                        dbc.CardHeader(id="titre-zoom-annee", className="fw-bold"),
                        dbc.CardBody(dcc.Graph(id='g-comp-zoom-daily'))
                    ], className="shadow-sm border-0")
                ]),
            ])
        ], width=12, lg=9)
    ])
], fluid=True, className="bg-light pb-5")


# =============================================================================
# 3. CALLBACKS
# =============================================================================

# A. Mise à jour des listes de villes selon la région
@callback(
    [Output('comp-ville-a', 'options'), Output('comp-ville-b', 'options')],
    [Input('comp-region', 'value')]
)
def update_city_options(region):
    if not region: return [], []

    if region == "Toutes les regions":
        df_f = df_villes
    else:
        df_f = df_villes[df_villes["Region_Assignee"] == region]

    df_f = df_f.sort_values("label").drop_duplicates(subset=["label"])
    opts = [{'label': r['label'], 'value': r['label']} for _, r in df_f.iterrows()]
    return opts, opts


# B. Mise à jour des graphiques
@callback(
    [Output('g-comp-timeline', 'figure'),
     Output('g-comp-saison', 'figure'),
     Output('g-comp-hot', 'figure'),
     Output('g-comp-zoom-daily', 'figure'),
     Output('titre-zoom-annee', 'children')],
    [Input('comp-ville-a', 'value'), Input('comp-ville-b', 'value'),
     Input('comp-slider-seuil', 'value'), Input('comp-year-zoom', 'value')]
)
def update_comparison_graphs(va, vb, seuil, annee_zoom):
    empty_fig = go.Figure().add_annotation(text="Sélectionnez deux villes", showarrow=False)

    if not va or not vb:
        return empty_fig, empty_fig, empty_fig, empty_fig, "Zoom Année"

    # --- FONCTION D'EXTRACTION ---
    def extract_city_data(ville_name):
        try:
            row = df_villes[df_villes['label'] == ville_name].iloc[0]
            lat, lon = row['lat'], row['lon']
            offset = 0.25
            subset = ds['temp_c'].sel(lat=slice(lat - offset, lat + offset), lon=slice(lon - offset, lon + offset))

            if subset.isnull().all() or subset.mean().isnull():
                offset = 0.8
                subset = ds['temp_c'].sel(lat=slice(lat - offset, lat + offset), lon=slice(lon - offset, lon + offset))

            return subset.mean(['lat', 'lon']).to_dataframe(name='temp')
        except:
            return pd.DataFrame()

    df_a = extract_city_data(va)
    df_b = extract_city_data(vb)

    if df_a.empty or df_b.empty:
        return empty_fig, empty_fig, empty_fig, empty_fig, f"Zoom {annee_zoom}"

    # ==========================
    # ONGLET 1 : VUE D'ENSEMBLE
    # ==========================

    # G1 : Timeline Moyenne Annuelle
    ya = df_a.resample('YE')['temp'].mean()
    yb = df_b.resample('YE')['temp'].mean()

    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(x=ya.index, y=ya, name=va, mode='lines', line=dict(color=COLOR_A, width=2)))
    fig_time.add_trace(go.Scatter(x=yb.index, y=yb, name=vb, mode='lines', line=dict(color=COLOR_B, width=2)))
    fig_time.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=20, b=40), hovermode="x unified", title="Moyenne Annuelle")

    # G2 : Saisonnalité
    df_a['Mois'] = df_a.index.month
    df_b['Mois'] = df_b.index.month
    sa = df_a.groupby('Mois')['temp'].mean()
    sb = df_b.groupby('Mois')['temp'].mean()

    mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    fig_saison = go.Figure()
    fig_saison.add_trace(go.Scatter(x=mois_noms, y=sa, name=va, line=dict(color=COLOR_A)))
    fig_saison.add_trace(go.Scatter(x=mois_noms, y=sb, name=vb, line=dict(color=COLOR_B)))
    fig_saison.update_layout(template="plotly_white", margin=dict(l=30, r=20, t=20, b=30))

    # G3 : Jours de Canicule (Variable selon Slider)
    ha = df_a[df_a['temp'] > seuil].resample('YE')['temp'].count().reindex(ya.index, fill_value=0)
    hb = df_b[df_b['temp'] > seuil].resample('YE')['temp'].count().reindex(yb.index, fill_value=0)

    # Lissage
    ha_smooth = ha.rolling(window=5, center=True).mean()
    hb_smooth = hb.rolling(window=5, center=True).mean()

    fig_hot = go.Figure()
    fig_hot.add_trace(go.Bar(x=ha.index.year, y=ha, name=f"{va} (Brut)", marker_color=COLOR_A, opacity=0.3, showlegend=False))
    fig_hot.add_trace(go.Bar(x=hb.index.year, y=hb, name=f"{vb} (Brut)", marker_color=COLOR_B, opacity=0.3, showlegend=False))
    fig_hot.add_trace(go.Scatter(x=ha_smooth.index.year, y=ha_smooth, name=va, line=dict(color=COLOR_A, width=2)))
    fig_hot.add_trace(go.Scatter(x=hb_smooth.index.year, y=hb_smooth, name=vb, line=dict(color=COLOR_B, width=2)))
    fig_hot.update_layout(template="plotly_white", barmode='overlay', margin=dict(l=30, r=20, t=20, b=30), title=f"Jours > {seuil}°C")

    # ==========================
    # ONGLET 2 : ZOOM ANNÉE
    # ==========================

    # Filtrage sur l'année choisie
    zoom_a = df_a[df_a.index.year == int(annee_zoom)]
    zoom_b = df_b[df_b.index.year == int(annee_zoom)]

    fig_zoom = go.Figure()
    if not zoom_a.empty and not zoom_b.empty:
        fig_zoom.add_trace(go.Scatter(x=zoom_a.index, y=zoom_a['temp'], name=va, line=dict(color=COLOR_A, width=1.5)))
        fig_zoom.add_trace(go.Scatter(x=zoom_b.index, y=zoom_b['temp'], name=vb, line=dict(color=COLOR_B, width=1.5)))

        # Ajout ligne seuil
        fig_zoom.add_hline(y=seuil, line_dash="dot", line_color="red", annotation_text=f"Seuil {seuil}°C")

        fig_zoom.update_layout(
            template="plotly_white",
            title=f"Comparaison Journalière en {annee_zoom}",
            yaxis_title="Température (°C)",
            hovermode="x unified"
        )
    else:
        fig_zoom.add_annotation(text="Pas de données pour cette année", showarrow=False)

    return fig_time, fig_saison, fig_hot, fig_zoom, f"🔎 Zoom Détail : {annee_zoom}"