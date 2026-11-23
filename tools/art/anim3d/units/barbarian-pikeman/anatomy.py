import bpy, json, os
from pathlib import Path
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
m=TargetService.get_default_macro_info_dict();m.update(gender=1.,age=.42,muscle=.65,weight=.45,height=.48,proportions=.65)
b=HumanService.create_human(macro_detail_dict=m)
bpy.context.view_layer.update();e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();z=[v.co.z for v in me.vertices];e.to_mesh_clear()
s=1.72/(max(z)-min(z));b.scale=(s,s,s);bpy.context.view_layer.objects.active=b;b.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
r=HumanService.add_builtin_rig(b,'game_engine');b.name='GEO-MPFB-anatomy';r.name='RIG-pikeman'
r.location.z=.10
p=Path(os.environ['ANIM_ROOT'])/'masters/barbarian-pikeman'
(p/'bones.json').write_text(json.dumps({x.name:{'head':list(x.head_local),'tail':list(x.tail_local)} for x in r.data.bones},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'anatomy.blend'))
