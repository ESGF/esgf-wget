# esgf-wget
Service API endpoint for simplified wget scripts

## Running the API
This API requires Python 3 and Django 3.0.  The required Django version can be installed from requirements.txt via pip.
```
pip install -r requirements.txt
```
This is ideally done through a virtual environment with virtualenv, or a conda environment using Anaconda Python.

Set the Django `SECRET_KEY` using the environment variable `ESGF_WGET_SECRET_KEY`
```
export ESGF_WGET_SECRET_KEY='...'
```

Copy the contents of esgf-wget-config.cfg-template to a file named esgf-wget-config.cfg.  Copy the path of this config file to an environment variable `ESGF_WGET_CONFIG`.
```
cp esgf-wget-config.cfg-template esgf-wget-config.cfg
export ESGF_WGET_CONFIG=$(pwd)/esgf-wget-config.cfg
```

Fill out the variables in esgf-wget-config.cfg.  Example below.
```
[django]
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = localhost,127.0.0.1

# Expand the number of fields allowed for wget API
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1024

[wget]
# Address of ESGF Solr
ESGF_SOLR_URL = localhost/solr

# Path to XML file containing Solr shards
ESGF_SOLR_SHARDS_XML = /esg/config/esgf_shards_static.xml

# Path to JSON file containing allowed projects to access for datasets
ESGF_ALLOWED_PROJECTS_JSON = /esg/config/esgf_allowed_projects.json

# Default limit on the number of files allowed in a wget script
WGET_SCRIPT_FILE_DEFAULT_LIMIT = 1000

# Maximum number of files allowed in a wget script
WGET_SCRIPT_FILE_MAX_LIMIT = 100000

# Maximum length for facet values used in the wget directory structure
WGET_MAX_DIR_LENGTH = 50
```
### ESGF_SOLR_SHARDS_XML
A path to a XML file that contains a list of Solr shards used by the ESGF Solr database for distributed search.  Example below.
```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<shards>
    <value>localhost:8983/solr</value>
    <value>localhost:8985/solr</value>
    <value>localhost:8987/solr</value>
</shards>
```

### ESGF_ALLOWED_PROJECTS_JSON
A path to a JSON file that contains a list of ESGF projects that are allowed to be used by this API.  Any project that is not listed will cause the API to reject the query.  Example below.
```
{
    "allowed_projects": [
        "CMIP6", 
        "CMIP5", 
        "CMIP3", 
        "input4MIPs", 
        "obs4MIPs", 
        "CREATE-IP", 
        "E3SM"
    ]
}
```

Run the API using manage.py.
```
python manage.py runserver
```
## How to generate scripts

esgf-wget can use either GET or POST requests for obtaining wget scripts.  Queries are accepted from the `/wget` path.

### Facet search
Search for files based on facet values in the ESGF Solr database.

Select files from datasets that have the variable `ta`.
```
http://localhost:8000/wget?variable=ta
```
Select files from a specific dataset ID.
```
http://localhost:8000/wget?dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cl.gr.v20191029|aims3.llnl.gov
```
Multiple values for different facets can be queried where the values are combined with a logical AND.  The query below will select files from datasets with the match `experiment=decadal2000` AND `variable=hus`.
```
http://localhost:8000/wget?experiment=decadal2000&variable=hus
```
Multiple values of the same facet can be queried either as multiple parameters of the same facet, or with a comma-separated list of values for a facet. The values are combined with a logical OR.  The queries below are functionally identical and will select files from datasets with the match `variable=hus` OR `variable=ta`.
```
http://localhost:8000/wget?variable=hus&variable=ta
http://localhost:8000/wget?variable=hus,ta
```
Facet values can be negated using the `!=` operator.  The query below will select files from datasets where `model` is not `CCSM`.
```
http://localhost:8000/wget?model!=CCSM
```

### Free text queries
The parameter `query` can be used for finding any matches for a text value in all metadata fields.  The query below will return files for datasets that have the term "humidity" in any of their metadata.  The query string must be URL-encoded.
```
http://localhost:8000/wget?query=humidity
```
`query` can also be used to pass query strings in the Apache Lucene query syntax.  The query below will return files for datasets that have dataset IDs that begin with the pattern `obs4MIPs.NASA-JPL.AIRS.`.  The query string must be URL-encoded.
```
http://localhost:8000/wget?query=dataset_id:obs4MIPs.NASA-JPL.AIRS.*
```

### Temporal search
Currently not working.  See issue [#36](https://github.com/ESGF/esgf-wget/issues/36)

### Spatial search
The parameter `bbox` is used for searching for data that has geospatial coverage that overlaps a bounding box defined as `[west, south, east, north]`, which represents ranges of latitude and longitude in degrees.  The query below will return files for datasets that overlap with a geospatial bounding box of -10 to 10 degrees longitude and -10 to 10 degrees latitude.  The query string must be URL-encoded.
```
http://localhost:8000/wget?bbox=%5B-10,-10,+10,+10%5D
```

### Dataset version
The parameter `version` is used for finding datasets of a specific version in the date format of YYYYMMDD.
```
http://localhost:8000/wget?version=20201223
```

### Latest datasets
The parameter `latest` is used for finding datasets that are currently the latest version in the database when set to `latest=true`.  It can be used to find datasets that have been superseded by newer versions by setting `latest=false`.  If not set, the wget API will find all versions of datasets.
```
http://localhost:8000/wget?latest=true
```

### Distributed search
The parameter `distrib` is used to enable/disable distributed search, where all provided Solr shards are used for the dataset search.  If `distrib=false`, then only a local search of Solr will be performed.  It is set to true by default.
```
http://localhost:8000/wget?distrib=false&dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cl.gr.v20191029|aims3.llnl.gov
```

### Shard search
The parameter `shards` is used to pass specific Solr shards for use by the dataset search.  Shards are provided as a string of URLs delimited by commas.  If no shards are provided, then the API will use the shards stored in the file `ESGF_SOLR_SHARDS_XML` in local_settings.py.
```
http://localhost:8000/wget?shards=esgf-node.llnl.gov/solr&dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cl.gr.v20191029|aims3.llnl.gov
```

### File number limit
The parameter `limit` helps control the file limit of the dataset search.  By default, the file limit will come from the variable `WGET_SCRIPT_FILE_DEFAULT_LIMIT` in local_settings.py.  The file limit is ultimately limited by the variable `WGET_SCRIPT_FILE_MAX_LIMIT` in local_settings.py.
```
http://localhost:8000/wget?limit=20000&project=CMIP5
```

### File query result offset
The parameter `offset` is used to control the start index for the list of results from a file query.  By default, the offset is set to 0.  The query below will return the next 100 CMIP6 files after the first 100 files.
```
http://localhost:8000/wget?project=CMIP6&limit=100&offset=100
```

### Simplified script
The parameter `simple` is used to choose whether or not the wget API will produce a simpler version of the download script.  By default, the API will produce a script filled with logic for accepting command line arguments, determining if files have already been downloaded by looking at a cache file, and matching the checksums of downloaded files with those in the script.  By setting `simple=true`, the API will generate a simpler bash script that only has a list of file URLs that will be used with wget.
```
http://localhost:8000/wget?project=CMIP6&limit=100&simple=true
```