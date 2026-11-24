"""Append evidence while keeping next-round focus instructions at the end."""
from pathlib import Path


def append_evidence(path, text):
    path = Path(path)
    previous = path.read_text() if path.exists() else ''
    lines = previous.splitlines(keepends=True)
    focus = next((i for i, line in enumerate(lines) if line.startswith('FOCUS a:')), len(lines))
    path.write_text(''.join(lines[:focus]).rstrip()+'\n\n'+text.strip()+'\n\n'+''.join(lines[focus:]))
