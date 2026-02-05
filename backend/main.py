from fastapi import FastAPI
from . import models, database
from .routers import auth, robots, emergency

# Create Database Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Robot Companion API", version="0.1.0")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router)
app.include_router(robots.router)
app.include_router(emergency.router)

@app.get("/")
async def read_root():
    return {"status": "online", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
