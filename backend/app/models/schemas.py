from pydantic import BaseModel, Field
from typing import Optional, Any

class PlayerSummary(BaseModel):
    id: int
    name: str
    nationality: str
    position: str
    team: str
    league: str
    age: int
    image_url: str

class CompareRequest(BaseModel):
    player_a_id: int
    player_b_id: int
    mode: str = "Overall"
    player_a_season: str = "2025-26"
    player_b_season: str = "2025-26"

class WcFitBreakdown(BaseModel):
    overall_fit_score: float
    breakdown: dict[str, float]

class CompareResponse(BaseModel):
    player_a_id: int
    player_b_id: int
    player_a_name: str
    player_b_name: str
    mode: str
    overall_a: float
    overall_b: float
    winner: str
    radar_data: list[dict[str, Any]]
    bar_data: list[dict[str, Any]]
    clutch_a: float
    clutch_b: float
    system_dependency_a: float
    system_dependency_b: float
    wc_fit_a: WcFitBreakdown
    wc_fit_b: WcFitBreakdown
    ai_explanation: dict[str, Any]
    
    # New Multi-Season and Historical Fields
    player_a_season: str
    player_b_season: str
    career_history_a: dict[str, dict[str, Any]]
    career_history_b: dict[str, dict[str, Any]]
    pressure_trend_a: dict[str, float]
    pressure_trend_b: dict[str, float]
    club_vs_country_a: dict[str, dict[str, Any]]
    club_vs_country_b: dict[str, dict[str, Any]]
