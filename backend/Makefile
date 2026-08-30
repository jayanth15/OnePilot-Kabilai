.PHONY: dev test install seed

install:
	uv pip install -r requirements.txt

dev:
	uv run python -m app

seed:
	uv run python -m app.seed

test:
	uv run python -m unittest discover -s tests -v
