"""
Serializers for the Product Importer API.
"""

from rest_framework import serializers
from .models import Product, UploadJob


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'description', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_sku(self, value):
        """Normalize SKU to lowercase."""
        return value.strip().lower() if value else value


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'price', 'is_active']

    def validate_sku(self, value):
        """Normalize SKU to lowercase and check for uniqueness on create."""
        normalized = value.strip().lower() if value else value
        
        # For updates, exclude the current instance from uniqueness check
        instance = getattr(self, 'instance', None)
        queryset = Product.objects.filter(sku=normalized)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        
        return normalized


class UploadJobSerializer(serializers.ModelSerializer):
    """Serializer for UploadJob model."""
    progress_percentage = serializers.ReadOnlyField()
    is_complete = serializers.ReadOnlyField()
    
    class Meta:
        model = UploadJob
        fields = [
            'id', 'filename', 'status', 'total_rows', 'processed_rows',
            'successful_rows', 'failed_rows', 'error_message',
            'progress_percentage', 'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload."""
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        """Validate that the uploaded file is a CSV."""
        if not value.name.lower().endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value
