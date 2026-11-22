import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useCelebration } from '../celebrate/MomentLane';
import { tileOnScreen } from '../map/screenPos';
import { useGame } from '../store';
import { loadWasmModule, loadedWasmModule } from '../wasmClient';
import { Kbd } from './index';
import { useGuide } from './guideState';
import { advisorSuggestion, useAdvisor, type AdvisorTarget } from './advisorModel';
import { useCoarsePointer } from './useCoarsePointer';
import './Advisor.css';

/** Look up mounted controls afresh: a panel can open or move without changing the suggestion. */
function targetElement(target: Exclude<NonNullable<AdvisorTarget>, { kind: 'tile' }>): HTMLElement | null {
  const first = (...selectors: string[]) => selectors.map((s) => document.querySelector<HTMLElement>(s)).find((e) => e && e.getClientRects().length && !e.closest('[hidden]')) ?? null;
  const action = (label: RegExp) => [...document.querySelectorAll<HTMLElement>('.unit-panel button, .phone-primary-actions button')]
    .find((e) => label.test(e.getAttribute('aria-label') ?? e.textContent?.trim() ?? '') && e.getClientRects().length) ?? null;
  switch (target.name) {
    case 'research': return first('.topbar .research-chip', '.topbar .tb-nav-tech');
    case 'turn': return first('.seatbar .cta', '.phone-turn-dock button');
    case 'race': return first('.game .panel.vp', '.phone-vp-strip');
    case 'found': return action(/^Found City/i);
    case 'fortify': return action(/^(Fortify|Wait)/i);
    case 'skip': return action(/^Skip/i);
    case 'explore': return action(/^Auto-explore/i);
    case 'ranged': return action(/^Ranged attack/i);
    case 'build': return [...document.querySelectorAll<HTMLElement>('.city-panel .production-choice')]
      .find((e) => e.dataset.item === target.value)?.querySelector<HTMLElement>('button.prod') ?? null;
    case 'tech': return [...document.querySelectorAll<HTMLElement>('dialog.tech-modal .era-card')]
      .find((e) => e.dataset.tech === target.value)?.querySelector<HTMLElement>('button[data-testid="research-now"]') ?? null;
  }
}
function targetRect(target: AdvisorTarget): { x: number; y: number; width: number; height: number; tile: boolean } | null {
  if (!target) return null;
  if (target.kind === 'tile') {
    const at = tileOnScreen(target.hex);
    const map = document.querySelector<HTMLElement>('[data-game-map]')?.getBoundingClientRect();
    if (!at || !map || at.x < map.left || at.x > map.right || at.y < map.top || at.y > map.bottom) return null;
    if (!document.elementFromPoint(at.x, at.y)?.closest('[data-game-map]')) return null;
    const r = at.radius * 1.1;
    return { x: at.x - r, y: at.y - r, width: 2 * r, height: 2 * r, tile: true };
  }
  const el = targetElement(target), r = el?.getBoundingClientRect();
  if (!r || !r.width || !r.height || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return null;
  const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  if (!hit || !(el === hit || el?.contains(hit))) return null;
  const pad = 6;
  return { x: r.x - pad, y: r.y - pad, width: r.width + pad * 2, height: r.height + pad * 2, tile: false };
}

function AdvisorRing({ target }: { target: AdvisorTarget }) {
  const [rect, setRect] = useState<ReturnType<typeof targetRect>>(null);
  useEffect(() => {
    if (!target) { setRect(null); return; }
    let frame = 0, last = '';
    const measure = () => {
      const next = targetRect(target);
      const key = next ? `${next.x},${next.y},${next.width},${next.height}` : '';
      if (key !== last) { last = key; setRect(next); }
      // The map camera can glide and pan; follow it on every frame.
      frame = requestAnimationFrame(measure);
    };
    measure();
    return () => cancelAnimationFrame(frame);
  }, [target?.kind, target?.kind === 'tile' ? `${target.hex.q},${target.hex.r}` : target?.kind === 'control' ? `${target.name}:${target.value}` : '']);
  if (!rect) return null;
  return <div className={`advisor-ring${rect.tile ? ' map-target' : ''}`} data-testid="advisor-ring" aria-hidden="true"
    style={{ left: rect.x, top: rect.y, width: rect.width, height: rect.height }} />;
}

export function Advisor() {
  const card = useRef<HTMLElement>(null);
  const touch = useCoarsePointer();
  const view = useGame((s) => s.views?.[s.seat]);
  const seat = useGame((s) => s.seat);
  const orders = useGame((s) => s.orders);
  const errors = useGame((s) => s.errors);
  const humans = useGame((s) => s.humans);
  const selection = useGame((s) => s.selection);
  const mode = useGame((s) => s.mode);
  const techOpen = useGame((s) => s.techOpen);
  const client = useGame((s) => s.client);
  const paused = useGame((s) => !!s.scenario || !!s.busy || !!s.endTurnConfirmation || s.reportOpen || s.diplomacyOpen || !!s.ready[s.seat] || !!s.place ||
    (s.client?.kind === 'remote' && s.net?.conn !== 'open'));
  const guideOpen = useGuide((s) => s.open);
  const { active: celebration, holding } = useCelebration();
  const { enabled, seen, skipped, skippedTurn, markSeen, skip, setEnabled } = useAdvisor();
  const [, refreshPlan] = useState(0);
  useEffect(() => {
    if (!view || !enabled || loadedWasmModule()) return;
    let active = true;
    void loadWasmModule().then(() => { if (active) refreshPlan((n) => n + 1); }).catch(() => { /* Basic guidance remains available. */ });
    return () => { active = false; };
  }, [view, enabled]);
  const hidden = paused || guideOpen || holding || !!celebration || !enabled || !view || view.finished;
  const suggestion = view && enabled ? advisorSuggestion({ view, orders: orders[seat] ?? [], errors: errors[seat], selection,
    humans: humans.length, touch, techOpen, mode, local: { humans, orders, errors },
    forecast: client ? (unit, at, mode) => client.forecast(view.me, unit, at, mode) : undefined }, seen,
    skippedTurn === view.turn ? skipped : []) : null;
  const [modal, setModal] = useState<HTMLDialogElement | null>(null);
  useEffect(() => { setModal(techOpen ? document.querySelector<HTMLDialogElement>('dialog.tech-modal[open]') : null); }, [techOpen]);
  useLayoutEffect(() => {
    const el = card.current, game = document.querySelector<HTMLElement>('.game');
    if (!el || !game) return;
    const measure = () => game.style.setProperty('--hint-bottom', `${el.getBoundingClientRect().bottom - game.getBoundingClientRect().top}px`);
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => { resize.disconnect(); game.style.removeProperty('--hint-bottom'); };
  }, [hidden, suggestion?.id, suggestion?.current, modal]);
  if (hidden || !suggestion) return null;
  const step = suggestion.steps[suggestion.current];
  const welcome = suggestion.id === 'welcome';
  const lesson = suggestion.acknowledge && !welcome;
  const content = <>
    <AdvisorRing target={step?.target ?? null} />
    <aside ref={card} className={`advisor-card${welcome ? ' welcome' : ''}`} data-overlay-slot="story-hint" data-testid="advisor" data-advisor-id={suggestion.id} aria-label="Advisor" onKeyDown={(e) => e.stopPropagation()}>
      <span className="advisor-label">Advisor</span>
      <div className="advisor-copy" role="status" aria-live="polite" aria-atomic="true">
        <h3>{suggestion.title}</h3>
        <p>{suggestion.why}</p>
      </div>
      {step && <div className="advisor-step"><span className="advisor-count">Step {suggestion.current + 1} of {suggestion.steps.length}</span>
        <strong>{step.instruction}</strong>{step.key && <Kbd>{step.key}</Kbd>}
      </div>}
      <div className="advisor-actions">
        {welcome ? <button className="btn primary" onClick={() => markSeen('welcome')}>Continue</button>
          : lesson ? <button className="btn primary" onClick={() => markSeen(suggestion.id)}>Got it</button>
            : <button className="advisor-link" onClick={() => skip(suggestion.id, view!.turn)}>Not now</button>}
        <button className="advisor-link" onClick={() => setEnabled(false)}>Turn off advisor</button>
      </div>
    </aside>
  </>;
  return modal ? createPortal(content, modal) : content;
}

export function AdvisorSettings() {
  const { enabled, setEnabled } = useAdvisor();
  return <div className="hint-settings" onKeyDown={(e) => e.stopPropagation()}>
    <label><input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />Advisor</label>
    <div className="hint-settings-foot"><span>Shown until you turn it off</span></div>
  </div>;
}
