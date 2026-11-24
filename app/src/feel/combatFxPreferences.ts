import { create } from 'zustand';

export const COMBAT_FX_KEY = 'legatum.combat-fx';

/** Map animations (combat playback and the other map moments, `map/combatFx.ts`): On or Off, on by default. */
export interface CombatFxPrefs {
  enabled: boolean;
  animatedUnits: boolean;
}

export const COMBAT_FX_DEFAULTS: Readonly<CombatFxPrefs> = { enabled: true, animatedUnits: true };

/** A saved Fast (the old third choice, removed 2026-10-24) reads as On: only `enabled` is kept. */
export function readCombatFxPrefs(): CombatFxPrefs {
  let raw: Partial<Record<keyof CombatFxPrefs, unknown>> = {};
  try { raw = JSON.parse(globalThis.localStorage?.getItem(COMBAT_FX_KEY) ?? '{}') ?? {}; }
  catch { /* Missing, blocked or corrupt storage: defaults. */ }
  return {
    enabled: typeof raw.enabled === 'boolean' ? raw.enabled : COMBAT_FX_DEFAULTS.enabled,
    animatedUnits: typeof raw.animatedUnits === 'boolean' ? raw.animatedUnits : COMBAT_FX_DEFAULTS.animatedUnits,
  };
}

export const useCombatFx = create<CombatFxPrefs & { update(patch: Partial<CombatFxPrefs>): void }>((set, get) => ({
  ...readCombatFxPrefs(),
  update: (patch) => {
    set(patch);
    const { enabled, animatedUnits } = get();
    try { globalThis.localStorage?.setItem(COMBAT_FX_KEY, JSON.stringify({ enabled, animatedUnits })); }
    catch { /* Keep the session preference when storage is unavailable. */ }
  },
}));
