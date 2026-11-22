import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useCelebration } from '../celebrate/MomentLane';
import { useGame } from '../store';
import { useGuide } from './guideState';
import { nextStep, stepCopy, stepNumber, useTutorial, type Spotlight, type StepAction, type StepId, type TutorialContext } from './tutorial';
import { useCoarsePointer } from './useCoarsePointer';
import './Tutorial.css';

/** The control a step points at. Looked up live, since panels mount and move. */
function spotlightTarget(spot: Spotlight): Element | null {
  const visible = (el: Element | null) => (el && (el as HTMLElement).offsetParent !== null ? el : null);
  const first = (...selectors: string[]) => selectors.map((s) => visible(document.querySelector(s))).find(Boolean) ?? null;
  switch (spot) {
    case 'research': return first('.topbar .research-chip', '.topbar .tb-nav-tech');
    case 'turn': return first('.seatbar .cta', '.phone-turn-dock');
    case 'race': return first('.game .panel.vp', '.phone-vp-strip');
    case 'found': return [...document.querySelectorAll('.left-dock button')].find((b) => /^Found City/i.test(b.textContent?.trim() ?? '') && visible(b)) ?? null;
    default: return null;
  }
}

/** A gilt ring around the control the step is about. It never takes clicks. */
function SpotlightRing({ spot }: { spot: Spotlight }) {
  const [rect, setRect] = useState<DOMRect | null>(null);
  useEffect(() => {
    if (!spot) { setRect(null); return; }
    let last = '';
    const measure = () => {
      const r = spotlightTarget(spot)?.getBoundingClientRect() ?? null;
      const key = r ? `${r.x},${r.y},${r.width},${r.height}` : '';
      if (key !== last) { last = key; setRect(r); }
    };
    measure();
    const timer = setInterval(measure, 300);
    return () => clearInterval(timer);
  }, [spot]);
  if (!rect || !rect.width) return null;
  const pad = 4;
  return <div className="tutorial-ring" aria-hidden="true" data-testid="tutorial-ring"
    style={{ left: rect.x - pad, top: rect.y - pad, width: rect.width + pad * 2, height: rect.height + pad * 2 }} />;
}

function runAction(action: StepAction) {
  const s = useGame.getState();
  switch (action.kind) {
    case 'select': s.select(action.target, true); break;
    case 'research': s.set({ techOpen: true }); break;
    case 'report': s.set({ reportOpen: true }); break;
    case 'guide': useGuide.getState().show(action.section); break;
  }
}

export function Tutorial() {
  const panel = useRef<HTMLElement>(null);
  const touch = useCoarsePointer();
  const view = useGame((s) => s.views?.[s.seat]);
  const seat = useGame((s) => s.seat);
  const allOrders = useGame((s) => s.orders);
  const errors = useGame((s) => s.errors);
  const humans = useGame((s) => s.humans);
  const selection = useGame((s) => s.selection);
  // Decisions and reports that own the screen come first; the tutorial waits for them to close.
  // Scenarios are for players who know the game: their objective bar takes the tutorial's place.
  const paused = useGame((s) => !!s.scenario || !!s.busy || !!s.endTurnConfirmation || s.techOpen || s.reportOpen || s.diplomacyOpen || !!s.ready[s.seat] || !!s.place ||
    (s.client?.kind === 'remote' && s.net?.conn !== 'open'));
  const guideOpen = useGuide((s) => s.open);
  const { enabled, done, marks, markDone, mark, setEnabled } = useTutorial();
  const { active: celebration, holding } = useCelebration();
  const hidden = paused || holding || !!celebration || guideOpen || !enabled || !view || view.finished;

  const ctx: TutorialContext | null = view ? {
    view, orders: allOrders[seat] ?? [], errors: errors[seat], selection, humans: humans.length, touch,
    local: { humans, orders: allOrders, errors },
  } : null;
  const { step, completed } = ctx && enabled ? nextStep(ctx, done, marks) : { step: null as StepId | null, completed: [] as StepId[] };
  const completedKey = completed.join(',');

  // Steps the player has already done (by playing or before the tutorial began) are noted as done.
  useEffect(() => {
    if (completedKey) markDone(completedKey.split(',') as StepId[]);
  }, [completedKey, markDone]);

  // "End the turn" and "Found a city" finish on what happens after they first show.
  const turn = view?.turn ?? 0;
  const myCities = view ? view.cities.filter((c) => c.owner === view.me).length : 0;
  useEffect(() => {
    if (hidden) return;
    if (step === 'endTurn' && (marks.endTurn === undefined || turn < marks.endTurn)) mark('endTurn', turn);
    if (step === 'found' && (marks.found === undefined || myCities < marks.found)) mark('found', myCities);
  }, [hidden, step, turn, myCities, marks.endTurn, marks.found, mark]);

  // On narrow screens the destination card uses the space between this card and the lens dock.
  useLayoutEffect(() => {
    const el = panel.current, game = el?.closest<HTMLElement>('.game');
    if (!el || !game) return;
    const measure = () => game.style.setProperty('--hint-bottom', `${el.getBoundingClientRect().bottom - game.getBoundingClientRect().top}px`);
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => { resize.disconnect(); game.style.removeProperty('--hint-bottom'); };
  }, [hidden, step]);

  if (hidden || !step || !ctx) return null;
  const copy = stepCopy(step, ctx);
  const count = stepNumber(step);
  const welcome = step === 'welcome';
  const finish = step === 'finish';
  return <>
    <SpotlightRing spot={copy.spotlight} />
    <aside ref={panel} className={`tutorial-card${welcome ? ' welcome' : ''}`} data-overlay-slot="story-hint" data-testid="tutorial"
      aria-label="Tutorial" onKeyDown={(e) => e.stopPropagation()}>
      <div className="tutorial-copy" role="status" aria-live="polite" aria-atomic="true">
        <h3>{copy.title}</h3>
        <p>{copy.body}</p>
      </div>
      <div className="tutorial-actions">
        {welcome ? <>
          <button className="btn primary" onClick={() => markDone(['welcome'])}>Start tutorial</button>
          <button className="tutorial-skip" onClick={() => setEnabled(false)}>Skip tutorial</button>
        </> : <>
          {copy.help && <button className={`btn${copy.acknowledge ? '' : ' primary'}`} onClick={() => { runAction(copy.help!.action); if (copy.acknowledge && copy.help!.action.kind !== 'guide') markDone([step]); }}>{copy.help.label}</button>}
          {copy.acknowledge && <button className="btn primary" onClick={() => markDone([step])}>{finish ? 'Finish' : 'Next'}</button>}
          <span className="tutorial-foot">
            {count && <span className="tutorial-count" aria-label={`Step ${count.n} of ${count.of}`}>{count.n} / {count.of}</span>}
            {!finish && <button className="tutorial-skip" onClick={() => setEnabled(false)}>Skip tutorial</button>}
          </span>
        </>}
      </div>
    </aside>
  </>;
}

/** Reused by title Settings and the in-game menu; Restart also turns the tutorial back on. */
export function TutorialSettings() {
  const { enabled, done, resetVersion, setEnabled, restart } = useTutorial();
  const [restartedAt, setRestartedAt] = useState<number | null>(null);
  return (
    <div className="hint-settings" onKeyDown={(e) => e.stopPropagation()}>
      <label><input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />First-game tutorial</label>
      <div className="hint-settings-foot">
        <span role="status">{restartedAt === resetVersion && !done.length ? 'Tutorial restarted' : 'Shown once in this browser'}</span>
        <button onClick={() => { restart(); setRestartedAt(useTutorial.getState().resetVersion); }}>Restart tutorial</button>
      </div>
    </div>
  );
}
