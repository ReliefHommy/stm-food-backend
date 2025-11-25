from django.urls import path, include
from rest_framework.routers import DefaultRouter
from thefood.views import OrderListAPIView
from .views import ProductViewSet, OrderViewSet,OrderCreateAPIView,OrderListAPIView,OrderDetailAPIView



router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='orders')



urlpatterns = [
  
    # ViewSet routes: /products/, /orders/
    path("", include(router.urls)),

    # Extra order endpoints
    path('orders/create', OrderCreateAPIView.as_view(), name='order-create'),
    path('my-orders/', OrderListAPIView.as_view(), name='my-order-list'),
    path('my-orders/<int:pk>/', OrderDetailAPIView.as_view(), name='my-order-detail'),
 
]
