// PROTOTYPE shots for the tech tree proposal (not for merge).
import { mkdir } from 'node:fs/promises';
import type { Page } from '@playwright/test';
import { test, expect } from './fixtures';
import { dismissInterstitials } from './turnActions';
import { coreFixture } from '../src/test/coreFixture';
import { researchFixture } from '../src/test/researchFixture';
import type { TechId } from '../src/types';

const out = '/mnt/project-files/tech-tree/shots/';
const SIZES = [{ width: 1000, height: 600 }, { width: 1440, height: 900 }];
const KNOWN: TechId[] = ['Irrigation', 'BronzeWorking', 'Masonry', 'Currency', 'Writing', 'Mathematics', 'Engineering', 'IronWorking', 'CodeOfLaws', 'Philosophy', 'Feudalism', 'Education', 'CropRotation'];

async function load(page: Page, query: string) {
  const f = researchFixture('Switzerland');
  f.players[0].techs = [...KNOWN];
  f.players[0].science = 60;
  f.players[1].techs = [...KNOWN, 'Chivalry'];
  f.players[0].research = null as never;
  f.players[0].research_queue = [] as never;
  for (const c of f.cities) c.population = 6;
  const game = coreFixture(f);
  await page.addInitScript(({ game }) => {
    if (!location.protocol.startsWith('http')) return;
    localStorage.setItem('legatum.autosave.v1', JSON.stringify({ format: 'legatum-save', version: 1, client: 'wasm', turn: 2, names: ['Ada'], savedAt: new Date().toISOString(), game }));
    localStorage.setItem('legatum.first-game-hints.v2', JSON.stringify({ enabled: false, seen: [] }));
    localStorage.setItem('legatum.advisor.v1', JSON.stringify({ enabled: false }));
  }, { game });
  await page.goto(`/?client=wasm${query}`);
  await page.getByRole('button', { name: /^Continue/ }).click();
  await expect(page.locator('.loading-screen')).toHaveCount(0);
  await dismissInterstitials(page);
  await page.locator('.topbar .research-chip').click();
  await expect(page.locator('dialog.tech-modal')).toBeVisible();
  await page.waitForTimeout(400);
}

async function shot(page: Page, size: { width: number; height: number }, name: string) {
  await page.mouse.move(size.width - 2, size.height - 2);
  await page.evaluate(() => document.fonts.ready.then(() => undefined));
  await page.waitForTimeout(800);
  await mkdir(`${out}${size.width}x${size.height}/`, { recursive: true });
  await page.screenshot({ path: `${out}${size.width}x${size.height}/${name}.png`, animations: 'disabled' });
}

for (const size of SIZES) {
  test(`tech tree shots ${size.width}x${size.height}`, async ({ page }) => {
    test.setTimeout(180_000);
    await page.setViewportSize(size);
    await load(page, '');
    await page.locator('.era-card[data-tech="Chivalry"]').click();
    await shot(page, size, '0-today-this-era');
    await page.getByRole('button', { name: 'Tech tree' }).click();
    await shot(page, size, '1-tree');
    await page.locator('.tree-node[data-tech="Gunpowder"]').click();
    await shot(page, size, '1-tree-goal');
  });
  test(`tech tree option 2 ${size.width}x${size.height}`, async ({ page }) => {
    await page.setViewportSize(size);
    await load(page, '&tree=era-links');
    await shot(page, size, '2-era-links');
  });
  test(`tech tree option 3 ${size.width}x${size.height}`, async ({ page }) => {
    await page.setViewportSize(size);
    await load(page, '&tree=open');
    await page.locator('.tree-node[data-tech="Banking"]').click();
    await shot(page, size, '3-open');
  });
}
