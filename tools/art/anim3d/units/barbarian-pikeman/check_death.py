"""Cheap terminal-pose check before rerendering all ten death samples."""
import bpy,os
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']);bpy.ops.wm.open_mainfile(filepath=str(r/'masters/barbarian-pikeman/clips/death.blend'));s=bpy.context.scene;s.frame_set(9);s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=6;s.cycles.use_denoising=True;s.render.resolution_x=s.render.resolution_y=256;s.render.image_settings.color_mode='RGBA';s.render.filepath=str(r/'review/3d-v2/barbarian-pikeman-death-check.png');bpy.ops.render.render(write_still=True)
