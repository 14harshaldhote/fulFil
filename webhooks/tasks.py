"""
Celery tasks for webhook processing.
"""

import logging
import time
import requests
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10  # seconds


@shared_task
def trigger_webhooks(event_type: str, payload: dict):
    """
    Trigger all active webhooks for a given event type.
    
    Args:
        event_type: The type of event that occurred
        payload: The data to send to webhooks
    """
    from .models import Webhook
    
    webhooks = Webhook.objects.filter(event_type=event_type, is_active=True)
    
    for webhook in webhooks:
        try:
            _send_webhook(webhook.id, event_type, payload)
        except Exception as e:
            logger.error(f"Failed to trigger webhook {webhook.id}: {e}")


@shared_task
def send_webhook_async(webhook_id: int, event_type: str, payload: dict):
    """
    Send a webhook asynchronously.
    
    Args:
        webhook_id: ID of the webhook to trigger
        event_type: The type of event
        payload: The data to send
    """
    _send_webhook(webhook_id, event_type, payload)


def _send_webhook(webhook_id: int, event_type: str, payload: dict):
    """
    Actually send the webhook request.
    
    Args:
        webhook_id: ID of the webhook
        event_type: The type of event
        payload: The data to send
    """
    from .models import Webhook
    
    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
        return
    
    data = {
        'event': event_type,
        'timestamp': timezone.now().isoformat(),
        'payload': payload
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            webhook.url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'X-Webhook-Event': event_type,
            },
            timeout=WEBHOOK_TIMEOUT
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Update webhook with last trigger info
        webhook.last_triggered_at = timezone.now()
        webhook.last_response_code = response.status_code
        webhook.last_response_time_ms = response_time_ms
        webhook.save()
        
        logger.info(f"Webhook {webhook_id} triggered: {response.status_code} in {response_time_ms}ms")
        
    except requests.exceptions.Timeout:
        webhook.last_triggered_at = timezone.now()
        webhook.last_response_code = 0
        webhook.last_response_time_ms = WEBHOOK_TIMEOUT * 1000
        webhook.save()
        logger.warning(f"Webhook {webhook_id} timed out")
        
    except requests.exceptions.RequestException as e:
        webhook.last_triggered_at = timezone.now()
        webhook.last_response_code = 0
        webhook.last_response_time_ms = None
        webhook.save()
        logger.error(f"Webhook {webhook_id} failed: {e}")


def test_webhook_sync(webhook) -> dict:
    """
    Test a webhook synchronously and return the result.
    
    Args:
        webhook: The Webhook instance to test
        
    Returns:
        dict with success, response_code, response_time_ms, and error
    """
    data = {
        'event': 'test',
        'timestamp': timezone.now().isoformat(),
        'payload': {'message': 'This is a test webhook'}
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            webhook.url,
            json=data,
            headers={
                'Content-Type': 'application/json',
                'X-Webhook-Event': 'test',
            },
            timeout=WEBHOOK_TIMEOUT
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Update webhook with test info
        webhook.last_triggered_at = timezone.now()
        webhook.last_response_code = response.status_code
        webhook.last_response_time_ms = response_time_ms
        webhook.save()
        
        return {
            'success': 200 <= response.status_code < 300,
            'response_code': response.status_code,
            'response_time_ms': response_time_ms,
            'error': None if 200 <= response.status_code < 300 else f"HTTP {response.status_code}"
        }
        
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'response_code': None,
            'response_time_ms': WEBHOOK_TIMEOUT * 1000,
            'error': 'Request timed out'
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'response_code': None,
            'response_time_ms': None,
            'error': str(e)
        }
