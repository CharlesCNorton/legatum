"""Frozen rest-camera UV projection on real mesh surfaces; generated unseen pelt."""
import bpy,os,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout';A=R/'assets/barbarian-scout'
bpy.ops.wm.open_mainfile(filepath=str(M/'registered.blend'))
sc=bpy.context.scene;cam=sc.camera
(M/'texture-process.json').write_text(json.dumps({'pid':os.getpid(),'stage':'start'}))
paint=bpy.data.images.load(str(A/'painting-aligned.png'));paint.pack()
fur=bpy.data.images.load(str(A/'painted-fur.png'));fur.pack()
stonepaint=bpy.data.images.load(str(A/'stone-fill.png'));stonepaint.pack()
underpaint=bpy.data.images.load(str(A/'cloth-underpaint.png'));underpaint.pack()
linen=bpy.data.images.load(str(A/'painted-linen.png'));linen.pack()
fills={}
for kind in ('skin','hair','leather'):
    fills[kind]=bpy.data.images.load(str(A/('painted-'+kind+'.png')));fills[kind].pack()
# Convert kit curves to genuine mesh surfaces so UVs are frozen in bind space.
for o in list(sc.objects):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.update()
view=cam.matrix_world.to_quaternion()@Vector((0,0,1))
deps=bpy.context.evaluated_depsgraph_get()
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
    # The base is a stationary solid disc with a separate clean projection plate.
    base=o.name=='GEO-stationary-cream-base'
    uv=o.data.uv_layers.new(name='PaintingRest')
    weights=o.data.color_attributes.new(name='ProjectionCoverage',type='FLOAT_COLOR',domain='CORNER')
    visible={}
    for vertex in o.data.vertices:
        point=o.matrix_world@vertex.co
        hit,location,normal,face,occluder,matrix=sc.ray_cast(deps,point+view*.003,view,distance=20)
        visible[vertex.index]=int(not hit or (occluder==o and (location-point).length<.035))
    for poly in o.data.polygons:
        n=(o.matrix_world.to_3x3()@poly.normal).normalized()
        for li in poly.loop_indices:
            co=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            p=world_to_camera_view(sc,cam,co)
            uv.data[li].uv=(p.x,p.y)
            index=o.data.loops[li].vertex_index
            coverage=visible[index]  # visibility, not grazing angle, determines rest paint
            # Overlapping locks move with the same head: masking each by its
            # neighbour creates alternating bare stripes, not useful occlusion.
            if o.name.startswith(('GEO-sculpted-hair','GEO-beard','GEO-sculpted-scalp')):coverage=1.0
            right_hand=False
            if o.name=='GEO-anatomy':
                groups=[o.vertex_groups[g.group].name for g in o.data.vertices[index].groups if g.weight>.02]
                right_hand=any(n.endswith('_r') and n.startswith(('hand','index','middle','ring','pinky','thumb')) for n in groups)
                raised=any(n.endswith('_l') and n.startswith(('hand','index','middle','ring','pinky','thumb')) for n in groups)
                if right_hand or raised:coverage=1.0 if n.dot(view)>-.15 else 0.0
            # Exclude the stowed axe from cloth beneath it: it must not remain
            # painted on the torso when the actual weapon is drawn.
            px=p.x*256;py=(1-p.y)*256
            if o.name=='GEO-anatomy' and not right_hand and ((px-117)/10)**2+((py-119)/14)**2<1:coverage=0
            # Garments beneath moving equipment use a generated clean underpainting.
            # They must not lose their brushwork to broad binary exclusion ellipses.
            weights.data[li].color=(coverage,)*3+(1,)
    under=o.data.color_attributes.new(name='UnderpaintCoverage',type='FLOAT_COLOR',domain='CORNER')
    for li,datum in enumerate(uv.data):
        px=datum.uv.x*256;py=(1-datum.uv.y)*256
        # Wide hidden garment region feathered over 8 pixels into the original.
        amount=max(0,min(1,(px-68)/8,(136-px)/8,(py-90)/8,(179-py)/8))
        under.data[li].color=(amount,)*3+(1,)
        if amount>.1 and o.name in ('GEO-folded-tunic-hem','GEO-linen-shirt','GEO-wool-trousers'):
            weights.data[li].color=(1,1,1,1)
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
        if 'pelt' in old.name or 'hair' in old.name:
            tex=ns.new('ShaderNodeTexImage');tex.image=fur;tex.projection='BOX';tex.projection_blend=.35
            coord=ns.new('ShaderNodeTexCoord');ls.new(coord.outputs['Generated'],tex.inputs['Vector']);fallback=tex.outputs['Color']
        if 'woven' in old.name or 'wool' in old.name or 'leather' in old.name:
            tex=ns.new('ShaderNodeTexImage');tex.image=linen;tex.projection='BOX';tex.projection_blend=.35
            coord=ns.new('ShaderNodeTexCoord');ls.new(coord.outputs['Generated'],tex.inputs['Vector'])
            tint=ns.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=.72
            tint.inputs[2].default_value=bs.inputs['Base Color'].default_value
            ls.new(tex.outputs['Color'],tint.inputs[1]);fallback=tint.outputs[0]
        for kind,img in fills.items():
            if kind in old.name:
                tex=ns.new('ShaderNodeTexImage');tex.image=img;tex.projection='BOX';tex.projection_blend=.4
                coord=ns.new('ShaderNodeTexCoord');ls.new(coord.outputs['Generated'],tex.inputs['Vector']);fallback=tex.outputs['Color']
        if base:
            # The generated empty top and original lower rim contain no source boots.
            for poly in o.data.polygons:
                for li in poly.loop_indices:
                    weights.data[li].color=(1,1,1,1)
            bump.inputs['Distance'].default_value=.0015
        tex=ns.new('ShaderNodeTexImage');tex.image=stonepaint if base else paint;tex.extension='CLIP'
        garment=o.name in ('GEO-folded-tunic-hem','GEO-linen-shirt','GEO-wool-trousers','GEO-wolf-pelt-cowl','GEO-folded-pelt-cape','GEO-layered-fur-tufts','GEO-layered-fur-tufts.001')
        u=ns.new('ShaderNodeUVMap');u.uv_map='PaintingRest';ls.new(u.outputs['UV'],tex.inputs['Vector'])
        if garment:
            clean=ns.new('ShaderNodeTexImage');clean.image=underpaint;clean.extension='CLIP';ls.new(u.outputs['UV'],clean.inputs['Vector'])
            mask=ns.new('ShaderNodeVertexColor');mask.layer_name='UnderpaintCoverage'
            blend=ns.new('ShaderNodeMixRGB');ls.new(mask.outputs['Color'],blend.inputs[0]);ls.new(tex.outputs['Color'],blend.inputs[1]);ls.new(clean.outputs['Color'],blend.inputs[2])
            paint_color=blend.outputs[0]
        else:paint_color=tex.outputs['Color']
        cov=ns.new('ShaderNodeVertexColor');cov.layer_name='ProjectionCoverage'
        mult=ns.new('ShaderNodeMath');mult.operation='MULTIPLY';ls.new(cov.outputs['Color'],mult.inputs[0]);ls.new(tex.outputs['Alpha'],mult.inputs[1])
        mix=ns.new('ShaderNodeMixRGB');mix.inputs[1].default_value=bs.inputs['Base Color'].default_value
        if fallback:ls.new(fallback,mix.inputs[1])
        ls.new(mult.outputs[0],mix.inputs[0]);ls.new(paint_color,mix.inputs[2]);ls.new(mix.outputs[0],bs.inputs['Base Color'])
        # Camera-only painted illumination: physical shaders still receive all
        # shadow/bounce rays. Source brushwork is not an orange scene light.
        pigment=ns.new('ShaderNodeEmission');pigment.name='Painted camera pigment'
        ls.new(mix.outputs[0],pigment.inputs['Color'])
        camera=ns.new('ShaderNodeLightPath')
        amount=ns.new('ShaderNodeMath');amount.operation='MULTIPLY'
        strength=ns.new('ShaderNodeMapRange');strength.inputs['To Min'].default_value=.20 if base else .38;strength.inputs['To Max'].default_value=.78 if base else .94
        ls.new(mult.outputs[0],strength.inputs['Value'])
        ls.new(camera.outputs['Is Camera Ray'],amount.inputs[0]);ls.new(strength.outputs[0],amount.inputs[1])
        shade=ns.new('ShaderNodeMixShader');ls.new(amount.outputs[0],shade.inputs[0])
        ls.new(bs.outputs[0],shade.inputs[1]);ls.new(pigment.outputs[0],shade.inputs[2])
        ls.new(shade.outputs[0],ns.get('Material Output').inputs['Surface'])
        bs.inputs['Roughness'].default_value=.78 if bs.inputs['Metallic'].default_value==0 else .39
sc['projection']='Frozen rest UV; semantic generated cloth/stone occlusion fills; generated backfill; no billboard'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-scout.blend'))
(M/'texture-process.json').write_text(json.dumps({'pid':os.getpid(),'stage':'complete'}))
print('TEXTURES_READY')
