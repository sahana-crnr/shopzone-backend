from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, BannerViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'banners', BannerViewSet, basename='banner')

urlpatterns = [
    path('', include(router.urls)),
]