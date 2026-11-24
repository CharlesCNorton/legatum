"""Compatibility imports for the shared evaluated-foot geometry kit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kit.contact import sole_points, landmarks
