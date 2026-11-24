"""Compatibility entry point; shared implementation lives in kit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.materials import painted_fill
