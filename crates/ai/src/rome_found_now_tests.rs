use super::*;
use crate::fixture::{ENEMY, ME, ViewBuilder, planner};
use legatum_core::view::PlayerView;
use legatum_core::{AiDifficulty, UnitKind};

const HOME: Hex = Hex::new(10, 8);

/// A Hard Rome with `cities` cities in a row four hexes apart (the tightest legal spacing),
/// the first at `HOME`, each with a level-0 guard inside.
fn rome(cities: u32) -> ViewBuilder {
    let mut b = ViewBuilder::new(48, 24).faction(Faction::Rome);
    for i in 0..cities {
        let pos = Hex::new(HOME.q + 4 * i as i32, HOME.r);
        b = b
            .city(i + 1, ME, pos, 3)
            .unit(100 + i, ME, UnitKind::Spearman, pos);
    }
    b
}

fn veteran(b: ViewBuilder, id: u32, pos: Hex, hp: i32) -> ViewBuilder {
    let mut v = b.unit_hp(id, ME, UnitKind::Spearman, pos, hp).build();
    let u = v.units.iter_mut().find(|u| u.id == UnitId(id)).unwrap();
    u.level = 1;
    u.xp = Some(20);
    ViewBuilder { view: v }
}

fn hard(v: &PlayerView, gene: i32) -> Planner<'_> {
    let mut p = planner(v, 7);
    p.difficulty = AiDifficulty::Hard;
    p.decisions.roman_founders = 1;
    p.decisions.roman_soldier_route = 1;
    p.decisions.rome_colonia = 0;
    p.decisions.rome_found_now = gene;
    p
}

fn founds(p: &Planner<'_>, unit: u32) -> bool {
    p.orders.contains(&Order::FoundCity { unit: UnitId(unit) })
}

fn walks(p: &Planner<'_>, unit: u32) -> Option<Hex> {
    p.orders.iter().find_map(|o| match o {
        Order::MoveUnit { unit: id, to } | Order::MoveUnitPath { unit: id, to, .. }
            if *id == UnitId(unit) =>
        {
            Some(*to)
        }
        _ => None,
    })
}

fn legal(v: &PlayerView, h: Hex) -> bool {
    legatum_core::settlement::known_legal_site(v, h)
}

/// A legal site exactly four hexes below the first city, and one below the third.
fn sites(v: &PlayerView) -> (Hex, Hex) {
    let (a, b) = (
        Hex::new(HOME.q, HOME.r + 4),
        Hex::new(HOME.q + 8, HOME.r + 4),
    );
    assert!(legal(v, a) && legal(v, b));
    assert!(a.distance(b) > 3);
    (a, b)
}

#[test]
fn every_veteran_founds_in_the_same_turn_at_any_city_count() {
    // Seven cities, seven guards and two veterans: the old path stops at six cities, sends
    // one founder a turn and needs more army than cities.
    let base = rome(7).build();
    let (a, b) = sites(&base);
    let v = veteran(veteran(rome(7), 1, a, 100), 2, b, 100).build();
    let mut on = hard(&v, 1);
    on.plan_settlers();
    assert!(founds(&on, 1) && founds(&on, 2), "{:?}", on.orders);
    let mut off = hard(&v, 0);
    off.plan_settlers();
    assert!(!founds(&off, 1) && !founds(&off, 2), "{:?}", off.orders);
}

#[test]
fn a_veteran_off_a_site_walks_to_the_nearest_one_and_keeps_it() {
    // One hex short of the tight sites beside the city: it takes one a single march away.
    let base = rome(2).build();
    let (a, _) = sites(&base);
    let start = Hex::new(a.q, a.r - 1);
    assert!(!legal(&base, start));
    let v = veteran(rome(2), 1, start, 100).build();
    let mut p = hard(&v, 1);
    p.plan_settlers();
    let to = walks(&p, 1).expect("a march to a site");
    assert!(legal(&v, to) && start.distance(to) <= 2, "{to:?}");
    assert_eq!(p.campaigns.rome_found_sites.get(&UnitId(1)), Some(&to));
    assert!(p.rome_founders_now.contains(&UnitId(1)));
    // Next turn another site is just as near: the remembered one stands.
    let other = start
        .neighbors()
        .into_iter()
        .find(|h| *h != to && legal(&v, *h))
        .expect("a second site beside it");
    let mut again = hard(&v, 1);
    again.campaigns.rome_found_sites.insert(UnitId(1), other);
    again.plan_settlers();
    assert_eq!(walks(&again, 1), Some(other));
}

#[test]
fn a_remembered_site_that_stops_being_legal_is_replaced() {
    let base = rome(2).build();
    let (a, _) = sites(&base);
    let start = Hex::new(a.q, a.r - 1);
    let v = veteran(rome(2), 1, start, 100).build();
    let mut p = hard(&v, 1);
    // A tile inside the first city's spacing: no longer a site.
    let stale = Hex::new(HOME.q, HOME.r + 2);
    assert!(!legal(&v, stale));
    p.campaigns.rome_found_sites.insert(UnitId(1), stale);
    p.plan_settlers();
    let to = walks(&p, 1).expect("a march to a site");
    assert!(to != stale && legal(&v, to), "{to:?}");
}

#[test]
fn two_veterans_never_take_sites_inside_each_others_spacing() {
    let base = rome(2).build();
    let (a, _) = sites(&base);
    let beside = a.neighbors()[0];
    assert!(legal(&base, beside));
    let v = veteran(veteran(rome(2), 1, a, 100), 2, beside, 100).build();
    let mut p = hard(&v, 1);
    p.plan_settlers();
    assert!(founds(&p, 1), "{:?}", p.orders);
    assert!(!founds(&p, 2), "found orders within spacing all fail");
    let to = walks(&p, 2).expect("the second veteran walks on");
    assert!(to.distance(a) > 3 && legal(&v, to), "{to:?}");
}

#[test]
fn the_garrison_of_a_city_under_attack_and_a_wounded_veteran_do_not_found() {
    // The veteran is the unit inside the city and an at-war Spearman stands two hexes away.
    let enemy = Hex::new(HOME.q + 2, HOME.r);
    let v = veteran(
        ViewBuilder::new(48, 24)
            .faction(Faction::Rome)
            .city(1, ME, HOME, 3)
            .unit(50, ENEMY, UnitKind::Spearman, enemy),
        1,
        HOME,
        100,
    )
    .build();
    assert!(v.at_war(ME, ENEMY));
    let mut p = hard(&v, 1);
    assert_eq!(p.rome_founder_kept(&v.units[1]), Some(Kept::Garrison));
    p.plan_settlers();
    assert!(!p.rome_founders_now.contains(&UnitId(1)));
    assert!(!founds(&p, 1) && walks(&p, 1).is_none(), "{:?}", p.orders);
    // The rules refuse a wounded founder: it is not sent.
    let base = rome(2).build();
    let (a, _) = sites(&base);
    let v = veteran(rome(2), 1, a, 60).build();
    let mut p = hard(&v, 1);
    p.plan_settlers();
    assert!(!founds(&p, 1), "{:?}", p.orders);
}

#[test]
fn a_wounded_veteran_leaves_a_siege_below_half_health_but_not_a_fallen_city() {
    // The opening siege keeps a lightly wounded veteran at the walls, not a badly hurt one.
    let rival = Hex::new(HOME.q + 8, HOME.r);
    let at = Hex::new(rival.q - 1, rival.r);
    for (hp, city_hp, stays) in [(70, 100, true), (40, 100, false), (40, 0, true)] {
        let mut v = veteran(
            ViewBuilder::new(48, 24)
                .faction(Faction::Rome)
                .city(1, ME, HOME, 3)
                .city(5, ENEMY, rival, 3),
            1,
            at,
            hp,
        )
        .build();
        v.cities.iter_mut().find(|c| c.pos == rival).unwrap().hp = city_hp;
        let mut p = hard(&v, 1);
        p.decisions.rome_opening_march = 1;
        p.campaigns.rome_opening_target = Some(legatum_core::CityId(5));
        assert!(p.rome_opening_active());
        let u = v.units.iter().find(|u| u.id == UnitId(1)).unwrap();
        assert_eq!(p.rome_founder_kept(u), Some(Kept::Siege));
        assert_eq!(p.rome_wounded_fights_on(u), stays, "hp {hp} city {city_hp}");
    }
}

#[test]
fn replacement_melee_is_trained_past_six_cities_only_with_the_gene() {
    let melee_orders = |gene: i32| {
        let v = rome(7).build();
        let mut p = hard(&v, gene);
        p.plan_cities();
        p.orders
            .iter()
            .filter(|o| {
                matches!(o, Order::SetProduction {
                    item: legatum_core::ProductionItem::Unit { unit },
                    ..
                } if data::unit_class(*unit) == Some(UnitClass::Melee))
            })
            .count()
    };
    let (off, on) = (melee_orders(0), melee_orders(1));
    assert!(on > off, "melee builds: gene off {off}, on {on}");
}
