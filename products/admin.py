"""
Admin configuration for Products app.
"""

from django.contrib import admin
from .models import Product, UploadJob


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('sku', 'name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'status', 'total_rows', 'processed_rows', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('filename',)
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
