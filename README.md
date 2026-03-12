# DashurAI API

A Django REST API with Wagtail CMS integration for managing careers, contact forms, and content management.

## Features

- **Authentication**: JWT-based authentication with refresh tokens
- **Careers**: Job postings and application management
- **Contact**: Contact form submissions
- **CMS**: Document, image, and page management via Wagtail
- **Admin**: Full admin interface for content management
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Security**: Rate limiting, CORS, security headers
- **Logging**: Comprehensive logging system

## Tech Stack

- **Backend**: Django 5.1.4
- **API Framework**: Django REST Framework 3.15.2
- **Authentication**: django-rest-framework-simplejwt
- **CMS**: Wagtail 6.3.1
- **API Documentation**: drf-spectacular
- **Security**: django-ratelimit, django-cors-headers
- **Cache**: Redis (with file fallback)
- **Image Processing**: Pillow

## Prerequisites

- Python 3.8+
- Redis (optional, falls back to file cache)
- Git

## Installation

### 1. Clone the Repository

git clone https://github.com/lesteriponce/dashurai-api.git
cd dashurai-api


### 2. Create Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


### 3. Install Dependencies

pip install -r requirements.txt


### 4. Environment Configuration

Copy the example environment file and configure your settings:

cp .env.example .env

Edit `.env` with your configuration:


# Required
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Security (production)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False


### 5. Database Setup

# Navigate to the Django project directory
cd src/dashurai

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic


### 6. Start the Development Server

python manage.py runserver


The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access the API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## API Endpoints

### Base URL

http://localhost:8000/api/v1/


### Authentication
- `POST /auth/login/` - User login
- `POST /auth/register/` - User registration
- `POST /auth/refresh/` - Refresh JWT token
- `POST /admin/login/` - Admin login

### Careers
- `GET /careers/positions/` - List active positions
- `GET /careers/positions/{id}/` - Get position details
- `POST /careers/apply/` - Submit job application

### Contact
- `POST /contact/submit/` - Submit contact form

### Admin (Requires Admin Access)
- `GET /admin/applications/` - List all applications
- `PUT /admin/applications/{id}/` - Update application
- `DELETE /admin/applications/{id}/delete/` - Delete application
- `GET /admin/contacts/` - List all contacts
- `PUT /admin/contacts/{id}/` - Update contact
- `DELETE /admin/contacts/{id}/delete/` - Delete contact
- `GET /admin/positions/` - List all positions
- `POST /admin/positions/create/` - Create position
- `PUT /admin/positions/{id}/` - Update position
- `DELETE /admin/positions/{id}/delete/` - Delete position

### CMS Content
- `GET /content/documents/` - List documents
- `GET /content/documents/{id}/` - Get document details
- `GET /content/documents/find/` - Find documents
- `GET /content/images/` - List images
- `GET /content/images/{id}/` - Get image details
- `GET /content/images/find/` - Find images
- `GET /content/pages/` - List pages
- `GET /content/pages/{id}/` - Get page details
- `POST /content/pages/{id}/action/{action}/` - Execute page action
- `GET /content/pages/find/` - Find pages

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

Authorization: Bearer <your-access-token>


### Token Flow

1. Login to get access and refresh tokens
2. Use access token for API requests
3. Refresh token when it expires
4. Use refresh token to get new access token

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 3-5 requests per minute
- **Contact form**: 2 requests per minute
- **Job applications**: 3 requests per hour
- **Content endpoints**: 30-60 requests per minute

## Admin Interface

Access the Wagtail CMS admin interface at:
- **Admin**: http://localhost:8000/admin/
- **CMS**: http://localhost:8000/cms/

## Development

### Code Style

This project follows PEP 8 style guidelines.

### Logging

Logs are written to the `logs/` directory:
- `django.log` - General application logs
- `django_error.log` - Error logs
- `security.log` - Security-related logs
- `api.log` - API request/response logs

## Production Deployment

### Security Settings

For production, ensure these settings in `.env`:

DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True


### Environment Variables

Required production variables:
- `SECRET_KEY` - Generate a strong secret key
- `DEBUG=False` - Disable debug mode
- `ALLOWED_HOSTS` - dashurai.com

### Database

For production, consider using PostgreSQL instead of SQLite:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dashurai_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


### Static Files

Configure static files serving for production:

python manage.py collectstatic --noinput


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.

## Changelog

### v1.0.0
- Initial release
- JWT authentication
- Careers management
- Contact forms
- CMS integration
- API documentation
