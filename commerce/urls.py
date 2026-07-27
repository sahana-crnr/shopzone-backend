from django.urls import path
from .views import (
    AcceptDeliveryView,
    CartView,
    CartItemDetailView,
    CheckoutView,
    CouponListView,
    DeliveryOrdersListView,
    OrderDetailView,
    OrderListView,
    UpdateOrderStatusView,
    ValidateCouponView,
    WishlistView,
    WishlistItemDetailView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/<int:item_id>/", CartItemDetailView.as_view(), name="cart_item_detail"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/items/<int:item_id>/", WishlistItemDetailView.as_view(), name="wishlist_item_detail"),
    path("coupons/", CouponListView.as_view(), name="coupon_list"),
    path("coupons/validate/", ValidateCouponView.as_view(), name="validate_coupon"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/deliveries/", DeliveryOrdersListView.as_view(), name="delivery_orders_list"),
    path("orders/<int:order_id>/", OrderDetailView.as_view(), name="order_detail"),
    path("orders/<int:order_id>/accept_delivery/", AcceptDeliveryView.as_view(), name="accept_delivery"),
    path("orders/<int:order_id>/status/", UpdateOrderStatusView.as_view(), name="update_order_status"),
]