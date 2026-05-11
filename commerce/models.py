from django.conf import settings
from django.db import models

from catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="unique_cart_product")
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.product} x {self.quantity}"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product")
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user} -> {self.product}"


class Coupon(models.Model):
    code = models.CharField(max_length=32, unique=True)
    discount_percent = models.PositiveSmallIntegerField()
    min_order_amount = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    shipping_address = models.TextField(default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLACED,
    )
    subtotal = models.PositiveIntegerField()
    discount_amount = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Order #{self.pk} for {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=255)
    product_image = models.CharField(max_length=500, blank=True)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_order_product")
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
