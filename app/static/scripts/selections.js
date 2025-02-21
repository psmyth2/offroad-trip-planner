mapboxgl.accessToken = mapboxApiKey;

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/outdoors-v12',
    center: [-105.0, 37.3],
    zoom: 10,
    pitch: 60,
    bearing: 180,
    antialias: true
});

// Add zoom and rotation controls
map.addControl(new mapboxgl.NavigationControl());

// Store selected trail segment IDs
let selectedTrails = new Set();

map.on('load', function () {
    map.addSource('mapbox-dem', {
        "type": "raster-dem",
        "url": "mapbox://mapbox.terrain-rgb",
        "tileSize": 512,
        "maxzoom": 14
    });

    map.setTerrain({ "source": "mapbox-dem", "exaggeration": 2.0 });

    console.log("✅ 3D Terrain Enabled with Southward Orientation");

    // Load the already saved trails GeoJSON
    fetch("/api/get_saved_trails")
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error loading trails:", data.error);
                return;
            }

            // Add trails to the map
            map.addSource("ohv-trails", { type: "geojson", data: data });
            map.addLayer({
                id: "trail-layer",
                type: "line",
                source: "ohv-trails",
                layout: { "line-join": "round", "line-cap": "round" },
                paint: {
                    "line-color": ["case",
                        ["boolean", ["feature-state", "selected"], false], "#00FF00", // Green for selected
                        "#FF5733" // Default color
                    ],
                    "line-width": 4
                }
            });

            console.log("✅ Trails loaded onto selection map.");
        })
        .catch(error => console.error("Error loading saved trails:", error));
});

// Change cursor when hovering over trails
map.on("mouseenter", "trail-layer", () => {
    map.getCanvas().style.cursor = "pointer";  // Change to pointer
});

map.on("mouseleave", "trail-layer", () => {
    map.getCanvas().style.cursor = "";  // Reset to default
});

// Click event to toggle trail segment selection
map.on("click", "trail-layer", (e) => {
    const feature = e.features[0];
    const trailId = feature.id || feature.properties.id;

    if (selectedTrails.has(trailId)) {
        selectedTrails.delete(trailId);
        map.setFeatureState({ source: "ohv-trails", id: trailId }, { selected: false });
    } else {
        selectedTrails.add(trailId);
        map.setFeatureState({ source: "ohv-trails", id: trailId }, { selected: true });
    }

    console.log("Selected Trails:", Array.from(selectedTrails));
});

// Confirm Selection Button
document.getElementById("confirm-selection").addEventListener("click", () => {
    console.log("🚀 Final Selected Trails:", Array.from(selectedTrails));

    fetch("/api/process_route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_trails: Array.from(selectedTrails) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.redirect) {
            window.location.href = data.redirect;  // Redirect to processing page
        }
    })
    .catch(error => console.error("Error processing route:", error));
});
