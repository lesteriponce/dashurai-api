from django.db import models


class Activity(models.Model):
    TYPE_CHOICES = [
        ('position', 'Position'),
        ('application', 'Application'),
        ('contact_form', 'Contact Form'),
        ('document', 'Document'),
        ('image', 'Image'),
        ('page', 'Page'),
    ]
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('closed', 'Closed'),
        ('reviewed', 'Reviewed'),
        ('deleted', 'Deleted'),
        ('interview', 'Interview'),
        ('responded', 'Responded'),
    ]
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.type} - {self.action}: {self.description}"
