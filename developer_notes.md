# Developer Notes

## What is it?

- The repository is useful for creating _static_ and _dynamic_ maps with pins. Each pin has a quanitity and tag associated with it. The tag also determines the color of the pin e.g. [here](https://map.chemotion.scc.kit.edu/) the tags are 'Planned usage', 'Test usage' etc and the quantity is visible by hovering over the pins.
- The repository consists primarly of a single python script called [`generate_map.py`](generate_map.py). When given a single argument `germany`, it produces a static map of Germany with instances marked on it. Otherwise it produces a static map of European countries as well as a dynamic map of the world with instances marked on it.
- The workflow is supported by data in the [`data`](data) folder.
- The workflow is automated for GitHub actions using [`map_workflow`](.github/workflows/map_workflow.yml) file.

## How it works?

- The static map is generated using the [`geopandas`](https://geopandas.org/) library and its ability to draw maps from topological (.geojson) files. These topological files are downloaded from [Eurostat](https://ec.europa.eu/eurostat/web/gisco/) and the [GitHub repository](https://github.com/nvkelso/natural-earth-vector) of [Natural Earth](https://www.naturalearthdata.com). The generated file is saved as `europe.svg` (and `germany.svg`).
- The dynamic version relies on the [Leaflet](https://leafletjs.com) JS library. We use [template.html](data/template.html) and employ Python to include markers, layers, and layer control panel on the map as well as replace variables written as `$...VARNAME...$`. This file is saved as `map.html`.
- Prerequistes:
  - Python
  - packages listed in [requirements.txt](requirements.txt)
  - font and topography files that are be downloaded using [download_prerequistes.sh](download_prerequistes.sh)

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
conda create -n mapenv python=3 pip
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
    "common_name": "Zürich",
    "id_name": "Zürich",
    "stage": "Planned",
    "num_users": 2,
    "country_code": "CH"
  },
```

where `common_name` is the name of the city/region (in language of your choice), `id_name` is the standard name of the city/region (in Europe) according to the NUTS standard or, for places outside Europe, the `name` as used by Natural Earth geojson (most likely the common English name), `stage` is the key that corresponds to `stage` variable in the script, `num_users` is the number of users in that location -- which then appears on the map -- and `country_code` is the [two letter country code as defined by ISO](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

### Changing appearence

- Colors of the pins can be changed. However they must be one of the colors accepted by `matplotlib`. Further, for the dynamic map we use [images for the pins, loaded on-the-fly by the user](https://github.com/pointhi/leaflet-color-markers/), they must be one the colors listed [here](https://github.com/pointhi/leaflet-color-markers/tree/master/img).
- We then overlay an icon on the pins. This icon can be changed by changing `overlay_icon`.
- The order of stages, as listed in the legend, can be changed by changing the order in the list `ordered_stages`.
- The title of the legend, in the dynamic version, can be changed by changing `legend_header`.
- Zooming and padding (set to sensible defaults) can be changed using these variables:
  - `static_map_patch_size`
  - `dynamic_map_start_zoom`
  - `dynamic_map_max_zoom`
  - `dynamic_map_padding`

### Things to remember

- On the static map, a (European) country appears as soon as it is included. For countries with (faraway) island territorries, the map does not show areas outside mainland for conciseness e.g. France & Spain. The code for this can be changed under the comment `# modifications to eur map, if any`. A helpful guide to NUTS codes is available [here](https://en.wikipedia.org/wiki/First-level_NUTS_of_the_European_Union).
- The exact location of a pin is set to be the centroid of the polygon that determines its borders (as defined by NUTS level 3). In rare cases this might [actually be outside the polygon](https://support.esri.com/en/technical-article/000017716). The code will have to be adapted for the same. PR is welcome, though most algorithms that fix can be slow.
