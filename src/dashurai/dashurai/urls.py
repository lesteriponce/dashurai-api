from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtail_docs_urls
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from drf_spectacular.utils import extend_schema

def cms_redirect_view(request):
    return HttpResponseRedirect('/cms/admin/')

class ManualSchemaView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'openapi': '3.0.0',
            'info': {
                'title': 'DashurAI API',
                'description': 'Django REST API with Wagtail CMS integration for managing careers, contact forms, and content management.',
                'version': '1.0.0'
            },
            'servers': [
                {'url': 'http://localhost:8003', 'description': 'Development server'},
                {'url': 'https://api.dashurai.com', 'description': 'Production server'},
            ],
            'paths': {
                '/api/v1/': {
                    'get': {
                        'summary': 'Get API version information',
                        'tags': ['API'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/auth/login/': {
                    'post': {
                        'summary': 'User login',
                        'tags': ['Authentication'],
                        'responses': {'200': {'description': 'Login successful'}}
                    }
                },
                '/api/v1/auth/register/': {
                    'post': {
                        'summary': 'User registration',
                        'tags': ['Authentication'],
                        'responses': {'201': {'description': 'Registration successful'}}
                    }
                },
                '/api/v1/admin/dashboard/': {
                    'get': {
                        'summary': 'Admin dashboard',
                        'tags': ['Admin'],
                        'responses': {'200': {'description': 'Dashboard data retrieved'}}
                    }
                },
                '/api/v1/auth/refresh/': {
                    'post': {
                        'summary': 'Refresh JWT token',
                        'tags': ['Authentication'],
                        'responses': {'200': {'description': 'Token refreshed successfully'}}
                    }
                },
                '/api/v1/admin/login/': {
                    'post': {
                        'summary': 'Admin login',
                        'tags': ['Authentication'],
                        'responses': {'200': {'description': 'Admin login successful'}}
                    }
                },
                '/api/v1/careers/positions/': {
                    'get': {
                        'summary': 'List active positions',
                        'tags': ['Careers'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/careers/positions/{pk}/': {
                    'get': {
                        'summary': 'Get position details',
                        'tags': ['Careers'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/careers/apply/': {
                    'post': {
                        'summary': 'Apply for job',
                        'tags': ['Careers'],
                        'responses': {'201': {'description': 'Application submitted successfully'}}
                    }
                },
                '/api/v1/contact/submit/': {
                    'post': {
                        'summary': 'Submit contact form',
                        'tags': ['Contact'],
                        'responses': {'201': {'description': 'Contact form submitted successfully'}}
                    }
                },
                '/api/v1/content/documents/': {
                    'get': {
                        'summary': 'List documents',
                        'tags': ['CMS - Documents'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/documents/{pk}/': {
                    'get': {
                        'summary': 'Get document detail',
                        'tags': ['CMS - Documents'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/documents/find/': {
                    'get': {
                        'summary': 'Find documents',
                        'tags': ['CMS - Documents'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/images/': {
                    'get': {
                        'summary': 'List images',
                        'tags': ['CMS - Images'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/images/{pk}/': {
                    'get': {
                        'summary': 'Get image detail',
                        'tags': ['CMS - Images'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/images/find/': {
                    'get': {
                        'summary': 'Find images',
                        'tags': ['CMS - Images'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/pages/': {
                    'get': {
                        'summary': 'List pages',
                        'tags': ['CMS - Pages'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/pages/{pk}/': {
                    'get': {
                        'summary': 'Get page detail',
                        'tags': ['CMS - Pages'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/pages/find/': {
                    'get': {
                        'summary': 'Find pages',
                        'tags': ['CMS - Pages'],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/content/pages/{pk}/action/{action_name}/': {
                    'post': {
                        'summary': 'Execute page action',
                        'tags': ['CMS - Pages'],
                        'responses': {'200': {'description': 'Page action completed successfully'}}
                    }
                },
                '/api/v1/admin/applications/': {
                    'get': {
                        'summary': 'List all applications (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/admin/applications/{pk}/': {
                    'put': {
                        'summary': 'Update application (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Application updated successfully'}}
                    }
                },
                '/api/v1/admin/applications/{pk}/delete/': {
                    'delete': {
                        'summary': 'Delete application (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Application deleted successfully'}}
                    }
                },
                '/api/v1/admin/contacts/': {
                    'get': {
                        'summary': 'List all contacts (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/admin/contacts/{pk}/': {
                    'put': {
                        'summary': 'Update contact (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Contact updated successfully'}}
                    }
                },
                '/api/v1/admin/contacts/{pk}/delete/': {
                    'delete': {
                        'summary': 'Delete contact (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Contact deleted successfully'}}
                    }
                },
                '/api/v1/admin/positions/': {
                    'get': {
                        'summary': 'List all positions (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Successful response'}}
                    }
                },
                '/api/v1/admin/positions/create/': {
                    'post': {
                        'summary': 'Create position (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'201': {'description': 'Position created successfully'}}
                    }
                },
                '/api/v1/admin/positions/{pk}/': {
                    'put': {
                        'summary': 'Update position (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Position updated successfully'}}
                    }
                },
                '/api/v1/admin/positions/{pk}/delete/': {
                    'delete': {
                        'summary': 'Delete position (admin only)',
                        'tags': ['Admin'],
                        'security': [{'bearerAuth': []}],
                        'responses': {'200': {'description': 'Position deleted successfully'}}
                    }
                }
            },
            'components': {
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    }
                }
            },
            'tags': [
                {'name': 'API', 'description': 'API version and metadata information'},
                {'name': 'Authentication', 'description': 'User and admin authentication endpoints'},
                {'name': 'Careers', 'description': 'Job positions and application management'},
                {'name': 'Contact', 'description': 'Contact form submissions'},
                {'name': 'Admin', 'description': 'Administrative operations (requires admin access)'},
                {'name': 'CMS - Documents', 'description': 'Document management and retrieval'},
                {'name': 'CMS - Images', 'description': 'Image management and retrieval'},
                {'name': 'CMS - Pages', 'description': 'Page management and actions'}
            ]
        })

urlpatterns = [
    # API Documentation
    path('api/schema/', ManualSchemaView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API 
    path('api/', include('api.urls')),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Wagtail CMS
    path('cms/', cms_redirect_view, name='cms_redirect'),
    path('cms/admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtail_docs_urls)),
    path('', include(wagtail_urls)),
]

# media and static files 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
