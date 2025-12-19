"""
Serializers for the Webhooks API.
"""

from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    """Serializer for Webhook model."""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = Webhook
        fields = [
            'id', 'url', 'event_type', 'event_type_display', 'is_active',
            'last_triggered_at', 'last_response_code', 'last_response_time_ms',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_triggered_at', 'last_response_code', 
                          'last_response_time_ms', 'created_at', 'updated_at']


class WebhookCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating webhooks."""
    
    class Meta:
        model = Webhook
        fields = ['url', 'event_type', 'is_active']


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for webhook test results."""
    success = serializers.BooleanField()
    response_code = serializers.IntegerField(allow_null=True)
    response_time_ms = serializers.IntegerField(allow_null=True)
    error = serializers.CharField(allow_null=True, allow_blank=True)
