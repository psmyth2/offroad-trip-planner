import os
import logging
import geopandas as gpd
import json
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.geometry.filters import intersects
from app.reference_layers import trails_roads
from app.reference_layers import reference_layers

class DataFetcher:
    def __init__(self):
        """Initialize DataFetcher with GIS connection and output paths."""
        self.logger = logging.getLogger(__name__)
        self.gis = GIS()
        self.trails = trails_roads
        self.reference_layers = reference_layers
        self.data_raw_path = "data/raw"
        os.makedirs(self.data_raw_path, exist_ok=True)

    def process_selected_trails(self, trail_list):
        print(trail_list)

    def fetch_feature_layer(self, layer, bbox):
        """Fetches data from an Esri Feature Layer based on user BBOX."""
        feature_layer = FeatureLayer(layer['url'], self.gis)
        wkid = 4326  # Ensure data is in WGS84

        try:
            # Convert BBOX to Esri's dictionary format
            bbox_dict = {
                "xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3],
                "spatialReference": {"wkid": wkid}
            }
            
            query_filter = intersects(bbox_dict, sr=wkid)
            features = feature_layer.query(geometry_filter=query_filter, out_sr=wkid, out_fields=layer['fields'])

            # Convert to GeoDataFrame
            gdf = self.gdf_from_feature_layer(features, wkid)

            if gdf.empty:
                self.logger.warning(f"No data found for {layer['name']}")
                return None

            # Save raw GeoJSON
            gdf.to_file(f"{self.data_raw_path}/{layer['name']}.geojson", driver="GeoJSON")
            return gdf

        except Exception as e:
            self.logger.error(f"Error fetching {layer['name']}: {e}")
            return None

    def gdf_from_feature_layer(self, feature_layer, wkid=4326):
        """Converts Esri FeatureLayer response to GeoDataFrame with correct projection."""
        if feature_layer.features:
            geojson = feature_layer.to_geojson
            gdf = gpd.read_file(geojson)

            # Explicitly set geometry column if needed
            if "geometry" not in gdf.columns:
                for col in gdf.columns:
                    if gdf[col].dtype == "geometry":
                        gdf = gdf.set_geometry(col)
                        break

            # Ensure CRS is set correctly
            if gdf.crs is None or gdf.crs != f"EPSG:{wkid}":
                gdf = gdf.set_crs(epsg=wkid)

            return gdf

        return gpd.GeoDataFrame()

    def fetch_all_trails(self, bbox):
        all_data = []

        for layer in self.trails:
            self.logger.info(f"Fetching {layer['full_name']}...")
            gdf = self.fetch_feature_layer(layer, bbox)
            if gdf is not None:
                all_data.append(gdf)

        return all_data
    
    def _correct_multipolygon_nesting_as_string(self, geojson_data):
        geojson_data = json.loads(geojson_data)
        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'MultiPolygon':
                corrected_coordinates = [feature['geometry']['coordinates']]
                feature['geometry']['coordinates'] = corrected_coordinates

        return json.dumps(geojson_data, indent=4)
