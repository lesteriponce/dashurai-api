from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError, models
from django.http import HttpResponse, Http404
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiRequest, OpenApiResponse, OpenApiTypes
from django_ratelimit.decorators import ratelimit
from .versioning import get_api_version_info
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    PositionSerializer, JobApplicationSerializer, ContactSubmissionSerializer,
    AdminLoginSerializer, DashboardStatsSerializer
)
from cms.serializers import DocumentSerializer, ImageSerializer, PageSerializer
from users.models import User
from careers.models import Position, JobApplication
from contact.models import ContactSubmission
from cms.models import Document, Image, Page

# API Version View
@extend_schema(
    tags=['API'],
    responses={
        200: OpenApiResponse(
            description='API version information',
            response=OpenApiTypes.OBJECT,
            examples={
                'application/json': {
                    'current_version': 'v1',
                    'supported_versions': ['v1'],
                    'default_version': 'v1',
                    'deprecated_versions': [],
                    'endpoints': {
                        'auth': '/api/v1/auth/',
                        'careers': '/api/v1/careers/',
                        'contact': '/api/v1/contact/',
                        'admin': '/api/v1/admin/',
                        'content': '/api/v1/content/'
                    }
                }
            }
        )
    },
    summary="Get API version information",
    description="Returns current API version and available endpoints"
)
class APIVersionView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        version_info = get_api_version_info()
        version = version_info['current_version']
        return Response({
            'current_version': version,
            'supported_versions': version_info['supported_versions'],
            'default_version': version_info['default_version'],
            'deprecated_versions': version_info['deprecated_versions'],
            'endpoints': {
                'auth': f'/api/{version}/auth/',
                'careers': f'/api/{version}/careers/',
                'contact': f'/api/{version}/contact/',
                'admin': f'/api/{version}/admin/',
                'content': f'/api/{version}/content/'
            }
        })

# Helper function for consistent response format
def api_response(success=True, data=None, message=None, status_code=status.HTTP_200_OK):
    if success:
        return Response({'success': True, 'data': data}, status=status_code)
    else:
        # Handle both string messages and dictionary errors
        if isinstance(message, dict):
            return Response({'success': False, 'errors': message}, status=status_code)
        else:
            return Response({'success': False, 'message': message}, status=status_code)

# Authentication Views
@extend_schema(
    tags=['Authentication'],
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(description='Login successful', response=UserSerializer),
        401: OpenApiResponse(description='Invalid credentials')
    },
    summary="User login",
    description="Authenticate user and return JWT tokens"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login(request):
    # return JWT tokens
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return api_response(data={
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    return api_response(success=False, message='Invalid credentials', status_code=status.HTTP_401_UNAUTHORIZED)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        tags=['Authentication'],
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='Registration successful'),
            400: OpenApiResponse(description='Bad request - validation errors')
        }
    )
    @ratelimit(key='ip', rate='3/m', method='POST', block=True)
    def post(self, request):
        # register a new user account
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return api_response(data={'message': 'Registration successful'}, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Authentication'],
    request={'refresh': {'type': 'string', 'example': 'refresh_token_here'}},
    responses={
        200: OpenApiResponse(description='Token refreshed successfully'),
        401: OpenApiResponse(description='Invalid refresh token'),
        400: OpenApiResponse(description='Refresh token required')
    },
    summary="Refresh JWT token",
    description="Get new access token using refresh token"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def refresh_token(request):
    # Refresh JWT token 
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return api_response(success=False, message='Refresh token required', status_code=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        return api_response(data={'access': str(refresh.access_token)})
    except (TokenError, InvalidToken) as e:
        return api_response(success=False, message='Invalid or expired refresh token', status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return api_response(success=False, message='Token refresh failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    request={'refresh': {'type': 'string', 'example': 'refresh_token_here'}},
    responses={
        200: OpenApiResponse(description='Logout successful'),
        400: OpenApiResponse(description='Refresh token required'),
        401: OpenApiResponse(description='Invalid refresh token')
    },
    summary="User logout",
    description="Invalidate refresh token to logout user"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/m', method='POST', block=True)
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return api_response(success=False, message='Refresh token required', status_code=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        refresh.blacklist()
        return api_response(data={'message': 'Logout successful'})
    except (TokenError, InvalidToken) as e:
        return api_response(success=False, message='Invalid or expired refresh token', status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return api_response(success=False, message='Logout failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Authentication required')
    },
    summary="Get current user",
    description="Get current authenticated user information"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='30/m', method='GET', block=True)
def get_current_user(request):
    try:
        serializer = UserSerializer(request.user)
        return api_response(data=serializer.data)
    except Exception as e:
        return api_response(success=False, message='Failed to retrieve user information', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    request=UserSerializer,
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        401: OpenApiResponse(description='Authentication required')
    },
    summary="Update current user",
    description="Update current authenticated user information"
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/m', method='PATCH', block=True)
def update_current_user(request):
    try:
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return api_response(success=False, message='Failed to update user information', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Authentication'],
    request=AdminLoginSerializer,
    responses={
        200: OpenApiResponse(description='Admin login successful', response=UserSerializer),
        401: OpenApiResponse(description='Invalid admin credentials')
    },
    summary="Admin login",
    description="Authenticate admin user and return JWT tokens"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def admin_login(request):
    # Admin loginand return JWT tokens
    serializer = AdminLoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return api_response(data={
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    return api_response(success=False, message='Invalid admin credentials', status_code=status.HTTP_401_UNAUTHORIZED)

# Dashboard view for admin stats
@extend_schema(
    tags=['Admin'],
    responses={
        200: DashboardStatsSerializer
    },
    summary="Admin Dashboard",
    description="Get admin dashboard statistics"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='10/m', method='GET', block=True)
def admin_dashboard(request):
    try:
        total_applications = JobApplication.objects.count()
        total_contacts = ContactSubmission.objects.count()
        total_positions = Position.objects.count()
        active_positions = Position.objects.filter(status='active').count()
        
        serializer = DashboardStatsSerializer ({
            'total_applications': total_applications,
            'total_contacts': total_contacts,
            'total_positions': total_positions,
            'active_positions': active_positions,
        })
        
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Database error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message=f"Internal server error: {str(e)}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Career Views
@extend_schema(
    tags=['Careers'],
    responses={
        200: PositionSerializer(many=True)
    },
    summary="List active positions",
    description="Get list of all active job positions"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def positions_list(request):
    try:
        positions = Position.objects.filter(status='active')
        serializer = PositionSerializer(positions, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve positions', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Careers'],
    responses={
        200: PositionSerializer,
        404: OpenApiResponse(description='Position not found')
    },
    summary="Get position details",
    description="Get detailed information about a specific position"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def position_detail(request, pk):
    try:
        position = get_object_or_404(Position, pk=pk, status='active')
        serializer = PositionSerializer(position)
        return api_response(data=serializer.data)
    except Position.DoesNotExist:
        return api_response(success=False, message='Position not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve position', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Careers'],
    request=JobApplicationSerializer,
    responses={
        201: OpenApiResponse(description='Application submitted successfully'),
        400: OpenApiResponse(description='Bad request - validation errors')
    },
    summary="Apply for job",
    description="Submit a job application"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def apply_job(request):
    try:
        serializer = JobApplicationSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            return api_response(data={'message': 'Application submitted successfully', 'application_id': str(application.id)}, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to submit application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Application submission failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Careers'],
    responses={
        200: JobApplicationSerializer,
        404: OpenApiResponse(description='Application not found')
    },
    summary="Get application status",
    description="Get application status for applicant (optional)"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='10/m', method='GET', block=True)
def get_application_status(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        # Return limited information for applicants
        serializer = JobApplicationSerializer(application)
        data = serializer.data
        # Only include status-related fields for privacy
        limited_data = {
            'id': data['id'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'email': data['email'],
            'position': data['position'],
            'status': data['status'],
            'applied_at': data['applied_at'],
            'updated_at': data['updated_at']
        }
        return api_response(data=limited_data)
    except JobApplication.DoesNotExist:
        return api_response(success=False, message='Application not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Contact Views
@extend_schema(
    tags=['Contact'],
    request=ContactSubmissionSerializer,
    responses={
        201: OpenApiResponse(description='Contact form submitted successfully'),
        400: OpenApiResponse(description='Bad request - validation errors')
    },
    summary="Submit contact form",
    description="Submit a contact inquiry"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='2/m', method='POST', block=True)
def contact_submit(request):
    try:
        serializer = ContactSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data={'message': 'Contact form submitted successfully'}, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to submit contact form', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Contact submission failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views - Applications
@extend_schema(
    tags=['Admin'],
    responses={
        200: JobApplicationSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all applications",
    description="Get list of all job applications (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_applications(request):
    try:
        applications = JobApplication.objects.all()
        
        # Search by name or email
        search = request.GET.get('search', '')
        if search:
            applications = applications.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(position__title__icontains=search)
            )
        
        # Filter by status
        status = request.GET.get('status', '')
        if status:
            applications = applications.filter(status=status)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    applications = applications.filter(applied_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    applications = applications.filter(applied_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        applications = applications.order_by('-applied_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(applications, request)
        
        serializer = JobApplicationSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve applications', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    responses={
        200: JobApplicationSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Application not found')
    },
    summary="Get application detail",
    description="Get detailed information about a specific job application (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_application_detail(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        serializer = JobApplicationSerializer(application)
        return api_response(data=serializer.data)
    except JobApplication.DoesNotExist:
        return api_response(success=False, message='Application not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    request=JobApplicationSerializer,
    responses={
        200: JobApplicationSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        404: OpenApiResponse(description='Application not found')
    },
    summary="Update application",
    description="Update job application status or details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_update_application(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        serializer = JobApplicationSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except JobApplication.DoesNotExist:
        return api_response(success=False, message='Application not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to update application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    responses={
        200: OpenApiResponse(description='Application deleted successfully'),
        404: OpenApiResponse(description='Application not found')
    },
    summary="Delete application",
    description="Delete a job application (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_application(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        application.delete()
        return api_response(data={'message': 'Application deleted successfully'})
    except JobApplication.DoesNotExist:
        return api_response(success=False, message='Application not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    responses={
        200: OpenApiResponse(description='Resume file downloaded successfully'),
        404: OpenApiResponse(description='Application not found or no resume file'),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="Download application resume",
    description="Download resume file for a job application (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_download_resume(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        
        if not application.resume:
            return api_response(success=False, message='No resume file found for this application', status_code=status.HTTP_404_NOT_FOUND)
        
        try:
            resume_file = application.resume
            response = HttpResponse(resume_file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{resume_file.name.split("/")[-1]}"'
            response['Content-Length'] = resume_file.size
            return response
        except FileNotFoundError:
            return api_response(success=False, message='Resume file not found on server', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return api_response(success=False, message='Failed to read resume file', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except JobApplication.DoesNotExist:
        return api_response(success=False, message='Application not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views - Contacts
@extend_schema(
    tags=['Admin'],
    responses={
        200: ContactSubmissionSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all contacts",
    description="Get list of all contact submissions (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contacts(request):
    try:
        contacts = ContactSubmission.objects.all()
        
        # Search by name, email, or subject
        search = request.GET.get('search', '')
        if search:
            contacts = contacts.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(subject__icontains=search)
            )
        
        # Filter by status
        status = request.GET.get('status', '')
        if status:
            contacts = contacts.filter(status=status)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    contacts = contacts.filter(submitted_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    contacts = contacts.filter(submitted_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        contacts = contacts.order_by('-submitted_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(contacts, request)
        
        serializer = ContactSubmissionSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve contacts', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    responses={
        200: ContactSubmissionSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Contact not found')
    },
    summary="Get contact detail",
    description="Get detailed information about a specific contact submission (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contact_detail(request, pk):
    try:
        contact = get_object_or_404(ContactSubmission, pk=pk)
        serializer = ContactSubmissionSerializer(contact)
        return api_response(data=serializer.data)
    except ContactSubmission.DoesNotExist:
        return api_response(success=False, message='Contact not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve contact', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    request=ContactSubmissionSerializer,
    responses={
        200: ContactSubmissionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Contact not found')
    },
    summary="Update contact",
    description="Update contact submission details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_update_contact(request, pk):
    # Update contact
    contact = get_object_or_404(ContactSubmission, pk=pk)
    serializer = ContactSubmissionSerializer(contact, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Admin'],
    responses={
        200: OpenApiResponse(description='Contact deleted successfully'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Contact not found')
    },
    summary="Delete contact",
    description="Delete a contact submission (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_contact(request, pk):
    # Delete contact
    contact = get_object_or_404(ContactSubmission, pk=pk)
    contact.delete()
    return api_response(data={'message': 'Contact deleted successfully'})

# Admin Views - Positions
@extend_schema(
    tags=['Admin'],
    responses={
        200: PositionSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all positions",
    description="Get list of all positions including inactive ones (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_positions(request):
    try:
        positions = Position.objects.all()
        
        # Search by title or department
        search = request.GET.get('search', '')
        if search:
            positions = positions.filter(
                models.Q(title__icontains=search) |
                models.Q(department__icontains=search)
            )
        
        # Filter by status
        status = request.GET.get('status', '')
        if status:
            positions = positions.filter(status=status)
        
        # Filter by type
        type_filter = request.GET.get('type', '')
        if type_filter:
            positions = positions.filter(type=type_filter)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    positions = positions.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    positions = positions.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        positions = positions.order_by('-created_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(positions, request)
        
        serializer = PositionSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve positions', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    responses={
        200: PositionSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Position not found')
    },
    summary="Get position detail",
    description="Get detailed information about a specific position (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_position_detail(request, pk):
    try:
        position = get_object_or_404(Position, pk=pk)
        serializer = PositionSerializer(position)
        return api_response(data=serializer.data)
    except Position.DoesNotExist:
        return api_response(success=False, message='Position not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve position', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin'],
    request=PositionSerializer,
    responses={
        201: PositionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="Create position",
    description="Create a new job position (admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_position(request):
    serializer = PositionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Admin'],
    request=PositionSerializer,
    responses={
        200: PositionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Position not found')
    },
    summary="Update position",
    description="Update job position details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_update_position(request, pk):
    # update job position details (admin only)
    position = get_object_or_404(Position, pk=pk)
    serializer = PositionSerializer(position, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=['Admin'],
    responses={
        200: OpenApiResponse(description='Position deleted successfully'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Position not found')
    },
    summary="Delete position",
    description="Delete a job position (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_position(request, pk):
    # delete admin only
    position = get_object_or_404(Position, pk=pk)
    position.delete()
    return api_response(data={'message': 'Position deleted successfully'})

# CMS Views - Documents
@extend_schema(
    tags=['CMS - Documents'],
    responses={
        200: DocumentSerializer(many=True)
    },
    summary="List documents",
    description="Get list of all documents"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def cms_documents(request):
    try:
        documents = Document.objects.filter(is_published=True)
        serializer = DocumentSerializer(documents, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve documents', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Documents'],
    responses={
        200: DocumentSerializer,
        404: OpenApiResponse(description='Document not found')
    },
    summary="Get document detail",
    description="Get detailed information about a specific document"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_document_detail(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk, is_published=True)
        serializer = DocumentSerializer(document)
        return api_response(data=serializer.data)
    except Document.DoesNotExist:
        return api_response(success=False, message='Document not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve document', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Documents'],
    responses={
        200: DocumentSerializer
    },
    summary="Find document",
    description="Find documents by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='30/m', method='GET', block=True)
def cms_find_document(request):
    try:
        query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        
        documents = Document.objects.filter(is_published=True)
        
        if query:
            documents = documents.filter(title__icontains=query)
        if category:
            documents = documents.filter(category__icontains=category)
        
        serializer = DocumentSerializer(documents, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to search documents', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin CMS Views - Documents
@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: DocumentSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all documents",
    description="Get list of all documents including unpublished ones (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_documents(request):
    try:
        documents = Document.objects.all()
        
        # Search by title or category
        search = request.GET.get('search', '')
        if search:
            documents = documents.filter(
                models.Q(title__icontains=search) |
                models.Q(category__icontains=search)
            )
        
        # Filter by published status
        is_published = request.GET.get('is_published', '')
        if is_published.lower() in ['true', 'false']:
            documents = documents.filter(is_published=is_published.lower() == 'true')
        
        # Filter by category
        category = request.GET.get('category', '')
        if category:
            documents = documents.filter(category__icontains=category)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    documents = documents.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    documents = documents.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        documents = documents.order_by('-created_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(documents, request)
        
        serializer = DocumentSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve documents', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: DocumentSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Document not found')
    },
    summary="Get document detail",
    description="Get detailed information about a specific document (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_document_detail(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentSerializer(document)
        return api_response(data=serializer.data)
    except Document.DoesNotExist:
        return api_response(success=False, message='Document not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve document', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=DocumentSerializer,
    responses={
        201: DocumentSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="Create document",
    description="Create a new document (admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_cms_create_document(request):
    try:
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to create document', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=DocumentSerializer,
    responses={
        200: DocumentSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Document not found')
    },
    summary="Update document",
    description="Update document details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_cms_update_document(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except Document.DoesNotExist:
        return api_response(success=False, message='Document not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to update document', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: OpenApiResponse(description='Document deleted successfully'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Document not found')
    },
    summary="Delete document",
    description="Delete a document (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_cms_delete_document(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk)
        document.delete()
        return api_response(data={'message': 'Document deleted successfully'})
    except Document.DoesNotExist:
        return api_response(success=False, message='Document not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete document', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CMS Views - Images
@extend_schema(
    tags=['CMS - Images'],
    responses={
        200: ImageSerializer(many=True)
    },
    summary="List images",
    description="Get list of all images"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def cms_images(request):
    try:
        images = Image.objects.filter(is_published=True)
        serializer = ImageSerializer(images, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve images', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Images'],
    responses={
        200: ImageSerializer,
        404: OpenApiResponse(description='Image not found')
    },
    summary="Get image detail",
    description="Get detailed information about a specific image"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_image_detail(request, pk):
    try:
        image = get_object_or_404(Image, pk=pk, is_published=True)
        serializer = ImageSerializer(image)
        return api_response(data=serializer.data)
    except Image.DoesNotExist:
        return api_response(success=False, message='Image not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve image', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Images'],
    responses={
        200: ImageSerializer
    },
    summary="Find image",
    description="Find images by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def cms_find_image(request):
    try:
        query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        
        images = Image.objects.filter(is_published=True)
        
        if query:
            images = images.filter(title__icontains=query)
        if category:
            images = images.filter(category__icontains=category)
        
        serializer = ImageSerializer(images, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to search images', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin CMS Views - Images
@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: ImageSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all images",
    description="Get list of all images including unpublished ones (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_images(request):
    try:
        images = Image.objects.all()
        
        # Search by title or category
        search = request.GET.get('search', '')
        if search:
            images = images.filter(
                models.Q(title__icontains=search) |
                models.Q(category__icontains=search)
            )
        
        # Filter by published status
        is_published = request.GET.get('is_published', '')
        if is_published.lower() in ['true', 'false']:
            images = images.filter(is_published=is_published.lower() == 'true')
        
        # Filter by category
        category = request.GET.get('category', '')
        if category:
            images = images.filter(category__icontains=category)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    images = images.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    images = images.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        images = images.order_by('-created_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(images, request)
        
        serializer = ImageSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve images', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: ImageSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Image not found')
    },
    summary="Get image detail",
    description="Get detailed information about a specific image (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_image_detail(request, pk):
    try:
        image = get_object_or_404(Image, pk=pk)
        serializer = ImageSerializer(image)
        return api_response(data=serializer.data)
    except Image.DoesNotExist:
        return api_response(success=False, message='Image not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve image', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=ImageSerializer,
    responses={
        201: ImageSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="Create image",
    description="Create a new image (admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_cms_create_image(request):
    try:
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to create image', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=ImageSerializer,
    responses={
        200: ImageSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Image not found')
    },
    summary="Update image",
    description="Update image details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_cms_update_image(request, pk):
    try:
        image = get_object_or_404(Image, pk=pk)
        serializer = ImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except Image.DoesNotExist:
        return api_response(success=False, message='Image not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to update image', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: OpenApiResponse(description='Image deleted successfully'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Image not found')
    },
    summary="Delete image",
    description="Delete an image (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_cms_delete_image(request, pk):
    try:
        image = get_object_or_404(Image, pk=pk)
        image.delete()
        return api_response(data={'message': 'Image deleted successfully'})
    except Image.DoesNotExist:
        return api_response(success=False, message='Image not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete image', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CMS Views - Pages
@extend_schema(
    tags=['CMS - Pages'],
    responses={
        200: PageSerializer(many=True)
    },
    summary="List pages",
    description="Get list of all published pages"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def cms_pages(request):
    try:
        pages = Page.objects.filter(status='published')
        serializer = PageSerializer(pages, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve pages', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Pages'],
    responses={
        200: PageSerializer,
        404: OpenApiResponse(description='Page not found')
    },
    summary="Get page detail",
    description="Get detailed information about a specific page"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_page_detail(request, pk):
    try:
        page = get_object_or_404(Page, pk=pk, status='published')
        serializer = PageSerializer(page)
        return api_response(data=serializer.data)
    except Page.DoesNotExist:
        return api_response(success=False, message='Page not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve page', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Pages'],
    responses={
        200: OpenApiResponse(description='Page action completed successfully'),
        404: OpenApiResponse(description='Page not found')
    },
    summary="Execute page action",
    description="Execute a specific action on a page"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def cms_page_action(request, pk, action_name):
    try:
        page = get_object_or_404(Page, pk=pk)
        
        # Define available actions
        actions = {
            'publish': lambda p: setattr(p, 'status', 'published'),
            'archive': lambda p: setattr(p, 'status', 'archived'),
            'draft': lambda p: setattr(p, 'status', 'draft'),
        }
        
        if action_name not in actions:
            return api_response(success=False, message='Invalid action', status_code=status.HTTP_400_BAD_REQUEST)
        
        actions[action_name](page)
        page.save()
        
        return api_response(data={'message': f'Page {action_name} action completed successfully'})
    except Page.DoesNotExist:
        return api_response(success=False, message='Page not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to execute page action', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['CMS - Pages'],
    responses={
        200: PageSerializer
    },
    summary="Find page",
    description="Find pages by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='60/m', method='GET', block=True)
def cms_find_page(request):
    try:
        query = request.GET.get('q', '')
        template = request.GET.get('template', '')
        
        pages = Page.objects.filter(status='published')
        
        if query:
            pages = pages.filter(title__icontains=query)
        if template:
            pages = pages.filter(template__icontains=template)
        
        serializer = PageSerializer(pages, many=True)
        return api_response(data=serializer.data)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to search pages', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin CMS Views - Pages
@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: PageSerializer(many=True),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="List all pages",
    description="Get list of all pages including unpublished ones (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_pages(request):
    try:
        pages = Page.objects.all()
        
        # Search by title or template
        search = request.GET.get('search', '')
        if search:
            pages = pages.filter(
                models.Q(title__icontains=search) |
                models.Q(template__icontains=search)
            )
        
        # Filter by status
        status = request.GET.get('status', '')
        if status:
            pages = pages.filter(status=status)
        
        # Filter by template
        template = request.GET.get('template', '')
        if template:
            pages = pages.filter(template__icontains=template)
        
        # Filter by date range
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                if date_from_obj:
                    pages = pages.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                if date_to_obj:
                    pages = pages.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        pages = pages.order_by('-created_at')
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(pages, request)
        
        serializer = PageSerializer(result_page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'data': serializer.data
        })
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve pages', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: PageSerializer,
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Page not found')
    },
    summary="Get page detail",
    description="Get detailed information about a specific page (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_cms_page_detail(request, pk):
    try:
        page = get_object_or_404(Page, pk=pk)
        serializer = PageSerializer(page)
        return api_response(data=serializer.data)
    except Page.DoesNotExist:
        return api_response(success=False, message='Page not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve page', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=PageSerializer,
    responses={
        201: PageSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required')
    },
    summary="Create page",
    description="Create a new page (admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_cms_create_page(request):
    try:
        serializer = PageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to create page', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    request=PageSerializer,
    responses={
        200: PageSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Page not found')
    },
    summary="Update page",
    description="Update page details (admin only)"
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
def admin_cms_update_page(request, pk):
    try:
        page = get_object_or_404(Page, pk=pk)
        serializer = PageSerializer(page, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except Page.DoesNotExist:
        return api_response(success=False, message='Page not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to update page', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    tags=['Admin CMS'],
    responses={
        200: OpenApiResponse(description='Page deleted successfully'),
        403: OpenApiResponse(description='Admin access required'),
        404: OpenApiResponse(description='Page not found')
    },
    summary="Delete page",
    description="Delete a page (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_cms_delete_page(request, pk):
    try:
        page = get_object_or_404(Page, pk=pk)
        page.delete()
        return api_response(data={'message': 'Page deleted successfully'})
    except Page.DoesNotExist:
        return api_response(success=False, message='Page not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete page', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
