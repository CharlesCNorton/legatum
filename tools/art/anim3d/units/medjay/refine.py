"""Full-depth finished calf registration and stone pigment; no alpha-cut geometry."""
from common import *
from bpy_extras.object_utils import world_to_camera_view
import numpy as np


def refine(sc):
    body=bpy.data.objects['Medjay MPFB anatomical body'];rig=bpy.data.objects['Medjay MPFB game_engine']
    masks=[(m,m.show_viewport) for m in body.modifiers if m.type=='MASK']
    for m,_ in masks:m.show_viewport=False
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    assert len(me.vertices)==len(body.data.vertices)
    world=[ev.matrix_world @ v.co for v in me.vertices];ev.to_mesh_clear()
    xy=np.array([(q.x*256,(1-q.y)*256) for q in [world_to_camera_view(sc,sc.camera,w) for w in world]])
    image=bpy.data.images.load(str(Path('app/src/assets/units/medjay-256.png').resolve()),check_existing=True)
    pix=np.array(image.pixels[:]).reshape(256,256,4)[::-1]
    visible=np.array([any(g.group==body.vertex_groups['body'].index and g.weight>.5 for g in v.groups) for v in body.data.vertices])
    right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0));unit=sc.camera.data.ortho_scale/256
    transforms={p.name:p.matrix @ p.bone.matrix_local.inverted() for p in rig.pose.bones}
    for lo,hi in [(108,132),(133,160)]:
        rows=np.arange(147,209);old=[];new=[]
        for y in rows:
            side=(xy[:,0]<132) if lo==108 else (xy[:,0]>=132)
            chosen=xy[visible&side&(xy[:,0]>lo-6)&(xy[:,0]<hi+6)&(abs(xy[:,1]-y)<1.5)]
            src=np.flatnonzero(pix[y,lo:hi,3]>.5)+lo
            runs=np.split(src,np.flatnonzero(np.diff(src)>1)+1)
            src=min(runs,key=lambda run:abs(float(np.mean(run))-(121 if lo==108 else 145)))
            assert len(chosen) and len(src),(y,lo)
            old.append([chosen[:,0].min(),chosen[:,0].max()]);new.append([src.min()+.1,src.max()+.9])
        old=np.array(old);new=np.array(new)
        # Smooth row envelopes, retaining continuous native depth and all weights.
        for arr in [old,new]:
            for j in range(2):arr[:,j]=np.convolve(np.pad(arr[:,j],(2,2),mode='edge'),np.array([1,2,3,2,1])/9,mode='valid')
        for v,w,(x,y) in zip(body.data.vertices,world,xy):
            if not visible[v.index] or not (lo-6<x<hi+6 and 143<y<212):continue
            # Keep each leg on its own side of the inter-leg gap.
            if (lo==108 and x>=132) or (lo==133 and x<132):continue
            a,b=[np.interp(y,rows,old[:,j]) for j in range(2)];c,d=[np.interp(y,rows,new[:,j]) for j in range(2)]
            target=c+(x-a)*(d-c)/max(1,b-a)
            fade=min(1,max(0,(y-143)/5),max(0,(212-y)/4));dx=(target-x)*fade
            skin=Matrix(((0.,)*4,)*4);total=0
            for g in v.groups:
                name=body.vertex_groups[g.group].name
                if name in transforms:skin+=transforms[name]*g.weight;total+=g.weight
            if total:
                skin*=1/total
                v.co+=skin.to_3x3().inverted_safe() @ (body.matrix_world.inverted().to_3x3() @ (right*(dx*unit)))
    # Remove the trapezius wedge above the painted shoulders. Fit the connected
    # neck/shoulder contour, separate from headband, shield and weapon geometry.
    rows=np.arange(43,69);old=[];new=[]
    for y in rows:
        selected=xy[visible&(xy[:,0]>100)&(xy[:,0]<157)&(abs(xy[:,1]-y)<1.5)]
        src=np.flatnonzero(pix[y,100:157,3]>.5)+100
        runs=np.split(src,np.flatnonzero(np.diff(src)>1)+1)
        src=max(runs,key=len)
        old.append([selected[:,0].min(),selected[:,0].max()]);new.append([src.min()+.1,src.max()+.9])
    old=np.array(old);new=np.array(new)
    for arr in [old,new]:
        for j in range(2):arr[:,j]=np.convolve(np.pad(arr[:,j],(2,2),mode='edge'),np.array([1,2,3,2,1])/9,mode='valid')
    for v,w,(x,y) in zip(body.data.vertices,world,xy):
        if not visible[v.index] or not (100<x<157 and 43<y<69):continue
        a,b=[np.interp(y,rows,old[:,j]) for j in range(2)];c,d=[np.interp(y,rows,new[:,j]) for j in range(2)]
        fade=min(1,(y-43)/4,(69-y)/6,(x-100)/5,(157-x)/5)
        dx=(c+(x-a)*(d-c)/max(1,b-a)-x)*fade
        skin=Matrix(((0.,)*4,)*4);total=0
        for g in v.groups:
            name=body.vertex_groups[g.group].name
            if name in transforms:skin+=transforms[name]*g.weight;total+=g.weight
        if total:
            skin*=1/total
            v.co+=skin.to_3x3().inverted_safe() @ (body.matrix_world.inverted().to_3x3() @ (right*(dx*unit)))
    body.data.update()
    for m,show in masks:m.show_viewport=show
    sc['calf_registration']='continuous finished-surface row envelopes, full native depth and weights'


def stone_finish(sc):
    ob=bpy.data.objects['Stationary warm cream stone']
    # Lower the underside while preserving the support plane at z=.085.
    for v in ob.data.vertices:v.co.z=.0325-(.0325-v.co.z)*(.080/.065)
    ob.data.update();bpy.context.view_layer.update()
    mat=ob.active_material;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n['Principled BSDF'];out=n['Material Output']
    # Real world-space grain, surface orientation, and live contact occlusion.
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=170;noise.inputs['Detail'].default_value=2
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.75,.55,.31,1);ramp.color_ramp.elements[1].color=(1,.82,.57,1);l.new(noise.outputs['Fac'],ramp.inputs[0])
    geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Normal'],sep.inputs[0])
    top=n.new('ShaderNodeMapRange');top.inputs['From Min'].default_value=-.2;top.inputs['From Max'].default_value=.8;top.inputs['To Min'].default_value=.79;top.inputs['To Max'].default_value=1;l.new(sep.outputs['Z'],top.inputs['Value'])
    tone=n.new('ShaderNodeMixRGB');tone.blend_type='MULTIPLY';tone.inputs[0].default_value=1;l.new(ramp.outputs[0],tone.inputs[1]);l.new(top.outputs[0],tone.inputs[2])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.11
    contact=n.new('ShaderNodeMixRGB');contact.blend_type='MULTIPLY';contact.inputs[0].default_value=.65;l.new(tone.outputs[0],contact.inputs[1]);l.new(ao.outputs['Color'],contact.inputs[2])
    l.new(contact.outputs[0],s.inputs['Base Color']);s.inputs['Emission Strength'].default_value=0
    paint=n.new('ShaderNodeBsdfPrincipled');paint.inputs['Base Color'].default_value=(0,0,0,1);paint.inputs['Specular IOR Level'].default_value=0;paint.inputs['Emission Strength'].default_value=1;l.new(contact.outputs[0],paint.inputs['Emission Color'])
    path=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.72;l.new(path.outputs['Is Camera Ray'],weight.inputs[0])
    mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(paint.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])

    # The lower stone is fully visible in the reference; no painted feet/shadows
    # are copied. The upper support surface keeps live AO and procedural grain.
    uv=ob.data.uv_layers.new(name='Stone pigment UV')
    for loop in ob.data.loops:
        q=world_to_camera_view(sc,sc.camera,ob.matrix_world @ ob.data.vertices[loop.vertex_index].co)
        uv.data[loop.index].uv=(q.x,q.y)
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True);tex.extension='CLIP'
    coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;l.new(coord.outputs[0],tex.inputs['Vector'])
    # Evaluate exclusion per pixel: a corner attribute interpolates across the
    # top n-gon and can leak painted toes into the support surface.
    split=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs[0],split.inputs[0])
    gate=n.new('ShaderNodeMapRange');gate.clamp=True;gate.inputs['From Min'].default_value=1-220/256;gate.inputs['From Max'].default_value=1-224/256;gate.inputs['To Min'].default_value=0;gate.inputs['To Max'].default_value=1;l.new(split.outputs['Y'],gate.inputs['Value'])
    factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(gate.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
    camera=n.new('ShaderNodeMath');camera.operation='MULTIPLY';l.new(factor.outputs[0],camera.inputs[0]);l.new(path.outputs['Is Camera Ray'],camera.inputs[1])
    pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0;pigment.inputs['Emission Strength'].default_value=1;l.new(tex.outputs['Color'],pigment.inputs['Emission Color'])
    final=n.new('ShaderNodeMixShader');l.new(camera.outputs[0],final.inputs[0]);l.new(mix.outputs[0],final.inputs[1]);l.new(pigment.outputs[0],final.inputs[2]);l.new(final.outputs[0],out.inputs['Surface'])
