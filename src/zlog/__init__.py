import sys
import logging.config

#from formatter import LogFormatterFactory


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "INFO", "handlers": ["handler"]},
    "handlers": {
        "handler": {
            "class": "logging.StreamHandler",
            "formatter": "formatter",
            "stream": sys.stdout,
        }
    },
    "formatters": {"formatter": {"()": "zlog.formatter.LogFormatterFactory"}},
}


def configure(loggers=None, hacks=None, pretty=False):
    if loggers is not None:
        LOGGING_CONFIG["loggers"] = loggers
    if hacks is not None:
        LOGGING_CONFIG["formatters"]["formatter"]["hacks"] = hacks
    if pretty:
        LOGGING_CONFIG["formatters"]["formatter"]["pretty"] = True
    logging.config.dictConfig(LOGGING_CONFIG)
