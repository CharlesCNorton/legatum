"""Frozen rest-camera UV projection on real mesh surfaces; generated unseen pelt."""
import bpy,os,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout';A=R/'assets/barbarian-scout'
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'))
sc=bpy.context.scene;cam=sc.camera
paint=bpy.data.images.load(str(A/'painting-aligned.png'));paint.pack()
fur=bpy.data.images.load(str(A/'painted-fur.png'));fur.pack()
# Convert kit curves to genuine mesh surfaces so UVs are frozen in bind space.
for o in list(sc.objects):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.update()
view=(cam.location-Vector((0,0,.8))).normalized()
for o in list(sc.objects):
    if o.type!='MESH' or not o.data.materials:continue
    # Correct winding on the outward-facing fitted garment rings.
    if o.name in ('GEO-wolf-pelt-cowl','GEO-folded-tunic-hem','GEO-sculpted-scalp'):
        center=Vector((0,0,0))
        if o.name=='GEO-sculpted-scalp':center=Vector((.04,-.10,1.34))
        for poly in o.data.polygons:
            radial=poly.center-center
            if o.name!='GEO-sculpted-scalp':radial.z=0
            if poly.normal.dot(radial)<0:poly.flip()
        o.data.update()
    # Keep base pigment independent of a projection; it is stationary warm stone.
    base=o.name=='GEO-stationary-cream-base'
    uv=o.data.uv_layers.new(name='PaintingRest')
    weights=o.data.color_attributes.new(name='ProjectionCoverage',type='FLOAT_COLOR',domain='CORNER')
    for poly in o.data.polygons:
        n=(o.matrix_world.to_3x3()@poly.normal).normalized()
        facing=max(0,min(1,(n.dot(view)+.18)/.55)) if not base else 0
        for li in poly.loop_indices:
            co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            p=world_to_camera_view(sc,cam,co)
            uv.data[li].uv=(p.x,p.y)
            weights.data[li].color=(facing,)*3+(1,)
    for idx,old in enumerate(list(o.data.materials)):
        mat=old.copy();mat.name=old.name+' • '+o.name;o.data.materials[idx]=mat
        ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=ns.get('Principled BSDF')
        if not bs:continue
        noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=140 if 'cloth' in old.name.lower() or 'wool' in old.name.lower() else 65
        noise.inputs['Detail'].default_value=3
        bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.006
        ls.new(noise.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],bs.inputs['Normal'])
        # Existing base material remains on all unseen surfaces. Generated fur
        # uses box mapping and blends gradually to projection on facing surfaces.
        fallback=None
        if 'pelt' in old.name:
            tex=ns.new('ShaderNodeTexImage');tex.image=fur;tex.projection='BOX';tex.projection_blend=.35
            coord=ns.new('ShaderNodeTexCoord');ls.new(coord.outputs['Generated'],tex.inputs['Vector']);fallback=tex.outputs['Color']
        if base:continue
        tex=ns.new('ShaderNodeTexImage');tex.image=paint;tex.extension='CLIP'
        u=ns.new('ShaderNodeUVMap');u.uv_map='PaintingRest';ls.new(u.outputs['UV'],tex.inputs['Vector'])
        cov=ns.new('ShaderNodeVertexColor');cov.layer_name='ProjectionCoverage'
        mult=ns.new('ShaderNodeMath');mult.operation='MULTIPLY';ls.new(cov.outputs['Color'],mult.inputs[0]);ls.new(tex.outputs['Alpha'],mult.inputs[1])
        mix=ns.new('ShaderNodeMixRGB');mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
        if fallback:ls.new(fallback,mix.inputs[1])
        ls.new(mult.outputs[0],mix.inputs[0]);ls.new(tex.outputs['Color'],mix.inputs[2]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
        # Retain painted lighting without flattening the three-dimensional forms.
        ls.new(mix.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.22
        bs.inputs['Roughness'].default_value=.78 if bs.inputs['Metallic'].default_value==0 else .39
sc['projection']='Frozen rest UV; camera-facing coverage; generated fur backfill; no billboard'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-scout.blend'))
print('TEXTURES_READY')
