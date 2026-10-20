from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from chromatic.color_analysis import extract_palette


def test_extract_palette_returns_requested_number_of_colors():
    image_path = Path(__file__).parents[2] / "1.jpg"
    if not image_path.exists():
        return
    result = extract_palette(image_path.read_bytes(), 4, 5_000)
    assert len(result[2]) == 4
    assert result[1].mode == "RGB"


def test_segmentation_labels_match_sorted_centers():
    image = Image.new("RGB", (40, 20), "#ef4444")
    pixels = image.load()
    for x in range(20, 40):
        for y in range(20):
            pixels[x, y] = (37, 99, 235)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    preview, segmented, _, _, _, _ = extract_palette(buffer.getvalue(), 2, 800)
    error = np.abs(np.asarray(preview).astype(float) - np.asarray(segmented).astype(float)).mean()
    assert error < 1.0
