"""
Original Project Author: IndigoWizard, July 7, 2026.
Project Name: JAXA ALOS Terrain
"""

import streamlit as st
import ee
from ee import oauth
from google.oauth2 import service_account
from streamlit_folium import folium_static, st_folium
import folium
import geemap
import json

st.set_page_config(
    page_title="JAXA Terrain Viewer",
    layout="wide",
    menu_items={
        "About": "Interactive Terrain Mapping GIS app using JAXA ALOS World 3D Digital Surface Model Data. You can check the project's [GitHub repo](https://github.com/IndigoWizard/JAXA-ALOS-Terrain) or email me at [my Email](mailto:tro56f5j6@mozmail.com) if need be.",
        "Get Help": "mailto:tro56f5j6@mozmail.com",
        "Report a Bug": "https://github.com/IndigoWizard/JAXA-ALOS-Terrain/issues"
    }
    
)

# ee auth (use service account + key & init ee) for cloud deployement
@st.cache_data(persist=True, show_spinner="Authenticating to GEE")
def ee_authenticate():
    # checking for json key in streamlit secrets
    if "json_key" in st.secrets:
        json_creds = st.secrets["json_key"]
        service_account_info = json.loads(json_creds)

        # catching possible email related errors
        if "client_email" not in service_account_info:
            raise ValueError("Service account email address missing in json key")
        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=oauth.SCOPES)

        # intizializing gee for each app run
        ee.Initialize(creds)
    else:
        # fallback to normal init method if no json key/st.secrets available (locally)
        ee.Initialize()


# ee drawing method
def add_ee_layer(self, ee_image_object, vis_params, name):
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    layer = folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='GEE',
        name=name,
        overlay=True,
        control=True
    )
    layer.add_to(self)
    return layer

# ee display rendering method config in folium
folium.Map.add_ee_layer = add_ee_layer


def main():

    # inti gee
    # ee_authenticate()

    st.title("Terrain Viewer")
    st.markdown("View Digital Surface Model terrain through JAXA's ALOS World 3D Map high resolution data on the fly!")

    # main map
    m = folium.Map(location=[36.45, 10.85], tiles=None, zoom_start=5, control=True, control_scale=True, attributionControl=0)

    # basemaps tiles
    ## OSM
    b0 = folium.TileLayer("OpenStreetMap", name="Open Street Map", attr="OSM")
    b0.add_to(m)

    ## Mapbox
    mapbox_api = st.secrets["mapbox_token"]
    mapbox_url = f"https://api.mapbox.com/styles/v1/mapbox/dark-v11/tiles/{{z}}/{{x}}/{{y}}?access_token={mapbox_api}"

    b1 = folium.TileLayer(tiles=mapbox_url, name="MapBox Dark", attr="MapBox", overlay=False, control=True, min_zoom=1, max_zoom=20)
    b1.add_to(m)


    # folium useeful plugins
    ## fullscreen
    folium.plugins.Fullscreen(position="bottomright", title="Full Screen", title_cancel="Exit", force_separate_button=True).add_to(m)

    ## layer control
    folium.LayerControl(collapsed=True).add_to(m)

    # map display
    st_folium(m, use_container_width=True, height="700")


if __name__ == "__main__":
    main()