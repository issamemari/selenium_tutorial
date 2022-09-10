import json
import socket

import traceback
from datetime import datetime
from os import environ

from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.web import JsonLexer


LOGRECORD_RESERVED_ATTRS = set(
    [
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    ]
)


class StrFallbackJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(StrFallbackJSONEncoder, self).default(obj)
        except TypeError:
            return str(obj)


class LogFormatter:
    LEVELS_SHORTNAMES = {"critical": "crit", "error": "err", "warning": "warn"}

    def __init__(self, prefix="", hacks=None, pretty=True):
        self.base = {
            "log_version": "1.0.0",
            "host": socket.gethostname(),
        }
        self.prefix = prefix
        self.hacks = hacks
        self.pretty = pretty

    def format(self, record):
        level = record.levelname.lower()
        level = self.LEVELS_SHORTNAMES.get(level, level)

        m = {
            "msg": record.msg,
            "timestamp": int(record.created * 1e9),
            "time": datetime.utcfromtimestamp(record.created).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "severity": level,
            "logger_name": record.name,
            "pid": record.process,
            "filename": record.filename,
            "func_name": record.funcName,
            "lineno": record.lineno,
        }

        if record.exc_info is not None:
            exc_type, exc_value, exc_traceback = record.exc_info
            m["exc_type"] = exc_type.__name__
            m["exc_value"] = exc_value
            m["exc_traceback"] = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )

        if record.args is None:
            pass
        elif isinstance(record.args, dict):
            for k, v in record.args.items():
                if k in LOGRECORD_RESERVED_ATTRS:
                    k = k + "_"
                m[k] = v
        elif isinstance(record.args, tuple):
            for i, el in enumerate(record.args):
                m["arg" + str(i)] = el
        else:
            m["args"] = record.args

        # add the keyvals that were passed in the "extra" kwarg and added
        # among the LogRecord's fields
        for k, v in record.__dict__.items():
            if k not in LOGRECORD_RESERVED_ATTRS and not (
                hasattr(k, "startswith") and k.startswith("_")
            ):
                m[k] = v

        m.update(self.base)

        if self.hacks is not None:
            for hack in self.hacks:
                m = hack(m)

        if self.pretty:
            j = json.dumps(m, cls=StrFallbackJSONEncoder, indent=4)
            j = highlight(
                j,
                lexer=JsonLexer(),
                formatter=Terminal256Formatter(style="stata-dark", full=True),
            ).strip()
            # unescape the escaped newlines in order to display tracebacks properly
            j = j.encode("utf-8", "backslashreplace").decode("unicode-escape")
        else:
            j = json.dumps(m, cls=StrFallbackJSONEncoder)

        return self.prefix + j


def LogFormatterFactory(prefix="", hacks=None, pretty=False):
    return LogFormatter(prefix, hacks, pretty)
