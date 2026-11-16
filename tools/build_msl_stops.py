"""Builds msl-stops.json: Curiosity's route (NASA MMGIS waypoints) and a set of stops with a short story and the
rover's own Navcam / Hazcam / ChemCam photos taken there, each with where it looked (azimuth, elevation, width).
Inputs: msl_wp.csv (sol,site,drive,lon,lat,elev,dist) and photos.json (raw-image API items, fetched per stop)."""
import json, math, re, sys, bisect
wp_csv, photos_json, stories_json, out = sys.argv[1:5]
WP = [tuple(float(x) for x in l.split(',')) for l in open(wp_csv) if l.strip()]
WP.sort(key=lambda w: (w[1], w[2]))
keys = [(w[1], w[2]) for w in WP]
def pos_at(site, drive):
    i = bisect.bisect_right(keys, (site, drive)) - 1
    return WP[max(i, 0)]
def pos_sol(sol):
    c = [w for w in WP if w[0] <= sol]
    return max(c, key=lambda w: (w[1], w[2])) if c else WP[0]
v = lambda s: [float(x) for x in re.findall(r'-?[\d.]+(?:e-?\d+)?', s or '')]
def qrot(q, a):
    w, x, y, z = q; p, b, c = a
    ix = w*p + y*c - z*b; iy = w*b + z*p - x*c; iz = w*c + x*b - y*p; iw = -x*p - y*b - z*c
    return [ix*w + iw*-x + iy*-z - iz*-y, iy*w + iw*-y + iz*-x - ix*-z, iz*w + iw*-z + ix*-y - iy*-x]
CAM = {'NAV': 'n', 'FHA': 'f', 'RHA': 'r', 'CHE': 'c'}
def geom(it):
    q, a = v(it['at']), v(it['cv'])
    if len(q) != 4 or len(a) != 3: return None
    d = qrot(q, a)
    az = math.degrees(math.atan2(d[1], d[0])) % 360
    el = -math.degrees(math.asin(max(-1, min(1, d[2]))))
    parts = [v(p) for p in (it['cm'] or '').split(';')]
    sf = v(it['sf']); hfov = None
    if len(parts) > 2 and len(parts[1]) == 3 and len(parts[2]) == 3 and len(sf) == 4:
        A, H = parts[1], parts[2]
        f = math.hypot(A[1]*H[2]-A[2]*H[1], A[2]*H[0]-A[0]*H[2], A[0]*H[1]-A[1]*H[0])
        w = sf[2] - sf[0] + 1
        if f > 20: hfov = 2 * math.degrees(math.atan(w / 2 / f))
    if hfov is None: hfov = {'n': 45, 'f': 124, 'r': 124, 'c': 1.1}[CAM[it['in'][:3]]]
    return az, el, max(0.5, min(130, hfov))
P = json.load(open(photos_json)); S = json.load(open(stories_json))
stops = []
for s in S:
    w = pos_sol(s['key'])
    items = []
    for it in P.get(s['id'], []):
        g = geom(it)
        if not g or g[1] > 50: continue          # sky / sun shots have no place on the map
        site, dr = it['site'], it['dr']
        p = pos_at(site, dr) if site is not None and dr is not None else pos_sol(it['s'])
        if math.hypot((p[3] - w[3]) * 59200, (p[4] - w[4]) * 59200) > 400: continue   # keep photos near the stop
        cam = CAM[it['in'][:3]]
        items.append(dict(cam=cam, left='LEFT' in it['in'] or cam == 'c', full=it['st'] == 'full', sol=it['s'], u=it['u'].replace('http://', 'https://'),
                          az=g[0], el=g[1], hf=g[2], lon=p[3], lat=p[4], id=it['id']))
    # one photo per pointing: left eye first, full frames first
    items.sort(key=lambda i: (not i['left'], not i['full'], i['sol']))
    seen, keep = set(), []
    for i in items:
        k = (i['cam'], round(i['az'] / (4 if i['cam'] != 'c' else 0.5)), round(i['el'] / 4), round(i['lon'], 4), round(i['lat'], 4))
        if k in seen: continue
        seen.add(k); keep.append(i)
    # spread the picks: ChemCam close-ups and Hazcams first, then Navcam around the horizon
    keep.sort(key=lambda i: ({'c': 0, 'f': 1, 'r': 2, 'n': 3}[i['cam']], i['sol'], i['az']))
    pick = [i for i in keep if i['cam'] == 'c'][:8] + [i for i in keep if i['cam'] in 'fr'][:6]
    nav = [i for i in keep if i['cam'] == 'n']
    step = max(1, len(nav) // 22); pick += nav[::step][:22]
    pick.sort(key=lambda i: (i['sol'], i['az']))
    stops.append(dict(id=s['id'], t=s['t'], sol=s['key'], date=s['date'], text=s['text'], link=s.get('link'),
                      lon=round(w[3], 6), lat=round(w[4], 6), km=round(w[6] / 1000, 2),
                      ph=[[i['cam'], i['sol'], i['u'], round(i['az'], 1), round(i['el'], 1), round(i['hf'], 2), round(i['lon'], 6), round(i['lat'], 6), i['id']] for i in pick]))
    print(s['id'], len(P.get(s['id'], [])), len(keep), len(pick), file=sys.stderr)
route = [[round(w[3], 6), round(w[4], 6), int(w[0])] for w in sorted(WP, key=lambda w: (w[0], w[1], w[2]))]
json.dump(dict(route=route, stops=stops), open(out, 'w'), separators=(',', ':'))
