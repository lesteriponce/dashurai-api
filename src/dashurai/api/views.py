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
from cms.serializers import DocumentSerializer, ImageSerializer, PageSerializer
from users.models import User
from careers.models import Position, JobApplication
from contact.models import ContactSubmission
from cms.models import Document, Image, Page

# Helper function for consistent response format
def api_response(success=True, data=None, message=None, status_code=status.HTTP_200_OK):
    if success:
        return Response({'success': True, 'data': data}, status=status_code)
    else:
        return Response({'success': False, 'message': message}, status=status_code)

# Authentication Views
@extend_schema(
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

@extend_schema(
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

@extend_schema(
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
@extend_schema(
    responses={
        200: PositionSerializer(many=True)
    },
    summary="List active positions",
    description="Get list of all active job positions"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def positions_list(request):
    """List active positions - get list of all active job positions"""
    positions = Position.objects.filter(status='active')
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@extend_schema(
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
    """Get position details - get detailed information about a specific position"""
    position = get_object_or_404(Position, pk=pk, status='active')
    serializer = PositionSerializer(position)
    return api_response(data=serializer.data)

@extend_schema(
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
def apply_job(request):
    """Apply for job - submit a job application"""
    serializer = JobApplicationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Application submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Contact Views
@extend_schema(
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
def contact_submit(request):
    """Submit contact form - submit a contact inquiry"""
    serializer = ContactSubmissionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data={'message': 'Contact form submitted successfully'}, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

# Admin Views - Applications
@extend_schema(
    responses={
        200: JobApplicationSerializer(many=True)
    },
    summary="List all applications",
    description="Get list of all job applications (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_applications(request):
    """List all applications - get list of all job applications (admin only)"""
    applications = JobApplication.objects.all()
    serializer = JobApplicationSerializer(applications, many=True)
    return api_response(data=serializer.data)

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
    """Delete application - delete a job application (admin only)"""
    application = get_object_or_404(JobApplication, pk=pk)
    application.delete()
    return api_response(data={'message': 'Application deleted successfully'})

# Admin Views - Contacts
@extend_schema(
    responses={
        200: ContactSubmissionSerializer(many=True)
    },
    summary="List all contacts",
    description="Get list of all contact submissions (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_contacts(request):
    """List all contacts - get list of all contact submissions (admin only)"""
    contacts = ContactSubmission.objects.all()
    serializer = ContactSubmissionSerializer(contacts, many=True)
    return api_response(data=serializer.data)

@extend_schema(
    request=ContactSubmissionSerializer,
    responses={
        200: ContactSubmissionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        404: OpenApiResponse(description='Contact not found')
    },
    summary="Update contact",
    description="Update contact submission details (admin only)"
)
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

@extend_schema(
    responses={
        200: OpenApiResponse(description='Contact deleted successfully'),
        404: OpenApiResponse(description='Contact not found')
    },
    summary="Delete contact",
    description="Delete a contact submission (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_contact(request, pk):
    """Delete contact - delete a contact submission (admin only)"""
    contact = get_object_or_404(ContactSubmission, pk=pk)
    contact.delete()
    return api_response(data={'message': 'Contact deleted successfully'})

# Admin Views - Positions
@extend_schema(
    responses={
        200: PositionSerializer(many=True)
    },
    summary="List all positions",
    description="Get list of all positions including inactive ones (admin only)"
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_positions(request):
    """List all positions - get list of all positions including inactive ones (admin only)"""
    positions = Position.objects.all()
    serializer = PositionSerializer(positions, many=True)
    return api_response(data=serializer.data)

@extend_schema(
    request=PositionSerializer,
    responses={
        201: PositionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors')
    },
    summary="Create position",
    description="Create a new job position (admin only)"
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_position(request):
    """Create position - create a new job position (admin only)"""
    serializer = PositionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
    return api_response(success=False, message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=PositionSerializer,
    responses={
        200: PositionSerializer,
        400: OpenApiResponse(description='Bad request - validation errors'),
        404: OpenApiResponse(description='Position not found')
    },
    summary="Update position",
    description="Update job position details (admin only)"
)
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

@extend_schema(
    responses={
        200: OpenApiResponse(description='Position deleted successfully'),
        404: OpenApiResponse(description='Position not found')
    },
    summary="Delete position",
    description="Delete a job position (admin only)"
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def admin_delete_position(request, pk):
    """Delete position - delete a job position (admin only)"""
    position = get_object_or_404(Position, pk=pk)
    position.delete()
    return api_response(data={'message': 'Position deleted successfully'})

# CMS Views - Documents
@extend_schema(
    responses={
        200: DocumentSerializer(many=True)
    },
    summary="List documents",
    description="Get list of all documents"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_documents(request):
    """List documents - get list of all documents"""
    documents = Document.objects.filter(is_published=True)
    serializer = DocumentSerializer(documents, many=True)
    return api_response(data=serializer.data)

@extend_schema(
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
    """Get document detail - get detailed information about a specific document"""
    document = get_object_or_404(Document, pk=pk, is_published=True)
    serializer = DocumentSerializer(document)
    return api_response(data=serializer.data)

@extend_schema(
    responses={
        200: DocumentSerializer
    },
    summary="Find document",
    description="Find documents by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_find_document(request):
    """Find document - find documents by search criteria"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    documents = Document.objects.filter(is_published=True)
    
    if query:
        documents = documents.filter(title__icontains=query)
    if category:
        documents = documents.filter(category__icontains=category)
    
    serializer = DocumentSerializer(documents, many=True)
    return api_response(data=serializer.data)

# CMS Views - Images
@extend_schema(
    responses={
        200: ImageSerializer(many=True)
    },
    summary="List images",
    description="Get list of all images"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_images(request):
    """List images - get list of all images"""
    images = Image.objects.filter(is_published=True)
    serializer = ImageSerializer(images, many=True)
    return api_response(data=serializer.data)

@extend_schema(
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
    """Get image detail - get detailed information about a specific image"""
    image = get_object_or_404(Image, pk=pk, is_published=True)
    serializer = ImageSerializer(image)
    return api_response(data=serializer.data)

@extend_schema(
    responses={
        200: ImageSerializer
    },
    summary="Find image",
    description="Find images by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_find_image(request):
    """Find image - find images by search criteria"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    images = Image.objects.filter(is_published=True)
    
    if query:
        images = images.filter(title__icontains=query)
    if category:
        images = images.filter(category__icontains=category)
    
    serializer = ImageSerializer(images, many=True)
    return api_response(data=serializer.data)

# CMS Views - Pages
@extend_schema(
    responses={
        200: PageSerializer(many=True)
    },
    summary="List pages",
    description="Get list of all published pages"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_pages(request):
    """List pages - get list of all published pages"""
    pages = Page.objects.filter(status='published')
    serializer = PageSerializer(pages, many=True)
    return api_response(data=serializer.data)

@extend_schema(
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
    """Get page detail - get detailed information about a specific page"""
    page = get_object_or_404(Page, pk=pk, status='published')
    serializer = PageSerializer(page)
    return api_response(data=serializer.data)

@extend_schema(
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
    """Execute page action - execute a specific action on a page"""
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

@extend_schema(
    responses={
        200: PageSerializer
    },
    summary="Find page",
    description="Find pages by search criteria"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cms_find_page(request):
    """Find page - find pages by search criteria"""
    query = request.GET.get('q', '')
    template = request.GET.get('template', '')
    
    pages = Page.objects.filter(status='published')
    
    if query:
        pages = pages.filter(title__icontains=query)
    if template:
        pages = pages.filter(template__icontains=template)
    
    serializer = PageSerializer(pages, many=True)
    return api_response(data=serializer.data)
