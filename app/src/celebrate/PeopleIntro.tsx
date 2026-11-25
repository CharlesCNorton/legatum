import { useEffect, useRef } from 'react';
import { FACTION_GOAL, FACTION_INFO, factionGoalTerms, factionGoalVp } from '../data';
import { FACTION_SHEETS } from '../factionSheets';
import { feel, useCombatFx } from '../feel';
import { useGame } from '../store';
import { Amounts } from '../ui/Amounts';
import { Icon } from '../ui/bits';
import { MedallionRow, PortraitFrame } from '../ui/premium';
import { useReducedMotion } from '../ui/useReducedMotion';
import { eraArt } from './eraArt';
import './eraTakeover.css';
import './peopleIntro.css';

/**
 * The opening of a new game (user, 2026-11-25): before the first turn, a full-screen plate introduces the people
 * you lead, in the era takeover's language. The first era's painting, the leaders' portrait, the people's name and
 * motto, then what the faction sheet already says in the same words: what you are good at, what it costs you and
 * the goal only you can score. One primary, Begin (Return; Esc does the same: there is nothing to cancel).
 *
 * It shows once, for a game that has just begun (`store.intro`, set by `startGame` and by joining an online game
 * on its first turn), never for a loaded game, and with a Random people it is where you learn who you drew.
 * Narration, when recorded, plays from here (`data-people` names the people for it).
 */
export function PeopleIntro() {
  const intro = useGame((s) => s.intro);
  const view = useGame((s) => s.views?.[s.seat] ?? null);
  const motionOff = useReducedMotion();
  const animationsOn = useCombatFx((s) => s.enabled);
  const primary = useRef<HTMLButtonElement>(null);
  const up = intro && !!view && view.turn === 1;
  const begin = () => { feel.select(); useGame.setState({ intro: false }); };

  useEffect(() => { if (up) primary.current?.focus({ preventScroll: true }); }, [up]);
  // Leaving the game (exit to title, a loaded save) ends the introduction with it.
  useEffect(() => () => useGame.setState({ intro: false }), []);
  useEffect(() => {
    if (!up) return;
    // Capture phase, ahead of the game's own keys: nothing under this plate may act on them.
    const key = (e: KeyboardEvent) => {
      if (e.key !== 'Enter' && e.key !== 'Escape') return;
      e.preventDefault();
      e.stopPropagation();
      if (e.repeat || e.isComposing) return;
      begin();
    };
    window.addEventListener('keydown', key, true);
    return () => window.removeEventListener('keydown', key, true);
  });

  if (!up || !view) return null;
  const faction = view.players.find((p) => p.id === view.me)?.faction;
  if (!faction) return null;
  const info = FACTION_INFO[faction];
  const sheet = FACTION_SHEETS[faction];
  const rows = sheet.pairs.filter((p) => !p.onCard);
  const goal = factionGoalVp(faction) > 0 ? FACTION_GOAL[faction] : null;
  const art = eraArt(0);
  const reduced = motionOff || !animationsOn;
  return <div className={`era-takeover people-intro ${reduced ? 'reduced' : ''}`} role="dialog" aria-modal="true" aria-label={`You lead ${info.name}`}
    data-game-overlay data-testid="people-intro" data-people={faction}>
    <div className="et-art" aria-hidden="true">
      {art && <img src={art.small} srcSet={`${art.small} 1280w, ${art.large} 1920w`} sizes="100vw" alt="" draggable={false} />}
    </div>
    <div className="et-wash" aria-hidden="true" />
    <header className="et-head pi-head">
      <PortraitFrame faction={faction} className="pi-portrait" crestSize={46} />
      <div className="pi-title">
        <div className="et-kicker">You lead</div>
        <h2 className="et-title">{info.name}</h2>
        <p className="pi-motto">“{info.motto}”</p>
        <p className="pi-lore">{sheet.lore}</p>
      </div>
    </header>
    <section className="et-changes pi-cols" aria-label={`What sets ${info.name} apart`}>
      <div className="et-col" data-testid="people-intro-strengths">
        <h3>Your strengths</h3>
        {rows.map((p, i) => p.strength && p.strengthIcon && <MedallionRow key={i} icon={p.strengthIcon} tone="good" sign="Strength">{p.strength}</MedallionRow>)}
      </div>
      {rows.some((p) => p.price) && <div className="et-col" data-testid="people-intro-prices">
        <h3>What they cost</h3>
        {rows.map((p, i) => p.price && p.priceIcon && <MedallionRow key={i} icon={p.priceIcon} tone="bad" sign="Price">{p.price}</MedallionRow>)}
      </div>}
      {goal && <div className="et-col pi-goal" data-testid="people-intro-goal">
        <h3><Icon name={goal.icon} size={13} /> Your goal</h3>
        <div className="pi-goal-head"><b>{goal.name}</b><span><Amounts text={factionGoalTerms(faction)} /></span></div>
        <p><Amounts text={`${(goal.sheet ?? goal.detail)()}.`} /></p>
      </div>}
    </section>
    <footer className="et-foot pi-foot">
      <p className="et-rule-line">Your people’s full rules are in How to Play (?).</p>
      <div className="et-buttons">
        <button ref={primary} className="btn primary" data-primary-action onClick={begin}>Begin <span className="kbd">Return</span></button>
      </div>
    </footer>
  </div>;
}
