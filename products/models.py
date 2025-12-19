"""
Product models for the Product Importer application.
"""

import uuid
from django.db import models


class Product(models.Model):
    """
    Product model representing items that can be imported from CSV.
    SKU is unique and case-insensitive (stored as lowercase).
    """
    sku = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique product identifier (case-insensitive)"
    )
    name = models.CharField(max_length=255, help_text="Product name")
    description = models.TextField(blank=True, null=True, help_text="Product description")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Product price"
    )
    is_active = models.BooleanField(default=True, help_text="Whether the product is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        # Normalize SKU to lowercase for case-insensitive uniqueness
        if self.sku:
            self.sku = self.sku.strip().lower()
        super().save(*args, **kwargs)


class UploadJob(models.Model):
    """
    Tracks the progress of a CSV upload job.
    """
    STATUS_PENDING = 'pending'
    STATUS_PARSING = 'parsing'
    STATUS_VALIDATING = 'validating'
    STATUS_IMPORTING = 'importing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PARSING, 'Parsing CSV'),
        (STATUS_VALIDATING, 'Validating'),
        (STATUS_IMPORTING, 'Importing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} - {self.status}"

    @property
    def progress_percentage(self):
        """Calculate the progress percentage."""
        if self.total_rows == 0:
            return 0
        return round((self.processed_rows / self.total_rows) * 100, 1)

    @property
    def is_complete(self):
        """Check if the job is complete (success or failure)."""
        return self.status in (self.STATUS_COMPLETED, self.STATUS_FAILED)
