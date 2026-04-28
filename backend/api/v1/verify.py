"""
verify.py — Verification API Endpoints
=======================================
POST /api/v1/verify/compare   : compares two uploaded videos and returns a forensic decision.
POST /api/v1/verify/log_threat: logs a confirmed threat to Firestore.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
import shutil
import uuid
import logging
from typing import Dict, Any

from services.media_processor import extract_frames
from services.fast_path import compare_frame_sets
# deep_path and vector_db are DISABLED for Hybrid MVP — reserved for future semantic layer

from services.firestore_client import log_threat

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "guardians_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _save_upload(upload_file: UploadFile) -> str:
    """Writes an uploaded file to disk and returns its path."""
    ext = upload_file.filename.rsplit(".", 1)[-1] if "." in upload_file.filename else "bin"
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return path


def _cleanup(*paths: str) -> None:
    """Silently removes temporary files."""
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


# ─── /compare ────────────────────────────────────────────────────────────────

@router.post("/compare")
def verify_video(
    original_video: UploadFile = File(...),
    suspicious_video: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Forensic comparison endpoint.

    Accepts two video files:
        original_video   — the reference (protected) asset.
        suspicious_video — the media under investigation.

    Returns a full forensic report including classification, confidence score,
    per-frame match flags, and Hamming distance statistics.
    """
    # ── Validate MIME types ───────────────────────────────────────────────────
    for f in (original_video, suspicious_video):
        if not f.content_type.startswith("video/"):
            raise HTTPException(
                status_code=400,
                detail=f"'{f.filename}' is not a video file (got {f.content_type}).",
            )

    original_path: str = ""
    suspicious_path: str = ""

    try:
        # ── 1. Persist uploads ────────────────────────────────────────────────
        original_path   = _save_upload(original_video)
        suspicious_path = _save_upload(suspicious_video)
        logger.info(f"[Verify] Saved: {original_path}, {suspicious_path}")

        # ── 2. Extract frames (10 per video) ──────────────────────────────────
        original_frames   = extract_frames(original_path,   num_frames=10)
        suspicious_frames = extract_frames(suspicious_path, num_frames=10)

        if not original_frames:
            raise HTTPException(status_code=422, detail="Could not extract frames from the original video.")
        if not suspicious_frames:
            raise HTTPException(status_code=422, detail="Could not extract frames from the suspicious video.")

        # ── 3. Run pHash detection engine (ACTIVE LAYER) ──────────────────────
        result = compare_frame_sets(original_frames, suspicious_frames)

        # ── 4. Deep Path — DISABLED FOR HYBRID MVP ────────────────────────────
        # if False:  # Reserved for future semantic CLIP layer
        #     from services.deep_path import compare_deep_features
        #     deep_result = compare_deep_features(original_frames, suspicious_frames)

        logger.info(
            f"[Verify] Decision: {result['status']} | "
            f"Confidence: {result['confidence_score']} | "
            f"Match: {result['matched_frames']}/{result['total_frames']}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Verify] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        original_video.file.close()
        suspicious_video.file.close()
        # Optionally remove temporary files to save disk space
        # _cleanup(original_path, suspicious_path)


# ─── /log_threat ─────────────────────────────────────────────────────────────

class ThreatLog(BaseModel):
    status: str
    confidenceScore: float
    detectionMethod: str = "pHash_Only"


@router.post("/log_threat")
def log_threat_endpoint(threat: ThreatLog) -> Dict[str, Any]:
    """
    Receives a threat report from the frontend and persists it to Firestore.
    Called automatically when status is PIRATED or SUSPICIOUS.
    """
    try:
        threat_id = str(uuid.uuid4())
        threat_data = {
            "status": threat.status,
            "confidenceScore": threat.confidenceScore,
            "detectionMethod": threat.detectionMethod,
            "timestamp": "auto",
        }
        log_threat(threat_id, threat_data)
        logger.info(f"[ThreatLog] Logged threat {threat_id}: {threat.status} @ {threat.confidenceScore:.1f}%")
        return {"status": "success", "threat_id": threat_id}
    except Exception as e:
        logger.error(f"[ThreatLog] Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to log threat: {str(e)}")
