from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Guardians MVP API")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Guardians MVP AI Engine is running"}

from api.v1.upload import router as upload_router
from api.v1.verify import router as verify_router

app.include_router(upload_router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(verify_router, prefix="/api/v1/verify", tags=["verify"])
