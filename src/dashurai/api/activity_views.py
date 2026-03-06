from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse, OpenApiTypes
from django.db import DatabaseError
from .activity_service import get_recent_activities, activity_to_dict
from .activity_serializers import ActivitySerializer, ActivityListSerializer


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
            401: OpenApiResponse(description='Unauthorized'),
            500: OpenApiResponse(description='Internal server error')
        }
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
            return Response({
                'error': 'Invalid parameters',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except DatabaseError as e:
            return Response({
                'error': 'Database error',
                'details': 'Failed to retrieve activities'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'error': 'Internal server error',
                'details': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActivityStreamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Activities'],
        responses={
            200: ActivityListSerializer,
            401: OpenApiResponse(description='Unauthorized'),
            500: OpenApiResponse(description='Internal server error')
        }
    )
    def get(self, request):
        try:
            limit = int(request.GET.get('limit', 50))
            limit = min(limit, 200)  # Cap at 200 for performance
            
            activities = get_recent_activities(limit=limit)
            activities_data = [activity_to_dict(activity) for activity in activities]
            
            return Response({
                'activities': activities_data,
                'count': len(activities_data)
            }, status=status.HTTP_200_OK)
            
        except (ValueError, TypeError) as e:
            return Response({
                'error': 'Invalid parameters',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except DatabaseError as e:
            return Response({
                'error': 'Database error',
                'details': 'Failed to retrieve activity stream'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'error': 'Internal server error',
                'details': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
