from django.contrib import admin
from .models import Cart, CartItem, Coupon, Order, OrderItem, Wishlist, WishlistItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user")
    search_fields = ("user__email", "user__name")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity")
    search_fields = ("cart__user__email", "product__name")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "wishlist", "product")
    search_fields = ("wishlist__user__email", "product__name")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "discount_percent", "min_order_amount", "is_active")
    search_fields = ("code",)
    list_filter = ("is_active",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "product_image",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "subtotal", "discount_amount", "total_amount", "created_at")
    search_fields = ("user__email", "user__name", "shipping_address")
    list_filter = ("status", "created_at")
    inlines = [OrderItemInline]
    actions = ["mark_as_processing", "mark_as_shipped", "mark_as_delivered"]

    def mark_as_processing(self, request, queryset):
        queryset.update(status="PROCESSING")
        self.message_user(request, "Selected orders marked as Processing.")
    mark_as_processing.short_description = "Accept Delivery (Mark as Processing)"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status="SHIPPED")
        self.message_user(request, "Selected orders marked as Shipped.")
    mark_as_shipped.short_description = "Mark as Out for Delivery (Shipped)"

    def mark_as_delivered(self, request, queryset):
        queryset.update(status="DELIVERED")
        self.message_user(request, "Selected orders marked as Delivered.")
    mark_as_delivered.short_description = "Mark as Delivered"
