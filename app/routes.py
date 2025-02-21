import os
import json
import configparser
import geopandas as gpd
import pandas as pd
import requests
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.utils.data_fetcher import DataFetcher

routes = Blueprint("routes", __name__)

# Read API Key from config.ini
config = configparser.ConfigParser()
config.read("config.ini")
MAPBOX_API_KEY = config.get("mapbox", "API_KEY")

# Initialize DataFetcher
data_fetcher = DataFetcher()

@routes.route("/")
def index():
    """Serve the Mapbox 3D map at the root URL."""
    return render_template("map.html", mapbox_api_key=MAPBOX_API_KEY)

@routes.route("/api/fetch_trails", methods=["POST"])
def fetch_trails():
    """Fetch trails and redirect to the selections page after processing."""
    data = request.get_json()
    bbox = data.get("bbox")

    if not bbox or len(bbox) != 4:
        return jsonify({"error": "Invalid BBOX format"}), 400

    try:
        # Fetch trails
        fetched_data = data_fetcher.fetch_all_data(bbox)
        if not fetched_data:
            return jsonify({"message": "No trails found"}), 200

        # Extract just the trail data
        final_gdf = fetched_data[0]  # Ensure this is the trail layer

        # Ensure CRS is WGS84
        if final_gdf.crs is None or final_gdf.crs != "EPSG:4326":
            final_gdf = final_gdf.to_crs(epsg=4326)

        # Save trails
        processed_path = "data/processed/fetched_trails.geojson"
        final_gdf.to_file(processed_path, driver="GeoJSON")

        # Return GeoJSON data along with redirect URL
        return jsonify({
            "redirect": url_for('routes.selections'),
            "trails": json.loads(final_gdf.to_json())  # Convert to JSON
        })

    except Exception as e:
        return jsonify({"error": f"Failed to fetch trails: {str(e)}"}), 500
    
@routes.route("/api/get_saved_trails", methods=["GET"])
def get_saved_trails():
    """Serve the previously saved trails from data/processed."""
    try:
        trails_path = "data/processed/fetched_trails.geojson"

        if not os.path.exists(trails_path):
            return jsonify({"error": "No saved trails found"}), 404

        trails = gpd.read_file(trails_path).to_json()
        return jsonify(json.loads(trails))  # Convert GeoJSON to dict before sending

    except Exception as e:
        return jsonify({"error": f"Failed to load saved trails: {str(e)}"}), 500

@routes.route("/selections")
def selections():
    """Serve the trail selection page."""
    return render_template("selections.html", mapbox_api_key=MAPBOX_API_KEY)

@routes.route("/api/process_route", methods=["POST"])
def process_route():
    """Process selected trail segments and redirect to the logging page."""
    data = request.get_json()
    selected_trails = data.get("selected_trails")

    if not selected_trails:
        return jsonify({"error": "No trails selected"}), 400

    # Processing step (Enrichment - Slope, POIs, etc.)
    processed_data = data_fetcher.process_selected_trails(selected_trails)

    # Save processed trip data
    processed_path = "data/processed/final_trip.geojson"
    processed_data.to_file(processed_path, driver="GeoJSON")

    return jsonify({"redirect": url_for('routes.logging')})

@routes.route("/logging")
def logging():
    """Serve the logging page where geospatial processing feedback is shown."""
    return render_template("processing.html")

@routes.route("/adventure")
def adventure():
    """Serve the final adventure page."""
    return render_template("adventure.html", mapbox_api_key=MAPBOX_API_KEY)

@routes.route("/api/get_adventure_data", methods=["GET"])
def get_adventure_data():
    """Serve final enriched trail and POI layers."""
    try:
        trails = gpd.read_file("data/processed/final_trip.geojson").to_json()
        trailheads = gpd.read_file("data/processed/trailheads.geojson").to_json()
        pois = gpd.read_file("data/processed/pois.geojson").to_json()

        return jsonify({
            "trails": json.loads(trails),
            "trailheads": json.loads(trailheads),
            "pois": json.loads(pois)
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load adventure data: {str(e)}"}), 500