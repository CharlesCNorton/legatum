"""Freeze the small render dependency tree before waiting in the Blender gate."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(checkout,root,round_id):
    destination=Path(tempfile.mkdtemp(prefix=f'gpu-r{round_id}-',dir=root/'masters/cataphract'))
    files=list((checkout/'tools/art/anim3d').glob('*.py'))
    files+=list((checkout/'tools/art/anim3d/units/cataphract').glob('*.py'))
    files += [checkout/'tools/art/anim3d/units/cataphract/assets.lock.json',checkout/'app/src/assets/units/cataphract-256.png']
    records={}
    for source in files:
        relative=source.relative_to(checkout);target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        records[str(relative)]=digest(target)
    receipt={'checkout':str(checkout),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=checkout,text=True).strip(),'files':records}
    (destination/'snapshot.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return destination

def publish(snapshot_dir):
    receipt=json.loads((snapshot_dir/'snapshot.json').read_text());checkout=Path(receipt['checkout'])
    # Retain the verified deliverable even if the driver has already retired this lane.
    out=Path(os.environ['ANIM_ROOT'])/'masters/cataphract/gpu-delivery';out.mkdir(exist_ok=True)
    for suffix in ['webp','json']:
        shutil.copy2(snapshot_dir/f'app/src/assets/units/anim/cataphract.{suffix}',out/f'cataphract.{suffix}')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=checkout,text=True).strip()
    assert branch==receipt['branch']=='astra/unit-anim-3d-cataphract','Checkout switched during GPU pass; verified atlas retained in masters/cataphract/gpu-delivery'
    for relative,sha in receipt['files'].items():
        assert digest(checkout/relative)==sha,('Checkout changed during GPU pass',relative)
    dest=checkout/'app/src/assets/units/anim';dest.mkdir(exist_ok=True)
    for suffix in ['webp','json']:shutil.copy2(out/f'cataphract.{suffix}',dest/f'cataphract.{suffix}')

if __name__=='__main__':
    if '--publish' in sys.argv:publish(Path.cwd())
    else:print(snapshot(Path.cwd(),Path(os.environ['ANIM_ROOT']),os.environ['ROUND']))
