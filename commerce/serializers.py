from rest_framework import serializers
from catalog.serializers import ProductSerializer
from .models import Cart, CartItem, Coupon, Order, OrderItem, WishlistItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "subtotal"]

    def get_subtotal(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    totalItems = serializers.SerializerMethodField()
    totalPrice = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "totalItems", "totalPrice"]

    def get_totalItems(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_totalPrice(self, obj):
        return obj.get_total_price()


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class CouponSerializer(serializers.ModelSerializer):
    discountPercent = serializers.IntegerField(source="discount_percent")
    minOrderAmount = serializers.DecimalField(source="min_order_amount", max_digits=10, decimal_places=2)
    isActive = serializers.BooleanField(source="is_active")

    class Meta:
        model = Coupon
        fields = ["id", "code", "discountPercent", "minOrderAmount", "isActive"]


class OrderItemSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source="product_id")
    productName = serializers.CharField(source="product_name")
    productImage = serializers.CharField(source="product_image")
    unitPrice = serializers.DecimalField(source="unit_price", max_digits=10, decimal_places=2)
    lineTotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "productId", "productName", "productImage", "unitPrice", "quantity", "lineTotal"]

    def get_lineTotal(self, obj):
        return obj.line_total()


class OrderSummarySerializer(serializers.ModelSerializer):
    shippingAddress = serializers.CharField(source="shipping_address")
    discountAmount = serializers.DecimalField(source="discount_amount", max_digits=10, decimal_places=2)
    totalAmount = serializers.DecimalField(source="total_amount", max_digits=10, decimal_places=2)
    coupon = CouponSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    customerName = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customerName",
            "customerPhone",
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

    def get_customerName(self, obj):
        return obj.user.name if obj.user else "Customer"

    def get_customerPhone(self, obj):
        return obj.user.phone if obj.user else ""