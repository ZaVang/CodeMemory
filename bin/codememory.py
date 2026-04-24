#!/usr/bin/env python3
"""CodeMemory CLI — thin launcher for src/codememory/ package."""

import sys
from pathlib import Path

# Ensure src/ is on the path so codememory package is importable
_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from codememory.cli import main

if __name__ == "__main__":
    main()
