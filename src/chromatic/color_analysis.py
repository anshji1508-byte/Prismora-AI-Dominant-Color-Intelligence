from io import BytesIO

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans, MiniBatchKMeans


def rgb_to_hex(rgb: np.ndarray) -> str:
    return "#" + "".join(f"{int(value):02X}" for value in rgb)


def valid_centers(value, n_colors: int):
    try:
        centers = np.asarray(value, dtype=np.float32)
        if centers.shape != (n_colors, 3) or not np.isfinite(centers).all():
            return None
        return np.clip(np.rint(centers), 0, 255).astype(np.uint8)
    except (TypeError, ValueError):
        return None


def extract_palette(
    image_bytes: bytes,
    n_colors: int,
    sample_size: int,
    online: bool = False,
    previous_centers=None,
    learn: bool = True,
):
    """Analyze an image and return preview, segmentation, palette and percentages."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    original_size = image.size
    preview = image.copy()
    preview.thumbnail((1200, 900), Image.Resampling.LANCZOS)
    pixels = np.asarray(preview).reshape(-1, 3)

    if len(pixels) > sample_size:
        rng = np.random.default_rng(42)
        pixels_for_fit = pixels[rng.choice(len(pixels), sample_size, replace=False)]
    else:
        pixels_for_fit = pixels

    if online and previous_centers is not None:
        model = MiniBatchKMeans(
            n_clusters=n_colors,
            init=np.asarray(previous_centers, dtype=float),
            n_init=1,
            batch_size=1024,
            random_state=42,
        )
    elif online:
        model = MiniBatchKMeans(
            n_clusters=n_colors, init="k-means++", n_init=3,
            batch_size=1024, random_state=42,
        )
    else:
        model = KMeans(n_clusters=n_colors, init="k-means++", n_init=10, random_state=42)

    if online and learn:
        model.partial_fit(pixels_for_fit)
    elif not online:
        model.fit(pixels_for_fit)

    if online and not learn:
        learned_centers = np.asarray(previous_centers, dtype=np.uint8)
        distances = ((pixels[:, None, :].astype(np.float32) - learned_centers[None, :, :]) ** 2).sum(axis=2)
        labels = np.argmin(distances, axis=1)
    else:
        learned_centers = np.clip(np.rint(model.cluster_centers_), 0, 255).astype(np.uint8)
        labels = model.predict(pixels)

    counts = np.bincount(labels, minlength=n_colors)
    order = np.argsort(counts)[::-1]
    centers = learned_centers[order]
    percentages = counts[order] / len(labels) * 100
    segmented = centers[labels].reshape(np.asarray(preview).shape)
    return preview, Image.fromarray(segmented, "RGB"), centers, percentages, original_size, learned_centers
