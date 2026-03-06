import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError
from .models import Activity

logger = logging.getLogger(__name__)

def create_activity(activity_type: str, action: str, description: str) -> Optional[Activity]:

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

    try:
        activities = Activity.objects.order_by('-created_at')[:limit]
        return list(activities)
    except DatabaseError as e:
        logger.error(f"Failed to fetch recent activities: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching activities: {e}")
        return []


def activity_to_dict(activity: Activity) -> Dict[str, Any]:
    return {
        'id': activity.id,
        'type': activity.type,
        'action': activity.action,
        'description': activity.description,
        'created_at': activity.created_at.isoformat() if activity.created_at else None
    }


def create_position_activity(title: str, action: str) -> Optional[Activity]:
    descriptions = {
        'created': f"New position added: {title}",
        'updated': f"Position updated: {title}",
        'closed': f"Position closed: {title}",
        'deleted': f"Position deleted: {title}"
    }
    
    description = descriptions.get(action, f"Position {action}: {title}")
    return create_activity('position', action, description)


def create_application_activity(position_title: str, applicant_name: str, action: str) -> Optional[Activity]:
    descriptions = {
        'created': f"New application for {position_title}",
        'reviewed': f"Application reviewed: {applicant_name}",
        'interview': f"Interview scheduled: {applicant_name}"
    }
    
    description = descriptions.get(action, f"Application {action}: {applicant_name}")
    return create_activity('application', action, description)


def create_contact_activity(name: str, action: str) -> Optional[Activity]:
    descriptions = {
        'created': "New contact form submission",
        'responded': f"Response sent to inquiry from {name}"
    }
    
    description = descriptions.get(action, f"Contact {action}: {name}")
    return create_activity('contact_form', action, description)
