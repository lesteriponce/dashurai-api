from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
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

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return api_response(data={'message': 'Registration successful'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return api_response(success=False, message='Refresh token required', status_code=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        return api_response(data={'access': str(refresh.access_token)})
    except Exception as e:
        return api_response(success=False, message='Invalid refresh token', status_code=status.HTTP_401_UNAUTHORIZED)

# Admin Authentication
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_login(request):
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
    positions = Position.objects.filter(status='active')
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def position_detail(request, pk):
    position = get_object_or_404(Position, pk=pk, status='active')
    serializer = PositionSerializer(position)
    return api_response(data=serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def apply_job(request):
    serializer = JobApplicationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Application submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Contact Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def contact_submit(request):
    serializer = ContactSubmissionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Contact form submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Admin Views - Applications
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_applications(request):
    applications = JobApplication.objects.all()
    serializer = JobApplicationSerializer(applications, many=True)
    return api_response(data=serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_application(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)
    serializer = JobApplicationSerializer(application, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_application(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)
    application.delete()
    return api_response(data={'message': 'Application deleted successfully'})

# Admin Views - Contacts
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contacts(request):
    contacts = ContactSubmission.objects.all()
    serializer = ContactSubmissionSerializer(contacts, many=True)
    return api_response(data=serializer.data)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_contact(request, pk):
    contact = get_object_or_404(ContactSubmission, pk=pk)
    serializer = ContactSubmissionSerializer(contact, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_contact(request, pk):
    contact = get_object_or_404(ContactSubmission, pk=pk)
    contact.delete()
    return api_response(data={'message': 'Contact deleted successfully'})

# Admin Views - Positions
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_positions(request):
    positions = Position.objects.all()
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_position(request):
    serializer = PositionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def admin_update_position(request, pk):
    position = get_object_or_404(Position, pk=pk)
    serializer = PositionSerializer(position, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_position(request, pk):
    position = get_object_or_404(Position, pk=pk)
    position.delete()
    return api_response(data={'message': 'Position deleted successfully'})
