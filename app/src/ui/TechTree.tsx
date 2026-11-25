// PROTOTYPE (thread "Bring back a Civ-style tech tree", not for merge): the whole research timeline as a
// Civ-style tree. Nine era columns of five technologies, linked by the real upgrade lines (unit lines by
// class, building lines), today's era open, later eras visible but locked. `variant` draws the two rule
// options Sam is choosing between: 'era-links' adds illustrative prerequisites inside each era,
// 'open' drops the strict gate for an open tree where an era is entered at 3 of 5.
import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { BUILDING_STATS, ERA_COUNT, TECH_NAME, UNIT_STATS, unitClass } from '../data';
import type { BuildingKind, Faction, PlayerView, TechId, UnitKind } from '../types';
import { eraName, eraNumeral, turnsText, type QueueSlot } from './eraResearch';
import { techCardUnlocks } from './techCardUnlocks';
import { unitCardUrl } from '../unitArt';
import { itemArtUrl } from '../unlockArt';
import { unlockEntryArt } from '../unlockArt';
import { Icon } from './bits';

export type TreeVariant = 'tree' | 'era-links' | 'open';

/** Hand-ordered rows so the lines run straight: melee, ranged, mounted, then economy. */
const ROWS: TechId[][] = [
  ['Irrigation', 'Masonry', 'BronzeWorking', 'Currency', 'Writing'],
  ['Mathematics', 'Engineering', 'IronWorking', 'CodeOfLaws', 'Philosophy'],
  ['Feudalism', 'Machinery', 'Chivalry', 'CropRotation', 'Education'],
  ['Gunpowder', 'MilitaryEngineering', 'Metallurgy', 'Banking', 'PrintingPress'],
  ['Rifling', 'Cannonry', 'MilitaryScience', 'Industrialization', 'Railways'],
  ['ReplaceableParts', 'Steel', 'Combustion', 'Flight', 'Electricity'],
  ['MassMobilisation', 'Rocketry', 'ArmouredWarfare', 'AirPower', 'Electronics'],
  ['MechanisedWarfare', 'GuidedMissiles', 'CompositeArmour', 'JetEngines', 'GreenRevolution'],
  ['Robotics', 'AutonomousSystems', 'FusionPower', 'StealthTechnology', 'RecursiveAi'],
] as TechId[][];

/** Option 2 (illustrative only): one or two prerequisites inside each era. */
const IN_ERA: [TechId, TechId][] = [
  ['BronzeWorking', 'Masonry'], ['Writing', 'Currency'],
  ['Mathematics', 'Engineering'], ['Philosophy', 'CodeOfLaws'],
  ['Feudalism', 'Chivalry'], ['Machinery', 'Chivalry'],
  ['Gunpowder', 'Metallurgy'], ['Metallurgy', 'MilitaryEngineering'], ['Banking', 'PrintingPress'],
  ['Rifling', 'Cannonry'], ['Industrialization', 'Railways'],
  ['ReplaceableParts', 'Steel'], ['Combustion', 'Flight'],
  ['MassMobilisation', 'ArmouredWarfare'], ['Electronics', 'AirPower'],
  ['MechanisedWarfare', 'CompositeArmour'], ['GuidedMissiles', 'JetEngines'],
  ['AutonomousSystems', 'Robotics'], ['Robotics', 'RecursiveAi'],
] as [TechId, TechId][];

type Line = 'Melee' | 'Ranged' | 'Mounted' | 'Air' | 'Economy' | 'Prereq';
interface Link { from: TechId; to: TechId; line: Line; label: string }

function upgradeLinks(): Link[] {
  const out = new Map<string, Link>();
  const add = (from: TechId | null, to: TechId | null, line: Line, label: string) => {
    if (!from || !to || from === to) return;
    const k = `${from}>${to}`;
    if (!out.has(k)) out.set(k, { from, to, line, label });
  };
  for (const [kind, s] of Object.entries(UNIT_STATS) as [UnitKind, (typeof UNIT_STATS)[UnitKind]][]) {
    if (!s.upgradesTo) continue;
    const cls = unitClass(s.upgradesTo) ?? unitClass(kind);
    add(s.requires, UNIT_STATS[s.upgradesTo].requires, (cls ?? 'Melee') as Line, `${kind} → ${s.upgradesTo}`);
  }
  for (const [kind, b] of Object.entries(BUILDING_STATS) as [BuildingKind, (typeof BUILDING_STATS)[BuildingKind]][]) {
    if (!b.predecessor) continue;
    add(BUILDING_STATS[b.predecessor].requires, b.requires, 'Economy', `${b.predecessor} → ${kind}`);
  }
  return [...out.values()];
}

const W = 188, GAP = 70;

export function TechTree({ view, faction, queue, schedule, variant, onResearchNow, onQueue }: {
  view: PlayerView; faction: Faction; queue: TechId[]; schedule: QueueSlot[]; variant: TreeVariant;
  onResearchNow(t: TechId): void; onQueue(t: TechId): void;
}) {
  const r = view.research;
  const scroller = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(520);
  const [goal, setGoal] = useState<TechId | null>(() => (new URLSearchParams(location.search).get('treeGoal') as TechId | null));
  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setHeight(el.clientHeight));
    ro.observe(el);
    setHeight(el.clientHeight);
    // Open on the era you are in, with the one before it in view.
    el.scrollLeft = Math.max(0, (r.era - 1) * (W + GAP) - 12);
    return () => ro.disconnect();
  }, [r.era]);
  const short = height < 520;
  const RG = short ? 8 : 14, HEAD = short ? 50 : 58, PAD = short ? 10 : 18;
  const H = Math.max(64, Math.min(98, Math.floor((height - HEAD - PAD * 2 - 4 * RG - 4) / 5)));
  const compact = H < 82;
  const pos = useMemo(() => {
    const m = new Map<TechId, { x: number; y: number; era: number; row: number }>();
    ROWS.forEach((col, era) => col.forEach((t, row) => m.set(t, { x: PAD + era * (W + GAP), y: HEAD + PAD + row * (H + RG), era, row })));
    return m;
  }, [H, RG, HEAD, PAD]);
  const links = useMemo(() => {
    const l = upgradeLinks().filter((k) => pos.get(k.from)!.era !== pos.get(k.to)!.era);
    if (variant !== 'tree') for (const [from, to] of IN_ERA) l.push({ from, to, line: 'Prereq', label: `${TECH_NAME[from]} first` });
    return l;
  }, [pos, variant]);
  const known = new Set(r.known);
  const prereqs = (t: TechId) => links.filter((k) => k.to === t && (variant === 'open' || k.line === 'Prereq')).map((k) => k.from);
  const eraKnown = (era: number) => ROWS[era].filter((t) => known.has(t)).length;
  // In the open-tree option an era opens once you know 3 of the era before it.
  const eraOpen = (era: number) => variant === 'open' ? era === 0 || eraKnown(era - 1) >= 3 : era === r.era;
  const available = (t: TechId) => !known.has(t) && eraOpen(pos.get(t)!.era) && prereqs(t).every((p) => known.has(p));
  const science = Math.max(1, view.economy.science_per_turn.total);
  const costOf = (t: TechId) => r.catalog.find((c) => c.tech === t)?.cost.total ?? 0;
  const goalPlan = goal && !known.has(goal) ? (() => {
    const g = pos.get(goal)!;
    let path: TechId[];
    if (variant === 'open') {
      const need = new Set<TechId>();
      const walk = (t: TechId) => { for (const p of prereqs(t)) if (!known.has(p) && !need.has(p)) { need.add(p); walk(p); } };
      walk(goal);
      // Each era before the goal's needs 3 known to open the next.
      for (let e = 0; e < g.era; e++) { const have = ROWS[e].filter((t) => known.has(t) || need.has(t)); for (const t of ROWS[e]) if (have.length < 3 && !have.includes(t)) { need.add(t); have.push(t); } }
      path = [...need];
    } else path = ROWS.flatMap((col, era) => era < g.era ? col : []).filter((t) => !known.has(t));
    const total = [...path, goal].reduce((s, t) => s + costOf(t), 0) - r.progress;
    const turns = Math.ceil(Math.max(0, total) / science);
    return { path, turns, era: g.era };
  })() : null;
  const width = PAD * 2 + ERA_COUNT * W + (ERA_COUNT - 1) * GAP;
  const total = HEAD + PAD * 2 + 5 * H + 4 * RG;
  const path = (k: Link) => {
    const a = pos.get(k.from)!, b = pos.get(k.to)!;
    if (k.line === 'Prereq') {
      // A bracket in the gap to the right of the column: out of the first, down (or up), into the second.
      const x = a.x + W, y1 = a.y + H / 2 + 8, y2 = b.y + H / 2 - 8, bx = x + 14;
      return `M ${x} ${y1} L ${bx - 4} ${y1} Q ${bx} ${y1} ${bx} ${y1 + Math.sign(y2 - y1) * 4} L ${bx} ${y2 - Math.sign(y2 - y1) * 4} Q ${bx} ${y2} ${bx - 4} ${y2} L ${x + 2} ${y2}`;
    }
    const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
    if (b.era - a.era === 1) { const mx = (x1 + x2) / 2; return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`; }
    // A line that skips eras runs in the lane between rows so it never seems to pass through a technology.
    const lane = Math.min(a.y, b.y) - RG / 2;
    const ex = x1 + GAP / 2, sx = x2 - GAP / 2;
    return `M ${x1} ${y1} C ${ex} ${y1}, ${ex} ${y1}, ${ex} ${(y1 + lane) / 2} L ${ex} ${lane + 6} Q ${ex} ${lane} ${ex + 6} ${lane} L ${sx - 6} ${lane} Q ${sx} ${lane} ${sx} ${lane + 6} L ${sx} ${(y2 + lane) / 2} C ${sx} ${y2}, ${sx} ${y2}, ${x2} ${y2}`;
  };
  const onGoalPath = (t: TechId) => !!goalPlan && (t === goal || goalPlan.path.includes(t));
  return <div className={`tech-tree variant-${variant}${compact ? ' compact' : ''}`} data-testid="tech-tree">
    <div className="tree-legend" aria-hidden="true">
      <span><i className="ln melee" />Spear line</span><span><i className="ln ranged" />Bow and gun line</span><span><i className="ln mounted" />Horse and armour line</span>
      <span><i className="ln air" />Aircraft</span><span><i className="ln economy" />Buildings</span>
      {variant !== 'tree' && <span><i className="ln prereq" />Needs first</span>}
      {goalPlan && goal ? <span className="tree-goal" data-testid="tree-goal">
        <span className="tree-goal-flag">Goal</span>
        <span><b>{TECH_NAME[goal]}</b>: {variant === 'tree' ? `${goalPlan.path.length} technologies first` : `${goalPlan.path.length} prerequisites first`}, then it. <b>About turn {view.turn + goalPlan.turns}</b></span>
        <button type="button" className="tree-goal-x" onClick={() => setGoal(null)} aria-label="Clear goal"><Icon name="ui-cross" size={11} /></button>
      </span> : <span className="tree-hint">{variant === 'open' ? 'Research anything whose arrows are met. Enter an era at 3 of its 5.' : 'Click a technology in your era to research it. Click a later one to set it as your goal.'}</span>}
    </div>
    <div className="tree-scroll" ref={scroller} onWheel={(e) => { if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) e.currentTarget.scrollLeft += e.deltaY; }}>
      <div className="tree-canvas" style={{ width, height: total }}>
        {ROWS.map((_, era) => {
          const state = variant === 'open' ? (eraKnown(era) === 5 ? 'past' : eraOpen(era) ? 'current' : 'future') : era < r.era ? 'past' : era === r.era ? 'current' : 'future';
          return <div key={era} className={`tree-era ${state}`} style={{ left: PAD + era * (W + GAP) - GAP / 2 + 6, width: W + GAP - 12, height: total }}>
            <div className="tree-era-head">
              <span className="tree-era-numeral">{state === 'past' ? <Icon name="ui-check" size={12} /> : eraNumeral(era)}</span>
              <span className="tree-era-name">{eraName(era)}</span>
              <span className="tree-era-state">{state === 'past' ? 'Done' : state === 'current' ? (variant === 'open' ? `${eraKnown(era)} of 5 · enter at 3` : `You are here · ${eraKnown(era)} of 5`) : variant === 'open' ? 'Opens at 3 of the era before' : 'Opens when the era before is done'}</span>
            </div>
          </div>;
        })}
        <svg className="tree-links" width={width} height={total} aria-hidden="true">
          {links.map((k) => <path key={`${k.from}>${k.to}`} d={path(k)} className={`tl ${k.line.toLowerCase()}${known.has(k.from) ? ' lit' : ''}${onGoalPath(k.to) && onGoalPath(k.from) ? ' goal' : ''}`} markerEnd={k.line === 'Prereq' ? 'url(#tree-arrow)' : undefined} />)}
          <defs><marker id="tree-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L8 4 L0 8 z" fill="var(--ink-2)" /></marker></defs>
        </svg>
        {ROWS.flat().map((t) => {
          const p = pos.get(t)!;
          const isKnown = known.has(t);
          const qi = queue.indexOf(t);
          const avail = available(t);
          const researching = qi === 0 && !isKnown;
          const option = r.catalog.find((c) => c.tech === t);
          const skipped = r.skipped?.includes(t);
          const entries = techCardUnlocks(r, t, faction);
          const arts = entries.slice(0, 3).map((e) => {
            const unit = e.kind === 'Unit' && e.unlock?.item && typeof e.unlock.item === 'object' && 'Unit' in e.unlock.item ? (e.unlock.item as { Unit: UnitKind }).Unit : e.upgrades[0]?.to;
            const url = unit ? unitCardUrl(unit, faction) ?? itemArtUrl({ kind: 'Unit', unit } as never, faction, 128) : e.icon.startsWith('resource-') ? null : unlockEntryArt(e.unlock?.item, e.label, t, faction, 128);
            return { url, icon: e.icon, label: e.label };
          });
          const blocked = !isKnown && !avail && (variant === 'open' || p.era === r.era) ? prereqs(t).filter((x) => !known.has(x)) : [];
          const state = isKnown ? 'known' : researching ? 'researching' : qi > 0 ? 'queued' : avail ? 'available' : blocked.length ? 'blocked' : 'locked';
          const slot = qi >= 0 ? schedule[qi] : undefined;
          const turns = slot?.turns ?? option?.turns ?? null;
          const isGoal = goal === t;
          return <button key={t} type="button" className={`tree-node ${state}${isGoal ? ' goal' : ''}${onGoalPath(t) && !isGoal ? ' on-path' : ''}${skipped ? ' skipped' : ''}`}
            style={{ left: p.x, top: p.y, width: W, height: H }} data-tech={t} data-state={state}
            title={entries.map((e) => e.label).join('\n')}
            onClick={(e) => { if (state === 'available' || state === 'queued') { if (e.shiftKey) onQueue(t); else onResearchNow(t); } else if (!isKnown) setGoal(isGoal ? null : t); }}>
            <span className="tn-head">
              <b className="tn-name">{TECH_NAME[t]}</b>
              {isKnown ? <span className="tn-mark"><Icon name="ui-check" size={12} /></span> : qi > 0 ? <span className="tn-q">#{qi + 1}</span> : isGoal ? <span className="tn-goal">Goal</span> : null}
            </span>
            <span className="tn-art">{arts.map((a, i) => <span key={i} className="tn-thumb" title={a.label}>{a.url ? <img src={a.url} alt="" draggable={false} /> : <Icon name={a.icon} size={compact ? 18 : 22} />}</span>)}
              {entries.length > 3 && <span className="tn-more">+{entries.length - 3}</span>}</span>
            <span className="tn-foot">{isKnown ? 'Researched' : researching ? <><span className="tn-bar"><i style={{ width: `${option ? Math.min(100, r.progress * 100 / option.cost.total) : 0}%` }} /></span>{turns === null ? '' : turnsText(turns)}</>
              : state === 'available' || state === 'queued' ? `${option?.cost.total ?? ''} Science${turns === null ? '' : ` · ${turnsText(turns)}`}`
              : blocked.length ? `Needs ${blocked.map((x) => TECH_NAME[x]).join(', ')}` : `${option?.cost.total ?? ''} Science`}</span>
          </button>;
        })}
      </div>
    </div>
  </div>;
}
