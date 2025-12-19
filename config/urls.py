"""
URL configuration for Product Importer application.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
    path('api/', include('webhooks.urls')),
    # Frontend views
    path('', TemplateView.as_view(template_name='products/upload.html'), name='home'),
    path('products/', TemplateView.as_view(template_name='products/list.html'), name='product-list'),
    path('webhooks/', TemplateView.as_view(template_name='webhooks/list.html'), name='webhook-list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
