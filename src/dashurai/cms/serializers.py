from rest_framework import serializers
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import re
from .models import Document, Image, Page

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'content', 'file_url', 'category', 'tags', 
                 'created_at', 'updated_at', 'is_published')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long")
        return value.strip()
    
    def validate_file_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("File URL must be a valid URL")
        return value
    
    def validate_category(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Category must be at least 2 characters long")
        return value.strip() if value else value

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'title', 'alt_text', 'image_url', 'category', 'tags',
                 'created_at', 'updated_at', 'is_published')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_alt_text(self, value):
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("Alt text must be at least 3 characters long")
        return value.strip() if value else value
    
    def validate_image_url(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Image URL cannot be empty")
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Image URL must be a valid URL")
        
        # Check file extension for image formats
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        file_extension = value.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(f"Image must be one of: {', '.join(allowed_extensions)}")
        
        return value.strip()
    
    def validate_category(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Category must be at least 2 characters long")
        return value.strip() if value else value

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('id', 'title', 'slug', 'content', 'meta_title', 'meta_description',
                 'template', 'status', 'published_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'published_at', 'created_at', 'updated_at')
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_slug(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Slug cannot be empty")
        
        # Validate slug format (lowercase, alphanumeric, hyphens only)
        slug_pattern = r'^[a-z0-9-]+$'
        if not re.match(slug_pattern, value.strip()):
            raise serializers.ValidationError("Slug can only contain lowercase letters, numbers, and hyphens")
        
        # Check for consecutive hyphens or starting/ending hyphens
        slug = value.strip()
        if '--' in slug or slug.startswith('-') or slug.endswith('-'):
            raise serializers.ValidationError("Slug cannot have consecutive hyphens or start/end with hyphens")
        
        return slug
    
    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long")
        return value.strip()
    
    def validate_meta_title(self, value):
        if value:
            if len(value.strip()) < 10:
                raise serializers.ValidationError("Meta title must be at least 10 characters long")
            if len(value.strip()) > 60:
                raise serializers.ValidationError("Meta title should not exceed 60 characters for SEO")
        return value.strip() if value else value
    
    def validate_meta_description(self, value):
        if value:
            if len(value.strip()) < 50:
                raise serializers.ValidationError("Meta description must be at least 50 characters long")
            if len(value.strip()) > 160:
                raise serializers.ValidationError("Meta description should not exceed 160 characters for SEO")
        return value.strip() if value else value
    
    def validate_template(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Template must be at least 2 characters long")
        return value.strip() if value else value

class PageActionSerializer(serializers.Serializer):
    action_name = serializers.CharField()
    parameters = serializers.JSONField(required=False)
    
    def validate_action_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Action name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Action name must be at least 2 characters long")
        return value.strip()
    
    def validate_parameters(self, value):
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a valid JSON object")
        return value
