from django.contrib import admin
from .models import Document, Image, Page

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'category')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'is_published')
        }),
        ('Content', {
            'fields': ('content', 'file_url', 'tags')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'alt_text', 'category')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'alt_text', 'category', 'is_published')
        }),
        ('Content', {
            'fields': ('image_url', 'tags')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'template', 'published_at', 'created_at')
    list_filter = ('status', 'template', 'published_at', 'created_at')
    search_fields = ('title', 'slug', 'content', 'meta_title')
    ordering = ('-created_at',)
    readonly_fields = ('published_at', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'status', 'template')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
