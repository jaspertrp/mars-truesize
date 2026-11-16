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

CTX, THEMIS and HiRISE are black-and-white cameras. They show in their original grey; type **red** in the *Add a country…* box and their tiles take their colour from the same spot in the Viking colour mosaic and keep their own detail as brightness (a ratio pan-sharpen, with the tile's brightness matched to Viking); where Viking can't be reached, a Mars colour ramp is used. Type **grey** to switch back.

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

**Drive a buggy:** on the Moon and on Mars, typing **drive** in the *Add a country…* box puts an Apollo Lunar Roving Vehicle on the 3D
terrain (a three.js model in a MapLibre custom layer, loaded only when you start driving). It starts where you are
looking, or at Apollo 15 (Moon) / Jezero Crater (Mars) when zoomed out. Arrow keys or WASD to drive, Shift to boost,
1–4 for top speed (1×, 4×, 15×, 50× the real LRV's 13 km/h), Space to hop, C to change camera, Esc to stop. It drives
in the world's own gravity (Moon 1.62 m/s², Mars 3.72 m/s²), kicks up dust and leaves tyre tracks, drawn as
real-size strips on the ground so they keep their width at every zoom. *Size* draws it 1×, 10× or 40× real size.
The Moon's ground is the LOLA DEM (~470 m per pixel), so small craters are in the photo but not in the heights.

**Fly a fighter jet:** typing **fly** in the *Add a country…* box (Moon and Mars) puts a generic twin-tail fighter, at true size, 1.2 km above
where you are looking, or over the Montes Apenninus / Valles Marineris when zoomed out. Arrow keys pitch and roll
(like a flight stick; the HUD button or I swaps up and down), A/D rudder, W/S throttle, Shift afterburner, 1–3 speed
class (1×, 5×, 25×: up to about 68,000 km/h), C for chase, far chase and cockpit views, Esc to land. Banking turns the
jet, the world's gravity costs speed in a climb, and touching the ground is a crash (a new jet appears after a moment).
MapLibre 5 throws when asked for ground heights at zoom 18 or more with terrain on, so both cameras stay below that.

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

## Saturn (flattened globe with rings)

`?body=saturn`. Planet map: Cassini ISS colour global map of 11 Aug 2011 (NASA PDS Atmospheres Node, *Cassini ISS
Global Maps of Jupiter and Saturn*, Li et al., doi:10.17189/rkkb-6y30), contrast-enhanced; the strips hidden by the
rings' shadow are filled in from neighbouring latitudes. The north polar cap with the hexagon comes from Cassini's
natural-colour polar-stereographic mosaic of June 2013 (PIA21611, NASA/JPL-Caltech/SSI/Hampton University),
colour-matched where it meets the global map (`tools/build_saturn_map.py`). Tiles in `saturn-tiles/` (made with
`tools/build_gasgiant_tiles.py --saturn --pia`). Because MapLibre's tiles stop at 85° latitude, the cap above 84° is
drawn by a small WebGL layer straight from `saturn-npole.jpg`, so the polar vortex in the hexagon's centre shows. Saturn is flattened even more than Jupiter (polar 54,364 km, equatorial
60,268 km) and uses the same squashed-globe code.

The rings are a WebGL custom layer in the globe's own coordinates. Their density is a real measurement: the normal
optical depth from Cassini radio occultation Rev 7 (CORSS_8001, PDS Ring-Moon Systems Node), averaged to 100 km, so
the C ring, B ring, Cassini Division, A ring and Encke Gap are where they really are; opacity is 1 − exp(−τ/μ), so
they close up when seen edge-on. Colours per ring are approximate; the narrow F ring is added by hand. The far side
is hidden behind the planet by a ray test against the (squashed) planet in the fragment shader.

## THE PLANET Pluto

`?body=pluto`. Basemap: the USGS *Pluto New Horizons LORRI–MVIC Global Mosaic 300 m* (NASA/JHUAPL/SwRI/LPI, from the July
2015 flyby), cut into `pluto-tiles/` by `tools/build_pluto_tiles.py`. South of about 35°S Pluto was in polar night during
the flyby and was never seen; that part is left dark grey. Pluto's whole surface (17.6 million km²) is about the size of
Russia. No 3D terrain: the New Horizons height map only covers one side.

## Rover tracks (Mars)

`rover-tracks.geojson`: every drive of Perseverance and Curiosity and every flight of the Ingenuity helicopter, from the
GeoJSON behind NASA's "Where is the rover?" maps (MMGIS: `M20_traverse.json`, `MSL_traverse.json`,
`m20_heli_flight_path.json` on mars.nasa.gov), with heights dropped and coordinates rounded to 6 decimals.

## Gale crater in colour (Mars)

`msl-color/`: the HiRISE colour (LRGB) mosaic of Gale crater around Curiosity's route, from NASA's "Where is Curiosity?"
map (MMGIS layer `MSL_Gale_HiRISE-LRGB_78quads`, NASA/JPL-Caltech/University of Arizona). NASA's tile server does not
allow other websites to load its tiles, so zoom levels 10–17 (about 0.65 m per pixel) are mirrored here as WebP,
in the usual XYZ web-mercator layout. Shown with the "HiRISE detail" switch.

## Jezero crater in colour (Mars)

`m20-color/`: the HiRISE colour + CTX mosaic of Jezero crater from NASA's "Where is Perseverance?" map (MMGIS layer
`M20_HiRISE_RGB_CTX_mosaic_25cm_v7_Merge_LERC_clip`, NASA/JPL-Caltech/University of Arizona/MSSS), mirrored as WebP:
zoom 10–16 over the whole mosaic, plus zoom 17–18 (about 0.3 m per pixel) in a corridor of a few hundred metres around
Perseverance's and Ingenuity's paths.

## Gale crater in 3D (Mars)

`gale-dem/`: 3D terrain around Curiosity's route from the USGS *Mars MSL Gale Merged DEM 1m* (Parker & Calef;
HiRISE, CTX and HRSC stereo DEMs tied to MOLA). The 1 m DEM was read for the area of the colour mosaic (about
9 × 19 km) and cut into 512-px Web Mercator tiles, zoom 10–15 (~1.3 m per pixel), by `tools/build_gale_dem.py`:
`.dem` files: gzipped little-endian int16, delta-coded (each value from its left neighbour, a row's first from the row above), height = value / 10 − 5000 m, 0 = no data. (Not an image format: browsers' colour management altered the values and made spikes.) Inside that area these heights replace the
200 m global DEM, blended over the last 300 m.

## Drive Curiosity (Mars)

Type `rover` in the "Add a country…" box to drive NASA's Curiosity rover from Bradbury Landing along its real route
through Gale crater (on the 1 m 3D terrain). Its speed goes from the real 4 cm/s up to 1500×, and it can turn on the
spot. Sixteen numbered stops mark the big findings, from the first streambed pebbles to the sulfur crystals, the
boxwork and where the rover is today. Drive up to a stop (or press N to jump there) and a card tells the story,
with the photos Curiosity took there. Each photo has a view cone on the map showing where it looked: the Navcam,
Hazcam and ChemCam images in NASA's raw-image archive carry the camera's pointing and the rover's attitude, so the
direction, tilt and width are the real ones.

`msl-stops.json` is built by `tools/build_msl_stops.py` from NASA's MMGIS waypoints for Curiosity (sol, site,
drive, position) and the raw-image API (photos with camera vectors, attitude quaternions and CAHV camera models).
