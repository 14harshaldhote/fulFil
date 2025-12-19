"""
Celery tasks for processing CSV uploads.
"""

import csv
import logging
import os
from celery import shared_task
from django.db import transaction
from django.conf import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000  # Number of records to process in each batch


@shared_task(bind=True)
def process_csv_upload(self, job_id: str, file_path: str):
    """
    Process a CSV file upload in the background.
    
    Args:
        job_id: UUID of the UploadJob
        file_path: Path to the uploaded CSV file
    """
    from .models import Product, UploadJob
    from webhooks.tasks import trigger_webhooks
    
    try:
        job = UploadJob.objects.get(id=job_id)
    except UploadJob.DoesNotExist:
        logger.error(f"UploadJob {job_id} not found")
        return
    
    try:
        # Update status to parsing
        job.status = UploadJob.STATUS_PARSING
        job.save()
        
        # Count total rows first (for progress tracking)
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            job.total_rows = len(rows)
            job.save()
        
        if job.total_rows == 0:
            job.status = UploadJob.STATUS_COMPLETED
            job.error_message = "CSV file is empty or has no valid rows."
            job.save()
            return

        # Update status to importing
        job.status = UploadJob.STATUS_IMPORTING
        job.save()
        
        # Track statistics
        successful = 0
        failed = 0
        processed = 0
        
        # Process in batches
        batch = []
        skus_in_batch = set()
        
        for row in rows:
            processed += 1
            
            try:
                # Extract and validate required fields
                sku = row.get('sku', '').strip().lower()
                name = row.get('name', '').strip()
                description = row.get('description', '').strip() if row.get('description') else ''
                
                if not sku:
                    failed += 1
                    continue
                
                if not name:
                    name = sku  # Use SKU as name if name is empty
                
                # Skip duplicates within the same batch (keep last occurrence)
                if sku in skus_in_batch:
                    # Remove previous entry with same SKU
                    batch = [p for p in batch if p.sku != sku]
                
                skus_in_batch.add(sku)
                batch.append(Product(
                    sku=sku,
                    name=name,
                    description=description,
                    is_active=True
                ))
                successful += 1
                
                # Process batch when it reaches the batch size
                if len(batch) >= BATCH_SIZE:
                    _save_batch(batch)
                    batch = []
                    skus_in_batch = set()
                    
                    # Update progress
                    job.processed_rows = processed
                    job.successful_rows = successful
                    job.failed_rows = failed
                    job.save()
                    
            except Exception as e:
                logger.error(f"Error processing row {processed}: {e}")
                failed += 1
        
        # Save remaining batch
        if batch:
            _save_batch(batch)
        
        # Final update
        job.processed_rows = processed
        job.successful_rows = successful
        job.failed_rows = failed
        job.status = UploadJob.STATUS_COMPLETED
        job.save()
        
        # Trigger webhooks for bulk import
        trigger_webhooks.delay('product_imported', {
            'job_id': str(job.id),
            'total_imported': successful,
            'total_failed': failed
        })
        
        logger.info(f"CSV upload completed: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.exception(f"Error processing CSV upload: {e}")
        job.status = UploadJob.STATUS_FAILED
        job.error_message = str(e)
        job.save()
    
    finally:
        # Clean up the uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up file {file_path}: {e}")


def _save_batch(products: list):
    """
    Save a batch of products using bulk_create with update_conflicts.
    
    Args:
        products: List of Product instances to save
    """
    from .models import Product
    
    with transaction.atomic():
        Product.objects.bulk_create(
            products,
            update_conflicts=True,
            unique_fields=['sku'],
            update_fields=['name', 'description', 'is_active', 'updated_at']
        )


@shared_task
def delete_all_products():
    """Delete all products from the database."""
    from .models import Product
    from webhooks.tasks import trigger_webhooks
    
    count = Product.objects.count()
    Product.objects.all().delete()
    
    # Trigger webhook for bulk delete
    trigger_webhooks.delay('bulk_delete', {
        'deleted_count': count
    })
    
    logger.info(f"Deleted all {count} products")
    return count
