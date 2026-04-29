from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product

from .models import Cart, CartItem, WishlistItem
from .serializers import (
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartItemUpsertSerializer,
    CartSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer,
)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data)

    @transaction.atomic
    def post(self, request):
        serializer = CartItemUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.get(pk=serializer.validated_data["product_id"])
        quantity = serializer.validated_data.get("quantity", 1)
        cart = _get_or_create_cart(request.user)

        item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            CartItem.objects.filter(pk=item.pk).update(quantity=F("quantity") + quantity)
            item.refresh_from_db()

        payload = CartSerializer(cart).data
        return Response(
            payload,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity", "updated_at"])
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("product")
        return Response(WishlistItemSerializer(items, many=True).data)

    def post(self, request):
        serializer = WishlistItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = Product.objects.get(pk=serializer.validated_data["product_id"])

        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product,
        )
        return Response(
            WishlistItemSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WishlistItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(WishlistItem, pk=pk, user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

