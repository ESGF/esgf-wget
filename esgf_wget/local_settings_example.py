

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Address of ESGF Solr
ESGF_SOLR_URL = ''

# Path to XML file containing Solr shards
ESGF_SOLR_SHARDS_XML = ''

# Default limit on the number of files allowed in a wget script
WGET_SCRIPT_FILE_DEFAULT_LIMIT = 1000

# Maximum number of files allowed in a wget script
WGET_SCRIPT_FILE_MAX_LIMIT = 100000

# Maximum length for facet values used in the wget directory structure
WGET_MAX_DIR_LENGTH = 50