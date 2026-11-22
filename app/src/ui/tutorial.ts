// The first-game tutorial: a short, skippable walk through the basics (select, move, build, research,
// end the turn, found a city, the VP race). Each step finishes when the player does the thing it asks,
// read from their own fog-filtered view and planned orders, so it works from turn 1 or mid-game.
// Steps never change the game: they live in this browser, not in the save.
// The `tutorial-gate` check (tools/gates/tutorial.py) flags any branch that changes the mechanics or
// controls these steps teach, so the copy here stays true.
import { create } from 'zustand';
import { BARBARIAN } from '../barbarians';
import { itemName } from '../data';
import { atWar, barbariansSpareMe } from '../diplomacy';
import { empireTitle } from '../empires';
import { effectiveProduction, effectiveResearchQueue } from '../orders';
import { isFounderCandidate } from '../settlement';
import { pendingDecisions } from '../turnFlow';
import { HOLD_TURNS } from '../victoryHold';
import type { Order, OrderError, PlayerView, UnitView } from '../types';
import type { GuideSection } from './guideState';

/** Storage key kept from the first-game hints, so "off" stays off for every player and test that set it. */
export const TUTORIAL_KEY = 'legatum.first-game-hints.v2';

export const STEP_IDS = ['welcome', 'production', 'research', 'select', 'move', 'others', 'endTurn', 'report',
  'settler', 'found', 'race', 'rival', 'finish'] as const;
export type StepId = typeof STEP_IDS[number];
/** Steps counted in "Step 3 of 10". The rival step comes when a rival does, so it is not counted. */
export const COUNTED_STEPS: readonly StepId[] = STEP_IDS.filter((id) => id !== 'rival' && id !== 'welcome' && id !== 'finish');

/** What a step asks the screen to do when the player presses its helper button. */
export type StepAction =
  | { kind: 'select'; target: { kind: 'unit' | 'city'; id: number } }
  | { kind: 'research' }
  | { kind: 'report' }
  | { kind: 'guide'; section: GuideSection };

/** Which control the step points at with a ring. */
export type Spotlight = 'research' | 'turn' | 'found' | 'race' | null;

export interface TutorialStep {
  id: StepId;
  title: string;
  body: string;
  /** The step ends when the player presses Next, not by playing. */
  acknowledge: boolean;
  /** A helper that does the first part for the player ("Show me"). */
  help?: { label: string; action: StepAction };
  spotlight: Spotlight;
}

export interface TutorialContext {
  view: PlayerView;
  orders: Order[];
  errors?: OrderError[];
  /** The selected unit or city, if any. */
  selection: { kind: string; id: number } | null;
  /** Human seats in this game: one means solo (End turn), more means Ready. */
  humans: number;
  touch: boolean;
  local?: Parameters<typeof pendingDecisions>[3];
}

/**
 * Values noted when a step first shows, so "end the turn" and "found a city" finish on what the player
 * does next, not on what a game in progress already has. Kept in memory: a new game or a reload
 * notes them again.
 */
export type StepMarks = Partial<Record<'endTurn' | 'found', number>>;

const own = (ctx: TutorialContext) => ({
  cities: ctx.view.cities.filter((c) => c.owner === ctx.view.me),
  units: ctx.view.units.filter((u) => u.owner === ctx.view.me),
});

const validOrders = (ctx: TutorialContext) => ctx.orders.filter((_, i) => !ctx.errors?.some((e) => e.index === i));

const MOVE_ORDERS = new Set<Order['type']>(['MoveUnit', 'MoveUnitPath', 'SetAutomation']);

function unitDecisions(ctx: TutorialContext) {
  return pendingDecisions(ctx.view, validOrders(ctx), ctx.errors ?? [], ctx.local).filter((d) => d.kind === 'unit');
}

function idleCity(ctx: TutorialContext) {
  return own(ctx).cities.find((c) => c.detail && c.detail.resistance === 0 && !effectiveProduction(validOrders(ctx), c.id, c.detail.producing));
}

function buildsSettler(ctx: TutorialContext) {
  const orders = validOrders(ctx);
  return own(ctx).cities.some((c) => {
    const item = c.detail ? effectiveProduction(orders, c.id, c.detail.producing) : null;
    return item?.kind === 'Unit' && item.unit === 'Settler';
  });
}

function founder(ctx: TutorialContext): UnitView | undefined {
  return own(ctx).units.find((u) => isFounderCandidate(ctx.view, u));
}

/** A city of yours big enough for a Settler. Rome trains no Settlers (its veterans found cities). */
function settlerCity(ctx: TutorialContext) {
  const faction = ctx.view.players.find((p) => p.id === ctx.view.me)?.faction;
  if (faction === 'Rome') return undefined;
  return own(ctx).cities.find((c) => c.population >= 2 && c.detail && c.detail.resistance === 0);
}

function rivalsInSight(view: PlayerView) {
  const enemies = new Set([...(barbariansSpareMe(view) ? [] : [BARBARIAN]), ...view.players.filter((p) => p.team !== view.team && p.alive).map((p) => p.id)]);
  return view.units.some((u) => enemies.has(u.owner)) || view.cities.some((c) => c.visible && enemies.has(c.owner));
}

function firstUnit(ctx: TutorialContext): UnitView | undefined {
  const units = own(ctx).units;
  const waiting = unitDecisions(ctx).map((d) => d.kind === 'unit' ? d.id : -1);
  return units.find((u) => waiting.includes(u.id) && u.kind === 'Scout') ?? units.find((u) => waiting.includes(u.id)) ?? units.find((u) => u.kind === 'Scout') ?? units[0];
}

/** True once the player has done what the step asks (acknowledge steps finish only by their button). */
export function stepComplete(id: StepId, ctx: TutorialContext, marks: StepMarks): boolean {
  const { cities, units } = own(ctx);
  switch (id) {
    case 'production': return cities.length > 0 && !idleCity(ctx);
    case 'research': return effectiveResearchQueue(validOrders(ctx), ctx.view.research).length > 0;
    case 'select': return ctx.selection?.kind === 'unit' && units.some((u) => u.id === ctx.selection!.id);
    case 'move': return validOrders(ctx).some((o) => MOVE_ORDERS.has(o.type)) || units.some((u) => !!u.automation);
    case 'others': return !unitDecisions(ctx).length;
    case 'endTurn': return marks.endTurn !== undefined && ctx.view.turn > marks.endTurn;
    case 'settler': return buildsSettler(ctx) || units.some((u) => u.kind === 'Settler');
    case 'found': return validOrders(ctx).some((o) => o.type === 'FoundCity') || (marks.found !== undefined && cities.length > marks.found);
    default: return false;
  }
}

/** Whether a step can be shown now. */
export function stepReady(id: StepId, ctx: TutorialContext, done: readonly StepId[]): boolean {
  const { cities, units } = own(ctx);
  const has = (s: StepId) => done.includes(s);
  switch (id) {
    case 'welcome': return true;
    case 'production': return !!idleCity(ctx);
    case 'research': return cities.length > 0 && ctx.view.research.available.length > 0;
    case 'select': case 'move': return units.length > 0;
    case 'others': return unitDecisions(ctx).length > 0;
    case 'endTurn': return true;
    case 'report': return has('endTurn');
    case 'settler': return has('report') && !!settlerCity(ctx) && !founder(ctx);
    case 'found': return has('report') && !!founder(ctx);
    case 'race': return has('report') && (ctx.view.turn >= 8 || has('found'));
    case 'rival': return has('report') && rivalsInSight(ctx.view);
    case 'finish': return has('race') && (has('found') || ctx.view.turn >= 40);
  }
}

/** The steps before this one must be done first; the later ones wait for the game to reach them. */
const LINEAR = new Set<StepId>(['welcome', 'production', 'research', 'select', 'move', 'others', 'endTurn', 'report']);

/**
 * The step to show now, and any steps the player has already done without being asked (to note as
 * done). Returns null when nothing applies yet or the tutorial is over.
 */
export function nextStep(ctx: TutorialContext, done: readonly StepId[], marks: StepMarks): { step: StepId | null; completed: StepId[] } {
  const completed: StepId[] = [];
  if (ctx.view.finished || ctx.view.players.find((p) => p.id === ctx.view.me)?.alive === false) return { step: null, completed };
  if (done.includes('finish')) return { step: null, completed };
  const all = [...done];
  for (const id of STEP_IDS) {
    if (all.includes(id)) continue;
    if (stepComplete(id, ctx, marks)) { completed.push(id); all.push(id); continue; }
    if (stepReady(id, ctx, all)) return { step: id, completed };
    if (LINEAR.has(id)) {
      // An early step that cannot apply now (no idle city, no units) is passed over, not waited on.
      if (id === 'production' || id === 'select' || id === 'move' || id === 'others') { completed.push(id); all.push(id); continue; }
      return { step: null, completed };
    }
  }
  return { step: null, completed };
}

/** The words and helper for a step, written for this player's screen. */
export function stepCopy(id: StepId, ctx: TutorialContext): TutorialStep {
  const solo = ctx.humans <= 1;
  const { cities, units } = own(ctx);
  const capital = cities.find((c) => c.is_capital) ?? cities[0];
  const faction = ctx.view.players.find((p) => p.id === ctx.view.me)?.faction;
  switch (id) {
    case 'welcome': return {
      id, acknowledge: true, spotlight: null,
      title: 'Welcome to Legatum',
      body: 'You lead an empire from its first city. Each turn you give orders to your cities and units. Then every empire’s orders happen at once. These steps walk you through your first turns.',
    };
    case 'production': {
      const city = idleCity(ctx) ?? capital;
      return {
        id, acknowledge: false, spotlight: null,
        title: `Choose what ${city?.name ?? 'your city'} builds`,
        body: ctx.touch
          ? 'Tap your city, then pick a unit or building. Production builds it over a few turns.'
          : 'Click your city on the map, then pick a unit or building. Production builds it over a few turns.',
        help: city ? { label: 'Show me', action: { kind: 'select', target: { kind: 'city', id: city.id } } } : undefined,
      };
    }
    case 'research': return {
      id, acknowledge: false, spotlight: 'research',
      title: 'Choose a technology',
      body: ctx.touch
        ? 'Tap Research at the top, then pick a technology. Your Science discovers it over a few turns.'
        : 'Click Research at the top, or press T, then pick a technology. Your Science discovers it over a few turns.',
      help: { label: 'Open Research', action: { kind: 'research' } },
    };
    case 'select': {
      const unit = firstUnit(ctx);
      return {
        id, acknowledge: false, spotlight: null,
        title: 'Select a unit',
        body: ctx.touch
          ? 'Tap one of your units on the map. Its card shows what it can do.'
          : 'Click one of your units on the map. Its card opens in the corner and shows what it can do.',
        help: unit ? { label: 'Show me', action: { kind: 'select', target: { kind: 'unit', id: unit.id } } } : undefined,
      };
    }
    case 'move': {
      const unit = firstUnit(ctx);
      return {
        id, acknowledge: false, spotlight: null,
        title: 'Move it',
        body: ctx.touch
          ? 'Tap a tile to see the path, then tap it again to go there. Long trips carry on over several turns.'
          : 'Right-click a tile to send the selected unit there. On a trackpad, click with two fingers. You can also drag from the unit to the tile.',
        help: unit && !(ctx.selection?.kind === 'unit' && units.some((u) => u.id === ctx.selection!.id))
          ? { label: 'Select a unit', action: { kind: 'select', target: { kind: 'unit', id: unit.id } } } : undefined,
      };
    }
    case 'others': {
      const next = unitDecisions(ctx)[0];
      return {
        id, acknowledge: false, spotlight: null,
        title: 'Give every unit an order',
        body: ctx.touch
          ? 'Each unit needs an order every turn. Move it, Fortify it to stand guard, or Skip it for this turn.'
          : 'Each unit needs an order every turn. Move it, press F to Fortify and stand guard, or press Space to skip this turn.',
        help: next?.kind === 'unit' ? { label: 'Next unit', action: { kind: 'select', target: { kind: 'unit', id: next.id } } } : undefined,
      };
    }
    case 'endTurn': return {
      id, acknowledge: false, spotlight: 'turn',
      title: solo ? 'End the turn' : 'Press Ready',
      body: solo
        ? `Press End turn${ctx.touch ? '' : ' at the bottom right, or Return'}. Every empire’s orders happen at once, then you plan the next turn.`
        : 'Press Ready when your orders are set. The turn happens once every player is ready.',
    };
    case 'report': return {
      id, acknowledge: true, spotlight: null,
      title: 'See what happened',
      body: ctx.touch
        ? 'The Turn report lists battles, discoveries and orders that failed. Open it from This Turn.'
        : 'The Turn report lists battles, discoveries and orders that failed. Press L to open it any time.',
      help: { label: 'Open Turn report', action: { kind: 'report' } },
    };
    case 'settler': {
      const city = settlerCity(ctx);
      return {
        id, acknowledge: false, spotlight: null,
        title: 'Build a Settler',
        body: `${city?.name ?? 'Your city'} has population 2, enough for a Settler. A Settler founds a new city, and more cities make a stronger empire.`,
        help: city ? { label: 'Show me', action: { kind: 'select', target: { kind: 'city', id: city.id } } } : undefined,
      };
    }
    case 'found': {
      const unit = founder(ctx);
      const name = unit ? itemName({ kind: 'Unit', unit: unit.kind }, faction) : 'Settler';
      return {
        id, acknowledge: false, spotlight: 'found',
        title: 'Found a new city',
        body: `Select your ${name}. The map shows good places for a city in green. Move there, then press Found City${ctx.touch ? '' : ' (B)'}.`,
        help: unit ? { label: 'Show me', action: { kind: 'select', target: { kind: 'unit', id: unit.id } } } : undefined,
      };
    }
    case 'race': return {
      id, acknowledge: true, spotlight: 'race',
      title: 'Race for victory points',
      body: `Reach your team’s VP target and hold it for ${HOLD_TURNS} turns to win. The Victory race shows every empire’s VP and how you score.`,
      help: { label: 'How to win', action: { kind: 'guide', section: 'victory' } },
    };
    case 'rival': {
      const sighted = [...ctx.view.units.map((u) => u.owner), ...ctx.view.cities.filter((c) => c.visible).map((c) => c.owner)]
        .flatMap((owner) => ctx.view.players.filter((p) => p.id === owner && p.team !== ctx.view.team && p.alive));
      const war = sighted.some((p) => atWar(ctx.view, p.id)) || (!sighted.length && !barbariansSpareMe(ctx.view));
      const name = sighted[0] && empireTitle(ctx.view, sighted[0].team);
      return {
        id, acknowledge: true, spotlight: null,
        title: 'A rival in sight',
        body: war
          ? 'You are at War with them. Before you attack, point at the target to see the battle forecast.'
          : `You are at Peace${name ? ` with ${name}` : ''}. A rival can declare War and attack in the same turn, so guard your cities.`,
        help: { label: 'How combat works', action: { kind: 'guide', section: 'combat' } },
      };
    }
    case 'finish': return {
      id, acknowledge: true, spotlight: null,
      title: 'You know the basics',
      body: 'Every rule is in How to Play, in the Menu. Good luck.',
      help: { label: 'Open How to Play', action: { kind: 'guide', section: 'turns' } },
    };
  }
}

/** Step N of M for the counted steps, or null for steps outside the count. */
export function stepNumber(id: StepId): { n: number; of: number } | null {
  const i = COUNTED_STEPS.indexOf(id);
  return i < 0 ? null : { n: i + 1, of: COUNTED_STEPS.length };
}

interface TutorialPreferences { enabled: boolean; done: StepId[] }

export function readTutorialPreferences(): TutorialPreferences {
  try {
    const raw: unknown = JSON.parse(globalThis.localStorage?.getItem(TUTORIAL_KEY) ?? 'null');
    if (raw && typeof raw === 'object') {
      const p = raw as { enabled?: unknown; tutorial?: unknown };
      const done: unknown[] = Array.isArray(p.tutorial) ? p.tutorial : [];
      return { enabled: p.enabled !== false, done: STEP_IDS.filter((id) => done.includes(id)) };
    }
  } catch { /* Unavailable or invalid storage should never prevent playing. */ }
  return { enabled: true, done: [] };
}

function savePreferences(p: TutorialPreferences) {
  try { globalThis.localStorage?.setItem(TUTORIAL_KEY, JSON.stringify({ enabled: p.enabled, seen: [], tutorial: p.done })); }
  catch { /* Keep session preferences even if storage is blocked. */ }
}

interface TutorialState extends TutorialPreferences {
  marks: StepMarks;
  resetVersion: number;
  markDone(ids: readonly StepId[]): void;
  mark(key: keyof StepMarks, value: number): void;
  setEnabled(enabled: boolean): void;
  restart(): void;
}

export const useTutorial = create<TutorialState>((set) => ({
  ...readTutorialPreferences(),
  marks: {},
  resetVersion: 0,
  markDone: (ids) => set((s) => {
    const add = ids.filter((id) => !s.done.includes(id));
    if (!add.length) return s;
    const next = { ...s, done: [...s.done, ...add] };
    savePreferences(next);
    return next;
  }),
  mark: (key, value) => set((s) => (s.marks[key] === value ? s : { marks: { ...s.marks, [key]: value } })),
  setEnabled: (enabled) => set((s) => {
    const next = { ...s, enabled };
    savePreferences(next);
    return next;
  }),
  restart: () => set((s) => {
    const next = { ...s, enabled: true, done: [], marks: {}, resetVersion: s.resetVersion + 1 };
    savePreferences(next);
    return next;
  }),
}));
