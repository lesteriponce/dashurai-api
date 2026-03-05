from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from users.models import User
from careers.models import Position, JobApplication
from contact.models import ContactSubmission

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'name')
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("First name must be at least 3 characters long")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Last name must be at least 3 characters long")
        return value.strip()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, 
                                   validators=[RegexValidator(
                                       regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                                       message='Password must contain at least 8 characters, one uppercase, one lowercase, one digit, and one special character'
                                   )])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password_confirm')
    
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("First name can only contain letters")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("Last name can only contain letters")
        return value.strip()
    
    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty")
        return value.lower().strip()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class PositionSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Position
        fields = ('id', 'title', 'description', 'tags', 'image_url', 'department', 'type', 'type_display', 'status', 'status_display')
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value.strip()
    
    def validate_image_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Image URL must be a valid URL")
        return value

class JobApplicationSerializer(serializers.ModelSerializer):
    position_title = serializers.CharField(source='position.title', read_only=True)
    name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='applied_at', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ('id', 'position', 'position_title', 'first_name', 'last_name', 'name', 'email', 'resume', 'status', 'status_display', 'applied_at', 'date')
        read_only_fields = ('id', 'status', 'applied_at', 'name', 'date', 'status_display')
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("First name can only contain letters")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("Last name can only contain letters")
        return value.strip()
    
    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty")
        return value.lower().strip()
    
    def validate_resume(self, value):
        if not value:
            raise serializers.ValidationError("Resume file is required")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(f"Resume must be one of: {', '.join(allowed_extensions)}")
        
        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("Resume file must be smaller than 5MB")
        
        return value

class ContactSubmissionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='submitted_at', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ContactSubmission
        fields = ('id', 'first_name', 'last_name', 'name', 'email', 'phone', 'subject', 'message', 'status', 'status_display', 'submitted_at', 'date')
        read_only_fields = ('id', 'status', 'submitted_at', 'name', 'date', 'status_display')
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("First name can only contain letters")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name cannot be empty")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long")
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("Last name can only contain letters")
        return value.strip()
    
    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty")
        return value.lower().strip()
    
    def validate_phone(self, value):
        if value and not value.strip().replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Phone number can only contain digits, +, -, and spaces")
        return value.strip() if value else value
    
    def validate_subject(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Subject cannot be empty")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Subject must be at least 3 characters long")
        return value.strip()
    
    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long")
        return value.strip()

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            if not user.is_staff:
                raise serializers.ValidationError('Access denied. Admin privileges required.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')
