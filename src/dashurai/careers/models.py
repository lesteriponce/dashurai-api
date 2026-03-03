from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid

class Position(models.Model):
    POSITION_TYPES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
    ]
    
    POSITION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    title = models.CharField(max_length=200, db_index=True)
    department = models.CharField(max_length=100, db_index=True)
    type = models.CharField(max_length=20, choices=POSITION_TYPES, default='full-time', db_index=True)
    status = models.CharField(max_length=20, choices=POSITION_STATUS, default='active', db_index=True)
    description = models.TextField()
    tags = models.JSONField(default=list) 
    image_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class JobApplication(models.Model):
    APPLICATION_STATUS = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='applications', db_index=True)
    first_name = models.CharField(max_length=50, db_index=True)
    last_name = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(db_index=True)
    resume = models.FileField(
        upload_to='resumes/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])
        ]
    )
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending', db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ['position', 'email']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position.title}"
    
    def clean(self):
        super().clean()
        if self.resume:
            max_size = 5 * 1024 * 1024  # 5MB
            if self.resume.size > max_size:
                raise ValidationError({'resume': 'Resume file must be smaller than 5MB'})
