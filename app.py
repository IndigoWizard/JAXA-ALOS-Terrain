"""
Original Project Author: IndigoWizard, July 7, 2026.
Project Name: JAXA ALOS Terrain
"""

import streamlit as st
from streamlit_folium import folium_static, st_folium
import folium
import geemap

st.set_page_config(
    page_title="JAXA Terrain Viewer",
    layout="wide",
    menu_items={
        "About": "Interactive Terrain Mapping GIS app using JAXA ALOS World 3D Digital Surface Model Data. You can check the project's [GitHub repo](https://github.com/IndigoWizard/JAXA-ALOS-Terrain) or email me at [my Email](mailto:tro56f5j6@mozmail.com) if need be.",
        "Get Help": "mailto:tro56f5j6@mozmail.com",
        "Report a Bug": "https://github.com/IndigoWizard/JAXA-ALOS-Terrain/issues"
    }
    
)


def main():
    st.title("Terrain Viewer")
    st.markdown("View Digital Surface Model terrain through JAXA's ALOS World 3D Map high resolution data on the fly!")



if __name__ == "__main__":
    main()