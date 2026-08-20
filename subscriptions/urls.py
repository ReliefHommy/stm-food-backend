from django.urls import path

from .views import (
    StripeWebhookView,
    SubscriptionCancelView,
    SubscriptionItemsView,
    SubscriptionMyView,
    SubscriptionPauseView,
    SubscriptionResumeView,
    SubscriptionStartView,
)

urlpatterns = [
    path('start/', SubscriptionStartView.as_view(), name='subscription-start'),
    path('webhook/', StripeWebhookView.as_view(), name='subscription-webhook'),
    path('my/', SubscriptionMyView.as_view(), name='subscription-my'),
    path('my/items/', SubscriptionItemsView.as_view(), name='subscription-my-items'),
    path('my/pause/', SubscriptionPauseView.as_view(), name='subscription-my-pause'),
    path('my/resume/', SubscriptionResumeView.as_view(), name='subscription-my-resume'),
    path('my/cancel/', SubscriptionCancelView.as_view(), name='subscription-my-cancel'),
]
