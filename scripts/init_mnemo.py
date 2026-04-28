#!/usr/bin/env python3
"""Public wrapper for the mnemo init bootstrap script."""
from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    script = Path(__file__).resolve().parents[1] / "skills" / "init" / "init_mnemo.py"
    runpy.run_path(str(script), run_name="__main__")
