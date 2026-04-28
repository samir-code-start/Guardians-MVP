"""
media_processor.py — Video Frame Extractor
===========================================
Extracts evenly-spaced keyframes from a video file and returns them as
PIL Images for downstream pHash computation.
"""

import cv2
from PIL import Image
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# Default number of frames to extract — 10 gives reliable pHash statistics
# without significant overhead (a 60-second clip takes ~1 s to sample).
DEFAULT_NUM_FRAMES: int = 10


def extract_frames(video_path: str, num_frames: int = DEFAULT_NUM_FRAMES) -> List[Image.Image]:
    """
    Extracts `num_frames` evenly-spaced frames from the video at `video_path`.

    Sampling strategy:
        Frame indices are spread uniformly across the video, skipping the very
        first and last 5% of content (avoids black leader / end-card frames).

    Args:
        video_path : Absolute path to the video file.
        num_frames : How many representative frames to extract (default 10).

    Returns:
        List of PIL Images (RGB). Empty list if extraction fails.

    Raises:
        FileNotFoundError : if the video file does not exist.
        RuntimeError      : if OpenCV cannot open the file.
    """
    if not os.path.exists(video_path):
        logger.error(f"[MediaProcessor] File not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"[MediaProcessor] Cannot open: {video_path}")
        raise RuntimeError(f"Failed to open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        logger.warning(f"[MediaProcessor] 0 frames reported for: {video_path}")
        cap.release()
        return []

    # Clamp num_frames to available frames
    num_frames = min(num_frames, total_frames)

    # ── Sampling: skip first 5% and last 5% of content ───────────────────────
    start_idx = max(0, int(total_frames * 0.05))
    end_idx   = min(total_frames - 1, int(total_frames * 0.95))
    usable_span = end_idx - start_idx

    if usable_span <= 0 or num_frames <= 0:
        # Fallback: just use all frames evenly
        frame_indices = list(range(min(num_frames, total_frames)))
    else:
        # Evenly spaced indices within the usable span
        if num_frames == 1:
            frame_indices = [start_idx + usable_span // 2]
        else:
            step = usable_span / (num_frames - 1)
            frame_indices = [int(start_idx + i * step) for i in range(num_frames)]

    # Deduplicate and sort (can occur when total_frames < num_frames)
    frame_indices = sorted(set(idx for idx in frame_indices if 0 <= idx < total_frames))

    # ── Read frames ──────────────────────────────────────────────────────────
    extracted_images: List[Image.Image] = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert OpenCV BGR → PIL RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            extracted_images.append(Image.fromarray(frame_rgb))
        else:
            logger.warning(f"[MediaProcessor] Failed to read frame #{idx}")

    cap.release()

    logger.info(
        f"[MediaProcessor] Extracted {len(extracted_images)}/{len(frame_indices)} "
        f"frames from '{os.path.basename(video_path)}' "
        f"(total_frames={total_frames})"
    )

    return extracted_images
