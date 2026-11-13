# True Size of Mars

An interactive map of Mars where you can drop Earth's countries at their **real size** and drag them around. It works like [thetruesize.com](https://thetruesize.com), but on Mars.

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

Country borders come from [Natural Earth](https://www.naturalearthdata.com/) via `world-atlas`.

## How the true-size projection works

For each country the page computes its spherical centroid on Earth. It then stores every vertex as a (great-circle distance, bearing) pair from that centroid. When you drop or drag the country, each vertex is placed at the same bearing from the new centre on Mars, with its distance multiplied by 6371 / 3389.5. That keeps distances from the centre and directions true. Rotating a country (Shift/Alt-drag it) simply adds an angle to every bearing. Countries can be dragged anywhere, including over the poles: d3-geo cuts each placed shape at the antimeridian and closes it over a pole when the shape covers one, so it renders correctly on both the flat map and the globe.

Built with [MapLibre GL JS](https://maplibre.org/) (globe projection), d3-geo and topojson-client.
