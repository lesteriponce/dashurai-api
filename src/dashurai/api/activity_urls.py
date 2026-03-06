"""
URL configuration for Activity endpoints.
Includes both REST API and Server-Sent Events routes.
"""

from django.urls import path
from .activity_views import ActivityListView, ActivityStreamView

app_name = 'activities'

urlpatterns = [
    path('activities/', ActivityListView.as_view(), name='activity-list'),
    path('activities/stream/', ActivityStreamView.as_view(), name='activity-stream'),
]
