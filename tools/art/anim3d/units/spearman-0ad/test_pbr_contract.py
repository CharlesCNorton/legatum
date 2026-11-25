"""Regression probes for the new LOD/PBR contract, using the delivered asset."""
import copy, json, struct, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from validate_glb import GLB,validate
UNIT=Path(__file__).resolve().parent
class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=GLB(UNIT/'spearman.glb')
    def mutated(self,edit):
        d=copy.deepcopy(self.g.doc);edit(d)
        raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4);blob=self.g.bin
        with tempfile.TemporaryDirectory(prefix='spearman-pbr-contract-') as tmp:
            p=Path(tmp)/'spearman.glb'
            for name in ('PROVENANCE.md','LICENSE-ART'):(p.parent/name).write_bytes((UNIT/name).read_bytes())
            p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
            return validate(p)
    def test_delivered_contract(self):self.assertTrue(validate(UNIT/'spearman.glb')['valid'])
    def test_wrong_lod_name_rejected(self):
        def edit(d):next(n for n in d['nodes'] if n.get('name')=='spearman_LOD1')['name']='accidental_duplicate'
        r=self.mutated(edit);self.assertIn('Named LOD nodes required',r['errors'])
    def test_missing_normal_rejected(self):
        r=self.mutated(lambda d:d['materials'][0].pop('normalTexture'))
        self.assertIn('Base colour, normal, ORM and occlusion bindings required',r['errors'])
    def test_separate_ao_rejected(self):
        def edit(d):d['materials'][0]['occlusionTexture']['index']=0
        r=self.mutated(edit);self.assertIn('AO and metallic/roughness must share packed ORM',r['errors'])
    def test_small_authoring_master_rejected(self):
        r=self.mutated(lambda d:d['asset']['extras'].update(texture_master_px=512))
        self.assertIn('Declare 2048 master textures',r['errors'])
    def test_orm_must_use_uv0(self):
        def edit(d):d['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']['texCoord']=1
        self.assertIn('All maps must use UV0',self.mutated(edit)['errors'])
    def test_shared_material_required(self):
        def edit(d):d['meshes'][1]['primitives'][0]['material']=1
        self.assertIn('LODs must share material 0',self.mutated(edit)['errors'])
    def test_lod1_cannot_drop_team_region(self):
        def edit(d):
            for r in d['meshes'][1]['extras']['vertex_regions']:
                if r.get('team')=='crest':r['team']=None
        r=self.mutated(edit);self.assertIn('spearman_LOD1: missing team regions',r['errors'])
if __name__=='__main__':unittest.main()
