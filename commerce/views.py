from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from catalog.models import Product
from .models import Cart, CartItem, Coupon, Order, OrderItem, Wishlist, WishlistItem
from .serializers import (
    CartSerializer,
    CouponSerializer,
    OrderSummarySerializer,
    WishlistItemSerializer,
)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"detail": "product_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, id=item_id).first()
        if not cart_item:
            cart_item = CartItem.objects.filter(cart=cart, product_id=item_id).first()

        if not cart_item:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        quantity = int(request.data.get("quantity", 1))
        if quantity <= 0:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        cart_item.quantity = quantity
        cart_item.save()
        return Response({"id": cart_item.id, "quantity": cart_item.quantity})

    def delete(self, request, item_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(cart=cart, id=item_id).first()
        if not cart_item:
            cart_item = CartItem.objects.filter(cart=cart, product_id=item_id).first()

        if cart_item:
            cart_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        items = wishlist.items.all().select_related("product")
        serializer = WishlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"detail": "product_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, id=product_id)
        item, _ = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product,
        )

        serializer = WishlistItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        item = WishlistItem.objects.filter(wishlist=wishlist, id=item_id).first()
        if not item:
            item = WishlistItem.objects.filter(wishlist=wishlist, product_id=item_id).first()

        if item:
            item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CouponListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        coupons = Coupon.objects.filter(is_active=True)
        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)


class ValidateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        if not code:
            return Response(
                {"detail": "Coupon code is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
        if not coupon:
            return Response(
                {"detail": "Invalid or inactive discount code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CouponSerializer(coupon)
        return Response(serializer.data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all().select_related("product")

        if not cart_items.exists():
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shipping_address = request.data.get("shipping_address", "").strip()
        if not shipping_address:
            shipping_address = "Standard Delivery Address"

        coupon_code = request.data.get("coupon_code", "").strip()
        coupon = None
        discount_percent = 0

        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first()
            if coupon:
                discount_percent = coupon.discount_percent

        subtotal = cart.get_total_price()
        discount_amount = round((subtotal * discount_percent) / 100, 2)
        total_amount = max(0, subtotal - discount_amount)

        order = Order.objects.create(
            user=request.user,
            status="PENDING",
            shipping_address=shipping_address,
            coupon=coupon,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_image=item.product.image,
                unit_price=item.product.price,
                quantity=item.quantity,
            )

        # Clear cart items after successful checkout
        cart_items.delete()

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSummarySerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderSummarySerializer(order)
        return Response(serializer.data)


class DeliveryOrdersListView(APIView):
    """
    Endpoint for Delivery Staff and Staff Admins to view all checkout orders.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = [r.role_name for r in request.user.roles.all()]
        is_staff_or_delivery = (
            request.user.is_staff
            or any(r in user_roles for r in ["delivery_staff", "admin", "owner", "shop_manager", "inventory_manager"])
        )
        if not is_staff_or_delivery:
            return Response(
                {"detail": "Only delivery staff and system admins can access delivery orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = Order.objects.all().order_by("-created_at")
        serializer = OrderSummarySerializer(orders, many=True)
        return Response(serializer.data)


class AcceptDeliveryView(APIView):
    """
    Endpoint for Delivery Staff to accept a checkout order.
    Changes status from PENDING to PROCESSING or SHIPPED.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user_roles = [r.role_name for r in request.user.roles.all()]
        is_staff_or_delivery = (
            request.user.is_staff
            or any(r in user_roles for r in ["delivery_staff", "admin", "owner", "shop_manager"])
        )
        if not is_staff_or_delivery:
            return Response(
                {"detail": "Only delivery staff can accept deliveries."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = get_object_or_404(Order, id=order_id)
        order.status = "SHIPPED"
        order.save()

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateOrderStatusView(APIView):
    """
    Endpoint to update order delivery status (e.g. SHIPPED -> DELIVERED).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user_roles = [r.role_name for r in request.user.roles.all()]
        is_staff_or_delivery = (
            request.user.is_staff
            or any(r in user_roles for r in ["delivery_staff", "admin", "owner", "shop_manager"])
        )
        if not is_staff_or_delivery:
            return Response(
                {"detail": "Only delivery staff can update order status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status", "").upper()
        valid_statuses = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]

        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)