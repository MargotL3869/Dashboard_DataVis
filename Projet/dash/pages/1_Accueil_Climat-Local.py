import dash
from dash import dcc, html, Input, Output, ctx, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import du Data Loader
from utils.data_loader import load_all_data

dash.register_page(__name__, path='/climat', name='1. Climat Local')

# =============================================================================
# 1. CHARGEMENT DES DONNÉES (VIA DATA LOADER)
# =============================================================================

# Appel unique à la fonction de chargement
ds, ds_poids, df_villes = load_all_data()

# Préparation des listes pour l'interface
liste_regions = sorted(df_villes["Region_Assignee"].unique())
liste_regions.insert(0, "Toutes les regions")

# Récupération des années depuis le Dataset météo
liste_annees = sorted(list(set(pd.to_datetime(ds.time.values).year)))
premiere_annee_dispo = liste_annees[0]

THEME_COLOR = "#64748B"

# =============================================================================
# 2. INTERFACE UTILISATEUR (LAYOUT)
# =============================================================================

layout = dbc.Container([
    # En-tête
    dbc.Row([
        dbc.Col(html.H1("Observatoire du Climat Local", className="mt-4 fw-bold", style={"color": THEME_COLOR}), width=8),
        dbc.Col([
            dbc.Label("Mode Elu", className="fw-bold me-2"),
            dbc.Switch(id="switch-mode-elu", value=False, className="d-inline-block", style={"transform": "scale(1.5)"})
        ], width=4, className="text-end mt-4")
    ]),

    dbc.Row([dbc.Col(dbc.Alert("Visualisez l'evolution climatique de votre ville (1950-2025)", color="#727F92"), width=12)]),

    # Résumé Élu (Caché par défaut)
    dbc.Row([dbc.Col(dbc.Alert(id="resume-elu", color="#64748B", className="shadow fw-bold", style={"fontSize": "1.1rem"}), width=12)], id="row-resume", style={"display": "none"}),

    dbc.Row([
        # Sidebar (Filtres)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Parametres", className="text-white fw-bold", style={"backgroundColor": THEME_COLOR}),
                dbc.CardBody([
                    html.Label("1. Region :", className="fw-bold"),
                    dcc.Dropdown(id='dd-region', options=[{'label': r, 'value': r} for r in liste_regions], value="Toutes les regions", clearable=False, className="mb-3"),
                    html.Label("2. Ville :", className="fw-bold"),
                    dcc.Dropdown(id='dd-ville', options=[], value=None, placeholder="Cherchez votre ville...", clearable=False, searchable=True, className="mb-3"),
                    html.Hr(),
                    html.Label("3. Seuil Canicule :", className="fw-bold text-danger"),
                    dcc.Slider(id='slider-seuil', min=25, max=40, step=1, value=30, marks={i: str(i) for i in range(25, 41, 5)}),

                    # --- C'EST ICI QU'IL MANQUAIT LE SLIDER GEL ---
                    html.Label("4. Seuil Gel :", className="fw-bold text-info mt-3"),
                    dcc.Slider(id='slider-gel', min=-20, max=0, step=1, value=0, marks={i: str(i) for i in range(0, -21, -5)}),

                    html.Hr(),

                    html.Label("5. Annee Zoom :", className="fw-bold"),
                    dcc.Dropdown(id='dd-annee', options=[{'label': str(a), 'value': a} for a in liste_annees], value=2003, clearable=False, className="mb-3"),
                ])
            ], className="shadow sticky-top", style={"top": "20px"})
        ], id="col-sidebar", width=12, lg=3),

        # Visualisations (Graphiques)
        dbc.Col([
            # KPIs
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([html.H6("Moyenne Annuelle", className="text-muted small fw-bold"), html.H2(id="kpi-mean", className="text-primary fw-bold")])), width=12, md=4),
                dbc.Col(dbc.Card(dbc.CardBody([html.H6("Record Absolu", className="text-muted small fw-bold"), html.H2(id="kpi-max", className="text-danger fw-bold"), html.Small(id="kpi-max-date", className="text-muted")])), width=12, md=4),
                dbc.Col(dbc.Card(dbc.CardBody([html.H6("Rechauffement (+75 ans)", className="text-muted small fw-bold"), html.H2(id="kpi-delta", className="text-warning fw-bold"), html.Small("Difference 2020-25 vs 1950-55", className="text-muted small")])), width=12, md=4),
            ], className="mb-3"),

            # ONGLETS
            html.Div([
                dbc.Tabs([
                    dbc.Tab(label="Synthese", tab_id="tab-synthese", children=[
                        dbc.Card([dbc.CardHeader("Anomalies (Warming Stripes)"), dbc.CardBody(dcc.Graph(id='g-master'))], className="mb-3 mt-3 shadow-sm border-0"),
                        dbc.Card([dbc.CardHeader("Comparatif : Ville vs Moyenne Regionale"), dbc.CardBody(dcc.Graph(id='g-compare'))], className="mb-3 shadow-sm border-0"),
                    ]),

                    dbc.Tab(label="Saisonnalite", tab_id="tab-saisons", id="tab-container-saisons", children=[
                        dbc.Card([dbc.CardHeader("Evolution par Saison"), dbc.CardBody(dcc.Graph(id='g-saisons'))], className="mb-3 mt-3 shadow-sm border-0"),
                    ]),

                    dbc.Tab(label="Details", tab_id="tab-details", id="tab-container-details", children=[
                        dbc.Card([dbc.CardHeader("Heatmap Mensuelle"), dbc.CardBody(dcc.Graph(id='g-heatmap'))], className="shadow-sm border-0 mb-3 mt-3"),
                        dbc.Card([dbc.CardHeader("Zoom Journalier"), dbc.CardBody(dbc.Row([
                            dbc.Col(dcc.Graph(id='g-detail-ref'), width=12, lg=6),
                            dbc.Col(dcc.Graph(id='g-detail-main'), width=12, lg=6)
                        ]))], className="mb-3 shadow-sm border-0"),
                    ]),

                  dbc.Tab(label="Impacts", tab_id="tab-impacts", children=[
                        dbc.Row([
                            # Carte Canicule
                            dbc.Col(dbc.Card([
                                dbc.CardHeader("Jours de Canicule (Chaud)"),
                                dbc.CardBody(dcc.Graph(id='g-simulateur'))
                            ], className="shadow-sm border-0 mb-3 mt-3"), width=12, lg=6),

                            # Carte Gel (CORRIGÉ : Elle est ajoutée ici !)
                            dbc.Col(dbc.Card([
                                dbc.CardHeader("Jours de Gel (Froid)"),
                                dbc.CardBody(dcc.Graph(id='g-gel'))
                            ], className="shadow-sm border-0 mb-3 mt-3"), width=12, lg=6),
                        ])
                    ]),
                ], id="tabs", active_tab="tab-synthese")
            ], id="tabs-container")

        ], id="col-graphs", width=12, lg=9)
    ])
], fluid=True, className="bg-light pb-5")

# =============================================================================
# 3. CALLBACKS
# =============================================================================

# Gestion Villes (Mise à jour du dropdown ville selon la région)
@dash.callback(
    [Output('dd-ville', 'options'), Output('dd-ville', 'value')],
    [Input('dd-region', 'value')],
    [State('dd-ville', 'value')]
)
def update_cities(region, current):
    if not region: return [], None
    if region == "Toutes les regions":
        df_f = df_villes
    else:
        df_f = df_villes[df_villes["Region_Assignee"] == region]

    df_f = df_f.sort_values("label").drop_duplicates(subset=["label"])
    opts = [{'label': r['label'], 'value': r['label']} for _, r in df_f.iterrows()]
    vals = [o['value'] for o in opts]
    val = current if current in vals else (vals[0] if vals else None)
    return opts, val

# Callback Principal (Mise à jour des graphiques)
@dash.callback(
   [Output('g-compare', 'figure'), Output('g-master', 'figure'),
    Output('g-detail-ref', 'figure'), Output('g-detail-main', 'figure'),
    Output('g-heatmap', 'figure'), Output('g-simulateur', 'figure'),
    Output('g-gel', 'figure'),
    Output('g-saisons', 'figure'),
    Output('kpi-mean', 'children'), Output('kpi-max', 'children'), Output('kpi-max-date', 'children'), Output('kpi-delta', 'children'),
    Output('dd-annee', 'value'),
    Output('resume-elu', 'children'),
    Output('row-resume', 'style'),
    Output('col-sidebar', 'style'),
    Output('col-graphs', 'width'),
    Output('tab-container-saisons', 'style'),
    Output('tab-container-details', 'style')],
   [Input('dd-region', 'value'), Input('dd-ville', 'value'),
    Input('slider-seuil', 'value'), Input('slider-gel', 'value'), Input('dd-annee', 'value'),
    Input('g-master', 'clickData'), Input('switch-mode-elu', 'value')]
)
def update_charts(region, ville, seuil, seuil_gel, annee_dd, click_data, mode_elu):
    # --- STYLE PAR DEFAUT ---
    style_resume = {'display': 'none'}
    style_sidebar = {'display': 'block'}
    width_graphs = 9
    style_tabs_complex = None
    texte_resume = ""

    if not ville:
        empty = go.Figure()
        return [empty]*7 + ["-", "-", "-", "-", annee_dd, "", style_resume, style_sidebar, width_graphs, style_tabs_complex, style_tabs_complex]

    annee = click_data['points'][0]['customdata'] if (ctx.triggered_id == 'g-master' and click_data) else annee_dd

    # 1. DONNÉES
    try:
        # Calcul Région (Pondération ou Moyenne simple)
        if region != "Toutes les regions" and 'weights' in ds_poids and region in ds_poids.coords.get('region', []):
             mask_data = ds_poids['weights'].sel(region=region)
             # On utilise 'temp_c' qui a été créé par le data_loader
             df_reg = (ds['temp_c'] * mask_data).sum(['lat', 'lon']) / mask_data.sum(['lat', 'lon'])
        else:
             df_reg = ds['temp_c'].mean(['lat', 'lon'])

        df_reg = df_reg.to_dataframe(name='temp').resample('YE')['temp'].mean()

        # Calcul Ville
        row = df_villes[df_villes['label'] == ville].iloc[0]
        t_lat, t_lon = row['lat'], row['lon']
        offset = 0.25
        subset = ds['temp_c'].sel(lat=slice(t_lat - offset, t_lat + offset), lon=slice(t_lon - offset, t_lon + offset))

        # Gestion des points en mer ou vides
        if subset.isnull().all() or subset.mean().isnull():
            offset = 0.8
            subset = ds['temp_c'].sel(lat=slice(t_lat - offset, t_lat + offset), lon=slice(t_lon - offset, t_lon + offset))

        ts_ville = subset.mean(['lat', 'lon']).to_dataframe(name='temp')
        df_vil_year = ts_ville.resample('YE')['temp'].mean()

    except Exception as e:
        print(f"Erreur calculs : {e}")
        err = go.Figure().add_annotation(text="Donnees indisponibles", showarrow=False)
        return [err]*7 + ["Err", "Err", "-", "Err", annee, "", style_resume, style_sidebar, width_graphs, style_tabs_complex, style_tabs_complex]

    # Calcul des KPIs
    kpi_mean = f"{df_vil_year.mean():.1f}°C"
    val_max = ts_ville['temp'].max()
    kpi_max = f"{val_max:.1f}°C"
    kpi_max_date = f"Le {ts_ville['temp'].idxmax().strftime('%d/%m/%Y')}"
    delta = df_vil_year.iloc[-5:].mean() - df_vil_year.iloc[:5].mean()
    kpi_delta = f"+{delta:.1f}°C" if delta > 0 else f"{delta:.1f}°C"

    # --- MODE ÉLU (Logique métier inchangée) ---
    if mode_elu:
        style_resume = {'display': 'block'}
        style_sidebar = {'display': 'none'}
        width_graphs = 12
        style_tabs_complex = {'display': 'none'}

        nb_jours_chauds = int(ts_ville[ts_ville['temp'] > seuil].resample('YE')['temp'].count().iloc[-5:].mean())
        jours_ete = ts_ville[ts_ville['temp'] > 25].resample('YE')['temp'].count()
        gain_ete = int(jours_ete.iloc[-10:].mean() - jours_ete.iloc[:10].mean())
        txt_ete = f"+{gain_ete} jours" if gain_ete > 0 else f"{gain_ete} jours"
        annee_record = ts_ville['temp'].idxmax().year
        couleur_cadre = "#64748B"

        texte_resume = dbc.Card([
            dbc.CardHeader([
                html.H4(f"RAPPORT CLIMATIQUE : {ville.upper()}", className="m-0 fw-bold text-white", style={"letterSpacing": "1px"})
            ], style={"backgroundColor": couleur_cadre, "borderBottom": "none", "borderRadius": "5px 5px 0 0"}),

            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Small("TENDANCE (1950-2025)", className="text-muted fw-bold small"),
                        html.H2(kpi_delta, className="fw-bold", style={"color": couleur_cadre}),
                        html.Small("Hausse température moyenne", className="text-muted")
                    ], width=12, md=4, className="text-center border-end"),

                    dbc.Col([
                        html.Small(f"JOURS > {seuil}°C / AN", className="text-muted fw-bold small"),
                        html.H2(str(nb_jours_chauds), className="fw-bold text-danger"),
                        html.Small("Moyenne actuelle (récente)", className="text-muted")
                    ], width=12, md=4, className="text-center border-end"),

                    dbc.Col([
                        html.Small("ALLONGEMENT ÉTÉ", className="text-muted fw-bold small"),
                        html.H2(txt_ete, className="fw-bold text-warning"),
                        html.Small("Jours > 25°C vs 1950", className="text-muted")
                    ], width=12, md=4, className="text-center")
                ], className="mb-4 mt-2"),
                html.Hr(),
                html.Div([
                    html.Span("CONCLUSION : ", className="fw-bold", style={"color": couleur_cadre}),
                    f"Les données confirment une transformation majeure du climat local. ",
                    f"Le record historique de {kpi_max} ({annee_record}) n'est plus une anomalie isolée. ",
                    html.B("Les infrastructures actuelles doivent être adaptées à cette nouvelle normalité.")
                ], style={"fontSize": "1.1rem", "lineHeight": "1.5"})
            ])
        ], className="shadow-lg border-0 mb-4")

    # --- GRAPHIQUES ---

    # G1 Compare
    fig_c = go.Figure()
    if not mode_elu:
        fig_c.add_trace(go.Scatter(x=df_reg.index, y=df_reg, name=f"Moyenne Region", line=dict(color='gray', dash='dot')))
    width_line = 5 if mode_elu else 3
    fig_c.add_trace(go.Scatter(x=df_vil_year.index, y=df_vil_year, name=ville, line=dict(color='#2c3e50', width=width_line)))
    fig_c.update_layout(template="plotly_white", title="Trajectoire Temperatures", xaxis_title="Annee", yaxis_title="°C", margin=dict(l=40, r=20, t=40, b=40))

    # G2 Warming Stripes
    ano = df_vil_year - df_vil_year['1950':'1980'].mean()
    colors = ['#e74c3c' if x > 0 else '#3498db' for x in ano]
    fig_m = go.Figure(data=[go.Bar(x=ano.index.year, y=ano, marker_color=colors)])
    fig_m.update_layout(template="plotly_white", xaxis_title="Annee", yaxis_title="Ecart", showlegend=False, margin=dict(l=40, r=20, t=20, b=40))

    # G3/G4 Zoom
    df_ref = ts_ville[ts_ville.index.year == premiere_annee_dispo]
    if df_ref.empty:
        try: df_ref = ts_ville[ts_ville.index.year == ts_ville.index.year[0]]
        except: pass
    df_choix = ts_ville[ts_ville.index.year == annee]

    # Calcul dynamique des échelles Y
    vr, vc = df_ref['temp'].dropna(), df_choix['temp'].dropna()
    min_y = min(vr.min(), vc.min()) - 2 if not vr.empty and not vc.empty else 0
    max_y = max(vr.max(), vc.max()) + 2 if not vr.empty and not vc.empty else 40

    fig_ref = px.line(df_ref, x=df_ref.index, y='temp', title=f"Ref ({premiere_annee_dispo})")
    fig_ref.update_layout(template="plotly_white", yaxis_range=[min_y, max_y], height=300, margin=dict(l=40, r=20, t=40, b=40))
    fig_main = px.line(df_choix, x=df_choix.index, y='temp', title=f"Annee {annee}")
    fig_main.add_hline(y=seuil, line_dash="dash", line_color="red")
    fig_main.update_layout(template="plotly_white", yaxis_range=[min_y, max_y], height=300, margin=dict(l=40, r=20, t=40, b=40))

    # G5 Heatmap
    hm = ts_ville.copy()
    hm['Year'], hm['Mois'] = hm.index.year, hm.index.month
    data_brute = hm.groupby(['Year', 'Mois'])['temp'].mean().unstack()
    ref_period = hm[(hm['Year'] >= 1950) & (hm['Year'] <= 1980)]
    data_ecart = data_brute - ref_period.groupby('Mois')['temp'].mean().values
    fig_h = px.imshow(data_ecart, color_continuous_scale="RdBu_r", origin='lower', aspect="auto", zmin=-4, zmax=4)
    fig_h.update_layout(template="plotly_white", height=400, margin=dict(l=40, r=20, t=20, b=40))

    # G6 Jours Canicule
    days = ts_ville[ts_ville['temp'] > seuil].resample('YE')['temp'].count().reindex(df_vil_year.index, fill_value=0)
    fig_s = px.bar(x=days.index.year, y=days.values, color=days.values, color_continuous_scale="OrRd")
    fig_s.update_layout(template="plotly_white", xaxis_title="Annee", yaxis_title="Jours > seuil", margin=dict(l=40, r=20, t=20, b=40))

    days_gel = ts_ville[ts_ville['temp'] < seuil_gel].resample('YE')['temp'].count().reindex(df_vil_year.index, fill_value=0)
    fig_gel = px.bar(x=days_gel.index.year, y=days_gel.values, color=days_gel.values, color_continuous_scale="Blues_r")
    fig_gel.update_layout(template="plotly_white", title=f"Jours < {seuil_gel}°C", xaxis_title="Année", yaxis_title="Jours", margin=dict(l=40, r=20, t=40, b=40))

    # G8 Saisons
    df_saison = ts_ville.copy()
    saison_map = {12:'Hiver', 1:'Hiver', 2:'Hiver', 3:'Printemps', 4:'Printemps', 5:'Printemps', 6:'Ete', 7:'Ete', 8:'Ete', 9:'Automne', 10:'Automne', 11:'Automne'}
    df_saison['Saison'] = df_saison.index.month.map(saison_map)
    df_saison_yearly = df_saison.groupby([df_saison.index.year, 'Saison'])['temp'].mean().unstack()
    fig_saisons = go.Figure()
    for s in ['Hiver', 'Printemps', 'Ete', 'Automne']:
        if s in df_saison_yearly.columns:
            fig_saisons.add_trace(go.Scatter(x=df_saison_yearly.index, y=df_saison_yearly[s], name=s, mode='lines'))
    fig_saisons.update_layout(template="plotly_white", xaxis_title="Annee", margin=dict(l=40, r=20, t=20, b=40))

    return (fig_c, fig_m, fig_ref, fig_main, fig_h, fig_s, fig_gel, fig_saisons,
            kpi_mean, kpi_max, kpi_max_date, kpi_delta, annee,
            texte_resume, style_resume, style_sidebar, width_graphs, style_tabs_complex, style_tabs_complex)