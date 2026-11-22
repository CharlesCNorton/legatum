import { describe, expect, it } from 'vitest';
import { FixtureClient } from '../test/fixtureEngine';
import { advisor_orders } from '../wasm-pkg/legatum.js';
import { neighbors } from '../hex';
import type { Order } from '../types';
import { advisorSuggestion, advisorWhy, type AdvisorContext } from './advisorModel';

async function opening() {
  const client = new FixtureClient();
  await client.newGame(await client.standardSetup('4545', 'Athens', 'India', 'Ada', 'Bo'));
  const view = client.view(0);
  const city = view.cities.find((c) => c.owner === view.me)!;
  const unit = view.units.find((u) => u.owner === view.me)!;
  const build = city.detail!.options[0].item;
  const tech = view.research.available[0].tech;
  const plan: Order[] = [
    { type: 'SetProduction', city: city.id, item: build },
    { type: 'MoveUnit', unit: unit.id, to: neighbors(unit.pos)[0] },
    { type: 'SetResearch', tech },
  ];
  const ctx = (orders: Order[] = [], selection: AdvisorContext['selection'] = null, chosen: Order[] | null = plan): AdvisorContext =>
    ({ view, orders, selection, plan: chosen, humans: 1, touch: false });
  return { view, city, unit, build, tech, plan, ctx };
}

describe('one decision at a time', () => {
  it('welcomes once, then follows turn-one city, unit, research order', async () => {
    const { city, unit, plan, ctx } = await opening();
    expect(advisorSuggestion(ctx(), [], [])?.id).toBe('welcome');
    expect(advisorSuggestion(ctx(), ['welcome'], [])).toMatchObject({ id: `city:${city.id}`, current: 0 });
    expect(advisorSuggestion(ctx([], { kind: 'city', id: city.id }), ['welcome'], [])).toMatchObject({ id: `city:${city.id}`, current: 1 });
    const cityDone = [plan[0]];
    expect(advisorSuggestion(ctx(cityDone), ['welcome'], [])?.id).toBe(`unit:${unit.id}`);
    expect(advisorSuggestion(ctx(cityDone, { kind: 'unit', id: unit.id }), ['welcome'], [])).toMatchObject({ id: `unit:${unit.id}`, current: 1 });
    const unitDone = [...cityDone, ...plan.filter((o) => o.type === 'MoveUnit' || o.type === 'MoveUnitPath').map((o) => ({ ...o, type: 'SkipUnit' as const }))];
    expect(advisorSuggestion(ctx(unitDone), ['welcome'], [])?.id).not.toBe(`unit:${unit.id}`);
    expect(advisorSuggestion(ctx(unitDone), ['welcome'], [])?.title).toBeTruthy();
  });

  it('follows the screen: the open Research panel or the selected unit comes first', async () => {
    const { city, unit, plan, ctx } = await opening();
    expect(advisorSuggestion({ ...ctx([plan[0]]), techOpen: true }, ['welcome'], [])?.id).toBe('research');
    expect(advisorSuggestion(ctx([], { kind: 'unit', id: unit.id }), ['welcome'], [])?.id).toBe(`unit:${unit.id}`);
    expect(advisorSuggestion(ctx([], { kind: 'city', id: city.id }), ['welcome'], [])?.id).toBe(`city:${city.id}`);
  });

  it('accepts a different build and research choice as that decision made', async () => {
    const { city, view, ctx } = await opening();
    const chosen = city.detail!.options.at(-1)!.item;
    expect(advisorSuggestion(ctx([{ type: 'SetProduction', city: city.id, item: chosen }]), ['welcome'], [])?.id).not.toBe(`city:${city.id}`);
    const available = view.research.available.map((t) => t.tech);
    const alternative = available.at(-1)!;
    const orders: Order[] = [{ type: 'SetProduction', city: city.id, item: chosen }, { type: 'SetResearch', tech: alternative }];
    expect(advisorSuggestion(ctx(orders), ['welcome'], [])?.id).not.toBe('research');
  });

  it('falls back to a basic instruction if the plan is unavailable', async () => {
    const { city, ctx } = await opening();
    const s = advisorSuggestion(ctx([], null, null), ['welcome'], []);
    expect(s).toMatchObject({ id: `city:${city.id}`, title: `Choose a build in ${city.name}` });
    expect(s!.steps[1].instruction).toBe('Choose a unit or building to build.');
  });

  it('skips one suggestion for the turn without changing orders', async () => {
    const { city, ctx } = await opening();
    expect(advisorSuggestion(ctx(), ['welcome'], [`city:${city.id}`])?.id).not.toBe(`city:${city.id}`);
  });

  it('points to End turn only when every pending decision is made', async () => {
    const { view, plan, ctx } = await opening();
    const orders: Order[] = [plan[0], plan[2], ...view.units.filter((u) => u.owner === view.me).map((u) => ({ type: 'SkipUnit' as const, unit: u.id }))];
    expect(advisorSuggestion(ctx(orders), ['welcome'], [])).toMatchObject({ id: 'endTurn', steps: [{ target: { kind: 'control', name: 'turn' } }] });
  });

  it('shows report once after turn one and the VP lesson around turn eight', async () => {
    const { view, ctx } = await opening();
    view.turn = 2;
    expect(advisorSuggestion(ctx(), ['welcome'], [])?.id).toBe('report');
    view.turn = 8;
    expect(advisorSuggestion(ctx(), ['welcome', 'report'], [])?.id).toBe('race');
    expect(advisorSuggestion(ctx(), ['welcome', 'report', 'race'], [])?.id).not.toBe('race');
  });

  it('never invents battle odds', async () => {
    const { view, unit } = await opening();
    const to = neighbors(unit.pos)[0];
    const order: Order = { type: 'MoveUnit', unit: unit.id, to };
    const why = advisorWhy(order, view, undefined, unit);
    expect(why).not.toMatch(/%/);
  });

  it('the first-run tour seed has a Hard move to teach', async () => {
    const client = new FixtureClient();
    await client.newGame(await client.standardSetup('424242', 'Athens', 'India', 'Ada', 'Bo'));
    const plan = JSON.parse(advisor_orders(JSON.stringify(client.view(0)))) as Order[];
    expect(plan.some((o) => o.type === 'MoveUnit' || o.type === 'MoveUnitPath')).toBe(true);
  });
});
