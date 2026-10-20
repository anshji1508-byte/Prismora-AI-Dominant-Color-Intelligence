from pathlib import Path

from chromatic.color_analysis import extract_palette


def test_extract_palette_returns_requested_number_of_colors():
    image_path = Path(__file__).parents[2] / "1.jpg"
    if not image_path.exists():
        return
    result = extract_palette(image_path.read_bytes(), 4, 5_000)
    assert len(result[2]) == 4
    assert result[1].mode == "RGB"
