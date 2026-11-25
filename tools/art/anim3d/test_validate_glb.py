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
    def patch_vertex(self,blob,accessor,row,values):
        a=self.g.doc['accessors'][accessor];v=self.g.doc['bufferViews'][a['bufferView']]
        fmt={5120:'b',5121:'B',5122:'h',5123:'H',5126:'f'}[a['componentType']]
        if a.get('normalized'):
            maximum={5120:127,5121:255,5122:32767,5123:65535}[a['componentType']]
            values=[round(x*maximum) for x in values]
        stride=v.get('byteStride',struct.calcsize(fmt)*len(values))
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)+row*stride
        struct.pack_into('<'+fmt*len(values),blob,offset,*values)
    def rejects(self,edit,message):
        d=copy.deepcopy(self.g.doc);edit(d);self.write(d)
        self.assertTrue(any(message in e for e in validate(self.path)['errors']))
    def test_delivered_asset(self):self.assertTrue(validate(ASSET)['valid'])
    def test_clip_name(self):self.rejects(lambda d:d['animations'][0].update(name='Attack'), 'five named clips')
    def test_credit(self):self.rejects(lambda d:d['asset'].pop('copyright'),'exact credit')
    def test_bone_budget(self):self.rejects(lambda d:d['skins'][0]['joints'].extend(d['skins'][0]['joints'][:12]),'40 joints')
    def test_normal_map(self):self.rejects(lambda d:d['materials'][0].update(normalTexture={'index':0}),'must be distinct')
    def test_team(self):
        self.rejects(lambda d:d['meshes'][0]['primitives'][0]['attributes'].pop('COLOR_0'),'Missing team mask')
    def test_extra_material(self):
        self.rejects(lambda d:d['materials'].append(copy.deepcopy(d['materials'][0])),'exactly 1 material')
    def test_extra_mesh(self):
        self.rejects(lambda d:d['meshes'].append(copy.deepcopy(d['meshes'][0])),'exactly 2 LOD meshes')
    def test_extra_primitive(self):
        self.rejects(lambda d:d['meshes'][0]['primitives'].append(copy.deepcopy(d['meshes'][0]['primitives'][0])),'one draw call per LOD')
    def test_prop_attachment(self):
        def edit(d):
            region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='spear')
            region['bone']='head'
        self.rejects(edit,'spear must attach to weapon_R')
    def test_prop_blended_weight(self):
        d=copy.deepcopy(self.g.doc);p=d['meshes'][0]['primitives'][0]
        region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r['part']=='spear')
        a=d['accessors'][p['attributes']['WEIGHTS_0']];v=d['bufferViews'][a['bufferView']]
        blob=bytearray(self.g.bin);self.patch_vertex(blob,p['attributes']['WEIGHTS_0'],region['start'],(.5,.5,0,0))
        self.write(d,blob);self.assertTrue(any('single-bone unit weights' in e for e in validate(self.path)['errors']))
    def test_empty_team_mask(self):
        d=copy.deepcopy(self.g.doc);p=d['meshes'][0]['primitives'][0]
        region=next(r for r in d['meshes'][0]['extras']['vertex_regions'] if r.get('team')=='crest')
        a=d['accessors'][p['attributes']['COLOR_0']];v=d['bufferViews'][a['bufferView']]
        blob=bytearray(self.g.bin);self.patch_vertex(blob,p['attributes']['COLOR_0'],region['start'],(0,0,0,1))
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
