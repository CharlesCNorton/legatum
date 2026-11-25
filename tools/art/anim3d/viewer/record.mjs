#!/usr/bin/env node
/** Host-only Chromium capture. Starts a local server, writes exact 30 fps PNGs,
 * then encodes each clip repeated three times as H.264 yuv420p. */
import {createServer} from 'node:http';
import {readFile, mkdir, writeFile, realpath} from 'node:fs/promises';
import {resolve, dirname, extname, sep, join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {homedir} from 'node:os';

const here=dirname(fileURLToPath(import.meta.url));
const root=resolve(here,'../../../..');
const args=process.argv.slice(2);
function option(name,fallback){const i=args.indexOf(name);return i<0?fallback:args[i+1];}
const out=resolve(option('--out',join(homedir(),'LegatumRuns/anim-pilot/review/3d-v2')));
let playwright;
if(process.env.PLAYWRIGHT_MODULE) playwright=await import(pathToFileURL(resolve(process.env.PLAYWRIGHT_MODULE)).href);
else {
  const require=createRequire(import.meta.url);
  try{playwright=require('playwright');}
  catch {playwright=createRequire(join(root,'app/package.json'))('playwright');}
}
const chromium=playwright.chromium||playwright.default?.chromium;
if(!chromium)throw new Error('Playwright chromium export missing');
const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.glb':'model/gltf-binary','.png':'image/png'};
const server=createServer(async(req,res)=>{
  try{
    const path=await realpath(resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname)));
    if(!path.startsWith(root+sep)) {res.writeHead(403);res.end();return;}
    const body=await readFile(path);res.writeHead(200,{'Content-Type':mime[extname(path)]||'application/octet-stream'});res.end(body);
  }catch {res.writeHead(404);res.end('Not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try {
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:640,height:640},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/tools/art/anim3d/viewer/index.html?record=1`);
  await page.waitForFunction(()=>window.review?.ready||window.review?.error,{},{timeout:60000});
  const state=await page.evaluate(()=>window.review);
  if(!state.ready)throw new Error(state.error);
  await mkdir(out,{recursive:true});const receipts={};
  for(const [clip,duration] of Object.entries(state.clips)) {
    const frames=resolve(out,'.spearman-0ad-r3-viewer-frames',clip);await mkdir(frames,{recursive:true});
    const count=Math.round(duration*30);
    for(let i=0;i<count;i++) {
      await page.evaluate(({clip,t})=>window.review.sample(clip,t),{clip,t:i/30});
      await page.locator('canvas').screenshot({path:join(frames,`${String(i).padStart(4,'0')}.png`)});
    }
    const output=join(out,`spearman-0ad-r3-${clip}-viewer.mp4`);
    const encode=spawnSync('ffmpeg',['-y','-loglevel','error','-framerate','30','-stream_loop','2','-i',join(frames,'%04d.png'),'-frames:v',String(count*3),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',output],{stdio:'inherit'});
    if(encode.status!==0)throw new Error(`ffmpeg failed for ${clip}`);
    const probe=spawnSync('ffprobe',['-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,pix_fmt,nb_read_frames,r_frame_rate','-of','json',output],{encoding:'utf8'});
    if(probe.status!==0)throw new Error(`ffprobe failed for ${clip}`);
    const stream=JSON.parse(probe.stdout).streams[0];
    if(Number(stream.nb_read_frames)!==count*3||stream.pix_fmt!=='yuv420p')throw new Error(`Invalid encoded clip ${clip}`);
    receipts[clip]={output,...stream};console.log(output);
  }
  if(errors.length)throw new Error(errors.join('\n'));
  await writeFile(join(out,'spearman-0ad-r3-viewer-validation.json'),JSON.stringify(receipts,null,2));
} finally {
  if(browser)await browser.close();await new Promise(r=>server.close(r));
}
