#!/usr/bin/env node
/* Headless gallery QA. Run after all four atlases exist; never invent timings. */
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const http = require('node:http');
const { chromium } = require('playwright');
const repo = path.resolve(__dirname, '../../..');
const pass = process.argv[2] || '1';
if (!/^\d+$/.test(pass)) throw Error('Pass must be a positive integer');
const out = path.join(os.homedir(), 'LegatumRuns/anim-pilot/review', `pass-${pass}`);
fs.mkdirSync(out, {recursive: true});
const mime = {'.html':'text/html', '.png':'image/png', '.webp':'image/webp', '.json':'application/json'};
const server = http.createServer((req,res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  let file = path.resolve(repo, '.' + pathname);
  if (!file.startsWith(repo + path.sep)) { res.writeHead(403).end(); return; }
  if (pathname.endsWith('/')) file = path.join(file,'index.html');
  fs.readFile(file, (err,data) => {
    if(err) {res.writeHead(404).end();return;}
    res.writeHead(200, {'Content-Type':mime[path.extname(file)] || 'application/octet-stream'});res.end(data);
  });
});
(async()=>{
 let browser;
 try {
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  browser=await chromium.launch();
  const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/tools/art/anim/gallery/`);
  await page.waitForFunction(()=>window.reviewAPI?.ready,{},{timeout:15000});
  await page.evaluate(()=>window.reviewAPI.pause());
  const sizes=await page.evaluate(()=>window.reviewAPI.assets);
  assert.equal(sizes.length,4,'All four rendered atlases must load');
  for(const a of sizes) assert(a.bytes<=200000,`${a.slug}: atlas exceeds 200 KB`);
  for(const a of sizes) for(const clip of ['idle','move','attack','hit','death']) {
   const count=a.clips[clip].frames;
   const frame=clip==='death'?count-1:clip==='hit'?1:clip==='attack'?(count===6?3:4):Math.min(2,count-1);
   await page.evaluate(({slug,clip,frame})=>window.reviewAPI.setFrame(slug,clip,frame),{slug:a.slug,clip,frame});
   const card=page.locator(`#${a.slug} [data-clip="${clip}"]`);
   assert.deepEqual(await card.locator('.large').evaluate(el=>[el.getBoundingClientRect().width,el.getBoundingClientRect().height]),[256,256],'Inspection must display at native size');
   await card.locator('.large').screenshot({path:path.join(out,`${a.slug}-${clip}-256.png`)});
   await card.locator('.map').screenshot({path:path.join(out,`${a.slug}-${clip}-map.png`)});
  }
  // Backdrop/mirroring and every control are exercised rather than assumed.
  await page.locator('#mirror').check();await page.locator('#backdrop').selectOption('#f2ead8');
  await page.locator('#terrain').selectOption('plains');
  await page.locator('#spearman .clips').screenshot({path:path.join(out,'spearman-mirrored-parchment.png')});
  await page.locator('#mirror').uncheck();await page.locator('#backdrop').selectOption('#888888');
  await page.locator('#terrain').selectOption('grass');
  const idle=page.locator('#spearman [data-clip="idle"]');
  const before=await idle.locator('output').textContent();await idle.locator('.step').click();
  assert.notEqual(await idle.locator('output').textContent(),before,'Step must advance the selected clip');
  await page.locator('#speed').evaluate(el=>{el.value='0.5';el.dispatchEvent(new Event('input',{bubbles:true}));});
  assert.equal(await page.locator('#speed-value').textContent(),'0.5×');
  const stress=[];
  for(const count of [300,600]){
   await page.locator('#count').selectOption(String(count));
   stress.push(await page.evaluate(count=>window.reviewAPI.benchmark(count),count));
   await page.locator('#stress').screenshot({path:path.join(out,`stress-${count}.png`)});
  }
  await page.setViewportSize({width:1000,height:600});await page.screenshot({path:path.join(out,'gallery-1000.png')});
  const result={pass:Number(pass),deviceScaleFactor:1,browser:browser.version(),atlases:sizes,stress,errors};
  fs.writeFileSync(path.join(out,'metrics.json'),JSON.stringify(result,null,2)+'\n');
  assert.deepEqual(errors,[],'Browser console errors');
  assert(stress[0].avg<4,`300-token draw ${stress[0].avg.toFixed(3)} ms exceeds 4 ms`);
  console.log(JSON.stringify(result,null,2));
 } finally {if(browser)await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
