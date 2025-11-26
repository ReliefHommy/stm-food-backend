from django.db import models
from datetime import date
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser,UserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        username = extra_fields.pop("username", email)

        return super().create_user(username=username, email=email, password=password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # same trick here: use email as username internally
        username = extra_fields.pop("username", email)


        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

# Extend Django's built-in user model
class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)

    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()   # <— ADD THIS  # removes username from required fields

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    is_vendor = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(max_length=500, null=True, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} Profile"



class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name


class PartnerStore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='partner_store')
    store_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.URLField(max_length=500, null=True, blank=True)
    contact_email = models.EmailField()
    website = models.URLField(blank=True)

    def __str__(self):
        return self.store_name


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True)
    image = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)  # 👈 Add this line
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    image = models.URLField(max_length=500, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    partner_store = models.ForeignKey(PartnerStore, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            cand = base
            i = 1
            while Product.objects.filter(slug=cand).exists():
                i += 1
                cand = f'{base}-{i}'
            self.slug = cand
        super().save(*args, **kwargs)



    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    placed_at = models.DateTimeField(auto_now_add=True)
# add more models for order items
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'Order {self.id} by {self.user.email}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name='items')
    product = models.ForeignKey('thefood.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


class Recipe(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.URLField(max_length=500, null=True, blank=True)
    ingredients = models.TextField()
    instructions = models.TextField()
    author = models.ForeignKey(PartnerStore, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, related_name='recipes')  # link to products


    def __str__(self):
        return self.title
    

class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey(PartnerStore, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    featured_image = models.URLField(max_length=500, null=True, blank=True)
    related_recipe = models.ForeignKey(Recipe, null=True, blank=True, on_delete=models.SET_NULL)
    related_products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.title


class NewsletterSignup(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
