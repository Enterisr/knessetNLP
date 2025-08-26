import logging
import os
import sys


def get_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.DEBUG,
    to_console: bool = True,
) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger  # already initialized

    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{name}.log")

    file_handler = logging.FileHandler(log_path, encoding="UTF-8", delay=False)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
