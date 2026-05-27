from app.data.leagues import LEAGUE_COEFFICIENTS

def normalize_stat(metric_name: str, raw_value: float, league: str) -> float:
    coef = LEAGUE_COEFFICIENTS.get(league, 0.70) # default to 0.70 if unknown
    
    # Percentage metrics shouldn't be multiplied directly
    if metric_name.endswith("_pct") or metric_name.endswith("_rate") or "accuracy" in metric_name:
        # Scale the percentage down slightly based on league difficulty but maintain realistic limits
        # e.g., 90% pass accuracy in MLS becomes 90 * (1 - (1 - 0.62) * 0.15) = 84.8%
        discount = (1.0 - coef) * 0.15
        return round(raw_value * (1.0 - discount), 1)
        
    # Raw counters get multiplied directly
    # e.g., 20 goals in MLS = 20 * 0.62 = 12.4 normalized goals
    return round(raw_value * coef, 2)

def normalize_player_stats(player: dict) -> dict:
    normalized = player.copy()
    league = player.get("league", "Premier League")
    
    # Normalize raw stats
    normalized_raw = {}
    for k, v in player.get("raw_stats", {}).items():
        normalized_raw[k] = normalize_stat(k, v, league)
    normalized["raw_stats"] = normalized_raw
    
    # Normalize defensive stats
    normalized_def = {}
    for k, v in player.get("defensive_stats", {}).items():
        normalized_def[k] = normalize_stat(k, v, league)
    normalized["defensive_stats"] = normalized_def
    
    # Normalize physical stats
    normalized_phys = {}
    for k, v in player.get("physical_stats", {}).items():
        normalized_phys[k] = normalize_stat(k, v, league)
    normalized["physical_stats"] = normalized_phys
    
    # Normalize advanced stats
    normalized_adv = {}
    for k, v in player.get("advanced_stats", {}).items():
        normalized_adv[k] = normalize_stat(k, v, league)
    normalized["advanced_stats"] = normalized_adv

    return normalized
