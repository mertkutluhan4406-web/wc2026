import requests
import json
import os

API_KEY = "433afb0a34594a0aaa6f47a16ce5b0a6"
URL = "http://api.football-data.org/v4/competitions/2000/teams"
PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

def generate_player_data(player_id, p_info, team_name):
    pos = p_info.get("position", "Midfield")
    if not pos: pos = "Midfield"
    
    # Map API positions to our positions
    pos_map = {
        "Goalkeeper": "GK",
        "Defence": "CB",
        "Centre-Back": "CB",
        "Left-Back": "LB",
        "Right-Back": "RB",
        "Midfield": "CM",
        "Defensive Midfield": "CDM",
        "Central Midfield": "CM",
        "Attacking Midfield": "CAM",
        "Offence": "ST",
        "Centre-Forward": "ST",
        "Left Winger": "LW",
        "Right Winger": "RW"
    }
    mapped_pos = pos_map.get(pos, "CM")
    
    # Generate stats based on position
    rating = 7.0
    goals = 5 if mapped_pos in ["ST", "RW", "LW"] else 1
    assists = 4 if mapped_pos in ["CAM", "RW", "LW"] else 1
    
    season_stats = {
        "team": team_name,
        "league": "World Cup",
        "age": 25,
        "raw_stats": {
            "goals": goals, "assists": assists, "xG": goals * 1.1, "xA": assists * 1.2,
            "shots": goals * 5, "shots_on_target": goals * 2, "key_passes": assists * 3,
            "progressive_passes": 40, "through_balls": 5, "dribbles_completed": 15,
            "dribbles_attempted": 25, "crosses": 10, "touches_in_box": goals * 8,
            "passes_completed": 350, "passes_attempted": 420
        },
        "defensive_stats": {
            "tackles": 15, "interceptions": 10, "clearances": 5, "blocks": 4,
            "aerial_duels_won": 8, "aerial_duels_total": 18, "duels_won_pct": 45.0,
            "recoveries": 35, "fouls_committed": 8
        },
        "physical_stats": { "distance_covered_km": 10.2, "sprints": 22, "press_resistance": 82.0, "top_speed_kmh": 32.5 },
        "advanced_stats": { "progressive_carries": 44, "final_third_entries": 45, "penalty_area_entries": 22, "shot_creating_actions": 35, "goal_creating_actions": 5 },
        "big_match_stats": { "rating_top6": 7.1, "goals_top6": 0, "assists_top6": 1, "clutch_goals": 0 },
        "international_stats": { "caps": 15, "goals": 2, "tournament_appearances": 1, "international_rating": 7.0 },
        "wc_fit_factors": { "big_match_performance": 70, "pressure_handling": 72, "consistency": 75, "physical_intensity": 70, "international_experience": 60, "tactical_flexibility": 78 },
        "form_ratings": [7.0, 7.2, 7.1, 7.3, 7.2, 7.4, 7.3, 7.5, 7.4, 7.5]
    }
    
    player_data = {
        "id": player_id,
        "name": p_info.get("name", "Unknown"),
        "nationality": p_info.get("nationality", "Unknown"),
        "position": mapped_pos,
        "team": team_name,
        "image_url": "/avatars/default.png",
        "career_peak_season": "2025-26",
        "career_history": {
            "2025-26": {"rating": rating, "goals": goals, "assists": assists, "apps": 20}
        },
        "tournament_pressure_trend": {"2025-26": 72.0},
        "club_vs_country": {
            "club": {"rating": rating, "goals": goals, "assists": assists, "key_passes": 15, "dribbles": 10},
            "country": {"rating": rating+0.2, "goals": 1, "assists": 1, "key_passes": 5, "dribbles": 3}
        },
        "seasons": {
            "2025-26": season_stats
        }
    }
    return player_data

def main():
    print("Fetching teams from football-data.org...")
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return

    data = response.json()
    teams = data.get("teams", [])
    
    if not teams:
        print("No teams found. Let's try the direct competitions URL to see structure.")
        # Sometimes teams are directly in the root or under 'teams'
        teams = data.get("competitions", []) # Wait, the /teams endpoint should return 'teams'

    print(f"Found {len(teams)} teams.")
    
    # Let's find highest ID currently in players.py
    current_id = 14
    
    new_players = {}
    
    for team in teams:
        team_name = team.get("name", "Unknown Team")
        squad = team.get("squad", [])
        print(f"Processing {team_name} ({len(squad)} players)...")
        
        for p in squad:
            current_id += 1
            new_players[current_id] = generate_player_data(current_id, p, team_name)
    
    if not new_players:
        print("No players were generated. Data structure might be different.")
        return
        
    print(f"Generated {len(new_players)} new players. Appending to players.py...")
    
    # Append as PLAYERS_DB.update(...)
    update_str = "\n\n# Bulk imported players from World Cup 2026\n"
    update_str += "BULK_PLAYERS = " + json.dumps(new_players, indent=4) + "\n"
    update_str += "PLAYERS_DB.update({int(k): v for k, v in BULK_PLAYERS.items()})\n"
    
    with open(PLAYERS_FILE, "a", encoding="utf-8") as f:
        f.write(update_str)
        
    print("Done! Players added successfully.")

if __name__ == "__main__":
    main()
