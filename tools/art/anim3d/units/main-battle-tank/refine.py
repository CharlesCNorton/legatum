"""Register full-depth geometry in the rest camera; retain physical depth and rigid pivots."""
import bpy,os,sys,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
M=Path(os.environ['ANIM_ROOT'])/'masters/main-battle-tank'
bpy.ops.wm.open_mainfile(filepath=str(M/'main-battle-tank-built.blend'))
sc=bpy.context.scene;bpy.context.view_layer.update();camera=sc.camera
right=camera.rotation_euler.to_matrix()@Vector((1,0,0));up=camera.rotation_euler.to_matrix()@Vector((0,1,0));unit=camera.data.ortho_scale/256
records=[]
def fit(label,prefixes,target):
    objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(prefixes)]
    points=[world_to_camera_view(sc,camera,o.matrix_world@v.co) for o in objects for v in o.data.vertices]
    x0=min(p.x*256 for p in points);x1=max(p.x*256 for p in points);y0=min((1-p.y)*256 for p in points);y1=max((1-p.y)*256 for p in points)
    a,b,c,d=target
    for o in objects:
        inv=o.matrix_world.inverted()
        for v in o.data.vertices:
            w=o.matrix_world@v.co;p=world_to_camera_view(sc,camera,w);x=p.x*256;y=(1-p.y)*256
            xx=a+(x-x0)/(x1-x0)*(c-a);yy=b+(y-y0)/(y1-y0)*(d-b)
            v.co=inv@(w+unit*(right*(xx-x)-up*(yy-y)))
        o.data.update()
    records.append(dict(part=label,before=[x0,y0,x1,y1],after=target))
fit('Hull envelope',('Lower hull','Sloped upper hull','Raised track fender','Armoured side skirt','Skirt bolt','Forward fender','Hull weld','Headlamp','Glacis handrail','Engine louvre'),(15,107,218,148))
fit('Cast turret',('Rounded cast turret','Turret casting seam','Turret bearing'),(71,86,145,114))
fit('Cupola',('Closed commander','Cupola bevel','Periscope'),(85,78,106,90))
fit('Machine gun and hatch',('Gunner hatch','Machine gun'),(106,74,124,87))
fit('Cast mantlet',('Cast mantlet',),(133,94,148,109))
fit('Gun sleeve',('Gun sleeve',),(144,96,161,104))
# Map the actual barrel axis, preserving cylindrical cross-section instead of
# stretching a gun/mantlet group's combined bounding box.
gun=bpy.data.objects['Gun recoil'];bpy.context.view_layer.update()
a=world_to_camera_view(sc,camera,gun.matrix_world@Vector((.32,0,0)))
b=world_to_camera_view(sc,camera,gun.matrix_world@Vector((2.14,0,0)))
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('Long smoothbore','Muzzle lip','Recessed muzzle')):continue
    inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        w=o.matrix_world@v.co;local=gun.matrix_world.inverted()@w;t=(local.x-.32)/1.82
        # Restrained two-pixel barrel, including the original painting's elevation.
        local.y*=.62;local.z*=.62;w=gun.matrix_world@local
        old=Vector((256*(a.x+t*(b.x-a.x)),256*(1-a.y-t*(b.y-a.y))))
        new=Vector((150+93*t,99-17*t));delta=new-old
        v.co=inv@(w+unit*(right*delta.x-up*delta.y))
    o.data.update()
fit('Rear drum',('Rear pale fuel drum','Fuel drum','Drum end'),(18,88,58,106))
fit('Canvas roll',('Canvas roll','Canvas thick'),(39,94,76,109))
fit('Rear boxes',('Rear stowage box','Stowage lid','Box latch'),(21,105,87,119))
fit('Cream disc',('Stationary cream stone base',),(13,143,223,182))
base=bpy.data.objects['Stationary cream stone base'];bpy.context.view_layer.update()
face=max([p for p in base.data.polygons if p.normal.z>.9],key=lambda p:p.area)
normal=(base.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized();plane=base.matrix_world@face.center
# Register actual wheel centres, retaining circular wheel geometry and real thickness.
# These are per-side physical X/Z translations, never 2D frame warps.
for side in [-1,1]:
    targets=[(33,137),(52,140),(72,142),(92,145),(112,147),(132,149)]
    for i,(x,y) in enumerate(targets):
        o=bpy.data.objects[f'Road wheel pivot {side} {i}'];p=world_to_camera_view(sc,camera,o.matrix_world@Vector((0,side*.18,0)))
        if side==1: x+=35;y-=13
        dx=(x-p.x*256)*unit/right.x;dz=(-(y-(1-p.y)*256)*unit-up.x*dx)/up.z
        o.location+=Vector((dx,0,dz));o.scale=(.84,1,.84);o['rolling_radius']=.29*.84
    ends=[]
    for label,(x,y) in zip(('-1.65','1.65'),[(22,127),(152,139)] if side==-1 else [(57,114),(204,130)]):
        o=bpy.data.objects[f'Sprocket pivot {side} {label}'];p=world_to_camera_view(sc,camera,o.matrix_world@Vector((0,side*.18,0)))
        dx=(x-p.x*256)*unit/right.x;dz=(-(y-(1-p.y)*256)*unit-up.x*dx)/up.z
        o.location+=Vector((dx,0,dz));o.scale=(.77,1,.77);o['rolling_radius']=.27*.77
        ends.append((o.location.x,o.location.z,.27*.77+.022))
    first=bpy.data.objects[f'Road wheel pivot {side} 0'];last=bpy.data.objects[f'Road wheel pivot {side} 5']
    circles=[ends[0],(first.location.x,first.location.z,.29*.84+.027),(last.location.x,last.location.z,.29*.84+.027),ends[1]]
    route_data=json.loads(sc['track_circles']);route_data[str(side)]=circles;sc['track_circles']=json.dumps(route_data)
    length,point=route(circles)
    for o in bpy.data.objects:
        if 'track_phase' in o and o['track_side']==side:
            x,z,a=point(o['track_phase']);o.location=(x,side*.99,z);o.rotation_euler[1]=a
    if side==-1:sc['track_length']=length
# Fit the disc's upper support plane to the belt contact run, keeping its
# lower rim fixed. The painting's slightly inclined ground is not a level studio floor.
bpy.context.view_layer.update()
contact=[]
for side,i in [(-1,0),(-1,5),(1,0)]:
    wheel=bpy.data.objects[f'Road wheel pivot {side} {i}']
    contact.append(wheel.matrix_world.translation-Vector((0,0,wheel['rolling_radius']+.0445)))
plane_normal=(contact[1]-contact[0]).cross(contact[2]-contact[0]).normalized()
if plane_normal.z<0:plane_normal=-plane_normal
base=bpy.data.objects['Stationary cream stone base'];inv=base.matrix_world.inverted()
verts=[base.matrix_world@v.co for v in base.data.vertices]
zmin=min(v.z for v in verts);zmax=max(v.z for v in verts)
for vertex,world in zip(base.data.vertices,verts):
    # Upper face and bevel move; bottom silhouette stays fixed.
    weight=max(0,min(1,(world.z-zmin)/(zmax-zmin)*1.6-.6))
    target=contact[0].z-(plane_normal.x*(world.x-contact[0].x)+plane_normal.y*(world.y-contact[0].y))/plane_normal.z
    world.z+=(target-world.z)*weight;vertex.co=inv@world
base.data.update()
# Running gear remains planted while only sprung armour vibrates.
root=bpy.data.objects['Vehicle suspension root']
gear=bpy.data.objects.new('Running gear root',None);bpy.context.collection.objects.link(gear);gear.location=root.location
for o in list(bpy.data.objects):
    if 'wheel' in o or 'track_phase' in o:o.parent=gear
# Full-depth bearing collar fills the space under the fitted dome.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.63,depth=.30,location=(.03,0,1.27))
collar=bpy.context.object;collar.name='Turret bearing collar';collar.parent=root
collar.data.materials.append(bpy.data.materials['Olive drab • mottled cast and rolled steel'])
bevel=collar.modifiers.new('Bearing bevel','BEVEL');bevel.width=.02;bevel.segments=3
bpy.ops.object.modifier_apply(modifier=bevel.name)
for polygon in collar.data.polygons:polygon.use_smooth=True
# Flash location follows the actual fitted muzzle rather than the donor's barrel length.
bpy.context.view_layer.update();gun=bpy.data.objects['Gun recoil'];muzzle=bpy.data.objects['Recessed muzzle bore']
sc['muzzle_local']=list(gun.matrix_world.inverted()@(muzzle.matrix_world@(sum((v.co for v in muzzle.data.vertices),Vector())/len(muzzle.data.vertices))))
sc['registered']=True
(M/'registration.json').write_text(json.dumps(records,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'main-battle-tank-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'main-battle-tank.blend'))
print('REGISTERED',len(records),'full-depth component groups')
