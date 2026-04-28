"""
fast_path.py — Perceptual Hash (pHash) Detection Engine
========================================================
Primary detection layer for the Guardians MVP.

Classification Logic:
    PIRATED    — High structural similarity (piracy confirmed)
    SUSPICIOUS — Partial overlap (flagged for review)
    AUTHENTIC  — No significant match (original content)

Confidence Score (0–100):
    Computed from a weighted combination of four signals:
      1. Frame Match Ratio        (weight: 40%)
      2. Continuous Streak Score  (weight: 25%)
      3. Hamming Distance Score   (weight: 25%)
      4. Coverage Density Score   (weight: 10%)

Decision Thresholds (confidence-based):
    >= 70  → PIRATED
    >= 40  → SUSPICIOUS
    <  40  → AUTHENTIC
"""

import imagehash
from PIL import Image
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ─── Tunable Constants ────────────────────────────────────────────────────────

# Hamming distance below which two frames are considered a perceptual match.
# pHash produces a 64-bit hash; a distance of 0 = identical, 64 = completely different.
# Distance ≤ 8  → very strong match (re-encode / slight compression)
# Distance ≤ 15 → solid match (brightness / colour grade tweak)
MATCH_THRESHOLD: int = 15

# Thresholds for the final 0-100 confidence score
PIRATED_THRESHOLD: int = 70
SUSPICIOUS_THRESHOLD: int = 40

# ─── pHash Primitives ─────────────────────────────────────────────────────────

def compute_phash(image: Image.Image) -> str:
    """Returns the hex pHash string for one frame. Returns '' on failure."""
    try:
        return str(imagehash.phash(image))
    except Exception as e:
        logger.error(f"[pHash] compute failed: {e}")
        return ""


def hamming_distance(h1: str, h2: str) -> int:
    """Hamming distance between two pHash hex strings. Returns 999 on error."""
    try:
        return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
    except Exception as e:
        logger.error(f"[pHash] distance failed: {e}")
        return 999


# ─── Core Comparison Engine ───────────────────────────────────────────────────

def _best_distance(query_hash: str, reference_hashes: List[str]) -> int:
    """
    For a single query hash, find the minimum Hamming distance
    against the entire reference hash set.
    """
    if not reference_hashes:
        return 999
    return min(hamming_distance(query_hash, ref) for ref in reference_hashes)


def _build_match_vector(
    query_hashes: List[str],
    reference_hashes: List[str],
) -> tuple[List[bool], List[int]]:
    """
    For each query frame, determine:
      - is_match  (bool)  : distance ≤ MATCH_THRESHOLD
      - best_dist (int)   : the closest Hamming distance found

    Returns (match_booleans, best_distances)
    """
    match_booleans: List[bool] = []
    best_distances: List[int] = []

    for qh in query_hashes:
        dist = _best_distance(qh, reference_hashes)
        match_booleans.append(dist <= MATCH_THRESHOLD)
        best_distances.append(dist)

    return match_booleans, best_distances


def _longest_streak(match_booleans: List[bool]) -> int:
    """Returns the length of the longest consecutive run of True values."""
    longest = 0
    current = 0
    for m in match_booleans:
        if m:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


# ─── Scoring Sub-components ───────────────────────────────────────────────────

def _score_match_ratio(match_ratio: float) -> float:
    """
    Maps match_ratio [0, 1] → score [0, 100].
    Curve is aggressive: 0.5 ratio already yields ~70 score.
    """
    # Sigmoid-like mapping: score = ratio^0.6 * 100
    import math
    if match_ratio <= 0:
        return 0.0
    return min(100.0, (match_ratio ** 0.6) * 100.0)


def _score_streak(longest_streak: int, total_frames: int) -> float:
    """
    Maps streak length relative to total frames → score [0, 100].
    A streak covering ≥50% of frames is considered a strong signal.
    """
    if total_frames == 0:
        return 0.0
    streak_ratio = longest_streak / total_frames
    return min(100.0, streak_ratio * 200.0)   # 0.5 streak ratio → 100 score


def _score_hamming_distribution(best_distances: List[int]) -> float:
    """
    Produces a score based on how tight/close the matched distances are.
    Filters to only matched frames (distance ≤ MATCH_THRESHOLD).
      - Average distance of 0   → 100 (perfect pixel reuse)
      - Average distance of threshold → 0
    """
    matched_dists = [d for d in best_distances if d <= MATCH_THRESHOLD]
    if not matched_dists:
        return 0.0
    avg_dist = sum(matched_dists) / len(matched_dists)
    # Linear scale: 0 → 100, MATCH_THRESHOLD → 0
    return max(0.0, 100.0 * (1.0 - avg_dist / MATCH_THRESHOLD))


def _score_coverage_density(match_booleans: List[bool]) -> float:
    """
    Measures how evenly spread the matches are across the video timeline.
    Evenly distributed matches → higher density score.
    Clustered-only matches → lower density bonus.
    """
    if not match_booleans or sum(match_booleans) == 0:
        return 0.0

    n = len(match_booleans)
    indices = [i for i, m in enumerate(match_booleans) if m]
    num_matches = len(indices)

    # Spread = range of matched indices / total span
    span = (indices[-1] - indices[0] + 1) if num_matches > 1 else 1
    density = num_matches / span   # how dense the matches are within their span
    spread  = span / n             # how far across the timeline the matches reach

    # Reward a spread pattern more than a dense cluster
    coverage = (density * 0.4 + spread * 0.6)
    return min(100.0, coverage * 100.0)


# ─── Final Classification ─────────────────────────────────────────────────────

def _compute_confidence(
    match_ratio: float,
    longest_streak: int,
    total_frames: int,
    best_distances: List[int],
    match_booleans: List[bool],
) -> float:
    """
    Weighted combination of four independent signals → confidence [0, 100].

    Weights (must sum to 1.0):
        match_ratio_score   : 0.40
        streak_score        : 0.25
        hamming_score       : 0.25
        coverage_score      : 0.10
    """
    ratio_score    = _score_match_ratio(match_ratio)
    streak_score   = _score_streak(longest_streak, total_frames)
    hamming_score  = _score_hamming_distribution(best_distances)
    coverage_score = _score_coverage_density(match_booleans)

    confidence = (
        ratio_score    * 0.40 +
        streak_score   * 0.25 +
        hamming_score  * 0.25 +
        coverage_score * 0.10
    )

    logger.debug(
        f"[Confidence] ratio={ratio_score:.1f} streak={streak_score:.1f} "
        f"hamming={hamming_score:.1f} coverage={coverage_score:.1f} "
        f"→ final={confidence:.1f}"
    )

    return round(min(100.0, max(0.0, confidence)), 2)


def _classify(match_ratio: float, avg_hamming: float) -> str:
    """Maps match ratio and hamming distance to a human-readable decision label."""
    if match_ratio >= 0.9:
        if avg_hamming > 0.0:
            return "PIRATED (Edited Copy)"
        return "PIRATED (Exact Copy)"
    elif match_ratio >= 0.4:
        return "SUSPICIOUS"
    else:
        return "AUTHENTIC"


# ─── Public API ──────────────────────────────────────────────────────────────

def compare_frame_sets(
    original_frames: List[Image.Image],
    suspicious_frames: List[Image.Image],
) -> Dict[str, Any]:
    """
    Main entry point: compare two sets of PIL frames.

    Args:
        original_frames   : frames extracted from the reference (protected) video.
        suspicious_frames : frames from the video under investigation.

    Returns a dict containing:
        status                  : "PIRATED" | "SUSPICIOUS" | "AUTHENTIC"
        confidence_score        : float 0–100 (composite weighted score)
        confidence              : "HIGH" | "MEDIUM" | "LOW" (label for UI)
        match_ratio             : float, fraction of suspicious frames matched
        matched_frames          : int
        total_frames            : int
        longest_continuous_match: int
        min_hamming_distance    : int (closest single-frame distance found)
        avg_hamming_distance    : float (average across matched frames only)
        detection_method        : "pHash_Only"
        match_indices           : List[bool] (per-frame match flags for filmstrip UI)
    """
    # ── Guard: empty input ────────────────────────────────────────────────────
    if not original_frames or not suspicious_frames:
        logger.warning("[FastPath] One or both frame lists are empty.")
        return _empty_result()

    # ── 1. Compute pHash for every frame ──────────────────────────────────────
    ref_hashes = [compute_phash(f) for f in original_frames if f]
    qry_hashes = [compute_phash(f) for f in suspicious_frames if f]

    # Remove any hash computation failures
    ref_hashes = [h for h in ref_hashes if h]
    qry_hashes = [h for h in qry_hashes if h]

    if not ref_hashes or not qry_hashes:
        logger.warning("[FastPath] pHash computation produced no valid hashes.")
        return _empty_result()

    # ── 2. Build per-frame match vector ───────────────────────────────────────
    match_booleans_raw, best_distances = _build_match_vector(qry_hashes, ref_hashes)
    # Cast to plain Python bool — imagehash comparisons return numpy.bool_ which
    # FastAPI/Pydantic cannot serialize. This must be done before any return.
    match_booleans: List[bool] = [bool(m) for m in match_booleans_raw]

    total_frames   = len(qry_hashes)
    matched_frames = sum(match_booleans)
    match_ratio    = matched_frames / total_frames if total_frames > 0 else 0.0

    # ── 3. Streak analysis ────────────────────────────────────────────────────
    longest_streak = _longest_streak(match_booleans)

    # ── 4. Distance statistics ────────────────────────────────────────────────
    matched_dists = [d for d in best_distances if d <= MATCH_THRESHOLD]
    min_hamming   = min(best_distances) if best_distances else 999
    avg_hamming   = (sum(matched_dists) / len(matched_dists)) if matched_dists else 0.0

    # ── 5. Composite confidence score ─────────────────────────────────────────
    confidence_score = _compute_confidence(
        match_ratio,
        longest_streak,
        total_frames,
        best_distances,
        match_booleans,
    )

    # ── 6. Final classification ───────────────────────────────────────────────
    status = _classify(match_ratio, avg_hamming)

    # Map to a simple label for UI badges
    if confidence_score >= PIRATED_THRESHOLD:
        confidence_label = "HIGH"
    elif confidence_score >= SUSPICIOUS_THRESHOLD:
        confidence_label = "MEDIUM"
    else:
        confidence_label = "LOW"

    logger.info(
        f"[FastPath] status={status} | confidence={confidence_score:.1f} | "
        f"match_ratio={match_ratio:.2f} ({matched_frames}/{total_frames}) | "
        f"streak={longest_streak} | min_dist={min_hamming}"
    )

    return {
        # Primary decision fields
        "status": status,
        "confidence_score": float(confidence_score),
        "confidence": confidence_label,

        # Frame-level statistics
        "match_ratio": round(float(match_ratio), 4),
        "matched_frames": int(matched_frames),
        "total_frames": int(total_frames),
        "longest_continuous_match": int(longest_streak),

        # Hamming distance analytics
        "min_hamming_distance": int(min_hamming),
        "avg_hamming_distance": round(float(avg_hamming), 2),

        # Metadata
        "detection_method": "pHash_Only",

        # Per-frame flags — plain Python bool list for JSON serialization
        "match_indices": [bool(m) for m in match_booleans],
    }


def _empty_result() -> Dict[str, Any]:
    """Returns an error result when frames cannot be extracted from the video."""
    return {
        "status": "ERROR",
        "confidence_score": 0.0,
        "confidence": "LOW",
        "match_ratio": 0.0,
        "matched_frames": 0,
        "total_frames": 0,
        "longest_continuous_match": 0,
        "min_hamming_distance": 999,
        "avg_hamming_distance": 0.0,
        "detection_method": "pHash_Only",
        "match_indices": [],
    }
