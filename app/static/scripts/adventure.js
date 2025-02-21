mapboxgl.accessToken = mapboxApiKey;

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/outdoors-v12',
    center: [-105.0, 37.3],
    zoom: 10,
    pitch: 65,
    bearing: 180,
    antialias: true
});

// ✅ Add zoom and rotation controls
map.addControl(new mapboxgl.NavigationControl());

// ✅ Wait until the map style is fully loaded before adding sources
map.on("load", function () {
    console.log("✅ Map style fully loaded. Adding sources...");

    map.addSource('mapbox-dem', {
        "type": "raster-dem",
        "url": "mapbox://mapbox.terrain-rgb",
        "tileSize": 512,
        "maxzoom": 14
    });

    map.setTerrain({ "source": "mapbox-dem", "exaggeration": 2.0 });
    console.log("✅ 3D Terrain Enabled with Southward Orientation");

    fetch("/api/get_adventure_data")
        .then(response => response.json())
        .then(data => {
            if (!data.trails || !data.trails.features) {
                console.error("❌ Error: No trail data available.");
                return;
            }

            addTrailLayer(data.trails);
            addPOILayer(data.pois);
            populateSidebar(data);
        })
        .catch(error => console.error("❌ Error loading adventure data:", error));
});

// ✅ Function to Add Trail Layer with Difficulty-Based Coloring
function addTrailLayer(trails) {
    map.addSource("final-trails", { type: "geojson", data: trails });
    map.addLayer({
        id: "trail-layer",
        type: "line",
        source: "final-trails",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
            "line-color": [
                "match",
                ["get", "Difficulty"],
                "Easy", "#2ECC71",
                "Moderate", "#F1C40F",
                "Difficult", "#E74C3C",
                "#7F8C8D"
            ],
            "line-width": 4
        }
    });
}

// ✅ Function to Add POI Layer with Unique Symbols per `SITE_SUBTYPE`
function addPOILayer(pois) {
    if (!pois || !pois.features) return;

    // ✅ Extract Unique `SITE_SUBTYPE` Values
    let uniquePOITypes = new Set();
    pois.features.forEach(poi => {
        if (poi.properties.SITE_SUBTYPE) {
            uniquePOITypes.add(poi.properties.SITE_SUBTYPE);
        }
    });

    console.log("✅ Unique POI Types Found:", Array.from(uniquePOITypes));

    // ✅ Define Color Mapping for POI Categories
    const poiColorMap = {
        "CAMPING AREA": "#8B4513",
        "CAMPGROUND": "#2E8B57",
        "TRAILHEAD": "#1E90FF",
        "DAY USE AREA": "#FFD700",
        "FISHING SITE": "#4169E1",
        "LOOKOUT/CABIN": "#8B0000",
        "OHV STAGING AREA": "#FF4500",
        "PICNIC SITE": "#FF69B4",
        "SKI AREA ALPINE": "#00CED1",
        "WILDLIFE VIEWING SITE": "#32CD32"
    };

    // ✅ Apply Default Gray for Unlisted POI Types
    map.addSource("pois", { type: "geojson", data: pois });
    map.addLayer({
        id: "poi-layer",
        type: "circle",
        source: "pois",
        paint: {
            "circle-radius": 6,
            "circle-color": [
                "match",
                ["get", "SITE_SUBTYPE"],
                ...Object.entries(poiColorMap).flat(),
                "#808080"  // Default Gray
            ]
        }
    });

    // ✅ Generate POI Legend Dynamically
    const poiLegendContainer = document.getElementById("poi-legend");
    poiLegendContainer.innerHTML = "";  // Clear existing legend

    uniquePOITypes.forEach(type => {
        const color = poiColorMap[type] || "#808080";  // Default Gray if not found
        const legendItem = document.createElement("div");
        legendItem.innerHTML = `<span class="legend-box" style="background:${color};"></span> ${type}`;
        poiLegendContainer.appendChild(legendItem);
    });
}


// ✅ Function to Populate Sidebar with Trails & POIs
function populateSidebar(data) {
    const trailsList = document.getElementById("selected-trails-list");
    data.trails.features.forEach(trail => {
        let item = document.createElement("li");
        let name = trail.properties.TRAIL_NAME || trail.properties.NAME || "Unnamed Trail";
        let difficulty = trail.properties.Difficulty || "Unknown";
        let mileage = trail.properties.GIS_MILES ? `${trail.properties.GIS_MILES.toFixed(1)} mi` : "Unknown mileage";
        item.innerText = `${name} - ${difficulty} (${mileage})`;
        trailsList.appendChild(item);
    });

    const poiList = document.getElementById("poi-list");
    data.pois.features.forEach(poi => {
        let item = document.createElement("li");
        let name = poi.properties.PUBLIC_SITE_NAME || "Unnamed POI";
        let subtype = poi.properties.SITE_SUBTYPE || "Unknown Type";
        item.innerText = `${name} (${subtype})`;
        poiList.appendChild(item);
    });
}
