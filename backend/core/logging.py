import logging


class RequestIDFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return super().format(record)


def configure_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    formatter = RequestIDFormatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s request_id=%(request_id)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if logger.handlers:
        logger.handlers.clear()
    logger.addHandler(handler)
