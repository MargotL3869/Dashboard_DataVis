import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
import gc
import os
import time

print("🚀 Démarrage de la compression ULTRA-LÉGÈRE (V4 - Nouveau Nom)...")

# --- 1. DÉTECTION INTELLIGENTE DU DOSSIER ---
dossier_script = Path(__file__).resolve().parent

# On cherche "Donnees"
chemin_1 = dossier_script / "Donnees"         # Cas : script à la racine
chemin_2 = dossier_script.parent / "Donnees"  # Cas : script dans un sous-dossier

if chemin_1.exists():
    BASE_DIR = chemin_1
elif chemin_2.exists():
    BASE_DIR = chemin_2
else:
    print("❌ ERREUR FATALE : Dossier 'Donnees' introuvable.")
    exit()

# --- 2. CHEMINS ---
FILE_VILLES = BASE_DIR / "DonneesVilles" / "villes_avec_regions.parquet"
DIR_METEO = BASE_DIR / "DonneesTempPrecipitation"

DIR_CACHE = BASE_DIR / "Cache_System"
os.makedirs(DIR_CACHE, exist_ok=True)

# NOUVEAU NOM POUR ÉVITER LES CONFUSIONS
OUTPUT_FILE = DIR_CACHE / "historique_pluie_v2_light.parquet"

def main():
    start_time = time.time()

    # --- 3. CHARGEMENT VILLES ---
    print(f"\n📍 Villes : {FILE_VILLES.name}")
    if not FILE_VILLES.exists(): return
    df_villes = pd.read_parquet(FILE_VILLES)
    df_villes = df_villes.drop_duplicates(subset=['label']) # Vital
    print(f"   ✅ {len(df_villes)} villes chargées.")

    # --- 4. CHARGEMENT MÉTÉO ---
    print(f"\n🌦️  Météo : {DIR_METEO.name}")
    if not list(DIR_METEO.glob("*.nc")): return

    ds = xr.open_mfdataset(str(DIR_METEO / "*.nc"), combine='by_coords', chunks={'time': 500})

    # Renommage
    renommage = {}
    if 'valid_time' in ds.dims or 'valid_time' in ds.coords: renommage['valid_time'] = 'time'
    if 'latitude' in ds.dims or 'latitude' in ds.coords: renommage['latitude'] = 'lat'
    if 'longitude' in ds.dims or 'longitude' in ds.coords: renommage['longitude'] = 'lon'
    if renommage: ds = ds.rename(renommage)

    var_pluie = 'tp' if 'tp' in ds else 'total_precipitation'

    # Dates
    try:
        annees = sorted(np.unique(ds['time'].dt.year.compute().values))
        print(f"   📅 Années : {annees[0]} - {annees[-1]}")
    except:
        return

    tgt_lat = xr.DataArray(df_villes['lat'].values, dims="city")
    tgt_lon = xr.DataArray(df_villes['lon'].values, dims="city")

    print("\n🏗️  Compression FLOAT16 (Année par Année)...")
    dfs_yearly = []

    for year in annees:
        t0 = time.time()
        print(f"   -> {year}...", end=" ", flush=True)

        try:
            ds_year = ds[var_pluie].sel(time=str(year))
            ds_geo = ds_year.sel(lat=tgt_lat, lon=tgt_lon, method='nearest')
            ds_monthly = ds_geo.resample(time='1ME').sum()

            df_year = ds_monthly.to_pandas()
            df_year = df_year * 1000

            # --- FORCE LE FLOAT16 (DIVISE TAILLE PAR 2) ---
            df_year = df_year.astype('float16')
            # ----------------------------------------------

            df_year.columns = df_villes['label'].values
            dfs_yearly.append(df_year)

            del ds_year, ds_geo, ds_monthly, df_year
            gc.collect()
            print(f"OK ({time.time() - t0:.1f}s)")

        except Exception as e:
            print(f"ERREUR : {e}")

    # --- 5. SAUVEGARDE ---
    if dfs_yearly:
        print(f"\n💾 Fusion...")
        df_final = pd.concat(dfs_yearly)
        df_final[df_final < 0] = 0

        print(f"   💾 Écriture : {OUTPUT_FILE.name}")
        df_final.to_parquet(OUTPUT_FILE, compression='zstd')

        taille_mo = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"\n🎉 SUCCÈS ! Taille : {taille_mo:.2f} Mo")

        if taille_mo < 100:
            print("✅ Objectif < 100 Mo atteint !")
        else:
            print("⚠️ Bizarre, toujours lourd.")

    ds.close()

if __name__ == "__main__":
    main()