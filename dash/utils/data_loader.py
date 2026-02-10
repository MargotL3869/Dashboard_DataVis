import xarray as xr
import pandas as pd
from pathlib import Path
import sys

def load_all_data():
    """
    Charge l'ensemble des datasets (Villes + Météo + Poids)
    Gère les chemins, les formats et la conversion Kelvin -> Celsius.
    """
    print(">> [Data Loader] Initialisation...")

    # 1. Définition des chemins relatifs
    # On suppose que ce fichier est dans /Projet/dash/utils/
    # On remonte : utils -> dash -> Projet -> Donnees
    base_dir = Path(__file__).resolve().parent.parent.parent

    data_dir = base_dir / "Donnees"

# 2. Chargement des Villes
    chemin_villes = data_dir / "DonneesVilles" / "villes_avec_regions.parquet"

    if not chemin_villes.exists():
    # Petit tips : affiche le chemin testé pour debugger
       print(f"DEBUG: Je cherche ici -> {chemin_villes}")
       sys.exit(f"[ERREUR] Fichier villes introuvable.")

    df_villes = pd.read_parquet(chemin_villes)
    df_villes["Region_Assignee"] = df_villes["Region_Assignee"].fillna("Hors Region").astype(str).str.strip()

    # 3. Chargement Météo (Gestion de plusieurs noms possibles)
    dir_meteo = data_dir / "DonneesTemperaturePays"
    noms_possibles = ["meteo_france_1950_2025.nc", "donnees_carte_75ans_journalier.nc", "meteo_france_75ans_final.nc"]
    chemin_nc = None

    for nom in noms_possibles:
        p = dir_meteo / nom
        if p.exists():
            chemin_nc = p
            print(f">> [Data Loader] Fichier météo trouvé : {nom}")
            break

    if not chemin_nc:
        sys.exit(f"[ERREUR] Aucun fichier météo trouvé dans {dir_meteo}")

    # 4. Chargement des Poids (Weights)
    chemin_poids = dir_meteo / "weights_bool_precise.nc"
    if not chemin_poids.exists():
        # Fallback si le fichier n'est pas là
        chemin_poids = data_dir / "DonneesRegion" / "poids_regions_finie.nc"

    try:
        ds = xr.open_dataset(chemin_nc)
        # On charge les poids s'ils existent, sinon on gérera sans dans le callback
        ds_poids = xr.open_dataset(chemin_poids) if chemin_poids.exists() else xr.Dataset()
    except Exception as e:
        sys.exit(f"[ERREUR] Lecture NetCDF : {e}")

    # 5. Standardisation (Renommage lat/lon)
    if 'latitude' in ds.coords: ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})
    if 'latitude' in ds_poids.coords: ds_poids = ds_poids.rename({'latitude': 'lat', 'longitude': 'lon'})

    # 6. Conversion Kelvin -> Celsius automatique
    # On cherche la variable de température
    var_temp = 'Temperature_C' if 'Temperature_C' in ds else 't2m'

    # Si la moyenne est > 200, c'est du Kelvin, on convertit
    # On prend un échantillon pour tester
    sample_val = ds[var_temp].isel(time=0).values.flat[0]

    if sample_val > 200:
        print(">> [Data Loader] Conversion Kelvin -> Celsius effectuée.")
        ds['temp_c'] = ds[var_temp] - 273.15
    else:
        ds['temp_c'] = ds[var_temp]

    print(">> [Data Loader] Données chargées avec succès.")
    return ds, ds_poids, df_villes

