import logging


def configure_logging() -> None:
    level = logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    # uvicorn configures the root logger, which makes basicConfig() a no-op.
    # Attach our own handler so app logs always reach stdout.
    has_app_handler = any(
        getattr(h, "_kabilai", False) for h in root.handlers
    )
    if not has_app_handler:
        handler = logging.StreamHandler()
        handler._kabilai = True  # type: ignore[attr-defined]
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root.addHandler(handler)

    # Make sure uvicorn loggers don't suppress our INFO logs.
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("app").setLevel(level)
