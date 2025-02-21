trails_roads = [
    {
        "name": "usfs_trails",
        "full_name": "trails",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0",
        "fields": ["TRAIL_NAME", "GIS_MILES"],
        "query": '1=1'
    },
    {
        "name": "usfs_roads",
        "full_name": "roads",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_RoadBasic_01/MapServer/0",
        "fields": ["NAME", "GIS_MILES"],
        "query": '1=1'
    },
    {
        "name": "usfs_rec_sites",
        "full_name": "rec_sites",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_InfraRecreationSites_01/MapServer/0",
        "fields": ["PUBLIC_SITE_NAME"],
        "query": '1=1'
    },
]

reference_layers = [
    {
        "name": "rec_sites",
        "full_name": "recreation_sites",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_InfraRecreationSites_01/MapServer/0",
        "extraction_method": "spatial_join",
        "field": "SITE_SUBTYPE",
        "query": '1=1'
    },
]