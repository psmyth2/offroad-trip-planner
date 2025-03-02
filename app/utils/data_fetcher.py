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
        self.logger = logging.getLogger(__name__)
        self.gis = GIS()
        self.trails = trails_roads
        self.reference_layers = reference_layers
        self.data_raw_path = "/tmp/data/raw"
        # self.data_raw_path = "tmp/data/raw"
        # os.makedirs(self.data_raw_path, exist_ok=True)

    def fetch_feature_layer(self, layer, bbox):
        """get data from an esri layers based on user bbox. request output in 4326"""
        feature_layer = FeatureLayer(layer['url'], self.gis)
        wkid = 4326

        try:
            bbox_dict = {
                "xmin": bbox[0], "ymin": bbox[1], "xmax": bbox[2], "ymax": bbox[3],
                "spatialReference": {"wkid": wkid}
            }
            
            query_filter = intersects(bbox_dict, sr=wkid)
            features = feature_layer.query(geometry_filter=query_filter, out_sr=wkid, out_fields=layer['fields'])

            #convert to gdf
            gdf = self.gdf_from_feature_layer(features, wkid)

            if gdf.empty:
                self.logger.warning(f"No data found for {layer['name']}")
                return None

            #save geojson
            gdf.to_file(f"{self.data_raw_path}/{layer['name']}.geojson", driver="GeoJSON")
            return gdf

        except Exception as e:
            self.logger.error(f"Error fetching {layer['name']}: {e}")
            return None

    def gdf_from_feature_layer(self, feature_layer, wkid=4326):
        """converts esri flayer response to gdf in 4326"""
        if feature_layer.features:
            geojson = feature_layer.to_geojson
            gdf = gpd.read_file(geojson)

            if "geometry" not in gdf.columns:
                for col in gdf.columns:
                    if gdf[col].dtype == "geometry":
                        gdf = gdf.set_geometry(col)
                        break

            if gdf.crs is None or gdf.crs != f"EPSG:{wkid}":
                gdf = gdf.set_crs(epsg=wkid)

            return gdf

        return gpd.GeoDataFrame()

    def fetch_all_trails(self, bbox):
        all_data = []

        for layer in self.trails:
            self.logger.info(f"Fetching {layer['name']}...")
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
