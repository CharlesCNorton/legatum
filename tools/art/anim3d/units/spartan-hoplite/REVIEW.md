# Spartan hoplite — round 2

This remains an art candidate. At 256 px, the raised grip, narrower crest/shield
and source-painted linen are closer to the painting. Helmet/gaze, plume sweep,
shoulder drape, leg shading and the stone rim still differ. At 64 px the unit is
recognizable and its contour is closer, but it is still distinguishable. No PASS
marker is warranted. CPU previews are not evidence of a completed GPU pass.

The new repeatable `refine.py` starts from the preserved unpainted checkpoint,
finishes static geometry before UV calibration, and uses one frozen camera
projection instead of stretching each part's painting independently. Original
MPFB anatomy/weights, 53 bones, solid kit, cloth simulation, AO/curvature and the
existing generated linen fill remain. Camera-only painted pigment preserves
brushwork while non-camera rays retain PBR shading. One automatic rest histogram
grade is reused across all clips. Unit-owned animation carries the raised guard
through idle/move/combat; repeated held-death samples reuse identical PNG bytes.

External artifacts remain under `~/LegatumRuns/anim-pilot/`:

- Current editable master, clips/caches, raw previews, 256 gallery frames and
  provenance: `masters/spartan-hoplite/round2-3d/`.
- Previous 512 CPU masters: `masters/spartan-hoplite/round1-3d/`, retained intact.
- Current review PNGs, WebPs, round MP4, checks and running log:
  `review/3d-v2/spartan-hoplite-*`; previous images in the round1-history directory.
- Original source painting and masks: `assets/spartan-hoplite/`.

The candidate atlas retains 160 px logical cells, per-frame trim offsets and all
8/8/10/4/10 samples. Quality stays at least 75 and size at most 200,000 bytes.
No runtime UI or rules change. Measurements and final checks are recorded below
and in the external pack/validation reports.

The complete host command is:

```sh
ROUND=2 tools/art/anim3d/units/spartan-hoplite/gpu.sh
```

This executable no-argument entry point regenerates the model/cloth clips, audits
geometry, renders every stage at GPU512/64, writes actual 512/256 masters, verifies
provenance, packs/validates the atlas, and creates the decoded five-clip MP4. A
retained transcript and status file identify the failing stage if interrupted.
Unavailable Metal fails explicitly. Review the new images and motion before art
acceptance; the script never writes PASS automatically.

Round-two CPU results: all 40 RGBA frames at 256 px / Cycles CPU / 12 samples;
160 px trimmed atlas **199,862 bytes at quality 90**. All five clip
counts, trim/alpha/RGB reconstruction, motion, margins, current source hashes and
identical terminal death validate. Full forty-sample rig audit: **0 findings**.
Scene check: 172 projected meshes, original 19,158-vertex anatomy and 53 bones,
camera-only pigment wiring, nonzero scales and input hashes passed. The decoded
MP4 verifies H.264/yuv420p, 1600×348, 240 frames/eight seconds; a frame extracted
from the actual movie was visually inspected alongside every clip strip.

The CPU-only output is correctly rejected by the GPU master gate because fresh
512 masters are absent. Missing-input script preflight recorded the expected
failure before Blender. A separate GPU device test was cancelled while waiting
for the shared gate; no device result or host GPU pass is claimed. Fresh 512 GPU
masters remain required. Previous round-one CPU512 masters are preserved.

Visual verdict: no PASS. At 256, the plume is still too uniform, the neck/mantle
forms a broad shelf, linen layers remain less crisp and stone shading differs.
At 64 the identity/outline is closer but distinguishable. Death presents its
shield more frontally at entry and settles stiffly; technical audit success does
not establish five visually clean clips. The next round should address these.

Code checks: 16 Python files parsed; both unit shell scripts passed syntax; GPU
entry point is executable; whitespace passed. Current-file hygiene scanned 21
files with zero findings after spacing the matrix operators. Baseline public-claims
passed. Browser art-set gate failed in the sandbox Node renderer and needs host
verification. Git add/commit were denied index.lock creation; changes remain
uncommitted for the runner. The requested co-author commit message is retained
in the external task tmp directory. No push or PR was attempted.
