"""Sequential CPU/GPU stage rendering with authored rigid-action keys."""
import bpy,sys,os,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/bomber';stage=sys.argv[sys.argv.index('--')+1]
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
UP=Vector((0,.25,math.sqrt(1-.25**2)));FRONT=Vector((0,-UP.z,UP.y));RIGHT=Vector((1,0,0))

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
    root=bpy.data.objects['RIG-airframe'];rest=root.location.copy();props=[bpy.data.objects['RIG-'+side+' propeller'] for side in ('near','far')];rot=[o.rotation_euler.copy() for o in props];bombs=[bpy.data.objects['GEO-bomb-'+str(i)] for i in range(3)];bombrest=[o.location.copy() for o in bombs]
    support=bpy.data.objects['GEO-curved stationary stone support']
    damage=[]
    support_damage=None
    if clip=='death':
        # Keep the support as a crushed, solid remnant; disappearing it made
        # the contact look like levitation despite the scalar height audit.
        base=bpy.data.objects['GEO-stationary cream base']
        top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box)
        support.shape_key_add(name='Basis')
        support_damage=support.shape_key_add(name='Crushed stone support')
        for v,k in zip(support.data.vertices,support_damage.data):
            height=max(0,v.co.z-top)
            k.co.x+=.12*height
            k.co.y=base.location.y+(v.co.y-base.location.y)*.6+.17*height
            k.co.z=top+.025+.10*height
        for name in ('GEO-near wing','GEO-fuselage'):
            o=bpy.data.objects[name];o.shape_key_add(name='Basis');key=o.shape_key_add(name='Impact deformation');damage.append(key)
            for v,k in zip(o.data.vertices,key.data):
                if name=='GEO-near wing':
                    w=max(0,min(1,(-v.co.x+.2)/2.7))**2;k.co+=UP*(.95*w)+FRONT*(.22*w)
                else:
                    w=max(0,min(1,(v.co.x-1.2)/1.7));k.co-=RIGHT*(.22*w)+UP*(.07*w)
    for j in range(n+1 if loop else n):
        t=j/n if loop else j/(n-1);phase=math.tau*t;sc.frame_set(j+1);root.location=rest.copy();root.rotation_euler=(0,0,0)
        if clip=='idle':root.location+=UP*(.018*math.sin(phase));root.rotation_euler.x=.025*math.sin(phase)
        if clip=='move':root.location+=RIGHT*(.055*math.sin(phase))+UP*(.025*math.sin(phase));root.rotation_euler.x=.065*math.sin(phase);root.rotation_euler.y=.025*math.sin(phase)
        if clip=='attack':root.location+=RIGHT*(-.05*math.sin(math.pi*t))-UP*(.12*math.sin(math.pi*t));root.rotation_euler.y=.07*math.sin(math.pi*t);root.rotation_euler.x=.04*math.sin(phase)
        if clip=='hit':
            h=[0,1,-.45,0][j];root.location+=UP*(.045*h)-RIGHT*(.055*h);root.rotation_euler.x=.09*h;root.rotation_euler.y=.035*h
        if clip=='death':
            # Bank, descend, nose impact; terminal wreck held for two samples.
            drop=[0,.04,.14,.36,.72,1.25,1.58,1.48,1.46,1.46][j];ease=drop/1.46;root.location+=-UP*drop-RIGHT*(.25*min(ease,1));root.rotation_euler.x=-.36*min(ease,1);root.rotation_euler.y=[0,.04,.11,.20,.32,.38,.27,.21,.20,.20][j];root.rotation_euler.z=-.08*min(ease,1)
            for key in damage:key.value=0 if j<6 else 1;key.keyframe_insert('value',frame=j+1)
            support_damage.value=[0,0,.08,.25,.55,.85,1,1,1,1][j]
            support_damage.keyframe_insert('value',frame=j+1)
        root.keyframe_insert('location');root.keyframe_insert('rotation_euler')
        for k,o in enumerate(props):
            o.rotation_euler=rot[k].copy()
            angle=j*(math.tau/3+math.tau/(3*n)) if loop else j*(math.tau/3+.26)
            if clip=='death' and j>=7:
                angle=6*(math.tau/3+.26)+(.16 if j==7 else .22)
            o.rotation_euler.z+=angle
            o.keyframe_insert('rotation_euler')
        support.hide_render=False;support.keyframe_insert('hide_render')
        for k,b in enumerate(bombs):
            release=.23+k*.12;b.hide_render=not(clip=='attack' and release<=t<=release+.35);b.location=bombrest[k].copy()
            if clip=='attack':b.location+=RIGHT*(.1*max(0,t-release))-UP*(3.5*max(0,t-release))
            b.keyframe_insert('hide_render');b.keyframe_insert('location')
    for o in [root,*props,*bombs]:
        if o.animation_data:
            o.animation_data.action.name=clip+' | '+o.name
            for f in curves(o.animation_data.action):
                for k in f.keyframe_points:k.interpolation='CONSTANT' if 'hide_render' in f.data_path else 'LINEAR'
    if clip=='death':
        # Settle the belly on the actual disc, not merely near it in projection.
        sc.frame_set(n-1);base=bpy.data.objects['GEO-stationary cream base'];top=max((base.matrix_world @ Vector(v)).z for v in base.bound_box);points=[]
        deps=bpy.context.evaluated_depsgraph_get()
        for name in ('GEO-fuselage','GEO-near nacelle'):
            o=bpy.data.objects[name].evaluated_get(deps);me=o.to_mesh()
            for v in me.vertices:
                pt=o.matrix_world @ v.co
                if (pt.xy-base.location.xy).length<.94:points.append(pt.z)
            o.to_mesh_clear()
        assert points,'wreck misses the base footprint'
        correction=min(points)-top
        for f,weight in zip(range(6,n+1),(.2,.7,1,1,1)):
            sc.frame_set(f);root.location.z-=correction*weight;root.keyframe_insert('location',frame=f)
        sc['wreck_contact_correction']=correction
    sc['master_sha256']=hashlib.sha256((M/'bomber.blend').read_bytes()).hexdigest()
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))

stages=['b','c','d','g',*['e-'+c for c in CLIPS]] if stage=='all' else [stage]
for part in stages:
    sc=setup(M/('plain.blend' if part=='b' else 'bomber.blend'))
    out=M/'raw'/str(res)/part;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
    if part=='b':
        clay=bpy.data.materials.new('MAT-clay');clay.diffuse_color=(.46,.46,.46,1);sc.view_layers[0].material_override=clay;render(sc,out/'000.png')
        from mathutils import Matrix
        original=sc.camera.location.copy()
        for i,angle in enumerate((.52,1.20),1):
            sc.camera.data.ortho_scale=6.4*(1.15 if i==1 else 1.3);sc.camera.location=Matrix.Rotation(angle,4,'Z')@original;sc.camera.rotation_euler=(-sc.camera.location).to_track_quat('-Z','Y').to_euler();render(sc,out/f'{i:03}.png')
    elif part=='c':render(sc,out/'000.png')
    elif part=='g':
        # Aircraft counterpart to feet check: shaft direction and bank from top/front.
        animate(sc,'move')
        target=bpy.data.objects['RIG-airframe'].location.copy()
        for row,direction in enumerate((Vector((0,0,1)),Vector((0,-1,.08)))):
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
    manifest.write_text(json.dumps({'stage':part,'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':samples,'resolution':res,'input_sha256':hashlib.sha256((M/('plain.blend' if part=='b' else 'bomber.blend')).read_bytes()).hexdigest(),'master_sha256':hashlib.sha256((M/'bomber.blend').read_bytes()).hexdigest(),'frames':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))}},indent=2))
    print('STAGE_COMPLETE',part,flush=True)
