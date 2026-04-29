from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalog.serializers import ProductSerializer

from .models import Cart, CartItem, WishlistItem


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

