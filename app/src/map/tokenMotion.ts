// Painted-token motion. All distances below are CSS px at 2x map zoom.
// Samples write into one caller-owned record; the canvas draw loop reuses it for every visible unit.
import type { CombatPlan, FxClash, FxShot, Pt } from './combatFx';

export const IDLE_MS = 2400;
export const ATTACK_MS = 1100;
export const HIT_MS = 700;
export const DEATH_MS = 1100;
const RAD = Math.PI / 180;
const clamp = (v: number) => Math.max(0, Math.min(1, v));
const smooth = (v: number) => { const k = clamp(v); return k * k * (3 - 2 * k); };
export const unitsMayMove = (animated: boolean, animations: boolean, reduced: boolean) => animated && animations && !reduced;
export const idleVisible = (on: boolean, selected: boolean, zoom: number, visible: boolean) => on && selected && zoom >= 1.25 && visible;
export interface TokenClip { kind: 'idle' | 'move' | 'attack' | 'hit' | 'death'; direction: number; elapsed?: number }

export interface TokenPose {
  dx: number; dy: number; rotation: number; sx: number; sy: number;
  shadow: number; red: number; grey: number; alpha: number;
  specular: number; dust: number; spark: number; tipX: number; tipY: number;
}
export const makePose = (): TokenPose => ({ dx: 0, dy: 0, rotation: 0, sx: 1, sy: 1, shadow: 1, red: 0, grey: 0, alpha: 1, specular: -1, dust: 0, spark: 0, tipX: 0, tipY: 0 });
export function resetPose(p: TokenPose): void {
  p.dx = p.dy = p.rotation = p.red = p.grey = p.dust = p.spark = p.tipX = p.tipY = 0;
  p.sx = p.sy = p.shadow = p.alpha = 1; p.specular = -1;
}
export function idlePose(t: number, p: TokenPose): void {
  const k = ((t % IDLE_MS) + IDLE_MS) % IDLE_MS / IDLE_MS;
  p.sy = 1 + 0.012 * Math.sin(k * Math.PI * 2);
  p.rotation = 0.5 * RAD * Math.sin(k * Math.PI * 2);
  p.specular = k;
}
export function movePose(k: number, direction: number, zoom: number, p: TokenPose): void {
  const v = clamp(k);
  p.dy -= 9 * zoom * Math.sin(Math.PI * v);
  p.rotation += 5 * RAD * Math.sin(Math.PI * v) * (Math.cos(direction) >= 0 ? 1 : -1);
  const land = Math.max(0, 1 - Math.abs(v - 0.94) / 0.06);
  p.sy *= 1 - 0.12 * land; p.sx *= 1 + 0.08 * land;
  p.shadow = 1 - 0.35 * Math.sin(Math.PI * v);
  p.dust = Math.max(0, 1 - v / 0.16, 1 - (1 - v) / 0.16);
}
export function attackPose(dt: number, direction: number, zoom: number, p: TokenPose): void {
  if (dt < 0 || dt >= ATTACK_MS) return;
  let reach: number, lean: number;
  if (dt < 350) { const k = smooth(dt / 350); reach = -5 * k; lean = -5 * k; }
  else if (dt < 450) { const k = clamp((dt - 350) / 100); reach = -5 + 25 * k * k; lean = -5 + 21 * k * k; }
  else if (dt < 600) { reach = 20; lean = 16; }
  else { const k = smooth((dt - 600) / 500); reach = 20 * (1 - k); lean = 16 * (1 - k); }
  p.dx += Math.cos(direction) * reach * zoom; p.dy += Math.sin(direction) * reach * zoom;
  p.rotation += lean * RAD * (Math.cos(direction) >= 0 ? 1 : -1);
  p.spark = dt >= 450 && dt < 750 ? 1 - (dt - 450) / 300 : 0;
  p.tipX = Math.cos(direction); p.tipY = Math.sin(direction);
}
export function hitPose(dt: number, direction: number, zoom: number, p: TokenPose): void {
  if (dt < 0 || dt >= HIT_MS) return;
  const decay = 1 - dt / HIT_MS;
  p.dx += Math.cos(direction) * 5 * zoom * smooth(Math.min(1, dt / 120)) * decay;
  p.dy += Math.sin(direction) * 5 * zoom * smooth(Math.min(1, dt / 120)) * decay;
  p.dx += Math.sin(dt / 35 * Math.PI) * 3.5 * zoom * decay;
  p.red = dt < 350 ? 0.32 * (1 - dt / 350) : 0;
}
export function deathPose(dt: number, direction: number, p: TokenPose): void {
  if (dt < 0 || dt >= DEATH_MS) return;
  const k = clamp(dt / DEATH_MS);
  p.rotation += (k < 0.16 ? -6 * smooth(k / 0.16) : -6 + 66 * Math.pow(clamp((k - 0.16) / 0.84), 2)) * RAD * (Math.cos(direction) >= 0 ? 1 : -1);
  p.grey = k; p.alpha = dt < 600 ? 1 : 1 - (dt - 600) / 500;
  p.dust = dt > 450 ? Math.max(0, 1 - (dt - 450) / 650) : 0;
}

interface Events { attacks: FxClash[]; hits: FxClash[]; shots: FxShot[] }
const indexed = new WeakMap<CombatPlan, Map<number, Events>>();
export const hasPlaybackMotion = (plan: CombatPlan, id: number): boolean =>
  plan.moves.has(id) || !!eventsFor(plan, id);
function eventsFor(plan: CombatPlan, id: number): Events | undefined {
  let byUnit = indexed.get(plan);
  if (!byUnit) {
    byUnit = new Map();
    const entry = (key: number) => { let e = byUnit!.get(key); if (!e) { e = { attacks: [], hits: [], shots: [] }; byUnit!.set(key, e); } return e; };
    for (const c of plan.clashes) { if (c.attacker != null) entry(c.attacker).attacks.push(c); if (c.defender != null && c.hit) entry(c.defender).hits.push(c); }
    for (const s of plan.shots) { if (s.shooter != null) entry(s.shooter).shots.push(s); if (s.target != null && s.hit) entry(s.target).shots.push(s); }
    indexed.set(plan, byUnit);
  }
  return byUnit.get(id);
}
const angle = (a: Pt, b: Pt) => Math.atan2(b.y - a.y, b.x - a.x);
/** Sample only after the renderer's screen-space cull. */
export function playbackPose(plan: CombatPlan, id: number, t: number, zoom: number, p: TokenPose): void {
  const steps = plan.moves.get(id);
  if (steps) for (const step of steps) {
    if (t < step.t0 || t > step.t1) continue;
    const length = step.path.length - 1;
    const part = clamp((t - step.t0) / (step.t1 - step.t0)) * length;
    const i = Math.min(length - 1, Math.floor(part));
    movePose(part - i, angle(step.path[i], step.path[i + 1]), zoom, p);
    break;
  }
  const e = eventsFor(plan, id);
  if (!e) return;
  for (const c of e.attacks) attackPose(t - (c.t - 450), angle(c.from, c.to), zoom, p);
  for (const c of e.hits) hitPose(t - c.t, angle(c.from, c.to), zoom, p);
  for (const s of e.shots) {
    if (s.shooter === id) attackPose(t - (s.launch - 450), angle(s.from, s.to), zoom, p);
    if (s.target === id && s.hit) hitPose(t - s.launch - s.flight, angle(s.from, s.to), zoom, p);
  }
}
