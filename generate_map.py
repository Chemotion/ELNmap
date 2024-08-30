from pathlib import Path
from matplotlib.colors import rgb2hex
from matplotlib.patches import Circle
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import sys

# no need to change unless changes in apprearance are required. Please know what you are doing.
# static map only for Germany, not other european countries
only_germany = len(sys.argv) > 1 and sys.argv[1] == "germany"
no_germany = len(sys.argv) > 1 and sys.argv[1] == "nogermany"
color = {"Production": "green",  # color codes for different types of instances
         "Mixed": "blue",  # color supported in dynamic map are listed here https://github.com/pointhi/leaflet-color-markers
         "Test": "orange",
         "Interested": "grey"}
ordered_stages = ["Interested", "Test", "Production", "Mixed"]
static_map_patch_size = 300
static_number_fontsize = 12
dynamic_map_start_zoom = 6
dynamic_map_max_zoom = 9
dynamic_map_padding = 0.3  # works in tandem with the start zoom setting
overlay_icon = "https://raw.githubusercontent.com/harivyasi/ELNmap/main/data/favicon.ico"
legend_header = "<a href='https://chemotion.net/'>Chemotion</a>"
if only_germany:
    legend_location = (0.7, 0.4)
    color_based_on = "NUTS_NAME"
    map_filename = "germany.svg"
elif no_germany:
    legend_location = (0.8, 0.4)
    color_based_on = "CNTR_CODE"
    map_filename = "restofeur.svg"
else:
    legend_location = (0.8, 0.4)
    color_based_on = "CNTR_CODE"
    map_filename = "europe.svg"

# access font and JSON data
data_dir = Path("data")
font_file = data_dir / "OpenSans-Bold.ttf"
# NUTS level 1 is 'states' or 'group of states' or something similar
# NUTS level 3 is (usually) city-level boundary
geojsons = {"eur_country":  data_dir / "NUTS_RG_01M_2021_4326_LEVL_1.geojson",
            "eur_location": data_dir / "NUTS_RG_01M_2021_4326_LEVL_3.geojson",
            "int_location": data_dir / "ne_10m_populated_places_simple.geojson"}

# read all locations to be plotted
locations = pd.read_json(data_dir / "plotted_locations.json")
locations['longitude'] = [0.0]*len(locations)
locations['latitude'] = [0.0]*len(locations)

# prepare europe map
# read country boundaries, specify the format, limit to countries that are included
eur_country = gpd.read_file(geojsons["eur_country"])
if only_germany:
    eur_country_list = ["DE"]
    eur_country = eur_country[eur_country.CNTR_CODE.isin(eur_country_list)]
else:
    eur_country_list = locations["country_code"].unique().tolist()
    try:
        # limit geographical boundary for conciseness
        eur_country_list.remove("TR")
    except ValueError:
        pass
    eur_country = eur_country[eur_country.CNTR_CODE.isin(
        eur_country_list)]
    eur_country_list = list(eur_country.CNTR_CODE.unique().tolist())
if no_germany:
    eur_country.drop(
        eur_country[eur_country.CNTR_CODE.isin(["DE"])].index, inplace=True)
    try:
        eur_country_list.remove("DE")
    except ValueError:
        pass
if not len(eur_country_list):
    print("WARNING: No European country to be plotted.")

# modifications to eur map, if any
# keep only mainland parts for conciseness
eur_country_drop_parts = {"FR": ["FRY", "FRM"], "ES": ["ES7"], "IT": ["ITG"]}
for v in eur_country_drop_parts.values():
    eur_country.drop(
        eur_country[eur_country.NUTS_ID.isin(v)].index, inplace=True)

# read location boundaries, specify the format, reduce location representation to their centroid point
eur_location = gpd.read_file(geojsons["eur_location"])
# reduce size by limiting to included cities, then find centroid
eur_location = eur_location[eur_location.NUTS_NAME.isin(locations.id_name)]
crs = eur_location.crs
eur_location = eur_location.to_crs('+proj=cea')
eur_location['geometry'] = eur_location.centroid
eur_location = eur_location.to_crs(crs)

# read international cities
int_location = gpd.read_file(geojsons["int_location"]).to_crs(crs)

for idx, row in locations.iterrows():
    # try and get location from the european city list
    geometry = eur_location[eur_location.NUTS_NAME == row.id_name].geometry
    if geometry.empty:  # if not then check international cities list
        geometry = int_location[int_location.ls_name == row.id_name].geometry
    if geometry.empty:  # if still not found then raise error
        raise IndexError(
            "Could not place the following location on map: "+row.common_name)
    else:
        locations.loc[locations.id_name == row.id_name,
                      'latitude'] = geometry.x.values[0]
        locations.loc[locations.id_name == row.id_name,
                      'longitude'] = geometry.y.values[0]

locations = gpd.GeoDataFrame(locations, geometry=gpd.points_from_xy(
    locations.latitude, locations.longitude), crs=crs)

#######################
# Plot the static map #
#######################

if not Path.is_file(font_file):
    raise FileNotFoundError(
        "Failed to find the font file. Please make sure that you have it.")

# change projection for static map
eur_country = eur_country.to_crs("EPSG:3857")
eur_locations = locations[locations.country_code.isin(
    eur_country.CNTR_CODE)].to_crs("EPSG:3857")

# plot countries map
fig, ax = plt.subplots(1, tight_layout=True,
                       figsize=((12, 12) if only_germany else (20, 20)))
ax = eur_country.plot(ax=ax, column=color_based_on,
                      cmap='tab20', edgecolor='w')
# plot the patches
ax = eur_locations.plot(column="stage", cmap='Dark2', ax=ax, markersize=static_map_patch_size, zorder=2, legend=True, legend_kwds={
                        'prop': {'size': 25}, 'frameon': False, 'framealpha': 0.2, 'handletextpad': 0.1, 'markerscale': 2, 'bbox_to_anchor': legend_location})
# plot the number of users
for x, y, num_users in zip(eur_locations.geometry.x, eur_locations.geometry.y, eur_locations.num_users):
    ax.annotate(num_users, xy=(x, y), horizontalalignment='center',
                verticalalignment='center', color='white', font=font_file, size=static_number_fontsize)

plt.axis('off')
plt.savefig(map_filename)
if only_germany or no_germany:
    exit()  # exit after producing the static map

########################
# Plot the dynamic map #
########################

keep = []
used_stage = set(locations.stage)
for stage in ordered_stages:
    if stage in used_stage:
        keep.append(stage)
ordered_stages = keep

# limits of the dynamic
map_limits = {"lon": {"max": locations.longitude.max() + dynamic_map_padding,
                      "min": locations.longitude.min() - dynamic_map_padding},
              "lat": {"max": locations.latitude.max() + dynamic_map_padding,
                      "min": locations.latitude.min() - dynamic_map_padding}}

# load templated text for the dynamic map
html_text = (data_dir / "template.html").read_text()

# set the start and maximum zoom levels
html_text = html_text.replace(
    "$STARTZOOM$", "{}".format(dynamic_map_start_zoom))
html_text = html_text.replace("$MAXZOOM$", "{}".format(dynamic_map_max_zoom))
html_text = html_text.replace(
    "$LATMIN$", "{}".format(map_limits["lat"]["min"]))
html_text = html_text.replace(
    "$LONMIN$", "{}".format(map_limits["lon"]["min"]))
html_text = html_text.replace(
    "$LATMAX$", "{}".format(map_limits["lat"]["max"]))
html_text = html_text.replace(
    "$LONMAX$", "{}".format(map_limits["lon"]["max"]))

# set up all the location markers
marker_text = ""

# first setup the icons
for stage in ordered_stages:
    marker_text += """\n    var icon_{} = L.icon(
        {{iconUrl: '{}',
            iconSize: [25, 25],
            iconAnchor: [13, 41],
            shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{}.png',
            shadowSize: [25, 41],
            shadowAnchor: [13, 40]}}  
    );""".format(stage, overlay_icon, color[stage])

# create markers for all the locations and add them to the corresponding layer
layers = {}
for stage in ordered_stages:
    layers[stage] = "\n    var {} = L.layerGroup([".format(stage)

locations['inHTML'] = ["location"]*len(locations)
for idx, location in locations.iterrows():
    marker_text += "\n    var location{} = L.marker([{}, {}], {{icon: icon_{}}} )".format(
        idx, location.longitude, location.latitude, location.stage)
    plural = "s are" if location.num_users > 1 else " is"
    marker_text += "\n    location{}.bindTooltip(`<div>{}: {} installation{} in {} stage.<div>`, {{\"sticky\": true}});".format(
        idx, location.common_name, location.num_users, plural, location.stage)
    locations.loc[idx, "inHTML"] += str(idx)

for stage in ordered_stages:
    layers[stage] += ",".join(locations[locations.stage ==
                              stage].inHTML.tolist())+"]).addTo(map)"

for stage in ordered_stages:
    marker_text += layers[stage]

html_text = html_text.replace("// $MARKERS-GO-HERE$", marker_text)

# add layer control
# start
layercontrol_text = "\n    var overlays = {"
# include markers
for stage in ordered_stages:
    layercontrol_text += "\n        \"{} usage\": {},".format(
        stage, stage)
# end
layercontrol_text += "\n    };"

legend_html = "<b>{}</b><br>".format(legend_header)
for stage in ordered_stages:
    legend_html += "\n        <img src='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{}.png' width=12>  {} usage<br>".format(
        color[stage], stage)

html_text = html_text.replace("$LEGEND_HTML$", legend_html)
html_text = html_text.replace("// $LAYERCONTROL-GO-HERE$", layercontrol_text)

# write out the final file
Path('map.html').write_text(html_text, encoding="UTF-8")
