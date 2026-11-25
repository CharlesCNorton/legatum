// @vitest-environment happy-dom
// Deals (rules 61) in the diplomacy panel: the Gold field on an empire's offers and its forecast,
// Offer Open Borders and Close borders, Give Gold to a met empire at Peace, incoming offers that
// carry Gold, and the Open Borders mark.
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { FixtureClient, meetAll } from '../test/fixtureEngine';
import { useGame } from '../store';
import { DiplomacyPanel } from './DiplomacyPanel';
import type { PeaceProposal, PlayerView } from '../types';

let container: HTMLDivElement, root: Root, client: FixtureClient;
async function start({ deals = true, proposals = [] as PeaceProposal[], open = false, gold = 120 } = {}) {
  client = new FixtureClient();
  const setup = await client.standardSetup('700040', 'India', 'Byzantium', 'Ada', 'Bo');
  if (deals) setup.deals = true;
  await client.newGame(setup);
  const s = client.debugState();
  meetAll(s);
  s.diplomacy!.proposals = proposals;
  if (open) (s.diplomacy as unknown as { open_borders: [number, number][] }).open_borders = [[0, 1]];
  for (const p of s.players) p.gold = gold;
  const view = client.view(0);
  useGame.setState({ client, views: [view], humans: [0], orders: [[]], errors: [[]], ready: [false], seat: 0, diplomacyOpen: true, diplomacyTeam: 1 });
  return view;
}
beforeEach(() => {
  vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true);
  container = document.body.appendChild(document.createElement('div')); root = createRoot(container);
  useGame.setState(useGame.getInitialState(), true);
});
afterEach(() => { act(() => root.unmount()); container.remove(); vi.unstubAllGlobals(); });
const button = (prefix: string) => [...container.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent?.startsWith(prefix));
const text = () => container.textContent ?? '';
const orders = () => useGame.getState().orders[0];
const render = () => act(() => root.render(<DiplomacyPanel />));

it('without deals: no Gold field, no Open Borders, no Give Gold to another empire', async () => {
  const view = await start({ deals: false });
  expect(view.diplomacy.deals).toBeFalsy();
  render();
  expect(container.querySelector('[data-testid=deal-gold]')).toBeNull();
  expect(button('Offer Open Borders')).toBeUndefined();
  expect(container.querySelector('[data-testid=rival-gift]')).toBeNull();
});

it('an empire at Peace: offers lead under one Gold field whose forecast names the treasury', async () => {
  await start();
  render();
  const field = container.querySelector('[data-testid=deal-gold]')!;
  expect(field).toBeTruthy();
  expect(button('Offer Open Borders')).toBeTruthy();
  expect(button('Close borders')).toBeUndefined();
  // Offers come before Declare War when deals are on.
  const labels = [...container.querySelectorAll('.empire-detail .diplomacy-action > button')].map((b) => b.textContent);
  expect(labels.findIndex((l) => l?.startsWith('Offer Alliance'))).toBeLessThan(labels.findIndex((l) => l?.startsWith('Declare War')));
  act(() => button('You pay')!.click());
  expect(container.querySelector('[data-testid=deal-forecast]')!.textContent).toBe('You pay 50 Gold when they accept. You have 120 Gold.');
  act(() => (container.querySelector('button[aria-label="10 Gold less"]') as HTMLButtonElement).click());
  expect(container.querySelector('[data-testid=deal-forecast]')!.textContent).toBe('You pay 40 Gold when they accept. You have 120 Gold.');
  act(() => button('Offer Open Borders')!.click());
  expect(orders()).toEqual([{ type: 'ProposeTreaty', to: 1, kind: 'OpenBorders', gold: 40 }]);
  expect(button('Queued: Offer Open Borders with 40 Gold')).toBeTruthy();
  // Undo removes the queued offer whatever Gold it carries.
  act(() => button('Queued: Offer Open Borders')!.click());
  expect(orders()).toEqual([]);
});

it('asking for Gold queues a negative amount, and paying more than you have is refused in place', async () => {
  await start({ gold: 30 });
  render();
  act(() => button('You ask')!.click());
  expect(container.querySelector('[data-testid=deal-forecast]')!.textContent).toBe('They pay you 50 Gold when they accept.');
  act(() => button('Offer Alliance')!.click());
  expect(orders()).toEqual([{ type: 'ProposeTreaty', to: 1, kind: 'Alliance', gold: -50 }]);
  act(() => button('Queued: Offer Alliance')!.click());
  act(() => button('You pay')!.click());
  expect(container.querySelector('[data-testid=deal-forecast]')!.getAttribute('role')).toBe('alert');
  expect(text()).toContain('You have 30 Gold: offer at most 30.');
  expect(button('Offer Alliance')!.disabled).toBe(true);
  act(() => button('No Gold')!.click());
  expect(container.querySelector('[data-testid=deal-forecast]')).toBeNull();
  expect(button('Offer Alliance')!.disabled).toBe(false);
});

it('Give Gold to a met empire at Peace queues a gift to its leader', async () => {
  const view = await start();
  const leader = view.players.find((p) => p.team === 1)!.id;
  render();
  const gift = container.querySelector('[data-testid=rival-gift]')!;
  expect(gift.textContent).toContain('They get it next turn');
  act(() => (gift.querySelector('[data-testid=give-gold]') as HTMLButtonElement).click());
  expect(orders()).toEqual([{ type: 'GiveGold', to: leader, amount: 50 }]);
  expect(gift.querySelector('[data-testid=gift-queued]')).toBeTruthy();
});

it('Open Borders: the mark beside the treaty state, the passage line and Close borders', async () => {
  const view = await start({ open: true });
  expect(view.diplomacy.open_borders).toEqual([[0, 1]]);
  render();
  expect(container.querySelector('.empire-relation.open-borders')?.textContent).toBe('Open Borders');
  expect(text()).toContain('Open Borders let both sides’ units enter each other’s land');
  expect(button('Offer Open Borders')).toBeUndefined();
  act(() => button('Close borders')!.click());
  expect(orders()).toEqual([{ type: 'BreakTreaty', with: 1, agreement: 'OpenBorders' }]);
});

it('an incoming offer says its Gold in the headline and the For-you terms', async () => {
  const asks: PeaceProposal = { id: 1, kind: 'OpenBorders', from: 1, to: 0, proposer: 1, created_turn: 1, respond_by: 3, relation_version: 0, gold: -40 };
  let view: PlayerView = await start({ proposals: [asks] });
  render();
  const card = () => container.querySelector('.offer-card')!;
  expect(card().querySelector('.offer-headline')!.textContent).toMatch(/asks 40 Gold for Open Borders$/);
  expect(card().textContent).toContain('You pay 40 Gold. You have 120 Gold');
  expect(button('Accept Open Borders')).toBeTruthy();
  act(() => root.unmount()); root = createRoot(container);
  view = await start({ proposals: [{ ...asks, kind: 'Peace', gold: 40 }] });
  void view;
  render();
  expect(card().querySelector('.offer-headline')!.textContent).toMatch(/offers Peace and 40 Gold$/);
  expect(card().textContent).toContain('You get 40 Gold');
});
