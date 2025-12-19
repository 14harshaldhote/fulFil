"""
URL configuration for the products app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, FileUploadView, UploadStatusView, UploadJobViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'upload-jobs', UploadJobViewSet, basename='upload-job')

urlpatterns = [
    # Custom URLs must come BEFORE router.urls
    path('products/upload/', FileUploadView.as_view(), name='product-upload'),
    path('products/upload/<uuid:job_id>/status/', UploadStatusView.as_view(), name='upload-status'),
    path('', include(router.urls)),
]
