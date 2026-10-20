.PHONY: install run test lint format

install:
	python -m pip install -e ".[dev]"

run:
	streamlit run app/streamlit_app.py

test:
	pytest -q

lint:
	ruff check src app tests

format:
	ruff format src app tests
