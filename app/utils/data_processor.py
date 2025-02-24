import logging
import configparser
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol
import requests
import os
import numpy as np
from shapely.geometry import MultiLineString, LineString
from app.reference_layers import reference_layers

log = logging.getLogger(__name__)

# config = configparser.ConfigParser()
# config.read("config.ini")
# OPEN_TOPO_API_KEY = config.get("open-topo", "API_KEY", fallback=None)
OPEN_TOPO_API_KEY = os.getenv("OPEN_TOPO_API_KEY")

class DataProcessor:
    def __init__(self, final_route_path):
        self.final_route_path = final_route_path
        self.elevation_url = reference_layers[0]["url"]

    def process_route(self):
        """filter trailheads, extract elevation, calculate slope, and classify difficulty."""
        log.info("🔄 Starting geospatial enhancements on final route...")

        self.filter_trailheads()

        elevation_tif = self.query_elevation_tif()
        if not elevation_tif:
            log.error("❌ Failed to download elevation raster. Cannot proceed with processing.")
            return None

        elevation_data = self.extract_elevation_from_raster()
        if elevation_data is None:
            log.error("❌ Elevation extraction failed.")
            return None

        slope_data = self.calculate_slope(elevation_data)

        self.classify_difficulty(slope_data)

        log.info("✅ Route processing complete.")
        return self.final_route_path

    def compute_bbox(self, final_gdf):
        all_coords = []

        for geom in final_gdf.geometry:
            if geom.geom_type == "LineString":
                all_coords.extend(geom.coords)
            elif geom.geom_type == "MultiLineString":
                for line in geom.geoms:
                    all_coords.extend(line.coords)

        if not all_coords:
            log.error("❌ No valid coordinates found in route geometry.")
            return None

        lons, lats = zip(*all_coords)
        return {
            "north": max(lats),
            "south": min(lats),
            "east": max(lons),
            "west": min(lons)
        }

    def query_elevation_tif(self):
        """query open topo for raster based on the route bounding box."""
        final_gdf = gpd.read_file(self.final_route_path)
        if final_gdf.empty:
            log.error("❌ Final trip route is empty. Cannot query DEM.")
            return None

        bbox = self.compute_bbox(final_gdf)
        if not bbox:
            log.error("❌ Could not compute bounding box. Aborting DEM request.")
            return None

        params = {
            "demtype": "SRTMGL3",
            "south": bbox["south"],
            "north": bbox["north"],
            "west": bbox["west"],
            "east": bbox["east"],
            "outputFormat": "GTiff",
            "API_Key": OPEN_TOPO_API_KEY
        }

        log.info(f"📡 Requesting DEM for bbox: {bbox}")

        try:
            response = requests.get(self.elevation_url, params=params)
            response.raise_for_status()

            if response.headers.get("content-type") == "application/octet-stream":
                log.info("received DEM GeoTIFF file for requested area.")
                with open("/tmp/data/processed/elevation.tif", "wb") as f:
                    f.write(response.content)
                return "/tmp/data/processed/elevation.tif"
            else:
                log.warning(f"Unexpected response format: {response.headers.get('content-type')}")
                return None

        except requests.exceptions.RequestException as req_err:
            log.error(f"❌ API Request Error: {req_err}")
            return None


    def extract_elevation_from_raster(self):
        """extract elevation values from elevation.tif for each vertex along the final route."""
        raster_path = "/tmp/data/processed/elevation.tif"
        log.info("🔄 Extracting elevation values from local raster...")

        final_gdf = gpd.read_file(self.final_route_path)
        if final_gdf.empty:
            log.error("❌ Final trip route is empty. Cannot extract elevation.")
            return None

        elevation_data = []

        try:
            with rasterio.open(raster_path) as src:
                affine_transform = src.transform
                height, width = src.shape #raster dimensions

                for index, row in final_gdf.iterrows():
                    geom = row.geometry
                    coords = [coord for line in geom.geoms for coord in line.coords] if geom.geom_type == "MultiLineString" else list(geom.coords)
                    
                    segment_elevations = []
                    for lon, lat in coords:
                        row_idx, col_idx = rowcol(affine_transform, lon, lat)

                        if not (0 <= row_idx < height and 0 <= col_idx < width):
                            #skipping points outside of bounds of tif/raster
                            continue 

                        elevation = src.read(1)[row_idx, col_idx]
                        segment_elevations.append(elevation)

                    elevation_data.append(segment_elevations)

            log.info("✅ Elevation extraction from raster complete.")
            return elevation_data

        except Exception as e:
            log.error(f"❌ ERROR extracting elevation from raster: {str(e)}")
            return None

    def calculate_slope(self, elevation_data, horizontal_resolution=30):
        """calculates slope between consecutive points along each segment.
        """
        log.info("🔄 Calculating slope for each route segment...")

        slopes = []
        for segment in elevation_data:
            segment_slopes = []
            
            for i in range(1, len(segment)):
                rise = segment[i] - segment[i - 1] # elevation delta in meters
                run = horizontal_resolution #cell size

                slope = (rise / run) * 100
                segment_slopes.append(abs(slope)) #best approach for dealing with negative slope?
            
            slopes.append(np.mean(segment_slopes) if segment_slopes else 0)

        log.info(f"✅ Slope calculation complete. Example values: {slopes[:5]}")
        return slopes

    def classify_difficulty(self, slopes):
        """classify route difficulty based on slope severity."""
        final_gdf = gpd.read_file(self.final_route_path)

        def categorize_slope(slope):
            if slope < 5:
                return "Easy"
            elif slope < 10:
                return "Moderate"
            else:
                return "Difficult"

        log.info("🔄 Assigning difficulty levels based on slope values...")
        final_gdf["Slope"] = slopes
        final_gdf["Difficulty"] = final_gdf["Slope"].apply(categorize_slope)

        final_gdf.to_file(self.final_route_path, driver="GeoJSON")

    def filter_trailheads(self, buffer_distance=0.001):  # dfault buffer ~100m (0.001 degrees)
        """filter trailheads to only those that intersect or are near the final selected route."""
        log.info("🔄 Filtering trailheads that intersect or are near the final trip route...")

        final_route_path = self.final_route_path
        trailheads_path = "/tmp/data/processed/fetched_trailheads.geojson"
        filtered_trailheads_path = "/tmp/data/processed/filtered_trailheads.geojson"

        if not os.path.exists(final_route_path) or not os.path.exists(trailheads_path):
            log.error("❌ Final route or trailheads file is missing. Cannot filter trailheads.")
            return None

        final_gdf = gpd.read_file(final_route_path)
        trailheads_gdf = gpd.read_file(trailheads_path)

        if final_gdf.empty or trailheads_gdf.empty:
            log.error("❌ Final route or trailheads dataset is empty. No filtering applied.")
            return None

        final_gdf["geometry"] = final_gdf.geometry.buffer(buffer_distance)

        #spat join to filter trailheads within buffer distance
        filtered_trailheads = gpd.sjoin(trailheads_gdf, final_gdf, predicate="intersects").drop(columns=["index_right"])

        if filtered_trailheads.empty:
            log.warning("no trailheads found within buffer distance of the final route.")
        else:
            filtered_trailheads.to_file(filtered_trailheads_path, driver="GeoJSON")
            log.info(f"saved {len(filtered_trailheads)} filtered trailheads to {filtered_trailheads_path}")

        return filtered_trailheads



