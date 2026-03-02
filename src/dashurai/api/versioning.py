from rest_framework.versioning import URLPathVersioning
from rest_framework.response import Response
from rest_framework.views import APIView

class APIVersioning(URLPathVersioning):
    default_version = 'v1'
    allowed_versions = ['v1']
    version_param = 'version'

class APIVersionView(APIView):
    versioning_class = APIVersioning
    
    def get(self, request):
        version = request.version
        return Response({
            'current_version': version,
            'supported_versions': ['v1'],
            'default_version': 'v1',
            'deprecated_versions': [],
            'endpoints': {
                'auth': f'/api/{version}/auth/',
                'careers': f'/api/{version}/careers/',
                'contact': f'/api/{version}/contact/',
                'admin': f'/api/{version}/admin/',
                'content': f'/api/{version}/content/'
            }
        })

def get_api_version_info():
    return {
        'current_version': 'v1',
        'supported_versions': ['v1'],
        'default_version': 'v1',
        'deprecated_versions': []
    }
