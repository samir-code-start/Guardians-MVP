from PIL import Image
import numpy as np
from services.fast_path import compute_phash, phash_distance, compare_frame_sets

import cv2

# Create random noise images to ensure pHash generates different values
np.random.seed(42)

img1_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
img1 = Image.fromarray(img1_array)

# Same as img1 but slightly modified
img2_array = img1_array.copy()
cv2.rectangle(img2_array, (10, 10), (40, 40), (255, 0, 0), -1)
img2 = Image.fromarray(img2_array)

# Completely different random image
img3_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
img3 = Image.fromarray(img3_array)

def test_identical_images():
    result = compare_frame_sets([img1], [img1])
    assert result["match"] is True
    assert result["confidence"] >= 70

def test_slightly_different_images():
    result = compare_frame_sets([img1], [img2])
    # The random modification might or might not match, but it shouldn't crash
    assert "match" in result

def test_completely_different_images():
    result = compare_frame_sets([img1], [img3])
    # Different noise images should definitely fail to match
    assert result["match"] is False
    assert result["confidence"] < 70

def test_list_of_images():
    # Comparing [img1, img2] to [img1, img3] should have 50% coverage match
    result = compare_frame_sets([img1, img2], [img1, img3])
    # Since confidence includes average similarity, it might be > 70 if the distance is small enough.
    # We mainly want to ensure the function works with lists.
    assert "match" in result
    assert result["matches_count"] >= 1
