//! Rome's goal, the Colonia Victrix (`legatum_core::goals::GoalRule::Colonia`), in the Hard AI
//! (gene `rome_colonia`, with `roman_founders`).
//!
//! A city founded by a Roman melee veteran of level `goals::COLONIA_LEVEL` (3) on a site within
//! `goals::COLONIA_BORDER_REACH` tiles of a rival's land is the Colonia: 2 VP to whoever holds it.
//! Rome's veterans found its cities, so the goal is a question of which veteran founds where:
//! - **reserve**: while the Colonia is open a level-3 veteran never founds an ordinary city, and
//!   while no unit is level 3 the most experienced level-2 melee unit is kept from founding too,
//!   so the war that earns the third level has a unit to earn it (`colonia_reserved`). Lower
//!   veterans found cities as before, so expansion is not slowed.
//! - **found**: a level-3 veteran walks to the most defensible reachable site beside a rival's
//!   border and founds there (`plan_colonia`). The city must be held: a Colonia that falls
//!   hands its captor the 2 VP, so a site is priced by its hold risk (the rival army that can
//!   reach it against ours near it, the border's war state, the distance from Rome's cities).
//!   With no such site the veteran waits as a soldier: a rival's land grows, a war moves.
//! - **hold**: the founded Colonia is garrisoned, walled and defended first, and retaken first
//!   if it falls (`goal_cities.rs`).
//!
//! Only the fogged view enters: tile owners are public on explored land
//! (`goals::known_colonia_site`), and a founder's level is its own.

use crate::scripted::Planner;
use legatum_core::settlement::settlement_candidates_with;
use legatum_core::view::UnitView;
use legatum_core::{Faction, Hex, Order, UnitClass, UnitKind, data, goals};

/// Value of the Colonia's 2 VP in the site search's currency (a held goal city, per VP).
const COLONIA_VALUE_PER_VP: i32 = 400;
/// A Colonia site further than this many turns' walk is not "reachable in reasonable time".
pub(crate) const COLONIA_MAX_TRAVEL: i32 = 12;
/// Each turn of travel keeps a level-3 veteran out of the war that made it.
const COLONIA_TRAVEL_COST: i32 = 25;
/// A site beyond this many hexes from Rome's nearest city is harder to reinforce: each hex
/// beyond adds this much hold risk (percent).
const COLONIA_HOME_REACH: i32 = 5;
const COLONIA_FAR_RISK_PER_HEX: i32 = 6;
/// Hold-risk percent above which a site is not worth founding: the expected swing is negative.
const COLONIA_MAX_RISK: i32 = 45;

impl Planner<'_> {
    /// Gene `rome_colonia`: Hard Rome pursues its goal now (open, not switched off).
    pub(crate) fn colonia_on(&self) -> bool {
        self.faction == Faction::Rome
            && self.hard_defense()
            && self.decisions.roman_founders > 0
            && self.decisions.rome_colonia > 0
            && goals::known_colonia_open(self.view())
    }

    /// Melee units of ours, with their levels.
    fn own_melee(&self) -> impl Iterator<Item = &UnitView> {
        self.ctx
            .own_units
            .iter()
            .copied()
            .filter(|u| data::unit_class(u.kind) == Some(UnitClass::Melee))
    }

    /// Gene `rome_colonia`: `u` is kept from ordinary founding. Every level-3 melee unit while
    /// the Colonia is open; while none exists, the single most experienced level-2 melee unit
    /// (highest XP, then lowest id), the one closest to earning the founder.
    pub(crate) fn colonia_reserved(&self, u: &UnitView) -> bool {
        if !self.colonia_on() || data::unit_class(u.kind) != Some(UnitClass::Melee) {
            return false;
        }
        if goals::known_colonia_founder(self.view(), u) {
            return true;
        }
        if self.own_melee().any(|m| m.level >= goals::COLONIA_LEVEL) {
            return false;
        }
        let candidate = goals::COLONIA_LEVEL - 1;
        u.level == candidate
            && self
                .own_melee()
                .filter(|m| m.level == candidate)
                .max_by_key(|m| (m.xp.unwrap_or(0), std::cmp::Reverse(m.id)))
                .is_some_and(|best| best.id == u.id)
    }

    /// Percent chance a Colonia founded at `site` is lost: the visible rival army that can reach
    /// it against our own near it, more when we are at war with the border's owner, plus its
    /// distance from Rome's nearest city. `founder` is consumed by founding, so it is not counted.
    pub(crate) fn colonia_hold_risk(&self, site: Hex, founder: legatum_core::UnitId) -> i32 {
        let v = self.view();
        let weight = |d: i32| match d {
            0..=2 => 100,
            3 => 75,
            4 => 50,
            5 => 35,
            6 => 25,
            _ => 0,
        };
        let ours: i32 = self
            .ctx
            .own_units
            .iter()
            .filter(|u| u.id != founder && u.military && u.kind != UnitKind::Scout)
            .map(|u| crate::analysis::threat_power(v, u) * weight(u.pos.distance(site)) / 100)
            .sum();
        let theirs: i32 = v
            .units
            .iter()
            .filter(|u| {
                u.military
                    && u.kind != UnitKind::Scout
                    && !u.owner.is_barbarian()
                    && !v.same_team(v.me, u.owner)
                    && !v.allied(v.me, u.owner)
            })
            .map(|u| {
                let at_war = if v.at_war(v.me, u.owner) { 2 } else { 1 };
                at_war * crate::analysis::threat_power(v, u) * weight(u.pos.distance(site)) / 100
            })
            .sum();
        // The rival whose border it is: at war, it comes for the city; much stronger, it can.
        let border_owners: Vec<_> = site
            .within(goals::COLONIA_BORDER_REACH)
            .into_iter()
            .filter_map(|h| v.tile(h).filter(|t| t.explored).and_then(|t| t.owner))
            .filter(|o| !o.is_barbarian() && !v.same_team(v.me, *o))
            .collect();
        let our_army = crate::diplomacy::strength(v, v.team).max(1);
        let chance = if border_owners.iter().any(|o| v.at_war(v.me, *o)) {
            60
        } else if border_owners
            .iter()
            .any(|o| crate::diplomacy::strength(v, v.team_of(*o)) > our_army * 3 / 2)
        {
            40
        } else {
            25
        };
        // A new city's own defence counts for a little.
        let superiority = theirs.saturating_mul(100) / (theirs + ours + 15).max(1);
        let home = self
            .ctx
            .own_cities
            .iter()
            .map(|c| c.pos.distance(site))
            .min()
            .unwrap_or(COLONIA_MAX_TRAVEL);
        let far = (home - COLONIA_HOME_REACH).max(0) * COLONIA_FAR_RISK_PER_HEX;
        (chance * superiority / 100 + far).clamp(0, 95)
    }

    /// The best Colonia site for founder `s`: a known legal site beside a rival's border, safe
    /// to found on (the Settler search's own hazard gates), within `COLONIA_MAX_TRAVEL` turns,
    /// whose hold risk leaves the 2 VP worth more than the swing they risk. Returns the value,
    /// the site and its travel turns.
    pub(crate) fn colonia_site(&self, s: &UnitView) -> Option<(i32, Hex, i32)> {
        let v = self.view();
        let gap = v.rule_experiments.min_city_gap(v.faction_of(self.ctx.me));
        let points = goals::spec_for(goals::GoalRule::Colonia).vp as i32;
        let mut best: Option<(i32, Hex, i32)> = None;
        for site in settlement_candidates_with(
            v,
            self.ctx.site_score.basics(),
            s,
            &self.settle_targets,
        ) {
            let h = site.pos;
            let Some(turns) = site.travel_turns else {
                continue;
            };
            if turns > COLONIA_MAX_TRAVEL
                || !goals::known_colonia_site(v, h)
                || self.enemy_war_tile(h)
                || self.enemy_army_near(h)
                || self.ctx.in_danger(h)
                || site.threats > 0
                || self.settle_targets.iter().any(|t| t.distance(h) <= gap)
                || v.units.iter().any(|u| {
                    u.owner != self.ctx.me
                        && u.kind == UnitKind::Settler
                        && u.pos.distance(h) <= v.rule_experiments.min_city_gap(v.faction_of(u.owner))
                })
                || turns + 8 >= self.turns_remaining()
                || self.campaigns.found_tried.iter().any(|&(unit, at, turn)| {
                    unit == s.id && at == h && turn + 1 == v.turn
                })
            {
                continue;
            }
            let risk = self.colonia_hold_risk(h, s.id);
            if risk > COLONIA_MAX_RISK {
                continue;
            }
            let value = points * COLONIA_VALUE_PER_VP * (100 - 2 * risk) / 100
                + site.score.max(0) / 4
                - turns * COLONIA_TRAVEL_COST;
            if value > 0 && best.is_none_or(|(b, _, _)| value > b) {
                best = Some((value, h, turns));
            }
        }
        best
    }

    /// Gene `rome_colonia`: send this turn's Colonia founder. Of the full-health level-3 melee
    /// units free to leave (not the last defender of a threatened city, not a live siege's
    /// unit), the one with the best site founds there, or walks toward it. Returns whether a
    /// founder was ordered.
    pub(crate) fn plan_colonia(&mut self) -> bool {
        if !self.colonia_on() {
            return false;
        }
        let siege = self.roman_live_siege();
        let founders: Vec<UnitView> = self
            .own_melee()
            .filter(|u| {
                goals::known_colonia_founder(self.view(), u)
                    && u.hp == data::UNIT_HP
                    && !self.has_acted(u.id)
                    && self.roman_unit_can_leave(u)
                    && siege.as_ref().is_none_or(|(city, ids)| {
                        !ids.contains(&u.id) || {
                            let rest: Vec<_> =
                                ids.iter().copied().filter(|id| *id != u.id).collect();
                            self.roman_capture_holds(city, &rest)
                        }
                    })
            })
            .cloned()
            .collect();
        let Some((s, (_, site, _))) = founders
            .iter()
            .filter_map(|u| self.colonia_site(u).map(|best| (u, best)))
            .max_by_key(|(u, (value, _, _))| (*value, std::cmp::Reverse(u.id)))
        else {
            return false;
        };
        let s = s.clone();
        self.colonia_founder = Some(s.id);
        self.settle_targets.push(site);
        if site == s.pos {
            let turn = self.view().turn;
            self.campaigns
                .found_tried
                .retain(|&(unit, _, t)| unit != s.id && t + 1 >= turn);
            self.campaigns.found_tried.push((s.id, s.pos, turn));
            self.unit_order(s.id, Order::FoundCity { unit: s.id });
        } else {
            self.escort_sites.push(site);
            self.move_settler(&s, site);
        }
        true
    }
}

#[cfg(test)]
#[path = "goal_colonia_tests.rs"]
mod tests;
