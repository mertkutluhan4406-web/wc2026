from fastapi import APIRouter, HTTPException
from app.data.players import PLAYERS_DB
from app.models.schemas import CompareRequest, CompareResponse
from app.engines.comparison import run_comparison
from app.engines.ai_explain import generate_ai_explanation

router = APIRouter()

@router.post("/", response_model=CompareResponse)
def compare_players(request: CompareRequest):
    player_a = PLAYERS_DB.get(request.player_a_id)
    player_b = PLAYERS_DB.get(request.player_b_id)
    
    if not player_a or not player_b:
        raise HTTPException(status_code=404, detail="One or both players not found")
        
    if request.player_a_id == request.player_b_id:
        raise HTTPException(status_code=400, detail="Cannot compare player with themselves")
        
    # Execute the comparison
    comp_result = run_comparison(
        player_a, 
        player_b, 
        request.mode, 
        request.player_a_season, 
        request.player_b_season
    )
    
    # Generate AI insights
    ai_explanation = generate_ai_explanation(comp_result, player_a, player_b)
    
    # Merge AI explanation into comparison result
    comp_result["ai_explanation"] = ai_explanation
    
    return CompareResponse(**comp_result)
