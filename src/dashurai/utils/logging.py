"""
Logging utilities for DashurAI application.
Provides convenient logging functions with consistent formatting.
"""

import logging
from django.conf import settings


def get_logger(name):
    """
    Get a logger instance with the specified name.
    
    Args:
        name (str): The name of the logger (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_api_request(request, response=None, exception=None):
    """
    Log API requests with relevant information.
    
    Args:
        request: Django request object
        response: Django response object (optional)
        exception: Exception if request failed (optional)
    """
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
    """
    Log security-related events.
    
    Args:
        event_type (str): Type of security event (login, logout, failed_login, etc.)
        details (str): Details about the event
        user: User object if applicable (optional)
    """
    logger = get_logger('django.security')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    logger.info(f"Security Event - {event_type}: {details} - {user_info}")


def log_cms_action(action, model_name, instance_id=None, user=None):
    """
    Log CMS-related actions.
    
    Args:
        action (str): Type of action (create, update, delete, publish, etc.)
        model_name (str): Name of the model being acted upon
        instance_id: ID of the instance (optional)
        user: User performing the action (optional)
    """
    logger = get_logger('cms')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    instance_info = f"ID: {instance_id}" if instance_id else ""
    logger.info(f"CMS {action}: {model_name} {instance_info} - {user_info}")


def log_user_action(action, user, details=None):
    """
    Log user-related actions.
    
    Args:
        action (str): Type of action (register, login, profile_update, etc.)
        user: User object
        details (str): Additional details (optional)
    """
    logger = get_logger('users')
    
    details_info = f" - {details}" if details else ""
    logger.info(f"User {action}: {user.id} ({user.email}){details_info}")


def log_career_action(action, job_id=None, user=None, details=None):
    """
    Log career-related actions.
    
    Args:
        action (str): Type of action (view, apply, list, etc.)
        job_id: ID of the job (optional)
        user: User object (optional)
        details (str): Additional details (optional)
    """
    logger = get_logger('careers')
    
    job_info = f"Job: {job_id}" if job_id else "Job: all"
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    details_info = f" - {details}" if details else ""
    logger.info(f"Career {action}: {job_info} - {user_info}{details_info}")


def log_contact_action(action, user=None, details=None):
    """
    Log contact-related actions.
    
    Args:
        action (str): Type of action (submit, view, etc.)
        user: User object (optional)
        details (str): Additional details (optional)
    """
    logger = get_logger('contact')
    
    user_info = f"User: {getattr(user, 'id', 'anonymous')}" if user else "User: anonymous"
    details_info = f" - {details}" if details else ""
    logger.info(f"Contact {action}: {user_info}{details_info}")
