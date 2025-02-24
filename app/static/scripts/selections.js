mapboxgl.accessToken = mapboxApiKey;

const map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/mapbox/outdoors-v12",
  center: [-105.0, 37.3],
  zoom: 10,
  pitch: 60,
  bearing: 180,
  antialias: true,
});

map.addControl(new mapboxgl.NavigationControl());

//store selected trail & road segments with mileage
let selectedSegments = new Map();
let totalDistance = 0;

let popup = new mapboxgl.Popup({
  closeButton: false,
  closeOnClick: false,
});

map.on("load", function () {
  map.addSource("mapbox-dem", {
    type: "raster-dem",
    url: "mapbox://mapbox.terrain-rgb",
    tileSize: 512,
    maxzoom: 14,
  });

  map.setTerrain({ source: "mapbox-dem", exaggeration: 2.0 });

  console.log("3D Terrain Enabled with Southward Orientation");

  //load the saved trails, roads & trailheads dedicated endpoint
  fetch("/api/get_saved_trails")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error loading trails, roads & trailheads:", data.error);
        return;
      }

      //add trails to map
      map.addSource("ohv-trails", { type: "geojson", data: data.trails });
      map.addLayer({
        id: "trail-layer",
        type: "line",
        source: "ohv-trails",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            "#00FF00",
            "#FF5733",
          ],
          "line-width": 4,
        },
      });

      //roads to the map
      map.addSource("roads", { type: "geojson", data: data.roads });
      map.addLayer({
        id: "road-layer",
        type: "line",
        source: "roads",
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            "#00FF00",
            "#FF5733",
          ],
          "line-width": 3,
        },
      });

      //add trailheads
      map.addSource("trailheads", { type: "geojson", data: data.trailheads });
      map.addLayer({
        id: "trailheads-layer",
        type: "circle",
        source: "trailheads",
        paint: {
          "circle-radius": 6,
          "circle-color": "#2ECC71",
          "circle-stroke-width": 1,
          "circle-stroke-color": "#000",
        },
      });

      console.log("Trails, Roads & Trailheads loaded onto selection map.");
    })
    .catch((error) => console.error("Error loading saved trails:", error));
});

//handle selection of both trails & roads
function toggleSegmentSelection(layerId, feature) {
  const mapboxId = feature.id; //mbox ID for feature state
  const segmentId = feature.properties.OBJECTID;

  if (!mapboxId || !segmentId) {
    console.error("Feature is missing a valid ID:", feature);
    return;
  }

  const segmentName =
    feature.properties.TRAIL_NAME ||
    feature.properties.NAME ||
    "Unnamed Segment";
  const distance = feature.properties.GIS_MILES || 0;

  if (selectedSegments.has(segmentId)) {
    selectedSegments.delete(segmentId);
    totalDistance -= distance;

    if (map.getSource(layerId)) {
      console.log(
        `Deselecting ${segmentName} (Mapbox ID: ${mapboxId}, OBJECTID: ${segmentId})`
      );
      map.setFeatureState(
        { source: layerId, id: mapboxId },
        { selected: false }
      );
    } else {
      console.warn(`source '${layerId}' not found for feature state update.`);
    }
  } else {
    selectedSegments.set(segmentId, { name: segmentName, distance: distance });
    totalDistance += distance;

    if (map.getSource(layerId)) {
      console.log(
        `Selecting ${segmentName} (Mapbox ID: ${mapboxId}, OBJECTID: ${segmentId})`
      );
      map.setFeatureState(
        { source: layerId, id: mapboxId },
        { selected: true }
      );
    } else {
      console.warn(`Source '${layerId}' not found for feature state update.`);
    }
  }

  updateSegmentList();
  console.log(
    "Selected Segments for Filtering:",
    Array.from(selectedSegments.keys())
  );
}

//toggle selection for trails
map.on("click", "trail-layer", (e) => {
  toggleSegmentSelection("ohv-trails", e.features[0]);
});

//toggle selection for roads
map.on("click", "road-layer", (e) => {
  toggleSegmentSelection("roads", e.features[0]);
});

map.on("mouseenter", "trail-layer", (e) => {
  map.getCanvas().style.cursor = "pointer";
  const trailName = e.features[0].properties.TRAIL_NAME || "Unknown Trail";
  const distance = e.features[0].properties.GIS_MILES || 0;
  popup
    .setLngLat(e.lngLat)
    .setHTML(
      `<strong>Trail:</strong> ${trailName} <br><strong>Distance:</strong> ${distance.toFixed(
        2
      )} miles`
    )
    .addTo(map);
});

map.on("mouseleave", "trail-layer", () => {
  map.getCanvas().style.cursor = "";
  popup.remove();
});

map.on("mouseenter", "road-layer", (e) => {
  map.getCanvas().style.cursor = "pointer";
  const roadName = e.features[0].properties.NAME || "Unknown Road";
  const distance = e.features[0].properties.GIS_MILES || 0;
  popup
    .setLngLat(e.lngLat)
    .setHTML(
      `<strong>Road:</strong> ${roadName} <br><strong>Distance:</strong> ${distance.toFixed(
        2
      )} miles`
    )
    .addTo(map);
});

map.on("mouseleave", "road-layer", () => {
  map.getCanvas().style.cursor = "";
  popup.remove();
});

map.on("mouseenter", "trailheads-layer", (e) => {
  map.getCanvas().style.cursor = "pointer";
  const siteName = e.features[0].properties.PUBLIC_SITE_NAME || "Unknown Site";
  popup
    .setLngLat(e.lngLat)
    .setHTML(`<strong>Trailhead:</strong> ${siteName}`)
    .addTo(map);
});

map.on("mouseleave", "trailheads-layer", () => {
  map.getCanvas().style.cursor = "";
  popup.remove();
});

//sidebar list
function updateSegmentList() {
  const segmentList = document.getElementById("selected-trails-list");
  const totalDistanceElement = document.getElementById("total-distance");

  if (!segmentList || !totalDistanceElement) {
    console.error("❌ Error: Sidebar elements missing from DOM.");
    return;
  }

  //clear existing list
  segmentList.innerHTML = "";

  selectedSegments.forEach((segment, id) => {
    let listItem = document.createElement("li");
    listItem.innerHTML = `${segment.name} - ${segment.distance.toFixed(2)} mi`;
    segmentList.appendChild(listItem);
  });

  totalDistanceElement.innerText = totalDistance.toFixed(2);
}

// confirm Selection Button
document.getElementById("confirm-selection").addEventListener("click", () => {
  console.log("selected segments:", Array.from(selectedSegments.keys()));

  fetch("/api/process_route", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_segments: Array.from(selectedSegments.keys()),
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.redirect) {
        window.location.href = data.redirect;
      }
    })
    .catch((error) => console.error("Error processing route:", error));
});
