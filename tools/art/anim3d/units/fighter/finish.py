"""Actual AO / Pointiness maps plus licensed painted hidden-surface fill."""
import bpy,os,json
from mathutils import Vector
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/fighter';O=M/'textures/baked';O.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'fighter.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=6
fill=bpy.data.images.load(str(R/'assets/fighter/painted-fill.png'));fill.pack()
records=[]
for o in [o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('FX-','BASE','DISPLAY','Exhaust cavity','Canopy •','Propeller blade'))]:
    n=o.data.materials[0].node_tree.nodes;l=o.data.materials[0].node_tree.links
    blend=n['Frozen source pigment'];old=blend.inputs[1].links[0].from_socket
    tex=n.new('ShaderNodeTexImage');tex.image=fill;tex.projection='BOX';tex.projection_blend=.3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
    # Generated olive texture's brushwork modulates existing material pigment,
    # so silver/charcoal remain their proper colour on unobserved faces.
    bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs[0],bw.inputs[0]);tone=n.new('ShaderNodeMapRange');tone.inputs['From Min'].default_value=.04;tone.inputs['From Max'].default_value=.4;tone.inputs['To Min'].default_value=.65;tone.inputs['To Max'].default_value=1.15;l.new(bw.outputs[0],tone.inputs[0])
    mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.7;l.new(old,mul.inputs[1]);l.new(tone.outputs[0],mul.inputs[2]);l.new(mul.outputs[0],blend.inputs[1])
for idx,name in enumerate(['Fuselage • elliptical riveted monocoque','Port wing • thick tapered airfoil','Starboard wing • thick tapered airfoil']):
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.0,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    mat=o.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');old=out.inputs[0].links[0].from_socket;maps={}
    for mode in ('AO','curvature'):
        im=bpy.data.images.new(f'fighter-{idx}-{mode}',512,512,alpha=False);im.colorspace_settings.name='Non-Color';t=n.new('ShaderNodeTexImage');t.image=im;n.active=t
        if mode=='curvature':
            geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        if mode=='curvature':l.new(old,out.inputs[0]);n.remove(em);n.remove(geo)
        im.filepath_raw=str(O/f'{idx}-{mode}.png');im.file_format='PNG';im.save();im.pack();maps[mode]=t
        coords=n.new('ShaderNodeUVMap');coords.uv_map='BakeUV';l.new(coords.outputs[0],t.inputs['Vector'])
    projection=n['Frozen source pigment'];base=projection.inputs[1].links[0].from_socket
    grime=n.new('ShaderNodeMixRGB');grime.blend_type='MULTIPLY';grime.inputs[0].default_value=.55;l.new(base,grime.inputs[1]);l.new(maps['AO'].outputs[0],grime.inputs[2])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.49;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.58;ramp.color_ramp.elements[1].color=(.35,.35,.35,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0])
    wear=n.new('ShaderNodeMixRGB');wear.inputs[2].default_value=(.65,.61,.48,1);l.new(ramp.outputs[0],wear.inputs[0]);l.new(grime.outputs[0],wear.inputs[1]);l.new(wear.outputs[0],projection.inputs[1])
    records.append({'object':name,'resolution':512,'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'method':'Cycles AO / Geometry Pointiness emission; hidden fill cavity grime and edge polish'})
# Locally fill occluded wing paint and restore lower-disc grain without freezing
# a pedestal shadow into the live-lit upper stone surface.
import sys
sys.path.insert(0,str(Path(__file__).parent))
from surfaces import finish_surfaces
finish_surfaces(R/'assets/fighter')
# Physical unseen surfaces retain the generated fill and baked AO/curvature.
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for mat in o.data.materials:
        n=mat.node_tree.nodes;l=mat.node_tree.links
        if 'Frozen source pigment' in n:
            pigment=n['Frozen source pigment'];l.new(pigment.inputs[1].links[0].from_socket,n['Principled BSDF'].inputs['Base Color'])
bpy.ops.wm.save_as_mainfile(filepath=str(M/'fighter.blend'));(O/'manifest.json').write_text(json.dumps(records,indent=2))
