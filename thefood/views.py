
#from rest_framework.permissions import IsAuthenticated
#from rest_framework.permissions import IsAuthenticatedOrReadOnly
#from rest_framework import viewsets
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product,Order
from .serializers import ProductSerializer,OrderSerializer, OrderCreateSerializer

#thefood/views.py

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field ='slug'

    def get_queryset(self):
        user = self.request.user
        # Partners see their own products in the generic list
        if user.is_authenticated and getattr(user, 'is_partner', False):
            return Product.objects.filter(partner_store__user=user)
        return Product.objects.all()
    
    def create(self, request, *args, **kwargs):
        print("📦 Incoming data:", request.data)
        print("📷 Incoming FILES:", request.FILES)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        if not getattr(user, 'is_partner', False):
            raise PermissionDenied("Not authorized")
        
        if not hasattr(user, 'partner_store'):
            raise PermissionDenied("Partner store not found for user.")
       
        serializer.save(partner_store=user.partner_store)
        
    def perform_update(self, serializer):
        obj = self.get_object()
        user = self.request.user
        if user.is_partner and getattr(obj.partner_store, "user_id", None) != user.id:
            raise PermissionDenied("Not allowed to modify this product.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_partner and instance.partner_store.user_id != user.id:
            raise PermissionDenied("You are not allowed to delete this product.")
        instance.delete()
    





class VendorProductListCreateView(APIView):
    """Vendor-only list/create."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'is_partner', False):
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        products = Product.objects.filter(partner_store=request.user.partner_store)
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        if not getattr(request.user, 'is_partner', False):
            return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(partner_store=request.user.partner_store)
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderCreateSerializer
    queryset = Order.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("🛑 Order Validation Errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)