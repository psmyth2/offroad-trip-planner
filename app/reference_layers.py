reference_layers = [
    {
        "name": "usfs_trails",
        "full_name": "trails",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0",
        "extraction_method": "spatial_join_majority",
        "field": "TRAIL_NAME",
        "query": '1=1'
    },
    {
        "name": "usfs_rec_sites",
        "full_name": "rec_sites",
        "url": "https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_InfraRecreationSites_01/MapServer/0",
        "extraction_method": "spatial_join_majority",
        "field": "SITE_SUBTYPE",
        "query": '1=1'
    },
]