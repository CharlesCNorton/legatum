import { describe, expect, it } from 'vitest';
import { ATTACK_MS, DEATH_MS, HIT_MS, IDLE_MS, attackPose, deathPose, hitPose, idlePose, makePose, movePose, unitsMayMove, idleVisible } from './tokenMotion';
import { COMBAT_FX_DEFAULTS } from '../feel/combatFxPreferences';

const pose = () => makePose();
describe('painted token clip timing', () => {
  it('idles on a 2.4 second loop with a small breath, sway, and one sweep', () => {
    const a = pose(), b = pose(); idlePose(600, a); idlePose(IDLE_MS + 600, b);
    expect(a).toEqual(b);
    expect(a.sy).toBeCloseTo(1.012);
    expect(a.rotation).toBeCloseTo(Math.PI / 360);
    expect(a.specular).toBe(.25);
  });
  it('hops, leans, shrinks its shadow, and lands with squash and dust', () => {
    const mid = pose(), land = pose(), start = pose();
    movePose(0, 0, 2, start); movePose(.5, 0, 2, mid); movePose(.94, 0, 2, land);
    expect(mid.dy).toBeCloseTo(-18);
    expect(mid.rotation * 180 / Math.PI).toBeCloseTo(5);
    expect(mid.shadow).toBeLessThan(1);
    expect(land.sy).toBeLessThan(1);
    expect(start.dust).toBe(1);
  });
  it('winds back, lunges, holds, sparks, and returns by 1.1 seconds', () => {
    const wind = pose(), lunge = pose(), held = pose(), done = pose();
    attackPose(350, 0, 2, wind); attackPose(450, 0, 2, lunge);
    attackPose(550, 0, 2, held); attackPose(ATTACK_MS, 0, 2, done);
    expect(wind.dx).toBeCloseTo(-10);
    expect(wind.rotation * 180 / Math.PI).toBeCloseTo(-5);
    expect(lunge.dx).toBeCloseTo(40);
    expect(lunge.rotation * 180 / Math.PI).toBeCloseTo(16);
    expect(held.dx).toBeCloseTo(40);
    expect(lunge.spark).toBe(1);
    expect(done.dx).toBe(0);
  });
  it('shakes and knocks away, fading the red tint in 0.35 seconds', () => {
    const first = pose(), late = pose(), done = pose();
    hitPose(0, 0, 2, first); hitPose(350, 0, 2, late); hitPose(HIT_MS, 0, 2, done);
    expect(first.red).toBeCloseTo(.32);
    expect(late.red).toBe(0);
    expect(done.dx).toBe(0);
  });
  it('recoils, tips to 60 degrees, desaturates and fades after 0.6 seconds', () => {
    const recoil = pose(), beforeFade = pose(), nearEnd = pose();
    deathPose(176, 0, recoil); deathPose(600, 0, beforeFade); deathPose(DEATH_MS - 1, 0, nearEnd);
    expect(recoil.rotation * 180 / Math.PI).toBeCloseTo(-6);
    expect(beforeFade.alpha).toBe(1);
    expect(nearEnd.rotation * 180 / Math.PI).toBeGreaterThan(59.8);
    expect(nearEnd.alpha).toBeLessThan(.01);
    expect(nearEnd.grey).toBeGreaterThan(.99);
  });
});

describe('motion gate', () => {
  it('requires both switches and allows no reduced motion', () => {
    expect(COMBAT_FX_DEFAULTS.animatedUnits).toBe(true);
    expect(unitsMayMove(true, true, false)).toBe(true);
    expect(unitsMayMove(false, true, false)).toBe(false);
    expect(unitsMayMove(true, false, false)).toBe(false);
    expect(unitsMayMove(true, true, true)).toBe(false);
  });
  it('idles only when selected, visible, and close', () => {
    expect(idleVisible(true, true, 2, true)).toBe(true);
    expect(idleVisible(true, false, 2, true)).toBe(false);
    expect(idleVisible(true, true, 1, true)).toBe(false);
    expect(idleVisible(true, true, 2, false)).toBe(false);
  });
});
