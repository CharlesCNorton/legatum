"""Regression checks for the two-LOD map handoff; use the delivered unit fixture."""
import copy,json,struct,tempfile,unittest
from pathlib import Path
from validate_glb import GLB,validate
UNIT=Path(__file__).parent/'units/spearman-0ad'

class PremiumContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=GLB(UNIT/'spearman.glb')
    def result(self,change):
        d=copy.deepcopy(self.source.doc);change(d)
        raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4);blob=self.source.bin
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'spearman.glb'
            for name in ['PROVENANCE.md','LICENSE-ART']:(p.parent/name).write_bytes((UNIT/name).read_bytes())
            p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(blob))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(blob),0x004e4942)+blob)
            return validate(p)
    def test_delivered_contract(self):self.assertTrue(self.result(lambda d:None)['valid'])
    def test_download_budget(self):
        r=self.result(lambda d:d['asset']['extras'].update(oversize='x'*2_000_000))
        self.assertIn('GLB must be under 2 MB (2000000 bytes)',r['errors'])
    def test_named_lods_required(self):
        r=self.result(lambda d:d['meshes'][1].update(name='unnamed'));self.assertIn('Expected named LOD0 and LOD1 meshes',r['errors'])
    def test_single_shared_material(self):
        r=self.result(lambda d:d['materials'].append(copy.deepcopy(d['materials'][0])));self.assertIn('Must have exactly 1 material',r['errors'])
    def test_no_msft_lod(self):
        r=self.result(lambda d:d.update(extensionsUsed=['MSFT_lod']));self.assertIn('MSFT_lod is forbidden',r['errors'])
    def test_mask_required_on_second_lod(self):
        r=self.result(lambda d:d['meshes'][1]['primitives'][0]['attributes'].pop('COLOR_0'));self.assertIn('Missing team mask COLOR_0',r['errors'])
    def test_shared_orm(self):
        r=self.result(lambda d:d['materials'][0]['occlusionTexture'].update(index=0));self.assertIn('Occlusion and metallic/roughness must share packed ORM',r['errors'])
    def test_uv0(self):
        r=self.result(lambda d:d['materials'][0]['normalTexture'].update(texCoord=1));self.assertIn('All maps must use UV0',r['errors'])
    def test_authoring_resolution_required(self):
        r=self.result(lambda d:d['asset']['extras'].update(texture_master_size=1024))
        self.assertIn('Textures must declare 2048 authoring masters',r['errors'])
    def test_team_regions_required_per_lod(self):
        def change(d):
            for region in d['meshes'][1]['extras']['vertex_regions']:
                if region.get('team')=='crest':region['team']=None
        r=self.result(change)
        self.assertIn('spearman_LOD1 team mask must cover cloak trim, shield rim and crest',r['errors'])
    def test_unit_normals(self):
        def change(d):
            attrs=d['meshes'][1]['primitives'][0]['attributes'];attrs['NORMAL']=attrs['POSITION']
        r=self.result(change)
        self.assertIn('spearman_LOD1 NORMAL vectors must be unit length',r['errors'])
    def test_rigid_spear_socket(self):
        def change(d):
            for r in d['meshes'][1]['extras']['vertex_regions']:
                if r['part']=='spear':r['bone']='hip'
        r=self.result(change);self.assertIn('spear must attach to weapon_R',r['errors'])

if __name__=='__main__':unittest.main()
