from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product

from .models import Cart, CartItem, Coupon, Order, OrderItem, WishlistItem
from .serializers import (
    CheckoutSerializer,
    CouponCodeSerializer,
    CouponSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartItemUpsertSerializer,
    CartSerializer,
    OrderSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer,
)


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _get_coupon_or_404(code):
    normalized_code = code.strip()
    try:
        return Coupon.objects.get(code__iexact=normalized_code, is_active=True)
    except Coupon.DoesNotExist as exc:
        raise ValidationError({"coupon_code": "Invalid or inactive coupon."}) from exc


def _calculate_order_totals(cart_items, coupon=None):
    subtotal = sum(item.quantity * item.product.price for item in cart_items)
    discount_amount = 0

    if coupon is not None:
        if coupon.min_order_amount and subtotal < coupon.min_order_amount:
            raise ValidationError(
                {
                    "coupon_code": (
                        f"{coupon.code} requires a minimum order amount of "
                        f"₹{coupon.min_order_amount}."
                    )
                }
            )
        discount_amount = (subtotal * coupon.discount_percent) // 100

    total_amount = max(subtotal - discount_amount, 0)
    return subtotal, discount_amount, total_amount


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


class CouponListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        coupons = Coupon.objects.filter(is_active=True).order_by("code")
        return Response(CouponSerializer(coupons, many=True).data)


class CouponValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = _get_coupon_or_404(serializer.validated_data["code"])
        return Response(CouponSerializer(coupon).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = _get_or_create_cart(request.user)
        cart_items = list(cart.items.select_related("product"))

        if not cart_items:
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        coupon = None
        coupon_code = serializer.validated_data.get("coupon_code")
        if coupon_code:
            coupon = _get_coupon_or_404(coupon_code)

        subtotal, discount_amount, total_amount = _calculate_order_totals(
            cart_items,
            coupon,
        )

        order = Order.objects.create(
            user=request.user,
            coupon=coupon,
            shipping_address=serializer.validated_data["shipping_address"],
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
        )

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_image=item.product.image,
                unit_price=item.product.price,
                quantity=item.quantity,
                line_total=item.quantity * item.product.price,
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()

        order = (
            Order.objects.select_related("coupon")
            .prefetch_related("items__product")
            .get(pk=order.pk)
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("coupon")
            .prefetch_related("items__product")
            .order_by("-id")
        )
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(
            Order.objects.select_related("coupon").prefetch_related("items__product"),
            pk=pk,
            user=request.user,
        )
        return Response(OrderSerializer(order).data)
