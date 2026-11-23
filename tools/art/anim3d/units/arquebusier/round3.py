"""Finish full-depth costume joins and painted stone after rest calibration."""
import math
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)


def skin_object(obj, rig, weight_function):
    """Bake only the rigid attachment, retaining its exact visible rest surface."""
    world = obj.matrix_world.copy()
    transform = rig.matrix_world.inverted() @ world
    for vertex in obj.data.vertices:
        vertex.co = transform @ vertex.co
    obj.parent = rig
    obj.parent_type = 'OBJECT'
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = Matrix.Identity(4)
    groups = {}
    for vertex in obj.data.vertices:
        for bone, weight in weight_function(vertex.co).items():
            if weight > 0:
                if bone not in groups:
                    groups[bone] = obj.vertex_groups.new(name=bone)
                groups[bone].add([vertex.index], weight, 'REPLACE')
    modifier = obj.modifiers.new('Continuous tailored sleeve weights', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = True


def silhouette_finish():
    """Small measured screen corrections on full-depth rigid costume surfaces."""
    scene=bpy.context.scene;camera=scene.camera
    right=camera.matrix_world.to_quaternion() @ Vector((1,0,0))
    up=camera.matrix_world.to_quaternion() @ Vector((0,1,0))
    unit=camera.data.ortho_scale/256
    for obj in scene.objects:
        if obj.type!='MESH':continue
        helmet='morion' in obj.name or 'comb bright' in obj.name
        stocking=obj.name=='GEO-ivory stocking l'
        shoe='shoe' in obj.name and obj.parent_bone=='foot_l'
        if not (helmet or stocking or shoe):continue
        inv=obj.matrix_world.to_3x3().inverted()
        for vertex in obj.data.vertices:
            point=world_to_camera_view(scene,camera,obj.matrix_world @ vertex.co)
            x,y=point.x*256,(1-point.y)*256
            dx=dy=0
            if helmet:
                if 'brim' in obj.name or 'rolled brass lip' in obj.name:
                    tip=smooth((x-126)/12)
                    dx=-2*tip;dy=3+3*tip
                else:dx=-2.5*smooth((49-y)/20)
            if stocking:dx=-.35*max(0,x-140)*smooth((y-158)/12)
            if shoe:dx=-.20*max(0,x-145)
            vertex.co+=inv @ (right*(dx*unit)-up*(dy*unit))
        obj.data.update()


def finished_soles():
    """Flatten the leather contact surface and give each shoe an actual thin sole."""
    for side in ('l','r'):
        shoe=bpy.data.objects['GEO-latchet shoe '+side]
        world=shoe.matrix_world.copy();inv=world.inverted()
        coords=[world @ vertex.co for vertex in shoe.data.vertices]
        low,high=min(v.z for v in coords),max(v.z for v in coords)
        # Preserve the vamp and toe profile; only replace the round underside.
        for vertex,point in zip(shoe.data.vertices,coords):
            point.z=max(point.z,low+.012)
            vertex.co=inv @ point
        sole=shoe.copy();sole.data=shoe.data.copy()
        sole.name='GEO-shoe leather sole '+side
        bpy.context.scene.collection.objects.link(sole);sole.matrix_world=world
        sole['skip_painting_projection']=True
        for vertex,point in zip(sole.data.vertices,coords):
            point.z=low+.002+.010*(point.z-low)/(high-low)
            vertex.co=inv @ point
        material=shoe.data.materials[0].copy();material.name='MAT-scuffed sole '+side
        # Leather pigment is the original generated fill, without projected stone.
        sole.data.materials.clear();sole.data.materials.append(material)
        bevel=sole.modifiers.new('Rounded sole edge','BEVEL');bevel.width=.0015;bevel.segments=3
        shoe.data.update();sole.data.update()


def sleeve_joins(rig):
    for side in ('l', 'r'):
        upper = rig.data.bones['upperarm_'+side]
        lower = rig.data.bones['lowerarm_'+side]
        for name, bone in [('upperarm', upper), ('lowerarm', lower)]:
            obj = bpy.data.objects['GEO-slashed '+name+' '+side]
            def weights(co, bone=bone, name=name):
                t = (co-bone.head_local).dot(bone.tail_local-bone.head_local)/bone.length**2
                if name == 'upperarm':
                    chest = .35*(1-smooth(t/.32))
                    forearm = .5*smooth((t-.65)/.35)
                    return {'spine_03': chest, 'upperarm_'+side: 1-chest-forearm,
                            'lowerarm_'+side: forearm}
                upper_weight = .5*(1-smooth(t/.35))
                return {'upperarm_'+side: upper_weight, 'lowerarm_'+side: 1-upper_weight}
            skin_object(obj, rig, weights)
        # Thick folded lining crosses the elbow; surfaces overlap inside sleeves.
        a = upper.tail_local.lerp(upper.head_local, .24)
        b = lower.head_local.lerp(lower.tail_local, .24)
        axis = (b-a).normalized()
        u = axis.cross(Vector((0, 1, 0))).normalized()
        v = axis.cross(u).normalized()
        vertices, faces = [], []
        for j in range(17):
            t = j/16
            center = a.lerp(b, t)
            radius = .063 + .004*math.sin(t*math.pi*6)
            for k in range(48):
                angle = k*math.tau/48
                fold = 1+.04*math.cos(8*angle+t*3)
                vertices.append(center+(u*math.cos(angle)+v*math.sin(angle))*radius*fold)
        for j in range(16):
            for k in range(48):
                i=j*48+k; n=j*48+(k+1)%48
                faces.append((i,n,n+48,i+48))
        mesh=bpy.data.meshes.new('Continuous elbow lining '+side)
        mesh.from_pydata(vertices,[],faces);mesh.update()
        obj=bpy.data.objects.new('GEO-folded elbow lining '+side,mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent=rig;obj.matrix_basis=Matrix.Identity(4)
        obj.data.materials.append(bpy.data.objects['GEO-red knee garter '+side].data.materials[0])
        upper_group=obj.vertex_groups.new(name='upperarm_'+side)
        lower_group=obj.vertex_groups.new(name='lowerarm_'+side)
        for j in range(17):
            t=smooth(j/16);indices=list(range(j*48,(j+1)*48))
            upper_group.add(indices,1-t,'REPLACE');lower_group.add(indices,t,'REPLACE')
        arm=obj.modifiers.new('Elbow cloth deformation','ARMATURE');arm.object=rig;arm.use_deform_preserve_volume=True
        solid=obj.modifiers.new('Woven lining thickness','SOLIDIFY');solid.thickness=.004
        for polygon in mesh.polygons:polygon.use_smooth=True


def hidden_pigment():
    """Keep newly exposed painted cloth/leather from falling into black seams.

    The original generated fills are reused, with live normal and contact shading.
    The main painting projection is layered on this later, without altering UVs.
    """
    materials=set()
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH' and any(word in obj.name for word in ('slashed','lining','stocking','knee','shoe')):
            materials.update(slot.material for slot in obj.material_slots if slot.material)
    for material in materials:
        nodes=material.node_tree.nodes;links=material.node_tree.links
        p=nodes.get('Principled BSDF')
        if p is None:continue
        # Preserve the physical BSDF and weave. Camera-only painted fill has real AO.
        color=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
        ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.065
        if color:links.new(color,ao.inputs['Color'])
        else:ao.inputs['Color'].default_value=p.inputs['Base Color'].default_value
        emission=nodes.new('ShaderNodeEmission');emission.name='Hidden painted fill';links.new(ao.outputs['Color'],emission.inputs['Color']);emission.inputs['Strength'].default_value=.8
        path=nodes.new('ShaderNodeLightPath');weight=nodes.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.35;links.new(path.outputs['Is Camera Ray'],weight.inputs[0])
        mix=nodes.new('ShaderNodeMixShader');mix.name='Hidden fill surface';links.new(weight.outputs[0],mix.inputs[0]);links.new(p.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])


def stone_edge_guard(material):
    """Blend generated edge pigment over cream; keep geometry fully opaque."""
    nodes=material.node_tree.nodes;links=material.node_tree.links
    tex=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image and n.image.name.startswith('stone-fill-source'))
    targets=[link.to_socket for link in list(tex.outputs['Color'].links)]
    coverage=nodes.new('ShaderNodeMapRange');coverage.clamp=True
    coverage.inputs['From Min'].default_value=.25
    coverage.inputs['From Max'].default_value=.95
    links.new(tex.outputs['Alpha'],coverage.inputs['Value'])
    pigment=nodes.new('ShaderNodeMixRGB');pigment.name='Opaque stone edge pigment'
    pigment.inputs[1].default_value=(.90,.72,.48,1)
    links.new(coverage.outputs[0],pigment.inputs[0]);links.new(tex.outputs['Color'],pigment.inputs[2])
    for target in targets:links.new(pigment.outputs[0],target)


def stone_pigment(root):
    scene=bpy.context.scene;base=bpy.data.objects['GEO-stationary cream base']
    bpy.context.view_layer.update()
    # Apply rounded geometry before computing UVs, including interior top samples.
    bpy.context.view_layer.objects.active=base
    for modifier in list(base.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    import bmesh
    bm=bmesh.new();bm.from_mesh(base.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(base.data);bm.free()
    coords=[world_to_camera_view(scene,scene.camera,base.matrix_world @ vertex.co) for vertex in base.data.vertices]
    xs=[v.x for v in coords];ys=[v.y for v in coords]
    # Clean generated plate occupies these alpha bounds on its original generated canvas.
    import json
    bounds=json.loads((root/'assets/arquebusier/stone-fill-bounds.json').read_text())
    left,top,right,bottom=bounds['bounds'];width,height=bounds['size']
    uv=base.data.uv_layers.new(name='Clean painted stone')
    for loop in base.data.loops:
        point=coords[loop.vertex_index]
        x=(point.x-min(xs))/(max(xs)-min(xs));y=(point.y-min(ys))/(max(ys)-min(ys))
        uv.data[loop.index].uv=((left+(right-left)*(.006+.988*x))/width,1-(bottom-(bottom-top)*(.006+.988*y))/height)
    material=base.data.materials[0];nodes=material.node_tree.nodes;links=material.node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(root/'assets/arquebusier/stone-fill-source.png'));tex.extension='EXTEND'
    mapping=nodes.new('ShaderNodeUVMap');mapping.uv_map=uv.name;links.new(mapping.outputs[0],tex.inputs[0])
    # Texture alpha never cuts geometry or makes stone transparent.
    p=nodes.get('Principled BSDF');links.new(tex.outputs['Color'],p.inputs['Base Color'])
    ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09;links.new(tex.outputs['Color'],ao.inputs['Color'])
    emission=nodes.new('ShaderNodeEmission');links.new(ao.outputs['Color'],emission.inputs['Color'])
    path=nodes.new('ShaderNodeLightPath');weight=nodes.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.94;links.new(path.outputs['Is Camera Ray'],weight.inputs[0])
    mix=nodes.new('ShaderNodeMixShader');links.new(weight.outputs[0],mix.inputs[0]);links.new(p.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
    stone_edge_guard(material)
    tex.image.pack()


def finish(rig, root):
    silhouette_finish()
    finished_soles()
    sleeve_joins(rig)
    hidden_pigment()
    stone_pigment(root)
    bpy.context.view_layer.update()
