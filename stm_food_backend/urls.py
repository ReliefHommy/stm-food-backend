from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

from .views import MyProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView





urlpatterns = [

    path('admin/', admin.site.urls),
  

    # Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/me/', MyProfileView.as_view(), name='my-profile'),

     # ✅ Admin metrics endpoints (NEW)
    path("api/admin/", include("stm_food_backend.admin_urls")),

    # App Apis
    path('api/food/', include("thefood.urls")),
    path("api/studio/", include("studio.urls")),  
    
    
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

