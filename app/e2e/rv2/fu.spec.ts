import { mkdir } from 'node:fs/promises';
import type { Page } from '@playwright/test';
import { test, expect } from '/home/user/legatum/app/e2e/fixtures';
import { dismissInterstitials } from '/home/user/legatum/app/e2e/turnActions';
import { coreFixture } from '/home/user/legatum/app/src/test/coreFixture';
import { researchFixture } from '/home/user/legatum/app/src/test/researchFixture';
import type { TechId } from '/home/user/legatum/app/src/types';

const SIZES = [{ width: 1000, height: 600 }, { width: 1440, height: 900 }];
const out = '/tmp/claude-0/-home-user/7cded06b-a56d-5e04-81b3-fd24439b3caf/scratchpad/rv/shots2/';
const KNOWN: TechId[] = ['Irrigation', 'BronzeWorking', 'Masonry', 'Currency', 'Writing', 'Mathematics', 'Engineering', 'IronWorking', 'CodeOfLaws', 'Philosophy', 'Feudalism', 'Education', 'CropRotation'];
const LATE: TechId[] = ['Irrigation', 'Masonry', 'BronzeWorking', 'Currency', 'Writing', 'Mathematics', 'Engineering', 'IronWorking', 'CodeOfLaws', 'Philosophy',
  'Feudalism', 'Machinery', 'Chivalry', 'CropRotation', 'Education', 'Gunpowder', 'MilitaryEngineering', 'Metallurgy', 'Banking', 'PrintingPress',
  'Rifling', 'Cannonry', 'MilitaryScience', 'Industrialization', 'Railways'];

async function load(page: Page, known: TechId[], view = 'tree', queue: TechId[] = []) {
  const f = researchFixture('Switzerland');
  f.players[0].techs = [...known];
  f.players[0].science = 60;
  f.players[1].techs = [...known];
  f.players[0].research = null as never;
  f.players[0].research_queue = queue as never;
  for (const c of f.cities) c.population = 6;
  const game = coreFixture(f);
  await page.addInitScript(({ game, view }) => {
    if (!location.protocol.startsWith('http')) return;
    localStorage.setItem('legatum.autosave.v1', JSON.stringify({ format: 'legatum-save', version: 1, client: 'wasm', turn: 2, names: ['Ada'], savedAt: new Date().toISOString(), game }));
    localStorage.setItem('legatum.first-game-hints.v2', JSON.stringify({ enabled: false, seen: [] }));
    localStorage.setItem('legatum.research-view.v1', view);
  }, { game, view });
  await page.goto('/?client=wasm');
  await page.getByRole('button', { name: /^Continue/ }).click();
  await expect(page.locator('.loading-screen')).toHaveCount(0);
  await dismissInterstitials(page);
  await page.locator('.topbar .research-chip').click();
  await expect(page.locator('dialog.tech-modal')).toBeVisible();
  await page.waitForTimeout(400);
}
async function shot(page: Page, size: { width: number; height: number }, name: string, move = true) {
  if (move) await page.mouse.move(size.width - 2, size.height - 2);
  await page.evaluate(() => document.fonts.ready.then(() => undefined));
  await page.waitForTimeout(400);
  await mkdir(`${out}${size.width}x${size.height}/`, { recursive: true });
  await page.screenshot({ path: `${out}${size.width}x${size.height}/${name}.png`, animations: 'disabled' });
}
test.describe.configure({ mode: 'parallel' });
async function edgeCheck(page: Page, side: 'left' | 'right') {
  return page.evaluate((side) => {
    const tree = document.querySelector('[data-testid="tech-tree"]')!.getBoundingClientRect();
    const btn = document.querySelector(`.tree-edge.${side}`)!.getBoundingClientRect();
    const res: any[] = [];
    for (const n of Array.from(document.querySelectorAll('.tree-node'))) {
      const r = n.getBoundingClientRect();
      const stripL = side === 'right' ? tree.right - 30 : tree.left;
      const stripR = side === 'right' ? tree.right : tree.left + 30;
      if (r.right <= stripL || r.left >= stripR || r.height === 0) continue;
      const pts = [];
      for (let y = r.top + 3; y < r.bottom - 2; y += 6) for (let x = Math.max(r.left + 2, stripL); x < Math.min(r.right - 2, stripR); x += 4) {
        if (y < tree.top || y > tree.bottom) continue;
        const el = document.elementFromPoint(x, y);
        const inBtn = x >= btn.left && x <= btn.right && y >= btn.top && y <= btn.bottom;
        pts.push({ hit: !!el && n.contains(el), inBtn });
      }
      res.push({ tech: (n as HTMLElement).dataset.tech, outside: pts.filter(p => !p.inBtn).length, outsideHit: pts.filter(p => !p.inBtn && p.hit).length, inBtn: pts.filter(p => p.inBtn).length });
    }
    return { btn: { x: btn.x, y: btn.y, w: btn.width, h: btn.height }, res };
  }, side);
}
for (const size of SIZES) {
  test(`fu early ${size.width}`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize(size);
    await load(page, KNOWN);
    const tree = page.getByTestId('tech-tree');
    await shot(page, size, 'a01-tree');
    console.log(size.width, 'right', JSON.stringify(await edgeCheck(page, 'right')));
    // click an edge node outside the chevron box
    const target = await page.evaluate(() => {
      const tree = document.querySelector('[data-testid="tech-tree"]')!.getBoundingClientRect();
      const btn = document.querySelector('.tree-edge.right')!.getBoundingClientRect();
      for (const n of Array.from(document.querySelectorAll('.tree-node.available, .tree-node.locked, .tree-node'))) {
        const r = n.getBoundingClientRect();
        if (r.right > tree.right - 28 && r.left < tree.right - 4 && r.bottom < tree.bottom && r.top > tree.top + 40 && (r.bottom < btn.top || r.top > btn.bottom)) return { tech: (n as HTMLElement).dataset.tech, x: Math.min(r.right - 4, tree.right - 8), y: r.top + r.height / 2 };
      }
      return null;
    });
    console.log(size.width, 'target', JSON.stringify(target));
    if (target) { await page.mouse.click(target.x, target.y); await page.waitForTimeout(400); await shot(page, size, 'a02-edge-node-clicked', false); }
    await page.getByRole('button', { name: 'Later eras' }).hover();
    await shot(page, size, 'a03-box-hover', false);
    await tree.locator('.tree-node[data-tech="Chivalry"]').click();
    await tree.locator('.tree-node[data-tech="Machinery"]').click({ modifiers: ['Shift'] });
    await shot(page, size, 'a04-queue-tree');
    await page.getByTestId('queue-rest').hover().catch(() => {});
    await shot(page, size, 'a04b-queue-hover', false);
    await page.getByTestId('research-view-era').click();
    await shot(page, size, 'a05-queue-era');
  });
  test(`fu late ${size.width}`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize(size);
    await load(page, LATE);
    await shot(page, size, 'b01-late');
    console.log(size.width, 'late-left', JSON.stringify(await edgeCheck(page, 'left')));
    const sc = page.getByTestId('tech-tree').locator('.tree-scroll');
    await sc.evaluate((el) => { el.scrollTop = 120; el.scrollLeft = Math.floor(el.scrollWidth / 3) + 37; });
    await shot(page, size, 'b02-pinned-scrolled');
    await sc.evaluate((el) => { el.scrollTop = el.scrollHeight; el.scrollLeft = 0; });
    await shot(page, size, 'b03-pinned-bottom-left');
    await sc.evaluate((el) => { el.scrollLeft = el.scrollWidth; });
    await shot(page, size, 'b04-pinned-bottom-right');
    console.log(size.width, 'late-left-after', JSON.stringify(await edgeCheck(page, 'left')));
  });
}
