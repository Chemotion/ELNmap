import matplotlib.pyplot as plt
import matplotlib.font_manager as mplf
import mplcursors as mplc
import pandas as pd
import geopandas as gpd
from pathlib import Path

# data directory
data_dir  = Path("data")
font_path = Path("OpenSans-Bold.ttf")

# load font
font = mplf.FontProperties(fname=font_path)

# NUTS level 1 is 'states' or 'group of states' or something similar
# NUTS level 3 is (usually) city-level boundary

jsons = {"country":  data_dir / "NUTS_RG_01M_2021_3035_LEVL_1.json",
         "city"   :  data_dir / "NUTS_RG_01M_2021_3035_LEVL_3.json",
         "plotted":  data_dir / "plotted_locations.json"}

connections = [("Karlsruhe","Aachen")] # can be moved to a separate file if required

# draw the canvas
fig, ax = plt.subplots(1, figsize=(15,9), tight_layout=True)

# read all locations
locations = pd.read_json(jsons["plotted"])

# determine included countries
countries_included = locations["country_code"].unique().tolist()

# read country boundaries
map_country = gpd.read_file(jsons["country"])
map_country = map_country[map_country.CNTR_CODE.isin(countries_included)]

# modifications to map, if any
if "FR" in countries_included:
    # if possible, include only mainland for conciseness
    map_country.drop(map_country[map_country.FID.isin(["FRY","FRM"])].index, inplace=True)

# plot countries map
map_country.plot(ax=ax, column="CNTR_CODE", cmap='tab20', edgecolor='w')

# read city boundaries, subset to countries included
map_city = gpd.read_file(jsons["city"])
map_city = map_city[map_city.CNTR_CODE.isin(countries_included)]

# find the representative point
map_city['coords'] = map_city['geometry'].apply(lambda x: x.representative_point().coords[0])

# set color for patches
color = {"production" : "green",
         "mixed"      : "green", 
         "testing"    : "orange",
         "planned"    : "blue"}

# plot all connections
tab10 = plt.cm.get_cmap("tab10", 10) # color map for connections
for idx, connection in enumerate(connections):
    polygon = []
    for city in connection:
        lvl3_name = locations[locations['common_name'] == city]['nuts_lvl3'].values[0]
        polygon.append(map_city[map_city['NAME_LATN'] == lvl3_name]['coords'].values[0])
    polygon.append(polygon[0]) #repeat the first point to create a 'closed loop' # see https://stackoverflow.com/questions/43971259/
    xs, ys = zip(*polygon)
    conn, = plt.plot(xs, ys, color=tab10(idx), ls=":", lw=2)

# plot all the cities
used_patches = []
for idx, row in locations.iterrows():
    coord = map_city[map_city['NAME_LATN'] == row['nuts_lvl3']]['coords'].values[0]
    ax.add_patch(plt.Circle(coord, 20000, color=color[row["stage"]]))
    used_patches.append(row["stage"])
    plt.annotate(text = row["num_users"], xy = coord, horizontalalignment='center', verticalalignment='center', color='white', fontproperties=font)

# create patches for legend
used_patches = set(used_patches)
used_patches.remove("mixed") # ignore mixed as the color is same as production
patches_for_legend = [[], []]
for patch in used_patches:
    patches_for_legend[0].append(patch.title())
    patches_for_legend[1].append(plt.Circle(coord, 20000, color=color[patch]))

plt.legend([conn]+patches_for_legend[1], ['Connected Repositories']+patches_for_legend[0]).set_draggable(True)
cursor = mplc.cursor(multiple=True)
plt.axis('off')
plt.savefig("map.svg")