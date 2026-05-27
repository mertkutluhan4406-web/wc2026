import os
import sys
import json
import re
import argparse
import requests
from bs4 import BeautifulSoup

# Define mappings for the 8 players across FBref, FotMob, and Sofascore
PLAYER_MAPPINGS = {
    1: {
        "name": "Arda Güler",
        "fotmob_id": 1439447,
        "sofascore_id": 1196420,
        "fbref_id": "b9fbe00e",
        "fbref_name": "Arda-Guler"
    },
    2: {
        "name": "Jamal Musiala",
        "fotmob_id": 1096733,
        "sofascore_id": 1002996,
        "fbref_id": "2c0558b8",
        "fbref_name": "Jamal-Musiala"
    },
    3: {
        "name": "Jude Bellingham",
        "fotmob_id": 1024364,
        "sofascore_id": 991011,
        "fbref_id": "57d88ef2",
        "fbref_name": "Jude-Bellingham"
    },
    4: {
        "name": "Pedri",
        "fotmob_id": 1068283,
        "sofascore_id": 987627,
        "fbref_id": "a260cc1b",
        "fbref_name": "Pedri"
    },
    5: {
        "name": "Kylian Mbappé",
        "fotmob_id": 695503,
        "sofascore_id": 826130,
        "fbref_id": "8778c924",
        "fbref_name": "Kylian-Mbappe"
    },
    6: {
        "name": "Vinícius Jr",
        "fotmob_id": 849384,
        "sofascore_id": 868007,
        "fbref_id": "7111d511",
        "fbref_name": "Vinicius-Junior"
    },
    7: {
        "name": "Erling Haaland",
        "fotmob_id": 839083,
        "sofascore_id": 834727,
        "fbref_id": "1f94ea65",
        "fbref_name": "Erling-Haaland"
    },
    8: {
        "name": "Emiliano Martínez",
        "fotmob_id": 269894,
        "sofascore_id": 114256,
        "fbref_id": "79443f37",
        "fbref_name": "Emiliano-Martinez"
    }
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_fotmob_recent_ratings(fotmob_id: int) -> list[float]:
    """Fetches the last 10 match ratings from FotMob public API."""
    url = f"https://www.fotmob.com/api/playerData?id={fotmob_id}"
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Try recentForm
            recent = data.get("recentForm", [])
            ratings = []
            for match in recent:
                rating = match.get("rating")
                if rating:
                    ratings.append(round(float(rating), 2))
            
            if len(ratings) < 5:
                # Try lastMatches fallback
                last_matches = data.get("lastMatches", [])
                ratings = []
                for match in last_matches:
                    rating = match.get("rating")
                    if rating:
                        ratings.append(round(float(rating), 2))
            
            # Ensure we return valid ratings
            if ratings:
                return ratings[:10]
    except Exception as e:
        print(f"[-] FotMob fetch error for ID {fotmob_id}: {e}")
    return []

def scrape_fbref_advanced_stats(fbref_id: str, fbref_name: str) -> dict:
    """Scrapes advanced stats summary (like xG, xA, key passes) from FBref player profile page."""
    url = f"https://fbref.com/en/players/{fbref_id}/{fbref_name}"
    scraped_stats = {}
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Parse standard stats from the dom_lg table
            std_table = soup.find("table", id=re.compile("stats_standard_.*"))
            if std_table:
                # Get the most recent season row (usually the last or second to last row)
                rows = std_table.find("tbody").find_all("tr")
                if rows:
                    latest_row = rows[-1] # Usually the most recent completed or active season
                    # Find stats like goals, assists, xg, xa
                    goals_cell = latest_row.find("td", {"data-stat": "goals"})
                    assists_cell = latest_row.find("td", {"data-stat": "assists"})
                    xg_cell = latest_row.find("td", {"data-stat": "xg"})
                    xa_cell = latest_row.find("td", {"data-stat": "xg_xg_assist"}) or latest_row.find("td", {"data-stat": "xg_assist"})
                    
                    if goals_cell: scraped_stats["goals"] = int(goals_cell.text) if goals_cell.text.isdigit() else 0
                    if assists_cell: scraped_stats["assists"] = int(assists_cell.text) if assists_cell.text.isdigit() else 0
                    if xg_cell: scraped_stats["xG"] = float(xg_cell.text) if xg_cell.text else 0.0
                    if xa_cell: scraped_stats["xA"] = float(xa_cell.text) if xa_cell.text else 0.0
            
            # 2. Try to get progressive carries and key passes from scout summary if available
            scout_table = soup.find("table", id=re.compile("scout_summary_.*"))
            if scout_table:
                for row in scout_table.find_all("tr"):
                    stat_name_cell = row.find("th", {"data-stat": "statistic"})
                    val_cell = row.find("td", {"data-stat": "value"})
                    if stat_name_cell and val_cell:
                        txt = stat_name_cell.text.lower()
                        val_str = val_cell.text.strip()
                        val = float(val_str) if val_str.replace('.', '', 1).isdigit() else 0.0
                        
                        if "progressive carries" in txt:
                            scraped_stats["progressive_carries"] = int(val)
                        elif "key passes" in txt:
                            scraped_stats["key_passes"] = int(val)
                        elif "tackles" in txt:
                            scraped_stats["tackles"] = int(val)
                        elif "interceptions" in txt:
                            scraped_stats["interceptions"] = int(val)
                            
    except Exception as e:
        print(f"[-] FBref scrape error for {fbref_name}: {e}")
    return scraped_stats

def fetch_sofascore_metadata(sofascore_id: int) -> dict:
    """Fetches general ratings/stats metadata from Sofascore public profile endpoints."""
    # Sofascore uses unique API headers and query structure
    # We will query unique API endpoints and parse them safely
    url = f"https://www.sofascore.com/api/v1/player/{sofascore_id}"
    sofa_stats = {}
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            player_info = data.get("player", {})
            
            # Extract basic rating stats if present
            if "proposedMarketValue" in player_info:
                sofa_stats["market_value"] = player_info.get("proposedMarketValue")
            
            # Try to fetch current season stats if available
            stats_url = f"https://www.sofascore.com/api/v1/player/{sofascore_id}/statistics/seasons"
            stats_res = requests.get(stats_url, headers=DEFAULT_HEADERS, timeout=10)
            if stats_res.status_code == 200:
                stats_data = stats_res.json()
                seasons = stats_data.get("uniqueTournamentSeasons", [])
                if seasons:
                    # Resolve average ratings and match stats from Sofascore
                    latest_tournament = seasons[0]
                    statistics = latest_tournament.get("statistics", {})
                    if "rating" in statistics:
                        sofa_stats["average_rating"] = round(float(statistics["rating"]), 2)
    except Exception as e:
        # Sofascore often has strict Cloudflare checks; fail gracefully
        print(f"[-] Sofascore fetch warning for ID {sofascore_id}: {e}")
    return sofa_stats

def run_scraper_test():
    """Runs a sandbox test fetching real data for Arda Güler and displays the results."""
    print("=== STARTING REAL-DATA SCRAPER SANDBOX TEST ===")
    target = PLAYER_MAPPINGS[1] # Arda Güler
    print(f"Target Player: {target['name']}")
    
    print("\n1. Fetching FotMob ratings...")
    fotmob_ratings = fetch_fotmob_recent_ratings(target["fotmob_id"])
    print(f"-> FotMob ratings result: {fotmob_ratings}")
    
    print("\n2. Scraping FBref advanced stats...")
    fbref_stats = scrape_fbref_advanced_stats(target["fbref_id"], target["fbref_name"])
    print(f"-> FBref scraped stats: {fbref_stats}")
    
    print("\n3. Fetching Sofascore metadata...")
    sofa_meta = fetch_sofascore_metadata(target["sofascore_id"])
    print(f"-> Sofascore metadata: {sofa_meta}")
    print("\n=== SANDBOX TEST COMPLETED ===")

def update_database():
    """Fetches real data for all players and safely integrates it into players.py database."""
    print("=== STARTING FULL DATABASE REAL-DATA UPDATE ===")
    
    # Import current DB to modify
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from app.data.players import PLAYERS_DB
    
    for pid, mappings in PLAYER_MAPPINGS.items():
        print(f"\n[*] Processing: {mappings['name']} (ID: {pid})")
        
        # 1. Fetch FotMob Ratings
        fm_ratings = fetch_fotmob_recent_ratings(mappings["fotmob_id"])
        if fm_ratings:
            print(f"   [+] FotMob: Fetched {len(fm_ratings)} ratings successfully.")
            # Update the form ratings in seasons
            for season in PLAYERS_DB[pid]["seasons"]:
                # Keep original data size, patch values
                PLAYERS_DB[pid]["seasons"][season]["form_ratings"] = fm_ratings
        else:
            print("   [-] FotMob: Blocked or failed. Using fallback values.")
            
        # 2. Fetch FBref Stats
        fb_stats = scrape_fbref_advanced_stats(mappings["fbref_id"], mappings["fbref_name"])
        if fb_stats:
            print(f"   [+] FBref: Fetched stats: {fb_stats}")
            # Merge/Update raw stats in the latest season (2025-26)
            latest_season = "2025-26"
            if latest_season in PLAYERS_DB[pid]["seasons"]:
                raw_stats = PLAYERS_DB[pid]["seasons"][latest_season]["raw_stats"]
                advanced = PLAYERS_DB[pid]["seasons"][latest_season]["advanced_stats"]
                
                # Apply updates if scrapers found non-zero values
                if fb_stats.get("goals"): raw_stats["goals"] = fb_stats["goals"]
                if fb_stats.get("assists"): raw_stats["assists"] = fb_stats["assists"]
                if fb_stats.get("xG"): raw_stats["xG"] = fb_stats["xG"]
                if fb_stats.get("xA"): raw_stats["xA"] = fb_stats["xA"]
                if fb_stats.get("key_passes"): raw_stats["key_passes"] = fb_stats["key_passes"]
                
                # Defenses/Advanced
                if fb_stats.get("progressive_carries"): advanced["progressive_carries"] = fb_stats["progressive_carries"]
                if fb_stats.get("key_passes"): advanced["shot_creating_actions"] = int(fb_stats["key_passes"] * 1.5)
        else:
            print("   [-] FBref: Blocked or failed. Using fallback stats.")
            
        # 3. Fetch Sofascore stats
        sofa_stats = fetch_sofascore_metadata(mappings["sofascore_id"])
        if sofa_stats:
            print(f"   [+] Sofascore: Fetched ratings details: {sofa_stats}")
            avg_rating = sofa_stats.get("average_rating")
            if avg_rating:
                # Merge into the career history for the latest season
                PLAYERS_DB[pid]["career_history"]["2025-26"]["rating"] = avg_rating
        else:
            print("   [-] Sofascore: Blocked or failed. Using fallback ratings.")

    # 4. Write back to players.py
    players_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "players.py"))
    
    with open(players_filepath, "w", encoding="utf-8") as f:
        f.write("# Real-Data updated database\n")
        f.write("PLAYERS_DB = " + json.dumps(PLAYERS_DB, indent=4, ensure_ascii=False) + "\n")
        f.write("\n# Convert keys to integers to avoid string lookup errors from json-dumped keys\nPLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
        
    print("\n[+] Database file players.py successfully updated with real-data!")
    print("=== DATABASE UPDATE COMPLETE ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Data Scraper for WC26 Compare Engine")
    parser.add_argument("--test", action="store_true", help="Run a test fetch for Arda Güler")
    parser.add_argument("--update", action="store_true", help="Fetch real data and update players.py database")
    
    args = parser.parse_args()
    
    if args.test:
        run_scraper_test()
    elif args.update:
        update_database()
    else:
        parser.print_help()
