# Saturn global map for the site:
#  1. NASA PDS Cassini ISS RGB global map, 11 Aug 2011 (planetocentric, 0.1°/px, west longitude 360..0), with the
#     strips hidden by the rings and the polar gaps filled from neighbouring latitudes;
#  2. a gentle contrast and sharpness boost (Saturn's bands are subtle in the original);
#  3. the north polar cap above ~76° replaced by Cassini's natural-colour polar-stereographic mosaic of June 2013
#     (PIA21611, left panel, 25 km per pixel, pole at the centre), colour-matched to the global map where they meet.
# Output: planetocentric equirectangular RGB, rows 90..-90 inclusive (1801 x 3601), longitude -180..180 east.
import sys, numpy as np
from PIL import Image, ImageFilter
A, B = 60268.0, 54364.0; Q = B / A
glob = np.load(sys.argv[1]).astype(np.float32)      # sat_filled.npy from the FITS (north up, -180..180)
polar = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32)[:, :1024]   # 2013 panel
out = sys.argv[3]
H, W, _ = glob.shape
# 1/2: contrast + saturation + unsharp
m = glob.reshape(-1, 3).mean(0)
g = (glob - m) * 1.9 + m
lum = g.mean(2, keepdims=True); g = lum + (g - lum) * 1.15
im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=1))
# work on a 4x finer grid (0.025°) so the 25 km/px polar mosaic keeps its detail
im = im.crop((0, 0, W - 1, H)).resize(((W - 1) * 4, (H - 1) * 4 + 1), Image.BICUBIC)
g = np.asarray(im).copy()
H, W = g.shape[:2]
# 3: polar cap
psi = 90 - np.arange(H) * 180 / (H - 1)                       # planetocentric latitude of each row
lon = -180 + (np.arange(W) + 0.5) * 360 / W
Rc = A * A / B                                                 # radius of curvature at the pole (km)
rows = np.where(psi > 72)[0]
P, LON = np.meshgrid(psi[rows], lon, indexing='ij')
phi = np.degrees(np.arctan(np.tan(np.radians(P)) / (Q * Q)))   # planetographic
rho = 2 * Rc * np.tan(np.radians(90 - phi) / 2) / 25.0         # pixels from the pole
px = 511.5 + rho * np.sin(np.radians(LON)); py = 511.5 - rho * np.cos(np.radians(LON))
inside = rho < 505
x0 = np.clip(np.floor(px).astype(int), 0, 1022); y0 = np.clip(np.floor(py).astype(int), 0, 1022)
fx = (px - x0)[..., None]; fy = (py - y0)[..., None]
samp = (polar[y0, x0] * (1 - fx) * (1 - fy) + polar[y0, x0 + 1] * fx * (1 - fy) +
        polar[y0 + 1, x0] * (1 - fx) * fy + polar[y0 + 1, x0 + 1] * fx * fy)
# colour match: in the blend ring (450..505 px) scale the polar image's channels to the global map's means there
ring = (rho > 430) & (rho < 505)
gr = g[rows].astype(np.float32)
gm = gr[ring].mean(0); pm = samp[ring].mean(0)
samp = samp * (gm / pm) ** 0.85                                # keep some of the real blue of the hexagon
w = np.clip((505 - rho) / 70, 0, 1)[..., None]
w = w * w * (3 - 2 * w)
g[rows] = np.clip(gr * (1 - w) + samp * w, 0, 255).astype(np.uint8)
np.save(out, g)
# the cap around the pole (above 85°) cannot be drawn by MapLibre's tiles; the site draws it from this crop of the
# same, colour-matched polar mosaic (centre = pole, 25 km per pixel, 640 x 640 px)
cap = polar[512 - 320:512 + 320, 512 - 320:512 + 320] * (gm / pm) ** 0.85
Image.fromarray(np.clip(cap, 0, 255).astype(np.uint8)).save(out.replace('.npy', '_npole.jpg'), quality=88)
Image.fromarray(g).resize((1440, 720)).save(out.replace('.npy', '_prev.jpg'))
print('done', gm, pm)
