import sys
import os
import requests
import time

sys.path.insert(0, r"C:\WC2026\backend")
from app.data.players import PLAYERS_DB

PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"
APISPORTS_KEY = "218816fbb53510d93e0c71bc1ca75686"
HEADERS = {"x-apisports-key": APISPORTS_KEY}
BASE_URL = "https://v3.football.api-sports.io"

def get_with_retry(url, headers, params):
    while True:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                # Check for error details inside successful JSON response (some API errors return 200)
                json_data = r.json()
                if "errors" in json_data and isinstance(json_data["errors"], dict):
                    err_msg = str(json_data["errors"])
                    if "rate limit" in err_msg.lower() or "requests limit" in err_msg.lower() or "429" in err_msg:
                        print("    Rate limit message in response! Sleeping 60 seconds...")
                        time.sleep(60)
                        continue
                return r
            elif r.status_code == 429:
                print("    Rate limited (429)! Sleeping 60 seconds...")
                time.sleep(60)
            else:
                print(f"    Request failed with status {r.status_code}: {r.text}")
                return r
        except Exception as e:
            print(f"    Network error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

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
    return name

def main():
    print("=" * 60)
    print("MAPPING API-FOOTBALL IDS TO PLAYERS_DB (WITH RATE LIMIT RETRIES)")
    print("=" * 60)

    # Step 1: Get all 32 teams from World Cup 2022
    print("\nStep 1: Fetching World Cup 2022 national teams...")
    r = get_with_retry(f"{BASE_URL}/teams", headers=HEADERS, params={"league": 1, "season": 2022})
    if r.status_code != 200:
        print(f"Error fetching WC teams: {r.status_code} - {r.text}")
        return

    wc_teams = r.json().get("response", [])
    team_map = {} # name -> id
    for item in wc_teams:
        t = item.get("team", {})
        team_map[t.get("name")] = t.get("id")
    
    print(f"  Found {len(team_map)} World Cup teams.")

    # Step 2: Identify other nationalities in PLAYERS_DB
    nationalities = sorted(list(set(p["nationality"] for p in PLAYERS_DB.values())))
    print(f"\nStep 2: Identifying other nationalities in DB...")
    
    # We need to map nationalities to API-Football national team IDs
    api_team_ids = {} # nationality -> team_id
    for nat in nationalities:
        # Check if already mapped
        mapped_name = nat
        if nat == "USA": mapped_name = "USA"
        elif nat == "South Korea": mapped_name = "South Korea"
        elif nat == "DR Congo" or nat == "Congo DR": mapped_name = "DR Congo"
        elif nat == "Cote d'Ivoire" or nat == "Ivory Coast": mapped_name = "Ivory Coast"
        elif nat == "Czech Republic": mapped_name = "Czech Republic"
        elif nat == "Cape Verde Islands": mapped_name = "Cape Verde"
        elif nat == "Curaçao": mapped_name = "Curacao"

        if mapped_name in team_map:
            api_team_ids[nat] = team_map[mapped_name]
        else:
            # Search for national team
            print(f"  Searching for national team: {mapped_name}...")
            sr = get_with_retry(f"{BASE_URL}/teams", headers=HEADERS, params={"search": mapped_name})
            time.sleep(1) # respect rate limit
            if sr.status_code == 200:
                results = sr.json().get("response", [])
                for res in results:
                    t = res.get("team", {})
                    # Ensure it is national
                    if t.get("national"):
                        api_team_ids[nat] = t.get("id")
                        print(f"    Found {nat} -> ID {t.get('id')}")
                        break
            if nat not in api_team_ids:
                print(f"    Could not find national team ID for {nat}")

    # Step 3: Fetch squads and map players
    print("\nStep 3: Fetching squads and mapping players...")
    mapped_count = 0
    total_players = len(PLAYERS_DB)

    for nat, team_id in api_team_ids.items():
        # Check if all players of this nationality already have api_football_id
        local_players = {pid: p for pid, p in PLAYERS_DB.items() if p["nationality"] == nat}
        unmapped_locals = {pid: p for pid, p in local_players.items() if "api_football_id" not in p}
        
        # If all mapped, skip request to save quota
        if not unmapped_locals:
            # Still count them as mapped for statistics
            already_mapped = len(local_players)
            mapped_count += already_mapped
            print(f"\n  Skipping {nat} (ID: {team_id}) - all players already mapped ({already_mapped} players).")
            continue

        print(f"\n  Fetching squad for {nat} (ID: {team_id})...")
        sq_r = get_with_retry(f"{BASE_URL}/players/squads", headers=HEADERS, params={"team": team_id})
        time.sleep(1) # respect rate limit
        if sq_r.status_code != 200:
            print(f"    Error fetching squad: {sq_r.status_code}")
            continue

        squad = sq_r.json().get("response", [])
        if not squad:
            print("    No squad roster found.")
            continue
        
        squad_players = squad[0].get("players", [])
        print(f"    Found {len(squad_players)} players in API squad.")

        # Build name indexes for matching
        local_name_index = {}
        for pid, p in local_players.items():
            norm = normalize_name(p["name"])
            local_name_index[norm] = pid

        for sp in squad_players:
            sp_name = sp.get("name")
            sp_id = sp.get("id")
            
            # Try exact match
            norm_sp = normalize_name(sp_name)
            matched_pid = local_name_index.get(norm_sp)

            # Try fuzzy matching if not matched
            if matched_pid is None:
                # Compare parts of the name
                sp_parts = set(norm_sp.split())
                best_match = None
                best_score = 0
                for norm_db, pid in local_name_index.items():
                    db_parts = set(norm_db.split())
                    common = sp_parts & db_parts
                    if common:
                        score = len(common) / max(len(sp_parts), len(db_parts))
                        if score > best_score and score >= 0.5:
                            best_score = score
                            best_match = pid
                if best_score >= 0.5:
                    matched_pid = best_match

            if matched_pid is not None:
                PLAYERS_DB[matched_pid]["api_football_id"] = sp_id
                # Remove from index so we don't double map
                keys_to_remove = [k for k, v in local_name_index.items() if v == matched_pid]
                for k in keys_to_remove:
                    local_name_index.pop(k, None)

        # Re-calculate mapped count for this country
        new_mapped = sum(1 for p in local_players.values() if "api_football_id" in p)
        mapped_count += new_mapped
        print(f"    Mapped squad. Total successfully mapped players so far: {mapped_count}/{total_players}")

    # Step 4: Save PLAYERS_DB back to players.py
    print("\nStep 4: Saving updated database to players.py...")
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
        f.write("# Finalized database - World Cup 2026 Players (Enriched with API-Football IDs)\n")
        f.write("PLAYERS_DB = {\n")
        for pid in sorted(PLAYERS_DB.keys()):
            pdata = PLAYERS_DB[pid]
            f.write(f"    {pid}: {py_repr(pdata, 1)},\n")
        f.write("}\n\n")
        f.write("# Convert keys to integers\n")
        f.write("PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")

    # Let's count total mapped players in the DB
    total_mapped = sum(1 for p in PLAYERS_DB.values() if "api_football_id" in p)
    print(f"Database successfully updated! Total {total_mapped}/{total_players} players mapped with API IDs.")

if __name__ == "__main__":
    main()
