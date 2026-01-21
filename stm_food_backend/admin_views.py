from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from thefood.models import UserProfile

User = get_user_model()

class AdminUserMetricsView(APIView):
    """
    Admin-only dashboard metrics (counts).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Base user count
        total_users = User.objects.count()

        # Your boolean flags (from your /api/me/ response)
        partners = User.objects.filter(is_partner=True).count()
        customers = User.objects.filter(is_customer=True).count()

        # "Creators" - you didn't show a flag yet; keep 0 for now OR adapt later
        creators = User.objects.filter(is_creator=True).count() if hasattr(User, "is_creator") else 0

        # "Admin users" -> usually staff
        admin_users = User.objects.filter(is_staff=True).count()

        # Profiles count (optional)
        profiles = UserProfile.objects.count()

        return Response({
            "admin_users": admin_users,
            "creators": creators,
            "partners": partners,
            "customers": customers,
            "total_users": total_users,
            "profiles": profiles,
        })
    
class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.order_by("-date_joined")[:50]

        data = []
        for u in users:
            data.append({
                "id": u.id,
                "email": getattr(u, "email", ""),
                "is_staff": getattr(u, "is_staff", False),
                "is_partner": getattr(u, "is_partner", False),
                "is_customer": getattr(u, "is_customer", False),
                "date_joined": getattr(u, "date_joined", None),

            })
        return Response({"results": data})
