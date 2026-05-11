from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.serializers import ProductSerializer

from .models import Cart, CartItem, Coupon, Order, OrderItem, WishlistItem


User = get_user_model()


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "subtotal"]
        read_only_fields = fields

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    totalItems = serializers.SerializerMethodField()
    totalPrice = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "totalItems", "totalPrice"]
        read_only_fields = fields

    def get_totalItems(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_totalPrice(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())


class CartItemUpsertSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(required=False, min_value=1, default=1)

    def validate_product_id(self, value):
        from catalog.models import Product

        try:
            return Product.objects.get(pk=value).pk
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError("Product not found.") from exc


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]
        read_only_fields = fields


class WishlistItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        from catalog.models import Product

        try:
            return Product.objects.get(pk=value).pk
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError("Product not found.") from exc


class CouponSerializer(serializers.ModelSerializer):
    discountPercent = serializers.IntegerField(source="discount_percent", read_only=True)
    minOrderAmount = serializers.IntegerField(source="min_order_amount", read_only=True)
    isActive = serializers.BooleanField(source="is_active", read_only=True)

    class Meta:
        model = Coupon
        fields = ["id", "code", "discountPercent", "minOrderAmount", "isActive"]
        read_only_fields = fields


class CouponCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500, trim_whitespace=True)
    coupon_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=32,
    )


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    productName = serializers.CharField(source="product_name", read_only=True)
    productImage = serializers.CharField(source="product_image", read_only=True)
    unitPrice = serializers.IntegerField(source="unit_price", read_only=True)
    lineTotal = serializers.IntegerField(source="line_total", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "productName",
            "productImage",
            "unitPrice",
            "quantity",
            "lineTotal",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    shippingAddress = serializers.CharField(source="shipping_address", read_only=True)
    discountAmount = serializers.IntegerField(source="discount_amount", read_only=True)
    totalAmount = serializers.IntegerField(source="total_amount", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "shippingAddress",
            "status",
            "coupon",
            "subtotal",
            "discountAmount",
            "totalAmount",
            "items",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields
