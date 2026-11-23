# Barbarian pikeman — driver round 2

Status: **candidate, not an art pass**. No PASS marker. The driver round-one
GPU pass succeeded: Cycles Metal512, 175552 bytes at Q90, validated 512/256
masters and H.264 review movie. Its evidence is preserved externally under
`masters/barbarian-pikeman/driver-r1-gpu/`.

This revision retains true MPFB anatomy, original weighted full-depth kit,
finished-geometry frozen camera UVs, product lighting and one automatic fixed
histogram grade. It adds image-generated linen on hidden garment surfaces,
raised diagonal quilting, an inverse-skinned coat-side fit, a shallower warm
stone disc and clean front-rim source pigment. Projection is forbidden on the
stone top and above token y225. Cream contamination on rolling boot edges is
masked while leather highlights remain.

Idle, move, hit and death now use CC0 Quaternius Universal Animation Library
Standard actions, calibrated through Blender constraints including rest poses
and bone roll. These are authored library animations, not mocap. The native
foot rotations are retained. Root translation stabilizes sampled toe stance;
vertical contact uses evaluated surfaces. Both hands solve to one pike control;
its carrying height is limited by the fixed camera so the long tip stays inside
the frame. The original short thrust remains. Hit recovers to guard, death
releases the pike and holds its last two samples. No cloth simulation is claimed.

At **256 px**, the front paint and base are closer, but the shoulder/sleeve
junction still has a plain patch, boots and face lose some painted detail, and
revealed surfaces are less rich. The thrust remains restrained and the move's
upright silhouette differs substantially from the braced guard. At **64 px**,
the helmet, buff/red costume and long pike clearly read as the same unit, but
rest is still distinguishable. All five strips and sampled decoded movie frames
were inspected. This does not meet the hard-to-distinguish art bar yet.

The numeric foot audit measures yaw with the lateral foot axis. An initial
ankle-to-toe horizontal test falsely flagged steep toe-off as reversed travel;
source and target rest axes were inspected and the measurement was corrected,
without changing foot rotations. Maximum forward yaw is 1.73 degrees; sampled
stance residual is 0.000001062 m. These measurements are not a complete
heel/toe rollover or cloth collision proof.

Current delivery and checks are recorded in the external unit log and
`barbarian-pikeman-validation.json`. CPU previews are Cycles CPU12/256, all
40 samples, 160px trimmed logical cells, **172048 bytes at Q90**, and lossless alpha. The scene, source
hashes and 40-frame rig audit pass; the rig's maximum wrist/shaft distance is
6.94 cm (a wrist metric, not a palm-contact proof). Six AO/Pointiness maps were
rebuilt. The front/top foot cycle is saved as `barbarian-pikeman-g-feet-check.png`.
All 16 Python files and both shell scripts pass syntax checks; whitespace passes. The movie is verified H.264/yuv420p, 1600x348, 240 frames and exactly eight seconds. No Rust or runtime UI changed.

The GPU receipt rejects CPU deliveries. Actual device preflight reports
`Metal GPU unavailable; no CPU fallback` in this sandbox. The revised GPU pass
must still run on the lead's host:

```sh
ROUND=2 tools/art/anim3d/units/barbarian-pikeman/gpu.sh
```

The executable no-argument handoff validates inputs and device, rebuilds clips,
audits, renders all ten stages (including sixteen foot views) on Cycles Metal
at 512px, retains 512/256 masters, grades, trims, validates, writes the eight-second
side-by-side MP4 and verifies its codec/pixel format/frame count. Logs, failure
stage and a fresh receipt distinguish completion from an interrupted run.
It does not write PASS; fresh GPU art and motion review is still required.
