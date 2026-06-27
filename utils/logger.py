import logging
import os


class LoggerUtils:
    @staticmethod
    def get_logger(name: str = "authenticator") -> logging.Logger:
        logger = logging.getLogger(name)

        if logger.handlers:
            return logger

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

        return logger
