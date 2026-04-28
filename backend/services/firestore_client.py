"""
firestore_client.py — Firestore Integration (Graceful Fallback Mode)
=====================================================================
Attempts to connect to Firestore if credentials are available.
All failures are caught and logged silently — Firestore logging is
non-critical for the MVP and must NEVER crash the verify pipeline.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_db = None
_init_failed = False   # prevent repeated init attempts


def _try_init_firestore() -> bool:
    """
    Lazily initialises Firebase Admin SDK.
    Returns True on success, False on any failure.
    Sets _init_failed=True so we don't retry on every request.
    """
    global _db, _init_failed

    if _init_failed:
        return False
    if _db is not None:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fs
        from core.config import settings

        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                "projectId": settings.FIREBASE_PROJECT_ID,
            })

        _db = fs.client()
        logger.info("[Firestore] Initialized successfully.")
        return True

    except Exception as e:
        _init_failed = True
        logger.warning(
            f"[Firestore] Initialization failed — operating in no-op mode. "
            f"Reason: {e}"
        )
        return False


def store_asset_metadata(asset_id: str, metadata: dict) -> None:
    """
    Stores video asset metadata in Firestore 'assets' collection.
    Silently no-ops if Firestore is unavailable.
    """
    if not _try_init_firestore():
        logger.debug(f"[Firestore] store_asset_metadata skipped (no-op) for {asset_id}")
        return
    try:
        _db.collection("assets").document(asset_id).set(metadata)
        logger.debug(f"[Firestore] Stored asset metadata for {asset_id}")
    except Exception as e:
        logger.warning(f"[Firestore] store_asset_metadata failed for {asset_id}: {e}")
        # Do NOT re-raise — non-critical path


def log_threat(threat_id: str, threat_data: dict) -> None:
    """
    Logs a threat detection result to Firestore 'threat_logs' collection.
    Silently no-ops if Firestore is unavailable.
    """
    if not _try_init_firestore():
        logger.debug(f"[Firestore] log_threat skipped (no-op) for {threat_id}")
        return
    try:
        _db.collection("threat_logs").document(threat_id).set(threat_data)
        logger.info(f"[Firestore] Logged threat {threat_id}")
    except Exception as e:
        logger.warning(f"[Firestore] log_threat failed for {threat_id}: {e}")
        # Do NOT re-raise — non-critical logging path
