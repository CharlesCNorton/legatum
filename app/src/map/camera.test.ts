import { describe, expect, it } from 'vitest';
import { registerMapCamera, takeMapHandoff } from './camera';

const host = (x: number, y: number) => ({ viewport: () => ({ x, y, zoom: 1, w: 800, h: 600 }), center: () => {} });

describe('map camera handoff', () => {
  it('passes the closing map centre to the map that opens right after (2D / 3D swap)', () => {
    registerMapCamera(host(120, 340))();
    expect(takeMapHandoff()).toMatchObject({ x: 120, y: 340 });
    expect(takeMapHandoff()).toBeNull();
  });
  it('ignores a map that closed a while ago, so a new game starts on its capital', () => {
    registerMapCamera(host(5, 6))();
    expect(takeMapHandoff(Date.now() + 5000)).toBeNull();
  });
});
