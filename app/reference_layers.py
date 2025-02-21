trails_roads = [
    {
        "name": "usfs_trails",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0",
        "fields": ["TRAIL_NAME", "GIS_MILES"],
        "query": '1=1'
    },
    {
        "name": "usfs_roads",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RoadBasic_01/MapServer/0",
        "fields": ["NAME", "GIS_MILES"],
        "query": '1=1'
    },
    {
        "name": "usfs_rec_sites",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_InfraRecreationSites_01/MapServer/0",
        "fields": ["PUBLIC_SITE_NAME", "SITE_SUBTYPE"],
        "query": '1=1'
    },
]

reference_layers = [
    {
        "name": "elevation",
        "url": "https://portal.opentopography.org/API/globaldem",
    },
    {
        "name": "osm",
        "url": "https://portal.opentopography.org/API/globaldem",
    }
]