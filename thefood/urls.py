from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, OrderViewSet,VendorProductListCreateView


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='orders')


urlpatterns = [
    # product CRUD via ViewSet
    path('', include(router.urls)),
    
# Vendor - specific create/list endpoint
    path('vendor/products/', VendorProductListCreateView.as_view(), name='vendor-products'),
]
