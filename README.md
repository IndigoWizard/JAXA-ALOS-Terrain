# JAXA-ALOS-Terrain

<p align="center">
  <a href="https://terrain-viewer.streamlit.app/"><img src="https://cdn-icons-png.flaticon.com/512/18693/18693124.png" alt="wildfire-icon" width="180"></a>
</p>

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live_App-brightgreen?logo=streamlit)](https://terrain-viewer.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.13-yellow?logo=python&logoColor=blue)
![GitHub Release](https://img.shields.io/github/v/release/IndigoWizard/JAXA-ALOS-Terrain?&logo=github&label=Release&color=ff4173)
![GitHub issues](https://img.shields.io/github/issues/IndigoWizard/JAXA-ALOS-Terrain?style=flat&logo=github&color=red)
![GitHub pull requests](https://img.shields.io/github/issues-pr-closed/IndigoWizard/JAXA-ALOS-Terrain?style=flat&logo=github&label=Pull%20Rrequests&color=orange)
![GitHub Repo stars](https://img.shields.io/github/stars/IndigoWizard/JAXA-ALOS-Terrain?style=flat&logo=github&label=Stars%20%E2%AD%90&color=yellow)
![ʕ　·ᴥ·ʔ](https://img.shields.io/badge/<_Consider_starring_⭐_the_project_ʕ_•ᴥ•ʔ_..._ʕ　·ᴥ·ʔ-blue.svg)

**'JAXA ALOS Terrain'** project is an interactive Web GIS app that let's you view terrain information from **JAXA's ALOS World 3D Map 30m (AW3D30)** dataset using a Digital Surface Model (DSM).<br>
The project is intended for terrain exploration, environmental studies, GIS analysis, and rapid visualization workflows using high resolution global Digital Surface Model datasets.

## Preview:

|RAW DSM (30m)|Hillshade|Aspect|Elevation (DSM Colorized)|
|:--:|:--:|:--:|:--:|
|![image](https://github.com/user-attachments/assets/3d7e6541-62e0-45b6-bed4-042a14e89417)|![image](https://github.com/user-attachments/assets/1688d877-c7ff-4d65-ab33-7601ed12af34)|![image](https://github.com/user-attachments/assets/53d99b58-d1d0-4bff-9837-6f896bd40488)|![image](https://github.com/user-attachments/assets/b4477aa4-d6c7-4506-8554-5eadcd69f24b)|
|Slopes|Contours (dark basemap)|Contours (light basemap)|Final Result - Layers Overlap|
|![image](https://github.com/user-attachments/assets/cc31c470-7b7e-42d0-894c-b69e445d01ce)|![image](https://github.com/user-attachments/assets/72cb7cb0-10e7-44ba-9352-d0dd7dc992ef)|![image](https://github.com/user-attachments/assets/8b3290a4-a7ed-49d2-bb54-72849f354c42)|![image](https://github.com/user-attachments/assets/36183b26-d883-4ba8-b4d7-b654de6054ba)|


## Features

Users can upload a GeoJSON file of the Area of Interest (AOI) and instantly generate an interactive map with multiple terrain visualization layers directly computed in the cloud, including:

- **DSM:** A Digital Surface Model that displays terrain elevation information that includes vegetation and buildings.
- **Elevation:** The colorized visualization of the DSM to improve terrain interpretation.
- **Hillshade:** Artificial illumination of the terrain to emphasize relief. It is useful for visually identifying **ridges**, **valleys** and **landforms**.
- **Aspect:** Direction each slope faces, measured clockwise starting from the north. It can be useful for; **solar exposure**, **watershed analysis** and *hydrological modeling**.
- **Slopes:** Terrain steepness in degrees. Useful for; **engineering**, **erosion**, **landslide susceptibility**, **animal habitat analysis** (e.g: cougars... etc).
- **Contours:** Isolines connecting equal elevations at certain intervals. Useful for; **topographic interpretation**, **terrain planning** and **map reading**.

All geoprocessing is performed in the cloud using **Earth Engine**, eliminating the need to download or pre-process DEM/DSM datasets locally. The app automatically filters, mosaics, clips and process the ALOS W3D satellite imagery to the Area of Interest, providing fast and interactive terrain visualization for any supported location (on land).

- Handles GeoJSON files parsing for area of interest
- AOI-based Min-Max local elevation
- Map zoom centered on AOI
- Interactive web map
- High resolution 30m DSM up to date based on JAXA ALOS data
- Multiple terrain derivatives
- Lightweight app in the browser; no authentication, no login, just use it.


<sub>This project is based off an old project *([GHW-GEE-API](https://github.com/IndigoWizard/GHW-GEE-API))* I built in 2023 during MLH Global Hack Week: April for APIs, for the Earth Science workshop using Earth Engine Python API. The dataset used back then was ALOS W3D V2.1, which has been depracated and it was a naked Python script, requiring developement environment setup and earth engine account, so I rebuilt it as a user-friendly web app using Streamlit where you can just access the app and use it without any technical or scientific requirements.</sub>


## Credit
The project was developped by [IndigoWizard](https://github.com/IndigoWizard) using; Python, Streamlit, Google Earth Engine, Folium and geemap. With data from **JAXA ALOS World 3D (AW3D30)**, 30m high-resolution Digital Surface Model dataset;
- **Provider:** [Japan Aerospace Exploration Agency (JAXA)](https://www.jaxa.jp/)
- **Mission:** [Advanced Land Observing Satellite (ALOS)](https://earth.jaxa.jp/ja/research/projects/alos/index.html)
- **Dataset:** [ALOS World 3D (AW3D30)](https://www.eorc.jaxa.jp/ALOS/jp/dataset/aw3d_j.htm)
- **Version:** 4.1
- **Resolution:** 30 m
- **Type:** Digital Surface Model (DSM)
- **Platform:** Google Earth Engine
