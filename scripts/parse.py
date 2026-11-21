#!/usr/bin/env python3
import os
import sys
import json

def parse_sdf_block(sdf_content: str, is_3d: bool = False):
    lines = sdf_content.splitlines()
    atoms = []
    bonds = []
    
    if len(lines) < 4:
        return atoms, bonds
    
    counts_line = lines[3]
    try:
        num_atoms = int(counts_line[0:3].strip())
        num_bonds = int(counts_line[3:6].strip())
    except ValueError:
        return atoms, bonds
    
    atom_start_idx = 4
    bond_start_idx = atom_start_idx + num_atoms
    
    for i in range(num_atoms):
        idx = atom_start_idx + i
        if idx >= len(lines):
            break
        line = lines[idx]
        parts = line.split()
        if len(parts) >= 4:
            x = float(parts[0])
            y = float(parts[1])
            z = float(parts[2]) if is_3d else 0.0
            atom_data = {
                "aid": i + 1,
                "element": parts[3],
                "x": x,
                "y": y
            }
            if is_3d:
                atom_data["z"] = z
            atoms.append(atom_data)
            
    for i in range(num_bonds):
        idx = bond_start_idx + i
        if idx >= len(lines):
            break
        line = lines[idx]
        parts = line.split()
        if len(parts) >= 3:
            bonds.append({
                "aid1": int(parts[0]),
                "aid2": int(parts[1]),
                "order": int(parts[2])
            })
            
    return atoms, bonds

def process_compound(cid: str):
    base_dir = os.path.join("data", cid)
    if not os.path.exists(base_dir):
        print(f"[!] Error: No existe el directorio de datos para el CID {cid} en '{base_dir}'.")
        return

    print(f"[*] Transformando datos para CID {cid}...")

    manifest_path = os.path.join(base_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"[!] Error: No se encontró el manifest.json para el CID {cid}.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    properties = manifest_data.get("PropertyTable", {}).get("Properties", [{}])[0]
    has_3d = manifest_data.get("has3d", False)

    meta = {
        "cid": properties.get("CID", int(cid)),
        "molecularFormula": properties.get("MolecularFormula", ""),
        "iupacName": properties.get("IUPACName", ""),
        "has3d": has_3d
    }

    # Procesar 2D -> data/<CID>/2d.json
    sdf_2d_path = os.path.join(base_dir, "raw.2d.sdf")
    if os.path.exists(sdf_2d_path):
        with open(sdf_2d_path, "r", encoding="utf-8") as f:
            atoms_2d, bonds_2d = parse_sdf_block(f.read(), is_3d=False)
        output_2d = {
            "metadata": meta,
            "dimension": "2D",
            "atoms": atoms_2d,
            "bonds": bonds_2d
        }
        out_path_2d = os.path.join(base_dir, "2d.json")
        with open(out_path_2d, "w", encoding="utf-8") as f:
            json.dump(output_2d, f, indent=2)
        print(f"    -> Generado: {out_path_2d} ({len(atoms_2d)} átomos, {len(bonds_2d)} enlaces)")

    # Procesar 3D -> data/<CID>/3d.json (solo si manifest.json indica has3d=True)
    if has_3d:
        sdf_3d_path = os.path.join(base_dir, "raw.3d.sdf")
        if os.path.exists(sdf_3d_path):
            with open(sdf_3d_path, "r", encoding="utf-8") as f:
                atoms_3d, bonds_3d = parse_sdf_block(f.read(), is_3d=True)
            output_3d = {
                "metadata": meta,
                "dimension": "3D",
                "atoms": atoms_3d,
                "bonds": bonds_3d
            }
            out_path_3d = os.path.join(base_dir, "3d.json")
            with open(out_path_3d, "w", encoding="utf-8") as f:
                json.dump(output_3d, f, indent=2)
            print(f"    -> Generado: {out_path_3d} ({len(atoms_3d)} átomos, {len(bonds_3d)} enlaces)")
        else:
            print(f"[!] Advertencia: El manifest indica has3d=True pero no se encontró raw.3d.sdf en disco.")
    else:
        print(f"    -> Omitido 3D: El manifest dictamina has3d=False.")

    print(f"[+] Transformación completada para CID {cid}.\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/parse.py <CID>")
        sys.exit(1)
    process_compound(sys.argv[1])
