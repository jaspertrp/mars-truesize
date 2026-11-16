# Gale crater 3D terrain tiles from the USGS "Mars MSL Gale Merged DEM 1m" (Parker & Calef; HiRISE/CTX/HRSC stereo
# DEMs tied to MOLA). Input: a crop of that DEM at its native 1 m (equirectangular, Mars 2000 sphere R = 3396190 m) as
# int16 decimetres + 5000 m (0 = no data), with its top-left pixel (col0, row0) in the full mosaic.
# Output: Web Mercator tiles of 512 px, zoom 10-15 (~1.3 m per pixel at 15), as .dem files: height h (metres) is
# stored as v = round((h + 5000) * 10), v = 0 meaning no data (the site then uses its global 200 m DEM there);
# the 512 x 512 values are delta-coded (each from its left neighbour; a row's first from the row above) as little-endian
# int16 and gzipped. (An image format was tried first, but browsers' colour management altered the values.)   Usage: build_gale_dem.py crop.int16 W H col0 row0 outdir [zmin zmax]
# Tiles that already exist are skipped; tiles are built in parallel.
import sys, os, math, numpy as np
from multiprocessing import Pool
from PIL import Image
src, W, H, col0, row0, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
R, OX, OY = 3396190.0, 8127993.992786024, -244781.575189438
a = np.memmap(src, dtype='<i2', mode='r', shape=(H, W))
lon_w = (OX + col0) / R * 180 / math.pi
lat_n = (OY - row0) / R * 180 / math.pi
dpp = 1 / R * 180 / math.pi                       # degrees per 1 m pixel
lon_e, lat_s = lon_w + W * dpp, lat_n - H * dpp
def tx(lon, z): return int((lon + 180) / 360 * 2 ** z)
def ty(lat, z): r = math.radians(lat); return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
TS = 512
ZMIN, ZMAX = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) > 8 else (10, 15)
def build(job):
            z, x, y = job; n = 2 ** z
            if os.path.exists(f'{out}/{z}/{x}/{y}.dem'): return 1
            lon = (x + (np.arange(TS) + 0.5) / TS) / n * 360 - 180
            yy = y + (np.arange(TS) + 0.5) / TS
            lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * yy / n))))
            cx = (lon - lon_w) / dpp - 0.5; cy = (lat_n - lat) / dpp - 0.5
            ok_x = (cx >= 0) & (cx <= W - 1); ok_y = (cy >= 0) & (cy <= H - 1)
            if not ok_x.any() or not ok_y.any(): return 0
            # area-average when a tile pixel covers several metres (low zooms), bilinear otherwise
            step = max(1, int(abs(cx[1] - cx[0])))
            xi = np.clip(cx, 0, W - 1.001); yi = np.clip(cy, 0, H - 1.001)
            if step > 1:
                s = step
                x0 = np.clip((xi - s / 2).astype(int), 0, W - s); y0 = np.clip((yi - s / 2).astype(int), 0, H - s)
                sub = np.zeros((TS, TS), np.float64); cntv = np.zeros((TS, TS), np.float64)
                for dy in range(0, s, max(1, s // 4)):
                    rows = a[y0 + dy][:, None]
                    for dx in range(0, s, max(1, s // 4)):
                        v = a[(y0 + dy)[:, None], (x0 + dx)[None, :]].astype(np.float64)
                        m = v > 0; sub += np.where(m, v, 0); cntv += m
                val = np.where(cntv > 0, sub / np.maximum(cntv, 1), 0)
            else:
                x0 = xi.astype(int); y0 = yi.astype(int); fx = (xi - x0)[None, :]; fy = (yi - y0)[:, None]
                p00 = a[y0[:, None], x0[None, :]].astype(np.float64); p01 = a[y0[:, None], x0[None, :] + 1]
                p10 = a[y0[:, None] + 1, x0[None, :]]; p11 = a[y0[:, None] + 1, x0[None, :] + 1]
                val = (p00 * (1 - fx) + p01 * fx) * (1 - fy) + (p10 * (1 - fx) + p11 * fx) * fy
                bad = (p00 == 0) | (p01 == 0) | (p10 == 0) | (p11 == 0)
                val = np.where(bad, 0, val)
            val = np.where(ok_y[:, None] & ok_x[None, :], val, 0)
            if not (val > 0).any(): return 0
            v = np.clip(np.round(val), 0, 65535).astype(np.uint16)
            vi = v.astype(np.int32); dd = np.empty_like(vi)
            dd[:, 1:] = vi[:, 1:] - vi[:, :-1]; dd[1:, 0] = vi[1:, 0] - vi[:-1, 0]; dd[0, 0] = vi[0, 0]
            d = f'{out}/{z}/{x}'; os.makedirs(d, exist_ok=True)
            open(f'{d}/{y}.dem', 'wb').write(__import__('gzip').compress(dd.astype('<i2').tobytes(), 9))
            return 1
if __name__ == '__main__':
    for z in range(ZMIN, ZMAX + 1):
        jobs = [(z, x, y) for x in range(tx(lon_w, z), tx(lon_e, z) + 1) for y in range(ty(lat_n, z), ty(lat_s, z) + 1)]
        with Pool(os.cpu_count()) as p: cnt = sum(p.map(build, jobs, chunksize=4))
        print(z, cnt, flush=True)
print('bounds', lon_w, lat_s, lon_e, lat_n)
