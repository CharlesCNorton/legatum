#!/usr/bin/env python3
"""Validate atlas contract plus the stationary painted stone and source framing."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter
from units import CLIPS, UNITS
from pack import PROFILES, clip_metadata

ROOT = Path(__file__).resolve().parents[3]
HOME = Path.home() / 'LegatumRuns/anim-pilot'


def validate(slugs=None, assets_dir=None, masters_dir=None, contract_only=False):
    assets_dir = assets_dir or ROOT / 'app/src/assets/units/anim'
    masters_dir = masters_dir or HOME / 'masters'
    for slug in slugs or UNITS:
        cfg = UNITS[slug]
        path = assets_dir / slug
        meta = json.loads(path.with_suffix('.json').read_text())
        assert list(meta) == ['frame', 'clips'], slug
        assert meta['frame'] == dict(w=256, h=256, ax=cfg['anchor'][0], ay=cfg['anchor'][1]), slug
        assert list(meta['clips']) == list(CLIPS), slug
        assert any(meta['clips'] == {c: clip_metadata(c, ids, r) for r, (c, ids) in enumerate(p.items())}
                   for p in PROFILES), (slug, 'unrecognized frame/timing profile')
        atlas = Image.open(path.with_suffix('.webp')).convert('RGBA')
        assert atlas.size == (2560, 1280), slug
        assert path.with_suffix('.webp').stat().st_size <= 200_000, slug
        rim = []
        if not contract_only:
            base = Image.open(masters_dir / slug / 'base.png').convert('RGBA')
            # Exposed front rim; moving feet and fallen figures may cover the top.
            y0 = cfg['base'][3] - 7
            core = base.getchannel('A').filter(ImageFilter.MinFilter(5))
            rim = [(x, y) for y in range(y0, 256) for x in range(256) if core.getpixel((x, y)) == 255]
            assert len(rim) >= 80, (slug, 'missing reference stone')
        first = None
        for row, (clip, data) in enumerate(meta['clips'].items()):
            n = data['frames']
            frames = []
            for i in range(n):
                frame = atlas.crop((i*256, row*256, (i+1)*256, (row+1)*256))
                frames.append(frame)
                alpha = frame.getchannel('A')
                bounds = alpha.getbbox()
                assert bounds and 0 < bounds[0] < bounds[2] < 256 and 0 < bounds[1] < bounds[3] < 256, (slug, clip, i, 'clipped silhouette')
                assert alpha.getextrema() == (0, 255), (slug, clip, i, 'missing alpha')
                if rim:
                    assert all(frame.getpixel(p)[3] >= 247 for p in rim), (slug, clip, i, 'missing/moving stone rim')
                    for reference in (base, first or base):
                        error = sum(abs(frame.getpixel(p)[c] - reference.getpixel(p)[c]) for p in rim for c in range(3)) / (3 * len(rim))
                        assert error < 12, (slug, clip, i, 'stone pigment/position changed', error)
                if first is None:
                    first = frame
                    if not contract_only:
                        source = Image.open(ROOT / f'app/src/assets/units/{slug}-256.png').convert('RGBA')
                        a, b = source.getchannel('A').getbbox(), bounds
                        assert max(abs(x-y) for x, y in zip(a, b)) <= 4, (slug, 'source framing', a, b)
            if n < 10:
                assert not atlas.crop((n*256, row*256, 2560, (row+1)*256)).getchannel('A').getbbox(), (slug, clip, 'padding')
            if clip == 'death':
                a, b = frames[-2:]
                assert ImageChops.difference(a.getchannel('A'), b.getchannel('A')).getbbox() is None, (slug, 'death must hold')
        suffix = ' (contract only; art unchecked)' if contract_only else ', stationary stone and source framing'
        print(f'{slug}: contract, alpha, padding, held death and size{suffix} PASS')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*', choices=list(UNITS))
    ap.add_argument('--assets-dir', type=Path)
    ap.add_argument('--masters-dir', type=Path)
    ap.add_argument('--contract-only', action='store_true', help='For legacy-frame diagnostics only; skips stone/framing checks')
    args = ap.parse_args()
    validate(args.slugs, args.assets_dir, args.masters_dir, args.contract_only)
