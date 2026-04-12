from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Ensure this import is correct based on your file structure
from api.routes import router as race_router

app = FastAPI(title="SinCircuit AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(race_router, prefix="/race")