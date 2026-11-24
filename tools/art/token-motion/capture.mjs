#!/usr/bin/env node
// Review a painted Spearman and compare the dense T131 map against master.
// Serve built app/dist for each branch, then run this script from any directory.
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../..');
const require = createRequire(import.meta.url);
const { chromium } = require(join(root, 'app/node_modules/playwright'));
const option = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i < 0 ? fallback : process.argv[i + 1]; };
const flag = (name) => process.argv.includes(`--${name}`);
const url = option('url', 'http://127.0.0.1:4173');
const masterUrl = option('master-url', null);
const save = resolve(option('save', join(root, 'out/perf-save-130-dense.json')));
const turn = Number(option('turn', '131'));
const review = join(here, 'review');
mkdirSync(review, { recursive: true });

async function clips() {
  const browser = await chromium.launch({ channel: option('channel', 'chrome'), headless: !flag('headed') });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
    const game = readFileSync(save, 'utf8');
    await page.addInitScript(({ game, turn }) => {
      localStorage.setItem('legatum.autosave.v1', JSON.stringify({ format: 'legatum-save', version: 1, client: 'wasm', turn, names: ['Me'], savedAt: new Date().toISOString(), game }));
      localStorage.setItem('legatum.first-game-hints.v2', JSON.stringify({ enabled: false, seen: [] }));
      localStorage.setItem('legatum.combat-fx', JSON.stringify({ enabled: true, animatedUnits: true }));
    }, { game, turn });
    await page.goto(`${url}/?client=wasm`);
    await page.getByRole('button', { name: /^Continue/ }).click();
    await page.getByTestId('turn-number').filter({ hasText: String(turn) }).waitFor({ timeout: 120000 });
    for (let i = 0; i < 8; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(80); }
    const unit = await page.evaluate(() => {
      const s = window.legatum.getState(), v = s.views[s.seat];
      const me = v.units.find((u) => u.owner === v.me && u.kind === 'Spearman');
      const any = me ?? v.units.find((u) => u.kind === 'Spearman');
      if (!any) throw new Error('The save contains no Spearman');
      s.select({ kind: 'unit', id: any.id });
      return { id: any.id, pos: any.pos };
    });
    await page.evaluate((pos) => {
      const map = window.legatumMap, c = map.camera;
      c.zoom = 2;
      const p = map.toScreen(pos);
      const r = document.querySelector('.map-canvas').getBoundingClientRect();
      c.x += (p.x - r.width / 2) / c.zoom; c.y += (p.y - r.height / 2) / c.zoom;
      map.redraw();
    }, unit.pos);
    await page.waitForTimeout(400);
    const durations = { idle: 2400, move: 600, attack: 1100, hit: 700, death: 1100 };
    for (const [kind, duration] of Object.entries(durations)) {
      const dir = join(review, kind); mkdirSync(dir, { recursive: true });
      await page.evaluate(({ id, kind }) => window.legatumMap.playTokenClip(id, kind, 0), { id: unit.id, kind });
      const start = Date.now(); let n = 0;
      while (Date.now() - start < duration) {
        await page.locator('.map-canvas').screenshot({ path: join(dir, `frame-${String(n++).padStart(3, '0')}.png`) });
        await page.waitForTimeout(33);
      }
      console.log(`${kind}: ${n} frames`);
    }
    writeFileSync(join(review, 'capture.json'), JSON.stringify({ unit, url, save, turn, capturedAt: new Date().toISOString() }, null, 2));
  } finally { await browser.close(); }
}

function perf() {
  if (!masterUrl) throw new Error('--master-url is required for the perf comparison');
  const script = join(root, 'tools/perf/battle-hover.cjs');
  const summary = {};
  for (const throttle of [1, 4]) {
    for (const [label, address] of [['master', masterUrl], ['motion', url]]) {
      const out = join(review, `perf-${label}-${throttle}x.json`);
      const args = [script, '--url', address, '--save', save, '--turn', String(turn), '--zoom', '2', '--dpr', '2', '--channel', option('channel', 'chrome'), '--throttle', String(throttle), '--out', out];
      const run = spawnSync(process.execPath, args, { cwd: root, stdio: 'inherit' });
      if (run.status !== 0) throw new Error(`Perf run failed: ${label} ${throttle}x (${run.status})`);
      summary[`${label}-${throttle}x`] = JSON.parse(readFileSync(out, 'utf8')).frameP95;
    }
  }
  summary.passed = summary['motion-1x'] <= summary['master-1x'] && summary['motion-4x'] <= summary['master-4x'];
  writeFileSync(join(review, 'perf-summary.json'), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
  if (!summary.passed) process.exitCode = 1;
}
if (!flag('perf-only')) await clips();
if (!flag('clips-only')) perf();
