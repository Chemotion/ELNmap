import matplotlib.pyplot as plt
import matplotlib
import geopandas as gpd

data_dir = "data/"
path = data_dir + "NUTS_RG_01M_2021_3035_LEVL_3.json"
pathBorders = data_dir + "NUTS_RG_01M_2021_3035_LEVL_1.json"

map_CH = gpd.read_file(path)
map_CH = map_CH[map_CH.CNTR_CODE == "CH"]

map_borders = gpd.read_file(pathBorders)
map_borders = map_borders[map_borders.CNTR_CODE == "DE"]

map_df = gpd.read_file(path)
map_df = map_df[map_df.CNTR_CODE == "DE"]
map_df = map_df.append(map_CH)

fig, ax = plt.subplots(1, figsize=(10, 6))
map_df['coords'] = map_df['geometry'].apply(lambda x: x.representative_point().coords[:])
map_df['coords'] = [coords[0] for coords in map_df['coords']]
map_df.plot(ax=ax, color='lightblue')

cities = [["Aachen","Städteregion Aachen","productive",4]]
cities.append(["Braunschweig", "Braunschweig, Kreisfreie Stadt", "testing",2])
cities.append(["Chemnitz", "Chemnitz, Kreisfreie Stadt","planned",1])
cities.append(["Dresden","Dresden, Kreisfreie Stadt","testing",1])
cities.append(["Duisburg-Essen","Duisburg, Kreisfreie Stadt","productive",1])
cities.append(["Freiburg","Freiburg im Breisgau, Stadtkreis","testing",1])
cities.append(["Greifswald","Vorpommern-Greifswald","productive",1])
cities.append(["Heidelberg","Heidelberg, Stadtkreis","productive",1])
cities.append(["Jena","Jena, Kreisfreie Stadt","productive",1])
cities.append(["Kaiserslautern","Kaiserslautern, Kreisfreie Stadt","productive",1])
cities.append(["Karlsruhe","Karlsruhe, Stadtkreis","mixed",5])
cities.append(["Kiel","Kiel, Kreisfreie Stadt","planned",1])
cities.append(["Köln","Köln, Kreisfreie Stadt","testing",1])
cities.append(["Lausanne","Genève","productive",1])
cities.append(["Mainz","Mainz, Kreisfreie Stadt","testing",1])
cities.append(["Paderborn","Paderborn","productive",1])
cities.append(["Stuttgart","Stuttgart, Stadtkreis","productive",2])
cities.append(["Zürich","Zürich","mixed",3])

xyKarlsruhe = map_df[map_df.NAME_LATN == "Karlsruhe, Stadtkreis"]['coords'].values[0]
xyAachen = map_df[map_df.NAME_LATN == "Städteregion Aachen"]['coords'].values[0]
plt.plot([xyKarlsruhe[0], xyAachen[0]], [xyKarlsruhe[1], xyAachen[1]], color='red', linestyle=":", linewidth=2, zorder=2)

font_path = "Open_Sans/static/OpenSans/OpenSans-Bold.ttf"
prop = matplotlib.font_manager.FontProperties(fname=font_path)

for idx, row in map_df.iterrows():
    for city in cities:
        if row['NAME_LATN'] == city[1]:
            if city[2] == "productive" or city[2] == "mixed":
                plt.annotate(text=city[3], xy=row['coords'], horizontalalignment='center', verticalalignment='center', color='w', fontproperties=prop, zorder=idx+3)
                circle = plt.Circle(row['coords'], 20000, color='g', zorder=idx+2)
            elif city[2] == "testing":
                plt.annotate(text=city[3], xy=row['coords'], horizontalalignment='center', verticalalignment='center', color='black', fontproperties=prop, alpha=1)
                circle = plt.Circle(row['coords'], 20000, color='orange')
            elif city[2] == "planned":
                plt.annotate(text=city[3], xy=row['coords'], horizontalalignment='center', verticalalignment='center', color='w', fontproperties=prop)
                circle = plt.Circle(row['coords'], 20000, color='b')
            # elif city[2] == "mixed":
            #     plt.annotate(text=city[3], xy=row['coords'], horizontalalignment='center', verticalalignment='center', color='w', fontproperties=prop)
            #     circle = matplotlib.patches.Wedge(row['coords'], 20000, 45, 225, fc='g')
            #     ax.add_patch(circle)
            #     circle = matplotlib.patches.Wedge(row['coords'], 20000, 225, 45, fc='orange')
            else:       
                plt.annotate(text=city[3], xy=row['coords'], horizontalalignment='center', verticalalignment='center', color='b', fontproperties=prop)
                circle = plt.Circle(row['coords'], 20000, color='w')

            ax.add_patch(circle)

map_borders.boundary.plot(color='w', ax=ax, zorder=1)

plt.axis('off')
plt.show()