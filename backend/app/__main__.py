"""Run the API with `python -m app`."""

import uvicorn


def main() -> None:
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
