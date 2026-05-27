"""
Fix players.py: Remove broken JSON bulk import and re-import with proper Python syntax.
"""
import requests
import json
import os

API_KEY = "433afb0a34594a0aaa6f47a16ce5b0a6"
URL = "http://api.football-data.org/v4/competitions/2000/teams"
PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

# Step 1: Truncate players.py - keep only original content (first 4031 lines)
print("Step 1: Truncating players.py to original content...")
with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the line with "# Bulk imported" and cut there
cut_index = None
for i, line in enumerate(lines):
    if "# Bulk imported players from World Cup 2026" in line:
        # Also remove the blank line before it
        cut_index = i - 1 if i > 0 and lines[i-1].strip() == "" else i
        break

if cut_index:
    lines = lines[:cut_index]
    # Ensure the file ends with the convert line and a newline
    # Check if last meaningful line is the PLAYERS_DB conversion
    last_content = lines[-1].strip() if lines else ""
    if "PLAYERS_DB" not in last_content:
        lines.append("\n# Convert keys to integers to avoid string lookup errors from json-dumped keys\n")
        lines.append("PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
    lines.append("\n")
    
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  Truncated to {len(lines)} lines.")
else:
    print("  No bulk import section found, file is clean.")

# Step 2: Fetch WC teams from API
print("\nStep 2: Fetching World Cup teams from football-data.org...")
headers = {"X-Auth-Token": API_KEY}
response = requests.get(URL, headers=headers)
if response.status_code != 200:
    print(f"  Error fetching data: {response.status_code}")
    exit(1)

data = response.json()
teams = data.get("teams", [])
print(f"  Found {len(teams)} teams.")

# Step 3: Generate player data
print("\nStep 3: Generating player data...")

def gen_player(pid, p_info, team_name, team_nationality):
    pos = p_info.get("position") or "Midfield"
    
    pos_map = {
        "Goalkeeper": "GK",
        "Defence": "CB", "Centre-Back": "CB", "Left-Back": "LB", "Right-Back": "RB",
        "Midfield": "CM", "Defensive Midfield": "CDM", "Central Midfield": "CM",
        "Attacking Midfield": "CAM",
        "Offence": "ST", "Centre-Forward": "ST", "Left Winger": "LW", "Right Winger": "RW",
    }
    mp = pos_map.get(pos, "CM")
    nat = p_info.get("nationality") or team_nationality or "Unknown"
    name = p_info.get("name") or "Unknown"
    
    # Position-based realistic stats
    if mp == "GK":
        goals, assists, rating = 0, 0, 7.0
        tackles, interceptions, clearances = 2, 1, 8
        shots, key_passes = 0, 2
        dribbles_c, dribbles_a = 1, 2
    elif mp in ("CB", "LB", "RB"):
        goals, assists, rating = 1, 2, 7.1
        tackles, interceptions, clearances = 38, 22, 45
        shots, key_passes = 8, 12
        dribbles_c, dribbles_a = 10, 18
    elif mp in ("CDM", "CM"):
        goals, assists, rating = 3, 5, 7.2
        tackles, interceptions, clearances = 30, 18, 12
        shots, key_passes = 22, 28
        dribbles_c, dribbles_a = 20, 35
    elif mp == "CAM":
        goals, assists, rating = 6, 8, 7.4
        tackles, interceptions, clearances = 15, 10, 5
        shots, key_passes = 40, 45
        dribbles_c, dribbles_a = 35, 55
    else:  # ST, RW, LW
        goals, assists, rating = 10, 5, 7.3
        tackles, interceptions, clearances = 10, 6, 3
        shots, key_passes = 55, 20
        dribbles_c, dribbles_a = 30, 50

    return {
        "id": pid,
        "name": name,
        "nationality": nat,
        "position": mp,
        "team": team_name,
        "image_url": "/avatars/default.png",
        "career_peak_season": "2025-26",
        "career_history": {
            "2025-26": {"rating": rating, "goals": goals, "assists": assists, "apps": 30}
        },
        "tournament_pressure_trend": {"2025-26": 72.0},
        "club_vs_country": {
            "club": {"rating": rating, "goals": goals, "assists": assists, "key_passes": key_passes, "dribbles": dribbles_c},
            "country": {"rating": round(rating + 0.2, 1), "goals": max(1, goals // 3), "assists": max(1, assists // 3), "key_passes": key_passes // 3, "dribbles": dribbles_c // 3}
        },
        "seasons": {
            "2025-26": {
                "team": team_name,
                "league": "World Cup 2026",
                "age": 25,
                "raw_stats": {
                    "goals": goals, "assists": assists,
                    "xG": round(goals * 0.9, 1), "xA": round(assists * 0.85, 1),
                    "shots": shots, "shots_on_target": shots // 2,
                    "key_passes": key_passes,
                    "progressive_passes": 45 + key_passes,
                    "through_balls": key_passes // 4,
                    "dribbles_completed": dribbles_c, "dribbles_attempted": dribbles_a,
                    "crosses": 12, "touches_in_box": goals * 6 + 20,
                    "passes_completed": 400, "passes_attempted": 480
                },
                "defensive_stats": {
                    "tackles": tackles, "interceptions": interceptions,
                    "clearances": clearances, "blocks": tackles // 4,
                    "aerial_duels_won": 10, "aerial_duels_total": 22,
                    "duels_won_pct": 48.0, "recoveries": tackles * 2,
                    "fouls_committed": 12
                },
                "physical_stats": {
                    "distance_covered_km": 10.5, "sprints": 25,
                    "press_resistance": 82.0, "top_speed_kmh": 32.5
                },
                "advanced_stats": {
                    "progressive_carries": dribbles_c + 15,
                    "final_third_entries": 50,
                    "penalty_area_entries": 25,
                    "shot_creating_actions": key_passes + 10,
                    "goal_creating_actions": goals + assists
                },
                "big_match_stats": {
                    "rating_top6": round(rating - 0.2, 1),
                    "goals_top6": max(0, goals // 4),
                    "assists_top6": max(0, assists // 4),
                    "clutch_goals": max(0, goals // 5)
                },
                "international_stats": {
                    "caps": 20, "goals": max(1, goals // 3),
                    "tournament_appearances": 3,
                    "international_rating": round(rating + 0.1, 1)
                },
                "wc_fit_factors": {
                    "big_match_performance": 72,
                    "pressure_handling": 74,
                    "consistency": 76,
                    "physical_intensity": 72,
                    "international_experience": 65,
                    "tactical_flexibility": 78
                },
                "form_ratings": [
                    round(rating - 0.2, 1), round(rating + 0.1, 1), round(rating - 0.1, 1),
                    round(rating + 0.3, 1), round(rating, 1), round(rating + 0.2, 1),
                    round(rating - 0.1, 1), round(rating + 0.4, 1), round(rating + 0.1, 1),
                    round(rating + 0.3, 1)
                ]
            }
        }
    }

current_id = 14
all_new = {}
for team in teams:
    team_name = team.get("name", "Unknown")
    team_nat = team.get("area", {}).get("name", "Unknown")
    squad = team.get("squad", [])
    print(f"  {team_name}: {len(squad)} players")
    for p in squad:
        current_id += 1
        all_new[current_id] = gen_player(current_id, p, team_name, team_nat)

print(f"\n  Total new players: {len(all_new)}")

# Step 4: Write as proper Python to players.py
print("\nStep 4: Appending to players.py with Python-safe syntax...")

def py_repr(obj, indent=0):
    """Convert a Python object to a pretty-printed Python repr string (not JSON)."""
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

with open(PLAYERS_FILE, "a", encoding="utf-8") as f:
    f.write("\n# Bulk imported players from World Cup 2026 (Python-safe syntax)\n")
    f.write("BULK_PLAYERS = {\n")
    for pid, pdata in all_new.items():
        f.write(f"    {pid}: {py_repr(pdata, 1)},\n")
    f.write("}\n")
    f.write("PLAYERS_DB.update(BULK_PLAYERS)\n")

print("Done! Verifying import...")

# Step 5: Verify
try:
    # Quick syntax check
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    compile(content, PLAYERS_FILE, "exec")
    print("  Syntax OK!")
except SyntaxError as e:
    print(f"  SYNTAX ERROR: {e}")
    exit(1)

print(f"\nAll done! {len(all_new)} players added successfully.")
