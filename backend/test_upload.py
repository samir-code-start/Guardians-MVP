import cv2
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app
from fastapi.testclient import TestClient

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
    create_dummy_video("test_dummy.mp4", color=(0, 255, 0))
    
    with open("test_dummy.mp4", "rb") as f:
        response = client.post("/api/v1/upload/", files={'file': ('test_dummy.mp4', f, 'video/mp4')})
        
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
    
    os.remove("test_dummy.mp4")
