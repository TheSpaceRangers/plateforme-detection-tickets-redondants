"""Test import path configuration for centralized pytest execution."""

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
ML_DIR = ROOT_DIR / "ml"

for path in (ROOT_DIR, ML_DIR):
    path_value = str(path)
    if path_value not in sys.path:
        sys.path.insert(0, path_value)
