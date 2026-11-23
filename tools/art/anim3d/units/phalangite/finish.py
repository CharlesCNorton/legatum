"""Paint the real rest-pose meshes; retain thickness, weights and back materials."""
import bpy,os,json,math,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/phalangite';A=R/'assets/phalangite'
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));sc=bpy.context.scene
sys.path.insert(0,str(Path(__file__).parent))
from refine import refine
refine(sc)
bpy.ops.wm.save_as_mainfile(filepath=str(M/'fitted-plain.blend'))
# Scan-scale grain on every surface, generated original project linen/bronze on unseen faces.
for mat in list(bpy.data.materials):
    if not mat.use_nodes:continue
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    if s is None:continue
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=145 if 'linen' in mat.name.lower() else 65;noise.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0025;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    ramp=n.new('ShaderNodeValToRGB');base=s.inputs['Base Color'].default_value[:]
    ramp.color_ramp.elements[0].color=tuple(c*.65 for c in base[:3])+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,c*1.15) for c in base[:3])+(1,)
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],s.inputs['Base Color'])
    kind='linen' if 'linen' in mat.name.lower() else 'bronze' if 'bronze' in mat.name.lower() else None
    if kind:
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/f'fill-{kind}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3
        coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.35;l.new(ramp.outputs[0],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
    if 'wool' in mat.name.lower() or 'linen' in mat.name.lower():s.inputs['Sheen Weight'].default_value=.2
# Actual AO and curvature maps, used as subtle cavity/wear signals beneath projection.
out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True);records=[]
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=4
for name in ['GEO-linothorax','GEO-helmet-bowl','GEO-small-bronze-shield']:
    ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    states=[(mod,mod.show_viewport,mod.show_render) for mod in ob.modifiers if mod.type=='SOLIDIFY']
    for mod,_,_ in states:mod.show_viewport=False;mod.show_render=False
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers.active.name='Baked surface';mat=ob.data.materials[0].copy();ob.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');output=n.get('Material Output');maps={}
    for mode in ['AO','curvature']:
        image=bpy.data.images.new(name+' '+mode,256,256,alpha=False);image.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=image;n.active=tex
        uv=n.new('ShaderNodeUVMap');uv.uv_map='Baked surface';l.new(uv.outputs[0],tex.inputs['Vector']);old=output.inputs['Surface'].links[0].from_socket
        if mode=='curvature':
            geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],output.inputs[0])
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        if mode=='curvature':l.new(old,output.inputs[0]);n.remove(em);n.remove(geo)
        image.filepath_raw=str(out/f'{name}-{mode}.png');image.file_format='PNG';image.save();maps[mode]=tex
    base=s.inputs['Base Color'].links[0].from_socket;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;l.new(base,mix.inputs[1]);l.new(maps['AO'].outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
    if 'bronze' in name or 'helmet' in name:
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.49;ramp.color_ramp.elements[0].color=(.48,.48,.48,1);ramp.color_ramp.elements[1].position=.52;ramp.color_ramp.elements[1].color=(.24,.24,.24,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Roughness'])
    for mod,view,render in states:mod.show_viewport=view;mod.show_render=render
    records.append({'object':name,'size':256,'maps':['AO','curvature']})
(out/'manifest.json').write_text(json.dumps(records,indent=2))
# Convert code curves to true round meshes before storing frozen UVs.
for ob in list(sc.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
painting=bpy.data.images.load(str(A/'painting-aligned.png'));projected=[]
view=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
for ob in list(sc.objects):
    if ob.type!='MESH' or 'base' in ob.name or 'sarissa' in ob.name or 'iron-butt' in ob.name or 'eyes' in ob.name.lower():continue
    # Only armature is evaluated so loop/vertex indexes remain those of editable geometry.
    states=[(mod,mod.show_viewport) for mod in ob.modifiers]
    for mod,_ in states:
        if mod.type!='ARMATURE':mod.show_viewport=False
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(ob.data.vertices),ob.name
    coords=[];inc=[]
    for v in me.vertices:
        world=ev.matrix_world @ v.co;q=world_to_camera_view(sc,sc.camera,world);coords.append((q.x,q.y))
        normal=(ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized()
        facing=normal.dot(view)
        # Shield back faces must not inherit the overlying torso/cloth pixels.
        # Body visibility remains limited by the fitted overlapping armour.
        visible=True
        if 'shield' in ob.name:
            hit,location,_,_,_,_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),world+view*5,-view,distance=5.03)
            visible=not hit or (location-world).length<.018
        inc.append(max(0,min(1,(facing-.02)/.35)) if visible else 0)
    ev.to_mesh_clear()
    for mod,state in states:mod.show_viewport=state
    uv=ob.data.uv_layers.new(name='Painting frozen rest');att=ob.data.color_attributes.new(name='Painting confidence',type='FLOAT_COLOR',domain='CORNER')
    for i,loop in enumerate(ob.data.loops):uv.data[i].uv=coords[loop.vertex_index];att.data[i].color=(inc[loop.vertex_index],)*3+(1,)
    for idx,oldmat in enumerate(list(ob.data.materials)):
        mat=oldmat.copy();mat.name=ob.name+' painted';ob.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
        if s is None:continue
        uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(uvnode.outputs[0],tex.inputs['Vector']);a=n.new('ShaderNodeVertexColor');a.layer_name=att.name
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(a.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.97;l.new(mul.outputs[0],strength.inputs[0])
        # The painted shaft must not remain stuck to the chest when the real
        # continuous 3D sarissa moves. This source-space exclusion changes only
        # paint confidence; real geometry and mesh opacity remain untouched.
        if any(k in ob.name for k in ['linothorax','pteruges','belt','shoulder-flap']):
            sep=n.new('ShaderNodeSeparateXYZ');l.new(uvnode.outputs[0],sep.inputs[0])
            xx=n.new('ShaderNodeMath');xx.operation='MULTIPLY';xx.inputs[1].default_value=256*.73913;l.new(sep.outputs['X'],xx.inputs[0])
            yy=n.new('ShaderNodeMath');yy.operation='MULTIPLY';yy.inputs[1].default_value=-256;l.new(sep.outputs['Y'],yy.inputs[0])
            add=n.new('ShaderNodeMath');add.operation='ADD';l.new(xx.outputs[0],add.inputs[0]);l.new(yy.outputs[0],add.inputs[1])
            bias=n.new('ShaderNodeMath');bias.operation='ADD';bias.inputs[1].default_value=256-193.065;l.new(add.outputs[0],bias.inputs[0])
            absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(bias.outputs[0],absolute.inputs[0])
            outside=n.new('ShaderNodeMath');outside.operation='GREATER_THAN';outside.inputs[1].default_value=1.6;l.new(absolute.outputs[0],outside.inputs[0])
            clean=n.new('ShaderNodeMath');clean.operation='MULTIPLY';l.new(mul.outputs[0],clean.inputs[0]);l.new(outside.outputs[0],clean.inputs[1]);l.new(clean.outputs[0],strength.inputs[0])
        # Preserve painted illumination for camera rays without emitting it into
        # the scene or applying the product lights a second time.
        pigment=n.new('ShaderNodeEmission');pigment.name='Camera painted pigment';l.new(tex.outputs['Color'],pigment.inputs['Color'])
        lightpath=n.new('ShaderNodeLightPath');gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(lightpath.outputs['Is Camera Ray'],gate.inputs[0]);l.new(strength.outputs[0],gate.inputs[1])
        blend=n.new('ShaderNodeMixShader');l.new(gate.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
    projected.append(ob.name)
# Warm limestone has physical contact shade, with camera-only painted pigment.
# No figure painting (and therefore no permanent painted feet) enters this material.
base=bpy.data.objects['GEO-stationary-cream-base'];base.data.materials.clear()
# Clean image-generated stone plate: no permanent feet or source contact shadow.
stone=bpy.data.images.load(str(A/'stone-fill-source.png'))
uv=base.data.uv_layers.new(name='Clean stone projection')
for i,loop in enumerate(base.data.loops):
    q=world_to_camera_view(sc,sc.camera,base.matrix_world @ base.data.vertices[loop.vertex_index].co)
    # Register generated clean plate bounds to the original token base bounds.
    x=q.x*256;y=(1-q.y)*256
    uv.data[i].uv=(.100+(x-26)/117*.450, 1-(.813+(y-212)/31*.118))
def linear(v):
    v=v/255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for label,rgb in [('top',(249,224,188)),('rim',(223,177,124))]:
    mat=bpy.data.materials.new('Cream limestone '+label);mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    color=tuple(linear(v) for v in rgb)+(1,);s.inputs['Base Color'].default_value=color;s.inputs['Roughness'].default_value=.86
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=350
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.045;bump.inputs['Distance'].default_value=.001;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.18
    shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.60;shade.inputs[1].default_value=color;l.new(ao.outputs['AO'],shade.inputs[2])
    tex=n.new('ShaderNodeTexImage');tex.image=stone;tex.extension='EXTEND'
    uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='Clean stone projection';l.new(uvnode.outputs[0],tex.inputs['Vector'])
    pigment=n.new('ShaderNodeMixRGB');pigment.inputs[1].default_value=color
    l.new(tex.outputs['Alpha'],pigment.inputs[0]);l.new(tex.outputs['Color'],pigment.inputs[2])
    l.new(pigment.outputs[0],shade.inputs[1]);l.new(pigment.outputs[0],s.inputs['Base Color'])
    em=n.new('ShaderNodeEmission');l.new(shade.outputs[0],em.inputs['Color'])
    path=n.new('ShaderNodeLightPath');strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.78;l.new(path.outputs['Is Camera Ray'],strength.inputs[0])
    mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    base.data.materials.append(mat)
for face in base.data.polygons:face.material_index=0 if face.normal.z>.5 else 1
sc['stage']='painted';sc['projection']='Frozen rest-camera UV, incidence and source alpha; true weighted meshes; generated linen/bronze back fills'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'phalangite.blend'))
(M/'projection.json').write_text(json.dumps({'objects':projected,'source':str(A/'painting-source.png')},indent=2));print('PAINTED_MASTER_READY')
