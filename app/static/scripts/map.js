mapboxgl.accessToken = mapboxApiKey;

const map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/mapbox/outdoors-v12",
  center: [-105.0, 37.3],
  zoom: 10,
  pitch: 65,
  bearing: 180,
  antialias: true,
});

map.addControl(new mapboxgl.NavigationControl());

//bbox draw
const draw = new MapboxDraw({
  displayControlsDefault: false,
  controls: { polygon: true, trash: true },
  defaultMode: "draw_polygon",
});
map.addControl(draw);

//mbox terrain source with increased extrusion
map.on("load", function () {
  map.addSource("mapbox-dem", {
    type: "raster-dem",
    url: "mapbox://mapbox.terrain-rgb",
    tileSize: 512,
    maxzoom: 14,
  });

  map.setTerrain({ source: "mapbox-dem", exaggeration: 2.0 });

  console.log("3D Terrain Enabled with Southward Orientation");
});

//confirmation of bbox
document.getElementById("confirm-bbox").addEventListener("click", function () {
  const selectedFeatures = draw.getAll();
  if (selectedFeatures.features.length === 0) {
    alert("Please draw a bounding box first.");
    return;
  }

  const coords = selectedFeatures.features[0].geometry.coordinates[0];
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;

  coords.forEach((coord) => {
    minX = Math.min(minX, coord[0]);
    minY = Math.min(minY, coord[1]);
    maxX = Math.max(maxX, coord[0]);
    maxY = Math.max(maxY, coord[1]);
  });

  const bbox = [minX, minY, maxX, maxY];
  console.log("Selected BBOX:", bbox);

  fetch("/api/fetch_trails", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bbox: bbox }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.redirect) {
        window.location.href = data.redirect; //redirect to selections page
      }
    })
    .catch((error) => console.error("Error fetching trails:", error));
});
