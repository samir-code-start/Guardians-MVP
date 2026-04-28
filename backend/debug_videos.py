import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)

def test_actual_videos():
    orig_path = r"d:\mvp of the gurdains frame\test video 2.mp4"
    susp_path = r"d:\mvp of the gurdains frame\test video 1.mp4"
    
    print("Opening files...")
    try:
        with open(orig_path, "rb") as orig, open(susp_path, "rb") as susp:
            print("Sending request to /api/v1/verify/compare...")
            response = client.post(
                "/api/v1/verify/compare",
                files={
                    "original_video": ("test video 2.mp4", orig, "video/mp4"),
                    "suspicious_video": ("test video 1.mp4", susp, "video/mp4")
                }
            )
        
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Error Detail:", response.json())
        else:
            print("Success:", response.json())
            
    except Exception as e:
        print("Crash occurred!")
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_videos()
