from django.contrib import admin

from .models import Cart, CartItem, WishlistItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "updated_at")
    search_fields = ("user__email", "user__name")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "updated_at")
    search_fields = ("cart__user__email", "product__name")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "created_at")
    search_fields = ("user__email", "product__name")

