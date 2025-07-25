from urllib import request
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Register your models here.
from .models import (
    User, Customer, PartnerStore, Category, Brand, Product,Cart, CartItem, Order,OrderItem,Recipe,NewsletterSignup
)
# Extend Django's UserAdmin to show custom fields

# Custom User Admin
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_customer', 'is_partner')}),
    )
    list_display = ('username', 'email', 'is_customer', 'is_partner', 'is_staff')
    list_filter = ('is_customer', 'is_partner', 'is_staff')
# Inline Order Items
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'placed_at')
    list_filter = ('status', 'placed_at')
    search_fields = ('user__username', 'user__email')
    inlines = [OrderItemInline]

# Inline Cart Items
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username', 'user__email')
    inlines = [CartItemInline]
#ProductAdmin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_available', 'stock_quantity', 'brand', 'category')
    list_filter = ('brand', 'category', 'is_available')
    search_fields = ('title', 'description')

   

  
# RecipeAsmin
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'ingredients', 'instructions')
  
# partners see only selected models in the sidebar
class PartnerStoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'contact_email')
    search_fields = ('store_name', 'user__username')
 

    
        
        
#Hide ciustomerAdmin from partner
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'country')
    search_fields = ('full_name', 'user__username')


# Custom Administation site
    
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

class CustomAdminSite(admin.AdminSite):
    site_title = "STM Food Admin"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def each_context(self, request):
        context = super().each_context(request)
        if request.user.is_authenticated:
            username = request.user.username
            try:
                store = request.user.partnerstore
                context['site_header'] = f"{username} / {store.store_name}"
            except:
                context['site_header'] = f"{username} / STM Food Admin"
        return context

# Apply it globally
admin.site = CustomAdminSite(name='custom_admin')


  





admin.site.register(User, UserAdmin)
admin.site.register(Customer)
admin.site.register(PartnerStore)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Recipe)
admin.site.register(NewsletterSignup)




