from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from thefood.models import PartnerStore, Product


class StripeCustomer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stripe_customer'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.email} -> {self.stripe_customer_id}"


class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
    ]
    STATUS_CHOICES = [
        ('incomplete', 'Incomplete'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('paused', 'Paused'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions'
    )
    partner_store = models.ForeignKey(
        PartnerStore, on_delete=models.CASCADE, related_name='subscriptions'
    )

    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_box_item_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_shipping_item_id = models.CharField(max_length=255, null=True, blank=True)

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')

    # Delivery snapshot — independent of billing, editable without touching Stripe.
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    current_period_end = models.DateTimeField(null=True, blank=True)
    next_delivery_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Subscription {self.id} ({self.user.email})"


class SubscriptionItem(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='subscription_items')
    quantity = models.PositiveIntegerField(default=1)

    def clean(self):
        if self.product_id and self.subscription_id:
            if self.product.partner_store_id != self.subscription.partner_store_id:
                raise ValidationError(
                    {'product': "Product's partner store must match the subscription's partner store."}
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} x {self.quantity} (Subscription {self.subscription_id})"


class StripeWebhookEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255)
    payload = models.JSONField()
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} ({self.stripe_event_id})"
