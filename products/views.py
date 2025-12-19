"""
API views for the Product Importer application.
"""

import os
import uuid
import json
import time
import logging
from django.http import StreamingHttpResponse
from django.conf import settings
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter, BooleanFilter

from .models import Product, UploadJob
from .serializers import (
    ProductSerializer, 
    ProductCreateUpdateSerializer, 
    UploadJobSerializer,
    FileUploadSerializer
)
from .tasks import process_csv_upload, delete_all_products

logger = logging.getLogger(__name__)


class ProductFilter(FilterSet):
    """Filter for Product queryset."""
    sku = CharFilter(lookup_expr='icontains')
    name = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')
    is_active = BooleanFilter()
    
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'is_active']


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.
    
    Supports filtering by sku, name, description, and is_active.
    Supports searching and ordering.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['sku', 'name', 'description']
    ordering_fields = ['sku', 'name', 'created_at', 'updated_at', 'is_active']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Delete all products."""
        # Queue the deletion task
        delete_all_products.delay()
        return Response(
            {'message': 'Bulk delete initiated. All products will be deleted.'},
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get product statistics."""
        total = Product.objects.count()
        active = Product.objects.filter(is_active=True).count()
        inactive = Product.objects.filter(is_active=False).count()
        
        return Response({
            'total': total,
            'active': active,
            'inactive': inactive
        })


class FileUploadView(APIView):
    """
    API view for uploading CSV files.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Handle CSV file upload."""
        serializer = FileUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = serializer.validated_data['file']
        
        # Create media directory if it doesn't exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Generate unique filename and save
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.MEDIA_ROOT, f'{file_id}.csv')
        
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Create upload job
        job = UploadJob.objects.create(
            filename=uploaded_file.name,
            status=UploadJob.STATUS_PENDING
        )
        
        # Queue the processing task
        process_csv_upload.delay(str(job.id), file_path)
        
        return Response(
            UploadJobSerializer(job).data,
            status=status.HTTP_202_ACCEPTED
        )


class UploadStatusView(APIView):
    """
    API view for checking upload job status.
    Supports both regular JSON response and Server-Sent Events (SSE).
    """

    def get(self, request, job_id):
        """Get upload job status."""
        try:
            job = UploadJob.objects.get(id=job_id)
        except UploadJob.DoesNotExist:
            return Response(
                {'error': 'Upload job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if SSE is requested
        if request.headers.get('Accept') == 'text/event-stream':
            return self._sse_response(job_id)
        
        return Response(UploadJobSerializer(job).data)

    def _sse_response(self, job_id):
        """Generate SSE stream for upload progress."""
        def event_stream():
            while True:
                try:
                    job = UploadJob.objects.get(id=job_id)
                    data = UploadJobSerializer(job).data
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    if job.is_complete:
                        break
                    
                    time.sleep(0.5)  # Poll every 500ms
                except UploadJob.DoesNotExist:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break
                except Exception as e:
                    logger.error(f"SSE error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    break
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class UploadJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing upload jobs."""
    queryset = UploadJob.objects.all()
    serializer_class = UploadJobSerializer
    ordering = ['-created_at']
