import cv2
import numpy as np
import os
from services.media_processor import extract_frames

# Create a valid dummy video for testing
video_name = 'real_dummy.mp4'
out = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 10, (640, 480))
for i in range(30): # 3 seconds at 10 fps
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Give it some moving color
    frame[:] = (i * 8, 255 - i * 8, 128)
    out.write(frame)
out.release()

try:
    frames = extract_frames(video_name, num_frames=3)
    print(f"Success! Extracted {len(frames)} frames.")
    for i, frame in enumerate(frames):
        print(f"Frame {i} - Size: {frame.size}, Mode: {frame.mode}")
finally:
    if os.path.exists(video_name):
        os.remove(video_name)
