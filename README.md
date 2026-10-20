# Chromatic Color Studio

A production-oriented Streamlit application that extracts dominant colors and generates a color-segmented image using K-Means clustering.

The project also includes a reproducible MLOps workflow: DVC parameter tracking, experiment metrics, artifact versioning, automated quality gates, and Docker-based delivery.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
make install
make run
```

Open `http://localhost:8501`, upload an image, choose the number of colors, and click **Analyze image**.

## Project layout

This follows a Cookiecutter Data Science-style layout: application code lives under `app/`, reusable logic under `src/`, tests under `tests/`, and data/model/report directories are reserved for future pipeline work.

## Quality checks

```bash
make test
make lint
```

## DVC experiments

```bash
dvc repro                         # reproduce the configured pipeline
dvc exp run -S model.n_colors=6   # run a parameterized experiment
dvc exp show                      # compare experiment results
dvc metrics show                  # inspect tracked metrics
```

The pipeline writes `models/palette.json`, `reports/metrics.json`, and `reports/segmented.png`.

## Docker

```bash
docker build -t chromatic-color-studio .
docker run --rm -p 8501:8501 chromatic-color-studio
```

Pushes to `main` run lint, tests, the DVC experiment, and publish the Docker image to GitHub Container Registry through `.github/workflows/ci-cd.yml`.
