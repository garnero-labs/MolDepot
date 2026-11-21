#!/usr/bin/env python3
import os
import sys

# Importamos las funciones lógicas desde los módulos hermanos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fetch import fetch_compound_data
from parse import process_compound


def read_cids_from_file(filepath: str) -> list[str]:
    """Lee CIDs limpios desde un archivo de texto, ignorando vacíos y comentarios."""
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cids = []
    seen = set()
    for line in lines:
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            cid = cleaned.split()[0]
            if cid.isdigit() and cid not in seen:
                seen.add(cid)
                cids.append(cid)
    return cids


def regenerate_catalog_from_data(data_dir: str = "data", catalog_file: str = os.path.join("catalog", "cids.txt")) -> list[str]:
    """Escanea los directorios existentes bajo data/ y regenera catalog/cids.txt ordenado."""
    os.makedirs(os.path.dirname(catalog_file), exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    existing_cids = []
    for entry in os.listdir(data_dir):
        entry_path = os.path.join(data_dir, entry)
        if os.path.isdir(entry_path) and entry.isdigit():
            existing_cids.append(int(entry))

    existing_cids.sort()
    sorted_cid_strs = [str(cid) for cid in existing_cids]

    with open(catalog_file, "w", encoding="utf-8") as f:
        for cid_str in sorted_cid_strs:
            f.write(f"{cid_str}\n")

    return sorted_cid_strs


def build_repository():
    delta_file = os.path.join("catalog", "delta.txt")
    data_dir = "data"
    catalog_file = os.path.join("catalog", "cids.txt")

    if not os.path.exists(delta_file):
        print(f"[!] No se encontró el archivo delta en '{delta_file}'.")
        return

    print(f"[*] Leyendo CIDs incrementales desde '{delta_file}'...")
    delta_cids = read_cids_from_file(delta_file)
    print(f"[+] Se encontraron {len(delta_cids)} CIDs únicos en delta.txt.\n")

    processed_count = 0
    skipped_count = 0

    for cid in delta_cids:
        target_dir = os.path.join(data_dir, cid)

        # Si el directorio ya existe, no se toca
        if os.path.exists(target_dir):
            print(f"[=] CID {cid} ya existe en '{target_dir}'. Se omite sin modificar.")
            skipped_count += 1
            continue

        print("=" * 60)
        print(f"[*] Procesando nuevo CID: {cid}")
        print("=" * 60)

        success_fetch = fetch_compound_data(cid)
        if not success_fetch:
            print(f"[!] Falló la ingesta para el CID {cid}. Saltando...\n")
            continue

        try:
            process_compound(cid)
            processed_count += 1
        except Exception as e:
            print(f"[!] Error inesperado parseando el CID {cid}: {e}\n")
            continue

    # Regenerar catalog/cids.txt a partir del estado real de data/
    consolidated_cids = regenerate_catalog_from_data(data_dir=data_dir, catalog_file=catalog_file)

    print("\n" + "=" * 60)
    print(f"[+] Resumen incremental: {processed_count} nuevos, {skipped_count} omitidos.")
    print(f"[+] Catálogo '{catalog_file}' regenerado con {len(consolidated_cids)} CIDs en total.")
    print("=" * 60)


if __name__ == "__main__":
    build_repository()
