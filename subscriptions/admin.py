from django.contrib import admin

from .models import StripeCustomer, Subscription, SubscriptionItem, StripeWebhookEvent


class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stripe_customer_id')
    search_fields = ('user__email', 'stripe_customer_id')


class SubscriptionItemInline(admin.TabularInline):
    model = SubscriptionItem
    extra = 0


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'partner_store', 'frequency', 'status',
        'next_delivery_date', 'current_period_end',
    )
    list_filter = ('status', 'frequency', 'partner_store')
    search_fields = ('user__email', 'full_name', 'stripe_subscription_id')
    inlines = [SubscriptionItemInline]


class SubscriptionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscription', 'product', 'quantity')
    search_fields = ('subscription__user__email', 'product__title')


class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'stripe_event_id', 'processed_at', 'created_at')
    list_filter = ('type',)
    search_fields = ('stripe_event_id', 'type')
    readonly_fields = ('created_at',)


admin.site.register(StripeCustomer, StripeCustomerAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(SubscriptionItem, SubscriptionItemAdmin)
admin.site.register(StripeWebhookEvent, StripeWebhookEventAdmin)
