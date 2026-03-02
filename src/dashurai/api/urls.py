from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Authentication URLs
    path('auth/login/', views.login, name='login'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/refresh/', views.refresh_token, name='refresh_token'),
    
    # Admin Authentication
    path('admin/login/', views.admin_login, name='admin_login'),
    
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
    
    # Admin URLs - Contacts
    path('admin/contacts/', views.admin_contacts, name='admin_contacts'),
    path('admin/contacts/<int:pk>/', views.admin_update_contact, name='admin_update_contact'),
    path('admin/contacts/<int:pk>/delete/', views.admin_delete_contact, name='admin_delete_contact'),
    
    # Admin URLs - Positions
    path('admin/positions/', views.admin_positions, name='admin_positions'),
    path('admin/positions/create/', views.admin_create_position, name='admin_create_position'),
    path('admin/positions/<str:pk>/', views.admin_update_position, name='admin_update_position'),
    path('admin/positions/<str:pk>/delete/', views.admin_delete_position, name='admin_delete_position'),
]
