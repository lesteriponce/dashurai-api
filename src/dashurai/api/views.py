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
from django_ratelimit.decorators import ratelimit
from .versioning import get_api_version_info
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    PositionSerializer, JobApplicationSerializer, ContactSubmissionSerializer,
    AdminLoginSerializer, DashboardStatsSerializer, RefreshTokenSerializer,
    LoginResponseSerializer, TokenResponseSerializer, LogoutResponseSerializer,
    SuccessResponseSerializer, CreatedResponseSerializer
)
from cms.serializers import DocumentSerializer, ImageSerializer, PageSerializer
from users.models import User
from careers.models import Position, JobApplication
from contact.models import ContactSubmission
from cms.models import Document, Image, Page

# API Version View
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_version(request):
    try:
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
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)

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
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: {'description': 'Invalid credentials'},
        500: {'description': 'Server error'}
    },
    summary='User Login',
    description='Authenticate user and return JWT tokens'
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login(request):
    try:
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
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request):
        try:
            # register a new user account
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return api_response(data={'message': 'Registration successful'}, status_code=status.HTTP_201_CREATED)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)

@extend_schema(
    request=RefreshTokenSerializer,
    responses={
        200: TokenResponseSerializer,
        400: {'description': 'Invalid token'},
        500: {'description': 'Server error'}
    },
    summary='Refresh Token',
    description='Refresh JWT access token using refresh token'
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
    request=RefreshTokenSerializer,
    responses={
        200: LogoutResponseSerializer,
        400: {'description': 'Invalid token'},
        500: {'description': 'Server error'}
    },
    summary='User Logout',
    description='Logout user and blacklist refresh token'
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
    request=UserSerializer,
    responses={
        200: UserSerializer,
        400: {'description': 'Invalid data'},
        500: {'description': 'Server error'}
    },
    summary='Update User Profile',
    description='Update authenticated user profile information'
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
    request=AdminLoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: {'description': 'Invalid credentials'},
        403: {'description': 'Access denied'},
        500: {'description': 'Server error'}
    },
    summary='Admin Login',
    description='Authenticate admin user and return JWT tokens'
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def admin_login(request):
    try:
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
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)

# Dashboard view for admin stats
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

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def position_detail(request, pk):
    try:
        position = Position.objects.get(pk=pk, status='active')
        serializer = PositionSerializer(position)
        return api_response(data=serializer.data)
    except (Position.DoesNotExist, ValueError, ValidationError):
        return api_response(success=False, message='Position not found', status_code=status.HTTP_404_NOT_FOUND)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to retrieve position', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    request=JobApplicationSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        500: {'description': 'Server error'}
    },
    summary='Submit Job Application',
    description='Submit a new job application'
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def apply_job(request):
    try:
        serializer = JobApplicationSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            # Log activity
            from .activity_views import create_and_broadcast_activity
            position_title = application.position.title if application.position else 'Unknown Position'
            create_and_broadcast_activity('application', 'created', f"New application for {position_title}")
            return api_response(data={'message': 'Application submitted successfully', 'application_id': str(application.id)}, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to submit application', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Application submission failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            'applied_at': data['applied_at']
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
    request=ContactSubmissionSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        500: {'description': 'Server error'}
    },
    summary='Submit Contact Form',
    description='Submit a new contact form submission'
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@ratelimit(key='ip', rate='2/m', method='POST', block=True)
def contact_submit(request):
    try:
        serializer = ContactSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            # Log activity
            from .activity_views import create_and_broadcast_activity
            create_and_broadcast_activity('contact_form', 'created', "New contact form submission")
            return api_response(data={'message': 'Contact form submitted successfully'}, status_code=status.HTTP_201_CREATED)
        else:
            # Log detailed validation errors for debugging
            print(f"Contact form validation errors: {serializer.errors}")
            return api_response(success=False, message=f'Validation failed: {serializer.errors}', status_code=status.HTTP_400_BAD_REQUEST)    
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to submit contact form', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Contact submission failed', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views - Applications
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
    request=JobApplicationSerializer,
    responses={
        200: JobApplicationSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Application not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Job Application',
    description='Retrieve or update a specific job application'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_application_detail(request, pk):
    try:
        application = get_object_or_404(JobApplication, pk=pk)
        
        if request.method == 'PATCH':
            serializer = JobApplicationSerializer(application, data=request.data, partial=True)
            if serializer.is_valid():
                updated_application = serializer.save()
                # Log activity temporary disabled
                # from .activity_views import create_and_broadcast_activity
                # create_and_broadcast_activity('application', 'updated', f"Application updated: {updated_application.applicant_name}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = JobApplicationSerializer(application, data=request.data, partial=False)
            if serializer.is_valid():
                updated_application = serializer.save()
                # Log activity temporary disabled
                # from .activity_views import create_and_broadcast_activity
                # create_and_broadcast_activity('application', 'updated', f"Application updated: {updated_application.applicant_name}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='20/m', method='GET', block=True)
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
    request=ContactSubmissionSerializer,
    responses={
        200: ContactSubmissionSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Contact not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Contact Submission',
    description='Retrieve or update a specific contact submission'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_contact_detail(request, pk):
    try:
        contact = get_object_or_404(ContactSubmission, pk=pk)
        
        if request.method == 'PATCH':
            serializer = ContactSubmissionSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                updated_contact = serializer.save()
                # Log activity temporary disableed
                # from .activity_views import create_and_broadcast_activity
                # create_and_broadcast_activity('contact', 'updated', f"Contact updated: {updated_contact.name}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = ContactSubmissionSerializer(contact, data=request.data, partial=False)
            if serializer.is_valid():
                updated_contact = serializer.save()
                # Log activity temporary disableed
                # from .activity_views import create_and_broadcast_activity
                # create_and_broadcast_activity('contact', 'updated', f"Contact updated: {updated_contact.name}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_contact(request, pk):
    try:
        contact = get_object_or_404(ContactSubmission, pk=pk)
        contact.delete()
        return api_response(data={'message': 'Contact deleted successfully'})
    except ContactSubmission.DoesNotExist:
        return api_response(success=False, message='Contact not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete contact', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Admin Views - Positions
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
    request=PositionSerializer,
    responses={
        200: PositionSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Position not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Position',
    description='Retrieve or update a specific position'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_position_detail(request, pk):
    try:
        position = get_object_or_404(Position, pk=pk)
        
        if request.method == 'PATCH':
            serializer = PositionSerializer(position, data=request.data, partial=True)
            if serializer.is_valid():
                updated_position = serializer.save()
                # Log activity
                from .activity_views import create_and_broadcast_activity
                create_and_broadcast_activity('position', 'updated', f"Position updated: {updated_position.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = PositionSerializer(position, data=request.data, partial=False)
            if serializer.is_valid():
                updated_position = serializer.save()
                # Log activity
                from .activity_views import create_and_broadcast_activity
                create_and_broadcast_activity('position', 'updated', f"Position updated: {updated_position.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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
    request=PositionSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Server error'}
    },
    summary='Create Position',
    description='Create a new position'
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_position(request):
    try:
        serializer = PositionSerializer(data=request.data)
        if serializer.is_valid():
            position = serializer.save()
            # Log activity
            from .activity_views import create_and_broadcast_activity
            create_and_broadcast_activity('position', 'created', f"New position added: {position.title}")
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except ValidationError as e:
        return api_response(success=False, message='Validation failed', status_code=status.HTTP_400_BAD_REQUEST)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to create position', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_position(request, pk):
    try:
        position = get_object_or_404(Position, pk=pk)
        position_title = position.title  # Store title before deletion
        position.delete()
        # Log activity (temporary disable)
#        from .activity_views import create_and_broadcast_activity
#        create_and_broadcast_activity('position', 'deleted', f"Position deleted: {position_title}")
        return api_response(data={'message': 'Position deleted successfully'})
    except Position.DoesNotExist:
        return api_response(success=False, message='Position not found', status_code=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return api_response(success=False, message='Admin access required', status_code=status.HTTP_403_FORBIDDEN)
    except DatabaseError as e:
        return api_response(success=False, message='Failed to delete position', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return api_response(success=False, message='Server error', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# CMS Views - Documents
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
@api_view(['GET'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='30/m', method='GET', block=True)
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
    request=DocumentSerializer,
    responses={
        200: DocumentSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Document not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Document',
    description='Retrieve or update a specific document'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='20/m', method=['GET', 'PATCH', 'PUT'], block=True)
def admin_cms_document_detail(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk)
        
        if request.method == 'PATCH':
            serializer = DocumentSerializer(document, data=request.data, partial=True)
            if serializer.is_valid():
                updated_document = serializer.save()
                # Log activity (temporar disable)
              #   from .activity_views import create_and_broadcast_activity
              #   create_and_broadcast_activity('document', 'updated', f"Document updated: {updated_document.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = DocumentSerializer(document, data=request.data, partial=False)
            if serializer.is_valid():
                updated_document = serializer.save()
                # Log activity (temporar disable)
              #   from .activity_views import create_and_broadcast_activity
              #   create_and_broadcast_activity('document', 'updated', f"Document updated: {updated_document.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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
    request=DocumentSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Server error'}
    },
    summary='Create Document',
    description='Create a new document'
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='10/m', method='POST', block=True)
def admin_cms_create_document(request):
    try:
        # Validate file upload
        if 'file' not in request.FILES:
            return api_response(success=False, message='No file provided', status_code=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # File size validation (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return api_response(success=False, message='File size exceeds 10MB limit', status_code=status.HTTP_400_BAD_REQUEST)
        
        # File type validation
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return api_response(success=False, message=f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}', status_code=status.HTTP_400_BAD_REQUEST)
        
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


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='10/m', method='DELETE', block=True)
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
    request=ImageSerializer,
    responses={
        200: ImageSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Image not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Image',
    description='Retrieve or update a specific image'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_cms_image_detail(request, pk):
    try:
        image = get_object_or_404(Image, pk=pk)
        
        if request.method == 'PATCH':
            serializer = ImageSerializer(image, data=request.data, partial=True)
            if serializer.is_valid():
                updated_image = serializer.save()
                # Log activity (temporary disable)
            #    from .activity_views import create_and_broadcast_activity
            #    create_and_broadcast_activity('image', 'updated', f"Image updated: {updated_image.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = ImageSerializer(image, data=request.data, partial=False)
            if serializer.is_valid():
                updated_image = serializer.save()
                # Log activity (temporaryy disable)
            #    from .activity_views import create_and_broadcast_activity
            #    create_and_broadcast_activity('image', 'updated', f"Image updated: {updated_image.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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
    request=ImageSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Server error'}
    },
    summary='Create Image',
    description='Create a new image'
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_cms_create_image(request):
    try:
        # Validate file upload
        if 'file' not in request.FILES:
            return api_response(success=False, message='No file provided', status_code=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # File size validation (max 5MB for images)
        if file.size > 5 * 1024 * 1024:
            return api_response(success=False, message='File size exceeds 5MB limit', status_code=status.HTTP_400_BAD_REQUEST)
        
        # File type validation
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return api_response(success=False, message=f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}', status_code=status.HTTP_400_BAD_REQUEST)
        
        # MIME type validation
        allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_mime_types:
            return api_response(success=False, message='Invalid MIME type', status_code=status.HTTP_400_BAD_REQUEST)
        
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

@api_view(['POST'])
@permission_classes([IsAdminUser])
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
    request=PageSerializer,
    responses={
        200: PageSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        404: {'description': 'Page not found'},
        500: {'description': 'Server error'}
    },
    summary='Get/Update Page',
    description='Retrieve or update a specific page'
)
@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([IsAdminUser])
def admin_cms_page_detail(request, pk):
    try:
        page = get_object_or_404(Page, pk=pk)
        
        if request.method == 'PATCH':
            serializer = PageSerializer(page, data=request.data, partial=True)
            if serializer.is_valid():
                updated_page = serializer.save()
                # Log activity (temporar disable)
            #    from .activity_views import create_and_broadcast_activity
            #    create_and_broadcast_activity('page', 'updated', f"Page updated: {updated_page.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'PUT':
            serializer = PageSerializer(page, data=request.data, partial=False)
            if serializer.is_valid():
                updated_page = serializer.save()
                # Log activity (temporar disable)
            #    from .activity_views import create_and_broadcast_activity
            #    create_and_broadcast_activity('page', 'updated', f"Page updated: {updated_page.title}")
                return api_response(data=serializer.data)
            return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        else:  # GET
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
    request=PageSerializer,
    responses={
        201: CreatedResponseSerializer,
        400: {'description': 'Validation failed'},
        403: {'description': 'Admin access required'},
        500: {'description': 'Server error'}
    },
    summary='Create Page',
    description='Create a new page'
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
