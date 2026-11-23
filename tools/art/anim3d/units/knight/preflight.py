"""Refuse missing or modified source assets before rebuilding the unit."""
import os,json,hashlib
from pathlib import Path
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
lock=json.loads(Path(__file__).with_name('sources.lock.json').read_text())
for rel,digest in lock.items():
 p=R/rel;assert p.is_file(),f'Missing {p}; see SOURCES.md'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,f'Source hash mismatch: {p}'
assert (R/'blender-user/extensions/user_default/mpfb').exists(),'MPFB 2.0.18 isolated install missing'
print(f'PREFLIGHT_PASS {len(lock)} licensed source hashes')
