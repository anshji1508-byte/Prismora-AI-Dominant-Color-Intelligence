import json
from pathlib import Path


def test_dvc_experiment_contract():
    root = Path(__file__).parents[1]
    assert (root / "dvc.yaml").exists()
    assert (root / "params.yaml").exists()
    metrics = root / "reports/metrics.json"
    if metrics.exists():
        payload = json.loads(metrics.read_text())
        assert payload["n_colors"] >= 2
        assert payload["mean_absolute_color_error"] >= 0
