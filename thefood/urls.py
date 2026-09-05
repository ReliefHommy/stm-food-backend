from django.urls import path, include
from rest_framework.routers import DefaultRouter
from thefood.views import OrderListAPIView
from .views import ProductViewSet, OrderViewSet,OrderCreateAPIView,OrderListAPIView,OrderDetailAPIView,VendorProductListCreateView,CategoryViewSet,StoreLocationViewSet,UserProfileListView,StoreProfileListView,PartnerStoreDetailView,BlogViewSet



router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'store-locations', StoreLocationViewSet, basename='storelocation')
router.register(r'blog', BlogViewSet, basename='blog')





urlpatterns = [
  
    # Vendor Create new products
    path('vendor/products/', VendorProductListCreateView.as_view(), name='vendor-product-list-create'),
    path('stores/<slug:slug>/', PartnerStoreDetailView.as_view(), name='store-detail'),
    path("", include(router.urls)),

    # Extra order endpoints
    path('orders/create', OrderCreateAPIView.as_view(), name='order-create'),
    path('my-orders/', OrderListAPIView.as_view(), name='my-order-list'),
    path('my-orders/<int:pk>/', OrderDetailAPIView.as_view(), name='my-order-detail'),

    path("userprofiles/", UserProfileListView.as_view(), name="userprofile-list"),
    path("storeprofiles/", StoreProfileListView.as_view(), name="storeprofile-list"),
]
    
 

