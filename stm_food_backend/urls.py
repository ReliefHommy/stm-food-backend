
from django.contrib import admin
from django.urls import path,include
#from thefood.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('thefood.urls')),
    
]

