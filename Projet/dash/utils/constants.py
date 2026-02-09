# utils/constants.py

# --- COULEURS DU THÈME ---
COLOR_PRIMARY = "#2C3E50"    # Bleu nuit (Titres, cadres)
COLOR_ACCENT = "#2980b9"     # Bleu roi (Boutons)

# --- COULEURS MÉTIER ---
COLOR_CHAUD = "#e74c3c"      # Rouge (Température chaude)
COLOR_FROID = "#3498db"      # Bleu clair (Gel, Froid)  <-- C'est celle-ci qui manquait !
COLOR_PLUIE = "#2980b9"      # Bleu pluie
COLOR_SUCCESS = "#27ae60"    # Vert
COLOR_WARNING = "#f39c12"    # Orange
COLOR_DANGER = "#c0392b"     # Rouge foncé

# --- CONFIGURATION GRAPHIQUES ---
CHART_TEMPLATE = "plotly_white"

# Config pour enlever la barre d'outils au survol des graphes
CHART_CONFIG = {
    'displayModeBar': False,
    'scrollZoom': False
}