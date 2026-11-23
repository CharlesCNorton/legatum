## 2026-11-22: Hybrid CG contact and painted light need explicit treatment

- The user's v5 frames approve camera, crisp painting and readable movement, but
  reject the oversized grey galley, floating water contact and small smoke puff.
  Ship scale now compares against the painted galley at the same water depth;
  the former frame-width target is superseded (recorded in `legatum-art`).
- The water effects followed the ship root/deck, not the immersed hull. V6
  projects the rotated hull waterline onto the water plane. Python checks at
  frames 1/72/144 give alignment error below 1e-8 px and ship/reference widths
  of 1.15–1.19. These are geometry checks, not rendered appearance acceptance.
- The scholars are part of an emission-only painted relief, so increasing the
  point light cannot illuminate them. V6 uses a soft, surface-specific amber
  treatment tied to the flame/light flicker while retaining the crisp painting.
- V5's live scene report records a successful 21.49-second bake but smoke spans
  of only 13.36–27.44 units. V6 enlarges the domain/inflow, extends pre-roll and
  checks projected occupied density after shader fades against 150–250 px.
  The full domain clears the relief by two units; stable vorticity is retained.
- Python preparation/compilation and source/asset hashes passed. No Blender was
  run, no commit was made, and runtime/visual validation remain with the lead
  under the lock. Fresh assets are in `masters/hybrid-v6`; v5 is preserved.
