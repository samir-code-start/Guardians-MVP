import numpy as np
import cv2
from PIL import Image
from services.deep_path import compare_deep_features

# We use solid colors to test because random noise might have high semantic similarity for CLIP (it's just noise)
# CLIP focuses on semantic content.
img1_array = np.zeros((224, 224, 3), dtype=np.uint8)
img1_array[:] = (255, 0, 0) # Solid red
img1 = Image.fromarray(img1_array)

img2_array = img1_array.copy()
img2 = Image.fromarray(img2_array)

img3_array = np.zeros((224, 224, 3), dtype=np.uint8)
img3_array[:] = (0, 255, 0) # Solid green
img3 = Image.fromarray(img3_array)

print("--- Testing Identical Images (Deep Path) ---")
result_identical = compare_deep_features([img1], [img2])
print(result_identical)

print("--- Testing Different Images (Deep Path) ---")
result_different = compare_deep_features([img1], [img3])
print(result_different)
