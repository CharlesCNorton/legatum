//! Gene `rome_found_now` (with `roman_founders`): Hard Rome turns every veteran into a city.
//!
//! Rome has no Settlers: a full-health melee unit of level 1 or higher founds a city, and the
//! unit is the whole price. The older founding path sent at most one veteran a turn, only
//! after the opening march, only below six cities and only while the army outnumbered the
//! cities, and it put each veteran through the Settler's site search (quality floors, trip
//! and army-near gates). A veteran that failed any of those went back to the army and was
//! parked as a guard. This pass replaces that path:
//! - **who**: every full-health melee veteran without an order, except the garrison of a city
//!   with an at-war unit within `GARRISON_ALARM` hexes, a unit a live siege still needs, and
//!   the Colonia's reserved founder (gene `rome_colonia`).
//! - **where**: the known legal site it reaches soonest (any land the rules allow, so cities
//!   pack at the minimum spacing), the better land first among equals. Only a site an at-war
//!   army in view could take straight back is left out.
//! - **commitment**: the chosen site is remembered (`CampaignMemory::rome_found_sites`) and
//!   kept until the unit founds there or the site stops being legal, reachable or holdable,
//!   so a veteran never trades sites back and forth.
//! - **claims**: the pass runs before the military passes, so guard, garrison and staging
//!   passes find the veteran already ordered.
//! - **wounded**: a wounded veteran is a city waiting on its health. It rests, or steps out of
//!   reach (gene `roman_veteran_retreat`), at any city count and during the opening march; a
//!   siege keeps it only above `SIEGE_MIN_HP`, and a fallen enemy city in reach is entered.
//! - **replacements**: melee is trained for the next founders at any city count
//!   (`production.rs`).
//!
//! Only the fogged view enters: known tiles, known cities and visible units.

use crate::analysis::UNREACHABLE;
use crate::scripted::Planner;
use legatum_core::view::UnitView;
use legatum_core::{Faction, Hex, Order, UnitClass, UnitId, data};

/// A site further than this many turns' walk is left to a later turn's view.
const MAX_TRAVEL_TURNS: i32 = 8;
/// A veteran standing in an own city stays while an at-war unit is within this many hexes.
const GARRISON_ALARM: i32 = 2;
/// A site whose fresh city the visible at-war army would take this often (percent) is left out.
const MAX_FRESH_CITY_LOSS: i32 = 50;
/// A wounded veteran below this many HP leaves even a siege that still needs it.
const SIEGE_MIN_HP: i32 = 50;

/// Why a veteran stays a soldier this turn (`Planner::rome_founder_kept`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Kept {
    /// Locked in a captured city until Peace (`rules::occupation`).
    Lock,
    /// Gene `rome_colonia`: reserved for the Colonia Victrix.
    Colonia,
    /// The unit inside one of our cities with an at-war unit in view beside it.
    Garrison,
    /// A siege whose capture still needs it.
    Siege,
}

impl Planner<'_> {
    /// Gene `rome_found_now` is on for this (Hard Roman) planner.
    pub(crate) fn rome_found_now(&self) -> bool {
        self.faction == Faction::Rome
            && self.hard_defense()
            && self.decisions.roman_founders > 0
            && self.decisions.rome_found_now > 0
    }

    /// A melee unit the rules let found a city this turn.
    fn rome_veteran(u: &UnitView) -> bool {
        u.level >= 1 && u.hp == data::UNIT_HP && data::unit_class(u.kind) == Some(UnitClass::Melee)
    }

    /// The veteran is the unit inside one of our cities and an at-war unit is in view within
    /// `GARRISON_ALARM` hexes of it: the city keeps its defender.
    fn rome_garrison_alarm(&self, u: &UnitView) -> bool {
        let v = self.view();
        self.ctx.own_cities.iter().any(|c| c.pos == u.pos)
            && self.ctx.threat_units.iter().any(|e| {
                e.military
                    && !e.owner.is_barbarian()
                    && v.at_war(v.me, e.owner)
                    && e.pos.distance(u.pos) <= GARRISON_ALARM
            })
    }

    /// Why `u` keeps its place in the army this turn, or None when it may found.
    pub(crate) fn rome_founder_kept(&self, u: &UnitView) -> Option<Kept> {
        if u.occupation_lock.is_some() {
            return Some(Kept::Lock);
        }
        if self.colonia_reserved(u) {
            return Some(Kept::Colonia);
        }
        if self.rome_garrison_alarm(u) {
            return Some(Kept::Garrison);
        }
        // Gene `rome_opening_march`: the opening siege keeps the units at its walls.
        if let Some(city) = self.rome_opening_city()
            && self.view().at_war(self.view().me, city.owner)
            && u.pos.distance(city.pos) <= 3
        {
            return Some(Kept::Siege);
        }
        // Gene `roman_finish_siege`: a capture that forecasts only with this unit keeps it.
        if let Some((city, ids)) = self.roman_live_siege()
            && ids.contains(&u.id)
        {
            let rest: Vec<UnitId> = ids.iter().copied().filter(|id| *id != u.id).collect();
            if !self.roman_capture_holds(&city, &rest) {
                return Some(Kept::Siege);
            }
        }
        None
    }

    /// A wounded veteran is a city waiting on its health: whether `u` (wounded, level 1 or
    /// higher) fights on this turn instead of resting or stepping out of reach. A siege keeps
    /// it only above `SIEGE_MIN_HP`; a fallen enemy city within its move is still entered.
    pub(crate) fn rome_wounded_fights_on(&self, u: &UnitView) -> bool {
        let v = self.view();
        if self.ctx.enemy_cities.iter().any(|c| {
            c.visible
                && c.hp <= 0
                && v.at_war(v.me, c.owner)
                && c.pos.distance(u.pos) <= u.max_moves.max(1)
        }) {
            return true;
        }
        match self.rome_founder_kept(u) {
            Some(Kept::Siege) => u.hp >= SIEGE_MIN_HP,
            Some(_) => true,
            None => false,
        }
    }

    /// Send every free veteran to found: on its tile when that is its site, else one march
    /// closer to the site it is committed to.
    pub(crate) fn plan_rome_found_now(&mut self) {
        if !self.rome_found_now() || self.turns_remaining() <= 8 {
            return;
        }
        let v = self.view();
        let alive: Vec<UnitId> = self.ctx.own_units.iter().map(|u| u.id).collect();
        self.campaigns
            .rome_found_sites
            .retain(|id, _| alive.contains(id));
        let mut veterans: Vec<&UnitView> = self
            .ctx
            .own_units
            .iter()
            .copied()
            .filter(|u| Self::rome_veteran(u) && !self.has_acted(u.id))
            .collect();
        if veterans.is_empty() {
            return;
        }
        veterans.sort_by_key(|u| u.id);
        let gap = v.rule_experiments.min_city_gap(v.faction_of(v.me));
        // Every tile the rules, as far as we know them, let us found on and that the visible
        // at-war army would not take straight back.
        let open: Vec<bool> = (0..v.tiles.len())
            .map(|i| {
                let h = self.ctx.hex_at(i);
                legatum_core::settlement::known_legal_site(v, h)
                    && !self.enemy_war_tile(h)
                    && self.rome_fresh_city_loss(h) < MAX_FRESH_CITY_LOSS
            })
            .collect();
        for u in veterans {
            if self.rome_founder_kept(u).is_some() {
                continue;
            }
            let field = self.ctx.distance_field(u.pos, true);
            let moves = u.max_moves.max(1);
            let free = |h: Hex| !self.settle_targets.iter().any(|t| t.distance(h) <= gap);
            let usable = |h: Hex| {
                v.index(h)
                    .is_some_and(|i| open[i] && field[i] != UNREACHABLE && free(h))
            };
            // Its own tile ends the walk at once; else the remembered site while it stands.
            let held = Some(u.pos).filter(|h| usable(*h)).or_else(|| {
                self.campaigns
                    .rome_found_sites
                    .get(&u.id)
                    .copied()
                    .filter(|h| usable(*h))
            });
            let site = held.or_else(|| {
                (0..v.tiles.len())
                    .filter(|&i| open[i] && field[i] != UNREACHABLE)
                    .map(|i| (i, (field[i] + moves - 1) / moves))
                    .filter(|&(i, turns)| turns <= MAX_TRAVEL_TURNS && free(self.ctx.hex_at(i)))
                    .min_by_key(|&(i, turns)| {
                        (
                            turns,
                            std::cmp::Reverse(self.ctx.site_score[i].unwrap_or(0)),
                            i,
                        )
                    })
                    .map(|(i, _)| self.ctx.hex_at(i))
            });
            let Some(site) = site else {
                self.campaigns.rome_found_sites.remove(&u.id);
                continue;
            };
            self.campaigns.rome_found_sites.insert(u.id, site);
            self.settle_targets.push(site);
            self.rome_founders_now.insert(u.id);
            if site == u.pos {
                self.unit_order(u.id, Order::FoundCity { unit: u.id });
            } else {
                self.mil_dest.insert(site);
                self.unit_order(
                    u.id,
                    Order::MoveUnit {
                        unit: u.id,
                        to: site,
                    },
                );
            }
        }
    }

    /// Percent chance a city founded at `h` this turn falls to the at-war units in view.
    fn rome_fresh_city_loss(&self, h: Hex) -> i32 {
        self.fresh_city_loss(h, true)
    }
}

#[cfg(test)]
#[path = "rome_found_now_tests.rs"]
mod tests;
