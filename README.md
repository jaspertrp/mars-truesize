# True Size of Mars

An interactive map of Mars where you can drop Earth's countries, provinces and continents at their **real size** and drag them around. It works like [thetruesize.com](https://thetruesize.com), but on Mars.

Each country is redrawn at its true dimensions in kilometres. Mars has about half Earth's radius (3,389.5 km vs 6,371 km), so a country covers about 1.9× more of the planet than it does on an Earth map. Switch between a flat Web Mercator map, which stretches shapes towards the poles, and a 3D globe, which doesn't.

**Live map:** https://jaspertrp.github.io/mars-truesize/

## Basemaps

| Basemap | Resolution | Source |
|---|---|---|
| Colour (Viking MDIM 2.1) | 232 m | NASA/JPL/USGS |
| Relief (MOLA/HRSC blended colour shaded relief) | 200 m | NASA/JPL/GSFC/ESA/DLR/FU Berlin/USGS |
| Infrared (THEMIS day IR, ±65°) | 100 m | NASA/JPL/ASU/USGS |
| Detail (Global CTX mosaic) | 5 m | NASA/JPL/MSSS/Caltech Murray Lab/Esri |
| HiRISE overlay (fades in from zoom 11 where images exist, mostly landing sites) | ~25 cm | NASA/JPL/University of Arizona/USGS/Esri |
| Classic (8k texture, bundled in `tiles/`) | ~2.6 km | [Solar System Scope](https://www.solarsystemscope.com/textures/), CC BY 4.0 |

The first four are streamed from [NASA Mars Trek](https://trek.nasa.gov/mars/) and Esri's OnMars service. Both serve tiles in a geographic (equirectangular) grid, and the page reprojects them to Web Mercator in the browser through a custom MapLibre protocol (`eq://`). If a tile server can't be reached, the map falls back to the bundled Classic tiles.

## 3D terrain

- **3D terrain** uses Esri's OnMars `MDEM200M` elevation service (MOLA/HRSC blended DEM, 200 m; NASA/ESA/DLR/FU Berlin/GSFC/USGS). Its LERC-compressed float tiles are decoded in the browser with [lerc](https://github.com/Esri/lerc) and resampled into Web Mercator terrarium tiles for MapLibre terrain (`dem://` protocol). Heights are measured from the floor of Hellas. Service levels above 6 are skipped because level 7 is wrong in places.
- **Height ×** sets the vertical exaggeration; 1× is true scale. MapLibre draws an Earth-sized planet, so heights are additionally multiplied by 6378.137 / 3389.5 to keep Mars proportions.

Country borders come from [Natural Earth](https://www.naturalearthdata.com/) via `world-atlas`. Provinces and states (4,596 first-level divisions) come from Natural Earth's 1:10m admin-1 layer, simplified with mapshaper to `provinces.json`, which loads only when you start searching. Continents are built by `tools/build_continents.py`: Natural Earth's continent outlines (Europe/Asia split at the Urals) plus the islands each country part belongs to (so Great Britain is in Europe and French Guiana in South America), with Australia, New Zealand, New Guinea and the Pacific islands as Oceania.

## How the true-size projection works

For each country the page computes its spherical centroid on Earth. It then stores every vertex as a (great-circle distance, bearing) pair from that centroid. When you drop or drag the country, each vertex is placed at the same bearing from the new centre on Mars, with its distance multiplied by 6371 / 3389.5. That keeps distances from the centre and directions true. Rotating a country (Shift/Alt-drag it) simply adds an angle to every bearing. Countries can be dragged anywhere, including over the poles: d3-geo cuts each placed shape at the antimeridian and closes it over a pole when the shape covers one, so it renders correctly on both the flat map and the globe.

Built with [MapLibre GL JS](https://maplibre.org/) (globe projection), d3-geo and topojson-client.

## The Moon

Switch between Mars and the Moon at the top of the panel (or open `?body=moon`). Each world keeps its own
countries and settings. Moon imagery comes from NASA Moon Trek (LRO WAC, LOLA relief, Kaguya TC). The Moon's
3D heights are the tiles in `moon-dem/`, made with `tools/build_moon_dem.py` from NASA's LRO LOLA 64 px/degree
DEM (heights in half-metres + 20000, stored as R/G bytes in lossless WebP).

**Drive the moon buggy:** on the Moon, the *Drive the moon buggy* button puts an Apollo Lunar Roving Vehicle on the
3D terrain (a three.js model in a MapLibre custom layer, loaded only when you start driving). Arrow keys or WASD
to drive, Shift to boost, Space to hop, C to change camera, Esc to stop. It drives in Moon gravity (1.62 m/s²),
kicks up dust on airless parabolas and leaves tyre tracks. *Size* draws it 1×, 10× or 40× real size, with speed and
gravity scaled to match. The ground is the LOLA DEM (~470 m per pixel), so the terrain is gently rolling: small craters
are in the photo but not in the heights.

## Europa

`?body=europa` (or the Europa button). Jupiter's moon has no public tile server, so `europa-tiles/` holds our own
tiles, cut with `tools/build_europa_tiles.py` from the USGS *Europa Voyager–Galileo SSI Global Mosaic 500 m*
(public domain; NASA/JPL/USGS). Detail varies a lot across the moon. There is no global height map of Europa,
so it has no 3D terrain; instead of landing sites it has a list of features to fly to.

## Jupiter (flattened globe)

`?body=jupiter`. The map is Björn Jónsson's merged Cassini (Dec 2000) + Juno (poles) global map, 40 px per
degree, published by The Planetary Society under CC BY 3.0 (credit: NASA/JPL-Caltech/SSI/SwRI/MSSS/ASI/INAF/
JIRAM/Björn Jónsson). It is resampled and cut into `jupiter-tiles/` by `tools/build_jupiter_tiles.py`.

Jupiter is visibly flattened (polar radius 66,854 km, equatorial 71,492 km), so the site draws it as an
ellipsoid: `installEllipsoid()` squashes MapLibre's globe matrix along the polar axis and recomputes the
camera, horizon plane and frustum to match, so drawing, clicking, dragging and markers stay consistent.
Map latitudes on Jupiter are the ellipsoid's reduced latitude; labels and the coordinate read-out use
planetographic latitude. Countries are placed with true geodesics on the ellipsoid (GeographicLib), and
the measure tool measures along them. "Earth (whole planet, as a disc)" can be added there for scale.
