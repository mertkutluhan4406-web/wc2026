from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import players, compare, positions

app = FastAPI(
    title="WC26 Compare Engine API",
    description="Premium Football Intelligence Platform API",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Allow any local client in case of different dev environments
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(compare.router, prefix="/api/compare", tags=["Comparison"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "WC26 Compare Engine API",
        "version": "1.0.0",
        "documentation": "/docs"
    }
