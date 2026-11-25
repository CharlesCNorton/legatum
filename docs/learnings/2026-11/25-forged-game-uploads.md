# Forged game uploads got past the shape check (2026-11-25)

On 2026-11-25, between 16:21 and 16:27 UTC, 99 hand-made records reached the games bucket: engine names
such as "seedtest" and "PENTESTPROBE", factions the game does not have (Carthage, Persia, Greece, Macedon),
and game ids whose start time was 2005 or late 2025, so they were stored under other months
(`games/2026-01/`, `2026-10/`, `2026-12/`). The Worker checked only that names were plain words and that
`created_at` was a valid time.

- The per-address cap (50 new games per UTC day) was working: the Quota object's request count matched the
  number of new games. More than 50 forged records means more than one address, so the cap alone cannot stop
  a determined sender; it only bounds each one.
- The fix is to accept only what the game writes: known factions and difficulties (`infra/games/src/names.ts`,
  kept equal to `Faction::ALL` by a core test), a 40-digit engine commit, and a game-id start time after
  launch, not in the future, and within a day of `created_at`.
- The analysis job already ignores records whose engine is not a trusted commit, so forged records never
  reached a model review; they still show up in raw counts read from the listing (filter on a 40-hex engine).
