# Europa basemap tiles from the USGS "Europa Voyager - Galileo SSI Global Mosaic 500m" GeoTIFF.
# The GeoTIFF starts at 0° at its left edge (it is centred on 180°); this rolls it to run -180..180 east,
# fills the no-data south polar cap with the surrounding grey, and writes the same geographic tile grid the
# site uses for NASA Trek layers: level L has 2^(L+1) x 2^L JPEG tiles of 256 px, each 180/2^L degrees.
import sys, os, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, out, maxl = sys.argv[1], sys.argv[2], int(sys.argv[3])
a = np.load(src) if src.endswith('.npy') else __import__('tifffile').imread(src)
H, W = a.shape
a = np.roll(a, -(W // 2), axis=1)                 # left edge 0° → left edge 180°W
nod = a == 0
if nod.any():                                     # fill no-data with the mean of each row's valid pixels, else global mean
    g = a[~nod].mean()
    rows = np.where(nod.any(1))[0]
    for r in rows:
        v = a[r][~nod[r]]
        a[r][nod[r]] = int(v.mean()) if v.size > W * 0.2 else int(g)
img = Image.fromarray(a)
for L in range(maxl + 1):
    gw, gh = 2 ** (L + 1) * 256, 2 ** L * 256
    im = img.resize((gw, gh), Image.LANCZOS if gw < W else Image.BICUBIC)
    tot = 0
    for r in range(2 ** L):
        for c in range(2 ** (L + 1)):
            t = im.crop((c * 256, r * 256, c * 256 + 256, r * 256 + 256))
            d = f'{out}/{L}/{r}'; os.makedirs(d, exist_ok=True)
            t.save(f'{d}/{c}.jpg', quality=82, optimize=True)
            tot += os.path.getsize(f'{d}/{c}.jpg')
    print(L, tot // 1000, 'kB', flush=True)
