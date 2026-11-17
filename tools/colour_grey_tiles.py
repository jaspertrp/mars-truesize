"""Colours the grey parts of a colour tile mosaic (e.g. msl-color, where HiRISE has no colour strip) with the
mosaic's own colours: for each brightness, the average colour of that brightness in the coloured parts (the same
table as GALE_RAMP in the page). Pixels blend by how grey they are, so there are no hard seams."""
import sys, os, glob, numpy as np
from PIL import Image
from multiprocessing import Pool
RAMP = [[0, 0, 0, 1], [16, 11, 18, 23], [32, 27, 34, 39], [48, 45, 50, 52], [64, 67, 64, 62], [80, 86, 79, 74], [96, 112, 92, 81],
  [112, 133, 106, 91], [128, 163, 118, 93], [144, 182, 133, 106], [160, 201, 148, 119], [176, 214, 163, 132], [192, 228, 182, 150],
  [208, 244, 199, 163], [224, 250, 218, 190], [240, 254, 238, 216], [255, 255, 255, 255]]
SAT = 1.35   # the averages are a little duller than single pixels: push the colour back out
xs = [r[0] for r in RAMP]
LUT = np.stack([np.interp(np.arange(256), xs, [r[c + 1] for r in RAMP]) for c in range(3)], 1)
src, dst = sys.argv[1], sys.argv[2]
def work(f):
    out = os.path.join(dst, os.path.relpath(f, src))
    if os.path.exists(out): return 0
    im = Image.open(f).convert('RGBA'); a = np.asarray(im).astype(np.float32)
    rgb = a[..., :3]; sat = rgb.max(-1) - rgb.min(-1)
    w = np.clip((12 - sat) / 5, 0, 1)[..., None]
    y = np.clip(rgb @ np.array([0.299, 0.587, 0.114], np.float32), 0, 255).astype(np.uint8)
    col = LUT[y]; yy = y[..., None].astype(np.float32); col = np.clip(yy + (col - yy) * SAT, 0, 255)
    o = a.copy(); o[..., :3] = rgb * (1 - w) + col * w
    os.makedirs(os.path.dirname(out), exist_ok=True)
    changed = float(w.mean()) > 0.001
    if not changed: import shutil; shutil.copyfile(f, out); return 0
    Image.fromarray(np.clip(o, 0, 255).astype(np.uint8), 'RGBA').save(out, 'WEBP', quality=82, method=4)
    return 1
if __name__ == '__main__':
    fs = glob.glob(os.path.join(src, '*/*/*.webp'))
    with Pool(os.cpu_count()) as p: n = sum(p.imap_unordered(work, fs, chunksize=16))
    print(len(fs), 'tiles,', n, 'recoloured')
