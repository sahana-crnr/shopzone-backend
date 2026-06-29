from django.urls import path

from .views import ProductDetailView, ProductListView, ProductReviewListCreateView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path(
        "products/<int:pk>/reviews/",
        ProductReviewListCreateView.as_view(),
        name="product-reviews",
    ),
]
