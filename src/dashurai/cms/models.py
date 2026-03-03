from django.db import models
from django.utils import timezone

class Document(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    file_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Image(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    alt_text = models.CharField(max_length=255, blank=True)
    image_url = models.URLField()
    category = models.CharField(max_length=100, blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Page(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    content = models.TextField()
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    template = models.CharField(max_length=100, default='default')
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ], default='draft', db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
