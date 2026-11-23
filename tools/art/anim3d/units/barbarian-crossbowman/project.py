"""Frozen finished-surface camera pigment, ray visibility and generated hidden fills."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
painting=bpy.data.images.load(str(A/'painting-aligned.png'))
view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
dg=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
for ob in sc.objects:
    if ob.type!='MESH':continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh();offset=len(verts)
    verts.extend(ev.matrix_world@v.co for v in me.vertices)
    faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,faces)
records=[]
for obj in list(sc.objects):
    if obj.type!='MESH' or obj==base or obj==eyes:continue
    states=[(m,m.show_viewport) for m in obj.modifiers]
    for m,_ in states:
        if m.type!='ARMATURE':m.show_viewport=False
    bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    uv=obj.data.uv_layers.new(name='Painting fixed UV');att=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER');coords=[];weights=[]
    for v in me.vertices:
        world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);coords.append((q.x,q.y))
        normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
        facing=max(0,min(1,(normal.dot(view)-.03)*4))
        hit,_,_,distance=bvh.ray_cast(world+view*5,-view,5.1)
        visible=hit is not None and (hit-world).length<.025
        weight=facing if visible else 0
        x,y=q.x*256,(1-q.y)*256
        if obj.name in {'GEO-leather boots','GEO-olive wool trousers'} and x<110 and y>110:weight=0
        # Cloth behind hands must not retain detached painted fingers during attack.
        if obj.name.startswith(('GEO-quilted gambeson','GEO-waist leather belt')) and (90<x<110 and 87<y<110 or 145<x<165 and 89<y<107):weight=0
        weights.append(weight)
    assert len(me.vertices)==len(obj.data.vertices),obj.name
    for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
    ev.to_mesh_clear()
    for m,on in states:m.show_viewport=on
    for i,old in enumerate(list(obj.data.materials)):
        mat=old.copy();obj.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
        tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';u=n.new('ShaderNodeUVMap');u.uv_map=uv.name;l.new(u.outputs[0],tex.inputs[0]);attr=n.new('ShaderNodeVertexColor');attr.layer_name=att.name
        mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(attr.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
        factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.97;l.new(mult.outputs[0],factor.inputs[0])
        # Principled pigment preserves the source's already-painted illumination for camera rays.
        pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera painted pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Roughness'].default_value=1; pigment.inputs['Specular IOR Level'].default_value=0
        l.new(tex.outputs['Color'],pigment.inputs['Emission Color']);pigment.inputs['Emission Strength'].default_value=1
        camera=n.new('ShaderNodeLightPath');mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(factor.outputs[0],mask.inputs[0]);l.new(camera.outputs['Is Camera Ray'],mask.inputs[1])
        physical=s.outputs[0]
        if old.get('painted_fill'):
            # A modest camera pigment contribution keeps revealed surfaces in the
            # painting's value range while retaining live form/contact shading.
            fill=n.new('ShaderNodeBsdfPrincipled');fill.name='Revealed painted fill';fill.inputs['Base Color'].default_value=(0,0,0,1);fill.inputs['Specular IOR Level'].default_value=0;fill.inputs['Emission Strength'].default_value=1
            l.new(s.inputs['Base Color'].links[0].from_socket,fill.inputs['Emission Color'])
            fw=n.new('ShaderNodeMath');fw.operation='MULTIPLY';fw.inputs[1].default_value=.42;l.new(camera.outputs['Is Camera Ray'],fw.inputs[0])
            fm=n.new('ShaderNodeMixShader');l.new(fw.outputs[0],fm.inputs[0]);l.new(s.outputs[0],fm.inputs[1]);l.new(fill.outputs[0],fm.inputs[2]);physical=fm.outputs[0]
        blend=n.new('ShaderNodeMixShader');l.new(mask.outputs[0],blend.inputs[0]);l.new(physical,blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
    records.append({'name':obj.name,'vertices':len(obj.data.vertices),'visible_vertices':sum(w>0 for w in weights),'finished_surface':True})
