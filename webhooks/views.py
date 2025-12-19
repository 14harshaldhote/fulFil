"""
API views for webhook management.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Webhook
from .serializers import WebhookSerializer, WebhookCreateUpdateSerializer, WebhookTestSerializer
from .tasks import test_webhook_sync

logger = logging.getLogger(__name__)


class WebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Webhook CRUD operations.
    """
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'is_active']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WebhookCreateUpdateSerializer
        return WebhookSerializer

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a webhook by sending a test request."""
        webhook = self.get_object()
        
        result = test_webhook_sync(webhook)
        
        return Response(WebhookTestSerializer(result).data)
    
    @action(detail=False, methods=['get'])
    def event_types(self, request):
        """Get available event types."""
        return Response([
            {'value': choice[0], 'label': choice[1]}
            for choice in Webhook.EVENT_CHOICES
        ])
