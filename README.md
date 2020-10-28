# esgf-wget
Service API endpoint for simplified wget scripts

## Running the API
This API requires Python 3 and Django 3.0.  The required Dango version can be installed from requirements.txt via pip.
```
pip install -r requirements.txt
```
This is ideally done through a virtual environment with virtualenv, or a conda environment using Anaconda Python.

Copy the contents of local_settings_example.py to a file named local_settings.py inside the esgf-wget directory.
```
cd esgf-wget
cp local_settings_example.py local_settings.py
```

Fill out the variables in local_settings.py.  Example below.
```
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '...'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [ 'localhost', '127.0.0.1' ]

# Expand the number of fields allowed for wget API
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1024

# Address of ESGF Solr
ESGF_SOLR_URL = 'localhost/solr'

# Path to XML file containing Solr shards
ESGF_SOLR_SHARDS_XML = '/esg/config/esgf_shards_static.xml'

# Default limit on the number of files allowed in a wget script
WGET_SCRIPT_FILE_DEFAULT_LIMIT = 1000

# Maximum number of files allowed in a wget script
WGET_SCRIPT_FILE_MAX_LIMIT = 100000
```

Run the API using manage.py.
```
python manage.py runserver
```
## How to generate scripts

esgf-wget can use either GET or POST requests for obtaining wget scripts.  Queries are accepted from the `/wget` path.

Select a dataset to collect files from using the parameter `dataset_id`.
```
localhost:8000/wget?dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cl.gr.v20191029|aims3.llnl.gov
```

Multiple datasets can be queried.
```
localhost:8000/wget?dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cl.gr.v20191029|aims3.llnl.gov&dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.cli.gr.v20191029|aims3.llnl.gov&dataset_id=CMIP6.CMIP.E3SM-Project.E3SM-1-1.piControl.r1i1p1f1.Amon.clivi.gr.v20191029|aims3.llnl.gov
```

The parameter `distrib` is used to enable/disable distributed search, where all provided Solr shards are used for the dataset search.  If `distrib=false`, then only a local search of Solr will be performed.  It is set to true by default.
```
localhost:8000/wget?distrib=false&dataset_id=...
```

The parameter `shards` is used to pass specific Solr shards for use by the dataset search.  Shards are provided as a string of URLs delimited by commas.  If no shards are provided, then the API will use the shards stored in the file `ESGF_SOLR_SHARDS_XML` in local_settings.py.
```
localhost:8000/wget?shards=localhost:8993/solr,localhost:8994/solr,localhost:8995/solr&dataset_id=...
```

The parameter `limit` helps control the file limit of the dataset search.  By default, the file limit will come from the variable `WGET_SCRIPT_FILE_DEFAULT_LIMIT` in local_settings.py.  The file limit is ultimately limited by the variable `WGET_SCRIPT_FILE_MAX_LIMIT` in local_settings.py.
```
localhost:8000/wget?limit=20000&dataset_id=...
```