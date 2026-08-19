from django.urls import path

from .views import SubscriptionStartView

urlpatterns = [
    path('start/', SubscriptionStartView.as_view(), name='subscription-start'),
]
