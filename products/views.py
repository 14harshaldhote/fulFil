"""
API views for the Product Importer application.
"""

import os
import uuid
import json
import time
import logging
from django.http import StreamingHttpResponse, JsonResponse
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

logger = logging.getLogger(__name__)


# Check if Celery/Redis is available
def is_celery_available():
    """Check if Celery broker is accessible."""
    try:
        from config.celery import app
        # Try to ping the broker
        app.control.ping(timeout=0.5)
        return True
    except Exception:
        return False


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
        from .tasks import delete_all_products
        
        if is_celery_available():
            delete_all_products.delay()
            return Response(
                {'message': 'Bulk delete initiated. All products will be deleted.'},
                status=status.HTTP_202_ACCEPTED
            )
        else:
            # Sync fallback
            count = Product.objects.count()
            Product.objects.all().delete()
            return Response(
                {'message': f'Deleted {count} products.'},
                status=status.HTTP_200_OK
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
        
        # Try async first, fallback to sync
        if is_celery_available():
            from .tasks import process_csv_upload
            process_csv_upload.delay(str(job.id), file_path)
            logger.info(f"Queued async CSV processing for job {job.id}")
        else:
            # Process synchronously if Celery not available
            logger.warning("Celery not available, processing CSV synchronously")
            self._process_sync(job, file_path)
        
        return Response(
            UploadJobSerializer(job).data,
            status=status.HTTP_202_ACCEPTED
        )
    
    def _process_sync(self, job, file_path):
        """Process CSV synchronously when Celery is not available."""
        import csv
        from decimal import Decimal, InvalidOperation
        from django.db import transaction
        
        BATCH_SIZE = 5000
        
        try:
            job.status = UploadJob.STATUS_PARSING
            job.save()
            
            # Read CSV
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                job.total_rows = len(rows)
                job.save()
            
            if job.total_rows == 0:
                job.status = UploadJob.STATUS_COMPLETED
                job.error_message = "CSV file is empty."
                job.save()
                return
            
            job.status = UploadJob.STATUS_IMPORTING
            job.save()
            
            # Get existing SKUs to track duplicates
            existing_skus = set(Product.objects.values_list('sku', flat=True))
            
            # Statistics
            processed = 0
            new_products = 0
            duplicates = 0
            failed = 0
            skipped = 0
            
            batch = []
            skus_in_batch = set()
            skus_in_file = set()  # Track all valid SKUs in this file
            
            for row in rows:
                processed += 1
                
                try:
                    # Get raw values
                    raw_sku = row.get('sku', '')
                    
                    # Check for blank/empty row
                    if not raw_sku or not raw_sku.strip():
                        failed += 1  # Missing SKU = failed
                        continue
                    
                    sku = raw_sku.strip().lower()
                    name = row.get('name', '').strip()
                    description = row.get('description', '').strip() if row.get('description') else ''
                    
                    # Parse price
                    price = None
                    price_str = row.get('price', '').strip()
                    if price_str:
                        try:
                            price = Decimal(price_str)
                            if price < 0:
                                price = None
                        except (InvalidOperation, ValueError):
                            pass
                    
                    if not name:
                        name = sku
                    
                    # Check if duplicate within this file (same SKU appears multiple times)
                    if sku in skus_in_file:
                        # This is a duplicate within the file - count it
                        duplicates += 1
                        # Remove old entry from batch, add new one
                        batch = [p for p in batch if p.sku != sku]
                    elif sku in existing_skus:
                        # This SKU exists in DB - will be overwritten
                        duplicates += 1
                    else:
                        # New product
                        new_products += 1
                    
                    skus_in_file.add(sku)
                    skus_in_batch.add(sku)
                    batch.append(Product(
                        sku=sku,
                        name=name,
                        description=description,
                        price=price,
                        is_active=True
                    ))
                    
                    # Process batch
                    if len(batch) >= BATCH_SIZE:
                        self._save_batch(batch)
                        batch = []
                        skus_in_batch = set()
                        
                        job.processed_rows = processed
                        job.successful_rows = new_products
                        job.duplicate_rows = duplicates
                        job.failed_rows = failed
                        job.skipped_rows = skipped
                        job.save()
                        
                except Exception as e:
                    logger.error(f"Error processing row {processed}: {e}")
                    skipped += 1
            
            # Save remaining batch
            if batch:
                self._save_batch(batch)
            
            job.processed_rows = processed
            job.successful_rows = new_products
            job.duplicate_rows = duplicates
            job.failed_rows = failed
            job.skipped_rows = skipped
            job.status = UploadJob.STATUS_COMPLETED
            job.save()
            
            logger.info(f"CSV import: {new_products} new, {duplicates} duplicates, {failed} failed, {skipped} skipped")
            
        except Exception as e:
            logger.exception(f"Error processing CSV: {e}")
            job.status = UploadJob.STATUS_FAILED
            job.error_message = str(e)
            job.save()
        finally:
            # Cleanup file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
    
    def _save_batch(self, products):
        """Save batch using bulk_create with upsert."""
        from django.db import transaction
        
        with transaction.atomic():
            Product.objects.bulk_create(
                products,
                update_conflicts=True,
                unique_fields=['sku'],
                update_fields=['name', 'description', 'price', 'is_active', 'updated_at']
            )


class UploadStatusView(APIView):
    """
    API view for checking upload job status.
    Supports both regular JSON response and Server-Sent Events (SSE).
    """
    # Disable DRF content negotiation for this view
    content_negotiation_class = None

    def get(self, request, job_id):
        """Get upload job status."""
        try:
            job = UploadJob.objects.get(id=job_id)
        except UploadJob.DoesNotExist:
            return JsonResponse(
                {'error': 'Upload job not found'},
                status=404
            )
        
        # Check if SSE is requested
        accept_header = request.headers.get('Accept', '')
        if 'text/event-stream' in accept_header:
            return self._sse_response(job_id)
        
        # Return JSON response
        data = UploadJobSerializer(job).data
        return JsonResponse(data)

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
                    
                    time.sleep(0.5)
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
