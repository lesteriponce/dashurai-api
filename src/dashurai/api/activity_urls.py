from django.urls import path
from .activity_views import ActivityListView, ActivityStreamView

app_name = 'activities'

urlpatterns = [
    path('activities/', ActivityListView.as_view(), name='activity-list'),
    path('activities/stream/', ActivityStreamView.as_view(), name='activity-stream'),
]