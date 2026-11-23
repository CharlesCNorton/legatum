/* CPU contract checks: no browser, canvas rasterizer or node_modules needed. */
const assert = require('node:assert/strict');
const sprites = require('./gallery/sprites.js');
const meta = {frame:{w:256,h:256,ax:127,ay:221},clips:{idle:{row:0,frames:8},death:{row:4,frames:6}}};
const canvases=[];
function canvas(width,height) {
  const calls=[];
  const g={drawImage(...args){calls.push(['drawImage',...args]);},translate(...args){calls.push(['translate',...args]);},scale(...args){calls.push(['scale',...args]);},clearRect(...args){calls.push(['clearRect',...args]);},getImageData(...args){calls.push(['getImageData',...args]);}};
  const c={width,height,calls,getContext(){return g;}};canvases.push(c);return c;
}
const image={width:2560,height:1280};
const asset={meta,mips:sprites.prepare(image,meta,[64,80,256],canvas)};
assert.equal(canvases.length,5);
for(const size of [64,80,256]) {
  const mip=asset.mips.get(size);
  assert.equal(mip.normal.width,10*size);assert.equal(mip.normal.height,5*size);
  if(size===256)assert.equal(mip.normal,image,'Reuse native atlas');
  else assert.equal(mip.normal.calls.length,14,'Every populated cell is scaled once');
  assert.deepEqual(mip.flipped.calls.map(c=>c[0]),['translate','scale','drawImage']);
  for(const flipped of [false,true]) {
    const draws=[];const g={drawImage(...args){draws.push(args);}};
    sprites.draw(g,asset,'death',5,101,120,size,flipped);
    assert.equal(draws.length,1,'Hot path must be one draw with no transforms');
    const [source,sx,sy,sw,sh,dx,dy,dw,dh]=draws[0];
    assert.equal(source,flipped?mip.flipped:mip.normal);
    assert.equal(sx,(flipped?4:5)*size);assert.equal(sy,4*size);
    assert.deepEqual([sw,sh,dw,dh],[size,size,size,size],'1:1 physical pixel blit');
    const expectedX=flipped?101-(256-127)*size/256:101-127*size/256;
    assert(Math.abs(dx-expectedX)<=.5);assert(Math.abs(dy-(120-221*size/256))<=.5);
  }
}
assert.throws(()=>sprites.draw({},asset,'idle',0,0,0,72,false),/not been prepared/);
(async()=>{
  const decoded=[];
  await sprites.decodeAndWarm(asset,canvas,async source=>{
    decoded.push(source);
    return {width:source.width,height:source.height,decoded:true};
  });
  assert.equal(decoded.length,5,'Both facings at map sizes and the native mirror are decoded');
  assert.equal(canvases.at(-1).calls.filter(c=>c[0]==='getImageData').length,14*3*2,
    'Every populated frame and facing is rasterized before timing');
  assert(canvases.at(-1).calls.filter(c=>c[0]==='getImageData').every(c=>c[3]===1&&c[4]===1));
  assert.equal(asset.mips.get(256).normal,image,'Native atlas is already decoded');
  assert(asset.mips.get(64).normal.decoded && asset.mips.get(64).flipped.decoded);
  console.log('Sprite cache PASS: cells, facings, anchors, 1:1 draw and first-use warmup');
})().catch(e=>{console.error(e);process.exitCode=1;});
