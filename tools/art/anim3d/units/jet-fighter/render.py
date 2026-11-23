"""Sequential CPU/GPU stage rendering with authored rigid-action keys."""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/jet-fighter';stage=sys.argv[sys.argv.index('--')+1]
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
UP=Vector((0,.28,math.sqrt(1-.28**2)));FRONT=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))

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
    flashes=[bpy.data.objects['GEO-flash-'+str(i)] for i in range(2)]
    support=bpy.data.objects['GEO-curved stone support'];supportrest=support.location.copy()
    # Longitudinal flight axis follows the painting's tail-to-nose direction.
    forward=(RIGHT*.93+UP*.24+FRONT*.27).normalized()
    root.rotation_mode='QUATERNION'
    from mathutils import Quaternion
    damage=None
    if clip=='death':
        wing=bpy.data.objects['GEO-near wing'];wing.shape_key_add(name='Basis')
        damage=wing.shape_key_add(name='Impact folded wing')
        for v,k in zip(wing.data.vertices,damage.data):
            weight=max(0,min(1,-v.co.x/2.3))**1.4
            k.co+=UP*(1.65*weight)+RIGHT*(.58*weight)
    for j in range(n+1 if loop else n):
        t=j/n if loop else j/(n-1);phase=math.tau*t;sc.frame_set(j+1)
        root.location=rest.copy();bank=0;pitch=0
        support.location=supportrest.copy();support.rotation_euler=(0,0,0)
        if clip=='idle':
            root.location+=UP*(.018*math.sin(phase));bank=.022*math.sin(phase)
        elif clip=='move':
            root.location+=forward*(.085*math.sin(phase))+UP*(.03*math.sin(phase));bank=.065*math.sin(phase);pitch=.012*math.cos(phase)-.012
        elif clip=='attack':
            root.location+=forward*(.08*math.sin(math.pi*t))-UP*(.13*math.sin(math.pi*t));bank=.07*math.sin(phase);pitch=-.055*math.sin(math.pi*t)
        elif clip=='hit':
            h=[0,1,-.45,0][j];root.location+=UP*(.05*h)-forward*(.06*h);bank=.13*h;pitch=.035*h
        elif clip=='death':
            drop=[0,.035,.12,.31,.60,1.06,1.44,1.48,1.46,1.46][j]
            root.location-=UP*drop;root.location-=RIGHT*[0,.01,.02,.03,.05,.07,.09,.11,.12,.12][j]
            bank=[0,.05,.12,.20,.30,.37,.43,.40,.39,.39][j]
            pitch=[0,-.01,-.04,-.07,-.13,-.18,-.16,-.13,-.13,-.13][j]
            fall=[0,0,.03,.11,.26,.43,.58,.63,.64,.64][j]
            support.rotation_euler.y=fall;support.location-=UP*(.12*fall)
            damage.value=[0,0,0,0,.05,.25,.70,.95,1,1][j];damage.keyframe_insert('value')
        root.rotation_quaternion=Quaternion(forward,bank)@Quaternion(FRONT,pitch)
        root.keyframe_insert('location');root.keyframe_insert('rotation_quaternion')
        support.keyframe_insert('location');support.keyframe_insert('rotation_euler')
        for k,ob in enumerate(flashes):
            ob.hide_render=not(clip=='attack' and j in (3+k,5+k));ob.keyframe_insert('hide_render')
    for ob in [root,support,*flashes]:
        if ob.animation_data:
            ob.animation_data.action.name=clip+' | '+ob.name
            for f in curves(ob.animation_data.action):
                for k in f.keyframe_points:k.interpolation='CONSTANT' if 'hide_render' in f.data_path else 'LINEAR'
    if clip=='death':
        # Contact is solved against the round base at impact, then held.
        sc.frame_set(n-1);base=bpy.data.objects['GEO-stationary cream base']
        top=max((base.matrix_world@Vector(v)).z for v in base.bound_box);points=[]
        deps=bpy.context.evaluated_depsgraph_get()
        for name in ('GEO-fuselage','GEO-near wing'):
            ob=bpy.data.objects[name].evaluated_get(deps);me=ob.to_mesh()
            for v in me.vertices:
                pt=ob.matrix_world@v.co
                if (pt.xy-base.location.xy).length<1.15:points.append(pt.z)
            ob.to_mesh_clear()
        assert points,'wreck misses base footprint'
        correction=min(points)-top
        for f,weight in zip(range(6,n+1),(.20,.65,1,1,1)):
            sc.frame_set(f);root.location.z-=correction*weight;root.keyframe_insert('location',frame=f)
        sc['wreck_contact_correction']=correction
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))

stages=['b','c','d',*['e-'+c for c in CLIPS]] if stage=='all' else [stage]
for part in stages:
    sc=setup(M/('plain.blend' if part=='b' else 'jet-fighter.blend'))
    out=M/'raw'/str(res)/part;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
    if part=='b':
        clay=bpy.data.materials.new('MAT-clay');clay.diffuse_color=(.46,.46,.46,1);sc.view_layers[0].material_override=clay;render(sc,out/'000.png')
        from mathutils import Matrix
        original=sc.camera.location.copy()
        for i,angle in enumerate((.52,1.20),1):
            sc.camera.data.ortho_scale=6.4*(1.15 if i==1 else 1.3);sc.camera.location=Matrix.Rotation(angle,4,'Z')@original;sc.camera.rotation_euler=(-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(sc,out/f'{i:03}.png')
    elif part=='c':render(sc,out/'000.png')
    elif part=='g':
        animate(sc,'move');center=bpy.data.objects['RIG-airframe'].location.copy()
        for view,direction in enumerate((Vector((0,0,1)),Vector((.93,-.27,.24)).normalized())):
            sc.camera.location=center+direction*15;sc.camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=8
            for i in range(8):sc.frame_set(i+1);render(sc,out/f'{view*8+i:03}.png')
    elif part=='d':
        animate(sc,'attack')
        for i,f in enumerate((1,4,7,10)):sc.frame_set(f);render(sc,out/f'{i:03}.png')
    else:
        clip=part[2:];animate(sc,clip)
        for i in range(CLIPS[clip][0]):

            if clip=='death' and i==9:
                import shutil;shutil.copyfile(out/'008.png',out/'009.png');continue
            sc.frame_set(i+1);render(sc,out/f'{i:03}.png')
    manifest.write_text(json.dumps({'stage':part,'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':samples,'resolution':res,'master_sha256':hashlib.sha256((M/'jet-fighter.blend').read_bytes()).hexdigest(),'render_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))}},indent=2))
    print('STAGE_COMPLETE',part,flush=True)
