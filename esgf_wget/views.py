
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

import urllib.request
import urllib.parse
import datetime
import json
import re

from esgf_wget.query_utils import *


def home(request):
    return HttpResponse('esgf-wget')


@require_http_methods(['GET', 'POST'])
@csrf_exempt
def generate_wget_script(request):

    query_url = settings.ESGF_SOLR_URL + '/files/select'
    file_limit = settings.WGET_SCRIPT_FILE_DEFAULT_LIMIT
    file_offset = 0
    use_sort = False
    use_distrib = True
    requested_shards = []
    wget_path_facets = []
    wget_empty_path = ''
    script_template_file = 'wget-template.sh'

    xml_shards = get_solr_shards_from_xml()
    allowed_projects = get_allowed_projects_from_json()
    solr_facets = get_facets_from_solr()

    querys = []
    file_query = ['type:File']

    # Gather dataset_ids and other parameters
    if request.method == 'POST':
        url_params = request.POST.copy()
    elif request.method == 'GET':
        url_params = request.GET.copy()
    else:
        return HttpResponseBadRequest('Request method must be POST or GET.')

    # If no parameters were passed to the API,
    # then default to limit=1 and distrib=false
    if len(url_params.keys()) == 0:
        url_params.update(dict(limit=1, distrib='false'))

    # Catch invalid parameters
    for param in url_params.keys():
        if param[-1] == '!':
            param = param[:-1]
        if param not in KEYWORDS \
                and param not in CORE_QUERY_FIELDS \
                and param not in solr_facets:
            msg = 'Invalid HTTP query parameter=%s' % param
            return HttpResponseBadRequest(msg)

    # Catch unsupported fields
    for uf in UNSUPPORTED_FIELDS:
        if url_params.get(uf):
            msg = 'Unsupported parameter: %s' % uf
            return HttpResponseBadRequest(msg)

    # Create list of parameters to be saved in the script
    url_params_list = []
    for param, value_list in url_params.lists():
        for v in value_list:
            url_params_list.append('{}={}'.format(param, v))

    # Set a Solr query string
    if url_params.get(QUERY):
        _query = url_params.pop(QUERY)[0]
        querys.append(_query)

    # Set range for timestamps to query
    if url_params.get(FROM) or url_params.get(TO):
        if url_params.get(FROM):
            timestamp_from = url_params.pop(FROM)[0]
            ts_from = timestamp_from
        else:
            ts_from = '*'
        if url_params.get(TO):
            timestamp_to = url_params.pop(TO)[0]
            ts_to = timestamp_to
        else:
            ts_to = '*'
        timestamp_from_to = "{}:[{} TO {}]".format(FIELD_TIMESTAMP_,
                                                   ts_from, ts_to)
        querys.append(timestamp_from_to)

    # Set datetime start and stop
    if url_params.get(FIELD_START):
        _start = url_params.pop(FIELD_START)[0]
        querys.append("{}:[{} TO *]".format(FIELD_DATETIME_STOP, _start))

    if url_params.get(FIELD_END):
        _end = url_params.pop(FIELD_END)[0]
        querys.append("{}:[* TO {}]".format(FIELD_DATETIME_START, _end))

    # Set version min and max
    if url_params.get(FIELD_MIN_VERSION):
        min_version = url_params.pop(FIELD_MIN_VERSION)[0]
        querys.append("{}:[{} TO *]".format(FIELD_VERSION, min_version))

    if url_params.get(FIELD_MAX_VERSION):
        max_version = url_params.pop(FIELD_MAX_VERSION)[0]
        querys.append("{}:[* TO {}]".format(FIELD_VERSION, max_version))

    # Set bounding box constraint
    if url_params.get(FIELD_BBOX):
        bbox_string = url_params.pop(FIELD_BBOX)[0]
        bbox_search = re.search(r'^\[(.*?),(.*?),(.*?),(.*?)\]$', bbox_string)
        (west, south, east, north) = bbox_search.group(1, 2, 3, 4)
        querys.append('{}:[{} TO *]'.format(FIELD_EAST_DEGREES, west))
        querys.append('{}:[{} TO *]'.format(FIELD_NORTH_DEGREES, south))
        querys.append('{}:[* TO {}]'.format(FIELD_WEST_DEGREES, east))
        querys.append('{}:[* TO {}]'.format(FIELD_SOUTH_DEGREES, north))

    if len(querys) == 0:
        querys.append('*:*')
    query_string = ' AND '.join(querys)

    # Create a simplified script that only runs wget on a list of files
    if url_params.get(SIMPLE):
        use_simple_param = url_params.pop(SIMPLE)[0].lower()
        if use_simple_param == 'false':
            script_template_file = 'wget-template.sh'
        elif use_simple_param == 'true':
            script_template_file = 'wget-simple-template.sh'
        else:
            msg = 'Parameter \"%s\" must be set to true or false.' % SIMPLE
            return HttpResponseBadRequest(msg)

    # Enable distributed search
    if url_params.get(DISTRIB):
        use_distrib_param = url_params.pop(DISTRIB)[0].lower()
        if use_distrib_param == 'false':
            use_distrib = False
        elif use_distrib_param == 'true':
            use_distrib = True
        else:
            msg = 'Parameter \"%s\" must be set to true or false.' % DISTRIB
            return HttpResponseBadRequest(msg)

    # Enable sorting of records
    if url_params.get(SORT):
        use_sort_param = url_params.pop(SORT)[0].lower()
        if use_sort_param == 'false':
            use_sort = False
        elif use_sort_param == 'true':
            use_sort = True
        else:
            msg = 'Parameter \"%s\" must be set to true or false.' % SORT
            return HttpResponseBadRequest(msg)

    # Use Solr shards requested from GET/POST
    if url_params.get(SHARDS):
        requested_shards = url_params.pop(SHARDS)[0].split(',')

    # Set file number limit within a set maximum number
    if url_params.get(LIMIT):
        file_limit = int(url_params.pop(LIMIT)[0])
    file_limit = min(file_limit, settings.WGET_SCRIPT_FILE_MAX_LIMIT)

    # Set the starting index for the returned records from the query
    if url_params.get(OFFSET):
        file_offset = int(url_params.pop(OFFSET)[0])

    # Set boolean constraints
    boolean_constraints = [FIELD_LATEST, FIELD_RETRACTED, FIELD_REPLICA]
    for bc in boolean_constraints:
        if url_params.get(bc):
            bc_value = url_params.pop(bc)[0].lower()
            if bc_value == 'false' or bc_value == 'true':
                file_query.append('%s:%s' % (bc, bc_value))
            else:
                msg = 'Parameter \"%s\" must be set to true or false.' % bc
                return HttpResponseBadRequest(msg)

    # Get directory structure for downloaded files
    if url_params.get(FIELD_WGET_PATH):
        wget_path_facets = url_params.pop(FIELD_WGET_PATH)[0].split(',')

    if url_params.get(FIELD_WGET_EMPTYPATH):
        wget_empty_path = url_params.pop(FIELD_WGET_EMPTYPATH)[0]

    # Collect remaining constraints
    for param, value_list in url_params.lists():
        # Check for negative constraints
        if param[-1] == '!':
            param = '-' + param[:-1]

        # Split values separated by commas
        # but don't split at commas inside parentheses
        # (i.e. cases such as "CESM1(CAM5.1,FV2)")
        split_value_list = []
        for v in value_list:
            for sv in split_value(v):
                split_value_list.append(sv)

        # If dataset_id values were passed
        # then check if they follow the expected pattern
        # (i.e. <facet1>.<facet2>...<facetn>.v<version>|<data_node>)
        if param == FIELD_DATASET_ID:
            id_pat = r'^[-\w]+(\.[-\w]+)*\.v\d{8}\|[-\w]+(\.[-\w]+)*$'
            id_regex = re.compile(id_pat)
            msg = 'The dataset_id, {id}, does not follow the format of ' \
                  '<facet1>.<facet2>...<facetn>.v<version>|<data_node>'
            for v in split_value_list:
                if not id_regex.match(v):
                    return HttpResponseBadRequest(msg.format(id=v))

        # If the list of allowed projects is not empty,
        # then check if the query is accessing projects not in the list
        if allowed_projects:
            msg = 'This query cannot be completed since the project, ' \
                  '{project}, is not allowed to be accessed by this site. ' \
                  'Please redo your query with unrestricted data only, ' \
                  'and request {project} data from another site.'
            # Check project parameter
            if param in [FIELD_PROJECT]:
                for v in split_value_list:
                    if v not in allowed_projects:
                        return HttpResponseBadRequest(msg.format(project=v))
            # Check ID parameters
            projects_lower = [x.lower() for x in allowed_projects]
            if param in ID_FIELDS:
                for v in split_value_list:
                    p = v.split('.')[0]
                    if p.lower() not in projects_lower:
                        return HttpResponseBadRequest(msg.format(project=p))

        if len(split_value_list) == 1:
            fq = '{}:{}'.format(param, split_value_list[0])
        else:
            fq = '{}:({})'.format(param, ' || '.join(split_value_list))
        file_query.append(fq)

    # If the projects were not passed and the allowed projects list exists,
    # then use the allowed projects as the project query
    if not url_params.get(FIELD_PROJECT) and allowed_projects:
        if len(allowed_projects) == 1:
            fq = '{}:{}'.format(FIELD_PROJECT, allowed_projects[0])
        else:
            fq = '{}:({})'.format(FIELD_PROJECT, ' || '.join(allowed_projects))
        file_query.append(fq)

    # Get facets for the file name, URL, checksum
    file_attribute_set = set(['title', 'url', 'checksum_type', 'checksum'])

    # Get facets for the download directory structure,
    # and remove duplicate facets
    file_attribute_set = file_attribute_set.union(set(wget_path_facets))
    file_attributes = list(file_attribute_set)

    # Solr query parameters
    query_params = dict(q=query_string,
                        wt='json',
                        facet='true',
                        fl=file_attributes,
                        fq=file_query,
                        start=file_offset,
                        limit=file_limit,
                        rows=file_limit)

    # Sort by timestamp descending if enabled, otherwise sort by id ascending
    if use_sort:
        query_params.update(dict(sort='_timestamp desc'))
    else:
        query_params.update(dict(sort='id asc'))

    # Use shards for distributed search if 'distrib' is true,
    # otherwise use only local search
    if use_distrib:
        if len(requested_shards) > 0:
            shards = ','.join([s + '/files' for s in requested_shards])
            query_params.update(dict(shards=shards))
        elif len(xml_shards) > 0:
            shards = ','.join([s + '/files' for s in xml_shards])
            query_params.update(dict(shards=shards))

    # Fetch files for the query
    file_list = {}
    query_encoded = urllib.parse.urlencode(query_params, doseq=True).encode()
    req = urllib.request.Request(query_url, query_encoded)
    with urllib.request.urlopen(req) as response:
        results = json.loads(response.read().decode())

    num_files = results['response']['numFound']
    for file_info in results['response']['docs']:
        filename = file_info['title']
        checksum_type = file_info['checksum_type'][0]
        checksum = file_info['checksum'][0]
        # Create directory structure from facet values
        # If the facet is not found, then use the empty path value
        dir_struct = []
        for facet in wget_path_facets:
            facet_value = wget_empty_path
            if facet in file_info:
                if isinstance(file_info[facet], list):
                    facet_value = file_info[facet][0]
                else:
                    facet_value = file_info[facet]
            # Prevent strange values while generating names
            facet_value = facet_value.replace("['<>?*\"\n\t\r\0]", "")
            facet_value = facet_value.replace("[ /\\\\|:;]+", "_")
            # Limit length of value to WGET_MAX_DIR_LENGTH
            if len(facet_value) > settings.WGET_MAX_DIR_LENGTH:
                facet_value = facet_value[:settings.WGET_MAX_DIR_LENGTH]
            dir_struct.append(facet_value)
        dir_struct.append(filename)
        file_path = os.path.join(*dir_struct)
        # Only add a file to the list if its file path is not already present
        if file_path not in file_list:
            for url in file_info['url']:
                url_split = url.split('|')
                if url_split[2] == 'HTTPServer':
                    file_entry = dict(url=url_split[0],
                                      checksum_type=checksum_type,
                                      checksum=checksum)
                    file_list[file_path] = file_entry
                    break

    # Limit the number of files to the maximum
    warning_message = None
    if num_files == 0:
        return HttpResponse('No files found for datasets.')
    elif num_files > file_limit:
        warning_message = 'Warning! The total number of files was {} ' \
                          'but this script will only process {}.' \
                          .format(num_files, file_limit)

    # Warning message about files that were skipped
    # to prevent overwriting similarly-named files.
    skip_msg = 'There were files with the same name which were requested ' \
               'to be download to the same directory. To avoid overwriting ' \
               'the previous downloaded one they were skipped.\n' \
               'Please use the parameter \'download_structure\' ' \
               'to set up unique directories for them.'
    if min(num_files, file_limit) > len(file_list):
        if warning_message:
            warning_message = '{}\n{}'.format(warning_message, skip_msg)
        else:
            warning_message = skip_msg

    # Build wget script
    current_datetime = datetime.datetime.now()
    timestamp = current_datetime.strftime('%Y/%m/%d %H:%M:%S')

    context = dict(timestamp=timestamp,
                   url_params=url_params_list,
                   files=file_list,
                   warning_message=warning_message)
    wget_script = render(request, script_template_file, context)

    script_filename = current_datetime.strftime('wget-%Y%m%d%H%M%S.sh')
    response_content = 'attachment; filename={}'.format(script_filename)

    response = HttpResponse(wget_script, content_type='text/x-sh')
    response['Content-Disposition'] = response_content
    return response
