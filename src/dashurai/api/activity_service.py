"""
Activity service for managing activity logging and retrieval.
Provides reusable functions for creating and fetching activity records.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError

from .models import Activity

logger = logging.getLogger(__name__)


def create_activity(activity_type: str, action: str, description: str) -> Optional[Activity]:
    """
    Create a new activity record in the database.
    
    Args:
        activity_type: Type of activity ('position', 'application', 'contact_form')
        action: Action performed ('created', 'updated', 'closed', 'reviewed', 'deleted', 'interview', 'responded')
        description: Human-readable description of the activity
    
    Returns:
        Activity object if successful, None if failed
    """
    try:
        with transaction.atomic():
            activity = Activity.objects.create(
                type=activity_type,
                action=action,
                description=description
            )
            logger.info(f"Created activity: {activity_type} - {action}: {description}")
            return activity
    except DatabaseError as e:
        logger.error(f"Failed to create activity: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating activity: {e}")
        return None


def get_recent_activities(limit: int = 20) -> List[Activity]:
    """
    Get the most recent activities ordered by creation date.
    
    Args:
        limit: Maximum number of activities to return (default: 20)
    
    Returns:
        List of Activity objects ordered by most recent first
    """
    try:
        activities = Activity.objects.select_for_update().order_by('-created_at')[:limit]
        return list(activities)
    except DatabaseError as e:
        logger.error(f"Failed to fetch recent activities: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching activities: {e}")
        return []


def activity_to_dict(activity: Activity) -> Dict[str, Any]:
    """
    Convert Activity object to dictionary format for API responses.
    
    Args:
        activity: Activity object to convert
    
    Returns:
        Dictionary representation of the activity
    """
    return {
        'id': activity.id,
        'type': activity.type,
        'action': activity.action,
        'description': activity.description,
        'created_at': activity.created_at.isoformat() if activity.created_at else None
    }


def create_position_activity(title: str, action: str) -> Optional[Activity]:
    """
    Helper function to create position-related activities.
    
    Args:
        title: Position title
        action: Action performed ('created', 'updated', 'closed')
    
    Returns:
        Activity object if successful, None if failed
    """
    descriptions = {
        'created': f"New position added: {title}",
        'updated': f"Position updated: {title}",
        'closed': f"Position closed: {title}",
        'deleted': f"Position deleted: {title}"
    }
    
    description = descriptions.get(action, f"Position {action}: {title}")
    return create_activity('position', action, description)


def create_application_activity(position_title: str, applicant_name: str, action: str) -> Optional[Activity]:
    """
    Helper function to create application-related activities.
    
    Args:
        position_title: Title of the position
        applicant_name: Name of the applicant
        action: Action performed ('created', 'reviewed', 'interview')
    
    Returns:
        Activity object if successful, None if failed
    """
    descriptions = {
        'created': f"New application for {position_title}",
        'reviewed': f"Application reviewed: {applicant_name}",
        'interview': f"Interview scheduled: {applicant_name}"
    }
    
    description = descriptions.get(action, f"Application {action}: {applicant_name}")
    return create_activity('application', action, description)


def create_contact_activity(name: str, action: str) -> Optional[Activity]:
    """
    Helper function to create contact form-related activities.
    
    Args:
        name: Contact person's name
        action: Action performed ('created', 'responded')
    
    Returns:
        Activity object if successful, None if failed
    """
    descriptions = {
        'created': "New contact form submission",
        'responded': f"Response sent to inquiry from {name}"
    }
    
    description = descriptions.get(action, f"Contact {action}: {name}")
    return create_activity('contact_form', action, description)
