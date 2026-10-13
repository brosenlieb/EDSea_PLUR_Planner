"""
Module to initialize the FastAPI application.

This module sets up the FastAPI instance, configures CORS middleware to allow
communication with the Next.js frontend, and registers the API routers for
artists, recommendations, schedule, and activities.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from backend.app.api.v1 import recommend, schedule, artists, activities

app = FastAPI(title="Festival Planner API", version="1.0.0")

# Configure CORS to allow Next.js to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our route files
app.include_router(artists.router, prefix="/api/v1", tags=["Artists"])
app.include_router(recommend.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(schedule.router, prefix="/api/v1", tags=["Schedule"])
app.include_router(activities.router, prefix="/api/v1", tags=["Activities"])

@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns a simple status message to verify that the backend service is running.

    Returns:
        dict: A dictionary containing the current status of the service.
    """
    return {"status": "Festival Backend is vibing."}