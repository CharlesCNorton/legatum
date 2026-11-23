"""Render each distinct simulation sample once, copying any held samples."""
from pathlib import Path
import shutil


def render_samples(frames, output, render):
    output = Path(output)
    rendered = {}
    for i, frame in enumerate(frames):
        destination = output/f'{i:02}.png'
        if frame in rendered:
            shutil.copyfile(rendered[frame], destination)
        else:
            render(frame, destination)
            assert destination.is_file(), f'Render did not produce {destination}'
            rendered[frame] = destination
