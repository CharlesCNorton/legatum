#!/usr/bin/env python3
"""Offline, CPU-only Depth Anything V2 small; white means near (relative depth)."""
import os
os.environ['HF_HOME'] = '/Users/samcorcos/LegatumRuns/era-video-pilot/hf'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '6'

import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MASTERS = ROOT.parent / 'masters/classical'
MODEL = 'depth-anything/Depth-Anything-V2-Small-hf'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=ROOT / 'app/src/assets/eras/classical-1920.jpg')
    parser.add_argument('--masters', type=Path, default=DEFAULT_MASTERS)
    args = parser.parse_args()
    torch.set_num_threads(6)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    args.masters.mkdir(parents=True, exist_ok=True)
    image = Image.open(args.image).convert('RGB')
    processor = AutoImageProcessor.from_pretrained(MODEL, local_files_only=True)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL, local_files_only=True).to('cpu').eval()
    with torch.inference_mode():
        prediction = model(**processor(images=image, return_tensors='pt')).predicted_depth
        depth = torch.nn.functional.interpolate(prediction[:, None], size=(image.height, image.width),
                                                 mode='bicubic', align_corners=False)[0, 0].numpy()
    lo, hi = np.percentile(depth, (0.5, 99.5))
    depth = np.clip((depth - lo) / max(float(hi - lo), 1e-6), 0, 1)
    Image.fromarray(np.round(depth * 65535).astype(np.uint16)).save(args.masters / 'depth16.png')
    Image.fromarray(np.round(depth * 255).astype(np.uint8)).save(args.masters / 'depth-preview.png')
    (args.masters / 'depth.json').write_text(json.dumps({
        'model': MODEL, 'source': str(args.image.resolve()), 'size': image.size,
        'convention': 'relative inverse depth: 0 far, 1 near; not metric',
        'normalization_percentiles': [0.5, 99.5], 'device': 'cpu', 'threads': 6,
    }, indent=2) + '\n')
    print(f'Depth written to {args.masters}', flush=True)


if __name__ == '__main__':
    main()
