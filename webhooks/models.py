"""
Webhook models for the Product Importer application.
"""

from django.db import models


class Webhook(models.Model):
    """
    Webhook model for external notifications.
    """
    EVENT_PRODUCT_CREATED = 'product_created'
    EVENT_PRODUCT_UPDATED = 'product_updated'
    EVENT_PRODUCT_DELETED = 'product_deleted'
    EVENT_PRODUCT_IMPORTED = 'product_imported'
    EVENT_BULK_DELETE = 'bulk_delete'
    
    EVENT_CHOICES = [
        (EVENT_PRODUCT_CREATED, 'Product Created'),
        (EVENT_PRODUCT_UPDATED, 'Product Updated'),
        (EVENT_PRODUCT_DELETED, 'Product Deleted'),
        (EVENT_PRODUCT_IMPORTED, 'Products Imported'),
        (EVENT_BULK_DELETE, 'Bulk Delete'),
    ]

    url = models.URLField(max_length=500, help_text="Webhook endpoint URL")
    event_type = models.CharField(
        max_length=50, 
        choices=EVENT_CHOICES,
        help_text="Event type that triggers this webhook"
    )
    is_active = models.BooleanField(default=True, help_text="Whether the webhook is active")
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_response_code = models.IntegerField(null=True, blank=True)
    last_response_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.url}"
