from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.database import engine, Base
from backend.app.api import auth, locations, ws

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EcoVision AI+",
    description="Smart Real-Time Sustainable Construction Decision Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(locations.router)
app.include_router(ws.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to EcoVision AI+ API"}
