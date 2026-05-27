import os
import json
from fastapi import APIRouter, HTTPException, Query
from app.data.players import PLAYERS_DB
from app.models.schemas import PlayerSummary
from app.engines.normalization import normalize_player_stats
from app.engines.similarity import calculate_player_similarity
from app.services.api_football import (
    is_api_configured,
    search_live_players,
    fetch_player_season_stats,
    map_stats_to_schema
)

router = APIRouter()

@router.get("/", response_model=list[PlayerSummary])
def get_players():
    result = []
    for pid, p in PLAYERS_DB.items():
        latest = p["seasons"]["2025-26"]
        result.append(PlayerSummary(
            id=p["id"],
            name=p["name"],
            nationality=p["nationality"],
            position=p["position"],
            team=p["team"],
            league=latest["league"],
            age=latest["age"],
            image_url=p["image_url"]
        ))
    return result

@router.get("/search/live")
def search_live(query: str = Query(..., min_length=2)):
    """Searches for players live on API-Football."""
    if not is_api_configured():
        raise HTTPException(
            status_code=400,
            detail="RapidAPI Key is not configured in backend .env file. Please add RAPIDAPI_KEY."
        )
    
    results = search_live_players(query)
    return results

@router.post("/import/{api_football_id}")
def import_api_player(
    api_football_id: int, 
    position: str = "CM", 
    team_name: str = "Unknown", 
    league_name: str = "Unknown"
):
    """Imports a player by API-Football ID and adds them to PLAYERS_DB."""
    if not is_api_configured():
        raise HTTPException(
            status_code=400,
            detail="RapidAPI Key is not configured in backend .env file. Please add RAPIDAPI_KEY."
        )
        
    # Check if player already exists in database
    for pid, p in PLAYERS_DB.items():
        if p.get("api_football_id") == api_football_id:
            return p

    # Fetch stats for seasons 2025, 2024, 2023
    seasons_data = {}
    player_basic = {}
    
    for year in [2025, 2024, 2023]:
        raw_data = fetch_player_season_stats(api_football_id, year)
        if raw_data:
            seasons_data[year] = raw_data
            if not player_basic:
                player_basic = {
                    "name": raw_data.get("player", {}).get("name", "Unknown"),
                    "nationality": raw_data.get("player", {}).get("nationality", "Unknown"),
                    "age": raw_data.get("player", {}).get("age", 22),
                    "photo": raw_data.get("player", {}).get("photo", "/avatars/default.png"),
                    "position": position,
                    "team": team_name,
                    "league": league_name
                }
                
    if not player_basic:
        raise HTTPException(
            status_code=404,
            detail="Player statistics not found on API-Football for the target seasons."
        )

    # Convert/Map to internal schema
    new_player_data = map_stats_to_schema(seasons_data, player_basic)
    
    # Resolve new unique ID
    new_id = max(PLAYERS_DB.keys()) + 1
    new_player_data["id"] = new_id
    new_player_data["api_football_id"] = api_football_id
    
    # Save to in-memory DB
    PLAYERS_DB[new_id] = new_player_data
    
    # Persist to players.py
    players_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "players.py"))
    try:
        with open(players_filepath, "w", encoding="utf-8") as f:
            f.write("# Real-Data updated database (Expanded with Live Imports)\n")
            f.write("PLAYERS_DB = " + json.dumps(PLAYERS_DB, indent=4, ensure_ascii=False) + "\n")
            f.write("\n# Convert keys to integers to avoid string lookup errors from json-dumped keys\nPLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
    except Exception as e:
        print(f"[-] Error writing imported player to players.py: {e}")

    return new_player_data

@router.get("/{player_id}")
def get_player_details(player_id: int):
    player = PLAYERS_DB.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Return both raw and normalized stats
    normalized = normalize_player_stats(player)
    return {
        "raw": player,
        "normalized": normalized
    }

@router.get("/{player_id}/similarity")
def get_similar_players(player_id: int):
    player = PLAYERS_DB.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    similar = calculate_player_similarity(player_id)
    return similar
