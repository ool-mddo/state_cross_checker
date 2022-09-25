import sys
import json
from typing import Dict


def debug(message: str) -> None:
    print(f"DEBUG: {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def warn_multiple(key: str, data: Dict) -> None:
    print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)
