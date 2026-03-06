from django.urls import path
from api import views
from api.views import APIVersionView

app_name = 'api_v1'

urlpatterns = [
    # API Version
    path('', APIVersionView.as_view(), name='version_info'),
    
    # Authentication URLs
    path('auth/login/', views.login, name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/refresh/', views.refresh_token, name='refresh_token'),
    
    # Admin Authentication
    path('admin/login/', views.admin_login, name='admin_login'),

    # Dashboard Stats
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Career URLs
    path('careers/positions/', views.positions_list, name='positions_list'),
    path('careers/positions/<str:pk>/', views.position_detail, name='position_detail'),
    path('careers/apply/', views.apply_job, name='apply_job'),
    
    # Contact URLs
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    
    # Admin URLs - Applications
    path('admin/applications/', views.admin_applications, name='admin_applications'),
    path('admin/applications/<int:pk>/', views.admin_update_application, name='admin_update_application'),
    path('admin/applications/<int:pk>/delete/', views.admin_delete_application, name='admin_delete_application'),
    path('admin/applications/<int:pk>/resume/', views.admin_download_resume, name='admin_download_resume'),
    
    # Admin URLs - Contacts
    path('admin/contacts/', views.admin_contacts, name='admin_contacts'),
    path('admin/contacts/<int:pk>/', views.admin_update_contact, name='admin_update_contact'),
    path('admin/contacts/<int:pk>/delete/', views.admin_delete_contact, name='admin_delete_contact'),
    
    # Admin URLs - Positions
    path('admin/positions/', views.admin_positions, name='admin_positions'),
    path('admin/positions/create/', views.admin_create_position, name='admin_create_position'),
    path('admin/positions/<str:pk>/', views.admin_update_position, name='admin_update_position'),
    path('admin/positions/<str:pk>/delete/', views.admin_delete_position, name='admin_delete_position'),
    
    # CMS URLs - Documents
    path('content/documents/', views.cms_documents, name='cms_documents'),
    path('content/documents/<str:pk>/', views.cms_document_detail, name='cms_document_detail'),
    path('content/documents/find/', views.cms_find_document, name='cms_find_document'),
    
    # CMS URLs - Images
    path('content/images/', views.cms_images, name='cms_images'),
    path('content/images/<str:pk>/', views.cms_image_detail, name='cms_image_detail'),
    path('content/images/find/', views.cms_find_image, name='cms_find_image'),
    
    # CMS URLs - Pages
    path('content/pages/', views.cms_pages, name='cms_pages'),
    path('content/pages/<str:pk>/', views.cms_page_detail, name='cms_page_detail'),
    path('content/pages/<str:pk>/action/<str:action_name>/', views.cms_page_action, name='cms_page_action'),
    path('content/pages/find/', views.cms_find_page, name='cms_find_page'),
    
    # Admin CMS URLs - Documents
    path('admin/content/documents/', views.admin_cms_documents, name='admin_cms_documents'),
    path('admin/content/documents/create/', views.admin_cms_create_document, name='admin_cms_create_document'),
    path('admin/content/documents/<str:pk>/', views.admin_cms_update_document, name='admin_cms_update_document'),
    path('admin/content/documents/<str:pk>/delete/', views.admin_cms_delete_document, name='admin_cms_delete_document'),
    
    # Admin CMS URLs - Images
    path('admin/content/images/', views.admin_cms_images, name='admin_cms_images'),
    path('admin/content/images/create/', views.admin_cms_create_image, name='admin_cms_create_image'),
    path('admin/content/images/<str:pk>/', views.admin_cms_update_image, name='admin_cms_update_image'),
    path('admin/content/images/<str:pk>/delete/', views.admin_cms_delete_image, name='admin_cms_delete_image'),
    
    # Admin CMS URLs - Pages
    path('admin/content/pages/', views.admin_cms_pages, name='admin_cms_pages'),
    path('admin/content/pages/create/', views.admin_cms_create_page, name='admin_cms_create_page'),
    path('admin/content/pages/<str:pk>/', views.admin_cms_update_page, name='admin_cms_update_page'),
    path('admin/content/pages/<str:pk>/delete/', views.admin_cms_delete_page, name='admin_cms_delete_page'),
]
