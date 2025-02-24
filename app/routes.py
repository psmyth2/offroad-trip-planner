import logging
import os
import json
import threading
import time
import geopandas as gpd
import configparser
import pandas as pd
import requests
import select
from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, Response, stream_with_context
)
from app.utils.data_fetcher import DataFetcher
from app.utils.data_processor import DataProcessor
from app.reference_layers import reference_layers

routes = Blueprint("routes", __name__)
log = logging.getLogger(__name__)

# config = configparser.ConfigParser()
# config.read("config.ini")
# MAPBOX_API_KEY = config.get("mapbox", "API_KEY")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

data_fetcher = DataFetcher()

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
os.makedirs(LOG_DIR, exist_ok=True)

processing_status = {}

### ----------------------------------------
### Helper Functions -> Perform Processing
### ----------------------------------------

def perform_processing(selected_segments, session_id):
    """Runs trip enrichment and logs the process in real-time."""
    log.info(f"🔄 Processing started for session {session_id}...")
    processing_status[session_id] = False

    try:
        trails_path = "/tmp/data/processed/fetched_trails.geojson"
        roads_path = "/tmp/data/processed/roads.geojson"

        log.info("Loading trail and road datasets...")
        trails_gdf = gpd.read_file(trails_path) if os.path.exists(trails_path) else gpd.GeoDataFrame()
        roads_gdf = gpd.read_file(roads_path) if os.path.exists(roads_path) else gpd.GeoDataFrame()

        log.info(f"loaded {len(trails_gdf)} trails and {len(roads_gdf)} roads.")

        id_field = None
        for df in [trails_gdf, roads_gdf]:
            if not df.empty:
                possible_ids = [col for col in df.columns if col.upper() in ["ID", "OBJECTID"]]
                if possible_ids:
                    id_field = possible_ids[0]
                    break

        if not id_field:
            log.error("no valid ID field found in dataset.")
            return

        selected_trails_gdf = trails_gdf[trails_gdf[id_field].astype(str).isin(map(str, selected_segments))] if not trails_gdf.empty else gpd.GeoDataFrame()
        selected_roads_gdf = roads_gdf[roads_gdf[id_field].astype(str).isin(map(str, selected_segments))] if not roads_gdf.empty else gpd.GeoDataFrame()

        log.info(f"selected {len(selected_trails_gdf)} trail segments and {len(selected_roads_gdf)} road segments.")

        log.info("merging selected segments into final trip route")
        final_trip_gdf = gpd.GeoDataFrame(pd.concat([selected_trails_gdf, selected_roads_gdf], ignore_index=True))

        if final_trip_gdf.crs is None or final_trip_gdf.crs != "EPSG:4326":
            final_trip_gdf = final_trip_gdf.to_crs(epsg=4326)

        processed_path = "/tmp/data/processed/final_trip.geojson"
        final_trip_gdf.to_file(processed_path, driver="GeoJSON")

        log.info(f"✅ Route combinations complete")

        log.info("🔄 Processing final route")
        processor = DataProcessor(processed_path)
        processed_route = processor.process_route()

        if processed_route:
            log.info("✅ Route enrichment complete with elevation and difficulty classifications.")
        else:
            log.error("❌ Route enrichment failed.")
            return

        processing_status[session_id] = True

    except Exception as e:
        log.error(f"❌ ERROR: {str(e)}")



### ----------------------------------------
### 🔹 Core App Routes
### ----------------------------------------

@routes.route("/")
def index():
    """Serve the Mapbox 3D map at the root URL."""
    return render_template("map.html", mapbox_api_key=MAPBOX_API_KEY)


@routes.route("/selections")
def selections():
    """serve the trail selection page."""
    return render_template("selections.html", mapbox_api_key=MAPBOX_API_KEY)

@routes.route("/processing/<session_id>")
def processing(session_id):
    """renders the processing page with live logs."""
    return render_template("processing.html", session_id=session_id)

@routes.route("/check-status/<session_id>")
def check_status(session_id):
    """checks if processing is complete and returns status."""
    is_done = processing_status.get(session_id, False)
    log.info(f"📡 Checking status for session {session_id}: {'✅ Done' if is_done else '🔄 In Progress'}")
    return jsonify({"done": is_done})

@routes.route("/adventure")
def adventure():
    """serve the final adventure page."""
    return render_template("adventure.html", mapbox_api_key=MAPBOX_API_KEY)


### ----------------------------------------
### flask endpoints mostly to get geojson and weathr
### ----------------------------------------

@routes.route("/api/fetch_trails", methods=["POST"])
def fetch_trails():
    """Fetch trails, roads, and trailheads and save to processed directory."""
    try:
        data = request.get_json()

        log.info(f"📡 Received request payload: {json.dumps(data, indent=2)}")

        if not data or "bbox" not in data:
            log.error("missing or invalid BBOX in request.")
            return jsonify({"error": "Missing 'bbox' parameter in request"}), 400

        bbox = data.get("bbox")

        if not isinstance(bbox, list) or len(bbox) != 4:
            log.error(f"invalid BBOX format received: {bbox}")
            return jsonify({"error": "Invalid bbox format. Expected [minX, minY, maxX, maxY]."}), 400

        log.info(f"bbox: {bbox}")

        # fetch data
        fetched_data = data_fetcher.fetch_all_trails(bbox)
        if not fetched_data:
            return jsonify({"message": "No trails found"}), 200

        trails_gdf, roads_gdf, trailheads_gdf = fetched_data

        # save geojson
        for gdf, path in [
            (trails_gdf, "/tmp/data/processed/fetched_trails.geojson"),
            (roads_gdf, "/tmp/data/processed/roads.geojson"),
            (trailheads_gdf, "/tmp/data/processed/fetched_trailheads.geojson")
        ]:
            if gdf.crs is None or gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            gdf.to_file(path, driver="GeoJSON")

        return jsonify({"redirect": url_for('routes.selections')})

    except Exception as e:
        log.error(f"❌ ERROR in fetch_trails: {str(e)}")
        return jsonify({"error": f"Failed to fetch trails: {str(e)}"}), 500
    
@routes.route("/api/get_saved_trails", methods=["GET"])
def get_saved_trails():
    """Serve the previously saved trails, roads, and trailheads."""
    try:
        files = {
            "trails": "/tmp/data/processed/fetched_trails.geojson",
            "roads": "/tmp/data/processed/roads.geojson",
            "trailheads": "/tmp/data/processed/fetched_trailheads.geojson"
        }

        saved_data = {}

        for key, path in files.items():
            if os.path.exists(path):
                log.info(f"Loading {key} from {path}")
                saved_data[key] = json.loads(gpd.read_file(path).to_json())
            else:
                log.warning(f"no saved {key} found at {path}")

        if not saved_data:
            return jsonify({"error": "No saved trails, roads, or trailheads found."}), 404

        return jsonify(saved_data)

    except Exception as e:
        log.error(f"ERROR in get_saved_trails: {str(e)}")
        return jsonify({"error": f"Failed to load saved data: {str(e)}"}), 500

@routes.route("/api/process_route", methods=["POST"])
def process_route():
    """Processes the selected segments and waits for all geoprocessing steps to complete."""
    data = request.get_json()
    selected_segments = data.get("selected_segments")

    if not selected_segments:
        log.error("no segments selected.")
        return jsonify({"error": "No segments selected"}), 400

    session_id = str(int(time.time()))
    final_route_path = "/tmp/data/processed/final_trip.geojson"
    processing_status[session_id] = False

    log.info(f"🔄 Starting processing for session {session_id}...")

    def run_processing():
        try:
            perform_processing(selected_segments, session_id)
            log.info(f"Final trip route saved to {final_route_path}")

            processor = DataProcessor(final_route_path)
            log.info("Filtering trailheads...")
            processor.process_route()

            processing_status[session_id] = True
            log.info("all processing steps completed successfully.")

        except Exception as e:
            log.error(f"Unexpected error during processing: {str(e)}")

    thread = threading.Thread(target=run_processing)
    thread.start()

    return jsonify({"redirect": url_for('routes.processing', session_id=session_id)})

@routes.route("/api/get_adventure_data", methods=["GET"])
def get_adventure_data():
    """Serves the final enriched route and filtered trailheads (as POIs)."""
    try:
        files = {
            "trails": "/tmp/data/processed/final_trip.geojson",
            "pois": "/tmp/data/processed/filtered_trailheads.geojson"
        }

        adventure_data = {}
        for key, path in files.items():
            if os.path.exists(path):
                log.info(f"📂 Loading {key} from {path}")
                adventure_data[key] = json.loads(gpd.read_file(path).to_json())
            else:
                log.warning(f"⚠️ No saved {key} found at {path}")

        return jsonify(adventure_data)

    except Exception as e:
        log.error(f"ERROR in get_adventure_data: {str(e)}")
        return jsonify({"error": f"Failed to load adventure data: {str(e)}"}), 500
    
@routes.route("/api/get_weather", methods=["POST"])
def get_weather():
    """Fetches weather forecast for the bounding box centroid."""
    try:
        data = request.get_json()
        bbox = data.get("bbox")

        if not bbox or len(bbox) != 4:
            return jsonify({"error": "Invalid BBOX format"}), 400

        minX, minY, maxX, maxY = bbox
        centroid_lat = (minY + maxY) / 2
        centroid_lon = (minX + maxX) / 2

        if not OPENWEATHER_API_KEY:
            return jsonify({"error": "Missing OpenWeather API Key"}), 500
        open_weather_url = reference_layers[1]["url"]

        # query open weather api for area forecast
        weather_url = f"{open_weather_url}?lat={centroid_lat}&lon={centroid_lon}&appid={OPENWEATHER_API_KEY}&units=imperial"
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json()

        forecast = {
            "temperature": weather_data["main"]["temp"],
            "description": weather_data["weather"][0]["description"].capitalize(),
            "wind_speed": weather_data["wind"]["speed"],
            "humidity": weather_data["main"]["humidity"]
        }

        return jsonify(forecast)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Weather API request failed: {str(e)}"}), 500


def log_stream():
    """stream logs to the frontend using SSE without blocking gunicorn workers."""
    with open(LOG_FILE, "r") as log_file:
        log_file.seek(0, os.SEEK_END)  # Move to the end of the file

        while True:
            rlist, _, _ = select.select([log_file], [], [], 1)
            
            if rlist:
                line = log_file.readline().strip()
                if line:
                    yield f"data: {line}\n\n"
            
            #handle client disconnects
            if not log_file.readable():
                print("client disconnected, stopping log stream.")
                break

@routes.route("/logs")
def stream_logs():
    """Streams logs in real-time using Server-Sent Events (SSE)."""
    return Response(
        stream_with_context(log_stream()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

