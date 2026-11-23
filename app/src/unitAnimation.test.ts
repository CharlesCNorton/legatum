import { describe, expect, it } from 'vitest';
import fixture from './test/fixtures/unitAnimation/tiny.json';
import { animatedUnitsEnabled, clipFrame, parseAtlas, unitFrameDelay, visibleAtlasSlugs } from './unitAnimation';

describe('painted unit atlases', () => {
  it('accepts the fixture schema and rejects invalid anchors, rows and rates', () => {
    expect(parseAtlas(fixture)).not.toBeNull();
    expect(parseAtlas({ ...fixture, frame: { ...fixture.frame, ax: 2 } })).toBeNull();
    expect(parseAtlas({ ...fixture, clips: { ...fixture.clips, hit: { ...fixture.clips.hit, row: 2 } } })).toBeNull();
    expect(parseAtlas({ ...fixture, clips: { ...fixture.clips, move: { ...fixture.clips.move, fps: 0 } } })).toBeNull();
  });
  it('loops idle and move, and holds the final attack, hit and death cells', () => {
    const atlas = parseAtlas(fixture)!;
    expect(clipFrame(atlas, 'idle', 850)).toBe(0);
    expect(clipFrame(atlas, 'move', 750)).toBe(1);
    expect(clipFrame(atlas, 'attack', 10000)).toBe(9);
    expect(clipFrame(atlas, 'hit', 10000)).toBe(3);
    expect(clipFrame(atlas, 'death', 10000)).toBe(9);
  });
  it('requires both switches and allows reduced motion to stop playback', () => {
    expect(animatedUnitsEnabled(true, true, false)).toBe(true);
    for (const gate of [[false, true, false], [true, false, false], [true, true, true]] as const)
      expect(animatedUnitsEnabled(gate[0], gate[1], gate[2])).toBe(false);
  });
  it('requests only visible kinds and no idle animation frame when no atlas is running', () => {
    const units = [{ kind: 'spearman', seen: true }, { kind: 'horseman', seen: false }, { kind: 'spearman', seen: true }];
    expect([...visibleAtlasSlugs(units, u => u.seen, u => u.kind)]).toEqual(['spearman']);
    expect(unitFrameDelay(null, false)).toBeNull();
    expect(unitFrameDelay(10, false)).toBe(100);
    expect(unitFrameDelay(10, true)).toBe(0);
  });
});
