"""Reproducible DVC experiment for the dominant-color model."""

import json
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chromatic.color_analysis import extract_palette, rgb_to_hex  # noqa: E402


def main() -> None:
    params = yaml.safe_load((ROOT / "params.yaml").read_text())
    model_params = params["model"]
    input_path = ROOT / params["data"]["input_image"]
    preview, segmented, centers, percentages, original_size, _ = extract_palette(
        input_path.read_bytes(),
        int(model_params["n_colors"]),
        int(model_params["sample_size"]),
        bool(model_params["online_learning"]),
        learn=True,
    )

    original = np.asarray(preview).astype(np.float32)
    reconstructed = np.asarray(segmented).astype(np.float32)
    mean_absolute_error = float(np.abs(original - reconstructed).mean())
    rmse = float(np.sqrt(np.square(original - reconstructed).mean()))
    percentages = np.asarray(percentages, dtype=float)
    normalized = percentages / 100.0
    entropy = float(-(normalized * np.log2(np.clip(normalized, 1e-12, 1))).sum())

    palette = [
        {"rank": i, "rgb": [int(value) for value in color], "hex": rgb_to_hex(color), "share_percent": round(float(share), 4)}
        for i, (color, share) in enumerate(zip(centers, percentages), 1)
    ]
    metrics = {
        "n_colors": int(model_params["n_colors"]),
        "sample_size": int(model_params["sample_size"]),
        "mean_absolute_color_error": round(mean_absolute_error, 6),
        "rmse_color_error": round(rmse, 6),
        "palette_entropy": round(entropy, 6),
        "dominant_color_share_percent": round(float(percentages[0]), 6),
        "image_width": original_size[0],
        "image_height": original_size[1],
    }

    (ROOT / "models/palette.json").write_text(json.dumps({"params": model_params, "palette": palette}, indent=2))
    (ROOT / "reports/metrics.json").write_text(json.dumps(metrics, indent=2))
    segmented.save(ROOT / "reports/segmented.png")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
