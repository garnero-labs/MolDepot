#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error

def fetch_compound_data(cid: str):
    base_dir = os.path.join("data", cid)
    os.makedirs(base_dir, exist_ok=True)
    
    print(f"[*] Procesando CID {cid} en '{base_dir}'...")

    # 1. Descargar Manifest (Propiedades: IUPAC Name, Fórmula)
    prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IUPACName,MolecularFormula/json"
    manifest_path = os.path.join(base_dir, "manifest.json")
    
    try:
        print(f"    -> Descargando metadatos (manifest)...")
        urllib.request.urlretrieve(prop_url, manifest_path)
    except urllib.error.HTTPError as e:
        print(f"[!] Error HTTP al descargar propiedades para CID {cid}: {e.code} {e.reason}")
        return False

    # 2. Descargar Geometría 2D (SDF) - Obligatoria
    sdf_2d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF?record_type=2d"
    sdf_2d_path = os.path.join(base_dir, "raw.2d.sdf")
    try:
        print(f"    -> Descargando geometría 2D (SDF)...")
        urllib.request.urlretrieve(sdf_2d_url, sdf_2d_path)
    except urllib.error.HTTPError as e:
        print(f"[!] Error: No se pudo descargar SDF 2D para CID {cid}: {e.code} {e.reason}")
        return False

    # 3. Descargar Geometría 3D (SDF) - Condicional
    sdf_3d_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF?record_type=3d"
    sdf_3d_path = os.path.join(base_dir, "raw.3d.sdf")
    has_3d = True
    
    try:
        print(f"    -> Descargando geometría 3D (SDF)...")
        urllib.request.urlretrieve(sdf_3d_url, sdf_3d_path)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"    -> Info: El compuesto no dispone de geometría 3D en PubChem (404). Se omite raw.3d.sdf.")
            has_3d = False
            # Asegurar que no quede rastro de archivo 3D si falló
            if os.path.exists(sdf_3d_path):
                os.remove(sdf_3d_path)
        else:
            print(f"[!] Advertencia HTTP al descargar 3D para CID {cid}: {e.code} {e.reason}")
            has_3d = False

    # 4. Inyectar explícitamente el flag 'has3d' en el manifest.json local
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        # Añadir el flag en el nivel raíz del manifiesto
        manifest_data["has3d"] = has_3d
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
    except Exception as e:
        print(f"[!] Advertencia: No se pudo actualizar el manifest con el flag has3d: {e}")

    print(f"[+] CID {cid} descargado y validado en origen. has3d: {has_3d}.\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/fetch_compound.py <CID>")
        print("Ejemplo: python3 scripts/fetch_compound.py 5234")
        sys.exit(1)
    
    compound_cid = sys.argv[1]
    fetch_compound_data(compound_cid)
