import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import drawings, balloons, export

app = FastAPI(title="Automated Ballooning System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drawings.router, prefix="/api/drawings", tags=["Drawings"])
app.include_router(balloons.router, prefix="/api/balloons", tags=["Balloons"])
app.include_router(export.router,   prefix="/api/export",   tags=["Export"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "CAD Backend is running"}