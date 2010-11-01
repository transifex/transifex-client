# These are the Transifex API urls

API_URLS = {
    'get_resources': '%(hostname)s/api/project/%(project)s/resources/',
    'project_details': '%(hostname)s/api/project/%(project)s/',
    'resource_details': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/',
    'release_details': '%(hostname)s/api/project/%(project)s/release/%(release)s/',
    'push_file': '%(hostname)s/api/storage/',  #'%(hostname)s/api/project/%(project)s/files/',
    'pull_file': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/file/',
    'extract_translation': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/',
    'extract_source': '%(hostname)s/api/project/%(project)s/files/',  #'%(hostname)s/api/project/%(project)s/files/',
    'resource_stats': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/stats/%(language)s/',
}


