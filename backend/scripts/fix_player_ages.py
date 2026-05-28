import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, r"C:\WC2026\backend")
from app.data.players import PLAYERS_DB

PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"
API_KEY = "433afb0a34594a0aaa6f47a16ce5b0a6"
URL = "http://api.football-data.org/v4/competitions/2000/teams"

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o', 'ø': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c', 'ß': 'ss',
        'ğ': 'g', 'ş': 's', 'ı': 'i',
        'ð': 'd', 'þ': 'th', 'æ': 'ae',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = name.replace("junior", "jr").replace("júnior", "jr")
    name = "".join(c for c in name if c.isalnum())
    return name

# Elite players birth years mapping (in case they don't match the WC API list)
ELITE_BIRTH_YEARS = {
    "arda guler": 2005,
    "jamal musiala": 2003,
    "jude bellingham": 2003,
    "pedri": 2002,
    "kylian mbappe": 1998,
    "vinicius jr": 2000,
    "erling haaland": 2000,
    "emiliano martinez": 1992,
    "lamine yamal": 2007,
    "florian wirtz": 2003,
    "lionel messi": 1987,
    "cristiano ronaldo": 1985,
    "phil foden": 2000,
    "federico valverde": 1998,
    "fernando muslera": 1986
}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("UPDATING PLAYER AGES WITH REAL DATA")
    print("=" * 60)
    
    # Step 1: Fetch all teams and squads from API
    print("Fetching squads from football-data.org...")
    headers = {"X-Auth-Token": API_KEY}
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"Error fetching teams: {r.status_code}")
            return
        data = r.json()
    except Exception as e:
        print(f"API Request failed: {e}")
        return

    teams = data.get("teams", [])
    print(f"Found {len(teams)} teams. Processing squads...")
    
    # Build mapping: (normalized_name, normalized_nationality) -> birth_year
    birth_years = {}
    for team in teams:
        squad = team.get("squad", [])
        for member in squad:
            name = member.get("name")
            dob_str = member.get("dateOfBirth")
            nat = member.get("nationality")
            
            if name and dob_str and nat:
                try:
                    # dob_str is 'YYYY-MM-DD'
                    dob = datetime.strptime(dob_str, "%Y-%m-%d")
                    norm_name = normalize_name(name)
                    norm_nat = normalize_name(nat)
                    birth_years[(norm_name, norm_nat)] = dob.year
                except ValueError:
                    pass

    print(f"Loaded {len(birth_years)} player birth dates from API.")

    # Step 2: Update players in PLAYERS_DB
    updated_count = 0
    not_found_count = 0
    
    for pid, p in PLAYERS_DB.items():
        norm_name = normalize_name(p['name'])
        norm_nat = normalize_name(p.get('nationality', ''))
        
        # Try to find birth year from API squad mapping
        birth_year = birth_years.get((norm_name, norm_nat))
        
        # If not found, try elite mapping
        if birth_year is None:
            # Check if norm_name is in elite players
            birth_year = ELITE_BIRTH_YEARS.get(norm_name)
            
        if birth_year is not None:
            # Update age for each season
            for sk, sdata in p.get('seasons', {}).items():
                # Extract starting year of season e.g. "2025-26" -> 2025
                try:
                    season_start_year = int(sk.split('-')[0])
                except:
                    season_start_year = 2025  # fallback
                    
                real_age = season_start_year - birth_year
                # Clamp age to sensible values
                real_age = max(16, min(real_age, 45))
                sdata['age'] = real_age
            updated_count += 1
        else:
            # Default to 25 if not found
            not_found_count += 1
            # Keep existing age

    print(f"Successfully updated real ages for {updated_count} players.")
    print(f"Could not find real age for {not_found_count} players (kept placeholder age).")

    # Step 3: Write back to players.py
    print(f"Writing updated database to {PLAYERS_FILE}...")
    
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
        f.write("# Cleaned database - World Cup 2026 Players (Real ages updated)\n")
        f.write("PLAYERS_DB = {\n")
        for pid in sorted(PLAYERS_DB.keys()):
            pdata = PLAYERS_DB[pid]
            f.write(f"    {pid}: {py_repr(pdata, 1)},\n")
        f.write("}\n\n")
        f.write("# Convert keys to integers\n")
        f.write("PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
        
    print("File saved successfully! Verifying syntax...")
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        compile(content, PLAYERS_FILE, "exec")
        print("Syntax check passed! PLAYERS_DB is valid.")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in generated players.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
