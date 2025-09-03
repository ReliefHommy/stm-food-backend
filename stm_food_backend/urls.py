from django.contrib import admin
from django.urls import path,include
from .views import MyProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),
    # main API entrypoint
    path('api/', include('thefood.urls')),
    # Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # user profile
    #path('api/my-profile/', MyProfileView.as_view(), name='my-profile'),
    path('api/me/', MyProfileView.as_view(), name='my-profile'),
    
    
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

