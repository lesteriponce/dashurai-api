from rest_framework import serializers
from .models import Activity

class ActivitySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Activity
        fields = ['id', 'type', 'action', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_type(self, value):
        # Validate that the type is one of the allowed choices.
        valid_types = [choice[0] for choice in Activity.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid type. Must be one of: {valid_types}")
        return value
    
    def validate_action(self, value):
        # Validate that the action is one of the allowed choices.
        valid_actions = [choice[0] for choice in Activity.ACTION_CHOICES]
        if value not in valid_actions:
            raise serializers.ValidationError(f"Invalid action. Must be one of: {valid_actions}")
        return value


class ActivityListSerializer(serializers.Serializer):
    
    activities = ActivitySerializer(many=True)
    
    class Meta:
        fields = ['activities']
