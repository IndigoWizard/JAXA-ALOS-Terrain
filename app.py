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
from branca.element import Template, MacroElement, Figure, Element
from folium.utilities import escape_backticks

st.set_page_config(
    page_title="Terrain Viewer",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Interactive Terrain WebGIS app using JAXA ALOS World 3D Digital Surface Model Data. Check the project's [GitHub repo](https://github.com/IndigoWizard/JAXA-ALOS-Terrain) or email me at [my Email](mailto:tro56f5j6@mozmail.com) if need be.",
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
        # will be used to display user's area of interest as its own folium layer
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

        # returning geometry list for earth engine geometry object ingestion
        # returning geojson aoi layer for folium geojson aoi visualization
        # returning None for no geometries
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


# add uploaded geojson as its own separate layer
def add_geojson_layers(map_object, geojson_layers):

    # creating a feature group to cummulate multiple geojson
    aoi_group = folium.FeatureGroup(
        name="Area of Interest",
        overlay=True,
        control=True,
    )

    # generating geojson layer with custom styling
    for geojson in geojson_layers:

        folium.GeoJson(
            data=geojson,
            style_function=lambda x: {
                "color": "#dc005db2",
                "weight": 2,
                "fill": False,
            },
        ).add_to(aoi_group)

    aoi_group.add_to(map_object)

def main():

    # inti gee
    ee_authenticate()

    # session states
    st.session_state.setdefault("ee_ready", False)
    st.session_state.setdefault("geometry_aoi", None)

    with st.sidebar:
        st.title("Terrain Viewer")
        st.markdown("---")
        st.markdown("### Contact:")
        contact_socials = """
            <style>
                .social-links {
                    display: flex;
                    flex-direction: row;
                    justify-content: start;
                    gap: 1rem;
                    margin-top: 0.5rem;
                }
                .social-links a {
                    transition: color 0.2s;
                }
                .social-links svg {
                    width: 1.6rem;
                    height: 1.6rem;
                }
            </style>
            <div class="social-links">
                <a href="https://lnkd.in/dT3VAPAB" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" xml:space="preserve"><path d="M22.262 0H1.809C.831 0 0 .774 0 1.727v20.545C0 23.226.545 24 1.523 24h20.453c.979 0 2.024-.774 2.024-1.728V1.727A1.72 1.72 0 0 0 22.262 0" style="fill:none"/><path d="M22.262 0H1.809C.831 0 0 .774 0 1.727v20.545C0 23.226.545 24 1.523 24h20.453c.979 0 2.024-.774 2.024-1.728V1.727A1.72 1.72 0 0 0 22.262 0M9.143 9.143h3.231v1.647h.035C12.902 9.902 14.357 9 16.155 9c3.453 0 4.416 1.833 4.416 5.229v6.343h-3.429v-5.718c0-1.52-.607-2.854-2.026-2.854-1.723 0-2.545 1.167-2.545 3.082v5.489H9.143zM3.429 20.571h3.429V9.143H3.429zM7.286 5.143a2.142 2.142 0 1 1-4.285.001 2.142 2.142 0 0 1 4.285-.001" style="fill-rule:evenodd;clip-rule:evenodd;fill:#0a66c2"/></svg>
                </a>
                <a href="https://medium.com/@Indigo.Wizard" target="_blank" rel="noopener noreferrer" aria-label="Medium">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" xml:space="preserve"><path d="M2.667 23.999h18.666A2.667 2.667 0 0 0 24 21.332V2.667A2.667 2.667 0 0 0 21.333 0H2.667A2.667 2.667 0 0 0 0 2.667v18.666a2.665 2.665 0 0 0 2.667 2.666" style="fill-rule:evenodd;clip-rule:evenodd"/><path d="M5.859 8.109c0-.188-.094-.422-.234-.516L4.172 5.812v-.281h4.594l3.516 7.781 3.141-7.781h4.359v.281l-1.266 1.219c-.094.047-.141.188-.141.328v8.906c0 .141.047.281.141.375l1.266 1.172v.281h-6.235v-.281l1.266-1.219c.141-.141.141-.188.141-.375V9.047l-3.563 9h-.469l-4.125-9v6.047c-.047.234.047.516.234.703l1.641 2.016v.234H3.984v-.234l1.641-2.016c.188-.188.281-.469.234-.703z" style="fill-rule:evenodd;clip-rule:evenodd;fill:#fff"/></svg>
                </a>
                <a href="https://github.com/IndigoWizard/JAXA-ALOS-Terrain" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="23.5" viewBox="0 0 24 23.5" xml:space="preserve"><path d="M10.148 16.985c-3.094-.375-5.273-2.6-5.273-5.482 0-1.171.422-2.436 1.125-3.28-.305-.773-.258-2.413.094-3.092.937-.117 2.203.375 2.953 1.054.891-.281 1.828-.422 2.977-.422s2.086.141 2.93.398c.727-.656 2.016-1.148 2.953-1.031.328.633.375 2.272.07 3.069.75.89 1.148 2.085 1.148 3.303 0 2.882-2.18 5.06-5.32 5.459.797.515 1.336 1.64 1.336 2.928v2.436c0 .703.586 1.101 1.289.82C20.672 21.53 24 17.289 24 12.042 24 5.412 18.609 0 11.977 0S0 5.412 0 12.042A11.82 11.82 0 0 0 7.758 23.17c.633.234 1.242-.188 1.242-.82v-1.874c-.328.141-.75.234-1.125.234-1.547 0-2.461-.843-3.117-2.413-.258-.633-.539-1.008-1.078-1.078-.281-.023-.375-.141-.375-.281 0-.281.469-.492.938-.492.68 0 1.266.422 1.875 1.289.469.679.961.984 1.547.984s.961-.211 1.5-.75c.398-.399.702-.75.983-.984"/></svg>
                </a>
                <a href="mailto:tro56f5j6@mozmail.com" target="_blank" rel="noopener noreferrer" aria-label="Email">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="21" viewBox="0 0 24 21" xml:space="preserve"><path d="M2.653 0h18.695C23.111 0 24 .731 24 2.217v16.567C24 20.257 23.111 21 21.347 21H2.653C.889 21 0 20.257 0 18.783V2.217C0 .731.889 0 2.653 0m8.705 13.12a1 1 0 0 0 1.269.001l8.875-7.286c.339-.282.606-.932.184-1.511-.409-.579-1.157-.593-1.651-.24l-7.417 5.948a1 1 0 0 1-1.252-.001L3.965 4.084c-.494-.353-1.242-.339-1.651.24-.424.578-.155 1.228.183 1.51z" style="fill:#969baa"/></svg>
                </a>
                <a href="https://indigowizard.github.io/portfolio/" target="_blank" rel="noopener noreferrer" aria-label="Website">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" xml:space="preserve"><path d="M14.667 2.667a1.333 1.333 0 0 1 0-2.667h8C23.403 0 24 .597 24 1.333v8a1.333 1.333 0 0 1-2.666 0v-4.8l-8.915 8.97c-.59.441-1.331.251-1.753-.17-.402-.402-.468-1.223-.114-1.697l8.915-8.97zM0 5.333a2.667 2.667 0 0 1 2.667-2.667h6.667a1.334 1.334 0 0 1-.001 2.667H2.667v16h16v-6.667a1.333 1.333 0 0 1 2.666 0v6.667A2.667 2.667 0 0 1 18.666 24h-16A2.667 2.667 0 0 1 0 21.333z" style="fill:#969baa"/></svg>
                </a>
            </div>
        """
        st.markdown(contact_socials, unsafe_allow_html=True)

    st.title("Terrain Viewer")
    st.markdown("View terrain surface through JAXA's ALOS World 3D Map high-resolution Digital Surface Model data on the fly!")


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


            # custom attribution textbox
            class MyCustomAttribution(MacroElement):
                _template = Template("""
                    {% macro script(this, kwargs) %}

                    L.Control.MyCustomAttribution = L.Control.extend({
                        onAdd: function(map) {
                            let div = L.DomUtil.create('div', 'map-credit-box');
                            div.innerHTML = `{{ this.injectedHtml }}`;
                            L.DomEvent.disableClickPropagation(div);
                            return div;
                        }
                    });

                    L.control.myCustomAttribution = function(opts) {
                        return new L.Control.MyCustomAttribution(opts);
                    };

                    L.control.myCustomAttribution({
                        position: "{{ this.position }}"
                    }).addTo({{ this._parent.get_name() }});

                    {% endmacro %}
                """)

                def __init__(self, injectedHtml, position="bottomright"):
                    super().__init__()
                    self.injectedHtml = escape_backticks(injectedHtml)
                    self.position = position

            credit_html = """
                <style>
                    .map-credit-box.leaflet-control {
                        bottom: -10px;
                        right: -10px;
                        z-index: 9999;
                        background: rgba(255, 255, 255, 0.85);
                        color: #333;
                        padding: 2px 2px;
                        border-radius: 4px;
                        font-size: 0.9rem;
                        font-weight: 600;
                        font-family: "Segoe UI", "Noto Sans", sans-serif;
                        line-height: 1.2;
                        max-width: 90vw;
                        white-space: normal;
                    }

                    .map-credit-box.leaflet-control a {
                        color: #0078A8;
                        text-decoration: none;
                    }
                    
                    .leaflet-bottom .leaflet-control-scale{
                        font-weight: 600;
                        font-family: "Source Sans Pro", sans-serif;
                        margin-bottom: 0;
                    }

                    /* Mobile adjustments */

                    @media (max-width: 825px) {
                        .leaflet-bottom .leaflet-control-scale{
                            margin-bottom: 25px;
                        }
                    }
                    @media (max-width: 815px) {
                        .map-credit-box.leaflet-control {
                            max-width: 100%;
                            width: 100%;
                        }
                        .leaflet-bottom .leaflet-control-scale{
                            margin-bottom: 45px;
                        }
                    }
                    @media (max-width: 610px) {
                        .map-credit-box.leaflet-control {
                            font-size: 0.8rem;
                            max-width: 100%;
                            text-align: center;
                        }
                        .leaflet-bottom .leaflet-control-scale{
                            margin-bottom: 45px;
                        }
                    }
                    @media (max-width: 550px) {
                        .map-credit-box.leaflet-control {
                            width: 100%;
                            text-align: center;
                        }
                        .leaflet-bottom .leaflet-control-scale{
                            margin-bottom: 45px;
                        }
                    }
                </style>

                🇵🇸 Terrain Viewer by <a href="https://github.com/IndigoWizard/JAXA-ALOS-Terrain" target="_blank" rel="noopener noreferrer">@IndigoWizard</a> | Map Data: <a href="https://leafletjs.com/" target="_blank" rel="noopener noreferrer">Leaflet</a>, <a href="https://www.openstreetmap.org/about" target="_blank" rel="noopener noreferrer">OSM</a>, <a href="https://www.mapbox.com/about/maps" target="_blank" rel="noopener noreferrer">Mapbox</a>, <a href="https://www.eorc.jaxa.jp/ALOS/jp/dataset/aw3d_j.htm" target="_blank" rel="noopener noreferrer">JAXA</a>, <a href="https://earthengine.google.com/" target="_blank" rel="noopener noreferrer">EarthEngine</a>
            """

            # add attribution control
            MyCustomAttribution(credit_html, position="bottomright").add_to(m)

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
                    'opacity': 0.8
                }

                # Elevation (colorized DSM height for better visual)
                elevation = dsm_image
                elevation_vis = {
                    'min': DSM_MIN,
                    'max': DSM_MAX,
                    'palette': ['#053061', '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7', '#fddbc7', '#f4a582', '#d6604d', '#b2182b', '#67001f'],
                    'opacity': 0.8
                }

                # Hillshade
                hillshade = ee.Terrain.hillshade(elevation)
                hillshade_vis = {
                    'min': 0,
                    'max': 500,
                    'palette': ['#000000', '#ffffff'],
                    'opacity': 0.8
                }

                # aspect
                aspect = ee.Terrain.aspect(elevation)
                aspect_vis = {
                    'min': 0.0,
                    'max': 359.99,
                    'opacity': 0.8,
                }

                # Slopes
                slopes = ee.Terrain.slope(elevation)
                slopes_vis = {
                    'min': 0,
                    'max': 90,
                    'palette': ['#6f0a91','#43d1bf','#86ea50','#ccec5a'],
                    'opacity': 0.8
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
                m.add_ee_layer(aspect, aspect_vis, 'Aspect')
                m.add_ee_layer(slopes, slopes_vis, 'Slopes')
                m.add_ee_layer(contours, contours_vis, 'Contour lines')
                add_geojson_layers(m, geojson_aoi_layer)

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

    st.divider()
    
    with st.container():
        legend_html = """
            <style>
            /*---- Map Key ----*/
            .mapkey {
                font-size: 1.75rem;
                font-weight: 600;
                padding-block: calc(-1px + 1rem);
            }
            .maplegendcontainer {
                display: flex;
                flex-direction: row;
                gap: 1.25rem;
            }
            .maplegend {
                padding: 12px;
                border-radius: 4px;
                width: fit-content;
            }
            .legendtitle {
                margin: 0 0 10px 0;
                font-size: 1.2rem;
                font-weight: 600;
            }
            .legendcontainer {
                display: flex;
                gap: 10px;
                height: 150px;
            }
            .colorbar {
                width: 1.6rem;
                height: 100%;
                border-radius: 2px;
            }
            #bar_elevation  {
                background: linear-gradient(to top, #053061, #2166ac, #4393c3, #92c5de, #d1e5f0, #f7f7f7, #fddbc7, #f4a582, #d6604d, #b2182b, #67001f);
            }
            #bar_contourlines  {
                background: linear-gradient(to top, #6f0a91, #43d1bf, #86ea50, #ccec5a);
            }
            .labels {
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                font-size: 12px;
                line-height: 1;
            }
            .maxlabel {
                font-size: 1rem;
                font-weight: 500;
                line-height: 1;
            }
            .minlabel {
                font-size: 1rem;
                font-weight: 500;
                line-height: 1;
            }
            </style>
            <div class="mapkeycontainer">
                <div class="mapkey" id="mapkey">Map Key</div>
                <div class="maplegendcontainer">
                    <div class="maplegend">
                        <div class="legendtitle">Elevation</div>
                        <div class="legendcontainer">
                            <div class="colorbar" id="bar_elevation"></div>
                            <div class="labels">
                                <span class="maxlabel">Max: 8768 m</span>
                                <span class="minlabel">Min: -433 m</span>
                            </div>
                        </div>
                    </div>
                    <div class="maplegend">
                        <div class="legendtitle">Slopes</div>
                        <div class="legendcontainer">
                            <div class="colorbar" id="bar_contourlines"></div>
                            <div class="labels">
                                <span class="maxlabel">90°</span>
                                <span class="minlabel">0°</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)

    st.divider()
    
    with st.container():
        st.subheader("Layers guide")
        st.markdown(
            """
            The following is a guide on the map layers available in this app for better understanding their use and context:

            - **DSM:** A Digital Surface Model that displays terrain elevation information that includes vegetation and buildings.
            - **Elevation:** The colorized visualization of the DSM to improve terrain interpretation.
            - **Hillshade:** Artificial illumination of the terrain to emphasize relief. It is useful for visually identifying **ridges**, **valleys** and **landforms**.
            - **Aspect:** Direction each slope faces, measured clockwise starting from the north. It can be useful for; **solar exposure**, **watershed analysis** and *hydrological modeling**.
            - **Slopes:** Terrain steepness in degrees. Useful for; **engineering**, **erosion**, **landslide susceptibility**, **animal habitat analysis** (e.g: cougars... etc).
            - **Contours:** Isolines connecting equal elevations at certain intervals. Useful for; **topographic interpretation**, **terrain planning** and **map reading**.

            ##### Notes
            - Elevation values represent a Digital Surface Model (DSM), not bare-earth terrain.
            - Buildings and vegetation are included in elevation values.
            - Only land areas covered by the ALOS World 3D dataset are available.
            """
        )

    st.divider()
    
    with st.container():
        st.subheader("Data")
        st.markdown(
            """
            Data used in this project is from JAXA ALOS World 3D (AW3D30). It is a 30m high resolution Digital Surface Model data.
            
            - **Provider:** [Japan Aerospace Exploration Agency (JAXA)](https://www.jaxa.jp/)
            - **Mission:** [Advanced Land Observing Satellite (ALOS)](https://earth.jaxa.jp/ja/research/projects/alos/index.html)
            - **Dataset:** [ALOS World 3D (AW3D30)](https://www.eorc.jaxa.jp/ALOS/jp/dataset/aw3d_j.htm)
            - **Version:** 4.1
            - **Resolution:** 30 m
            - **Type:** Digital Surface Model (DSM)
            - **Platform:** Google Earth Engine
            
            """
        )


if __name__ == "__main__":
    main()