"""Five reusable mechanical clips, with exact delivery sample counts."""
import bpy, math, os, json, hashlib
from pathlib import Path
from mathutils import Quaternion
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/fighter'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def curves(action):
    if hasattr(action,'fcurves'):return action.fcurves
    return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
for clip,(count,fps,loop) in CLIPS.items():
    if os.environ.get('ANIMATE_CLIP') and os.environ['ANIMATE_CLIP']!=clip:continue
    bpy.ops.wm.open_mainfile(filepath=str(M/'fighter.blend'));sc=bpy.context.scene;root=bpy.data.objects['RIG-flight'];prop=bpy.data.objects['RIG-propeller'];support=bpy.data.objects['DISPLAY • curved stone pedestal']
    rest=root.location.copy();prop_rest=prop.rotation_quaternion.copy();support_rest=support.location.copy();sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
    bends=[]
    if clip=='death':
        # Retain solid blades, folding their outer sections forward on impact.
        # Evaluate this deformation for contact rather than checking the rest mesh.
        center=prop.matrix_world.translation.copy()
        axis=prop.matrix_world.to_3x3().col[0].normalized()
        for blade in [o for o in sc.objects if o.name.startswith('Propeller blade')]:
            blade.shape_key_add(name='Basis');bend=blade.shape_key_add(name='Impact fold')
            inverse=blade.matrix_world.inverted()
            points=[blade.matrix_world @ v.co for v in blade.data.vertices]
            radial=(max(points,key=lambda p:(p-center).length_squared)-center).normalized()
            tangent=radial.cross(axis).normalized()
            for target,point in zip(bend.data,points):
                distance=(point-center).dot(radial)
                weight=max(0,min(1,(distance-.22)/.30))
                pivot=center+radial*.22
                target.co=inverse @ (pivot+Quaternion(tangent,1.25*weight) @ (point-pivot))
            bends.append(bend)
    # One extra sample closes periodic curves; not duplicated into output atlas.
    for i in range(count+int(loop)):
        sc.frame_set(i+1);t=i/count if loop else i/(count-1);s=math.sin(t*2*math.pi);c=math.cos(t*2*math.pi)
        root.location=rest;root.rotation_euler=(0,0,0);support.hide_render=False;support.rotation_euler=(0,0,0);support.location=support_rest
        if clip=='idle':root.location.z+=.035*s;root.rotation_euler.x=.018*s;root.rotation_euler.y=.008*s
        elif clip=='move':root.location.x+=.09*s;root.location.z+=.07*s;root.rotation_euler.x=.045*s;root.rotation_euler.y=.018*s
        elif clip=='attack':
            run=math.sin(math.pi*t)**2;root.location.x+=.12*run;root.location.z-=.16*run;root.rotation_euler.y=.065*run;root.rotation_euler.x=-.025*math.sin(2*math.pi*t)
        elif clip=='hit':
            j=[0,1,-.50,0][i];root.location.y+=.10*j;root.location.z-=.07*abs(j);root.rotation_euler.x=.065*j;root.rotation_euler.z=.035*j
        else:
            # Stall, nose drop, impact, then held wreck. No shrinking geometry.
            phases=[(0,0,0),(.05,-.04,.02),(.20,.07,.06),(.42,.18,.10),(.70,.28,.08),(.90,.34,.05),(1,.31,.02),(1,.30,.02),(1,.30,.02),(1,.30,.02)]
            fall,pitch,bank=phases[i];root.location.z-=1.33*fall;root.location.x-=.22*fall;root.rotation_euler=(bank,pitch,0);support.rotation_euler=(-1.48*fall,0,0)
        spin=(i*2*math.pi/count if clip in ('idle','move') else i*.31 if clip!='death' else min(i,6)*math.pi/9)
        prop.rotation_quaternion=prop_rest @ Quaternion((1,0,0),spin)
        for bend in bends:
            bend.value=[0,0,0,.12,.6,1,1,1,1,1][i]
            bend.keyframe_insert('value',frame=i+1)
        if clip=='death':
            # Solid geometry stays above the actual stone footprint/world ground.
            # Contact correction is on the rigid assemblies, never a zero-scale hide.
            bpy.context.view_layer.update()
            def floor_gap(objects):
                gap=0.0
                deps=bpy.context.evaluated_depsgraph_get()
                for obj in objects:
                    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
                    for vertex in mesh.vertices:
                        point=evaluated.matrix_world @ vertex.co
                        floor=.22 if (point.x+.02)**2+point.y**2<1.00**2 else .04
                        gap=max(gap,floor-point.z)
                    evaluated.to_mesh_clear()
                return gap
            support.location.z+=floor_gap([support])
            root.location.z+=floor_gap([o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith(('BASE','DISPLAY','FX-'))])
        for obj in (root,prop,support):
            obj.keyframe_insert('location',frame=i+1);obj.keyframe_insert('rotation_quaternion' if obj==prop else 'rotation_euler',frame=i+1)
        support.keyframe_insert('hide_render',frame=i+1)
        for obj in [o for o in bpy.data.objects if o.name.startswith('FX-')]:
            obj.hide_render=not(clip=='attack' and i in (3,5));obj.keyframe_insert('hide_render',frame=i+1)
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            obj.animation_data.action.name=clip+' • '+obj.name
            for fc in curves(obj.animation_data.action):
                if obj==prop and loop:fc.modifiers.new('CYCLES')
                for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path=='hide_render' else ('LINEAR' if obj==prop else 'BEZIER')
    sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/(clip+'.blend')))
(M/'clips.json').write_text(json.dumps({'source_sha256':hashlib.sha256((M/'fighter.blend').read_bytes()).hexdigest(),'clips':{n:{'frames':v[0],'fps':v[1],'loop':v[2]} for n,v in CLIPS.items()}},indent=2))
print('FIVE CLIPS SAVED')
