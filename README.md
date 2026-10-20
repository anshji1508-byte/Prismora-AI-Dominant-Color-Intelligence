# Chromatic Color Studio

A production-oriented Streamlit application that extracts dominant colors and generates a color-segmented image using K-Means clustering.

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

## Docker

```bash
docker build -t chromatic-color-studio .
docker run --rm -p 8501:8501 chromatic-color-studio
```
