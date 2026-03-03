from rest_framework.versioning import URLPathVersioning
from rest_framework.response import Response

class APIVersioning(URLPathVersioning):
    default_version = 'v1'
    allowed_versions = ['v1']
    version_param = 'version'

def get_api_version_info():
    return {
        'current_version': 'v1',
        'supported_versions': ['v1'],
        'default_version': 'v1',
        'deprecated_versions': []
    }
