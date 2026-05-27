import math
from app.data.players import PLAYERS_DB
from app.engines.normalization import normalize_player_stats

def calculate_player_similarity(player_id: int) -> list[dict]:
    target_player = PLAYERS_DB.get(player_id)
    if not target_player:
        return []
        
    latest_season = "2025-26"
    stats_target = target_player["seasons"].get(latest_season, target_player["seasons"]["2025-26"])
    version_target = {
        "id": target_player["id"],
        "name": target_player["name"],
        "nationality": target_player["nationality"],
        "position": target_player["position"],
        "image_url": target_player["image_url"],
        "team": stats_target["team"],
        "league": stats_target["league"],
        "age": stats_target["age"],
        **stats_target
    }
    
    norm_target = normalize_player_stats(version_target)
    target_pos = target_player["position"]
    
    similarities = []
    
    # We compare based on key metrics (depending on target's position)
    is_gk = (target_pos == "GK")
    
    # Determine which attributes we compare
    if is_gk:
        compare_keys = [
            ("advanced_stats", "saves"),
            ("advanced_stats", "save_pct"),
            ("advanced_stats", "clean_sheets"),
            ("defensive_stats", "aerial_duels_won"),
            ("advanced_stats", "sweeper_actions")
        ]
    else:
        # Standard players: goals, assists, xG, xA, dribbles, tackles
        compare_keys = [
            ("raw_stats", "goals"),
            ("raw_stats", "assists"),
            ("raw_stats", "xG"),
            ("raw_stats", "xA"),
            ("raw_stats", "dribbles_completed"),
            ("defensive_stats", "tackles")
        ]
        
    for other_id, other_player in PLAYERS_DB.items():
        if other_id == player_id:
            continue
            
        other_pos = other_player["position"]
        # Goalkeepers can only be similar to goalkeepers, outfielders to outfielders
        if (is_gk and other_pos != "GK") or (not is_gk and other_pos == "GK"):
            continue
            
        stats_other = other_player["seasons"].get(latest_season, other_player["seasons"]["2025-26"])
        version_other = {
            "id": other_player["id"],
            "name": other_player["name"],
            "nationality": other_player["nationality"],
            "position": other_player["position"],
            "image_url": other_player["image_url"],
            "team": stats_other["team"],
            "league": stats_other["league"],
            "age": stats_other["age"],
            **stats_other
        }
        
        norm_other = normalize_player_stats(version_other)
        
        # Calculate Euclidean Distance
        dist_sq = 0.0
        for cat, key in compare_keys:
            val_target = norm_target.get(cat, {}).get(key, 0.0)
            val_other = norm_other.get(cat, {}).get(key, 0.0)
            
            # Scale difference so stats with large numbers don't dominate
            max_val = max(val_target, val_other, 1.0)
            diff = (val_target - val_other) / max_val
            dist_sq += diff ** 2
            
        distance = math.sqrt(dist_sq)
        # Convert distance to similarity score (0 to 100)
        similarity_pct = round(100.0 / (1.0 + distance * 1.5), 1)
        
        similarities.append({
            "player_id": other_player["id"],
            "name": other_player["name"],
            "team": other_player["team"],
            "position": other_player["position"],
            "nationality": other_player["nationality"],
            "similarity_percentage": similarity_pct
        })
        
    # Sort by similarity descending
    similarities.sort(key=lambda x: x["similarity_percentage"], reverse=True)
    return similarities[:3]
