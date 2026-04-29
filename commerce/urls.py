from django.urls import path

from .views import CartItemDetailView, CartView, WishlistItemDetailView, WishlistView

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/<int:pk>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path(
        "wishlist/items/<int:pk>/",
        WishlistItemDetailView.as_view(),
        name="wishlist-item-detail",
    ),
]

