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

// Load Final Enriched GeoJSON Layers
fetch("/api/get_adventure_data")
    .then(response => response.json())
    .then(data => {
        // Add Selected Trails
        map.addSource("final-trails", { type: "geojson", data: data.trails });
        map.addLayer({
            id: "trail-layer",
            type: "line",
            source: "final-trails",
            layout: { "line-join": "round", "line-cap": "round" },
            paint: { "line-color": "#FF5733", "line-width": 3 }
        });

        // Add Trailheads
        map.addSource("trailheads", { type: "geojson", data: data.trailheads });
        map.addLayer({
            id: "trailheads-layer",
            type: "circle",
            source: "trailheads",
            paint: { "circle-radius": 6, "circle-color": "#2ECC71" }
        });

        // Add POIs
        map.addSource("pois", { type: "geojson", data: data.pois });
        map.addLayer({
            id: "poi-layer",
            type: "circle",
            source: "pois",
            paint: { "circle-radius": 6, "circle-color": "#3498DB" }
        });

        // Populate Sidebar Lists
        populateSidebar(data);
    })
    .catch(error => console.error("Error loading adventure data:", error));

function populateSidebar(data) {
    const trailsList = document.getElementById("selected-trails-list");
    data.trails.features.forEach(trail => {
        let item = document.createElement("li");
        item.innerText = trail.properties.name || "Unnamed Trail";
        trailsList.appendChild(item);
    });

    const poiList = document.getElementById("poi-list");
    data.pois.features.forEach(poi => {
        let item = document.createElement("li");
        item.innerText = poi.properties.name || "Unknown POI";
        poiList.appendChild(item);
    });
}
