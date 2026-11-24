"""Record validated delivery evidence; never convert numerical targets into PASS."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.report import append_evidence

root = Path(os.environ['ANIM_ROOT'])
review = root/'review/3d-v2'
round_number = int(os.environ['ROUND'])
validation = json.loads((review/'spearman-validation.json').read_text())
metrics = json.loads((review/f'spearman-round{round_number}-metrics.json').read_text())
feet = json.loads((root/'masters/spearman-3d-v2/feet-check/metrics.json').read_text())['checks']
label = 'CPU preview' if validation['preview'] else 'GPU final render, visual review pending'
append_evidence(review/f'spearman-round{round_number}-note.md',
    f"### Delivery receipt ({label})\n\n"
    f"- 40 frames; 160 px trimmed atlas: {validation['bytes']} bytes, quality {validation['quality']}; decoded validation {validation['status']}.\n"
    f"- Walk: planted slip {feet['max_sole_contact_slip_m']*1000:.4f} mm; floor error {feet['max_planted_floor_error_m']*1000:.3f} mm; heading {feet['max_planted_heading_degrees']:.3f}°.\n"
    f"- Movie: five clips, 1600×352, H.264 yuv420p, 192 frames / 8 seconds. No art PASS issued.")
if not validation['preview']:
    note = review/f'spearman-round{round_number}-note.md'
    text = note.read_text().replace('combined candidate, CPU review / GPU pending',
                                    'combined candidate, GPU rendered / visual review pending')
    text = text.replace('Delivery status: CPU verified; GPU pass and final visual review pending.',
                        'Not a PASS. The GPU pass, pixel-parity gate and decoded atlas validation completed; final visual approval is pending. The CPU evidence below remains labelled separately from the appended GPU receipt.')
    note.write_text(text)
    with Path('tools/art/anim3d/LOG.md').open('a') as log:
        log.write(f"\n- Spearman round {round_number} GPU receipt: IoU {metrics['silhouette_iou']:.4f}; blurred ΔE {metrics['mean_delta_e_blurred']:.2f}; raw ΔE {metrics['mean_delta_e_cie76']:.2f}; atlas {validation['bytes']} bytes / q{validation['quality']}; 40 frames. Visual review pending.\n")
