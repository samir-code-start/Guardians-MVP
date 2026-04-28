from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
import uuid
from typing import Dict, Any

from services.media_processor import extract_frames
from services.fast_path import compute_phash
from services.deep_path import generate_embedding
from services.vector_db import insert_embedding
from services.firestore_client import store_asset_metadata

router = APIRouter()

UPLOAD_DIR = os.environ.get(
    "UPLOAD_DIR",
    "/tmp/guardians_uploads" if os.environ.get("VERCEL") else "guardians_uploads",
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
def upload_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video files are allowed")
    
    file_extension = file.filename.split(".")[-1]
    asset_id = str(uuid.uuid4())
    unique_filename = f"{asset_id}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract frames
        frames = extract_frames(file_path, num_frames=3)
        if not frames:
            raise HTTPException(status_code=500, detail="Failed to extract frames from video.")
            
        # Generate features for the first frame as representative
        rep_frame = frames[0]
        phash_val = compute_phash(rep_frame)
        embedding = generate_embedding(rep_frame)
        
        metadata = {
            "asset_id": asset_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "phash": phash_val
        }
        
        # Store in Vector DB and Firestore
        insert_embedding(embedding, asset_id, metadata={"filename": file.filename})
        store_asset_metadata(asset_id, metadata)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save and process file: {str(e)}")
    finally:
        file.file.close()
        
    return {
        "message": "File uploaded and registered successfully",
        "asset_id": asset_id,
        "file_path": file_path,
        "filename": file.filename
    }
