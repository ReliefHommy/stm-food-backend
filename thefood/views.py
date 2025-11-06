#thefood/views.py
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from django.http import FileResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics,permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product,Order
from .serializers import ProductSerializer,OrderCreateSerializer,OrderSerializer


#download_receipt
@login_required
def download_receipt(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        # Alternatively, you can use:
        # order = get_object_or_404(Order, id=order_id, user=request.user)
    except Order.DoesNotExist:
        raise Http404("Order does not exist")

    #if order.user != request.user:
        #raise PermissionDenied("You do not have permission to access this receipt.")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    #width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800 - 100, "Order Receipt")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 770, f"Order ID: {order.id}")
    p.drawString(100, 750, f"Name: {order.full_name}")
    p.drawString(100, 730, f"Phone: {order.phone}")
    p.drawString(100, 710, f"Total: {order.total_amount} kr")

    p.drawString(100, 680, "Items:")
    
    y = 660
 
    for item in order.items.all():
        p.drawString(120, y, f"{item.product.title} × {item.quantity} = {item.price_at_purchase * item.quantity} kr")
        y -= 20

    

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'receipt_order_{order.id}.pdf')


#ProductViewSet
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
    

#VendorProductListCreateView
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
#OrderViewSet    
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
    
#OrderCreateView
class OrderCreateAPIView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return response  # ✅ Automatically includes serialized data
    

#UserOrderListView
class OrderListAPIView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)
#OrderDetailView
class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            if user.is_partner and hasattr(user,'partner_store'):
                order = Order.objects.get(pk=pk, store=user.partner_store)
            else:
                order = Order.objects.get(pk=pk, user=user)

            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found'},status=404)
        