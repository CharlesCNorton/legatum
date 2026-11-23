"""Sequential CPU/GPU stage rendering with authored rigid-action keys."""
import bpy,sys,os,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-fighter';stage=sys.argv[sys.argv.index('--')+1]
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
UP=Vector((0,.36,math.sqrt(1-.36**2)));FRONT=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))

def setup(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
    assert sc.camera is not None
    engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.render.engine=engine
    if engine=='CYCLES':
        sc.cycles.samples=samples;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
        device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.device=device
        if device=='GPU':
            prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
            for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
            if not found:raise RuntimeError('Metal GPU unavailable; no silent CPU fallback')
    sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
    return sc

def render(sc,path):
    path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)

def curves(action):
    if hasattr(action,'fcurves'):return action.fcurves
    return [f for l in action.layers for s in l.strips for b in s.channelbags for f in b.fcurves]

def animate(sc,clip):
    n,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=n
    root=bpy.data.objects['RIG-airframe'];rest=root.location.copy()
    elevons=[bpy.data.objects['RIG-'+side+' elevon'] for side in ('near','far')]
    missile=bpy.data.objects['GEO-missile'];missile_rest=missile.location.copy()
    support=bpy.data.objects['GEO-curved stationary stone support']
    support_rest=support.location.copy();support.rotation_mode='QUATERNION'
    damage=[]
    if clip=='death':
        for name in ('GEO-near wing','GEO-fuselage'):
            o=bpy.data.objects[name];o.shape_key_add(name='Basis');key=o.shape_key_add(name='Impact deformation');damage.append(key)
            for v,k in zip(o.data.vertices,key.data):
                if name=='GEO-near wing':
                    w=max(0,min(1,(v.co.x-.1)/2.0))**2;k.co+=UP*(.30*w)+FRONT*(.18*w)
                else:
                    w=max(0,min(1,(v.co.x-1.2)/1.7));k.co-=RIGHT*(.18*w)+UP*(.12*w)
    for j in range(n+1 if loop else n):
        t=j/n if loop else j/(n-1);phase=math.tau*t;sc.frame_set(j+1);root.location=rest.copy();root.rotation_euler=(0,0,0)
        if clip=='idle':
            root.location+=UP*(.014*math.sin(phase));root.rotation_euler.x=.018*math.sin(phase)
        if clip=='move':
            root.location+=RIGHT*(.035*math.sin(phase))+UP*(.025*math.sin(phase));root.rotation_euler.x=.065*math.sin(phase);root.rotation_euler.y=.025*math.sin(phase)
        if clip=='attack':
            root.location+=RIGHT*(-.10*math.sin(math.pi*t))-UP*(.13*math.sin(math.pi*t));root.rotation_euler.y=.085*math.sin(math.pi*t);root.rotation_euler.x=.045*math.sin(phase)
        if clip=='hit':
            h=[0,1,-.45,0][j];root.location+=UP*(.045*h)-RIGHT*(.045*h);root.rotation_euler.x=.09*h;root.rotation_euler.y=.035*h
        if clip=='death':
            drop=[0,.04,.14,.32,.66,1.10,1.42,1.36,1.34,1.34][j];ease=min(drop/1.34,1)
            root.location+=-UP*drop+RIGHT*(.01*ease);root.rotation_euler.x=-.30*ease;root.rotation_euler.y=[0,.04,.11,.20,.30,.36,.25,.21,.20,.20][j];root.rotation_euler.z=-.07*ease
            for key in damage:key.value=0 if j<6 else 1;key.keyframe_insert('value',frame=j+1)
        root.keyframe_insert('location');root.keyframe_insert('rotation_euler')
        for k,o in enumerate(elevons):
            o.rotation_euler=(0,0,0);o.rotation_euler.x=(1 if k==0 else -1)*(.035*math.sin(phase) if loop else .045*math.sin(math.pi*t))
            if clip=='death':o.rotation_euler.x=.12 if j>=6 else 0
            o.keyframe_insert('rotation_euler')
        support.hide_render=False;support.keyframe_insert('hide_render')
        fall=[0,0,.06,.25,.62,1.12,1.38,1.36,1.36,1.36][j] if clip=='death' else 0
        support.rotation_quaternion=Quaternion(FRONT,fall)
        support.location=support_rest.copy()
        support.keyframe_insert('rotation_quaternion');support.keyframe_insert('location')
        missile.hide_render=not(clip=='attack' and .33<=t<=.72);missile.location=missile_rest.copy()
        if clip=='attack':missile.location+=(RIGHT*3.8+UP*1.7)*max(0,t-.33)-UP*.78+RIGHT*.25+FRONT*.90
        missile.keyframe_insert('hide_render');missile.keyframe_insert('location')
    for o in [root,*elevons,missile,support]:
        if o.animation_data:
            o.animation_data.action.name=clip+' | '+o.name
            for f in curves(o.animation_data.action):
                for k in f.keyframe_points:k.interpolation='CONSTANT' if 'hide_render' in f.data_path else 'LINEAR'
    if clip=='death':
        # Keep every aircraft vertex inside the fixed camera; change trajectory,
        # never per-frame image scale or the camera/stone anchor.
        from bpy_extras.object_utils import world_to_camera_view
        for frame in range(1,n+1):
            sc.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();xs=[]
            for ob in bpy.data.objects:
                parent=ob.parent
                while parent and parent!=root:parent=parent.parent
                if ob.type!='MESH' or parent!=root:continue
                eo=ob.evaluated_get(deps);mesh=eo.to_mesh()
                xs.extend(world_to_camera_view(sc,sc.camera,eo.matrix_world@v.co).x for v in mesh.vertices)
                eo.to_mesh_clear()
            lo,hi=min(xs),max(xs)
            assert hi-lo<.98,('crash exceeds fixed cell',frame,lo,hi)
            shift=max(0,.012-lo)+min(0,.988-hi)
            root.location+=RIGHT*(shift*sc.camera.data.ortho_scale)
            root.keyframe_insert('location',frame=frame)
    if clip=='death':
        sc.frame_set(n-1);base=bpy.data.objects['GEO-stationary cream base'];top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box);points=[]
        deps=bpy.context.evaluated_depsgraph_get()
        o=bpy.data.objects['GEO-fuselage'].evaluated_get(deps);me=o.to_mesh()
        for v in me.vertices:
            pt=o.matrix_world @ v.co
            if (pt.xy-base.location.xy).length<1.02:points.append(pt.z)
        o.to_mesh_clear();assert points,'wreck misses base footprint';correction=min(points)-top
        for f,weight in zip(range(6,n+1),(.2,.7,1,1,1)):
            sc.frame_set(f);root.location.z-=correction*weight;root.keyframe_insert('location',frame=f)
        sc['wreck_contact_correction']=correction
    sc['master_sha256']=hashlib.sha256((M/'stealth-fighter.blend').read_bytes()).hexdigest()
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))

stages=['b','c','d','g',*['e-'+c for c in CLIPS]] if stage=='all' else [stage]
for part in stages:
    sc=setup(M/('plain.blend' if part=='b' else 'stealth-fighter.blend'))
    out=M/'raw'/str(res)/part;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
    if part=='b':
        clay=bpy.data.materials.new('MAT-clay');clay.diffuse_color=(.46,.46,.46,1);sc.view_layers[0].material_override=clay;render(sc,out/'000.png')
        from mathutils import Matrix
        original=sc.camera.location.copy()
        for i,angle in enumerate((.52,1.20),1):
            sc.camera.data.ortho_scale=6.4*(1.15 if i==1 else 1.3);sc.camera.location=Matrix.Rotation(angle,4,'Z')@original;sc.camera.rotation_euler=(-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(sc,out/f'{i:03}.png')
    elif part=='c':render(sc,out/'000.png')
    elif part=='g':
        # Aircraft counterpart to feet check: airframe direction and bank from top/front.
        animate(sc,'move')
        target=bpy.data.objects['RIG-airframe'].location.copy()
        for row,direction in enumerate((Vector((0,0,1)),(RIGHT*.89+UP*.455-FRONT*.03).normalized())):
            sc.camera.location=target+direction*15
            sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
            sc.camera.data.ortho_scale=7.5
            for i in range(8):
                sc.frame_set(i+1);render(sc,out/f'{row*8+i:03}.png')
    elif part=='d':
        animate(sc,'attack')
        for i,f in enumerate((1,4,7,10)):sc.frame_set(f);render(sc,out/f'{i:03}.png')
    else:
        clip=part[2:];animate(sc,clip)
        for i in range(CLIPS[clip][0]):
            if clip=='death' and i==9:
                shutil.copyfile(out/'008.png',out/'009.png')
            else:
                sc.frame_set(i+1);render(sc,out/f'{i:03}.png')
    manifest.write_text(json.dumps({'stage':part,'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':samples,'resolution':res,'input_sha256':hashlib.sha256((M/('plain.blend' if part=='b' else 'stealth-fighter.blend')).read_bytes()).hexdigest(),'master_sha256':hashlib.sha256((M/'stealth-fighter.blend').read_bytes()).hexdigest(),'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))}},indent=2))
    print('STAGE_COMPLETE',part,flush=True)
