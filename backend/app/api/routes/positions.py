from fastapi import APIRouter
from app.data.positions import POSITIONS_CONFIG

router = APIRouter()

@router.get("/")
def get_positions():
    return POSITIONS_CONFIG
