import sys
import json
from typing import Dict, NoReturn


def debug(message: str) -> NoReturn:
    print(f"DEBUG: {message}", file=sys.stderr)


def error(message: str) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def warn_multiple(key: str, data: Dict) -> NoReturn:
    print(f"WARNING: multiple {key}: {json.dumps(data)}", file=sys.stderr)
