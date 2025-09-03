from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from thefood.models import UserProfile

# core/views.py
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        profile, _ = UserProfile.objects.get_or_create(user=user)  
        return Response({
            "id": user.id,
            "email": user.email,
            "is_partner": user.is_partner,
            "is_customer": user.is_customer,
            "phone": profile.phone,
            "address": profile.address,
            "avatar": request.build_absolute_uri(profile.avatar.url) if profile.avatar else None,
         
        })