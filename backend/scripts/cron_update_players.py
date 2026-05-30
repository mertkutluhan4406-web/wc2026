import sys
import os
import requests
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Set paths
sys.path.insert(0, r"C:\WC2026\backend")
from app.data.players import PLAYERS_DB
from app.services.api_football import fetch_player_season_stats, map_stats_to_schema, is_api_configured

PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

# Load environment key
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Hangi sezonun çekileceği (2025 = 2025-26 Sezonu, 2024 = 2024-25 Sezonu)
# Ücretsiz pakette 2025 engelli olduğu için eğer ücretsiz kalacaksanız burayı 2024 yapabilirsiniz.
TARGET_YEAR = 2024
TARGET_SEASON_CODE = "2024-25"

def main():
    print("=" * 60)
    print(f"DAILY BACKGROUND PLAYER UPDATE - SEASON {TARGET_SEASON_CODE}")
    print("=" * 60)
    
    if not is_api_configured():
        print("API Key is not configured in .env file. Exiting.")
        return

    # Find players with API ID but still using default/baseline stats in target season
    target_players = []
    for pid, p in PLAYERS_DB.items():
        latest_season = p.get("seasons", {}).get(TARGET_SEASON_CODE, {})
        if p.get("api_football_id") and (
            not latest_season or latest_season.get("league") in ["World Cup 2026", "World Cup", "Unknown", None]
        ):
            target_players.append(pid)

    print(f"Total players remaining to update for {TARGET_SEASON_CODE}: {len(target_players)}")
    if not target_players:
        print(f"All players have been successfully updated with real {TARGET_SEASON_CODE} stats! Exiting.")
        return

    # Update 100 players per run (1 API call per player = 100 API calls total, matching the daily limit)
    batch = target_players[:100]
    print(f"Selected {len(batch)} players for tonight's update batch.")

    updated_count = 0
    for pid in batch:
        player = PLAYERS_DB[pid]
        api_football_id = player["api_football_id"]
        print(f"\nUpdating player: {player['name']} (ID: {pid}, API ID: {api_football_id})")
        
        # Rate limit safety: 10 requests per minute = 6.5 seconds delay between requests
        time.sleep(6.5)
        
        seasons_data = {}
        try:
            raw_data = fetch_player_season_stats(api_football_id, TARGET_YEAR)
            if raw_data:
                seasons_data[TARGET_YEAR] = raw_data
        except Exception as e:
            print(f"  Error fetching season {TARGET_YEAR}: {e}")
        
        if seasons_data:
            latest_season = player.get("seasons", {}).get(TARGET_SEASON_CODE, {})
            player_basic = {
                "name": player["name"],
                "nationality": player["nationality"],
                "age": latest_season.get("age", 25),
                "photo": player.get("image_url") or "/avatars/default.png",
                "position": player["position"],
                "team": player["team"],
                "league": "Unknown"
            }
            
            try:
                # Map to our schema (it will map only the TARGET_YEAR and leave other seasons unchanged or generated)
                new_player_data = map_stats_to_schema(seasons_data, player_basic)
                
                # Merge: Preserve all other seasons in players.py
                for sk in player.get("seasons", {}):
                    if sk != TARGET_SEASON_CODE:
                        new_player_data["seasons"][sk] = player["seasons"][sk]
                for sk in player.get("career_history", {}):
                    if sk != TARGET_SEASON_CODE:
                        new_player_data["career_history"][sk] = player["career_history"][sk]
                        
                new_player_data["id"] = pid
                new_player_data["api_football_id"] = api_football_id
                
                # Keep Transfermarkt details and metadata
                for field in ["market_value", "height", "foot", "contract_until", "image_url"]:
                    if field in player:
                        new_player_data[field] = player[field]
                
                # Save in memory
                PLAYERS_DB[pid] = new_player_data
                updated_count += 1
                print(f"  Successfully updated stats for {player['name']}")
            except Exception as e:
                print(f"  Error mapping stats for {player['name']}: {e}")
        else:
            print(f"  No season stats could be retrieved for {player['name']}. API quota might be exhausted or season is blocked on your plan.")

    if updated_count > 0:
        # Write back to players.py
        print("\nSaving updated database to players.py...")
        try:
            with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
                f.write("# Real-Data updated database (Expanded with Live Imports)\n")
                f.write("PLAYERS_DB = " + json.dumps(PLAYERS_DB, indent=4, ensure_ascii=False) + "\n")
                f.write("\n# Convert keys to integers to avoid string lookup errors from json-dumped keys\nPLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
            print(f"Saved database. Updated {updated_count} players.")
        except Exception as e:
            print(f"Error saving database file: {e}")
    else:
        print("\nNo database updates were made in this run.")

if __name__ == "__main__":
    main()
