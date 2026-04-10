from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as race_router

app = FastAPI(title="SinCircuit AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefixing everything with /race so your URLs are /race/start, /race/tick, etc.
app.include_router(race_router, prefix="/race")

@app.get("/")
def health_check():
    return {"status": "Engine Online"}