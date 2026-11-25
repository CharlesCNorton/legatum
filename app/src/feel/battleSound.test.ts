import { describe, expect, it } from 'vitest';
import type { CombatPlan } from '../map/combatFx';
import { battleSoundCues, CUE_MERGE_MS, MAX_BATTLE_CUES } from './battleSound';

const plan = (p: Partial<Record<'shots' | 'clashes' | 'deaths' | 'captures', unknown[]>>) =>
  ({ shots: [], clashes: [], deaths: [], captures: [], ...p }) as unknown as CombatPlan;
const names = (p: CombatPlan) => battleSoundCues(p).map((c) => `${c.sound}@${c.t}`);

describe('battle sound cues', () => {
  it('has nothing to say without a battle', () => {
    expect(battleSoundCues(null)).toEqual([]);
    expect(battleSoundCues(plan({}))).toEqual([]);
  });

  it('sounds a volley as it leaves and as it lands, and only a hit lands', () => {
    expect(names(plan({ shots: [
      { kind: 'arrows', launch: 100, flight: 500, hit: true, seed: 1 },
      { kind: 'bolts', launch: 900, flight: 400, hit: false, seed: 2 },
      { kind: 'stone', launch: 1500, flight: 800, hit: true, seed: 3 },
    ] }))).toEqual(['bow@100', 'arrowHit@600', 'bow@900', 'siegeLaunch@1500', 'siegeHit@2300']);
  });

  it('keeps guns, cannon, shells and aircraft silent: there is no recording for them yet', () => {
    expect(names(plan({
      shots: ['shot', 'ball', 'shell', 'drone', 'bombs'].map((kind) => ({ kind, launch: 0, flight: 300, hit: true, seed: 1 })),
      clashes: [{ t: 500, mounted: false, guns: true, seed: 1 }],
      deaths: [{ unit: { kind: 'Rifleman' }, t: 700, seed: 1 }, { unit: { kind: 'Tank' }, t: 900, seed: 1 }],
    }))).toEqual([]);
  });

  it('leads a mounted charge with hooves, voices an old-world unit’s fall and a razed city’s collapse', () => {
    expect(names(plan({
      clashes: [{ t: 1000, mounted: true, guns: false, seed: 5 }, { t: 100, mounted: true, guns: false, seed: 6 }],
      deaths: [{ unit: { kind: 'Spearman' }, t: 1300, seed: 1 }],
      captures: [{ t: 2000, razed: true, city: 3 }, { t: 2600, razed: false, city: 4 }],
    }))).toEqual(['hooves@0', 'clash@100', 'hooves@550', 'clash@1000', 'death@1300', 'collapse@2000']);
  });

  it('merges the same sound struck together and caps a crowded turn at its first blows', () => {
    const together = plan({ clashes: [0, 40, CUE_MERGE_MS - 1, CUE_MERGE_MS + 5].map((t) => ({ t, mounted: false, guns: false, seed: t })) });
    expect(names(together)).toEqual(['clash@0', `clash@${CUE_MERGE_MS + 5}`]);
    const crowded = plan({ clashes: Array.from({ length: 40 }, (_, i) => ({ t: i * 300, mounted: false, guns: false, seed: i })) });
    const cues = battleSoundCues(crowded);
    expect(cues).toHaveLength(MAX_BATTLE_CUES);
    expect(cues.at(-1)!.t).toBe((MAX_BATTLE_CUES - 1) * 300);
  });
});
