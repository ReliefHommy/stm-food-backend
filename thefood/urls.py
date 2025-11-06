from django.urls import path, include
from rest_framework.routers import DefaultRouter

from thefood.views import OrderListAPIView
from .views import ProductViewSet, OrderViewSet,OrderCreateAPIView,OrderListAPIView,OrderDetailAPIView
from thefood.views import download_receipt


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='orders')



urlpatterns = [
    # product CRUD via ViewSet
    path('', include(router.urls)),
    path("orders/<int:order_id>/receipt/", download_receipt),
    path('orders/', OrderCreateAPIView.as_view(), name='order-create'),
    path('my-orders/', OrderListAPIView.as_view(), name='my-order-list'),
    path('my-orders/<int:pk>/', OrderDetailAPIView.as_view(), name='my-order-detail'),
    #path('vendor/products/', OrderListAPIView.as_view(), name='vendor-products'),
]
