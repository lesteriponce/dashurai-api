from django.contrib import admin
from .models import Position, JobApplication
from .forms import JobApplicationAdminForm

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'type', 'status', 'created_at', 'updated_at')
    list_filter = ('type', 'status', 'department', 'created_at')
    search_fields = ('title', 'department', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'department', 'type', 'status')
        }),
        ('Details', {
            'fields': ('description', 'role_overview', 'key_responsibilities', 'tags', 'image_url')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    form = JobApplicationAdminForm
    list_display = ('first_name', 'last_name', 'email', 'get_position_title', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('first_name', 'last_name', 'email', 'position__title')
    ordering = ('-applied_at',)
    readonly_fields = ('applied_at', 'updated_at')
    
    def get_position_title(self, obj):
        return obj.position.title if obj.position else 'N/A'
    get_position_title.short_description = 'Position'
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Application Details', {
            'fields': ('position', 'resume', 'status')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
