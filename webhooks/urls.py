"""
URL configuration for the webhooks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookViewSet

router = DefaultRouter()
router.register(r'webhooks', WebhookViewSet, basename='webhook')

urlpatterns = [
    path('', include(router.urls)),
]
