POSITIONS_CONFIG = {
    "ST": {
        "name": "Striker",
        "key_metrics": ["goals", "xG", "shots_on_target", "touches_in_box", "aerial_duels_won"],
        "radar_attributes": {
            "Finishing": ("raw_stats", "goals", 1.0),
            "Expected Goals": ("raw_stats", "xG", 1.0),
            "Shot Quality": ("raw_stats", "shots_on_target", 1.0),
            "Box Presence": ("raw_stats", "touches_in_box", 1.0),
            "Aerial Threat": ("defensive_stats", "aerial_duels_won", 1.0),
            "Physical Power": ("physical_stats", "top_speed_kmh", 1.0)
        }
    },
    "LW": {
        "name": "Winger / Left Wing",
        "key_metrics": ["goals", "dribbles_completed", "penalty_area_entries", "shot_creating_actions", "top_speed_kmh"],
        "radar_attributes": {
            "Goal Scoring": ("raw_stats", "goals", 1.0),
            "Dribbling": ("raw_stats", "dribbles_completed", 1.0),
            "Pace / Sprints": ("physical_stats", "sprints", 1.0),
            "Box Penetration": ("advanced_stats", "penalty_area_entries", 1.0),
            "Chance Creation": ("advanced_stats", "shot_creating_actions", 1.0),
            "Creativity": ("raw_stats", "xA", 1.0)
        }
    },
    "CAM": {
        "name": "Central Attacking Midfielder",
        "key_metrics": ["key_passes", "xA", "progressive_passes", "through_balls", "press_resistance"],
        "radar_attributes": {
            "Chance Creation": ("raw_stats", "key_passes", 1.0),
            "Expected Assists": ("raw_stats", "xA", 1.0),
            "Playmaking": ("raw_stats", "progressive_passes", 1.0),
            "Vision / Through": ("raw_stats", "through_balls", 1.0),
            "Press Resistance": ("physical_stats", "press_resistance", 1.0),
            "Dribble Progress": ("raw_stats", "dribbles_completed", 1.0)
        }
    },
    "CM": {
        "name": "Central Midfielder",
        "key_metrics": ["passes_completed", "tackles", "recoveries", "progressive_passes", "distance_covered_km"],
        "radar_attributes": {
            "Passing Volume": ("raw_stats", "passes_completed", 1.0),
            "Defensive Work": ("defensive_stats", "tackles", 1.0),
            "Ball Recovery": ("defensive_stats", "recoveries", 1.0),
            "Progression": ("raw_stats", "progressive_passes", 1.0),
            "Engine / Workrate": ("physical_stats", "distance_covered_km", 1.0),
            "Press Resistance": ("physical_stats", "press_resistance", 1.0)
        }
    },
    "GK": {
        "name": "Goalkeeper",
        "key_metrics": ["saves", "save_pct", "clean_sheets", "sweeper_actions", "aerial_duels_won"],
        "radar_attributes": {
            "Shot Stopping": ("advanced_stats", "saves", 1.0),
            "Save Efficiency": ("advanced_stats", "save_pct", 1.0),
            "Clean Sheets": ("advanced_stats", "clean_sheets", 1.0),
            "Cross Claiming": ("defensive_stats", "aerial_duels_won", 1.0),
            "Sweeping Actions": ("advanced_stats", "sweeper_actions", 1.0),
            "Distribution": ("raw_stats", "progressive_passes", 1.0)
        }
    }
}
