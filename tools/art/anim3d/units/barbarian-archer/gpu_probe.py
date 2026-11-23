"""Fail before expensive stages when the requested Metal device is unavailable."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import settings
settings(512, 64)
print('Metal GPU preflight passed')
