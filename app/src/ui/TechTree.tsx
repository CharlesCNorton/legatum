// The tech tree (Civ style) over the strict era gate: every era a column of its technologies, linked by
// the real upgrade lines (each unit class's line and each building line), your era open to research,
// later eras visible but locked. A later technology can be made the research goal (Player::research_goal):
// whenever the queue runs out, the engine fills it toward the goal. Rules: legatum-rules research-and-eras.
import { useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type MouseEvent } from 'react';
import { BUILDING_STATS, TECH_NAME, UNIT_STATS, unitClass } from '../data';
import type { BuildingKind, Faction, PlayerView, TechId, TechOption, UnitKind } from '../types';
import { eraName, eraNumeral, turnsText, type QueueSlot } from './eraResearch';
import { techCardUnlocks, type TechCardUnlock } from './techCardUnlocks';
import { unitCardUrl } from '../unitArt';
import { itemArtUrl, unlockEntryArt } from '../unlockArt';
import { Icon } from './bits';
import { useCoarsePointer } from './useCoarsePointer';

/** Row order inside each era, so the lines run straight: the spear line, the bow and gun line, the horse
 * and armour line, then aircraft and the buildings. A technology missing here goes to the end of its era. */
const ROW_ORDER: TechId[] = [
  'Irrigation', 'Masonry', 'BronzeWorking', 'Currency', 'Writing',
  'Mathematics', 'Engineering', 'IronWorking', 'CodeOfLaws', 'Philosophy',
  'Feudalism', 'Machinery', 'Chivalry', 'CropRotation', 'Education',
  'Gunpowder', 'MilitaryEngineering', 'Metallurgy', 'Banking', 'PrintingPress',
  'Rifling', 'Cannonry', 'MilitaryScience', 'Industrialization', 'Railways',
  'ReplaceableParts', 'Steel', 'Combustion', 'Flight', 'Electricity',
  'MassMobilisation', 'Rocketry', 'ArmouredWarfare', 'AirPower', 'Electronics',
  'MechanisedWarfare', 'GuidedMissiles', 'CompositeArmour', 'JetEngines', 'GreenRevolution',
  'Robotics', 'AutonomousSystems', 'FusionPower', 'StealthTechnology', 'RecursiveAi',
] as TechId[];

export type TreeLine = 'Melee' | 'Ranged' | 'Mounted' | 'Air' | 'Economy';
export interface TreeLink { from: TechId; to: TechId; line: TreeLine }

/** The upgrade lines between technologies: a unit's technology to the technology of the unit it upgrades to,
 * a building's technology to its successor's. Links inside one era are left out (there are no prerequisites
 * inside an era). */
export function treeLinks(eraOf: (t: TechId) => number | undefined): TreeLink[] {
  const out = new Map<string, TreeLink>();
  const add = (from: TechId | null, to: TechId | null, line: TreeLine) => {
    if (!from || !to || from === to) return;
    const a = eraOf(from), b = eraOf(to);
    if (a === undefined || b === undefined || a >= b) return;
    if (!out.has(`${from}>${to}`)) out.set(`${from}>${to}`, { from, to, line });
  };
  for (const [kind, s] of Object.entries(UNIT_STATS) as [UnitKind, (typeof UNIT_STATS)[UnitKind]][]) {
    if (s.upgradesTo) add(s.requires, UNIT_STATS[s.upgradesTo].requires, unitClass(s.upgradesTo) ?? unitClass(kind) ?? 'Melee');
  }
  for (const b of Object.values(BUILDING_STATS)) {
    if (b.predecessor) add(BUILDING_STATS[b.predecessor as BuildingKind].requires, b.requires, 'Economy');
  }
  return [...out.values()];
}

/** The technologies of each era in row order. */
export function treeColumns(catalog: readonly TechOption[]): TechId[][] {
  const cols: TechId[][] = [];
  for (const t of catalog) (cols[t.era] ??= []).push(t.tech);
  const rank = (t: TechId) => { const i = ROW_ORDER.indexOf(t); return i < 0 ? ROW_ORDER.length : i; };
  return Array.from(cols, (c) => (c ?? []).sort((a, b) => rank(a) - rank(b)));
}

/** What reaching a goal takes: the unknown technologies of every era before it, then the goal. */
export function goalForecast(view: PlayerView, goal: TechId, columns: TechId[][]): { before: number; turns: number | null; arrival: number | null } {
  const r = view.research;
  const known = new Set(r.known);
  const goalEra = r.catalog.find((t) => t.tech === goal)?.era ?? r.era;
  const before = columns.flatMap((col, era) => (era < goalEra ? col : [])).filter((t) => !known.has(t));
  const cost = [...before, goal].reduce((sum, t) => sum + (r.catalog.find((c) => c.tech === t)?.cost.total ?? 0), 0);
  const science = view.economy.science_per_turn.total;
  if (science <= 0) return { before: before.length, turns: null, arrival: null };
  // At most one technology a turn, so it is never sooner than the count.
  const turns = Math.max(before.length + 1, Math.ceil(Math.max(0, cost - r.progress) / science));
  return { before: before.length, turns, arrival: view.turn + turns };
}

const W = 188, GAP = 70;

function unlockArt(entry: TechCardUnlock, faction: Faction): string | null {
  const unit = entry.upgrades[0]?.to ?? (entry.unlock?.item && typeof entry.unlock.item === 'object' && 'Unit' in entry.unlock.item ? (entry.unlock.item as { Unit: UnitKind }).Unit : undefined);
  if (unit) return unitCardUrl(unit, faction) ?? itemArtUrl({ Unit: unit } as never, faction, 128);
  if (entry.icon.startsWith('resource-')) return null;
  return unlockEntryArt(entry.unlock?.item, entry.label, entry.tech, faction, 128);
}

interface Props {
  view: PlayerView;
  faction: Faction;
  queue: TechId[];
  schedule: QueueSlot[];
  goal: TechId | null;
  locked: boolean;
  onResearchNow(t: TechId): void;
  onQueue(t: TechId): void;
  onGoal(t: TechId | null): void;
}

export function TechTree({ view, faction, queue, schedule, goal, locked, onResearchNow, onQueue, onGoal }: Props) {
  const r = view.research;
  const scroller = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(520);
  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setHeight(el.clientHeight));
    ro.observe(el);
    setHeight(el.clientHeight);
    // Open on your era, with the one before it in view.
    el.scrollLeft = Math.max(0, (r.era - 1) * (W + GAP) - 12);
    return () => ro.disconnect();
  }, [r.era]);
  const columns = useMemo(() => treeColumns(r.catalog), [r.catalog]);
  const rows = Math.max(1, ...columns.map((c) => c.length));
  const short = height < 520;
  const RG = short ? 8 : 14, HEAD = short ? 50 : 58, PAD = short ? 10 : 18;
  const H = Math.max(64, Math.min(98, Math.floor((height - HEAD - PAD * 2 - (rows - 1) * RG - 4) / rows)));
  const compact = H < 82;
  const pos = useMemo(() => {
    const m = new Map<TechId, { x: number; y: number; era: number }>();
    columns.forEach((col, era) => col.forEach((t, row) => m.set(t, { x: PAD + era * (W + GAP), y: HEAD + PAD + row * (H + RG), era })));
    return m;
  }, [columns, H, RG, HEAD, PAD]);
  const links = useMemo(() => treeLinks((t) => pos.get(t)?.era), [pos]);
  const known = new Set(r.known);
  const skipped = new Set(r.skipped ?? []);
  const forecast = goal && !known.has(goal) ? goalForecast(view, goal, columns) : null;
  const goalEra = goal ? pos.get(goal)?.era ?? -1 : -1;
  const onPath = (t: TechId) => !!forecast && !known.has(t) && (t === goal || (pos.get(t)?.era ?? 99) < goalEra);
  const width = PAD * 2 + columns.length * W + (columns.length - 1) * GAP;
  const total = HEAD + PAD * 2 + rows * H + (rows - 1) * RG;
  const path = (k: TreeLink) => {
    const a = pos.get(k.from)!, b = pos.get(k.to)!;
    const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
    if (b.era - a.era === 1) { const mx = (x1 + x2) / 2; return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`; }
    // A line that skips eras runs in the lane between rows, so it never seems to pass through a technology.
    const lane = Math.min(a.y, b.y) - RG / 2;
    const ex = x1 + GAP / 2, sx = x2 - GAP / 2;
    return `M ${x1} ${y1} C ${ex} ${y1}, ${ex} ${y1}, ${ex} ${(y1 + lane) / 2} L ${ex} ${lane + 6} Q ${ex} ${lane} ${ex + 6} ${lane} L ${sx - 6} ${lane} Q ${sx} ${lane} ${sx} ${lane + 6} L ${sx} ${(y2 + lane) / 2} C ${sx} ${y2}, ${sx} ${y2}, ${x2} ${y2}`;
  };
  const eraState = (era: number) => era < r.era ? 'past' : era === r.era ? 'current' : 'future';
  const touch = useCoarsePointer(), press = touch ? 'Tap' : 'Click';
  return <div className={`tech-tree${compact ? ' compact' : ''}`} data-testid="tech-tree">
    <div className="tree-legend">
      <span className="tree-key" aria-hidden="true"><i className="ln melee" />Spear line</span>
      <span className="tree-key" aria-hidden="true"><i className="ln ranged" />Bow and gun line</span>
      <span className="tree-key" aria-hidden="true"><i className="ln mounted" />Horse and armour line</span>
      <span className="tree-key" aria-hidden="true"><i className="ln air" />Aircraft</span>
      <span className="tree-key" aria-hidden="true"><i className="ln economy" />Buildings</span>
      {goal && forecast ? <span className="tree-goal" data-testid="tree-goal">
        <span className="tree-goal-flag">Goal</span>
        <span className="tree-goal-text"><b>{TECH_NAME[goal]}</b>{forecast.before ? `, after ${forecast.before} more technolog${forecast.before === 1 ? 'y' : 'ies'}` : ''}. {forecast.arrival === null ? 'Needs Science.' : <b>About turn {forecast.arrival}</b>}</span>
        <button type="button" className="tree-goal-x" disabled={locked} onClick={() => onGoal(null)} aria-label={`Clear the goal ${TECH_NAME[goal]}`} title="Clear the goal"><Icon name="ui-cross" size={11} /></button>
      </span>
        : <span className="tree-hint">{press} a technology to research it. {press} a later one to make it your goal.</span>}
    </div>
    <div className="tree-scroll" ref={scroller} tabIndex={-1}
      onWheel={(e) => { const el = e.currentTarget; if (el.scrollHeight <= el.clientHeight && Math.abs(e.deltaY) > Math.abs(e.deltaX)) el.scrollLeft += e.deltaY; }}>
      <div className="tree-canvas" style={{ width, height: total }}>
        {columns.map((_, era) => {
          const state = eraState(era);
          const count = columns[era].filter((t) => !skipped.has(t));
          return <div key={era} className={`tree-era ${state}`} data-era={era} style={{ left: PAD + era * (W + GAP) - GAP / 2 + 6, width: W + GAP - 12, height: total }}>
            <div className="tree-era-head">
              <span className="tree-era-numeral">{state === 'past' ? <Icon name="ui-check" size={12} /> : eraNumeral(era)}</span>
              <span className="tree-era-name">{eraName(era)}</span>
              <span className="tree-era-state">{state === 'past' ? 'Done' : state === 'current' ? `Your era · ${count.filter((t) => known.has(t)).length} of ${count.length} known` : `Opens after the ${eraName(era - 1)} era`}</span>
            </div>
          </div>;
        })}
        <svg className="tree-links" width={width} height={total} aria-hidden="true">
          {links.map((k) => <path key={`${k.from}>${k.to}`} d={path(k)} className={`tl ${k.line.toLowerCase()}${known.has(k.from) ? ' lit' : ''}${onPath(k.to) && (onPath(k.from) || known.has(k.from)) ? ' goal' : ''}`} />)}
        </svg>
        {columns.flatMap((col) => col).map((t) => <TreeNode key={t} t={t} view={view} faction={faction} pos={pos.get(t)!} w={W} h={H} compact={compact}
          queueIndex={queue.indexOf(t)} slot={schedule[queue.indexOf(t)]} goal={goal === t} onPath={onPath(t) && goal !== t} skipped={skipped.has(t)} locked={locked} touch={touch}
          onResearchNow={onResearchNow} onQueue={onQueue} onGoal={onGoal} />)}
      </div>
    </div>
  </div>;
}

function TreeNode({ t, view, faction, pos, w, h, compact, queueIndex, slot, goal, onPath, skipped, locked, touch, onResearchNow, onQueue, onGoal }: {
  t: TechId; view: PlayerView; faction: Faction; pos: { x: number; y: number; era: number }; w: number; h: number; compact: boolean;
  queueIndex: number; slot: QueueSlot | undefined; goal: boolean; onPath: boolean; skipped: boolean; locked: boolean; touch: boolean;
  onResearchNow(t: TechId): void; onQueue(t: TechId): void; onGoal(t: TechId | null): void;
}) {
  const r = view.research;
  const isKnown = r.known.includes(t);
  const option = r.catalog.find((c) => c.tech === t);
  const current = !isKnown && pos.era === r.era;
  const later = !isKnown && pos.era > r.era;
  const researching = queueIndex === 0 && !isKnown;
  const state = isKnown ? 'known' : researching ? 'researching' : queueIndex > 0 ? 'queued' : current ? 'available' : 'locked';
  const entries = techCardUnlocks(r, t, faction);
  const turns = slot?.turns ?? option?.turns ?? null;
  const cost = option?.cost.total ?? 0;
  const progress = researching ? Math.min(r.progress, cost) : 0;
  const act = (shift: boolean) => {
    if (locked || isKnown) return;
    if (current) { if (shift) onQueue(t); else onResearchNow(t); }
    else if (later) onGoal(goal ? null : t);
  };
  const onClick = (e: MouseEvent<HTMLButtonElement>) => act(e.shiftKey);
  const onKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => { if (e.key === 'Enter') { e.preventDefault(); act(e.shiftKey); } };
  const status = isKnown ? (skipped ? 'Not needed by your people' : 'Researched') : researching ? 'Researching' : queueIndex > 0 ? `Queued #${queueIndex + 1}` : current ? 'Available' : goal ? 'Your goal' : `Locked until the ${eraName(pos.era - 1)} era is done`;
  const press = touch ? 'Tap' : 'Click';
  const action = current ? (touch ? 'Tap to research now.' : 'Click to research now, Shift+click to queue.') : later ? (goal ? `${press} to clear the goal.` : `${press} to make it your goal.`) : '';
  return <button type="button" className={`tree-node ${state}${goal ? ' goal' : ''}${onPath ? ' on-path' : ''}${skipped ? ' skipped' : ''}`}
    style={{ left: pos.x, top: pos.y, width: w, height: h }} data-tech={t} data-state={state}
    title={`${TECH_NAME[t]}: ${entries.map((e) => e.label).join('; ') || 'nothing new'}`}
    aria-disabled={isKnown || locked || undefined} aria-pressed={later ? goal : undefined}
    aria-label={`${TECH_NAME[t]}. ${status}. Unlocks ${entries.map((e) => e.label).join('; ') || 'nothing new'}.${action ? ` ${action}` : ''}`}
    onClick={onClick} onKeyDown={onKeyDown} onMouseDown={(e) => { if (e.shiftKey) e.preventDefault(); }}>
    <span className="tn-head">
      <b className="tn-name">{TECH_NAME[t]}</b>
      {isKnown ? <span className="tn-mark"><Icon name="ui-check" size={12} /></span>
        : queueIndex > 0 ? <span className="tn-q">#{queueIndex + 1}</span>
        : goal ? <span className="tn-goal">Goal</span> : null}
    </span>
    <span className="tn-art">
      {entries.slice(0, 3).map((e, i) => { const url = unlockArt(e, faction); return <span key={i} className="tn-thumb">{url ? <img src={url} alt="" draggable={false} /> : <Icon name={e.icon} size={compact ? 16 : 20} />}</span>; })}
      {entries.length > 3 && <span className="tn-more">+{entries.length - 3}</span>}
    </span>
    <span className="tn-foot">{isKnown ? (skipped ? 'Not needed' : 'Researched')
      : researching ? <><span className="tn-bar" role="progressbar" aria-label={`${TECH_NAME[t]} research progress`} aria-valuemin={0} aria-valuemax={cost} aria-valuenow={progress}><i style={{ width: `${cost ? progress * 100 / cost : 0}%` }} /></span>{turns === null ? 'Needs Science' : turnsText(turns)}</>
      : current ? `${cost} Science · ${turns === null ? 'needs Science' : slot?.arrivalTurn ? `turn ${slot.arrivalTurn}` : turnsText(turns)}`
      : `${cost} Science`}</span>
  </button>;
}
