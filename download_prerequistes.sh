#!/bin/sh
# make the data folder
mkdir -p data
cd data
# download and save the font
wget -N https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf
# download and save the topojson files
wget -N https://gisco-services.ec.europa.eu/distribution/v2/nuts/topojson/NUTS_RG_01M_2021_3035_LEVL_1.json
wget -N https://gisco-services.ec.europa.eu/distribution/v2/nuts/topojson/NUTS_RG_01M_2021_3035_LEVL_3.json