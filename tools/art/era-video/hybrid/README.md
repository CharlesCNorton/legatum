# Classical harbour: hybrid v6

V6 responds to the supplied v5 renders: moving CG needs to belong to the painting.
The approved camera, ship route, cloth, 144 frames, 24 fps, 960×540, six threads,
CLI and CG-only compositor are preserved. The lead rendered v6; the subsequent
smoke/spill correction below has only Python verification so far. The lead owns
every Blender invocation through the machine-wide lock.

## Changes

- **Galley:** scale 2.1 instead of 3.65. Python projection gives hull widths
  84.5, 93.2 and 104.3 px at frames 1, 72 and 144: 1.15–1.19 times the painted
  galley at the same depth (source hull x=575..720, y=550). Build validation rejects
  a ratio above 1.3. This supersedes v5's 15–20% frame-width target; travel remains
  about 314 px. Original painted vessels and foreground occlusion remain.
- **Paint:** source-derived warm ivory sail with folds, seams and hems; dark umber
  timber with planking and wet keel shading; raised ochre gunwales, prow and eyes.
  Materials preserve more of their painted contrast, retain restrained daylight
  modelling and UV-locked bristle bump, and write the existing CG-only paint AOV.
- **Contact:** wake/reflection scale with the smaller vessel. Their camera-ray
  anchor now follows the immersed hull at local Z=-0.65 instead of the deck/root.
  Darker contact, brighter broken linen reflection and stronger foam support the
  waterline. The water mesh extends far enough right to carry the initial wake;
  its original mask still excludes shore and painted ships.
- **Smoke:** 32×88×28 domain, 96 base voxels, 2× noise, entirely at Z>=10 in front
  of the relief's maximum Z=8. Stronger/larger inflow, density 3.8±0.8, upward
  velocity 18±2, flame smoke 3.2 and render density gain 0.035. Pre-roll extends to
  -95 so the taller column can fill before frame 1. Ceiling and side feathers
  soften edges before the domain boundaries, with an amber base and cooler ash
  above. The vorticity stability fix (0.15/0.1, noise 0.5, six substeps, CFL 2)
  remains. No transforms animate on the fluid objects.
- **Gulls:** five distant birds preserved; two nearer passes now use Z=180/210
  and scale 3.1/3.5, approximately 28–44 px open wingspans.
- **Fire:** fuel, flame emission, point light and localized painted-surface spill
  share irregular flicker (roughly 0.53–1.44×). The scholars are emission-painted
  geometry and cannot receive a point light directly, so a soft surface mask
  applies amber light to nearby faces, robes and the brazier pedestal without
  relighting the entire picture. The point light illuminates the volume/CG.

### V6 smoke/spill correction

The lead's renders exposed an opaque, box-like smoke column. Reading the existing
noise caches without Blender shows that gain 3.4 saturates 86–90% of occupied
columns above optical depth 3 (under 5% transmission), even with boundary fades.
Gain 0.035 preserves density variation and translucent edges across the 28-unit
depth. Volume Info supplies scalar `density`, `flame` and `temperature`; density
times gain times side/ceiling feathers is the sole scattering/absorption density.
World Position normalized by the fixed domain bounds supplies the feathers.
Color only tints this density, and emission remains flame^1.2 times flicker times
the boundary envelope. Empty density/flame therefore produces no volume closure.
There is no surface shader or world volume. Warm base/grey-ochre colors remain.

The scholars' painted-surface spill is halved (0.48 → 0.24); the point light stays
unchanged because it lights the CG/volume, not the emission-painted scholars.
Galley, gulls, simulation and `verify_smoke()` height warnings are preserved.
`masters/hybrid-v6/smoke-shader-audit.json` records Python-only cache integration;
it is an opacity proxy, not a render. The lead must rebuild/render under the lock.

The source painting is unchanged. Generated textures and manifests are in
`masters/hybrid-v6`; v5 frames, clip and cache are preserved.

## Commands

Python preparation and syntax checks have been run. Rerun preparation whenever
the recipe changes. The CLI is unchanged.

```sh
export ERA_HYBRID=/Users/samcorcos/LegatumRuns/era-video-pilot/masters/hybrid-v6
export ERA_PYTHON=/Users/samcorcos/LegatumRuns/era-video-pilot/venv/bin/python
export OMP_NUM_THREADS=6
python3 -m py_compile tools/art/era-video/hybrid/scene.py
"$ERA_PYTHON" tools/art/era-video/hybrid/scene.py \
  --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" --prepare

# Invoke ONLY while the lead holds the existing Blender lock.
# This function does not acquire the lock itself.
hybrid_v6() {
  /opt/homebrew/bin/blender -b --factory-startup --disable-autoexec -t 6 \
    --python-exit-code 1 -P tools/art/era-video/hybrid/scene.py -- \
    --masters "$ERA_HYBRID" --out "$ERA_HYBRID/frames" "$@"
}
hybrid_v6 --dry-run
hybrid_v6 --bake-only
hybrid_v6 --frames 1-1
hybrid_v6 --frames 72-72
hybrid_v6 --frames 144-144
# Review representative stills and motion before rendering the entire clip.
hybrid_v6 --frames 49-72
hybrid_v6 --frames 1-144
FRAMES=144 SIZE=960x540 bash tools/art/era-video/encode.sh \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/classical-vfx-v6"
FRAMES=144 SIZE=960x540 "$ERA_PYTHON" tools/art/era-video/contact_sheet.py \
  "$ERA_HYBRID/frames" "$ERA_HYBRID/contact-vfx-v6.png"
```

## Verification and handoff

Python-only checks: `py_compile`, preparation, source/prepared hashes, unchanged
camera/timing/CLI/socket-helper ASTs, projected hull/reference ratios, and exact
camera-ray alignment of the hull contact and water effects. The checked textures
retain source paint; no image-generation service or Blender process was used.
Measurements are in `masters/hybrid-v6/static-validation.json`.

The lead-side bake must pass the existing complete-cache checks and now measures
the smoke grid **after the shader's density gain and boundary fades**. Its
projected occupied height target is 150–250 px at frames 1, 48, 96 and 144; misses
print a WARNING rather than aborting, preserving the lead's change. Density
occupancy is a geometric proxy: rendered opacity and brush character still need
visual review. Actual smoke height, clipping, flame shape, spill registration,
ship integration and runtime are unverified until the lead renders. The larger
domain and longer pre-roll increase bake work; the runtime report retains the
480-second target.

V5's successful lead render used a 21.49-second bake but only reached 13.36–27.44
world units of smoke height. The earlier excessive-vorticity diagnosis is recorded
in `docs/learnings/2026-11/22-hybrid-smoke-vorticity.md` and the preserved v5
diagnosis artifacts. Do not restore its unstable confinement settings.
