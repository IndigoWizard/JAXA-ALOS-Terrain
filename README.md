# JAXA-ALOS-Terrain

**'JAXA ALOS Terrain'** project is an interactive web GIS app that let's you view terrain information from **JAXA's ALOS World 3D Map 30m (AW3D30)** dataset using a Digital Surface Model (DSM).<br>
The project is intended for educational purposes, terrain exploration, environmental studies, GIS analysis, and rapid visualization workflows using high resolution global Digital Surface Model datasets.

Users can upload a GeoJSON file of the Area of Interest (AOI) and instantly generate an interactive map with multiple terrain visualization layers directly computed in the cloud, including:

* Digitial Surface Model (DSM)
* Colorized Elevation layer
* Hillshade
* Aspect
* Slopes
* Contour lines (isolines)

All geoprocessing is performed in the cloud using **Earth Engine**, eliminating the need to download or pre-process DEM/DSM datasets locally. The app automatically filters, mosaics, clips and process the ALOS W3D satellite imagery to the Area of Interest, providing fast and interactive terrain visualization for any supported location (on land).


## Features

* Handles GeoJSON files parsing for area of interest
* Map zoom on AOI centroid
* Interactive web map
* High resolution 30m DSM up to date based on JAXA ALOS data
* Multiple terrain derivatives
* Lightweight app inthe browser no authentication, no login, just use it.

This project is based off an old project ([GHW-GEE-API](https://github.com/IndigoWizard/GHW-GEE-API)) I built in 2023 during MLH Global Hack Week: April for APIs, for the Earth Science workshop using Earth Engine Python API. The dataset used back then was ALOS W3D V2.1, which has been depracated and it was a naked Python script, requiring developement environment setup and earth engine account, so I rebuilt it as a user-friendly web app using Streamlit where you can just access the app and use it without any technical or scientific requirements.


## Credit
The project and app was developped by [IndigoWizard](https://github.com/IndigoWizard) using; Python, Streamlit, Google Earth Engine Python API, Folium and geemap. The DSM data is from [JAXA (*Japan Aerospace Exploration Agency*)](https://www.jaxa.jp/) - [ALOS World 3D (30m)](https://www.eorc.jaxa.jp/ALOS/jp/dataset/aw3d_j.htm) dataset.