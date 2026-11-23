"""Round-two full-volume tailoring. Pigment never changes geometry opacity."""
import math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def sleeve(side, rig, material, mesh, solid, bind_weights, trousers=False):
    """One connected thick sleeve with overlapping shoulder and blended elbow."""
    upper, lower = ('thigh_'+side, 'calf_'+side) if trousers else ('upperarm_'+side, 'lowerarm_'+side)
    a = rig.matrix_world @ rig.pose.bones[upper].head
    b = rig.matrix_world @ rig.pose.bones[lower].head
    c = rig.matrix_world @ rig.pose.bones[lower].tail
    if trousers:c=b.lerp(c,.69)
    vertices, faces, weights = [], [], []
    rings, segments = 32, 40
    for j in range(rings+1):
        t = j/rings
        # Extend under jacket and cuff so the exterior never opens at the joint.
        if t <= .5:
            center = a.lerp(b, t*2)
            tangent = (b-a).normalized()
        else:
            center = b.lerp(c, (t-.5)*2)
            tangent = (c-b).normalized()
        if .40 < t < .60:
            tangent = (b-a).normalized().lerp((c-b).normalized(), (t-.4)/.2).normalized()
        u = tangent.cross(Vector((0,1,0))).normalized()
        v = tangent.cross(u).normalized()
        radius = (.095*(1-t)+.062*t) if trousers else (.076*(1-t)+.050*t)
        radius += .009*math.sin(math.pi*t)
        blend = max(0, min(1, (t-.37)/.26))
        blend = blend*blend*(3-2*blend)
        for k in range(segments):
            ang = 2*math.pi*k/segments
            fold = .004*math.sin(ang*7+t*5)*math.sin(math.pi*t)
            fold += .004*math.sin(t*math.pi*13+ang*2)*math.exp(-((t-.5)/.22)**2)
            vertices.append(center+(u*math.cos(ang)+v*math.sin(ang))*(radius+fold))
            weights.append({upper:1-blend, lower:blend})
    for j in range(rings):
        for k in range(segments):
            i=j*segments+k; n=j*segments+(k+1)%segments
            faces.append((i,n,n+segments,i+segments))
    obj=solid(mesh(('continuous folded trousers ' if trousers else 'continuous folded sleeve ')+side, vertices, faces, material), .006)
    # bind_weights visits the original vertices in order.
    it=iter(weights)
    bind_weights(obj, lambda _: next(it))
    return obj


def residual(obj, world, sc, groups):
    """Measured rest-camera displacement, with depth retained for every vertex."""
    cam=sc.camera;uv=world_to_camera_view(sc,cam,world)
    x,y=uv.x*256,(1-uv.y)*256
    dx=dy=0.;name=obj.name
    if 'anatomy' in name and groups:
        bone=max(groups,key=groups.get)
        if bone.startswith(('upperarm','lowerarm')):name='sleeve '+bone[-1]
        elif bone.startswith(('hand','index','middle','ring','pinky','thumb')) and bone.endswith('_l'):
            dx=-2;dy=3
    # Shoulder and elbow volumes were wider than the painted coat, especially
    # on the supporting side. Fit the same complete volume on its hidden side.
    if name.endswith('sleeve l'):
        dx=-6+max(0,min(1,(y-100)/25))*3
        dx+=(151-x)*.13
        dy=max(0,1-abs(y-108)/20)*5
    elif name.endswith('cuff l'):
        dx=-3;dy=2
    elif name.endswith('sleeve r') or name.endswith('cuff r'):
        dy=max(0,min(1,(60-y)/32))*7
        dx=(94-x)*max(0,min(1,(68-y)/38))*.16
    if 'helmet' in name and 'chin' not in name:
        dx=(128-x)*.16
        # Narrow the brim and tip it up on the face side, as in the source.
        if 'brim' in name or 'rim' in name:dy=-2
    if obj.parent and obj.parent.name=='CTRL-rifle':
        # Painted stock leans slightly right towards the muzzle.
        dx=(y-166)*-.032
    if name.split('.')[0].endswith(('boot l','sole l','lace l')):
        dx=(x-139)*.38
        dy=-.8
    if 'canvas backpack' in name:
        dx=(122-x)*.32-2;dy=2.5
    right=cam.rotation_euler.to_matrix()@Vector((1,0,0))
    up=cam.rotation_euler.to_matrix()@Vector((0,1,0))
    unit=cam.data.ortho_scale/256
    delta=right*dx*unit-up*dy*unit
    if world.z<.25:
        forward=Vector((0,1,0))
        delta=right*dx*unit+forward*(delta.dot(up)/up.dot(forward))
    return delta


def stone_finish(sc):
    """Live AO + pigment grain on the real disc; no painted stationary feet."""
    base=bpy.data.objects['GEO-stationary cream base']
    # The previous flat dark rim was 8px deep; source is a shallow cream edge.
    for v in base.data.vertices:
        v.co.z *= .75
    base.location.z += .075/2*.25  # preserve the top contact plane
    base.location.y -= .08
    for slot in base.material_slots:
        mat=slot.material;n=mat.node_tree.nodes;l=mat.node_tree.links
        p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord')
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95
        l.new(tc.outputs['Generated'],noise.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB')
        # Linear cream pigments; broad light variation is physically shaded.
        if 'rim' in mat.name:
            colors=((.62,.42,.20,1),(.82,.64,.36,1))
        else:
            colors=((.77,.57,.31,1),(.91,.74,.48,1))
        for elem,col in zip(ramp.color_ramp.elements,colors):elem.color=col
        l.new(noise.outputs['Fac'],ramp.inputs[0])
        ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.10
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.32
        l.new(ramp.outputs[0],mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
    # Rim on fabric should separate a form without painting it blue.
    light=bpy.data.objects['LGT-rim'];light.data.energy=65;light.data.color=(.89,.93,1)


def stone_pigment(sc, painting):
    base=bpy.data.objects['GEO-stationary cream base']
    uv=base.data.uv_layers.new(name='Stone painting')
    for loop in base.data.loops:
        p=world_to_camera_view(sc,sc.camera,base.matrix_world@base.data.vertices[loop.vertex_index].co)
        uv.data[loop.index].uv=(p.x,p.y)
    for slot in base.material_slots:
        n=slot.material.node_tree.nodes;l=slot.material.node_tree.links
        p=n.get('Principled BSDF');out=n.get('Material Output')
        tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name
        tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
        sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs[0],sep.inputs[0])
        mask=n.new('ShaderNodeMapRange');mask.clamp=True
        mask.inputs['From Min'].default_value=1-228/256;mask.inputs['From Max'].default_value=1-226/256
        mask.inputs['To Min'].default_value=1;mask.inputs['To Max'].default_value=0
        l.new(sep.outputs['Y'],mask.inputs['Value'])
        mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(mask.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
        # Outside the feet-free lower painting, retain grain with live AO.
        pigment=n.new('ShaderNodeMixRGB');l.new(mul.outputs[0],pigment.inputs[0]);l.new(p.inputs['Base Color'].links[0].from_socket,pigment.inputs[1]);l.new(tex.outputs['Color'],pigment.inputs[2])
        em=n.new('ShaderNodeEmission');l.new(pigment.outputs[0],em.inputs[0])
        camera=n.new('ShaderNodeLightPath');strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.85;l.new(camera.outputs['Is Camera Ray'],strength.inputs[0])
        mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
