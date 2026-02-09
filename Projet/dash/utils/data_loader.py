import pandas as pd
from pathlib import Path
import os

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Donnees"
DIR_REGIONS = BASE_DIR / "DonneesRegions"
FILE_VILLES = BASE_DIR / "DonneesVilles" / "villes_avec_regions.parquet"

# --- CACHE MÉMOIRE ---
# Pour éviter de recharger le fichier si on clique 2 fois de suite sur la même région
_cache_villes = None
_cache_meteo_current = None
_current_region_name = None

def clean_filename(name):
    """ Nettoie le nom pour trouver le fichier (doit correspondre au découpeur) """
    if name is None:
        return ""
    name = str(name).replace(" ", "").replace("'", "").replace("-", "")
    return "".join(c for c in name if c.isalnum())

def get_villes():
    """ Charge la liste des villes (Léger) """
    global _cache_villes
    if _cache_villes is None:
        if FILE_VILLES.exists():
            df = pd.read_parquet(FILE_VILLES)
            df["Region_Assignee"] = df["Region_Assignee"].fillna("Hors Region").astype(str).str.strip()
            # On ne garde que les communes uniques utiles
            _cache_villes = df[df["Region_Assignee"] != "Hors Region"].drop_duplicates(subset=['label'])
        else:
            print(f"⚠️ Fichier villes introuvable : {FILE_VILLES}")
            return pd.DataFrame()
    return _cache_villes

def get_meteo_data(region="Toutes les regions"):
    """
    Charge le fichier correspondant à la région.
    OPTIMISATION : Retourne les données avec 'Ville' en COLONNE (pas en index)
    """
    global _cache_meteo_current, _current_region_name

    # 1. Si on a déjà chargé cette région, on renvoie le cache (0 seconde)
    if region == _current_region_name and _cache_meteo_current is not None:
        return _cache_meteo_current

    # 2. Cas "Toutes les régions" -> On renvoie VIDE pour éviter de charger 6Go
    if region == "Toutes les regions" or not region:
        return pd.DataFrame(columns=['Date', 'Ville', 'Temp_C', 'Pluie_mm'])

    # 3. Chargement du fichier régional
    filename = f"meteo_{clean_filename(region)}.parquet"
    filepath = DIR_REGIONS / filename

    if filepath.exists():
        print(f"🔥 Chargement optimisé : {filename} ...")
        try:
            # CORRECTION : On lit avec engine='fastparquet' OU 'pyarrow'
            try:
                df = pd.read_parquet(filepath, engine='fastparquet')
            except:
                # Fallback sur pyarrow si fastparquet n'est pas dispo
                df = pd.read_parquet(filepath, engine='pyarrow')

            # Typage dates
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            # IMPORTANT : On s'assure que Ville est une COLONNE
            if df.index.name == 'Ville':
                df = df.reset_index()

            # Conversion des types pour optimiser la mémoire
            if 'Ville' in df.columns:
                df['Ville'] = df['Ville'].astype('category')

            if 'Temp_C' in df.columns:
                df['Temp_C'] = pd.to_numeric(df['Temp_C'], errors='coerce')

            if 'Pluie_mm' in df.columns:
                df['Pluie_mm'] = pd.to_numeric(df['Pluie_mm'], errors='coerce')

            # Mise à jour du cache
            _cache_meteo_current = df
            _current_region_name = region

            print(f"✅ Chargé : {len(df)} lignes, {df['Ville'].nunique() if 'Ville' in df.columns else 0} villes")
            return df

        except Exception as e:
            print(f"❌ Erreur lecture fichier {filename}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=['Date', 'Ville', 'Temp_C', 'Pluie_mm'])
    else:
        print(f"⚠️ Fichier introuvable : {filepath}")
        return pd.DataFrame(columns=['Date', 'Ville', 'Temp_C', 'Pluie_mm'])