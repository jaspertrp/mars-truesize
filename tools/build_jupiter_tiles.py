# Jupiter basemap tiles from Cassini's PIA07782 cylindrical map (Dec 2000; 3601 x 1801 px, planetocentric
# latitude, longitude -180..180 east from left to right).
# The site draws Jupiter as a flattened globe: a sphere squashed along its axis, so a map latitude is the
# *reduced* latitude beta of the ellipsoid. Rows are resampled from planetocentric psi to beta
# (tan psi = (b/a) tan beta) and cut into the site's geographic tile grid (level L: 2^(L+1) x 2^L JPEG
# tiles of 256 px, 180/2^L degrees each).
import sys, os, numpy as np
from PIL import Image
A, B = 71492.0, 66854.0
src, out, maxl = sys.argv[1], sys.argv[2], int(sys.argv[3])
a = np.load(src) if src.endswith('.npy') else np.asarray(Image.open(src).convert('RGB'))
H, W = a.shape[:2]
OH = 1800
beta = 90 - (np.arange(OH) + 0.5) * 180 / OH                      # output row centres
psi = np.degrees(np.arctan((B / A) * np.tan(np.radians(beta))))
fy = (90 - psi) / 180 * (H - 1)                                   # source rows run 90..-90 inclusive
y0 = np.clip(np.floor(fy).astype(int), 0, H - 2); t = (fy - y0)[:, None, None]
warped = (a[y0] * (1 - t) + a[y0 + 1] * t).astype(np.uint8)
img = Image.fromarray(warped)
for L in range(maxl + 1):
    gw, gh = 2 ** (L + 1) * 256, 2 ** L * 256
    im = img.resize((gw, gh), Image.LANCZOS)
    tot = 0
    for r in range(2 ** L):
        for c in range(2 ** (L + 1)):
            d = f'{out}/{L}/{r}'; os.makedirs(d, exist_ok=True)
            im.crop((c * 256, r * 256, c * 256 + 256, r * 256 + 256)).save(f'{d}/{c}.jpg', quality=85, optimize=True)
            tot += os.path.getsize(f'{d}/{c}.jpg')
    print(L, tot // 1000, 'kB', flush=True)
