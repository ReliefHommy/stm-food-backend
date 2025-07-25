#from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets
from .models import Product, Recipe
from .serializers import ProductSerializer, RecipeSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    #permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        #if user.is_superuser:
        if user.is_authenticated and user.is_partner:
            #return Product.objects.all()
        #if hasattr(user, "partnerstore"):
            return Product.objects.filter(partner_store__user=user)
        return Product.objects.all()



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    #permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            ##return Recipe.objects.all()
        ##if hasattr(user, "partnerstore"):
            return Recipe.objects.filter(author=user)
        return Recipe.objects.none()

