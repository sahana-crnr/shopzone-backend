from django.db import IntegrityError, transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product

from .models import Cart, CartItem, Coupon, Order, OrderItem, WishlistItem
from .serializers import (
    CartItemUpdateSerializer,
    CartItemUpsertSerializer,
    CartSerializer,
    CheckoutSerializer,
    CouponCodeSerializer,
    CouponSerializer,
    OrderSerializer,
    WishlistItemCreateSerializer,
    WishlistItemSerializer,
)


def _cart_for_user(user):
    return Cart.objects.get_or_create(user=user)[0]


def _cart_queryset():
    return Cart.objects.prefetch_related("items__product__tags")


def _order_queryset():
    return Order.objects.select_related("coupon").prefetch_related("items__product__tags")


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _cart_queryset().filter(user=request.user).first() or _cart_for_user(
            request.user
        )
        return Response(CartSerializer(cart).data)

    def post(self, request):
        serializer = CartItemUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.get(pk=serializer.validated_data["product_id"])
        quantity = serializer.validated_data["quantity"]
        cart = _cart_for_user(request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity", "updated_at"])

        cart = _cart_queryset().get(pk=cart.pk)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemUpdateSerializer
    http_method_names = ["patch", "delete", "options"]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def patch(self, request, *args, **kwargs):
        cart_item = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item.quantity = serializer.validated_data["quantity"]
        cart_item.save(update_fields=["quantity", "updated_at"])
        return Response({"id": cart_item.id, "quantity": cart_item.quantity})


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related(
            "product"
        ).prefetch_related("product__tags")
        return Response(WishlistItemSerializer(items, many=True).data)

    def post(self, request):
        serializer = WishlistItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.get(pk=serializer.validated_data["product_id"])
        try:
            item, _created = WishlistItem.objects.get_or_create(
                user=request.user,
                product=product,
            )
        except IntegrityError:
            item = WishlistItem.objects.get(user=request.user, product=product)

        item = (
            WishlistItem.objects.select_related("product")
            .prefetch_related("product__tags")
            .get(pk=item.pk)
        )
        return Response(
            WishlistItemSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )


class WishlistItemDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)


class CouponListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CouponSerializer

    def get_queryset(self):
        return Coupon.objects.filter(is_active=True)


class CouponValidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip().upper()

        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Invalid discount code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(CouponSerializer(coupon).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = (
            Cart.objects.select_for_update()
            .filter(user=request.user)
            .prefetch_related("items__product")
            .first()
        )
        if not cart or not cart.items.exists():
            return Response(
                {"detail": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = list(cart.items.select_related("product"))
        subtotal = sum(item.quantity * item.product.price for item in items)

        coupon = None
        coupon_code = serializer.validated_data.get("coupon_code")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    code__iexact=coupon_code.strip(),
                    is_active=True,
                )
            except Coupon.DoesNotExist:
                return Response(
                    {"detail": "Invalid discount code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if subtotal < coupon.min_order_amount:
                return Response(
                    {
                        "detail": (
                            "This coupon requires a minimum order of "
                            f"{coupon.min_order_amount}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        discount_amount = 0
        if coupon:
            discount_amount = round(subtotal * coupon.discount_percent / 100)

        order = Order.objects.create(
            user=request.user,
            coupon=coupon,
            shipping_address=serializer.validated_data["shipping_address"],
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=subtotal - discount_amount,
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
            for item in items
        ]
        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()

        order = _order_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return _order_queryset().filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return _order_queryset().filter(user=self.request.user)
