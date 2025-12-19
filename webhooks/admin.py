"""
Admin configuration for Webhooks app.
"""

from django.contrib import admin
from .models import Webhook


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'event_type', 'is_active', 'last_triggered_at', 'last_response_code')
    list_filter = ('event_type', 'is_active', 'created_at')
    search_fields = ('url',)
    ordering = ('-created_at',)
    readonly_fields = ('last_triggered_at', 'last_response_code', 'last_response_time_ms', 'created_at', 'updated_at')
