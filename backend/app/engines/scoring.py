def calculate_wc_fit(player: dict) -> dict:
    factors = player.get("wc_fit_factors", {})
    
    # Calculate weighted composite score
    score = (
        factors.get("big_match_performance", 80) * 0.25 +
        factors.get("pressure_handling", 80) * 0.15 +
        factors.get("consistency", 80) * 0.20 +
        factors.get("physical_intensity", 80) * 0.15 +
        factors.get("international_experience", 80) * 0.15 +
        factors.get("tactical_flexibility", 80) * 0.10
    )
    
    return {
        "overall_fit_score": round(score, 1),
        "breakdown": {
            "Big Match Performance (25%)": factors.get("big_match_performance", 80),
            "Pressure Handling (15%)": factors.get("pressure_handling", 80),
            "Consistency (20%)": factors.get("consistency", 80),
            "Physical Intensity (15%)": factors.get("physical_intensity", 80),
            "International Experience (15%)": factors.get("international_experience", 80),
            "Tactical Flexibility (10%)": factors.get("tactical_flexibility", 80)
        }
    }

def calculate_clutch_index(player: dict) -> float:
    # Big match ratings compared to regular form ratings
    form = player.get("form_ratings", [7.5])
    avg_form = sum(form) / len(form)
    
    big_match_rating = player.get("big_match_stats", {}).get("rating_top6", 7.5)
    
    # Clutch metric: ratio of big match rating to avg rating + bonus for clutch goals or shootout saves
    clutch_goals = player.get("big_match_stats", {}).get("clutch_goals", 0)
    shootout_saves = player.get("big_match_stats", {}).get("shootout_saves", 0)
    
    bonus = (clutch_goals * 2.5) + (shootout_saves * 3.0)
    ratio = big_match_rating / max(avg_form, 1.0)
    
    clutch_score = (ratio * 80) + bonus
    return min(round(clutch_score, 1), 100.0)

def calculate_system_dependency(player: dict) -> float:
    pos = player.get("position", "CM")
    
    if pos == "GK":
        # For keepers, dependency score reflects how much they rely on their defense.
        # High saves/shots faced ratio = active keeper, low dependency.
        adv = player.get("advanced_stats", {})
        saves = adv.get("saves", 50)
        xg_faced = adv.get("xG_faced", 40)
        
        # If they make many saves relative to xG faced, they are highly independent
        ratio = saves / max(xg_faced * 3, 1)
        score = 100.0 - (ratio * 100.0)
        return min(max(round(score, 1), 20.0), 95.0)
        
    elif pos == "ST":
        # Strikers are usually highly dependent on service (assists/crosses).
        # Box touches vs progressive carries/dribbles.
        box_touches = player.get("raw_stats", {}).get("touches_in_box", 50)
        dribbles = player.get("raw_stats", {}).get("dribbles_completed", 10)
        carries = player.get("advanced_stats", {}).get("progressive_carries", 10)
        
        # More box touches and fewer carries/dribbles = higher dependency
        independence = (dribbles + carries) / max(box_touches, 1)
        score = 90.0 - (independence * 40.0)
        return min(max(round(score, 1), 30.0), 98.0)
        
    else:
        # Midfielders/Wingers.
        # Self-creation (dribbles, shot creating actions) vs passing volume.
        passes = player.get("raw_stats", {}).get("passes_completed", 500)
        scas = player.get("advanced_stats", {}).get("shot_creating_actions", 40)
        dribbles = player.get("raw_stats", {}).get("dribbles_completed", 20)
        
        independence = (dribbles * 3 + scas * 2) / max(passes / 10, 1)
        score = 80.0 - (independence * 20.0)
        return min(max(round(score, 1), 25.0), 90.0)
