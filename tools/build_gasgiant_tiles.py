# Jupiter basemap tiles for the site's flattened globe.
#
# Source (default): Björn Jónsson's merged Cassini + Juno map (Planetary Society, CC BY 3.0):
#   14400 x 7200 px simple cylindrical, *planetographic* latitude, pixel-centred rows, longitude shifted ~180°
#   relative to NASA's PIA07782 (we roll it so features sit where they do in PIA07782).
# Older source: NASA PIA07782 (3601 x 1801 px, planetocentric latitude, rows 90..-90 inclusive) with --pia.
# Saturn: --saturn --pia with the PDS Cassini ISS RGB global map (2011, planetocentric, rows 90..-90 inclusive),
# prepared (north up, -180..180, gaps filled) as a .npy.
#
# The site draws Jupiter as an ellipsoid (sphere squashed by Q = b/a along its axis), so a map latitude is the
# ellipsoid's reduced latitude beta. Rows are resampled from the source latitude to beta and cut into the
# site's geographic tile grid (level L: 2^(L+1) x 2^L JPEG tiles of 256 px, 180/2^L degrees each).
import sys, os, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
A, B = 71492.0, 66854.0
import sys as _s
if '--saturn' in _s.argv: A, B = 60268.0, 54364.0
Q = B / A
src, out, maxl = sys.argv[1], sys.argv[2], int(sys.argv[3])
pia = '--pia' in sys.argv
roll_px = next((int(x.split('=')[1]) for x in sys.argv if x.startswith('--roll=')), 0)
a = np.load(src, mmap_mode='r') if src.endswith('.npy') else np.asarray(Image.open(src).convert('RGB'))
H, W = a.shape[:2]
OH, OW = 2 ** maxl * 256, 2 ** (maxl + 1) * 256
beta = 90 - (np.arange(OH) + 0.5) * 180 / OH
if pia:   # planetocentric psi: tan psi = Q tan beta ; rows 90..-90 inclusive
    lat = np.degrees(np.arctan(Q * np.tan(np.radians(beta)))); fy = (90 - lat) / 180 * (H - 1)
else:     # planetographic phi: tan phi = tan beta / Q ; pixel-centred rows
    lat = np.degrees(np.arctan(np.tan(np.radians(beta)) / Q)); fy = (90 - lat) / 180 * H - 0.5
fy = np.clip(fy, 0, H - 1.001)
rows = []
for j in range(OH):                                   # row by row keeps memory low for the big source
    y0 = int(fy[j]); t = fy[j] - y0
    r = (a[y0].astype(np.float32) * (1 - t) + a[min(H - 1, y0 + 1)].astype(np.float32) * t)
    if roll_px: r = np.roll(r, roll_px, axis=0)
    rows.append(np.asarray(Image.fromarray(r.clip(0, 255).astype(np.uint8)[None]).resize((OW, 1), Image.LANCZOS))[0])
img = Image.fromarray(np.stack(rows))
for L in range(maxl, -1, -1):
    gw, gh = 2 ** (L + 1) * 256, 2 ** L * 256
    im = img if L == maxl else img.resize((gw, gh), Image.LANCZOS)
    tot = 0
    for r in range(2 ** L):
        for c in range(2 ** (L + 1)):
            d = f'{out}/{L}/{r}'; os.makedirs(d, exist_ok=True)
            im.crop((c * 256, r * 256, c * 256 + 256, r * 256 + 256)).save(f'{d}/{c}.jpg', quality=82, optimize=True)
            tot += os.path.getsize(f'{d}/{c}.jpg')
    print(L, tot // 1000, 'kB', flush=True)
