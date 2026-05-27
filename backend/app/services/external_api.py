"""
WC26 Compare Engine - External API Integration Guide
This file serves as a production template demonstrating how to transition 
from mock data to a real API (e.g., API-Football via RapidAPI).
"""

import httpx
from typing import Dict, Any, Optional

RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY_HERE"
API_HOST = "api-football-v1.p.rapidapi.com"
BASE_URL = f"https://{API_HOST}/v3"

# Example mapping from API-Football structure to our internal DB structure
def map_api_football_to_schema(api_data: Dict[str, Any]) -> Dict[str, Any]:
    player_info = api_data.get("player", {})
    statistics = api_data.get("statistics", [{}])[0] # Get current season stats
    
    # Extract sub-categories
    games = statistics.get("games", {})
    goals = statistics.get("goals", {})
    passes = statistics.get("passes", {})
    tackles = statistics.get("tackles", {})
    duels = statistics.get("duels", {})
    dribbles = statistics.get("dribbles", {})
    
    # Resolve position to our codes (GK, ST, LW, CM, CAM)
    raw_pos = games.get("position", "Midfielder")
    pos_map = {
        "Goalkeeper": "GK",
        "Defender": "CM", # Fallback
        "Midfielder": "CAM", # Map to CAM or CM dynamically based on team role
        "Attacker": "ST"
    }
    mapped_pos = pos_map.get(raw_pos, "CAM")
    
    # Calculate per-90 metrics or use absolute metrics mapped to our keys
    apps = games.get("appearences", 1) or 1
    minutes = games.get("minutes", 90) or 90
    coef_per_90 = 90.0 / max(minutes, 1)

    return {
        "id": player_info.get("id"),
        "name": player_info.get("name"),
        "nationality": player_info.get("nationality"),
        "position": mapped_pos,
        "team": statistics.get("team", {}).get("name"),
        "league": statistics.get("league", {}).get("name"),
        "age": player_info.get("age"),
        "image_url": player_info.get("photo"),
        "season": statistics.get("league", {}).get("season", "2025-2026"),
        "raw_stats": {
            "goals": goals.get("total", 0) or 0,
            "assists": goals.get("assists", 0) or 0,
            "xG": round((goals.get("total", 0) or 0) * 0.9, 1), # API-Football lacks xG, we can estimate or fetch from StatsBomb
            "xA": round((goals.get("assists", 0) or 0) * 0.8, 1),
            "shots": statistics.get("shots", {}).get("total", 0) or 0,
            "shots_on_target": statistics.get("shots", {}).get("on", 0) or 0,
            "key_passes": passes.get("key", 0) or 0,
            "progressive_passes": int(passes.get("total", 0) * 0.25) if passes.get("total") else 0,
            "through_balls": int(passes.get("key", 0) * 0.15) if passes.get("key") else 0,
            "dribbles_completed": dribbles.get("success", 0) or 0,
            "dribbles_attempted": dribbles.get("attempts", 0) or 0,
            "crosses": int(passes.get("total", 0) * 0.1) if passes.get("total") else 0,
            "touches_in_box": int(statistics.get("shots", {}).get("total", 0) * 1.5) if statistics.get("shots") else 0,
            "passes_completed": passes.get("total", 0) or 0,
            "passes_attempted": int(passes.get("total", 0) / 0.85) if passes.get("total") else 0
        },
        "defensive_stats": {
            "tackles": tackles.get("total", 0) or 0,
            "interceptions": tackles.get("interceptions", 0) or 0,
            "clearances": tackles.get("blocks", 0) or 0,
            "blocks": tackles.get("blocks", 0) or 0,
            "aerial_duels_won": duels.get("won", 0) or 0, # Estimated
            "aerial_duels_total": duels.get("total", 0) or 0,
            "duels_won_pct": round((duels.get("won", 0) / max(duels.get("total", 0), 1)) * 100, 1),
            "recoveries": tackles.get("total", 0) * 2, # Estimate
            "fouls_committed": statistics.get("fouls", {}).get("committed", 0) or 0
        },
        "physical_stats": {
            "distance_covered_km": 10.5, # Static estimate
            "sprints": 25,
            "press_resistance": 85.0,
            "top_speed_kmh": 32.5
        },
        "advanced_stats": {
            # Map goalkeeper actions specifically
            "saves": statistics.get("goals", {}).get("saves", 0) or 0,
            "save_pct": 75.0, # Default estimate
            "clean_sheets": 10,
            "sweeper_actions": 15,
            "shot_creating_actions": passes.get("key", 0) * 2 if passes.get("key") else 0,
            "goal_creating_actions": goals.get("assists", 0) or 0
        },
        "big_match_stats": {
            "rating_top6": round(float(statistics.get("games", {}).get("rating", 7.2) or 7.2) + 0.2, 2),
            "goals_top6": int(goals.get("total", 0) * 0.2) if goals.get("total") else 0,
            "assists_top6": int(goals.get("assists", 0) * 0.2) if goals.get("assists") else 0,
            "clutch_goals": int(goals.get("total", 0) * 0.15) if goals.get("total") else 0
        },
        "international_stats": {
            "caps": 15,
            "goals": 2,
            "tournament_appearances": 4,
            "international_rating": 7.5
        },
        "wc_fit_factors": {
            "big_match_performance": 80,
            "pressure_handling": 85,
            "consistency": 78,
            "physical_intensity": 75,
            "international_experience": 60,
            "tactical_flexibility": 80
        },
        "form_ratings": [7.2, 7.5, 7.1, 7.8, 8.0, 7.4, 7.5, 7.6, 8.2, 7.3]
    }

async def fetch_real_player_stats(player_name: str, league_id: int, season: int) -> Optional[Dict[str, Any]]:
    """
    Fetches real player statistics from API-Football, maps it into the local schema
    and makes it ready for normalization and comparison.
    """
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": API_HOST
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Search player to get Player ID
        search_url = f"{BASE_URL}/players"
        params = {
            "search": player_name,
            "league": league_id,
            "season": season
        }
        
        response = await client.get(search_url, headers=headers, params=params)
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get("response", [])
        if not results:
            return None
            
        # 2. Extract and map the first matching player's data
        raw_player_data = results[0]
        mapped_player = map_api_football_to_schema(raw_player_data)
        
        return mapped_player
