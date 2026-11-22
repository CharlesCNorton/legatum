// Rome's Colonia Victrix and Egypt's Royal Tomb through the real engine: the screen-tour fixtures load, the public
// view lists the goal cities, and the UI's text helpers read that view.
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { beforeAll, describe, expect, it } from 'vitest';
import { WasmClient } from '../wasmClient';
import { coreFixture } from './coreFixture';
import { goalCitiesFixture, type GoalCityMode } from './goalCitiesFixture';
import { goalCitiesAt, goalCityLine, tombPublicLine, tombStatus } from '../goalCities';
import { bannerTooltip } from '../map/bannerTooltip';

const available = existsSync(fileURLToPath(new URL('../wasm-pkg/legatum.js', import.meta.url)));
let makeCore: () => WasmClient;

function viewOf(mode: GoalCityMode) {
  const f = goalCitiesFixture(mode);
  const core = makeCore();
  core.load(coreFixture(f.fixture));
  return { f, view: core.view(0) };
}

describe.skipIf(!available)('goal cities through the engine', () => {
  beforeAll(async () => {
    const pkg = '../wasm-pkg/legatum.js', mod = await import(/* @vite-ignore */ pkg);
    await mod.default({ module_or_path: readFileSync(fileURLToPath(new URL('../wasm-pkg/legatum_bg.wasm', import.meta.url))) });
    makeCore = () => new WasmClient(mod.Game);
  });

  it('Rome before and ready: the best veteran level and the founder', () => {
    expect(viewOf('romeBefore').view.actions?.colonia?.best).toBe(2);
    const { f, view } = viewOf('romeReady');
    expect(view.actions?.colonia?.best).toBe(3);
    expect(view.actions?.colonia?.founders).toContain(f.veteran);
    expect(view.colonias ?? []).toEqual([]);
  });

  it('a rival sees the Colonia, and its banner names it first', () => {
    const { f, view } = viewOf('romeRival');
    expect(view.colonias).toHaveLength(1);
    expect(view.colonias![0]).toMatchObject({ of: 1, holder: 1, city: f.colonia });
    const city = view.cities.find((c) => c.id === f.colonia)!;
    expect(goalCitiesAt(view, city.id)).toHaveLength(1);
    expect(goalCitiesAt(view, city.id)[0].kind).toBe('colonia');
    expect(bannerTooltip(view, city).startsWith('Colonia Victrix of')).toBe(true);
    expect(goalCityLine(view, goalCitiesAt(view, city.id)[0])).toBe("Rome's Colonia Victrix: Rome scores 2 VP while holding it. Take the city to take the points.");
  });

  it('a captured Colonia goes to its holder', () => {
    const { view } = viewOf('romeLost');
    expect(view.colonias![0]).toMatchObject({ of: 0, holder: 1 });
  });

  it('Egypt at work: the count is public and the own view has the tomb action', () => {
    const own = viewOf('egyptWork').view;
    expect(own.actions?.tomb).toMatchObject({ working: true, turns: 6, target: 15 });
    expect(tombStatus(own.players[0])).toMatchObject({ working: true, turns: 6 });
    const rival = viewOf('egyptRival').view;
    expect(rival.players[1].tomb_work).toBe(true);
    expect(rival.players[1].tomb_turns).toBe(6);
    expect(tombPublicLine(tombStatus(rival.players[1])!)).toMatch(/6 of 15/);
  });

  it('the standing tomb is public', () => {
    const { f, view } = viewOf('tombRival');
    expect(view.royal_tombs).toEqual([expect.objectContaining({ of: 1, holder: 1, city: f.a })]);
  });
});
