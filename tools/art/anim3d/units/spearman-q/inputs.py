"""Snapshot and hash-check the reviewed local costume and per-part painting kit."""
import hashlib,json,os,shutil
from pathlib import Path
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
target=root/'lanes/spearman-q-r2/input';source=root/'masters/spearman-3d-v2'
expected=json.loads(Path(__file__).with_name('input-sources.json').read_text())
for name,digest in expected.items():
    p=target/name
    if not p.exists():
        original=source/name
        assert hashlib.sha256(original.read_bytes()).hexdigest()==digest,f'Source changed: {original}'
        p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,f'Frozen input changed: {p}'
print(f'Frozen look source verified: {len(expected)} files')
