// The live main-map camera, shared with the minimap (and anything else that needs to pan the map
// or show where it looks). MapCanvas owns the camera; it registers here and reports changes after
// each drawn frame, so listeners hear about pans and zooms without polling.
/** What the main map shows: camera center and zoom (world px) and canvas size (CSS px). */
export interface MapViewport {
  x: number;
  y: number;
  zoom: number;
  w: number;
  h: number;
}

interface Host {
  viewport(): MapViewport;
  /** Snap the camera center to a world point, cancelling any focus animation. */
  center(x: number, y: number): void;
}

let host: Host | null = null;
const listeners = new Set<() => void>();
/** Where the map that just unmounted was looking, so the 2D and 3D maps can swap in place. */
let handoff: { vp: MapViewport; at: number } | null = null;

/** MapCanvas and Map3DView only. Returns the unregister function. */
export function registerMapCamera(h: Host): () => void {
  host = h;
  return () => {
    if (host !== h) return;
    try { handoff = { vp: h.viewport(), at: Date.now() }; } catch { handoff = null; }
    host = null;
  };
}

/** A map that mounts right after another unmounted (a 2D / 3D swap, not a new game) takes over its centre.
 *  Returns null when the last map closed more than a moment ago, e.g. before a new game. */
export function takeMapHandoff(now = Date.now()): MapViewport | null {
  const h = handoff;
  handoff = null;
  return h && now - h.at < 1500 ? h.vp : null;
}

/** MapCanvas only: the camera or canvas size changed this frame. */
export function notifyMapCamera(): void {
  for (const fn of listeners) fn();
}

export function mapViewport(): MapViewport | null {
  return host?.viewport() ?? null;
}

export function onMapCamera(fn: () => void): () => void {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}

/** Snap the main map to a world point (world px). */
export function centerOnWorld(x: number, y: number): void {
  host?.center(x, y);
}
