import logging
from django.conf import settings


def get_logger(name):
    return logging.getLogger(name)


def log_api_request(request, response=None, exception=None):
    logger = get_logger('api.requests')
    
    if exception:
        logger.error(
            f"API Request Failed: {request.method} {request.path} - "
            f"User: {getattr(request.user, 'id', 'anonymous')} - "
            f"Error: {str(exception)}"
        )
    else:
        status_code = getattr(response, 'status_code', 'N/A')
        logger.info(
            f"API Request: {request.method} {request.path} - "
            f"Status: {status_code} - "
            f"User: {getattr(request.user, 'id', 'anonymous')}"
        )


def log_security_event(event_type, details, user=None):
    logger = get_logger('django.security')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    logger.info(f"Security Event - {event_type}: {details} - {user_info}")


def log_cms_action(action, model_name, instance_id=None, user=None):
    logger = get_logger('cms')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    instance_info = f"ID: {instance_id}" if instance_id else ""
    logger.info(f"CMS {action}: {model_name} {instance_info} - {user_info}")


def log_user_action(action, user, details=None):
    logger = get_logger('users')
    
    details_info = f" - {details}" if details else ""
    logger.info(f"User {action}: {user.id} ({user.email}){details_info}")


def log_career_action(action, job_id=None, user=None, details=None):
    logger = get_logger('careers')
    
    job_info = f"Job: {job_id}" if job_id else "Job: all"
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    details_info = f" - {details}" if details else ""
    logger.info(f"Career {action}: {job_info} - {user_info}{details_info}")


def log_contact_action(action, user=None, details=None):
    logger = get_logger('contact')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    details_info = f" - {details}" if details else ""
    logger.info(f"Contact {action}: {user_info}{details_info}")
