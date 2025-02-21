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

// Store selected trail segments & their mileage
let selectedTrails = new Map();
let totalDistance = 0;

// Create a new popup instance
let popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnClick: false
});

map.on('load', function () {
    map.addSource('mapbox-dem', {
        "type": "raster-dem",
        "url": "mapbox://mapbox.terrain-rgb",
        "tileSize": 512,
        "maxzoom": 14
    });

    map.setTerrain({ "source": "mapbox-dem", "exaggeration": 2.0 });

    console.log("✅ 3D Terrain Enabled with Southward Orientation");

    // Load the saved trails & trailheads from API
    fetch("/api/get_saved_trails")
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error loading trails & trailheads:", data.error);
                return;
            }

            // Add trails to the map
            map.addSource("ohv-trails", { type: "geojson", data: data.trails });
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

            // Add trails to the map
            map.addSource("roads", { type: "geojson", data: data.roads });
            map.addLayer({
                id: "road-layer",
                type: "line",
                source: "roads",
                layout: { "line-join": "round", "line-cap": "round" },
                paint: {
                    "line-color": ["case",
                        ["boolean", ["feature-state", "selected"], false], "#00FF00", // Green for selected
                        "purple" // Default color
                    ],
                    "line-width": 4
                }
            });

            // Add trailheads to the map
            map.addSource("trailheads", { type: "geojson", data: data.trailheads });
            map.addLayer({
                id: "trailheads-layer",
                type: "circle",
                source: "trailheads",
                paint: {
                    "circle-radius": 6,
                    "circle-color": "#2ECC71",
                    "circle-stroke-width": 1,
                    "circle-stroke-color": "#000"
                }
            });

            console.log("✅ Trails & Trailheads loaded onto selection map.");
        })
        .catch(error => console.error("Error loading saved trails:", error));
});

// Change cursor & show popup when hovering over trails
map.on("mouseenter", "trail-layer", (e) => {
    map.getCanvas().style.cursor = "pointer";

    const trailName = e.features[0].properties.TRAIL_NAME || "Unknown Trail";
    const distance = e.features[0].properties.GIS_MILES || 0;

    popup.setLngLat(e.lngLat)
        .setHTML(`<strong>Trail:</strong> ${trailName} <br><strong>Distance:</strong> ${distance.toFixed(2)} miles`)
        .addTo(map);
});

// Remove popup and reset cursor when leaving trails
map.on("mouseleave", "trail-layer", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
});

// Change cursor & show popup when hovering over trailheads
map.on("mouseenter", "trailheads-layer", (e) => {
    map.getCanvas().style.cursor = "pointer";

    const siteName = e.features[0].properties.PUBLIC_SITE_NAME || "Unknown Site";
    
    popup.setLngLat(e.lngLat)
        .setHTML(`<strong>Trailhead:</strong> ${siteName}`)
        .addTo(map);
});

// Remove popup and reset cursor when leaving trailheads
map.on("mouseleave", "trailheads-layer", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
});

// Click event to toggle trail segment selection & update list
map.on("click", "trail-layer", (e) => {
    const feature = e.features[0];
    const trailId = feature.id || feature.properties.id;
    const trailName = feature.properties.TRAIL_NAME || "Unnamed Trail";
    const distance = feature.properties.GIS_MILES || 0;  // Use GIS_MILES

    if (selectedTrails.has(trailId)) {
        selectedTrails.delete(trailId);
        totalDistance -= distance;
        map.setFeatureState({ source: "ohv-trails", id: trailId }, { selected: false });
    } else {
        selectedTrails.set(trailId, { name: trailName, distance: distance });
        totalDistance += distance;
        map.setFeatureState({ source: "ohv-trails", id: trailId }, { selected: true });
    }

    updateTrailList();
    console.log("Selected Trails:", Array.from(selectedTrails.keys()));
});

function updateTrailList() {
    const trailList = document.getElementById("selected-trails-list");
    const totalDistanceElement = document.getElementById("total-distance");

    if (!trailList || !totalDistanceElement) {
        console.error("❌ Error: Sidebar elements missing from DOM.");
        return;
    }

    // Clear existing list
    trailList.innerHTML = "";

    selectedTrails.forEach((trail, id) => {
        let listItem = document.createElement("li");
        listItem.innerHTML = `${trail.name} - ${trail.distance.toFixed(2)} mi`;
        trailList.appendChild(listItem);
    });

    // Update total distance
    totalDistanceElement.innerText = totalDistance.toFixed(2);
}

// Confirm Selection Button
document.getElementById("confirm-selection").addEventListener("click", () => {
    console.log("🚀 Final Selected Trails:", Array.from(selectedTrails.keys()));

    fetch("/api/process_route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_trails: Array.from(selectedTrails.keys()) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.redirect) {
            window.location.href = data.redirect;  // Redirect to processing page
        }
    })
    .catch(error => console.error("Error processing route:", error));
});
