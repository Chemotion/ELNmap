#!/bin/sh
# make the data folder
mkdir -p data
cd data
# download and save the font
wget -N https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf
# download and save the topojson files
wget -N https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_1.geojson
wget -N https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_3.geojson
wget -N https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_populated_places_simple.geojson