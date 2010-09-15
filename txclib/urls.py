# These are the Transifex API urls

API_URLS = {
    'project_get' : '%(hostname)s/api/project/%(project)s/',
    'get_resources': '%(hostname)s/api/project/%(project)s/resources/',
    'get_resource_details': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/',
    'push_file': '%(hostname)s/api/storage/',  #'%(hostname)s/api/project/%(project)s/files/',
    'pull_file': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/file/',
    'extract_translation': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/',
    'extract_source': '%(hostname)s/api/project/%(project)s/files/',  #'%(hostname)s/api/project/%(project)s/files/',
    'resource_stats': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/stats/%(language)s/',
}


