# Developer Notes

## What is it?

- The repository is useful for creating _static_ and _dynamic_ maps with pins. Each pin has a quanitity and tag associated with it. The tag also determines the color of the pin e.g. [here](https://map.chemotion.scc.kit.edu/) the tags are 'Planned usage', 'Test usage' etc and the quantity is visible by hovering over the pins.
- The repository consists primarly of a single python script called [`generate_map.py`](generate_map.py).
- The workflow is supported by data in the [`data`](data) folder.
- The workflow is automated for GitHub actions using [`map_workflow`](.github/workflows/map_workflow.yml) file.

## How it works?

- The static map is generated using [`matplotlib`](https://matplotlib.org/) and its ability to draw maps from topological files. These topological files are downloaded from [Eurostat](https://ec.europa.eu/eurostat/web/gisco/). The generated file is saved as `map.svg`.
- The dynamic version relies on the [Leaflet](https://leafletjs.com) library. We use [template.html](data/template.html) and then use Python to include markers, layers, and layer control panel on the map as well as replace variables written as `$...VARNAME...$`. This file is saved as `map.html`.
- Prerequistes:
  - Python 3.8
  - packages listed in [requirements.txt](requirements.txt)
  - font and topography files that can be downloaded using [download_prerequistes.sh](download_prerequistes.sh)

### Installing Prerequistes

#### Using `venv` feature of Python

```bash
python3 -m venv .mapenv
source .mapenv/bin/activate
pip install -r requirements.txt
sh download_prerequistes.sh
```

#### Using `conda`

```bash
conda create -n mapenv python=3.8 pip
conda activate mapenv
pip install -r requirements.txt
sh download_prerequistes.sh
```

#### Using the included [`.devcontainer`](.devcontainer)

Open folder in a supporting IDE e.g. VS Code. Everything should be setup in ca. 5 min. The devcontainer is adapted from the Python devcontainer available [here](https://github.com/devcontainers/images).

## What can you adjust?

### Add / Remove entries on the Map

This can be done by adding JSON entries to the [data/plotted_locations.json](data/plotted_locations.json) file. Each entry must have the following keys:

```json
{
    "common_name" : "Aachen",
    "nuts_lvl3"   : "Städteregion Aachen",
    "stage"       : "production",
    "num_users"   : 4,
    "country_code": "DE"
},
```

where `common_name` is the name of the city/region (in language of your choice), `nuts_lvl3` is the standard name of the city/region according to the NUTS standard, `stage` is the key that corresponds to `stage` variable in the script, `num_users` is the number of users in that location -- which then appears on the map -- and `country_code` is the [two letter country code as defined by NUTS](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

### Adding / Removing connections (connection lines)

Connections are defined as a list of tuples called `connections`. You can add as many tuples to the list as you like. An empty list means no connections will be drawn on the maps.

### Changing appearence

- Colors of the pins can be changed. However they must be one of the colors accepted by `matplotlib`. Further, for the dynamic map we use [images for the pins, loaded on-the-fly by the user](https://github.com/pointhi/leaflet-color-markers/), they must be one the colors listed [here](https://github.com/pointhi/leaflet-color-markers/tree/master/img).
- We then overlay an icon on the pins. This icon can be changed by changing `overlay_icon`.
- The order of stages, as listed in the legend, can be changed by changing the order in the list `ordered_stages`.
- The title of the legend, in the dynamic version, can be changed by changing `legend_header`.
- The location of the legend, in the static version, can be changed by changing `legend_location`. Use [one supported]("https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html") by `matplotlib`.
- Zooming and padding (set to sensible defaults) can be changed using these variables:
  - `static_map_patch_size`
  - `dynamic_map_start_zoom`
  - `dynamic_map_max_zoom`
  - `dynamic_map_padding`

### Things to remember

- On the static map, a (European) country appears as soon as it is included. For France, the map does not show areas outside mainland (i.e. island regions) for conciseness. The code for this can be changed under the comment `# modifications to map, if any`. Similar modifications can be made to other regions on the map using similar code. This might be useful when plotting other countries with far-away islands e.g. Spain & Portugal. A helpful guide to NUTS codes is available [here](https://en.wikipedia.org/wiki/First-level_NUTS_of_the_European_Union).
- The exact location of a pin is set to be the centroid of the polygon that determines its borders (as defined by NUTS level 3). In rare cases this might [actually be outside the polygon](https://support.esri.com/en/technical-article/000017716). The code will have to be adapted for the same. PR is welcome, though most algorithms that fix can be slow.
