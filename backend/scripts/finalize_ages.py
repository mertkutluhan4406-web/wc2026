import sys
import os

sys.path.insert(0, r"C:\WC2026\backend")
from app.data.players import PLAYERS_DB

PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

UNMATCHED_AGES = {
    1: 20, # Arda Güler
    6: 25, # Vinícius Jr
    13: 25, # Phil Foden
    498: 29, # Gonzalo Valle
    602: 28, # Mohammed Al-Rubaie
    613: 36, # Salman Al-Faraj
    617: 26, # Abdullah Al-Hamdan
    618: 32, # Saleh Al-Shehri
    619: 25, # Firas Al-Buraikan
    629: 39, # Yassine Chikhaoui
    887: 27, # Saleh Hardani
    892: 24, # Mehdi Hashemnejad
    1039: 32, # Ahmed Alaaeldin
}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Finalizing player ages...")
    
    for pid, age in UNMATCHED_AGES.items():
        if pid in PLAYERS_DB:
            player = PLAYERS_DB[pid]
            # Update each season
            for sk, sdata in player.get('seasons', {}).items():
                try:
                    season_start_year = int(sk.split('-')[0])
                except:
                    season_start_year = 2025
                # calculate age relative to 2025-26
                sdata['age'] = age - (2025 - season_start_year)
            print(f"  Updated {player['name']} to age {age}")
            
    # Write back to file
    def py_repr(obj, indent=0):
        sp = "    " * indent
        sp1 = "    " * (indent + 1)
        if obj is None:
            return "None"
        elif isinstance(obj, bool):
            return "True" if obj else "False"
        elif isinstance(obj, (int, float)):
            return repr(obj)
        elif isinstance(obj, str):
            return repr(obj)
        elif isinstance(obj, list):
            if not obj:
                return "[]"
            items = ", ".join(py_repr(v, 0) for v in obj)
            if len(items) < 80:
                return f"[{items}]"
            items = (",\n" + sp1).join(py_repr(v, indent + 1) for v in obj)
            return f"[\n{sp1}{items}\n{sp}]"
        elif isinstance(obj, dict):
            if not obj:
                return "{}"
            parts = []
            for k, v in obj.items():
                kr = repr(k)
                vr = py_repr(v, indent + 1)
                parts.append(f"{kr}: {vr}")
            inner = (",\n" + sp1).join(parts)
            return f"{{\n{sp1}{inner}\n{sp}}}"
        return repr(obj)

    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        f.write("# Finalized database - World Cup 2026 Players (All ages correct)\n")
        f.write("PLAYERS_DB = {\n")
        for pid in sorted(PLAYERS_DB.keys()):
            pdata = PLAYERS_DB[pid]
            f.write(f"    {pid}: {py_repr(pdata, 1)},\n")
        f.write("}\n\n")
        f.write("# Convert keys to integers\n")
        f.write("PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
        
    print("Database finalized and written successfully!")

if __name__ == "__main__":
    main()
