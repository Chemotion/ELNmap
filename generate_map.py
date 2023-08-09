from pathlib import Path
from matplotlib.colors import rgb2hex
from matplotlib import colormaps
import matplotlib.patches as pat
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# change this as required
connections = []  # [("Karlsruhe","Aachen")] # to be stored as common_name

# no need to change unless changes in apprearance are required. Please know what you are doing.
color = {"production": "green",  # color codes for different types of instances
         "mixed": "blue",  # color supported in dynamic map are listed here https://github.com/pointhi/leaflet-color-markers
         "test": "orange",
         "planned": "grey"}
ordered_stages = ["planned", "test", "production", "mixed"]
static_map_patch_size = 20000
dynamic_map_start_zoom = 6
dynamic_map_max_zoom = 9
dynamic_map_padding = 0.3  # works in tandem with the start zoom setting
overlay_icon = "https://raw.githubusercontent.com/harivyasi/ELNmap/main/data/favicon.ico"
legend_header = "<a href='https://chemotion.net/'>Chemotion</a>"
legend_location = "lower right"

# access font and JSON data
data_dir = Path("data")
font_file = data_dir / "OpenSans-Bold.ttf"
# NUTS level 1 is 'states' or 'group of states' or something similar
# NUTS level 3 is (usually) city-level boundary
jsons = {"country":  data_dir / "NUTS_RG_01M_2021_3035_LEVL_1.json",
         "city":  data_dir / "NUTS_RG_01M_2021_3035_LEVL_3.json",
         "plotted":  data_dir / "plotted_locations.json"}

# read all locations to be plotted
locations = pd.read_json(jsons["plotted"])

# determine included countries
countries_included = locations["country_code"].unique().tolist()

# read country boundaries, specify the format, limit to countries that are included
map_country = gpd.read_file(jsons["country"])
map_country.crs = "EPSG:3035"
map_country = map_country[map_country.CNTR_CODE.isin(countries_included)]

# modifications to map, if any
if "FR" in countries_included:
    # include only mainland France for conciseness
    map_country.drop(map_country[map_country.FID.isin(
        ["FRY", "FRM"])].index, inplace=True)
    
if "ES" in countries_included:
    # include only mainland Spain for conciseness
    map_country.drop(map_country[map_country.FID.isin(
        ["ES7"])].index, inplace=True)

# read city boundaries, specify the format, subset to countries included
map_city = gpd.read_file(jsons["city"])
map_city.crs = "EPSG:3035"
map_city = map_city[map_city.CNTR_CODE.isin(countries_included)]

# reduce city representation to their centroid point
map_city['geometry'] = map_city.centroid

# Copy city map and convert it latitue longitude map format for the sake of Leaflet
# CAUTION: They are arranged such that x = lon and y = lat
llm_city = map_city.to_crs("EPSG:4326")

# Create polygons to draw connections
mpl_polygon = []  # matplotlib
lfl_polylin = []  # leafelt, needs lat lon format
for idx, connection in enumerate(connections):
    mpl_polygon.append([])
    lfl_polylin.append([])
    for city in connection:
        # get the level 3 name of the city
        lvl3_name = locations[locations['common_name']
                              == city]['nuts_lvl3'].values[0]
        matched_city = map_city['NAME_LATN'] == lvl3_name
        coord = list(map_city[matched_city]['geometry'].item().coords)[
            0]  # then get the coords associated with it
        latlon = list(llm_city[matched_city]['geometry'].item().coords)[
            0][::-1]  # reversed because lon = x, lat = y
        mpl_polygon[-1].append(coord)
        lfl_polylin[-1].append(latlon)
    if mpl_polygon[-1]:
        # repeat the first point to create a 'closed loop' # see https://stackoverflow.com/questions/43971259/
        mpl_polygon[-1].append(mpl_polygon[-1][0])

# Create table of cities to plot
# cities segregated according to their stage, keys are the possible stages
city_in_stages = {}
for stage in ordered_stages:
    # each entry is a dictionary with city+idx as key and common_name as value
    city_in_stages[stage] = {}
cities = []  # cities as a list of dictionaries, containing all relevant info

map_limits = {"lon": {"max": -180.0, "min": 180.0},  # useful for determining canvas of the static map
              "lat": {"max":    0.0, "min":  90.0}}  # opposite of what can happen so that the values are always overwritten
for idx, row in locations.iterrows():
    # identify the city
    matched_city = map_city['NAME_LATN'] == row['nuts_lvl3']
    coord = list(map_city[matched_city]['geometry'].item().coords)[
        0]  # then get the coords associated with it
    latlon = list(llm_city[matched_city]['geometry'].item().coords)[
        0][::-1]  # reversed because lon = x, lat = y
    map_limits["lat"]["max"] = max(map_limits["lat"]["max"], latlon[0])
    map_limits["lat"]["min"] = min(map_limits["lat"]["min"], latlon[0])
    map_limits["lon"]["max"] = max(map_limits["lon"]["max"], latlon[1])
    map_limits["lon"]["min"] = min(map_limits["lon"]["min"], latlon[1])
    cities.append({"name": row["common_name"], "coord": coord, "latlon": latlon,
                  "stage": row["stage"], "num_users": row["num_users"]})
    city_in_stages[row["stage"]]["city{}".format(idx)] = row["common_name"]
map_limits["lon"]["max"] += dynamic_map_padding
map_limits["lon"]["min"] -= dynamic_map_padding
map_limits["lat"]["max"] += dynamic_map_padding
map_limits["lat"]["min"] -= dynamic_map_padding

# preserve only used patches in the ordered list
# remove empty dictionary entries
city_in_stages = {k: v for k, v in city_in_stages.items() if v}
remove_stages = set(ordered_stages) - set(city_in_stages.keys())
for stage in remove_stages:
    ordered_stages.remove(stage)

#######################
# Plot the static map #
#######################

if not Path.is_file(font_file):
    raise FileNotFoundError(
        "Failed to find the font file. Please make sure that you have it.")

# draw the canvas for static map
fig, ax = plt.subplots(1, figsize=(9, 15), tight_layout=True)

# plot countries map
map_country.plot(ax=ax, column="CNTR_CODE", cmap='tab20', edgecolor='w')

# color map for connections
tab10 = colormaps["tab10"]

# plot the connections
connection_colors = []
for idx, polygon in enumerate(mpl_polygon):
    if polygon:
        xs, ys = zip(*polygon)
        connection_colors.append(tab10(idx))
        conn, = plt.plot(xs, ys, color=connection_colors[-1], ls=":", lw=2)

# plot the cities
for city in cities:
    ax.add_patch(pat.Circle(
        city["coord"], static_map_patch_size, color=color[city["stage"]], zorder=2))
    plt.annotate(text=city["num_users"], xy=city["coord"], horizontalalignment='center',
                 verticalalignment='center', color='white', font=font_file, size=20)

# create patches and connection-line for legend
patches_for_legend = [[], []]
for stage in ordered_stages:
    patches_for_legend[0].append(plt.Circle(
        coord, static_map_patch_size, color=color[stage]))
    patches_for_legend[1].append(stage.title())
if connection_colors:  # when more than one connections exist, represent them just once with a black dotted line
    conn_text = ["Connected Repository"]
    if len(connection_colors) > 1:
        conn_text = ["Connected Repositories"]
        from copy import copy
        conn = copy(conn)
        conn.set_visible = False
        conn.set_color("black")
    conn = [conn]
else:  # do not include connections entry in legend if no connections are present
    conn = []
    conn_text = []

plt.legend(conn+patches_for_legend[0], conn_text +
           patches_for_legend[1], loc=legend_location, prop={'size': 30}, frameon=False, framealpha=0)
plt.axis('off')
plt.savefig("map.svg")


########################
# Plot the dynamic map #
########################

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

# set up all the city markers
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

# create markers for all the cities and add them to the corresponding layer
layers = {}
for stage in ordered_stages:
    layers[stage] = "\n    var {} = L.layerGroup([".format(stage)

for idx, city in enumerate(cities):
    marker_text += "\n    var city{} = L.marker([{}, {}], {{icon: icon_{}}} )".format(
        idx, city["latlon"][0], city["latlon"][1], city["stage"])
    plural = "s" if city['num_users'] > 1 else ""
    marker_text += "\n    city{}.bindTooltip(`<div>{}: {} installation{} in {} usage.<div>`, {{\"sticky\": true}});".format(
        idx, city["name"], city["num_users"], plural, city["stage"])
    for stage, city_dict in city_in_stages.items():
        if "city{}".format(idx) in city_dict:
            layers[stage] += "city{},".format(idx)

for stage in layers:
    layers[stage] = layers[stage].rstrip(',')+"]).addTo(map)"

for stage in ordered_stages:
    marker_text += layers[stage]

html_text = html_text.replace("// $MARKERS-GO-HERE$", marker_text)

# if connections exist, draw all polylines, club them together into 'connections' so as to be used by the control later

polyline_text = ""
if connection_colors:  # shorthand to check if connections exists
    for idx, polyline in enumerate(lfl_polylin):
        latlon_str = ""
        for latlon in polyline:
            latlon_str += "[{}, {}],".format(latlon[0], latlon[1])
        latlon_str = latlon_str.rstrip(',')
        polyline_text += """\n    var polyline{} = L.polyline(
        [{}],
        {{"color": "{}", "lineCap": "round", "lineJoin": "round", "opacity": 0.8, "smoothFactor": 1.0, "stroke": true, "weight": 5}}
        )""".format(idx, latlon_str, rgb2hex(connection_colors[idx]))
    polyline_text += "\n    var connections = L.layerGroup([" + ",".join(
        ["polyline{}".format(idx) for idx in range(len(lfl_polylin))]) + "]).addTo(map)"

html_text = html_text.replace("// $POLYLINES-GO-HERE$", polyline_text)

# add layer control
# start
layercontrol_text = "\n    var overlays = {"
# include markers
for stage in ordered_stages:
    layercontrol_text += "\n        \"{} usage\": {},".format(
        stage.capitalize(), stage)
# include connections
if connection_colors:
    layercontrol_text += "\n        \"Connections\": connections"
# end
layercontrol_text += "\n    };"

legend_html = "<b>{}</b><br>".format(legend_header)
for stage in ordered_stages:
    legend_html += "\n        <img src='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{}.png' width=12>  {} usage<br>".format(
        color[stage], stage.capitalize())

html_text = html_text.replace("$LEGEND_HTML$", legend_html)
html_text = html_text.replace("// $LAYERCONTROL-GO-HERE$", layercontrol_text)

# write out the final file
Path('map.html').write_text(html_text, encoding="UTF-8")
