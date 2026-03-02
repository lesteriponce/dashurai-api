from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiRequest, OpenApiResponse
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer,
    PositionSerializer, JobApplicationSerializer, ContactSubmissionSerializer,
    AdminLoginSerializer
)
from users.models import User
from careers.models import Position, JobApplication
from contact.models import ContactSubmission

# Helper function for consistent response format
def api_response(success=True, data=None, message=None, status_code=status.HTTP_200_OK):
    if success:
        return Response({'success': True, 'data': data}, status=status_code)
    else:
        return Response({'success': False, 'message': message}, status=status_code)

# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """User login - authenticate user and return JWT tokens"""
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
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description='Registration successful'),
            400: OpenApiResponse(description='Bad request - validation errors')
        }
    )
    def post(self, request):
        """User registration - register a new user account"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return api_response(data={'message': 'Registration successful'}, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token(request):
    """Refresh JWT token - get new access token using refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return api_response(success=False, message='Refresh token required', status_code=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        return api_response(data={'access': str(refresh.access_token)})
    except Exception as e:
        return api_response(success=False, message='Invalid refresh token', status_code=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_login(request):
    """Admin login - authenticate admin user and return JWT tokens"""
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

# Career Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def positions_list(request):
    """List active positions - get list of all active job positions"""
    positions = Position.objects.filter(status='active')
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def position_detail(request, pk):
    """Get position details - get detailed information about a specific position"""
    position = get_object_or_404(Position, pk=pk, status='active')
    serializer = PositionSerializer(position)
    return api_response(data=serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def apply_job(request):
    """Apply for job - submit a job application"""
    serializer = JobApplicationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Application submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Contact Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def contact_submit(request):
    """Submit contact form - submit a contact inquiry"""
    serializer = ContactSubmissionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Contact form submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Admin Views - Applications
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_applications(request):
    """List all applications - get list of all job applications (admin only)"""
    applications = JobApplication.objects.all()
    serializer = JobApplicationSerializer(applications, many=True)
    return api_response(data=serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_application(request, pk):
    """Update application - update job application status or details (admin only)"""
    application = get_object_or_404(JobApplication, pk=pk)
    serializer = JobApplicationSerializer(application, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_application(request, pk):
    """Delete application - delete a job application (admin only)"""
    application = get_object_or_404(JobApplication, pk=pk)
    application.delete()
    return api_response(data={'message': 'Application deleted successfully'})

# Admin Views - Contacts
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contacts(request):
    """List all contacts - get list of all contact submissions (admin only)"""
    contacts = ContactSubmission.objects.all()
    serializer = ContactSubmissionSerializer(contacts, many=True)
    return api_response(data=serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_contact(request, pk):
    """Update contact - update contact submission details (admin only)"""
    contact = get_object_or_404(ContactSubmission, pk=pk)
    serializer = ContactSubmissionSerializer(contact, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_contact(request, pk):
    """Delete contact - delete a contact submission (admin only)"""
    contact = get_object_or_404(ContactSubmission, pk=pk)
    contact.delete()
    return api_response(data={'message': 'Contact deleted successfully'})

# Admin Views - Positions
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_positions(request):
    """List all positions - get list of all positions including inactive ones (admin only)"""
    positions = Position.objects.all()
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_position(request):
    """Create position - create a new job position (admin only)"""
    serializer = PositionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_position(request, pk):
    """Update position - update job position details (admin only)"""
    position = get_object_or_404(Position, pk=pk)
    serializer = PositionSerializer(position, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_position(request, pk):
    """Delete position - delete a job position (admin only)"""
    position = get_object_or_404(Position, pk=pk)
    position.delete()
    return api_response(data={'message': 'Position deleted successfully'})
