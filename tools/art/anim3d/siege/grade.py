"""Restrained histogram-derived grade; alpha and geometry are untouched."""
from pathlib import Path
import json
from PIL import Image,ImageStat,ImageEnhance

def grade(im,source):
 mask=im.getchannel('A').point(lambda x:255 if x>192 else 0)
 smask=source.getchannel('A').point(lambda x:255 if x>192 else 0)
 rgb=im.convert('RGB');target=source.convert('RGB')
 stats=ImageStat.Stat(rgb,mask);ref=ImageStat.Stat(target,smask)
 # Preserve material colours: modest channel gain, not unrestricted histogram transfer.
 gain=[max(.90,min(1.12,b/max(1,a))) for a,b in zip(stats.mean,ref.mean)]
 channels=[c.point(lambda x,g=g:min(255,round(x*g))) for c,g in zip(rgb.split(),gain)]
 rgb=Image.merge('RGB',channels)
 current=ImageStat.Stat(rgb.convert('L'),mask).stddev[0];desired=ImageStat.Stat(target.convert('L'),smask).stddev[0]
 contrast=max(1,min(1.14,desired/max(1,current)));rgb=ImageEnhance.Contrast(rgb).enhance(contrast);rgb=ImageEnhance.Color(rgb).enhance(1.07)
 rgb.putalpha(im.getchannel('A'));return rgb,{'channel_gain':gain,'contrast':contrast,'saturation':1.07}

def apply(folder,source):
 raw=folder/'ungraded';raw.mkdir(exist_ok=True);report={}
 for path in sorted(folder.glob('*.png')):
  original=raw/path.name
  # Each render call refreshes files; retain this pass's raw evidence before grading.
  im=Image.open(path).convert('RGBA');im.save(original);result,stats=grade(im,source);result.save(path);report[path.name]=stats
 (folder/'grade.json').write_text(json.dumps(report,indent=2))
