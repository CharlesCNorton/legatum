"""Fail before GPU work if packed artwork or geometry build inputs have drifted."""
import hashlib,json,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);U=Path(__file__).parent;M=R/'masters/jet-bomber'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((U/'inputs.json').read_text())
for file,digest in inputs.items():assert sha(R/file)==digest,('asset changed',file)
receipt=json.loads((M/'build.json').read_text())
for file,digest in receipt['scripts'].items():assert sha(U/file)==digest,('rebuild required',file)
for file,digest in receipt['masters'].items():assert sha(M/file)==digest,('master changed',file)
print('INPUT PREFLIGHT PASS')
