from django.urls import path, include
from .v1 import urls as v1_urls

app_name = 'api'

urlpatterns = [
    # API Version 1
    path('v1/', include(v1_urls)),
]
