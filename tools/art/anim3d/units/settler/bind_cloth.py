"""Bind full-depth robes to the existing posed rig without changing their rest view."""
import bpy
from mathutils import Matrix,Vector


def bind_robes(rig):
    # Calibrate the full blended skin transform at the painted rest pose.
    matrices={p.name:p.matrix @ p.bone.matrix_local.inverted() for p in rig.pose.bones}
    world_to_rig=rig.matrix_world.inverted()
    for ob in list(bpy.context.scene.objects):
        if ob.type!='MESH' or not any(n in ob.name for n in ['full length linen skirt','olive diagonal overdrape']):continue
        world=ob.matrix_world.copy()
        basis=ob.data.shape_keys.key_blocks[0].data if ob.data.shape_keys else ob.data.vertices
        coords=[world @ v.co for v in basis]
        keys={k.name:[world @ v.co for v in k.data] for k in ob.data.shape_keys.key_blocks} if ob.data.shape_keys else {}
        ob.parent=rig;ob.parent_type='OBJECT';ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
        ob.vertex_groups.clear()
        groups={name:ob.vertex_groups.new(name=name) for name in ['pelvis','thigh_l','thigh_r','calf_l','calf_r']}
        for i,pos in enumerate(coords):
            leg=max(0,min(.90,(1.10-pos.z)/.65))
            calf=max(0,min(.35,(.64-pos.z)/.50))*leg
            left=max(.10,min(.90,.5+pos.x/.45))
            weights={'pelvis':1-leg,'thigh_l':(leg-calf)*left,'thigh_r':(leg-calf)*(1-left),'calf_l':calf*left,'calf_r':calf*(1-left)}
            mat=Matrix([[sum(weights[n]*matrices[n][r][c] for n in weights) for c in range(4)] for r in range(4)])
            inv=mat.inverted();ob.data.vertices[i].co=inv @ world_to_rig @ pos
            for n,w in weights.items():
                if w>0:groups[n].add([i],w,'REPLACE')
            for key,values in keys.items():ob.data.shape_keys.key_blocks[key].data[i].co=inv @ world_to_rig @ values[i]
        arm=ob.modifiers.new('Tailored leg-following skin','ARMATURE');arm.object=rig
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.modifier_move_to_index(modifier=arm.name,index=0)
        ob['cloth_binding']='Inverse blended rest-pose skin, complete robe with shared thigh/calf weights'
        ob.data.update()
        disabled=[m for m in ob.modifiers if m!=arm and m.show_viewport]
        for mod in disabled:mod.show_viewport=False
        bpy.context.view_layer.update()
        evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        error=max(((evaluated.matrix_world @ v.co)-coords[v.index]).length for v in mesh.vertices)
        evaluated.to_mesh_clear()
        for mod in disabled:mod.show_viewport=True
        assert error<1e-5,(ob.name,'rest binding changed geometry',error)
        ob['rest_binding_max_error_m']=error
    bpy.context.view_layer.update()
