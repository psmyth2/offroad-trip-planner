# 🏔️ Offroad Multi-Day Adventure Planner

🚙 **A Flask + Mapbox web app for planning multi-day offroad adventures, integrating USFS trails, terrain analysis, and interactive 3D maps. This approach allows for a clear demonstration of geospatial Python methods while leveraging Mapbox for first-class interactive visualization.**

🔗 **Live Deployment:** [Offroad Trip Planner](https://offroad-trip-planner-production.up.railway.app/)

## **📌 Features**

- **📍 User-Defined Adventure Areas** → Select a bounding box to define your adventure region.
- **🛤️ Smart Trail Selection** → Fetches USFS OHV/Offroad trails and roads dynamically using intersections with user-defined adventure area (bbox).
- **🏠 Trailhead Filtering** → Displays **only trailheads near your route** as POIs.
- **📊 Elevation & Slope Analysis** → Calculates **route difficulty** (`Easy, Moderate, Difficult`).
- **🌍 3D Map Visualization** → Uses **MapboxGL terrain** with real-time **POI symbology**.
- **🚀 Dockerized Flask API** → Easily deployed via **Railway.app** or run locally using Docker.

---

## **📡 Data Collection Process**

### **📍 1. Trail and Road Data (USFS & BLM)**

- **Source:** [US Forest Service & Bureau of Land Management ArcGIS REST APIs](https://data-usfs.hub.arcgis.com/)
- **Collection Method:**
  - User **selects a bounding box**.
  - System **queries ArcGIS feature servers** for **OHV/Offroad Trails and Roads** in the area (**handled in** `data_fetcher.py`).
  - Results are stored in **GeoJSON** (`fetched_trails.geojson`).

### **🏠 2. Trailheads as POIs**

- **Source:** [USFS Trailheads Dataset](https://data-usfs.hub.arcgis.com/)
- **Processing:**
  - System **fetches all trailheads** within the adventure area (**handled in** `data_fetcher.py`).
  - **Trailheads are filtered** → **Only those within 100m of the final route** are used (geopandas).
  - Final filtered trailheads are saved in **`filtered_trailheads.geojson`** and used as **POIs**.

### **🛣️ 3. Elevation & Slope Data**

- **Source:** [OpenTopography (SRTM DEM)](https://opentopography.org/developers)
- **Processing:**
  - Queries **OpenTopography API** to retrieve a **DEM raster (GeoTIFF)**.
  - Raster analysis extracts **elevation values** along the trail (rasterio).
  - Slope is calculated → Trails are classified into:
    - **Easy** (< 5%)
    - **Moderate** (5-10%)
    - **Difficult** (> 10%)
  - Processed route is saved in **`final_trip.geojson`** (**handled in** `data_processor.py`).

---

## **🛤️ Route Planning Methodology**

### **Step 1: User Defines Adventure Area**

- **User selects a bounding box (BBOX)** using **Mapbox Draw tools**.
- The system fetches **all available trails** within that region (**handled in** `data_fetcher.py`).

### **Step 2: Trail Selection & Route Customization**

- The user **selects trail segments & roads** to build their **multi-day journey**.
- Selected segments are merged into a **single GeoDataFrame**.

### **Step 3: Trailhead & POI Filtering**

- **Trailheads within 100m of the final route** are extracted and displayed as POIs (**handled in** `data_processor.py`).

### **Step 4: Terrain & Slope Analysis**

- DEM data is used to calculate **elevation changes & slope difficulty**.
- Trail segments are classified into:
  - **Easy (Green)**
  - **Moderate (Yellow)**
  - **Difficult (Red)**

### **Step 5: Final Processing & Map Display**

- The **final enriched route** (with POIs, slope classifications, & elevation data) is displayed on the **interactive 3D Mapbox map**.

---

## **🚀 Running Locally with Docker**

To run the Flask app locally, you only need **Docker Desktop installed**. Follow these simple steps:

### **Step 1: Build the Docker Container**

```bash
docker build -t offroad-trip-planner .
```

### **Step 2: Run the Container**

```bash
docker run -p 5000:5000 offroad-trip-planner
```

### **Step 3: Access the App**

Once running, visit:

```
http://localhost:5000
```

✅ The app is now live locally and fully functional!

---
