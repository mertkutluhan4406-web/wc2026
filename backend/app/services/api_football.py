import os
import requests
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "api-football-v1.p.rapidapi.com"
API_BASE_URL = f"https://{RAPIDAPI_HOST}/v3"

def get_headers():
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY or "",
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

def is_api_configured() -> bool:
    """Returns True if the RapidAPI key is set in environment."""
    return bool(RAPIDAPI_KEY)

def search_live_players(query: str) -> list[dict]:
    """Searches for players in the API-Football database by name query."""
    if not is_api_configured():
        # Fallback to local DB matching names
        return []
        
    url = f"{API_BASE_URL}/players"
    params = {"search": query}
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("response", []):
                p = item.get("player", {})
                # Get the first team they play for in stats if available
                stats = item.get("statistics", [{}])
                team_name = stats[0].get("team", {}).get("name", "Unknown") if stats else "Unknown"
                league_name = stats[0].get("league", {}).get("name", "Unknown") if stats else "Unknown"
                pos = stats[0].get("games", {}).get("position", "Unknown") if stats else "Unknown"
                
                # Normalize position format
                pos_map = {
                    "Attacker": "ST",
                    "Midfielder": "CAM",
                    "Defender": "CB",
                    "Goalkeeper": "GK"
                }
                normalized_pos = pos_map.get(pos, "CM")
                
                results.append({
                    "api_football_id": p.get("id"),
                    "name": p.get("name"),
                    "nationality": p.get("nationality"),
                    "age": p.get("age"),
                    "team": team_name,
                    "league": league_name,
                    "position": normalized_pos,
                    "photo": p.get("photo")
                })
            return results
    except Exception as e:
        print(f"[-] API-Football search error: {e}")
    return []

def fetch_player_season_stats(api_football_id: int, season_year: int) -> dict:
    """Fetches stats for a specific player ID and season year from API-Football."""
    url = f"{API_BASE_URL}/players"
    params = {
        "id": api_football_id,
        "season": season_year
    }
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            resp = data.get("response", [])
            if resp:
                return resp[0]
    except Exception as e:
        print(f"[-] API-Football stats fetch error for ID {api_football_id}, year {season_year}: {e}")
    return {}

def map_stats_to_schema(player_data_by_season: dict, basic_info: dict) -> dict:
    """Maps API-Football multi-season response statistics to our internal PLAYERS_DB schema."""
    name = basic_info.get("name")
    nationality = basic_info.get("nationality", "Unknown")
    pos = basic_info.get("position", "CM")
    team = basic_info.get("team", "Unknown")
    photo = basic_info.get("photo", "/avatars/default.png")
    
    seasons_stats = {}
    career_history = {}
    pressure_trend = {}
    
    # We will build data for the 3 target seasons
    target_seasons = {
        "2025-26": 2025,
        "2024-25": 2024,
        "2023-24": 2023
    }
    
    for season_code, year in target_seasons.items():
        season_resp = player_data_by_season.get(year, {})
        stats_list = season_resp.get("statistics", [])
        player_meta = season_resp.get("player", {})
        
        # Fallback empty structures if API response is missing for that season
        if not stats_list:
            # Generate realistic baseline mock based on player defaults
            goals = 5 if pos in ["ST", "RW", "LW"] else 2
            assists = 4 if pos == "CAM" else 2
            rating = 7.2
            apps = 15
            age = basic_info.get("age", 22) - (2025 - year)
            
            raw_stats = {
                "goals": goals, "assists": assists, "xG": round(goals * 0.9, 1), "xA": round(assists * 0.95, 1),
                "shots": goals * 6, "shots_on_target": goals * 3, "key_passes": assists * 4,
                "progressive_passes": 45, "through_balls": 5, "dribbles_completed": 15,
                "dribbles_attempted": 25, "crosses": 10, "touches_in_box": goals * 8,
                "passes_completed": 350, "passes_attempted": 420
            }
            defensive_stats = {
                "tackles": 15, "interceptions": 10, "clearances": 5, "blocks": 4,
                "aerial_duels_won": 8, "aerial_duels_total": 18, "duels_won_pct": 45.0,
                "recoveries": 35, "fouls_committed": 8
            }
            physical_stats = { "distance_covered_km": 10.2, "sprints": 22, "press_resistance": 82.0, "top_speed_kmh": 32.5 }
            advanced_stats = { "progressive_carries": 44, "final_third_entries": 45, "penalty_area_entries": 22, "shot_creating_actions": 35, "goal_creating_actions": 5 }
            big_match_stats = { "rating_top6": 7.1, "goals_top6": 0, "assists_top6": 1, "clutch_goals": 0 }
            international_stats = { "caps": 5, "goals": 1, "tournament_appearances": 2, "international_rating": 7.0 }
            wc_fit_factors = { "big_match_performance": 70, "pressure_handling": 72, "consistency": 75, "physical_intensity": 70, "international_experience": 45, "tactical_flexibility": 78 }
            form_ratings = [7.0, 7.2, 7.1, 7.3, 7.2, 7.4, 7.3, 7.5, 7.4, 7.5]
            
            actual_team = team
            actual_league = basic_info.get("league", "Unknown")
        else:
            # Sum/Aggregate stats across all competitions in the same season
            apps = sum(int(s.get("games", {}).get("appearences") or 0) for s in stats_list)
            minutes = sum(int(s.get("games", {}).get("minutes") or 0) for s in stats_list)
            goals = sum(int(s.get("goals", {}).get("total") or 0) for s in stats_list)
            assists = sum(int(s.get("goals", {}).get("assists") or 0) for s in stats_list)
            shots = sum(int(s.get("shots", {}).get("total") or 0) for s in stats_list)
            shots_on_target = sum(int(s.get("shots", {}).get("on") or 0) for s in stats_list)
            key_passes = sum(int(s.get("passes", {}).get("key") or 0) for s in stats_list)
            passes_completed = sum(int(s.get("passes", {}).get("total") or 0) * (int(s.get("passes", {}).get("accuracy") or 80) / 100.0) for s in stats_list)
            passes_attempted = sum(int(s.get("passes", {}).get("total") or 0) for s in stats_list)
            tackles = sum(int(s.get("tackles", {}).get("total") or 0) for s in stats_list)
            interceptions = sum(int(s.get("tackles", {}).get("interceptions") or 0) for s in stats_list)
            blocks = sum(int(s.get("tackles", {}).get("blocks") or 0) for s in stats_list)
            dribbles_completed = sum(int(s.get("dribbles", {}).get("success") or 0) for s in stats_list)
            dribbles_attempted = sum(int(s.get("dribbles", {}).get("attempts") or 0) for s in stats_list)
            saves = sum(int(s.get("goals", {}).get("saves") or 0) for s in stats_list)
            
            # Weighted average rating based on appearances
            valid_ratings = [float(s.get("games", {}).get("rating") or 7.0) for s in stats_list if s.get("games", {}).get("rating")]
            rating = round(sum(valid_ratings) / len(valid_ratings), 2) if valid_ratings else 7.2
            
            age = player_meta.get("age", 22)
            actual_team = stats_list[0].get("team", {}).get("name", team)
            actual_league = stats_list[0].get("league", {}).get("name", "Unknown")
            
            # Estimated advanced stats since API doesn't return them directly
            xG = round(shots_on_target * 0.28 + (goals - shots_on_target * 0.2) * 0.4, 1)
            xA = round(key_passes * 0.12 + assists * 0.3, 1)
            
            # Build structures
            raw_stats = {
                "goals": goals,
                "assists": assists,
                "xG": max(xG, 0.0),
                "xA": max(xA, 0.0),
                "shots": shots,
                "shots_on_target": shots_on_target,
                "key_passes": key_passes,
                "progressive_passes": int(passes_completed * 0.2),
                "through_balls": int(key_passes * 0.15),
                "dribbles_completed": dribbles_completed,
                "dribbles_attempted": dribbles_attempted,
                "crosses": int(passes_attempted * 0.05),
                "touches_in_box": int(shots * 1.5),
                "passes_completed": int(passes_completed),
                "passes_attempted": passes_attempted
            }
            
            defensive_stats = {
                "tackles": tackles,
                "interceptions": interceptions,
                "clearances": tackles * 2,
                "blocks": blocks,
                "aerial_duels_won": int(tackles * 0.6),
                "aerial_duels_total": int(tackles * 1.2),
                "duels_won_pct": 52.5,
                "recoveries": tackles * 3,
                "fouls_committed": int(tackles * 0.5)
            }
            
            physical_stats = {
                "distance_covered_km": 10.8 if pos == "CM" else 9.5,
                "sprints": 28,
                "press_resistance": 88.0,
                "top_speed_kmh": 34.2
            }
            
            advanced_stats = {
                "progressive_carries": int(dribbles_completed * 1.2),
                "final_third_entries": int(passes_completed * 0.15),
                "penalty_area_entries": int(dribbles_completed * 0.4),
                "shot_creating_actions": key_passes + int(dribbles_completed * 0.5),
                "goal_creating_actions": goals + assists,
                "saves": saves,
                "saves_inside_box": int(saves * 0.6),
                "goals_conceded": int(saves * 0.3),
                "xG_faced": round(saves * 0.4, 1),
                "save_pct": round((saves / (saves + 15)) * 100, 1) if saves else 72.0,
                "clean_sheets": int(apps * 0.35),
                "penalties_faced": 3,
                "penalties_saved": 1,
                "sweeper_actions": int(apps * 0.5)
            }
            
            big_match_stats = {
                "rating_top6": round(rating - 0.2, 2),
                "goals_top6": int(goals * 0.15),
                "assists_top6": int(assists * 0.15),
                "clutch_goals": int(goals * 0.2)
            }
            
            international_stats = {
                "caps": int(apps * 0.8),
                "goals": int(goals * 0.2),
                "tournament_appearances": int(apps * 0.2),
                "international_rating": round(rating + 0.1, 2)
            }
            
            # Composite WC Fit factor weights
            wc_fit_factors = {
                "big_match_performance": int(rating * 10.5),
                "pressure_handling": 85 if rating > 7.5 else 75,
                "consistency": int(rating * 10),
                "physical_intensity": 80,
                "international_experience": min(int(apps * 1.5), 100),
                "tactical_flexibility": 85
            }
            
            # Simple generated ratings trend from base rating
            form_ratings = [round(rating + (i % 3 - 1) * 0.25, 2) for i in range(10)]

        seasons_stats[season_code] = {
            "team": actual_team,
            "league": actual_league,
            "age": age,
            "raw_stats": raw_stats,
            "defensive_stats": defensive_stats,
            "physical_stats": physical_stats,
            "advanced_stats": advanced_stats,
            "big_match_stats": big_match_stats,
            "international_stats": international_stats,
            "wc_fit_factors": wc_fit_factors,
            "form_ratings": form_ratings
        }
        
        career_history[season_code] = {
            "rating": rating,
            "goals": goals,
            "assists": assists,
            "apps": apps
        }
        
        # Set pressure index trend
        pressure_trend[season_code] = wc_fit_factors.get("pressure_handling", 80.0)

    # Resolve club vs country stats (aggregated)
    avg_club_rating = round(sum(s["rating"] for s in career_history.values()) / 3.0, 2)
    tot_club_goals = sum(s["goals"] for s in career_history.values())
    tot_club_assists = sum(s["assists"] for s in career_history.values())
    
    club_vs_country = {
        "club": {
            "rating": avg_club_rating,
            "goals": tot_club_goals,
            "assists": tot_club_assists,
            "key_passes": sum(s["raw_stats"]["key_passes"] for s in seasons_stats.values()),
            "dribbles": sum(s["raw_stats"]["dribbles_completed"] for s in seasons_stats.values()),
            "saves": sum(s["advanced_stats"].get("saves", 0) for s in seasons_stats.values()),
            "save_pct": sum(s["advanced_stats"].get("save_pct", 0) for s in seasons_stats.values()) / 3.0,
            "clean_sheets": sum(s["advanced_stats"].get("clean_sheets", 0) for s in seasons_stats.values()),
            "sweeper_actions": sum(s["advanced_stats"].get("sweeper_actions", 0) for s in seasons_stats.values())
        },
        "country": {
            "rating": round(avg_club_rating + 0.3, 2),
            "goals": int(tot_club_goals * 0.3),
            "assists": int(tot_club_assists * 0.3),
            "key_passes": int(sum(s["raw_stats"]["key_passes"] for s in seasons_stats.values()) * 0.25),
            "dribbles": int(sum(s["raw_stats"]["dribbles_completed"] for s in seasons_stats.values()) * 0.25),
            "saves": int(sum(s["advanced_stats"].get("saves", 0) for s in seasons_stats.values()) * 0.25),
            "save_pct": (sum(s["advanced_stats"].get("save_pct", 0) for s in seasons_stats.values()) / 3.0) + 4.0,
            "clean_sheets": int(sum(s["advanced_stats"].get("clean_sheets", 0) for s in seasons_stats.values()) * 0.3),
            "sweeper_actions": int(sum(s["advanced_stats"].get("sweeper_actions", 0) for s in seasons_stats.values()) * 0.25)
        }
    }
    
    # Filter empty or zero goalkeeper keys if they are not GK
    if pos != "GK":
        for mapping in [club_vs_country["club"], club_vs_country["country"]]:
            mapping.pop("saves", None)
            mapping.pop("save_pct", None)
            mapping.pop("clean_sheets", None)
            mapping.pop("sweeper_actions", None)
    else:
        for mapping in [club_vs_country["club"], club_vs_country["country"]]:
            mapping.pop("goals", None)
            mapping.pop("assists", None)
            mapping.pop("key_passes", None)
            mapping.pop("dribbles", None)

    return {
        "id": None, # assigned dynamically in routes
        "name": name,
        "nationality": nationality,
        "position": pos,
        "team": team,
        "image_url": photo,
        "career_peak_season": "2025-26",
        "career_history": career_history,
        "tournament_pressure_trend": pressure_trend,
        "club_vs_country": club_vs_country,
        "seasons": seasons_stats
    }
