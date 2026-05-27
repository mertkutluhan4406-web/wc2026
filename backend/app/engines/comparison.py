from app.engines.normalization import normalize_player_stats
from app.engines.scoring import calculate_wc_fit, calculate_clutch_index, calculate_system_dependency
from app.data.positions import POSITIONS_CONFIG

def get_comparison_attributes(mode: str, pos_a: str, pos_b: str) -> dict:
    """Returns the metrics to compare based on mode and player positions."""
    is_gk_involved = (pos_a == "GK" or pos_b == "GK")
    
    if is_gk_involved:
        if mode == "Defensive" or mode == "Overall":
            return {
                "Shot Stopping (Saves)": ("advanced_stats", "saves"),
                "Save Efficiency (%)": ("advanced_stats", "save_pct"),
                "Clean Sheets": ("advanced_stats", "clean_sheets"),
                "Claiming / Aerial": ("defensive_stats", "aerial_duels_won"),
                "Sweeping Actions": ("advanced_stats", "sweeper_actions")
            }
        elif mode == "Passing" or mode == "Creativity":
            return {
                "Passing Volume": ("raw_stats", "passes_completed"),
                "Pass Accuracy (%)": ("raw_stats", "passes_completed"),
                "Distribution / Launch": ("raw_stats", "progressive_passes")
            }
        elif mode == "Physical":
            return {
                "Distance (km)": ("physical_stats", "distance_covered_km"),
                "Top Speed (km/h)": ("physical_stats", "top_speed_kmh"),
                "Press Resistance": ("physical_stats", "press_resistance")
            }
        else:
            return {
                "Shot Stopping (Saves)": ("advanced_stats", "saves"),
                "Save Efficiency (%)": ("advanced_stats", "save_pct"),
                "Clean Sheets": ("advanced_stats", "clean_sheets"),
                "Claiming / Aerial": ("defensive_stats", "aerial_duels_won"),
                "Sweeping Actions": ("advanced_stats", "sweeper_actions"),
                "Distribution": ("raw_stats", "progressive_passes")
            }
            
    if mode == "Offensive":
        return {
            "Goals": ("raw_stats", "goals"),
            "Expected Goals (xG)": ("raw_stats", "xG"),
            "Shots on Target": ("raw_stats", "shots_on_target"),
            "Touches in Box": ("raw_stats", "touches_in_box"),
            "Goal Actions": ("advanced_stats", "goal_creating_actions")
        }
    elif mode == "Defensive":
        return {
            "Tackles": ("defensive_stats", "tackles"),
            "Interceptions": ("defensive_stats", "interceptions"),
            "Recoveries": ("defensive_stats", "recoveries"),
            "Duels Won (%)": ("defensive_stats", "duels_won_pct"),
            "Aerial Duels Won": ("defensive_stats", "aerial_duels_won")
        }
    elif mode == "Creativity":
        return {
            "Assists": ("raw_stats", "assists"),
            "Expected Assists (xA)": ("raw_stats", "xA"),
            "Key Passes": ("raw_stats", "key_passes"),
            "Shot Actions": ("advanced_stats", "shot_creating_actions"),
            "Through Balls": ("raw_stats", "through_balls")
        }
    elif mode == "Dribbling":
        return {
            "Dribbles Completed": ("raw_stats", "dribbles_completed"),
            "Dribbles Attempted": ("raw_stats", "dribbles_attempted"),
            "Carries Progressed": ("advanced_stats", "progressive_carries"),
            "Box Entries": ("advanced_stats", "penalty_area_entries")
        }
    elif mode == "Passing":
        return {
            "Passes Completed": ("raw_stats", "passes_completed"),
            "Progression Passes": ("raw_stats", "progressive_passes"),
            "Crosses": ("raw_stats", "crosses"),
            "Through Balls": ("raw_stats", "through_balls")
        }
    elif mode == "Physical":
        return {
            "Distance (km)": ("physical_stats", "distance_covered_km"),
            "Sprints": ("physical_stats", "sprints"),
            "Top Speed (km/h)": ("physical_stats", "top_speed_kmh"),
            "Press Resistance": ("physical_stats", "press_resistance")
        }
    elif mode == "Big Match Performance":
        return {
            "Big Match Rating": ("big_match_stats", "rating_top6"),
            "Clutch Goals": ("big_match_stats", "clutch_goals"),
            "Big Match Assists": ("big_match_stats", "assists_top6")
        }
    elif mode == "World Cup Impact":
        return {
            "Int. Caps": ("international_stats", "caps"),
            "Int. Goals": ("international_stats", "goals"),
            "Tournament Apps": ("international_stats", "tournament_appearances"),
            "Int. Rating": ("international_stats", "international_rating")
        }
    else:
        pos = pos_a if pos_a in POSITIONS_CONFIG else "CAM"
        cfg = POSITIONS_CONFIG.get(pos)
        attrs = {}
        for k, v in cfg["radar_attributes"].items():
            attrs[k] = (v[0], v[1])
        return attrs

def run_comparison(
    player_a: dict, 
    player_b: dict, 
    mode: str, 
    season_a_code: str = "2025-26", 
    season_b_code: str = "2025-26"
) -> dict:
    # Resolve peak season if requested
    actual_season_a = player_a["career_peak_season"] if season_a_code == "Peak" else season_a_code
    actual_season_b = player_b["career_peak_season"] if season_b_code == "Peak" else season_b_code
    
    # Get stats for selected seasons
    stats_a = player_a["seasons"].get(actual_season_a, player_a["seasons"]["2025-26"])
    stats_b = player_b["seasons"].get(actual_season_b, player_b["seasons"]["2025-26"])
    
    # Create complete player sub-dictionary copies representing that season version
    version_a = {
        "id": player_a["id"],
        "name": player_a["name"],
        "nationality": player_a["nationality"],
        "position": player_a["position"],
        "image_url": player_a["image_url"],
        "team": stats_a["team"],
        "league": stats_a["league"],
        "age": stats_a["age"],
        **stats_a
    }
    
    version_b = {
        "id": player_b["id"],
        "name": player_b["name"],
        "nationality": player_b["nationality"],
        "position": player_b["position"],
        "image_url": player_b["image_url"],
        "team": stats_b["team"],
        "league": stats_b["league"],
        "age": stats_b["age"],
        **stats_b
    }

    # Normalize stats based on season version properties
    norm_a = normalize_player_stats(version_a)
    norm_b = normalize_player_stats(version_b)
    
    pos_a = version_a["position"]
    pos_b = version_b["position"]
    
    # Calculate scores
    wc_a = calculate_wc_fit(version_a)
    wc_b = calculate_wc_fit(version_b)
    
    clutch_a = calculate_clutch_index(version_a)
    clutch_b = calculate_clutch_index(version_b)
    
    dep_a = calculate_system_dependency(version_a)
    dep_b = calculate_system_dependency(version_b)
    
    # Get attributes
    attrs = get_comparison_attributes(mode, pos_a, pos_b)
    
    # Build chart data
    radar_data = []
    bar_data = []
    
    score_a_sum = 0
    score_b_sum = 0
    attr_count = 0
    
    for label, path in attrs.items():
        cat, key = path
        
        val_a_raw = version_a.get(cat, {}).get(key, 0.0)
        val_b_raw = version_b.get(cat, {}).get(key, 0.0)
        
        val_a_norm = norm_a.get(cat, {}).get(key, 0.0)
        val_b_norm = norm_b.get(cat, {}).get(key, 0.0)
        
        max_val = max(val_a_norm, val_b_norm, 1.0)
        if label.endswith("(%)") or "pct" in key or "rate" in key or "accuracy" in key or label == "Int. Rating" or label == "Big Match Rating":
            pct_a = min((val_a_norm / 100.0) * 100 if label.endswith("(%)") else (val_a_norm / 10.0) * 100, 100.0)
            pct_b = min((val_b_norm / 100.0) * 100 if label.endswith("(%)") else (val_b_norm / 10.0) * 100, 100.0)
        else:
            pct_a = round((val_a_norm / max_val) * 100, 1)
            pct_b = round((val_b_norm / max_val) * 100, 1)
            
        radar_data.append({
            "subject": label,
            version_a["name"]: pct_a,
            version_b["name"]: pct_b,
            "fullMark": 100
        })
        
        bar_data.append({
            "metric": label,
            version_a["name"]: val_a_norm,
            version_b["name"]: val_b_norm,
            "raw_a": val_a_raw,
            "raw_b": val_b_raw
        })
        
        score_a_sum += pct_a
        score_b_sum += pct_b
        attr_count += 1
        
    avg_score_a = round(score_a_sum / max(attr_count, 1), 1)
    avg_score_b = round(score_b_sum / max(attr_count, 1), 1)
    
    if avg_score_a > avg_score_b:
        winner = version_a["name"]
    elif avg_score_b > avg_score_a:
        winner = version_b["name"]
    else:
        winner = "Tie"

    return {
        "player_a_id": version_a["id"],
        "player_b_id": version_b["id"],
        "player_a_name": version_a["name"],
        "player_b_name": version_b["name"],
        "mode": mode,
        "overall_a": avg_score_a,
        "overall_b": avg_score_b,
        "winner": winner,
        "radar_data": radar_data,
        "bar_data": bar_data,
        "clutch_a": clutch_a,
        "clutch_b": clutch_b,
        "system_dependency_a": dep_a,
        "system_dependency_b": dep_b,
        "wc_fit_a": wc_a,
        "wc_fit_b": wc_b,
        
        # Pass seasonal and historical metadata
        "player_a_season": season_a_code,
        "player_b_season": season_b_code,
        "career_history_a": player_a["career_history"],
        "career_history_b": player_b["career_history"],
        "pressure_trend_a": player_a["tournament_pressure_trend"],
        "pressure_trend_b": player_b["tournament_pressure_trend"],
        "club_vs_country_a": player_a["club_vs_country"],
        "club_vs_country_b": player_b["club_vs_country"]
    }
