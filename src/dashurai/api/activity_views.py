from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema
from django.db import DatabaseError
from .activity_service import get_recent_activities, activity_to_dict, create_activity
from .activity_serializers import ActivitySerializer, ActivityListSerializer
from .views import api_response


class ActivityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ActivityListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ActivityPagination

    @extend_schema(
        tags=['Activities'],
        responses={
            200: ActivityListSerializer,
            401: {'description': 'Unauthorized'},
            500: {'description': 'Internal server error'}
        },
        summary='Get Activities',
        description='Get paginated list of recent activities'
    )
    def get(self, request):
        try:
            page_size = int(request.GET.get('page_size', 20))
            limit = min(page_size, 100)  # Cap at 100 for safety
            
            activities = get_recent_activities(limit=limit)
            paginator = self.pagination_class()
            paginated_activities = paginator.paginate_queryset(
                [activity_to_dict(activity) for activity in activities], 
                request
            )
            
            return paginator.get_paginated_response({
                'activities': paginated_activities
            })
            
        except (ValueError, TypeError) as e:
            return api_response(success=False, message='Invalid parameters', status_code=status.HTTP_400_BAD_REQUEST)
            
        except DatabaseError as e:
            return api_response(success=False, message='Database error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return api_response(success=False, message='Internal server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActivityStreamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Activities'],
        responses={
            200: ActivityListSerializer,
            401: {'description': 'Unauthorized'},
            500: {'description': 'Internal server error'}
        },
        summary='Get Activity Stream',
        description='Get stream of recent activities'
    )
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 50))
            limit = min(limit, 200)  # Cap at 200 for performance
            
            activities = get_recent_activities(limit=limit)
            activities_data = [activity_to_dict(activity) for activity in activities]
            
            return api_response(data={
                'activities': activities_data,
                'count': len(activities_data)
            })
            
        except (ValueError, TypeError) as e:
            return api_response(success=False, message='Invalid parameters', status_code=status.HTTP_400_BAD_REQUEST)
            
        except DatabaseError as e:
            return api_response(success=False, message='Database error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return api_response(success=False, message='Internal server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_and_broadcast_activity(activity_type: str, action: str, description: str):
    try:
        activity = create_activity(activity_type, action, description)
        if activity:
            # In a real implementation, this would broadcast via WebSocket
            # For now, we just create the activity record
            return activity
        return None
    except Exception as e:
        # Log the error but don't break the main functionality
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create and broadcast activity: {e}")
        return None
