import matplotlib.pyplot as plt
import matplotlib.font_manager as mplf
import mplcursors as mplc
import pandas as pd
import geopandas as gpd
import folium
import branca
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

connections = [("Karlsruhe","Aachen")] # can be moved to a separate file if required, to be stored as common_name

# draw the canvas
fig, ax = plt.subplots(1, figsize=(15,9), tight_layout=True)

# read all locations
locations = pd.read_json(jsons["plotted"])

# determine included countries
countries_included = locations["country_code"].unique().tolist()

# read country boundaries, specify the format
map_country     = gpd.read_file(jsons["country"])
map_country.crs = "EPSG:3035"
map_country     = map_country[map_country.CNTR_CODE.isin(countries_included)]

# modifications to map, if any
if "FR" in countries_included:
    # if possible, include only mainland for conciseness
    map_country.drop(map_country[map_country.FID.isin(["FRY","FRM"])].index, inplace=True)

# plot countries map
map_country.plot(ax=ax, column="CNTR_CODE", cmap='tab20', edgecolor='w')

# read city boundaries, specify the format, subset to countries included
map_city     = gpd.read_file(jsons["city"])
map_city.crs = "EPSG:3035"
map_city     = map_city[map_city.CNTR_CODE.isin(countries_included)]

# reduce city representation to their the centroid point
map_city['geometry'] = map_city.centroid
llm_city = map_city.to_crs("EPSG:4326") # city in lat lon map format for the sake of folium. CAUTION: They are arranged such that x = lon and y = lat

# set color for patches
color = {"production" : "green",
         "mixed"      : "green", 
         "testing"    : "orange",
         "planned"    : "blue"}

# Draw dynamic map using folium
map_center = list(llm_city[llm_city['NAME_LATN']=="Paderborn"].geometry.item().coords)[0]
m = folium.Map(map_center[::-1], tiles="CartoDB positron", zoom_start=6, max_zoom=8) # center on Paderborn, roughly at the center of current locations // 20220424

# plot all connections
tab10 = plt.cm.get_cmap("tab10", 10) # color map for connections
for idx, connection in enumerate(connections):
    mpl_polygon  = []
    fol_polyline = []
    for city in connection:
        lvl3_name = locations[locations['common_name'] == city]['nuts_lvl3'].values[0] # get the level 3 name of the city
        matched_city = map_city['NAME_LATN'] == lvl3_name
        coord  = list(map_city[matched_city]['geometry'].item().coords)[0] # then get the coords associated with it
        latlon = list(llm_city[matched_city]['geometry'].item().coords)[0][::-1]
        mpl_polygon.append(coord)
        fol_polyline.append(latlon)
    mpl_polygon.append(mpl_polygon[0]) #repeat the first point to create a 'closed loop' # see https://stackoverflow.com/questions/43971259/
    folium.PolyLine(fol_polyline, weight=5, color="blue", opacity=0.8).add_to(m)
    xs, ys = zip(*mpl_polygon)
    conn, = plt.plot(xs, ys, color=tab10(idx), ls=":", lw=2)

# plot all the cities
used_patches = []
for idx, row in locations.iterrows():
    matched_city = map_city['NAME_LATN'] == row['nuts_lvl3']
    coord  = list(map_city[matched_city]['geometry'].item().coords)[0]
    latlon = list(llm_city[matched_city]['geometry'].item().coords)[0][::-1]
    plural = "s" if row['num_users'] > 1 else ""
    stage = "production or test stages" if row["stage"]=="mixed" else row["stage"]+" stage"
    tip = "{}: {} installation{} in {}".format(row['common_name'], row['num_users'], plural, stage)
    folium.Marker(latlon, tooltip=tip, icon=folium.Icon(icon="flask", prefix="fa", color="green")).add_to(m)
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

# save the static and dynamic maps
plt.legend([conn]+patches_for_legend[1], ['Connected Repositories']+patches_for_legend[0]).set_draggable(True)
cursor = mplc.cursor(multiple=True)
plt.axis('off')
plt.savefig("map.svg")
colormap = branca.colormap.StepColormap(colors=["blue"], caption="Connected Repositories", vmin=2, vmax=3, max_labels=1)
colormap.add_to(m)
m.save("map.html")