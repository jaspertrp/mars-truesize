import json
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

reg = json.load(open('dl/regions10.geojson'))['features']
sub = json.load(open('dl/subunits50.geojson'))['features']
REN = {'Australia': 'Oceania'}
NL = {'Africa':'Afrika','Antarctica':'Antarctica','Asia':'Azië','Europe':'Europa','North America':'Noord-Amerika','South America':'Zuid-Amerika','Oceania':'Oceanië'}
UNMAP = {'Europe':'Europe','Africa':'Africa','Asia':'Asia','Oceania':'Oceania','Americas':None,'Antarctica':'Antarctica'}

def parts(g):
    g = make_valid(g)
    if g.geom_type == 'Polygon': return [g]
    out = []
    for p in getattr(g, 'geoms', []):
        out += parts(p) if p.geom_type != 'Polygon' else [p]
    return out

cont = {}
for f in reg:
    p = f['properties']
    if p['FEATURECLA'] != 'Continent': continue
    name = REN.get(p['NAME_EN'], p['NAME_EN'])
    cont.setdefault(name, []).extend(parts(shape(f['geometry'])))
mainland = {k: unary_union(v) for k, v in cont.items()}

added = {k: 0 for k in mainland}
for f in sub:
    p = f['properties']
    c = p['CONTINENT']
    if c.startswith('Seven seas'):
        c = UNMAP.get(p['REGION_UN'])
        if c is None:
            c = 'North America' if (p.get('SUBREGION') or '').startswith(('Northern America','Central America','Caribbean')) else 'South America'
    if c not in mainland: continue
    for part in parts(shape(f['geometry'])):
        if part.area <= 0: continue
        # skip parts already covered by any mainland continent outline
        covered = max((part.intersection(m).area for m in mainland.values() if m.intersects(part)), default=0.0)
        if covered / part.area > 0.5: continue
        cont[c].append(part); added[c] += 1

feats = []
for name, ps in cont.items():
    u = make_valid(unary_union(ps))
    feats.append({'type': 'Feature', 'properties': {'name': name, 'name_nl': NL.get(name, name)}, 'geometry': mapping(u)})
json.dump({'type': 'FeatureCollection', 'features': feats}, open('continents_raw.geojson', 'w'))
print('islands added per continent:', added)
