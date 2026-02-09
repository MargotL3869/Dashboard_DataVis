import dash
from dash import dcc, html, Input, Output, State, ctx, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- IMPORTS ---
from utils.data_loader import get_villes, get_meteo_data
from utils.constants import (
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_CHAUD, COLOR_FROID,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, CHART_TEMPLATE
)

dash.register_page(__name__, path='/climat', name='1. Climat Local', order=1)

# --- CONFIGURATION INITIALE ---
df_villes = get_villes()
liste_regions = sorted(df_villes["Region_Assignee"].unique().tolist()) if not df_villes.empty else []
liste_regions.insert(0, "Toutes les regions")
liste_annees = list(range(2010, 2025))

# --- LAYOUT ---
layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1("Observatoire du Climat Local", className="fw-bold", style={"color": COLOR_PRIMARY}), width=8),
        dbc.Col([
            dbc.Label("Mode Elu", className="fw-bold me-2"),
            dbc.Switch(id="switch-mode-elu", value=False, className="d-inline-block", style={"transform": "scale(1.5)"})
        ], width=4, className="text-end")
    ]),

    dbc.Row([dbc.Col(dbc.Alert(id="resume-elu", color=COLOR_PRIMARY, className="shadow fw-bold", style={"fontSize": "1.1rem"}), width=12)], id="row-resume", style={"display": "none"}),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Paramètres", className="text-white fw-bold", style={"backgroundColor": COLOR_PRIMARY}),
                dbc.CardBody([
                    html.Label("1. Région :", className="fw-bold text-danger"),
                    dcc.Dropdown(id='dd-region', options=[{'label': r, 'value': r} for r in liste_regions], value="Toutes les regions", clearable=False, className="mb-3"),
                    html.Label("2. Ville :", className="fw-bold"),
                    dcc.Dropdown(id='dd-ville', options=[], value=None, placeholder="Choix de la ville...", clearable=False, searchable=True, className="mb-3"),
                    html.Hr(),
                    html.Label("Seuil Canicule :", className="fw-bold", style={"color": COLOR_DANGER}),
                    dcc.Slider(id='slider-seuil', min=25, max=40, step=1, value=30, marks={i: str(i) for i in range(25, 41, 5)}),
                    html.Label("Seuil Gel :", className="fw-bold mt-2", style={"color": COLOR_FROID}),
                    dcc.Slider(id='slider-seuil-gel', min=-15, max=0, step=1, value=0, marks={i: str(i) for i in range(-15, 6, 3)}),
                    html.Hr(),
                    html.Label("Année Zoom :", className="fw-bold"),
                    dcc.Dropdown(id='dd-annee', options=[{'label': str(a), 'value': a} for a in liste_annees], value=2023, clearable=False, className="mb-3"),
                ])
            ], className="shadow sticky-top", style={"top": "20px"})
        ], id="col-sidebar", width=12, lg=3),

        dbc.Col([
            dcc.Loading(type="circle", children=[
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([html.H6("Moyenne Annuelle", className="text-muted small fw-bold"), html.H2(id="kpi-mean", className="text-primary fw-bold")])), width=12, md=4),
                    dbc.Col(dbc.Card(dbc.CardBody([html.H6("Record Absolu", className="text-muted small fw-bold"), html.H2(id="kpi-max", className="text-danger fw-bold"), html.Small(id="kpi-max-date", className="text-muted")])), width=12, md=4),
                    dbc.Col(dbc.Card(dbc.CardBody([html.H6("Tendance", className="text-muted small fw-bold"), html.H2(id="kpi-delta", className="text-warning fw-bold"), html.Small("Evolution récente", className="text-muted small")])), width=12, md=4),
                ], className="mb-3"),

                dbc.Tabs([
                    dbc.Tab(label="Synthèse", tab_id="tab-synthese", children=[
                        dbc.Card([dbc.CardHeader("Anomalies (Warming Stripes)"), dbc.CardBody(dcc.Graph(id='g-master'))], className="mb-3 mt-3 shadow-sm border-0"),
                        dbc.Card([dbc.CardHeader("Comparatif : Ville vs Moyenne Régionale"), dbc.CardBody(dcc.Graph(id='g-compare'))], className="mb-3 shadow-sm border-0"),
                    ]),
                    dbc.Tab(label="Saisonnalité", tab_id="tab-saisons", id="tab-container-saisons", children=[
                        dbc.Card([dbc.CardHeader("Evolution par Saison"), dbc.CardBody(dcc.Graph(id='g-saisons'))], className="mb-3 mt-3 shadow-sm border-0"),
                    ]),
                    dbc.Tab(label="Détails", tab_id="tab-details", id="tab-container-details", children=[
                        dbc.Card([dbc.CardHeader("Heatmap Mensuelle"), dbc.CardBody(dcc.Graph(id='g-heatmap'))], className="shadow-sm border-0 mb-3 mt-3"),
                        dbc.Card([dbc.CardHeader("Zoom Journalier"), dbc.CardBody(dbc.Row([
                            dbc.Col(dcc.Graph(id='g-detail-ref'), width=12, lg=6),
                            dbc.Col(dcc.Graph(id='g-detail-main'), width=12, lg=6)
                        ]))], className="mb-3 shadow-sm border-0"),
                    ]),
                    dbc.Tab(label="Impacts", tab_id="tab-impacts", children=[
                        dbc.Row([
                            dbc.Col(dbc.Card([dbc.CardHeader("Jours de Canicule (Chaud)"), dbc.CardBody(dcc.Graph(id='g-simulateur'))], className="shadow-sm border-0 mb-3 mt-3"), width=12, lg=6),
                            dbc.Col(dbc.Card([dbc.CardHeader("Jours de Gel (Froid)"), dbc.CardBody(dcc.Graph(id='g-gel'))], className="shadow-sm border-0 mb-3 mt-3"), width=12, lg=6),
                        ])
                    ]),
                ], id="tabs", active_tab="tab-synthese")
            ])
        ], id="col-graphs", width=12, lg=9)
    ])
])

# --- CALLBACKS ---

@callback(
    [Output('dd-ville', 'options'), Output('dd-ville', 'value')],
    [Input('dd-region', 'value')],
    [State('dd-ville', 'value')]
)
def update_cities(region, current):
    if df_villes.empty or not region or region == "Toutes les regions":
        return [], None

    df_f = df_villes[df_villes["Region_Assignee"] == region]
    opts = [{'label': r['label'], 'value': r['label']} for _, r in df_f.sort_values("label").iterrows()]

    vals = set(o['value'] for o in opts)
    val = current if current in vals else (opts[0]['value'] if opts else None)
    return opts, val

@callback(
   [Output('g-compare', 'figure'), Output('g-master', 'figure'),
    Output('g-detail-ref', 'figure'), Output('g-detail-main', 'figure'),
    Output('g-heatmap', 'figure'), Output('g-simulateur', 'figure'), Output('g-gel', 'figure'), Output('g-saisons', 'figure'),
    Output('kpi-mean', 'children'), Output('kpi-max', 'children'), Output('kpi-max-date', 'children'), Output('kpi-delta', 'children'),
    Output('dd-annee', 'value'), Output('resume-elu', 'children'), Output('row-resume', 'style'), Output('col-sidebar', 'style'),
    Output('col-graphs', 'width'), Output('tab-container-saisons', 'style'), Output('tab-container-details', 'style')],
   [Input('dd-region', 'value'), Input('dd-ville', 'value'), Input('slider-seuil', 'value'), Input('slider-seuil-gel', 'value'),
    Input('dd-annee', 'value'), Input('g-master', 'clickData'), Input('switch-mode-elu', 'value')]
)
def update_charts(region, ville, seuil, seuil_gel, annee_dd, click_data, mode_elu):
    style_resume, style_sidebar, width_graphs, style_tabs_complex = {'display': 'none'}, {'display': 'block'}, 9, None
    annee = click_data['points'][0]['customdata'][0] if (ctx.triggered_id == 'g-master' and click_data) else annee_dd

    # 1. CHARGEMENT
    df_meteo = get_meteo_data(region)

    # Graphiques vides par défaut
    empty_outputs = [go.Figure()]*8 + ["-", "-", "-", "-", annee_dd, "", style_resume, style_sidebar, width_graphs, style_tabs_complex, style_tabs_complex]

    if df_meteo.empty or not ville:
        return empty_outputs

    try:
        # 2. FILTRAGE OPTIMISÉ SUR LA VILLE (sans .loc)
        print(f"🔍 Filtrage pour ville : {ville}")

        # CORRECTION MAJEURE : Filtrage direct avec masque booléen
        mask_ville = df_meteo['Ville'] == ville
        df_ville = df_meteo[mask_ville].copy()

        if df_ville.empty:
            print(f"❌ Ville '{ville}' introuvable dans les données")
            return empty_outputs

        # Définir Date comme index pour faciliter les opérations temporelles
        df_ville = df_ville.set_index('Date').sort_index()

        print(f"✅ {len(df_ville)} lignes pour {ville}")

        # 3. CALCULS RÉGIONAUX (Optimisé)
        # Moyenne régionale par jour
        df_reg_daily = df_meteo.groupby('Date')['Temp_C'].mean()
        df_reg_year = df_reg_daily.resample('YE').mean()

        # Moyenne ville par année
        df_vil_year = df_ville['Temp_C'].resample('YE').mean()

    except Exception as e:
        print(f"❌ Erreur critique lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        return empty_outputs

    # 4. KPI
    try:
        kpi_mean = f"{df_vil_year.mean():.1f}°C"
        val_max = df_ville['Temp_C'].max()
        date_max = df_ville['Temp_C'].idxmax()
        kpi_max = f"{val_max:.1f}°C"
        kpi_max_date = f"Le {date_max.strftime('%d/%m/%Y')}"
        delta = df_vil_year.iloc[-3:].mean() - df_vil_year.iloc[:3].mean() if len(df_vil_year) > 3 else 0
        kpi_delta = f"+{delta:.1f}°C" if delta > 0 else f"{delta:.1f}°C"
    except Exception as e:
        print(f"❌ Erreur KPI : {e}")
        kpi_mean, kpi_max, kpi_max_date, kpi_delta = "-", "-", "-", "-"

    # 5. MODE ELU
    texte_resume = ""
    if mode_elu:
        style_resume, style_sidebar, width_graphs, style_tabs_complex = {'display': 'block'}, {'display': 'none'}, 12, {'display': 'none'}

        try:
            jours_chauds = df_ville[df_ville['Temp_C'] > seuil].resample('YE')['Temp_C'].count()
            nb_jours_chauds = int(jours_chauds.iloc[-3:].mean()) if len(jours_chauds) > 3 else 0

            texte_resume = dbc.Card([
                dbc.CardHeader([html.H4(f"RAPPORT : {ville.upper()}", className="m-0 fw-bold text-white")], style={"backgroundColor": COLOR_PRIMARY}),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([html.Small("EVOLUTION T°", className="text-muted fw-bold"), html.H2(kpi_delta, className="fw-bold", style={"color": COLOR_PRIMARY})], width=4, className="text-center border-end"),
                        dbc.Col([html.Small(f"JOURS > {seuil}°C", className="text-muted fw-bold"), html.H2(str(nb_jours_chauds), className="fw-bold text-danger")], width=4, className="text-center border-end"),
                        dbc.Col([html.Small("RECORD", className="text-muted fw-bold"), html.H2(kpi_max, className="fw-bold text-warning")], width=4, className="text-center")
                    ], className="mb-4 mt-2"),
                    html.Div([html.Span("CONCLUSION : ", className="fw-bold"), f"Analyse climatique locale pour {ville}."], style={"fontSize": "1.1rem"})
                ])
            ], className="shadow-lg border-0 mb-4")
        except Exception as e:
            print(f"❌ Erreur mode élu : {e}")

    # 6. GRAPHIQUES
    try:
        # G1 Compare
        fig_c = go.Figure()
        if not mode_elu:
            fig_c.add_trace(go.Scatter(x=df_reg_year.index, y=df_reg_year, name="Moyenne Région", line=dict(color='gray', dash='dot')))
        fig_c.add_trace(go.Scatter(x=df_vil_year.index, y=df_vil_year, name=ville, line=dict(color=COLOR_PRIMARY, width=3)))
        fig_c.update_layout(template=CHART_TEMPLATE, title="Trajectoire Températures", xaxis_title="Année", yaxis_title="°C")

        # G2 Stripes
        base_mean = df_vil_year.mean()
        ano = df_vil_year - base_mean
        fig_m = go.Figure(data=[go.Bar(
            x=ano.index.year,
            y=ano,
            marker_color=[COLOR_CHAUD if x > 0 else COLOR_ACCENT for x in ano],
            customdata=[[y] for y in ano.index.year]
        )])
        fig_m.update_layout(template=CHART_TEMPLATE, xaxis_title="Année", yaxis_title="Ecart", showlegend=False)

        # G3/G4 Zoom
        df_ref = df_ville[df_ville.index.year == 2010]
        df_choix = df_ville[df_ville.index.year == int(annee)]
        fig_ref = px.line(df_ref, x=df_ref.index, y='Temp_C', title="Référence (2010)", template=CHART_TEMPLATE)
        fig_ref.update_traces(line_color="gray")
        fig_main = px.line(df_choix, x=df_choix.index, y='Temp_C', title=f"Année {annee}", template=CHART_TEMPLATE)
        fig_main.update_traces(line_color=COLOR_CHAUD)

        # G5 Heatmap
        try:
            heatmap_data = pd.pivot_table(df_ville.reset_index(), values='Temp_C', index=df_ville.index.year, columns=df_ville.index.month)
            data_ecart = heatmap_data - heatmap_data.mean()
            fig_h = px.imshow(data_ecart, color_continuous_scale="RdBu_r", origin='lower', aspect="auto", zmin=-3, zmax=3)
            fig_h.update_layout(template=CHART_TEMPLATE, xaxis_title="Mois", yaxis_title="Année")
        except:
            fig_h = go.Figure()

        # G6 Jours Canicule (CORRECTION : utilisation de DataFrame)
        days_hot_series = df_ville[df_ville['Temp_C'] > seuil].resample('YE')['Temp_C'].count()
        df_days_hot = days_hot_series.reset_index()
        df_days_hot.columns = ['Date', 'NbJours']
        df_days_hot['Annee'] = df_days_hot['Date'].dt.year

        fig_s = px.bar(df_days_hot, x='Annee', y='NbJours', color='NbJours', color_continuous_scale="OrRd")
        fig_s.update_layout(template=CHART_TEMPLATE, yaxis_title=f"Jours > {seuil}°C", coloraxis_showscale=False)

        # G7 Jours de Gel
        days_gel_series = df_ville[df_ville['Temp_C'] < seuil_gel].resample('YE')['Temp_C'].count()
        df_days_gel = days_gel_series.reset_index()
        df_days_gel.columns = ['Date', 'NbJours']
        df_days_gel['Annee'] = df_days_gel['Date'].dt.year

        fig_gel = px.bar(df_days_gel, x='Annee', y='NbJours', color='NbJours', color_continuous_scale="Blues_r")
        fig_gel.update_layout(template=CHART_TEMPLATE, yaxis_title=f"Jours < {seuil_gel}°C", coloraxis_showscale=False)

        # G8 Saisons
        df_saison = df_ville.copy()
        saison_map = {12:'Hiver', 1:'Hiver', 2:'Hiver', 3:'Printemps', 4:'Printemps', 5:'Printemps', 6:'Ete', 7:'Ete', 8:'Ete', 9:'Automne', 10:'Automne', 11:'Automne'}
        df_saison['Saison'] = df_saison.index.month.map(saison_map)
        df_saison_yearly = df_saison.groupby([df_saison.index.year, 'Saison'])['Temp_C'].mean().unstack()

        fig_saisons = go.Figure()
        for s, col_c in zip(['Hiver', 'Printemps', 'Ete', 'Automne'], [COLOR_ACCENT, COLOR_SUCCESS, COLOR_CHAUD, COLOR_WARNING]):
            if s in df_saison_yearly.columns:
                fig_saisons.add_trace(go.Scatter(x=df_saison_yearly.index, y=df_saison_yearly[s], name=s, line=dict(color=col_c)))
        fig_saisons.update_layout(template=CHART_TEMPLATE, xaxis_title="Année", yaxis_title="Température (°C)")

    except Exception as e:
        print(f"❌ Erreur génération graphiques : {e}")
        import traceback
        traceback.print_exc()
        return empty_outputs

    return (fig_c, fig_m, fig_ref, fig_main, fig_h, fig_s, fig_gel, fig_saisons,
            kpi_mean, kpi_max, kpi_max_date, kpi_delta, annee,
            texte_resume, style_resume, style_sidebar, width_graphs, style_tabs_complex, style_tabs_complex)