from django.db import models

class ContactSubmission(models.Model):
    CONTACT_STATUS = [
        ('new', 'New'),
        ('responded', 'Responded'),
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ]
    
    first_name = models.CharField(max_length=50, db_index=True)
    last_name = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200, blank=True, db_index=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=CONTACT_STATUS, default='new', db_index=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['email', 'subject']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.subject}"
