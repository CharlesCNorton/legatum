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
    def test_normal_map(self):self.rejects(lambda d:d['materials'][0].update(normalTexture={'index':0}),'Base colour, normal and ORM must be distinct textures')
    def test_team(self):
        self.rejects(lambda d:d['meshes'][0]['primitives'][0]['attributes'].pop('COLOR_0'),'Missing team mask')
    def test_extra_material(self):
        self.rejects(lambda d:d['materials'].append(copy.deepcopy(d['materials'][0])),'exactly 1 material')
    def test_extra_mesh(self):
        self.rejects(lambda d:d['meshes'].append(copy.deepcopy(d['meshes'][0])),'exactly 2 meshes')
    def test_extra_primitive(self):
        self.rejects(lambda d:d['meshes'][0]['primitives'].append(copy.deepcopy(d['meshes'][0]['primitives'][0])),'One primitive per LOD')
    def test_prop_attachment(self):
        def edit(d):
            region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='spear')
            region['bone']='head'
        self.rejects(edit,'spear must attach to weapon_R')
    def test_prop_blended_weight(self):
        d=copy.deepcopy(self.g.doc);p=d['meshes'][0]['primitives'][0]
        region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='spear')
        a=d['accessors'][p['attributes']['WEIGHTS_0']];v=d['bufferViews'][a['bufferView']]
        blob=bytearray(self.g.bin)
        fmt={5123:'H',5126:'f'}[a['componentType']];half=32767 if fmt=='H' else .5
        stride=v.get('byteStride',struct.calcsize(fmt)*4)
        struct.pack_into('<'+fmt*4,blob,v['byteOffset']+region['start']*stride,half,half,0,0)
        self.write(d,blob);self.assertTrue(any('single-bone unit weights' in e for e in validate(self.path)['errors']))
    def test_empty_team_mask(self):
        d=copy.deepcopy(self.g.doc);p=d['meshes'][0]['primitives'][0]
        region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r.get('team')=='crest')
        a=d['accessors'][p['attributes']['COLOR_0']];v=d['bufferViews'][a['bufferView']]
        blob=bytearray(self.g.bin)
        fmt={5121:'B',5123:'H',5126:'f'}[a['componentType']]
        stride=v.get('byteStride',struct.calcsize(fmt)*4)
        struct.pack_into('<'+fmt,blob,v.get('byteOffset',0)+a.get('byteOffset',0)+region['start']*stride,0)
        self.write(d,blob);self.assertTrue(any('team mask must be one' in e for e in validate(self.path)['errors']))
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
