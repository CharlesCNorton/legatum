"""Finish the rest surface and ground the actual leather soles before projection."""
import bpy, bmesh, json
from mathutils import Matrix, Vector
from math import sqrt
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils.kdtree import KDTree

def refine(sc):
    rig=bpy.data.objects['Gaesatae • MPFB game_engine']
    def aim(name,direction):
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
        mat=((q@Vector((0,1,0))).rotation_difference(direction.normalized())@q).to_matrix().to_4x4()
        mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
    def ankle(side,target):
        u=rig.pose.bones['thigh_'+side];l=rig.pose.bones['calf_'+side]
        a=u.head.copy();axis=target-a;length=axis.length;axis.normalize()
        along=(u.bone.length**2-l.bone.length**2+length**2)/(2*length)
        pole=Vector((target.x,-.5,.5))-a;pole=(pole-axis*pole.dot(axis)).normalized()
        knee=a+axis*along+pole*sqrt(max(0,u.bone.length**2-along**2))
        aim(u.name,knee-a);aim(l.name,target-knee)
    # Native MPFB foot orientation is independent of the braced calf tilt.
    for side in ('r','l'):
        target=rig.pose.bones['calf_'+side].tail.copy();target.y+=.30
        ankle(side,target)
        foot=rig.pose.bones['foot_'+side]
        orient=foot.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        # Turn the near toes out to recover the broad planted boot silhouette.
        orient=Matrix.Rotation(.95 if side=='l' else -.25,4,'Z')@orient
        orient.translation=foot.head.copy();foot.matrix=orient
        bpy.context.view_layer.update()
        boot=bpy.data.objects['GEO-soft leather boot '+side]
        ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        bottom=min((boot.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        pose=foot.matrix.copy();pose.translation.z+=.103-bottom;foot.matrix=pose
        bpy.context.view_layer.update()
    base=bpy.data.objects['GEO-stationary cream stone']
    base.scale.x=base.scale.y=.97;base.location.y=.15
    for mod in base.modifiers:
        if mod.type=='BEVEL':mod.width=.006;mod.segments=3
    # Finish geometry BEFORE recording UVs. Keep live skeletal deformation.
    for ob in list(sc.objects):
        if ob.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
            bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    for ob in list(sc.objects):
        if ob.type!='MESH':continue
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        if ob.data.shape_keys:
            # Freeze the current mixed macro shape; retain native skin weights.
            ob.shape_key_add(name='Frozen macro mix',from_mix=True)
            for key in list(ob.data.shape_keys.key_blocks)[:-1]:ob.shape_key_remove(key)
            ob.shape_key_remove(ob.data.shape_keys.key_blocks[0])
        for mod in list(ob.modifiers):
            if mod.type in {'SUBSURF','SOLIDIFY','BEVEL'}:
                if not mod.show_viewport or (mod.type=='SUBSURF' and mod.levels==0):
                    ob.modifiers.remove(mod);continue
                bpy.ops.object.modifier_apply(modifier=mod.name)
    # Height-only shell extraction also selected the lowered T-pose hands.
    # Keep the connected pelvis/leg shell, identified by its lowest evaluated
    # point, not by vertex count (the accidental finger shells are denser).
    pants=bpy.data.objects['GEO-folded wool trousers'];links=[[] for v in pants.data.vertices]
    for edge in pants.data.edges:
        a,b=edge.vertices;links[a].append(b);links[b].append(a)
    pending=set(range(len(links)));components=[]
    while pending:
        queue=[pending.pop()];part=[]
        while queue:
            index=queue.pop();part.append(index)
            for neighbour in links[index]:
                if neighbour in pending:pending.remove(neighbour);queue.append(neighbour)
        components.append(part)
    ev=pants.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    keep=set(min(components,key=lambda ids:min((ev.matrix_world@me.vertices[i].co).z for i in ids)))
    ev.to_mesh_clear()
    assert len(keep)>10000,'Unexpected trouser topology'
    bm=bmesh.new();bm.from_mesh(pants.data);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index not in keep],context='VERTS')
    bm.to_mesh(pants.data);bm.free();pants.data.update()
    sc['removed_trouser_hand_islands']=len(components)-1
    # Sculpt the real hair crown to the painting silhouette, preserving depth.
    # No alpha geometry: only crown vertices outside the painted outline move.
    image=bpy.data.images.load(str(Path('app/src/assets/units/gaesatae-256.png').resolve()),check_existing=True)
    pixels=list(image.pixels);tree=KDTree(256*64);count=0
    for y in range(24,76):
        for x in range(113,164):
            offset=4*((255-y)*256+x)
            if pixels[offset+3]>.5:
                tree.insert(Vector((x+.5,y+.5,0)),count);count+=1
    tree.balance();cam=sc.camera;q=cam.matrix_world.to_quaternion()
    right=q@Vector((1,0,0));up=q@Vector((0,1,0));unit=cam.data.ortho_scale/256
    moved=0
    for ob in sc.objects:
        if ob.type!='MESH' or not ob.name.startswith(('GEO-swept hair lock','GEO-sculpted scalp hair')):continue
        inv=ob.matrix_world.inverted().to_3x3()
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        assert len(me.vertices)==len(ob.data.vertices),ob.name
        points=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
        skinned=any(m.type=='ARMATURE' for m in ob.modifiers)
        for v,world in zip(ob.data.vertices,points):
            uv=world_to_camera_view(sc,cam,world)
            x,y=uv.x*256,(1-uv.y)*256
            if not (110<x<166 and y<48):continue
            nearest,_,distance=tree.find(Vector((x,y,0)))
            if distance>1:
                delta=inv@(right*((nearest.x-x)*unit)+up*((y-nearest.y)*unit))
                if skinned:
                    skin=Matrix(((0.,0.,0.,0.),)*4);weight=0
                    for g in v.groups:
                        bone=rig.pose.bones.get(ob.vertex_groups[g.group].name)
                        if bone:
                            skin+=(bone.matrix@bone.bone.matrix_local.inverted())*g.weight;weight+=g.weight
                    if weight:delta=skin.to_3x3().inverted_safe()@delta
                v.co+=delta;moved+=1
    sc['crown_refined_vertices']=moved
    # Camera-only pigment must not illuminate neighbouring skin or stone.
    sc['surface_finished']=True
    rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
