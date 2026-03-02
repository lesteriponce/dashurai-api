from rest_framework import serializers
from .models import Document, Image, Page

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'content', 'file_url', 'category', 'tags', 
                 'created_at', 'updated_at', 'is_published')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'title', 'alt_text', 'image_url', 'category', 'tags',
                 'created_at', 'updated_at', 'is_published')
        read_only_fields = ('id', 'created_at', 'updated_at')

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('id', 'title', 'slug', 'content', 'meta_title', 'meta_description',
                 'template', 'status', 'published_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'published_at', 'created_at', 'updated_at')

class PageActionSerializer(serializers.Serializer):
    action_name = serializers.CharField()
    parameters = serializers.JSONField(required=False)
