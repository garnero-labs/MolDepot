#!/usr/bin/env python3
import os
import sys

# Importamos las funciones lógicas desde los nuevos módulos: fetch.py y parse.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fetch import fetch_compound_data
from parse import process_compound

def build_repository():
    cids_file = os.path.join("catalog", "cids.txt")
    if not os.path.exists(cids_file):
        print(f"[!] No se encontró el archivo de catálogo en '{cids_file}'.")
        return

    print(f"[*] Leyendo CIDs desde '{cids_file}'...")
    
    with open(cids_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cids = []
    for line in lines:
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            cid = cleaned.split()[0]
            cids.append(cid)

    print(f"[+] Se encontraron {len(cids)} compuestos para procesar.\n")

    for cid in cids:
        print("=" * 60)
        print(f"[*] Procesando lote para CID: {cid}")
        print("=" * 60)

        # 1. Ejecutar ingesta
        success_fetch = fetch_compound_data(cid)
        if not success_fetch:
            print(f"[!] Falló la ingesta para el CID {cid}. Saltando...\n")
            continue

        # 2. Ejecutar transformación
        try:
            process_compound(cid)
        except Exception as e:
            print(f"[!] Error inesperado parseando el CID {cid}: {e}\n")
            continue

    print("\n[+] ¡Proceso de construcción del repositorio completado con éxito!")

if __name__ == "__main__":
    build_repository()
