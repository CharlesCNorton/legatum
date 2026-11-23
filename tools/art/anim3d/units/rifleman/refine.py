"""Full-depth painted-landmark fitting; UVs are frozen only after surface finish."""
import bpy, bmesh
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def finish(rig, body):
    sc=bpy.context.scene;cam=sc.camera
    if body.data.shape_keys:
        key=body.shape_key_add(name='Frozen anatomy',from_mix=True)
        coords=[v.co.copy() for v in key.data];body.shape_key_clear()
        for v,c in zip(body.data.vertices,coords):v.co=c
    # Freeze topology in bind space so the finished render and projection agree.
    for obj in list(sc.objects):
        if obj.type!='MESH':continue
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        for mod in list(obj.modifiers):
            if mod.type=='ARMATURE':continue
            if mod.type=='SUBSURF' and mod.levels==0:
                obj.modifiers.remove(mod);continue
            while list(obj.modifiers).index(mod)>0:
                bpy.ops.object.modifier_move_up(modifier=mod.name)
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        obj['finished_surface']=True
    bpy.context.view_layer.update()
    right=cam.matrix_world.to_quaternion() @ Vector((1,0,0));up=cam.matrix_world.to_quaternion() @ Vector((0,1,0));unit=cam.data.ortho_scale/256
    def deform(obj, transform, predicate=None, ground=False):
        deps=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(deps);me=ev.to_mesh()
        assert len(me.vertices)==len(obj.data.vertices),obj.name
        for vertex in obj.data.vertices:
            groups={obj.vertex_groups[g.group].name:g.weight for g in vertex.groups if obj.vertex_groups[g.group].name in rig.pose.bones}
            if predicate and not predicate(groups):continue
            w=ev.matrix_world @ me.vertices[vertex.index].co;p=world_to_camera_view(sc,cam,w);x,y=p.x*256,(1-p.y)*256
            tx,ty=transform(x,y);delta=(right*(tx-x)-up*(ty-y))*unit
            if ground:delta=right*(tx-x)*unit+Vector((0,1,0))*(-(ty-y)*unit/up.y)
            skin=obj.matrix_world.copy()
            if any(m.type=='ARMATURE' for m in obj.modifiers) and groups:
                matrix=Matrix(((0.,)*4,)*4);total=sum(groups.values())
                for name,weight in groups.items():matrix+=(rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted())*(weight/total)
                skin=rig.matrix_world @ matrix @ rig.matrix_world.inverted() @ obj.matrix_world
            vertex.co+=skin.to_3x3().inverted() @ delta
        ev.to_mesh_clear();obj.data.update()
    def affine(src,dst):
        return lambda x,y:(dst[0]+(x-src[0])*(dst[2]-dst[0])/(src[2]-src[0]),dst[1]+(y-src[1])*(dst[3]-dst[1])/(src[3]-src[1]))
    for obj in list(sc.objects):
        if obj.type!='MESH':continue
        name=obj.name
        if 'field jacket' in name:
            deform(obj,lambda x,y:(110+(x-110)*1.12, y+max(0,min(1,(y-91)/36))*15))
        elif 'sleeve r' in name or 'cuff r' in name:
            deform(obj,lambda x,y:(x-1,y+max(0,1-abs(y-100)/30)*2))
        elif 'sleeve l' in name or 'cuff l' in name:
            deform(obj,lambda x,y:(139+(x-139)*.78,y+max(0,1-abs(y-94)/38)*5))
        elif 'trousers' in name:
            side='r' if name.endswith('r') else 'l'
            deform(obj,lambda x,y:(x+(-5 if side=='l' else 2.0)*max(0,min(1,(y-118)/45)),y-max(0,(y-145)/68)*(0 if side=='r' else 1)))
        elif any(k in name for k in ('boot','lace')):
            side='r' if ' r' in name else 'l'
            deform(obj,affine((68.7,198.8,84.9,218.7),(65,201,87,216)) if side=='r' else affine((134.7,204.5,150.9,224.3),(128,205,159,223)),ground=True)
        elif 'pouch' in name:
            if name.endswith('.001'):deform(obj,affine((129.7,104.2,146.8,126.9),(128,108,139,137)))
            else:deform(obj,affine((72.8,104.2,89.9,126.9),(70,106,88,132)))
        elif 'kepi' in name:
            deform(obj,lambda x,y:(95+(x-96.1)*.96+max(0,(28-y))*.44,16+(y-19.1)*.86+(x-108)*.10))
        elif obj.parent and obj.parent.name=='CTRL-rifle' and 'sling' not in name:
            # Stock heel extends left; leave the muzzle registered.
            deform(obj,lambda x,y:(x-4*max(0,min(1,(y-90)/50)),y+2*max(0,min(1,(y-90)/50))))
    # Fit the actual grasping surfaces, not just wrist origins. Retain skin weights.
    for side,src,dst in [('r',(98,94,122,112),(101,95,120,111)),('l',(128,66,157,88),(135,73,151,92))]:
        deform(body,affine(src,dst),lambda groups:sum(w for n,w in groups.items() if n.endswith('_'+side) and n.startswith(('hand','index','middle','ring','pinky','thumb')))>.65)
    # Fit covered MPFB feet with their boots, retaining joint weights. Otherwise
    # the rest-view pigment hides toes that become exposed during the fall.
    for side,src,dst in [('r',(68.7,198.8,84.9,218.7),(65,201,87,216)),('l',(134.7,204.5,150.9,224.3),(128,205,159,223))]:
        deform(body,affine(src,dst),lambda groups:sum(w for n,w in groups.items() if n in ('foot_'+side,'ball_'+side))>.65,ground=True)
    # Under the uniform the anatomy must remain cloth when revealed in motion.
    body.data.materials.append(bpy.data.materials['MAT-painted indigo wool']);body.data.materials.append(bpy.data.materials['MAT-faded blue trousers']);body.data.materials.append(bpy.data.materials['MAT-scuffed tan leather'])
    for face in body.data.polygons:
        counts={}
        for i in face.vertices:
            for g in body.data.vertices[i].groups:
                name=body.vertex_groups[g.group].name
                if name in rig.pose.bones:counts[name]=counts.get(name,0)+g.weight
        if counts:
            name=max(counts,key=counts.get)
            if name.startswith(('spine','pelvis','clavicle','upperarm','lowerarm')):face.material_index=1
            elif name.startswith(('thigh','calf')):face.material_index=2
            elif name.startswith(('foot','ball')):face.material_index=3
    bpy.data.objects['LGT-rim'].data.energy=65
    bpy.data.objects['LGT-rim'].data.color=(.89,.93,1)
    bpy.context.view_layer.update()


def stone(sc, image):
    """Clean generated top on a real disc, live contact shadows, original rim."""
    obj=bpy.data.objects['GEO-stationary cream base'];cam=sc.camera
    uv=obj.data.uv_layers.new(name='Clean stone painting')
    for loop in obj.data.loops:
        co=world_to_camera_view(sc,cam,obj.matrix_world @ obj.data.vertices[loop.vertex_index].co);uv.data[loop.index].uv=(co.x,co.y)
    for slot in obj.material_slots:
        n=slot.material.node_tree.nodes;l=slot.material.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
        tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;t=n.new('ShaderNodeTexImage');t.image=image;t.extension='EXTEND';l.new(tc.outputs[0],t.inputs[0])
        ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09
        color=n.new('ShaderNodeMixRGB');l.new(t.outputs['Alpha'],color.inputs[0]);color.inputs[1].default_value=(.81485,.62396,.35153,1);l.new(t.outputs['Color'],color.inputs[2])
        shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.38;l.new(color.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
        pigment=n.new('ShaderNodeEmission');l.new(shade.outputs[0],pigment.inputs[0]);l.new(color.outputs[0],p.inputs['Base Color'])
        ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.95;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
        mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
