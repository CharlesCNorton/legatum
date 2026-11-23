import bpy, os, json
from pathlib import Path
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
root=Path(os.environ['ANIM_ROOT']); out=root/'masters/peltast'; out.mkdir(exist_ok=True,parents=True)
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.40,muscle=.85,weight=.55,height=.5,proportions=.65);macro['race']={'caucasian':.8,'african':.1,'asian':.1}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB peltast anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.85/(hi-lo),)*3;bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Peltast'
system=root/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
(out/'bones.json').write_text(json.dumps({b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'anatomy.blend'))
