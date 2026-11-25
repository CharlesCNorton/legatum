"""Regression checks against corrupted contract fields of the delivered fixture."""
import copy, json, struct, tempfile, unittest
from pathlib import Path
from validate_glb import GLB, validate

ASSET=Path(__file__).parent/'units/spearman-0ad/spearman.glb'
class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'spearman.glb';self.g=GLB(ASSET)
        for name in ['PROVENANCE.md','LICENSE-ART']:(self.path.parent/name).write_text(ASSET.with_name(name).read_text())
    def write(self,doc,blob=None):
        raw=json.dumps(doc).encode();raw+=b' '*(-len(raw)%4);blob=self.g.bin if blob is None else blob
        data=struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob
        self.path.write_bytes(data)
    def rejects(self,edit,message):
        d=copy.deepcopy(self.g.doc);edit(d);self.write(d)
        self.assertTrue(any(message in e for e in validate(self.path)['errors']))
    def test_delivered_asset(self):self.assertTrue(validate(ASSET)['valid'])
    def test_clip_name(self):self.rejects(lambda d:d['animations'][0].update(name='Attack'), 'five named clips')
    def test_credit(self):self.rejects(lambda d:d['asset'].pop('copyright'),'exact credit')
    def test_bone_budget(self):self.rejects(lambda d:d['skins'][0]['joints'].extend(d['skins'][0]['joints'][:12]),'40 joints')
    def test_normal_map(self):self.rejects(lambda d:d['materials'][0].update(normalTexture={'index':0}),'normal or baked AO')
    def test_team(self):
        def edit(d):
            for m in d['materials']:
                if m['name']=='team':m['name']='red'
        self.rejects(edit,'team must cover')
    def test_prop_attachment(self):
        def edit(d):
            n=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='spear')
            for node in d['nodes']:
                if n in node.get('children',[]):node['children'].remove(n)
            d['scenes'][0]['nodes'].append(n)
        self.rejects(edit,'spear must attach directly')
    def test_loop_seam(self):
        d=copy.deepcopy(self.g.doc);a=next(a for a in d['animations'] if a['name']=='walk')
        channel=next(c for c in a['channels'] if c['target']['path']=='rotation')
        acc=d['accessors'][a['samplers'][channel['sampler']]['output']];view=d['bufferViews'][acc['bufferView']]
        off=view.get('byteOffset',0)+acc.get('byteOffset',0)+(acc['count']-1)*16
        blob=bytearray(self.g.bin);x=struct.unpack_from('<f',blob,off)[0];struct.pack_into('<f',blob,off,x+.1)
        self.write(d,blob);self.assertTrue(any('loop endpoint' in e for e in validate(self.path)['errors']))
    def test_missing_provenance(self):
        self.write(self.g.doc);self.path.with_name('PROVENANCE.md').unlink()
        self.assertIn('Missing adjacent PROVENANCE.md',validate(self.path)['errors'])
if __name__=='__main__':unittest.main()
