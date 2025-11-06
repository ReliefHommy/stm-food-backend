from rest_framework import serializers
from .models import Order, OrderItem
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        #fields = '__all__'
        fields = ['id', 'title', 'slug','description', 'price', 'stock_quantity', 'image', 'partner_store', 'created_at']
        read_only_fields = ['id', 'partner_store', 'created_at']

        extra_kwargs = {
            'image': {'required': False, 'allow_null': True},
        }

        

# Nested OrderItem serializer
class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = ['id','product','product_title','quantity','price_at_purchase']


# Read-only Order serializer (for order history)
class OrderSerializer(serializers.ModelSerializer): 
    items = OrderItemSerializer(many=True, read_only=True)
    placed_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    user = serializers.StringRelatedField(read_only=True)


    class Meta:
        model = Order
        fields = ['id','user','full_name','phone','shipping_address','notes','delivery_date',
                  'status','total_amount','placed_at','items',
        ] 


    # Write serializer for new orders from checkout
class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True,read_only=True)

    class Meta:
        model = Order

        fields = [ 
            'id',
            'full_name',
            'phone',
            'shipping_address',
            'placed_at',
            'delivery_date',
            'notes',
            'total_amount',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        order = Order.objects.create(user=user, **validated_data)

        for item_data in items_data:
            order = Order.objects.create(user=user, **validated_data)

            # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order,**item_data)
        return order      


