from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1 import recommend, schedule

app = FastAPI(title="Festival Planner API", version="1.0.0")

# Configure CORS to allow Next.js to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our route files
app.include_router(artists.router, prefix="/api/v1", tags=["Artists"])
app.include_router(recommend.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(schedule.router, prefix="/api/v1", tags=["Schedule"])

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "Festival Backend is vibing."}