from django.urls import path

from .views import (
    CartItemDetailView,
    CartView,
    CheckoutView,
    CouponListView,
    CouponValidateView,
    OrderDetailView,
    OrderListView,
    WishlistItemDetailView,
    WishlistView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/<int:pk>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("coupons/", CouponListView.as_view(), name="coupon-list"),
    path("coupons/validate/", CouponValidateView.as_view(), name="coupon-validate"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="orders"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path(
        "wishlist/items/<int:pk>/",
        WishlistItemDetailView.as_view(),
        name="wishlist-item-detail",
    ),
]
