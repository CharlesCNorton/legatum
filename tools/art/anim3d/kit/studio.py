"""Explicit camera/light presets: no per-frame camera fitting or look changes."""
import json
from pathlib import Path
import bpy
from mathutils import Vector


def preset(name):
    return json.loads((Path(__file__).parent/'presets'/f'{name}.json').read_text())


def match_camera(scene, name):
    data = preset(name)['camera']
    camera = scene.camera
    assert camera is not None
    camera.location = data['location']
    camera.rotation_euler = (Vector(data['target'])-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'; camera.data.ortho_scale = data['ortho_scale']
    camera.data.dof.use_dof = False


def match_lighting(scene, name):
    data = preset(name)
    scene.view_settings.view_transform = data['view_transform']
    scene.view_settings.look = data['look']
    scene.world.color = data['world']
    for settings in data['lights']:
        ob = scene.objects.get(settings['name'])
        if ob is None:
            lamp = bpy.data.lights.new(settings['name'], 'AREA')
            ob = bpy.data.objects.new(settings['name'], lamp); scene.collection.objects.link(ob)
        ob.location = settings['location']
        ob.rotation_euler = (Vector(settings['target'])-ob.location).to_track_quat('-Z', 'Y').to_euler()
        ob.data.energy = settings['energy']; ob.data.size = settings['size']
        ob.data.color = settings['color']; ob.data.shape = 'DISK'
