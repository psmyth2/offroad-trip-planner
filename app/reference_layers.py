trails_roads = [
    {
        "name": "usfs_trails",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0",
        "fields": ["TRAIL_NAME", "GIS_MILES", "ACCESSIBILITY_STATUS", "TERRA_MOTORIZED"],
        "query": "ACCESSIBILITY_STATUS <> 'NOT ACCESSIBLE' AND TERRA_MOTORIZED <> 'N'"
    },
    {
        "name": "usfs_roads",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RoadBasic_01/MapServer/0",
        "fields": ["NAME", "GIS_MILES", "OPENFORUSETO"],
        "query": "OPENFORUSETO = 'ALL'"
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
        "name": "weather",
        "url": "https://api.openweathermap.org/data/2.5/weather",
    }

]