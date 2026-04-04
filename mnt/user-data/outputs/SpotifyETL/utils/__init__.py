"""Shared utilities: config loader, logger, retry decorator."""
import os
import logging
import time
import functools
import yaml
from pathlib import Path


_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def load_config(path: Path = _CONFIG_PATH) -> dict:
    """Load YAML config and expand ${ENV_VAR} placeholders."""
    with open(path) as f:
        raw = f.read()
    # expand environment variables
    import re
    def _replace(match):
        var = match.group(1)
        val = os.environ.get(var)
        if val is None:
            raise EnvironmentError(f"Required env var '{var}' is not set.")
        return val
    expanded = re.sub(r"\$\{([^}]+)\}", _replace, raw)
    return yaml.safe_load(expanded)


def get_logger(name: str, config: dict = None) -> logging.Logger:
    """Return a named logger writing to console + rotating file."""
    from logging.handlers import RotatingFileHandler

    log_level = logging.INFO
    log_dir = Path("logs")
    if config:
        log_level = getattr(logging, config["pipeline"].get("log_level", "INFO"))
        log_dir = Path(config["pipeline"].get("log_dir", "logs"))

    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger                   # already configured

    logger.setLevel(log_level)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                             datefmt="%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    fh = RotatingFileHandler(log_dir / "pipeline.log", maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


def retry(max_retries: int = 3, backoff_factor: int = 2, exceptions=(Exception,)):
    """Exponential-backoff retry decorator."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_retries:
                        raise
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator
