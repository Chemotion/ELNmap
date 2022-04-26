from matplotlib.colors import rgb2hex
import matplotlib.patches as pat
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
import geopandas as gpd
from pathlib import Path

# change this as required
connections = [("Karlsruhe","Aachen")] # to be stored as common_name

# no need to change unless changes in apprearance are required. Please know what you are doing.
color       = {"production" : "green", # color codes for different types of instances
               "mixed"      : "blue",  # color supported in dynamic map are listed here https://github.com/pointhi/leaflet-color-markers 
               "test"       : "orange",
               "planned"    : "grey"}
ordered_stages = ["planned","test","production","mixed"]
static_map_patch_size  = 20000
dynamic_map_start_zoom = 6
dynamic_map_max_zoom   = 9
dynamic_map_padding    = 0.3 # works in tandem with the start zoom setting

# access font and JSON data
font_file = Path("OpenSans-Bold.ttf")

data_dir  = Path("data")
# NUTS level 1 is 'states' or 'group of states' or something similar
# NUTS level 3 is (usually) city-level boundary
jsons = {"country":  data_dir / "NUTS_RG_01M_2021_3035_LEVL_1.json",
         "city"   :  data_dir / "NUTS_RG_01M_2021_3035_LEVL_3.json",
         "plotted":  data_dir / "plotted_locations.json"}

# read all locations to be plotted
locations = pd.read_json(jsons["plotted"])

# determine included countries
countries_included = locations["country_code"].unique().tolist()

# read country boundaries, specify the format, limit to countries that are included
map_country     = gpd.read_file(jsons["country"])
map_country.crs = "EPSG:3035"
map_country     = map_country[map_country.CNTR_CODE.isin(countries_included)]

# modifications to map, if any
if "FR" in countries_included:
    # include only mainland France for conciseness
    map_country.drop(map_country[map_country.FID.isin(["FRY","FRM"])].index, inplace=True)

# read city boundaries, specify the format, subset to countries included
map_city        = gpd.read_file(jsons["city"])
map_city.crs    = "EPSG:3035"
map_city        = map_city[map_city.CNTR_CODE.isin(countries_included)]

# reduce city representation to their centroid point
map_city['geometry'] = map_city.centroid

# Copy city map and convert it latitue longitude map format for the sake of Leaflet
# CAUTION: They are arranged such that x = lon and y = lat
llm_city = map_city.to_crs("EPSG:4326")

# Create polygons to draw connections
mpl_polygon  = [] # matplotlib
lfl_polylin = [] # leafelt, needs lat lon format
for idx, connection in enumerate(connections):
    mpl_polygon.append([])
    lfl_polylin.append([])
    for city in connection:
        lvl3_name = locations[locations['common_name'] == city]['nuts_lvl3'].values[0] # get the level 3 name of the city
        matched_city = map_city['NAME_LATN'] == lvl3_name
        coord  = list(map_city[matched_city]['geometry'].item().coords)[0] # then get the coords associated with it
        latlon = list(llm_city[matched_city]['geometry'].item().coords)[0][::-1] # reversed because lon = x, lat = y
        mpl_polygon[-1].append(coord)
        lfl_polylin[-1].append(latlon)
    mpl_polygon[-1].append(mpl_polygon[-1][0]) #repeat the first point to create a 'closed loop' # see https://stackoverflow.com/questions/43971259/

# Create table of cities to plot
city_in_stages = {} # cities segregated according to their stage, keys are the possible stages
for stage in ordered_stages:
    city_in_stages[stage] = {} # each entry is a dictionary with city+idx as key and common_name as value
cities = [] # cities as a list of dictionaries, containing all relevant info

map_limits = {"lon":{"max":-180, "min":180},
              "lat":{"max":   0, "min": 90}} # opposite of what can happen so that the values are always overwritten
for idx, row in locations.iterrows():
    matched_city = map_city['NAME_LATN'] == row['nuts_lvl3'] # identify the city
    coord  = list(map_city[matched_city]['geometry'].item().coords)[0] # then get the coords associated with it
    latlon = list(llm_city[matched_city]['geometry'].item().coords)[0][::-1] # reversed because lon = x, lat = y
    map_limits["lat"]["max"] = max(map_limits["lat"]["max"], latlon[0])
    map_limits["lat"]["min"] = min(map_limits["lat"]["min"], latlon[0])
    map_limits["lon"]["max"] = max(map_limits["lon"]["max"], latlon[1])
    map_limits["lon"]["min"] = min(map_limits["lon"]["min"], latlon[1])
    cities.append({"name": row["common_name"], "coord": coord, "latlon": latlon, "stage": row["stage"], "num_users": row["num_users"]})
    city_in_stages[row["stage"]]["city{}".format(idx)] = row["common_name"]
map_limits["lon"]["max"] += dynamic_map_padding
map_limits["lon"]["min"] -= dynamic_map_padding
map_limits["lat"]["max"] += dynamic_map_padding
map_limits["lat"]["min"] -= dynamic_map_padding

# preserve only used patches in the ordered list
city_in_stages = {k: v for k, v in city_in_stages.items() if v} # remove empty dictionary entries
remove_stages = set(ordered_stages) - set(city_in_stages.keys())
for stage in remove_stages:
    ordered_stages.remove(stage)

#######################
# Plot the static map #
#######################

# draw the canvas for static map
fig, ax = plt.subplots(1, figsize=(15,9), tight_layout=True)

# plot countries map
map_country.plot(ax=ax, column="CNTR_CODE", cmap='tab20', edgecolor='w')

# color map for connections
tab10 = plt.cm.get_cmap('tab20', 10)

# plot the connections
connection_colors = []
for idx, polygon in enumerate(mpl_polygon):
    xs, ys = zip(*polygon)
    connection_colors.append(tab10(idx))
    conn, = plt.plot(xs, ys, color=connection_colors[-1], ls=":", lw=2)

# plot the cities
for city in cities:
    ax.add_patch(pat.Circle(city["coord"], static_map_patch_size, color=color[city["stage"]], zorder=2))
    plt.annotate(text = city["num_users"], xy = city["coord"], horizontalalignment='center', verticalalignment='center', color='white', font=font_file)

# create patches and connection-line for legend
patches_for_legend = [[], []]
for stage in ordered_stages:    
    patches_for_legend[0].append(plt.Circle(coord, static_map_patch_size, color=color[stage]))
    patches_for_legend[1].append(stage.title())
if connection_colors: # when more than one connections exist, represent them just once with a black dotted line
    conn_text = ["Connected Repository"]
    if len(connection_colors) > 1:
        conn_text = ["Connected Repositories"]
        from copy import copy
        conn = copy(conn)
        conn.set_visible=False 
        conn.set_color("black")
    conn = [conn]
else: # do not include connections entry in legend if no connections are present
    conn = []
    conn_text = []

plt.legend(conn+patches_for_legend[0], conn_text+patches_for_legend[1]).set_draggable(True)
cursor = mplcursors.cursor(multiple=True)
plt.axis('off')
plt.savefig("map.svg")

########################
# Plot the dynamic map #
########################

# load templated text for the dynamic map 
html_text = (data_dir / "template.html").read_text()

# set the start and maximum zoom levels
html_text = html_text.replace("$STARTZOOM$", "{}".format(dynamic_map_start_zoom))
html_text = html_text.replace("$MAXZOOM$", "{}".format(dynamic_map_max_zoom))
html_text = html_text.replace("$LATMIN$", "{}".format(map_limits["lat"]["min"]))
html_text = html_text.replace("$LONMIN$", "{}".format(map_limits["lon"]["min"]))
html_text = html_text.replace("$LATMAX$", "{}".format(map_limits["lat"]["max"]))
html_text = html_text.replace("$LONMAX$", "{}".format(map_limits["lon"]["max"]))

# set up all the city markers
marker_text = ""

# first setup the icons
for stage in ordered_stages:
    marker_text += """\n    var icon_{} = L.icon(
        {{iconUrl: 'https://raw.githubusercontent.com/harivyasi/ELNmap/main/data/favicon.ico',
            iconSize: [25, 25],
            iconAnchor: [13, 41],
            shadowUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{}.png',
            shadowSize: [25, 41],
            shadowAnchor: [13, 40]}}  
    );""".format(stage, color[stage])

# create markers for all the cities and add them to the corresponding layer
layers = {}
for stage in ordered_stages:
    layers[stage] = "\n    var {} = L.layerGroup([".format(stage)

for idx, city in enumerate(cities):
    marker_text += "\n    var city{} = L.marker([{}, {}], {{icon: icon_{}}} )".format(idx, city["latlon"][0], city["latlon"][1], city["stage"])
    plural = "s" if city['num_users'] > 1 else ""
    marker_text += "\n    city{}.bindTooltip(`<div>{}: {} installation{} in {} usage.<div>`, {{\"sticky\": true}});".format(idx, city["name"], city["num_users"], plural, city["stage"])
    for stage, city_dict in city_in_stages.items():
        if "city{}".format(idx) in city_dict:
            layers[stage] += "city{},".format(idx)

for stage in layers:
    layers[stage] = layers[stage].rstrip(',')+"]).addTo(map)"

for stage in ordered_stages:
    marker_text += layers[stage]

html_text = html_text.replace("// $MARKERS-GO-HERE$", marker_text)

# draw all polylines, club them together into 'connections' so as to be used by the control later

polyline_text = ""
for idx, polyline in enumerate(lfl_polylin):
    latlon_str = ""
    for latlon in polyline:
        latlon_str += "[{}, {}],".format(latlon[0],latlon[1])
    latlon_str = latlon_str.rstrip(',')
    polyline_text += """\n    var polyline{} = L.polyline(
        [{}],
        {{"color": "{}", "lineCap": "round", "lineJoin": "round", "opacity": 0.8, "smoothFactor": 1.0, "stroke": true, "weight": 5}}
        )""".format(idx, latlon_str, rgb2hex(connection_colors[idx]))
if polyline_text:
    polyline_text += "\n    var connections = L.layerGroup([" + ",".join(["polyline{}".format(idx) for idx in range(len(lfl_polylin))]) + "]).addTo(map)"

html_text = html_text.replace("// $POLYLINES-GO-HERE$", polyline_text)

# add layer control
# start
layercontrol_text = "\n    var overlays = {"
# include markers
for stage in ordered_stages:
    layercontrol_text += "\n        \"{} usage\": {},".format(stage.capitalize(), stage)
# include connections
if connection_colors:
    layercontrol_text += "\n        \"Connections\": connections"
# end
layercontrol_text += "\n    };"

legend_html = "<b><a href='https://chemotion.net/'>Chemotion</a></b><br>"
for stage in ordered_stages:
    legend_html += "\n        <img src='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{}.png' width=12>  {} usage<br>".format(color[stage], stage.capitalize())

html_text = html_text.replace("$LEGEND_HTML$", legend_html)
html_text = html_text.replace("// $LAYERCONTROL-GO-HERE$", layercontrol_text)

# write out the final file
Path('map.html').write_text(html_text)