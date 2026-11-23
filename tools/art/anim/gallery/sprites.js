/* Shared Canvas 2D sprite cache. No DOM dependency; also exercised under Node. */
'use strict';
const UnitSprites = {
  prepare(image, meta, sizes, makeCanvas) {
    const cache = new Map();
    for (const size of sizes) {
      const cols = image.width / meta.frame.w, rows = image.height / meta.frame.h;
      const native = size === meta.frame.w && size === meta.frame.h;
      const normal = native ? image : makeCanvas(cols * size, rows * size);
      if (!native) {
        const g = normal.getContext('2d');
        g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
        // Scale cells separately: filtering must never sample the next pose.
        for (const clip of Object.values(meta.clips)) for (let i = 0; i < clip.frames; i++) {
          g.drawImage(image, i * meta.frame.w, clip.row * meta.frame.h,
            meta.frame.w, meta.frame.h, i * size, clip.row * size, size, size);
        }
      }
      const flipped = makeCanvas(normal.width, normal.height);
      const f = flipped.getContext('2d');
      f.translate(normal.width, 0); f.scale(-1, 1); f.drawImage(normal, 0, 0);
      cache.set(size, {normal, flipped, cols, ax: meta.frame.ax * size / meta.frame.w,
        ay: meta.frame.ay * size / meta.frame.h});
    }
    return cache;
  },
  draw(g, asset, clip, frame, x, y, size, flipped) {
    const mip = asset.mips.get(size);
    if (!mip) throw Error(`Sprite size ${size} has not been prepared`);
    const sx = (flipped ? mip.cols - 1 - frame : frame) * size;
    g.drawImage(flipped ? mip.flipped : mip.normal, sx, asset.meta.clips[clip].row * size,
      size, size, Math.round(x - (flipped ? size - mip.ax : mip.ax)),
      Math.round(y - mip.ay), size, size);
  }
};
if (typeof module !== 'undefined') module.exports = UnitSprites;
