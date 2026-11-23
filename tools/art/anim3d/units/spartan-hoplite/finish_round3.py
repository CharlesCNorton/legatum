"""Full-depth lower-body registration and stone grain for driver round three.

Called before frozen UV projection; preserves MPFB topology, skin weights and
source motion rotations. Screen constraints edit geometry, never a raster card.
"""
import bpy, math
from mathutils import Vector


def lerp_rows(y, rows):
    if y <= rows[0][0]:
        return rows[0][1]
    for (a, x), (b, z) in zip(rows, rows[1:]):
        if y <= b:
            return x + (z-x)*(y-a)/(b-a)
    return rows[-1][1]


def fit(sc, body, skin, pixel, sculpt, view):
    for ob in list(sc.objects):
        if ob.type != 'MESH' or ob.hide_render:
            continue
        lower = ob == body or ob.name.startswith(('Contoured greave', 'Greave chased', 'Leather sandal', 'Sandal'))
        if not lower:
            continue
        for v in ob.data.vertices:
            matrix = skin(ob, v)
            co = matrix @ v.co
            p = pixel(ob, co)
            if p.y < 140:
                continue
            target = p.copy()
            if p.x < 128:
                center = lerp_rows(p.y, [(140,115),(172,105),(215,102),(226,96)])
                desired = lerp_rows(p.y, [(140,115),(172,112),(215,106),(226,98)])
                dy = lerp_rows(p.y, [(140,0),(172,-10),(215,-7),(226,-7)])
            else:
                center = lerp_rows(p.y, [(140,141),(174,149),(217,160),(229,156)])
                desired = lerp_rows(p.y, [(140,141),(174,143),(217,153),(229,156)])
                dy = lerp_rows(p.y, [(140,0),(174,-9),(217,-5),(229,-5)])
            width = 1 + .22*max(0,min(1,(p.y-207)/10))
            target.x = desired + (p.x-center)*width
            target.y += dy
            fitted = sculpt(ob, co, target)
            # Keep soles on their physical ground plane. Translating along a
            # camera ray changes depth without changing projected registration.
            ground_weight = max(0, min(1, (p.y-199)/15))
            old_world = ob.matrix_world @ co
            new_world = ob.matrix_world @ fitted
            new_world += view * ((old_world.z-new_world.z)/view.z*ground_weight)
            v.co = matrix.inverted_safe() @ (ob.matrix_world.inverted() @ new_world)
        ob.data.update()
    # The source has a long asymmetrical drape, not a short level curtain.
    cloak = bpy.data.objects['Cloak • simulated wool']
    for v in cloak.data.vertices:
        p = pixel(cloak, v.co)
        t = max(0, min(1, (p.y-105)/80))
        drop = lerp_rows(p.x, [(94,-17),(112,-6),(135,6),(151,9),(170,-2)])
        target = p + Vector((0, drop*t*t))
        v.co = sculpt(cloak, v.co, target)
    for polygon in cloak.data.polygons:
        polygon.flip()
    cloak.data.update()
    linen_underlayer(sc, pixel, sculpt)


def spear(sc, weapons, pixel, sculpt, view):
    # Register the complete solid weapon along one straight 3D axis; retain its
    # cross section and all attachments. The butt stays at the stone plane.
    shaft=bpy.data.objects['Ash dory shaft']
    points=shaft.data.splines[0].points
    start=shaft.matrix_world @ Vector(points[0].co[:3])
    end=shaft.matrix_world @ Vector(points[-1].co[:3])
    axis=(end-start).normalized()
    samples=[]
    for ob in weapons:
        vertices=ob.data.vertices if ob.type=='MESH' else [p for sp in ob.data.splines for p in sp.points]
        for v in vertices:samples.append(ob.matrix_world @ Vector(v.co[:3]))
    lo=min((p-start).dot(axis) for p in samples);hi=max((p-start).dot(axis) for p in samples)
    bottom=start+axis*lo;top=start+axis*hi
    def placed(world,target,ground=False):
        local=shaft.matrix_world.inverted() @ world
        fitted=shaft.matrix_world @ sculpt(shaft,local,Vector(target))
        if ground:fitted+=view*((.10-fitted.z)/view.z)
        return fitted
    new_bottom=placed(bottom,(91,217),True);new_top=placed(top,(83,14))
    rig=bpy.data.objects['Spearman • MPFB game_engine']
    hand=rig.matrix_world @ rig.pose.bones['hand_r'].head
    hand_pixel=pixel(shaft,shaft.matrix_world.inverted() @ hand)
    fraction=(217-hand_pixel.y)/(217-14)
    line=new_bottom+(new_top-new_bottom)*fraction
    new_top+=view*((hand-line).dot(view)/fraction)
    new_axis=(new_top-new_bottom).normalized();rotation=axis.rotation_difference(new_axis)
    for ob in weapons:
        vertices=ob.data.vertices if ob.type=='MESH' else [p for sp in ob.data.splines for p in sp.points]
        for v in vertices:
            world=ob.matrix_world @ Vector(v.co[:3]);along=(world-bottom).dot(axis)
            offset=world-bottom-axis*along
            fitted=new_bottom+(new_top-new_bottom)*(along/(hi-lo))+rotation @ offset
            local=ob.matrix_world.inverted() @ fitted
            v.co=local if ob.type=='MESH' else (*local,1)
        if ob.type=='MESH':ob.data.update()


def stone_grain():
    """Visible pigment grain plus live AO; no feet or baked cast shadows."""
    for name in ['Cream limestone', 'Cream limestone darker rim']:
        mat = bpy.data.materials[name]
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = nodes.get('Principled BSDF')
        color = shader.inputs['Base Color'].default_value[:]
        coord = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 115
        noise.inputs['Detail'].default_value = 2.5
        links.new(coord.outputs['Generated'], noise.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .2
        ramp.color_ramp.elements[0].color = tuple(c*.73 for c in color[:3])+(1,)
        ramp.color_ramp.elements[1].position = .8
        ramp.color_ramp.elements[1].color = tuple(min(1,c*1.10) for c in color[:3])+(1,)
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        ao = nodes.new('ShaderNodeAmbientOcclusion')
        ao.inputs['Distance'].default_value = .10
        mix = nodes.new('ShaderNodeMixRGB');mix.blend_type = 'MULTIPLY';mix.inputs[0].default_value = .48
        links.new(ramp.outputs[0], mix.inputs[1]);links.new(ao.outputs['Color'], mix.inputs[2])
        links.new(mix.outputs[0], shader.inputs['Base Color'])
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED' and node != shader:
                links.new(mix.outputs[0], node.inputs['Emission Color'])


def linen_underlayer(sc, pixel, sculpt):
    # Separate short armour tabs sit over a continuous folded linen tunic.
    for ob in list(sc.objects):
        if ob.type == 'MESH' and ob.name.startswith(('Linen pteruges', 'Pteruges')):
            for vertex in ob.data.vertices:
                p = pixel(ob, vertex.co)
                if p.y > 122:
                    vertex.co = sculpt(ob, vertex.co, Vector((p.x,122+(p.y-122)*.66)))
            ob.data.update()
    vertices, faces = [], []
    for j in range(9):
        t=j/8
        for i in range(96):
            a=math.tau*i/96
            fold=.008*math.cos(a*16)*t
            vertices.append(((.178+.070*t+fold)*math.sin(a),-(.13+.047*t+fold)*math.cos(a),1.12-.255*t+.008*math.cos(a*8)*t))
    for j in range(8):
        for i in range(96):
            a=j*96+i;b=j*96+(i+1)%96
            faces.append((a,b,b+96,a+96))
    mesh=bpy.data.meshes.new('Folded linen tunic volume');mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new('Linen pteruges underlayer',mesh);sc.collection.objects.link(ob)
    mesh.materials.append(bpy.data.materials['Warm ivory linen'])
    for p in mesh.polygons:p.use_smooth=True
    for kind, name in [('SOLIDIFY','Hem thickness'),('BEVEL','Soft hem')]:
        mod=ob.modifiers.new(name,kind)
        if kind=='SOLIDIFY':mod.thickness=.005
        else:mod.width=.002;mod.segments=2
        bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.update();world=ob.matrix_world.copy()
    ob.parent=bpy.data.objects['Spearman • MPFB game_engine'];ob.parent_type='BONE';ob.parent_bone='pelvis'
    bpy.context.view_layer.update();ob.matrix_world=world;ob['attachment']='pelvis'


def fills(root):
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        name=ob.name
        kind='skin' if name.startswith('MPFB anatomical') else 'cloth' if name.startswith(('Cloak •','Crimson shoulder')) else 'leather' if name.startswith(('Leather sandal','Sandal')) else None
        if not kind:continue
        for idx,old in enumerate(list(ob.data.materials)):
            if not old or not old.use_nodes:continue
            mat=old.copy();mat.name=name+' generated backfill';ob.data.materials[idx]=mat
            nodes,links=mat.node_tree.nodes,mat.node_tree.links;s=nodes.get('Principled BSDF')
            if not s:continue
            tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(root/f'assets/spartan-hoplite/fill-{kind}.png'),check_existing=True)
            tex.projection='BOX';tex.projection_blend=.3
            tc=nodes.new('ShaderNodeTexCoord');links.new(tc.outputs['Generated'],tex.inputs['Vector'])
            hue=nodes.new('ShaderNodeHueSaturation');hue.inputs['Saturation'].default_value=.65 if kind=='skin' else .9
            hue.inputs['Value'].default_value=.7 if kind=='skin' else .8
            links.new(tex.outputs[0],hue.inputs['Color'])
            ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55
            links.new(hue.outputs[0],mix.inputs[1]);links.new(ao.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],s.inputs['Base Color'])
            s.inputs['Metallic'].default_value=0;s.inputs['Roughness'].default_value=.8


def skin_sandals(sc, body, skin):
    """Transfer actual anatomical foot/toe weights to soles and straps.

Rigid foot parenting left toes bending through the sandals during roll. Preserve
finished rest geometry exactly, then use the same MPFB skinning as the foot.
"""
    from mathutils import Matrix
    from mathutils.kdtree import KDTree
    rig=bpy.data.objects['Spearman • MPFB game_engine']
    matrices={p.name:p.matrix @ p.bone.matrix_local.inverted() for p in rig.pose.bones}
    for side in ['l','r']:
        bones=['foot_'+side,'ball_'+side]
        samples=[]
        for v in body.data.vertices:
            weights={body.vertex_groups[g.group].name:g.weight for g in v.groups if body.vertex_groups[g.group].name in bones}
            total=sum(weights.values())
            if total<.6:continue
            world=body.matrix_world @ (skin(body,v) @ v.co)
            samples.append((world,{n:w/total for n,w in weights.items()}))
        tree=KDTree(len(samples))
        for i,(world,_) in enumerate(samples):tree.insert(world,i)
        tree.balance()
        for ob in list(sc.objects):
            if ob.type!='MESH' or not ob.name.startswith(('Leather sandal sole '+side,'Sandal strap '+side)):continue
            worlds=[ob.matrix_world @ v.co for v in ob.data.vertices]
            ob.parent=rig;ob.parent_type='OBJECT';ob.parent_bone='';ob.matrix_world=rig.matrix_world.copy()
            groups={n:ob.vertex_groups.new(name=n) for n in bones}
            for v,world in zip(ob.data.vertices,worlds):
                entries=tree.find_n(world,4);weights={n:0.0 for n in bones}
                denominator=sum(1/max(.004,d)**2 for _,_,d in entries)
                for _,index,distance in entries:
                    factor=(1/max(.004,distance)**2)/denominator
                    for n,w in samples[index][1].items():weights[n]+=w*factor
                transform=sum((matrices[n]*w for n,w in weights.items()),Matrix(((0,)*4,)*4))
                v.co=transform.inverted_safe() @ (rig.matrix_world.inverted() @ world)
                for n,w in weights.items():groups[n].add([v.index],w,'REPLACE')
            modifier=ob.modifiers.new('Anatomical foot and toe skin','ARMATURE');modifier.object=rig
            ob.data.update()
    bpy.context.view_layer.update()
