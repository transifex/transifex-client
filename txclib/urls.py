# These are the Transifex API urls

API_URLS = {
    'get_resources': '%(hostname)s/api/2/project/%(project)s/resources/',
    'project_details': '%(hostname)s/api/2/project/%(project)s/?details',
    'resource_details': '%(hostname)s/api/2/project/%(project)s/resource/%(resource)s/',
    'release_details': '%(hostname)s/api/project/%(project)s/release/%(release)s/',
    'push_file': '%(hostname)s/api/storage/',  #'%(hostname)s/api/project/%(project)s/files/',
    'pull_file': '%(hostname)s/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file',
    'extract_translation': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/',
    'extract_source': '%(hostname)s/api/project/%(project)s/files/',  #'%(hostname)s/api/project/%(project)s/files/',
    'resource_stats': '%(hostname)s/api/2/project/%(project)s/resource/%(resource)s/stats/',
    'delete_translation': '%(hostname)s/api/project/%(project)s/resource/%(resource)s/%(language)s/file/',
    'push_source': '%(hostname)s/api/2/project/%(project)s/resource/%(resource)s/content/',
}


