# City names go in list order (2026-11-22)

Each empire used to start naming at a seeded random place in its faction list (`rng::purpose::NAMES`), and the lists held 6 to 20 names. So a Roman capital could be Ostia or Capua, and a wide empire ran out into "Sparta Colony 11". Sam asked why Rome's capital wasn't Rome and for more names than anyone could found.

Rules 56: names go in list order, capital first (`rules/city_names.rs`, 60 to 75 real cities a faction, none shared between factions, tested), then "New <name>", then "<Faction> Colony N". The `NAMES` stream number is retired, not reused. City names are game state, so tapes recorded before rules 56 name their cities differently on replay.
