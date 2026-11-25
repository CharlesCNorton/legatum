# Premium source survey: hoplite / Spartan models

Searched 2026-11-25. Goal: find a free, licence-clean, high-quality figure to fit onto the 0 A.D. skeleton, keeping the approved round-6 animations.

Sources checked:
- the Sketchfab API: six searches (`hoplite`, `spartan`, `greek warrior`, `greek soldier`, `ancient soldier`, `phalanx`), downloadable only, 131 unique models;
- an OpenGameArt search for "hoplite", which found only an aspis shield;
- Quaternius, Kenney and 0 A.D., already covered in `tools/art/anim3d/PRIOR-ART.md`: there is no premium hoplite figure there.

Sketchfab "Free Standard" and NonCommercial models are excluded: they can't sit in a public open-source repo, or forbid commercial use. Sci-fi "Spartan" results (Halo) and prop-only models are also excluded.

**Downloads: every Sketchfab model, free or paid, needs a Sketchfab login to download.** Nothing was downloaded except public thumbnails, and no account was created.

Contact sheet: `premium-source-shortlist.png` (the five candidates beside `spearman-panel.png`).

## Top 5 (free, CC BY 4.0: credit the author)

| # | Model | Author | Tris | Rigged | Textured | Likes | Fit to our painting |
|---|---|---|---|---|---|---|---|
| 1 | [Hoplite Warrior](https://sketchfab.com/3d-models/62d5291dd0454cb28a29a37056a59013) | caseydedore | 59k | no | yes, painted-realistic | 159 | **Closest.** Corinthian helmet with crest, bronze aspis, red chiton, greaves, spear, on a round base. Game-scale triangle count; decimate to about 10k. |
| 2 | [Hoplite](https://sketchfab.com/3d-models/bccbd407bf0e4b0495b352124e222300) | tolnaydavid | 404k | no | yes | 259 | Full panoply with a cloak. High-poly, so it would be a bake source (decimate or retopologise, then bake). Darker and more realistic in tone. |
| 3 | [300 Spartans](https://sketchfab.com/3d-models/e6960a513cfb40b0ac54637beab5ce85) | 3dUVpro | 30k | no | yes | 106 | Crested helmet, muscle armour, spear. Game-ready count. Film-style "300" look, more fantasy than our painting. |
| 4 | [Rigged for UE4 - Spartan - free](https://sketchfab.com/3d-models/666f485199db43488b14035f2a3840bf) | Andywoodhead | 178k | **yes** (UE4 skeleton) | yes | 379 | Bare-chested "300" Spartan. Rigged, but to UE4 bones, so it still needs retargeting to the 0 A.D. skeleton. Least like our armoured hoplite. |
| 5 | [Spartan warrior - 3d printable](https://sketchfab.com/3d-models/8e613f9755374f0ba3a56ad52a7a4ac4) | Andywoodhead | 744k | no | **no** (a print sculpt) | 119 | A strong heroic sculpt, useful as a body or armour bake source only. |

Also useful as parts (CC BY): [Hoplite equipment](https://sketchfab.com/3d-models/88b7941419b34c69a4d5968082d64adf) (daraenor, 8k: aspis, spear) and the CC BY helmet models ("Bronze Hoplite Helmet" by azamat.abdukahhorovich, "PBR Hoplite Helmet" by ferociousindustries.matthias).

## Pick

**#1 Hoplite Warrior (caseydedore, CC BY 4.0).** It's the only free candidate that already looks like our Spearman's kit and colours (bronze, crimson, crest and aspis) at a game-friendly 59k triangles. The plan:
- decimate to 10k and 3k for the two LODs;
- fit it to the 0 A.D. rest pose;
- transfer the skin weights from the 0 A.D. mesh;
- re-parent the spear, shield and helmet as rigid props;
- keep the round-6 clips unchanged.

Licence: CC BY 4.0 is compatible with a public repo. It needs the credit "Hoplite Warrior by caseydedore (Sketchfab), CC BY 4.0" in PROVENANCE.md and in the GLB's extras. Combined with the 0 A.D. skeleton (CC BY-SA 3.0), the result stays CC BY-SA.

Blocker: downloading it needs a Sketchfab login, which only Sam can do. One free account, then "Download 3D model", and put the glTF or FBX on the Mac at `~/LegatumRuns/anim-pilot/premium-source/`.

## Paid (for reference; nothing bought)

1. [Spartan Hoplite by RyanReos](https://sketchfab.com/3d-models/8c9f6bd9daab4a78b941ed389e142a55): $31, 163k tris, 1,007 likes. AAA-quality and realistic: a crested Corinthian helmet, a bare chest with straps and a cloak. Sketchfab "Standard" licence, which allows use in commercial games and derivative works, including rendered sprites and a shipped game asset. It does **not** allow redistributing the model files as such, so the source files can't sit in a public open-source repo. It's also further from our painted, armoured look.
2. A second paid option wasn't verified in the time-box. Typical CGTrader and TurboSquid royalty-free licences have the same limit as Sketchfab Standard: shipping in a game is fine, but the source files can't go in a public repo.
