"""Frozen camera UVs on deforming solids, generated hidden fills, actual AO/curvature bakes."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/settler';A=R/'assets/settler';V=R/'review/3d-v2'
bpy.ops.wm.open_mainfile(filepath=str(M/'settler-plain.blend'));sc=bpy.context.scene;cam=sc.camera
images={n:bpy.data.images.load(str(A/f'{n}.png'),check_existing=True) for n in ['projection','fill-ivory','fill-olive','fill-rust','fill-leather']}
# Task-owned Principled materials, with tileable generated fills on hidden sides.
for mat in list(bpy.data.materials):
    if not mat.name.startswith('MAT-'):continue
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');name=mat.name
    tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=155;noise.inputs['Detail'].default_value=3;l.new(tc.outputs['Generated'],noise.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    kind=next((k for k in ['ivory','olive','rust','leather'] if k in name),None)
    if 'terracotta' in name:kind='rust'
    if kind:
        tex=n.new('ShaderNodeTexImage');tex.image=images['fill-'+kind];tex.projection='BOX';tex.projection_blend=.25;l.new(tc.outputs['Generated'],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.45;mix.inputs[1].default_value=p.inputs['Base Color'].default_value;l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
        p.inputs['Sheen Weight'].default_value=.22 if kind!='leather' else 0
    if 'skin' in name:p.inputs['Subsurface Weight'].default_value=.06;p.inputs['Subsurface Radius'].default_value=(.8,.3,.15)
    if 'cream stone' in name:
        p.inputs['Base Color'].default_value=(.92,.71,.44,1);p.inputs['Emission Color'].default_value=(.815,.624,.352,1);p.inputs['Emission Strength'].default_value=.32
    # Physical AO and Pointiness add recessed shade and exposed edge wear before projection.
    old=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
    if old is None:
        rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;old=rgb.outputs[0]
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
    mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.3;l.new(old,mul.inputs[1]);l.new(ao.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],p.inputs['Base Color'])
    if 'brass' in name:
        geo=n.new('ShaderNodeNewGeometry');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.35;ramp.color_ramp.elements[0].color=(.15,.15,.15,1);ramp.color_ramp.elements[1].position=.55;ramp.color_ramp.elements[1].color=(.4,.4,.4,1);l.new(geo.outputs['Pointiness'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Roughness'])
# Convert curves to real mesh solids, preserving bone parent transforms, for projection.
for o in list(sc.objects):
    if o.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
records=[]
for ob in list(sc.objects):
    if ob.type!='MESH' or any(k in ob.name for k in ['eyes','stationary']):continue
    disabled=[]
    for mod in ob.modifiers:
        if mod.type!='ARMATURE' and mod.show_viewport:disabled.append(mod);mod.show_viewport=False
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(ob.data.vertices)
    coords=[world_to_camera_view(sc,cam,ev.matrix_world @ v.co) for v in me.vertices]
    facing=[max(0,min(1,(abs((ev.matrix_world.to_3x3() @ v.normal).normalized().dot((cam.location-ev.matrix_world @ v.co).normalized()))+.10)/.20)) for v in me.vertices]
    # One camera projection on the fitted geometry: no per-garment UV stretching.
    # Visibility is geometric, not the mesh normal sign (thin cloth can face inward).
    # Offset the ray origin toward camera to avoid self intersections at its endpoint.
    for v in me.vertices:
        point=ev.matrix_world @ v.co;direction=cam.matrix_world.to_quaternion() @ Vector((0,0,1))
        hit,loc,normal,index,hit_ob,matrix=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),point+direction*.012,direction,distance=20)
        if hit and (hit_ob.original!=ob.original or (loc-point).length>.04):facing[v.index]=0
        if 'MPFB female' in ob.name:
            dot=(ev.matrix_world.to_3x3() @ v.normal).normalized().dot(direction)
            facing[v.index]*=max(0,min(1,(dot+.05)/.20))
    ev.to_mesh_clear()
    for mod in disabled:mod.show_viewport=True
    uv=ob.data.uv_layers.get('Rest painting') or ob.data.uv_layers.new(name='Rest painting');mask=ob.data.color_attributes.new(name='Paint visibility',type='FLOAT_COLOR',domain='CORNER')
    for loop in ob.data.loops:
        i=loop.vertex_index;c=coords[i];uv.data[loop.index].uv=(c.x,c.y);f=facing[i];mask.data[loop.index].color=(f,f,f,1)
    for slot in ob.material_slots:
        mat=slot.material.copy();slot.material=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
        if not p:continue
        # One image, one fixed camera; material masks were erasing the face/folds.
        # Existing generated fills remain under the alpha and on unseen sides.
        kind='projection';strength=.985
        tc=n.new('ShaderNodeUVMap');tc.uv_map='Rest painting';tex=n.new('ShaderNodeTexImage');tex.image=images[kind];tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
        attr=n.new('ShaderNodeVertexColor');attr.layer_name='Paint visibility';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(attr.outputs['Color'],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1]);weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=strength;l.new(mult.outputs[0],weight.inputs[0])
        # Camera-only painted illumination; real BSDF retains shadows and hidden fill.
        pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera painted pigment'
        pigment.inputs['Base Color'].default_value=(0,0,0,1)
        pigment.inputs['Roughness'].default_value=1
        pigment.inputs['Specular IOR Level'].default_value=0
        pigment.inputs['Emission Strength'].default_value=1
        l.new(tex.outputs['Color'],pigment.inputs['Emission Color'])
        rays=n.new('ShaderNodeLightPath');visible=n.new('ShaderNodeMath');visible.operation='MULTIPLY'
        l.new(weight.outputs[0],visible.inputs[0]);l.new(rays.outputs['Is Camera Ray'],visible.inputs[1])
        blend=n.new('ShaderNodeMixShader');l.new(visible.outputs[0],blend.inputs[0]);l.new(p.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
    records.append({'object':ob.name,'vertices':len(ob.data.vertices),'projection':'Frozen evaluated rest-camera UV; facing and material mask'})
# Small true UV bakes for the principal cloth, anatomy, pack and clasp; retained as inspectable maps.
texdir=M/'textures/baked';texdir.mkdir(parents=True,exist_ok=True);sc.cycles.samples=8;sc.render.bake.margin=4
bakes=[]
for name in ['GEO-full length linen skirt','GEO-olive diagonal overdrape','GEO-open linen hood crown','GEO-rust shawl shoulder folds','GEO-brass shawl pin']:
    ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    uv=ob.data.uv_layers.new(name='Bake unwrap');ob.data.uv_layers.active=uv;uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
    disabled=[]
    for mod in ob.modifiers:
        if mod.type=='SOLIDIFY' and mod.show_render:disabled.append(mod);mod.show_render=False
    mat=ob.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');output=n.get('Material Output');surf=output.inputs['Surface'].links[0].from_socket
    for kind in ['ao','curvature']:
        img=bpy.data.images.new(name+'-'+kind,width=256,height=256,alpha=False);img.colorspace_settings.name='Non-Color';target=n.new('ShaderNodeTexImage');target.image=img;n.active=target
        if kind=='ao':bpy.ops.object.bake(type='AO')
        else:
            geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface']);bpy.ops.object.bake(type='EMIT');l.new(surf,output.inputs['Surface']);n.remove(em);n.remove(geo)
        path=texdir/(name[4:].replace(' ','-')+'-'+kind+'.png');img.filepath_raw=str(path);img.file_format='PNG';img.save();img.pack()
        tc=n.new('ShaderNodeUVMap');tc.uv_map='Bake unwrap';l.new(tc.outputs[0],target.inputs['Vector'])
        if kind=='ao':
            old=p.inputs['Base Color'].links[0].from_socket;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.18;l.new(old,mix.inputs[1]);l.new(target.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
        else:
            ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.3;ramp.inputs['From Max'].default_value=.6;ramp.inputs['To Min'].default_value=.92 if 'brass' not in name else .48;ramp.inputs['To Max'].default_value=.65 if 'brass' not in name else .22;l.new(target.outputs[0],ramp.inputs['Value']);l.new(ramp.outputs[0],p.inputs['Roughness'])
        bakes.append({'object':name,'kind':kind,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for mod in disabled:mod.show_render=True
sc['projection']='Frozen camera UV on true meshes; painting plus generated unseen fills. Painted light is intentionally retained.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'settler.blend'));(M/'projection.json').write_text(json.dumps(records,indent=2));(M/'bakes.json').write_text(json.dumps(bakes,indent=2))
with (V/'settler-log.md').open('a') as f:f.write('- Applied frozen-camera painting, generated unseen linen/olive/rust/leather, fine bump, warm product lights, physical AO and ten actual AO/curvature maps.\n')
