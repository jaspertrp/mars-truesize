# Moon DEM pyramid in a geographic grid (same layout as Esri's Mars DEM: level L has 2^(L+1) x 2^L tiles of
# 180/2^L degrees, edge pixels sit on tile edges). Value per pixel: LOLA height in half-metres + 20000
# (= ldem_64_uint value), stored as R = high byte, G = low byte in a lossless WebP.
import sys, os, numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image
src, out, maxl, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), 256
a = np.load(src).astype(np.float32)          # 11520 x 23040, 64 ppd, col 0 at -180, row 0 at +90
PPD = 64
for L in range(maxl + 1):
    span = 180 / 2 ** L; ppd = (W - 1) / span; sig = max(0, PPD / ppd / 2)
    g = gaussian_filter(a, sig, mode=('nearest', 'wrap')) if sig > 0.5 else a
    tot = 0
    for r in range(2 ** L):
        for c in range(2 ** (L + 1)):
            j = np.arange(W); lat = 90 - (r + j / (W - 1)) * span; lon = -180 + (c + j / (W - 1)) * span
            yy = (90 - lat) * PPD - 0.5; xx = (lon + 180) * PPD - 0.5
            Y, X = np.meshgrid(yy, xx, indexing='ij')
            Y = np.clip(Y, 0, a.shape[0] - 1); X = np.mod(X, a.shape[1])
            v = map_coordinates(g, [Y, X], order=1, mode='grid-wrap')
            v = np.clip(np.round(v), 0, 65535).astype(np.uint16)
            rgb = np.zeros((W, W, 3), np.uint8); rgb[..., 0] = v >> 8; rgb[..., 1] = v & 255
            d = f'{out}/{L}/{r}'; os.makedirs(d, exist_ok=True)
            Image.fromarray(rgb).save(f'{d}/{c}.webp', lossless=True, method=6)
            tot += os.path.getsize(f'{d}/{c}.webp')
    print(L, 2 ** L * 2 ** (L + 1), 'tiles', round(tot / 1e6, 1), 'MB', flush=True)
