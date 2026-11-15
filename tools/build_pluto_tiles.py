# THE PLANET Pluto basemap tiles from the USGS "Pluto New Horizons LORRI MVIC Global Mosaic 300m" GeoTIFF.
# The mosaic starts at 0° at its left edge (centred on 180° east); this rolls it to run -180..180 east. South of about
# 35°S Pluto was in polar night during the 2015 flyby and was never seen: that no-data area is filled with a dark grey
# (with a soft edge), not invented terrain. Tiles use the site's geographic grid: level L has 2^(L+1) x 2^L JPEG tiles
# of 256 px, each 180/2^L degrees.  Usage: build_pluto_tiles.py mosaic.tif|.npy outdir maxlevel
import sys, os, numpy as np
from PIL import Image, ImageFilter
Image.MAX_IMAGE_PIXELS = None
src, out, maxl = sys.argv[1], sys.argv[2], int(sys.argv[3])
a = np.load(src) if src.endswith('.npy') else __import__('tifffile').imread(src)
H, W = a.shape
a = np.roll(a, -(W // 2), axis=1)
img = Image.fromarray(a)
FILL = 26
for L in range(maxl + 1):
    gw, gh = 2 ** (L + 1) * 256, 2 ** L * 256
    im = np.asarray(img.resize((gw, gh), Image.LANCZOS if gw < W else Image.BICUBIC)).astype(np.float32)
    nod = np.asarray(img.resize((gw, gh), Image.NEAREST)) == 0
    # soft edge: blend towards the fill colour over a few pixels around the no-data boundary
    m = Image.fromarray((nod * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(1, gw / 4096)))
    m = np.asarray(m).astype(np.float32) / 255
    m = np.maximum(m, nod)
    im = im * (1 - m) + FILL * m
    im = Image.fromarray(im.clip(0, 255).astype(np.uint8))
    tot = 0
    for r in range(2 ** L):
        for c in range(2 ** (L + 1)):
            t = im.crop((c * 256, r * 256, c * 256 + 256, r * 256 + 256))
            d = f'{out}/{L}/{r}'; os.makedirs(d, exist_ok=True)
            t.save(f'{d}/{c}.jpg', quality=82, optimize=True)
            tot += os.path.getsize(f'{d}/{c}.jpg')
    print(L, tot // 1000, 'kB', flush=True)
