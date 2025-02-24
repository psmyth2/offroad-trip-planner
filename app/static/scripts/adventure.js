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
            populateSidebar(data.trails)

            // ✅ Fit map to final trail extent
            zoomToFinalRoute(data.trails);

            // ✅ Fetch weather separately
            fetchWeatherForecast();
        })
        .catch(error => console.error("❌ Error loading adventure data:", error));
});

function zoomToFinalRoute(trails) {
    const bounds = new mapboxgl.LngLatBounds();
    
    trails.features.forEach(feature => {
        feature.geometry.coordinates.forEach(coord => bounds.extend(coord));
    });

    map.fitBounds(bounds, {
        padding: 100,  // ✅ Increased padding for better visibility
        duration: 1200  // ✅ Slightly longer animation for smooth zoom
    });

    // ✅ Set 3D Perspective After Zooming
    map.once('moveend', () => {
        map.easeTo({
            zoom: 11,
            bearing: 180,  // ✅ Face southward for better view
            pitch: 65,     // ✅ Increase pitch for a 3D effect
            duration: 800  // ✅ Smooth transition
        });
    });
}

// ✅ Function to Add Trail Layer with Difficulty-Based Coloring + Hover Popups
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

    // ✅ Add hover popups for trails/roads (Use `TRAIL_NAME` OR `NAME`)
    map.on("mouseenter", "trail-layer", (e) => {
        map.getCanvas().style.cursor = "pointer";
        const feature = e.features[0].properties;
        const trailName = feature.TRAIL_NAME || feature.NAME || "Unnamed Trail";
        const difficulty = feature.Difficulty || "Unknown";
        
        const popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false })
            .setLngLat(e.lngLat)
            .setHTML(`<strong>${trailName}</strong><br>Difficulty: ${difficulty}`)
            .addTo(map);

        map.on("mouseleave", "trail-layer", () => {
            map.getCanvas().style.cursor = "";
            popup.remove();
        });
    });
}


// ✅ Function to Add POI Layer with Unique Symbols per `SITE_SUBTYPE` + Hover Popups + Legend
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

    // ✅ Add hover popups for POIs
    map.on("mouseenter", "poi-layer", (e) => {
        map.getCanvas().style.cursor = "pointer";
        const poiName = e.features[0].properties.PUBLIC_SITE_NAME || "Unnamed POI";
        const siteType = e.features[0].properties.SITE_SUBTYPE || "Unknown Type";
        const popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false })
            .setLngLat(e.lngLat)
            .setHTML(`<strong>${poiName}</strong><br>Type: ${siteType}`)
            .addTo(map);
        map.on("mouseleave", "poi-layer", () => {
            map.getCanvas().style.cursor = "";
            popup.remove();
        });
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

function populateSidebar(trails) {
    const trailsList = document.getElementById("selected-trails-list");
    trailsList.innerHTML = "";  // ✅ Clear existing list before populating

    // ✅ Ensure `data.trails.features` exists before looping
    if (!trails || !trails.features || trails.features.length === 0) {
        console.warn("⚠️ No trails found in dataset.");
        trailsList.innerHTML = "<li>No trails selected.</li>";
        return;
    }

    // ✅ Populate Selected Trails with Name & Mileage
    trails.features.forEach(trail => {
        let item = document.createElement("li");
        let name = trail.properties.TRAIL_NAME || trail.properties.NAME || "Unnamed Trail";
        let mileage = trail.properties.GIS_MILES ? `${trail.properties.GIS_MILES.toFixed(1)} mi` : "Unknown mileage";
        let difficulty = trail.properties.Difficulty || "Unknown";

        item.innerText = `${name} - ${mileage} (${difficulty})`;
        trailsList.appendChild(item);
    });
}

// ✅ Function to Get Current Map Bounding Box
function getMapBoundingBox() {
    const bounds = map.getBounds();
    return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];
}

// ✅ Separate Fetch for Weather Forecast
function fetchWeatherForecast() {
    const bbox = getMapBoundingBox();
    fetch("/api/get_weather", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bbox: bbox })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("❌ Weather API Error:", data.error);
            return;
        }
        document.getElementById("weather-info").innerHTML = `
            <strong>Temperature:</strong> ${data.temperature}°F <br>
            <strong>Condition:</strong> ${data.description} <br>
            <strong>Wind Speed:</strong> ${data.wind_speed} mph <br>
            <strong>Humidity:</strong> ${data.humidity}%
        `;
    })
    .catch(error => console.error("❌ Error fetching weather data:", error));
}
