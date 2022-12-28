import sys
import json
from typing import Dict, NoReturn


def debug(message: str, enable=False) -> NoReturn:
    """debug message"""
    if enable:
        print(f"DEBUG: {message}", file=sys.stderr)


def error(message: str) -> NoReturn:
    """error message (print and exit)"""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> NoReturn:
    """warning message"""
    print(f"WARNING: {message}", file=sys.stderr)


def warn_multiple(key: str, data: Dict) -> NoReturn:
    """specific warning message"""
    print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)
