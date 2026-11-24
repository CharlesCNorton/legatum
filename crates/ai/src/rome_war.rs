//! Gene `rome_endless_war`: Hard Rome keeps conquering after its opening march.
//!
//! Rome grows only by taking cities and by founding with promoted soldiers, so a Rome that
//! stops fighting stops growing. After the opening window the gene keeps one city as the
//! campaign target at all times: the city already being worn down, else the retained target
//! while it has no Walls, else the nearest open city of an enemy already at War, else the
//! nearest open city of a neighbour it may declare on. The melee army gathers three strong
//! near the target, then every unit beside it strikes on the same turn, each turn, without
//! waiting for a capture forecast (one counterattack is shared between the attackers, and a
//! city struck or flanked each turn does not heal). Rome refuses Peace with the target's
//! owner unless it is losing (an own city about to fall, or an army less than half the
//! enemy's), keeps the cities it takes, and the capital trains melee while the army is
//! small. Level 1 fights one war at a time; level 2 refuses Peace with every enemy and opens
//! up to three wars without waiting for Peace. Everything reads the seat's `PlayerView`.
use crate::scripted::Planner;
use legatum_core::view::{CityView, UnitView};
use legatum_core::{AiDifficulty, Faction, Hex, Order, ProductionItem, UnitClass, data};

/// The last turn of the opening march (`rome_opening.rs`); the war continues after it.
const OPENING_TURNS: u32 = 40;
/// Melee units that make a storm: the group strikes once this many can reach the city.
const STORM_GROUP: usize = 3;
/// A unit below this HP neither joins a storm nor marches; the recovery passes take it.
const STORM_MIN_HP: i32 = 40;
/// The army gathers within this distance of the target before it closes in.
const GATHER_RADIUS: i32 = 4;
/// The capital trains melee below this many living melee units.
const HEALTHY_ARMY: usize = 8;
/// A unit this likely to die in the strike sits it out.
const STORM_MAX_LOSS: u32 = 30;
/// An enemy army this close to an own city keeps the soldiers beside that city home.
const HOME_ALARM: i32 = 4;
/// A target further than this from every own city is left to the ordinary plan.
const TARGET_REACH: i32 = 14;
/// Wars Rome keeps open at once at gene level 2 (level 1: one).
const MAX_WARS: usize = 3;

impl Planner<'_> {
    pub(crate) fn rome_endless_war(&self) -> bool {
        self.faction == Faction::Rome
            && self.difficulty == AiDifficulty::Hard
            && self.decisions.rome_endless_war > 0
    }

    /// The campaign target after the opening window.
    pub(crate) fn rome_war_city(&self) -> Option<&CityView> {
        if !self.rome_endless_war() || self.view().turn <= OPENING_TURNS {
            return None;
        }
        let id = self.campaigns.rome_opening_target?;
        let v = self.view();
        v.cities
            .iter()
            .find(|city| city.id == id && !v.same_team(v.me, city.owner))
    }

    /// The city Rome's melee army marches on: the opening's, then the endless war's.
    pub(crate) fn rome_march_city(&self) -> Option<&CityView> {
        self.rome_opening_city().or_else(|| self.rome_war_city())
    }

    fn rome_war_fit(&self) -> Vec<&UnitView> {
        self.rome_opening_melee()
            .into_iter()
            .filter(|u| u.hp >= STORM_MIN_HP)
            .collect()
    }

    /// Three fit melee units have gathered near the city.
    pub(crate) fn rome_war_ready(&self, city: &CityView) -> bool {
        self.rome_war_fit()
            .iter()
            .filter(|u| u.pos.distance(city.pos) <= GATHER_RADIUS)
            .count()
            >= STORM_GROUP
    }

    /// The declaration gate for the marching target, by phase.
    pub(crate) fn rome_march_ready(&self, city: &CityView) -> bool {
        if self.rome_opening_active() {
            self.rome_opening_ready(city)
        } else {
            self.rome_war_ready(city)
        }
    }

    /// Distance from the army (its three nearest fit melee units) and from home.
    fn rome_war_distance(&self, target: Hex) -> i32 {
        let mut units: Vec<i32> = self
            .rome_war_fit()
            .iter()
            .map(|u| u.pos.distance(target))
            .collect();
        units.sort_unstable();
        let army: i32 = units.iter().take(STORM_GROUP).sum();
        army + 2 * self.rome_opening_distance(target).min(100)
    }

    pub(crate) fn choose_rome_war(&mut self) {
        if !self.rome_endless_war() || self.view().turn <= OPENING_TURNS {
            return;
        }
        let v = self.view();
        let melee = self.rome_opening_melee();
        // A new neighbour is chosen only when no enemy at War has an open city in reach, and
        // only below the gene's limit of open wars. Level 2 does not wait for Peace first.
        let wars = v
            .players
            .iter()
            .filter(|p| p.alive && p.team != v.team && v.teams_at_war(v.team, p.team))
            .count();
        let candidates: Vec<&CityView> = v
            .cities
            .iter()
            .filter(|city| {
                !city.owner.is_barbarian()
                    && !v.same_team(v.me, city.owner)
                    && !city.walls
                    && (v.at_war(v.me, city.owner)
                        || (wars < self.rome_max_wars()
                            && crate::opportunity::legal_declaration(v, v.team_of(city.owner))))
                    && self.rome_opening_distance(city.pos) <= TARGET_REACH
                    && melee.iter().any(|u| {
                        self.ctx.reachable(u.pos, city.pos)
                            || city
                                .pos
                                .ring(3)
                                .iter()
                                .any(|staging| self.ctx.reachable(u.pos, *staging))
                    })
            })
            .collect();
        // A city already worn down with two of ours beside it is finished first.
        let wounded = candidates
            .iter()
            .copied()
            .filter(|city| {
                v.at_war(v.me, city.owner)
                    && city.visible
                    && city.hp < city.max_hp
                    && melee
                        .iter()
                        .filter(|u| u.pos.distance(city.pos) <= 2)
                        .count()
                        >= 2
            })
            .min_by_key(|city| (city.hp, city.id));
        let prior = self
            .campaigns
            .rome_opening_target
            .and_then(|id| candidates.iter().copied().find(|c| c.id == id));
        let soft = |city: &CityView| {
            // Sparta's and the Mongols' armies punish a melee swarm: last among new wars.
            v.players.iter().any(|p| {
                p.id == city.owner && matches!(p.faction, Faction::Sparta | Faction::Mongols)
            })
        };
        let selected = wounded.or(prior).or_else(|| {
            candidates.iter().copied().min_by_key(|city| {
                let at_war = v.at_war(v.me, city.owner);
                (
                    !at_war,
                    !at_war && soft(city),
                    city.visible
                        && self
                            .ctx
                            .enemy_units
                            .iter()
                            .any(|u| u.military && u.pos == city.pos),
                    self.rome_war_distance(city.pos),
                    city.id,
                )
            })
        });
        match selected {
            Some(city) => self.commit_rome_target(city, "Roman endless war"),
            // No open city in reach: the ordinary plan decides (it may besiege Walls).
            None => self.campaigns.rome_opening_target = None,
        }
    }

    /// A veteran that belongs to this turn's storm stays a soldier.
    pub(crate) fn rome_storming(&self, u: &UnitView) -> bool {
        self.rome_endless_war()
            && self.rome_march_city().is_some_and(|city| {
                self.view().at_war(self.view().me, city.owner)
                    && u.pos.distance(city.pos) <= 2
                    && u.hp >= STORM_MIN_HP
                    && (city.hp < city.max_hp || self.rome_war_ready(city))
            })
    }

    /// Every fit melee unit that reaches the open target strikes it together.
    pub(crate) fn rome_storm(&mut self, army: &[&UnitView]) {
        if !self.rome_endless_war() {
            return;
        }
        let Some(city) = self.rome_march_city() else {
            return;
        };
        let v = self.view();
        if !v.at_war(v.me, city.owner) || city.walls || !city.visible {
            return;
        }
        let (target, city_hp, max_hp) = (city.pos, city.hp, city.max_hp);
        let garrison = self
            .ctx
            .enemy_units
            .iter()
            .any(|u| u.military && u.pos == target);
        let mut group: Vec<&UnitView> = self
            .free(army)
            .into_iter()
            .filter(|u| {
                data::unit_class(u.kind) == Some(UnitClass::Melee)
                    && u.hp >= STORM_MIN_HP
                    && self.reaches_this_turn(u, target)
                    && self
                        .melee_forecast(u, target)
                        .is_some_and(|f| f.loss_chance <= STORM_MAX_LOSS)
            })
            .collect();
        group.sort_by_key(|u| (std::cmp::Reverse(u.hp), u.id));
        if city_hp <= 0 && !garrison {
            // An empty fallen city: a recruit walks in (the occupation lock holds the unit
            // that takes a city there, and a veteran is worth a founded city), healthiest first.
            if let Some(u) = group
                .iter()
                .min_by_key(|u| (u.level, std::cmp::Reverse(u.hp), u.id))
            {
                self.assault_attacks.insert(u.id);
                self.unit_order(
                    u.id,
                    Order::MoveUnit {
                        unit: u.id,
                        to: target,
                    },
                );
            }
            return;
        }
        if city_hp <= 0 {
            // The garrison of a fallen city fights as a unit. Charge it only to kill it this
            // turn or at an even trade; otherwise hold the ring so the city cannot heal.
            let (dealt, taken) = group
                .iter()
                .filter_map(|u| self.melee_forecast(u, target))
                .fold((0, 0), |(dealt, taken), f| {
                    (
                        dealt + f.expected_damage_to_defender,
                        taken + f.expected_damage_to_attacker,
                    )
                });
            let garrison_hp = self
                .ctx
                .enemy_units
                .iter()
                .filter(|u| u.military && u.pos == target)
                .map(|u| u.hp)
                .max()
                .unwrap_or(0);
            if group.is_empty() || (dealt < garrison_hp && dealt < taken) {
                return;
            }
        } else {
            // Three start a storm; two continue one, or start it when a third is a step
            // behind; one keeps a city that is nearly down from healing.
            let behind = self
                .rome_opening_melee()
                .iter()
                .filter(|u| u.hp >= STORM_MIN_HP && u.pos.distance(target) <= 2)
                .count();
            let enough = group.len() >= STORM_GROUP
                || (group.len() >= 2 && (city_hp < max_hp || behind >= STORM_GROUP))
                || (!group.is_empty() && city_hp * 5 <= max_hp * 2);
            if !enough {
                return;
            }
        }
        self.assault_groups
            .push(group.iter().map(|u| u.id).collect());
        for u in group {
            self.assault_attacks.insert(u.id);
            self.unit_order(
                u.id,
                Order::MoveUnit {
                    unit: u.id,
                    to: target,
                },
            );
        }
    }

    /// Gather the fit melee army near the target, then close in beside it.
    pub(crate) fn march_rome_war(&mut self, army: &[&UnitView]) {
        let Some(city) = self.rome_war_city() else {
            return;
        };
        let target = city.pos;
        let v = self.view();
        let at_war = v.at_war(v.me, city.owner);
        let close = at_war && !city.walls && self.rome_war_ready(city);
        let alarmed = self.rome_alarmed_cities();
        let melee: Vec<&UnitView> = self
            .free(army)
            .into_iter()
            .filter(|u| {
                data::unit_class(u.kind) == Some(UnitClass::Melee)
                    && u.hp >= STORM_MIN_HP
                    && !alarmed.iter().any(|home| home.distance(u.pos) <= 3)
            })
            .collect();
        for unit in melee {
            if self.has_acted(unit.id) {
                continue;
            }
            // Every city keeps its last soldier.
            if self.ctx.own_cities.iter().any(|c| c.pos == unit.pos)
                && !self
                    .ctx
                    .own_units
                    .iter()
                    .any(|o| o.id != unit.id && o.military && o.pos == unit.pos)
            {
                continue;
            }
            let distance = unit.pos.distance(target);
            let radius = if close { 1 } else { 3 };
            let waits = if close {
                distance <= 1
            } else {
                (2..=GATHER_RADIUS).contains(&distance)
            };
            if waits && self.free_tile_for(unit, unit.pos) {
                self.go_to(unit, unit.pos);
                continue;
            }
            let spot = (radius..=radius + 1)
                .flat_map(|r| target.ring(r))
                .filter(|h| {
                    self.free_tile_for(unit, *h)
                        && self.ctx.reachable(unit.pos, *h)
                        && v.tile(*h).is_some_and(|tile| {
                            tile.terrain.is_some() && v.passage_allowed(v.me, unit.kind, tile.owner)
                        })
                })
                .min_by_key(|h| (h.distance(target), unit.pos.distance(*h), *h));
            if let Some(spot) = spot {
                self.go_to(unit, spot);
            }
        }
    }

    /// Own cities with an enemy army at War close by.
    fn rome_alarmed_cities(&self) -> Vec<Hex> {
        let v = self.view();
        self.ctx
            .own_cities
            .iter()
            .filter(|home| {
                let alarm = if home.is_capital { HOME_ALARM } else { 2 };
                self.ctx.enemy_units.iter().any(|e| {
                    e.military
                        && !e.owner.is_barbarian()
                        && v.at_war(v.me, e.owner)
                        && e.pos.distance(home.pos) <= alarm
                })
            })
            .map(|home| home.pos)
            .collect()
    }

    /// The capital trains the strongest melee unit while the army is small.
    pub(crate) fn rome_war_build(&self, city: &CityView) -> Option<ProductionItem> {
        if !self.rome_endless_war()
            || !city.is_capital
            || self.campaigns.rome_opening_target.is_none()
            || self.rome_opening_melee().len() >= HEALTHY_ARMY
            || self.rome_alarmed_cities().contains(&city.pos)
        {
            return None;
        }
        city.detail
            .as_ref()?
            .options
            .iter()
            .filter_map(|option| match option.item {
                ProductionItem::Unit { unit }
                    if data::unit_class(unit) == Some(UnitClass::Melee)
                        && option.resource_blocker.is_none()
                        && option.turns > 0 =>
                {
                    Some((unit, option.item))
                }
                _ => None,
            })
            .max_by_key(|(unit, _)| data::unit_stats(*unit).strength)
            .map(|(_, item)| item)
    }
}

impl Planner<'_> {
    fn rome_max_wars(&self) -> usize {
        if self.decisions.rome_endless_war >= 2 {
            MAX_WARS
        } else {
            1
        }
    }

    /// Rome is losing its war with `against`: a city of its own is about to fall, or its
    /// public army is less than half of that enemy's.
    pub(crate) fn rome_war_losing(&self, against: legatum_core::TeamId) -> bool {
        let v = self.view();
        self.collapsing()
            || crate::diplomacy::strength(v, v.team) * 2 < crate::diplomacy::strength(v, against)
    }

    /// Whether the gene decides Peace with `against`: at level 1 only for the owner of the
    /// city Rome marches on, at level 2 for every enemy.
    pub(crate) fn rome_war_holds(&self, against: legatum_core::TeamId) -> bool {
        let v = self.view();
        self.rome_endless_war()
            && v.teams_at_war(v.team, against)
            && (self.decisions.rome_endless_war >= 2
                || self
                    .rome_march_city()
                    .is_some_and(|city| v.team_of(city.owner) == against))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Knobs;
    use crate::fixture::{ENEMY, ME, ViewBuilder, off, set_armies};
    use crate::plan::PlanKind;
    use legatum_core::diplomacy::{Relation, RelationState};
    use legatum_core::{CityId, PlayerView, TeamId, UnitId, UnitKind};

    /// Rome at War after the opening window: two open enemy cities, three Spearmen forward.
    fn war_view() -> PlayerView {
        let mut view = ViewBuilder::new(28, 18)
            .faction(Faction::Rome)
            .city(1, ME, off(4, 8), 3)
            .city(2, ENEMY, off(10, 8), 3)
            .city(3, ENEMY, off(14, 8), 3)
            .unit(1, ME, UnitKind::Spearman, off(8, 8))
            .unit(2, ME, UnitKind::Spearman, off(8, 9))
            .unit(3, ME, UnitKind::Spearman, off(7, 8))
            .build();
        view.turn = 60;
        view.diplomacy.legacy = false;
        view.diplomacy.relations.push(Relation {
            a: TeamId(0),
            b: TeamId(2),
            state: RelationState::War,
            effective_turn: 30,
            guarantee_until: 0,
            version: 1,
            security: None,
            war_id: None,
            declarers: Vec::new(),
        });
        view
    }

    fn rome(view: &PlayerView, gene: i32) -> Planner<'_> {
        let mut planner = Planner::new(view, Knobs::for_faction(Faction::Rome), Faction::Rome, 1);
        planner.difficulty = AiDifficulty::Hard;
        planner.decisions.rome_endless_war = gene;
        planner
    }

    fn beside(view: &mut PlayerView, city: u32, units: &[u32]) {
        let at = view.cities.iter().find(|c| c.id.0 == city).unwrap().pos;
        for (unit, tile) in units.iter().zip(at.neighbors()) {
            view.units.iter_mut().find(|u| u.id.0 == *unit).unwrap().pos = tile;
        }
    }

    fn storms(planner: &Planner<'_>, city: Hex) -> Vec<UnitId> {
        planner
            .orders
            .iter()
            .filter_map(|order| match order {
                Order::MoveUnit { unit, to } if *to == city => Some(*unit),
                _ => None,
            })
            .collect()
    }

    #[test]
    fn the_war_keeps_one_open_target_after_the_opening_and_the_gene_is_off_by_default() {
        let mut view = war_view();
        let mut planner = rome(&view, 0);
        planner.choose_rome_war();
        assert_eq!(planner.campaigns.rome_opening_target, None);
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        assert_eq!(planner.campaigns.rome_opening_target, Some(CityId(2)));
        assert!(matches!(
            planner.campaigns.plan.active.as_ref().unwrap().kind,
            PlanKind::Campaign {
                target: CityId(2),
                ..
            }
        ));
        // Walls on the target: the same enemy's next open city.
        let memory = planner.campaigns.clone();
        view.cities.iter_mut().find(|c| c.id.0 == 2).unwrap().walls = true;
        let mut planner = rome(&view, 1);
        planner.campaigns = memory;
        planner.choose_rome_war();
        assert_eq!(planner.campaigns.rome_opening_target, Some(CityId(3)));
        // No open city in reach: the ordinary plan decides.
        let memory = planner.campaigns.clone();
        view.cities.iter_mut().find(|c| c.id.0 == 3).unwrap().walls = true;
        let mut planner = rome(&view, 1);
        planner.campaigns = memory;
        planner.choose_rome_war();
        assert_eq!(planner.campaigns.rome_opening_target, None);
    }

    #[test]
    fn a_city_already_worn_down_with_two_units_beside_it_is_finished_first() {
        let mut view = war_view();
        beside(&mut view, 3, &[1, 2]);
        view.cities.iter_mut().find(|c| c.id.0 == 3).unwrap().hp = 90;
        let mut planner = rome(&view, 1);
        planner.campaigns.rome_opening_target = Some(CityId(2));
        planner.choose_rome_war();
        assert_eq!(planner.campaigns.rome_opening_target, Some(CityId(3)));
    }

    #[test]
    fn three_melee_beside_the_open_target_strike_together_without_a_capture_forecast() {
        let mut view = war_view();
        beside(&mut view, 2, &[1, 2, 3]);
        let city = view.cities.iter().find(|c| c.id.0 == 2).unwrap().pos;
        let army: Vec<_> = view.units.iter().filter(|u| u.owner == ME).collect();
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        planner.rome_storm(&army);
        let mut struck = storms(&planner, city);
        struck.sort();
        assert_eq!(struck, vec![UnitId(1), UnitId(2), UnitId(3)]);
        // Gene 0 leaves the assault to the forecast-gated coordinator.
        let mut planner = rome(&view, 0);
        planner.choose_rome_war();
        planner.rome_storm(&army);
        assert!(storms(&planner, city).is_empty());
    }

    #[test]
    fn a_lone_unit_waits_for_the_army_and_a_badly_wounded_one_sits_the_strike_out() {
        let mut view = war_view();
        beside(&mut view, 2, &[1]);
        let city = view.cities.iter().find(|c| c.id.0 == 2).unwrap().pos;
        let army: Vec<_> = view.units.iter().filter(|u| u.owner == ME).collect();
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        planner.rome_storm(&army);
        assert!(storms(&planner, city).is_empty());
        let mut view = war_view();
        beside(&mut view, 2, &[1, 2, 3]);
        view.units.iter_mut().find(|u| u.id.0 == 3).unwrap().hp = STORM_MIN_HP - 1;
        view.cities.iter_mut().find(|c| c.id.0 == 2).unwrap().hp = 120;
        let army: Vec<_> = view.units.iter().filter(|u| u.owner == ME).collect();
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        planner.rome_storm(&army);
        let mut struck = storms(&planner, city);
        struck.sort();
        assert_eq!(struck, vec![UnitId(1), UnitId(2)]);
    }

    #[test]
    fn rome_refuses_peace_unless_its_army_is_far_smaller() {
        let mut view = war_view();
        set_armies(&mut view, &[(ME, 100), (ENEMY, 150)]);
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        assert_eq!(
            planner.wants_peace_why(TeamId(2)),
            (false, "Roman endless war")
        );
        set_armies(&mut view, &[(ME, 100), (ENEMY, 201)]);
        let mut planner = rome(&view, 1);
        planner.choose_rome_war();
        assert_eq!(
            planner.wants_peace_why(TeamId(2)),
            (true, "Roman endless war")
        );
    }
}
