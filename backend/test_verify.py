from fastapi.testclient import TestClient
import io
from PIL import Image
import numpy as np
import cv2

# Ensure we can import from main
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

def create_dummy_video(filename, color=(255, 0, 0)):
    # Create a small dummy video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 1.0, (100, 100))
    for _ in range(5): # 5 frames
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:] = color
        out.write(frame)
    out.release()

if __name__ == "__main__":
    print("Creating dummy videos...")
    create_dummy_video("dummy_orig.mp4", color=(255, 0, 0))
    create_dummy_video("dummy_susp.mp4", color=(255, 0, 0)) # Exact same
    
    with open("dummy_orig.mp4", "rb") as orig, open("dummy_susp.mp4", "rb") as susp:
        response = client.post(
            "/api/v1/verify/compare",
            files={
                "original_video": ("dummy_orig.mp4", orig, "video/mp4"),
                "suspicious_video": ("dummy_susp.mp4", susp, "video/mp4")
            }
        )
    
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    
    # Cleanup
    os.remove("dummy_orig.mp4")
    os.remove("dummy_susp.mp4")
