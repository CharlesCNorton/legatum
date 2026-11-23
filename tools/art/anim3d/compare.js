// Independent shadow DOM keeps the relief gallery's loading/disable-all path
// from stopping this comparison when another pilot atlas is unavailable.
const host = document.querySelector('relief-3d-comparison');
const shadow = host.attachShadow({ mode: 'open' });
const base = new URL('../../../app/src/assets/units/', import.meta.url);
shadow.innerHTML = `<style>
:host{display:block;margin:24px 0;font:16px/1.5 Georgia,serif;color:#2b2419}
article{border-top:1px solid #b8aa8c;padding:16px 0}.strip{display:flex;gap:12px;overflow-x:auto}figure{margin:0;flex:0 0 256px}canvas{display:block;background:#ded4bd}.small{display:flex;align-items:end;gap:12px;margin-top:8px}.small canvas{background:#b3bf85}h3{font-weight:normal;margin:8px 0}button{font:14px system-ui;background:#fbf6ea;border:1px solid #9d8c6c;padding:7px 12px;cursor:pointer;margin-right:8px}button:focus-visible{outline:3px solid #9a3322}figcaption,output,.note{font:12px/1.5 system-ui}output{margin-left:8px}
</style><p class="loading" role="status">Loading the spearman comparison…</p>`;
async function load(slug) {
  const [mr, ir] = await Promise.all([fetch(new URL(`anim/${slug}.json`, base)), fetch(new URL(`anim/${slug}.webp`, base))]);
  if (!mr.ok || !ir.ok) throw Error(`${slug} atlas is unavailable. Run its build script, then reload.`);
  const meta = await mr.json(), blob = await ir.blob();
  return { meta, image: await createImageBitmap(blob), bytes: blob.size };
}
function frameAt(meta, time) {
  if (meta.loop) return Math.floor(time * meta.fps) % meta.frames;
  return Math.min(meta.frames - 1, Math.floor((time % (meta.frames / meta.fps + .85)) * meta.fps));
}
async function init() {
  const [relief, solid, painting] = await Promise.all([load('spearman'), load('spearman-3d'), (async () => {
    const r = await fetch(new URL('spearman-256.png', base)); if (!r.ok) throw Error('Painting unavailable');
    return createImageBitmap(await r.blob());
  })()]);
  shadow.querySelector('.loading').textContent = `Spearman · relief ${(relief.bytes/1000).toFixed(1)} KB · 3D ${(solid.bytes/1000).toFixed(1)} KB. Both use decoded delivery atlases. Death replays after a hold for inspection.`;
  const views = [];
  for (const clip of ['idle', 'move', 'attack', 'hit', 'death']) {
    const article = document.createElement('article');
    article.innerHTML = `<h3>${clip[0].toUpperCase()+clip.slice(1)}</h3><button class="play">Pause pair</button><button class="step">Step pair</button><output></output><div class="strip"></div>`;
    shadow.append(article);
    const v = { clip, time: 0, playing: true, manual: null, figures: [], output: article.querySelector('output') };
    for (const label of ['Painting', 'Relief', '3D']) {
      const figure = document.createElement('figure');
      figure.innerHTML = `<figcaption>${label} · 256 px</figcaption><canvas width="256" height="256" aria-label="${label} ${clip} at 256 pixels"></canvas><div class="small"><div><canvas width="80" height="80" aria-label="${label} ${clip} at map token size"></canvas><span class="note">80 px map token</span></div><div><canvas width="64" height="64" aria-label="${label} ${clip} at 64 pixels"></canvas><span class="note">64 px silhouette</span></div></div>`;
      article.querySelector('.strip').append(figure);v.figures.push([...figure.querySelectorAll('canvas')]);
    }
    const play = article.querySelector('.play');
    play.onclick = () => { v.playing = !v.playing; v.manual = null; play.textContent = v.playing ? 'Pause pair' : 'Play pair'; };
    article.querySelector('.step').onclick = () => {
      v.manual = ((v.manual ?? frameAt(solid.meta.clips[clip], v.time)) + 1) % solid.meta.clips[clip].frames;
      v.time = v.manual / solid.meta.clips[clip].fps;v.playing = false;play.textContent = 'Play pair';draw(v);
    };
    views.push(v);
  }
  function draw(v) {
    const indices = [0, frameAt(relief.meta.clips[v.clip], v.time), v.manual ?? frameAt(solid.meta.clips[v.clip], v.time)];
    v.figures.forEach((canvases, index) => canvases.forEach(c => {
      const g = c.getContext('2d'), size = c.width;g.clearRect(0, 0, size, size);
      if (index === 0) g.drawImage(painting, 0, 0, size, size);
      else { const a = index === 1 ? relief : solid;g.drawImage(a.image, indices[index]*256, a.meta.clips[v.clip].row*256, 256, 256, 0, 0, size, size); }
    }));
    v.output.textContent = `Relief ${indices[1]+1}/${relief.meta.clips[v.clip].frames} · 3D ${indices[2]+1}/${solid.meta.clips[v.clip].frames}`;
  }
  let visible = true, previous = performance.now();
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; }).observe(host);
  function tick(now) {
    const dt = Math.min(.1, (now-previous)/1000);previous = now;
    if (visible) for (const v of views) { if (v.playing) v.time += dt;draw(v); }
    requestAnimationFrame(tick);
  }
  views.forEach(draw);requestAnimationFrame(tick);
}
init().catch(error => { shadow.querySelector('.loading').textContent = error.message; });
