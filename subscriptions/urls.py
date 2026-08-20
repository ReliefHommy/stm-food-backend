from django.urls import path

from .views import StripeWebhookView, SubscriptionStartView

urlpatterns = [
    path('start/', SubscriptionStartView.as_view(), name='subscription-start'),
    path('webhook/', StripeWebhookView.as_view(), name='subscription-webhook'),
]
