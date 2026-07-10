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

# Error dialog box
@st.dialog("Error Report:")
def show_error_dialog(messages):
    st.error(messages)


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


# a function to access and filter a GEE image collection
def satCollection(aoi):
    alos_image = None

    try:
        collection = (
            ee.ImageCollection("JAXA/ALOS/AW3D30/V4_1")
            .filterBounds(aoi)
            .select("DSM")
        )
        
        # geting the collection's tile projection
        alos_projection = collection.first().select("DSM").projection()

        # mosaicing, reprojecting and clipping the image collection as an image
        alos_image = (collection.mosaic().setDefaultProjection(alos_projection).clip(aoi))

        return alos_image, None
    except Exception as e:
        return alos_image, f"Earth Engine encountered an error while building JAXA ALOS W3D Image: \n {str(e)}"

# File Parser: GeoJSON (.geojson, .json)
def parse_geojson(upload_file):
    try:
        bytes_data = upload_file.read()
        try:
            geojson_data = json.loads(bytes_data)
        except json.JSONDecodeError:
            return [], "Invalid GeoJSON file. JSON could not be decoded."

        # keeping a copy of the original uploaded file for layer display
        geojson_aoi_layer = geojson_data

        # detect the correct container of features
        if 'features' in geojson_data and isinstance(geojson_data['features'], list):
            features = geojson_data['features']
        elif 'geometries' in geojson_data and isinstance(geojson_data['geometries'], list):
            # Handle GeometryCollection-style structures
            features = [{'geometry': geo} for geo in geojson_data['geometries']]
        else:
            # skip unsupported or invalid GeoJSON
            return [], "Unsupported GeoJSON structure. Must containe a 'features' or 'geometries' field."

        geometry_list = []

        # build Earth Engine geometries
        for feature in features:
            if 'geometry' in feature and 'coordinates' in feature['geometry']:
                coordinates = feature['geometry']['coordinates']
                geometry_type = feature['geometry']['type']

                # Create Polygon or MultiPolygon geometry
                geometry = (
                    ee.Geometry.Polygon(coordinates)
                    if geometry_type == 'Polygon'
                    else ee.Geometry.MultiPolygon(coordinates)
                )

                geometry_list.append(geometry)

        if not geometry_list:
            return [], "No valide geometries in the GeoJSON file. Ensure it contains Polygon or MultiPolygon features."
        return geometry_list, geojson_aoi_layer, None
    except Exception as e:
        return [], f"Error processing GeoJSON file: {str(e)} Please verify the file is valid."


# Upload Function
last_uploaded_centroid = None
def upload_files_proc(upload_files):
    # A global variable to track the latest geojson uploaded
    global last_uploaded_centroid
    # Setting up a variable that takes all polygons/geometries within the same/different geojson
    geometry_aoi_list = []
    geojson_aoi_layer = []
    # Variable to store all error messages from various parsers
    error_messages = []
    
    for upload_file in upload_files:
        # Get the file name for extension detection
        file_name = getattr(upload_file, 'name').lower()
        # reset file pointer if it was read before
        upload_file.seek(0)

        # File Parser: GeoJSON files
        if file_name.endswith(".geojson") or file_name.endswith(".json"):
            geojson_geoms, geojson_layer, error = parse_geojson(upload_file)
            if error:
                error_messages.append(f"→ {file_name}: \n > {error}")
            geometry_aoi_list.extend(geojson_geoms)
            geojson_aoi_layer.append(geojson_layer)
            if geojson_geoms:
                last_uploaded_centroid = geojson_geoms[0].centroid(maxError=1).getInfo()['coordinates']
            continue
    
    if error_messages:
        show_error_dialog("\n\n---\n\n".join(error_messages))
    # assembling aoi geometries
    if geometry_aoi_list:
        geometry_aoi = ee.Geometry.MultiPolygon(geometry_aoi_list)
    else:
        geometry_aoi = ee.Geometry.Point([14, 37.5])

    return geometry_aoi, geojson_aoi_layer


def main():

    # inti gee
    ee_authenticate()

    # session states
    st.session_state.setdefault("ee_ready", False)
    st.session_state.setdefault("geometry_aoi", None)

    st.title("Terrain Viewer")
    st.markdown("View Digital Surface Model terrain through JAXA's ALOS World 3D Map high resolution data on the fly!")


    with st.form("terrain map"):

        c_left, c_right = st.columns([3, 1])
        ee_errors = []
        ee_ready = True
        DSM_MIN = -433
        DSM_MAX = 8768

        with c_right:

            st.info("Upload Area of Interest file:")
            # file upload
            upload_files = st.file_uploader("Create a GeoJSON file at: [geojsion.io](https://geojson.io/)", accept_multiple_files=True)
            # calling upload function
            geometry_aoi, geojson_aoi_layer = upload_files_proc(upload_files)
        
        with c_left:
            global last_uploaded_centroid

            if last_uploaded_centroid is not None:
                latitude = last_uploaded_centroid[1]
                longitude = last_uploaded_centroid[0]

                # main map
                m = folium.Map(location=[latitude, longitude], tiles=None, zoom_start=11, control=True, control_scale=True, attributionControl=0)
            else:
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

            # geoprocessing - start

            # defining an image collection
            alosw3d_jaxa, alos_image_error = satCollection(geometry_aoi)


            if alos_image_error:
                # collecting the error message in the error list
                ee_errors.append(f"JAXA ALOS Collection Error: \n {alos_image_error}")
                # ee processing workflow is not available. Try again.
                ee_ready = False

            if ee_ready:
                # start of geoprocessing

                # DSM band from alos collection/image
                ## masking the dsm image to show only land area
                dsm_image = alosw3d_jaxa.updateMask(alosw3d_jaxa.gt(0))
                # dsm layer visual parameters
                dsm_vis = {
                    'min': DSM_MIN,
                    'max': DSM_MAX,
                    'opacity': 0.9
                }

                # Elevation (colorized DSM height for better visual)
                elevation = dsm_image
                elevation_vis = {
                    'min': DSM_MIN,
                    'max': DSM_MAX,
                    'palette': ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'],
                    'opacity': 0.9
                }

                # Hillshade
                hillshade = ee.Terrain.hillshade(elevation)
                hillshade_vis = {
                    'min': 0,
                    'max': 500,
                    'palette': ['#000000', '#ffffff'],
                    'opacity': 0.9
                }

                # Slopes
                slopes = ee.Terrain.slope(elevation)
                slopes_vis = {
                    'min': 0,
                    'max': 90,
                    'palette': ['#6f0a91','#43d1bf','#86ea50','#ccec5a'],
                    'opacity': 0.9
                }

                # contour lines (isolines)
                contours = geemap.create_contours(elevation, min_value=DSM_MIN, max_value=DSM_MAX, interval=20, region=geometry_aoi)
                contours_vis = {
                    'min': DSM_MIN,
                    'max': DSM_MAX,
                    'palette': ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f']
                }

            # geoprocessing - end

            if ee_ready:
                st.session_state.ee_ready = True
                st.session_state.geometry_aoi = geometry_aoi

                ####################
                # Layers display

                m.add_ee_layer(dsm_image, dsm_vis, 'JAXA ALOS - DSM')
                m.add_ee_layer(elevation, elevation_vis, 'Elevation')
                m.add_ee_layer(hillshade, hillshade_vis, 'Hillshade')
                m.add_ee_layer(slopes, slopes_vis, 'Slopes')
                m.add_ee_layer(contours, contours_vis, 'Contour lines')

                ####################

            else:
                st.session_state.ee_ready = False
                st.toast("No satellite imagery available for the selected parameters.")


            # folium useeful plugins
            ## fullscreen
            folium.plugins.Fullscreen(position="bottomright", title="Full Screen", title_cancel="Exit", force_separate_button=True).add_to(m)

            ## layer control
            folium.LayerControl(collapsed=True).add_to(m)

        # form's submit button
        submitted = c_right.form_submit_button("Generate Map")
        
        if submitted:
            with c_left:
                # map display with the calculated layers
                st_folium(m, use_container_width=True, height="600")
        else:
            with c_left:
                # map display by default
                st_folium(m, use_container_width=True, height="600")



if __name__ == "__main__":
    main()