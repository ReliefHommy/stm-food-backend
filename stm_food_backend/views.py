from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from thefood.models import UserProfile

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        name = (request.data.get('name') or '').strip()

        if not email or not password or not name:
            return Response(
                {'detail': 'email, password, and name are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {'detail': 'An account with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(password)
        except DjangoValidationError as exc:
            return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        first_name, _, last_name = name.partition(' ')

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_customer=True,
        )

        return Response(
            {'id': user.id, 'email': user.email},
            status=status.HTTP_201_CREATED,
        )


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