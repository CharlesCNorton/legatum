/** Pure atlas rules shared by the loader and map playback. */
export const CLIPS = ['idle', 'move', 'attack', 'hit', 'death'] as const;
export type UnitClip = typeof CLIPS[number];
export interface AtlasSpec {
  frame: { w: number; h: number; ax: number; ay: number };
  clips: Record<UnitClip, { row: number; frames: number; fps: number; loop: boolean }>;
}

export function parseAtlas(value: unknown): AtlasSpec | null {
  if (!value || typeof value !== 'object') return null;
  const v = value as Record<string, unknown>;
  if (!v.frame || typeof v.frame !== 'object' || !v.clips || typeof v.clips !== 'object') return null;
  const frame = v.frame as Record<string, unknown>;
  const clips = v.clips as Record<string, unknown>;
  const positive = (n: unknown) => typeof n === 'number' && Number.isInteger(n) && n > 0;
  if (!positive(frame.w) || !positive(frame.h) || typeof frame.ax !== 'number' || typeof frame.ay !== 'number'
    || !Number.isFinite(frame.ax) || !Number.isFinite(frame.ay) || frame.ax < 0 || frame.ay < 0 || frame.ax > (frame.w as number) || frame.ay > (frame.h as number)) return null;
  for (const [row, name] of CLIPS.entries()) {
    const clip = clips[name] as Record<string, unknown> | undefined;
    if (!clip || clip.row !== row || !positive(clip.frames) || !positive(clip.fps) || typeof clip.loop !== 'boolean' || clip.loop !== (name === 'idle' || name === 'move')) return null;
  }
  return value as AtlasSpec;
}

export function clipFrame(spec: AtlasSpec, clip: UnitClip, elapsedMs: number): number {
  const c = spec.clips[clip];
  const n = Math.max(0, Math.floor(Math.max(0, elapsedMs) * c.fps / 1000));
  return c.loop ? n % c.frames : Math.min(c.frames - 1, n);
}

export function animatedUnitsEnabled(units: boolean, map: boolean, reduced: boolean): boolean {
  return units && map && !reduced;
}

export function visibleAtlasSlugs<T>(units: readonly T[], visible: (unit: T) => boolean, slug: (unit: T) => string): Set<string> {
  return new Set(units.filter(visible).map(slug));
}

/** A unit idle by itself asks for one frame at its atlas rate; no other unit motion uses this timer. */
export function unitFrameDelay(fps: number | null, otherMotion: boolean): number | null {
  return otherMotion ? 0 : fps && fps > 0 ? 1000 / fps : null;
}
