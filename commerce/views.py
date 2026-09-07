from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.html import escape
from decimal import Decimal
from hashlib import sha512
from io import BytesIO
import json
from uuid import uuid4
from urllib.parse import urlencode, quote_plus, urlsplit
from rest_framework_simplejwt.tokens import RefreshToken
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from catalog.models import Product
from .models import Cart, CartItem, Coupon, Order, OrderItem, Wishlist, WishlistItem
from .serializers import (
    CartSerializer,
    CouponSerializer,
    OrderSummarySerializer,
    WishlistItemSerializer,
)


def _payu_hash(values):
    """PayU's SHA-512 hash; the salt deliberately remains server-only."""
    raw = "|".join(str(value) for value in values)
    return sha512(raw.encode("utf-8")).hexdigest()


def _create_pending_order(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related("product")
    if not cart_items.exists():
        return None, Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

    shipping_address = request.data.get("shipping_address", "").strip() or "Standard Delivery Address"
    coupon_code = request.data.get("coupon_code", "").strip()
    coupon = Coupon.objects.filter(code__iexact=coupon_code, is_active=True).first() if coupon_code else None
    subtotal = cart.get_total_price()
    discount_percent = coupon.discount_percent if coupon else 0
    discount_amount = round((subtotal * discount_percent) / 100, 2)
    total_amount = max(Decimal("0"), subtotal - discount_amount)

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user, shipping_address=shipping_address, coupon=coupon,
            subtotal=subtotal, discount_amount=discount_amount, total_amount=total_amount,
            payment_transaction_id=f"SZ{uuid4().hex[:24].upper()}",
        )
        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product, product_name=item.product.name,
                product_image=item.product.image, unit_price=item.product.price, quantity=item.quantity,
            )
    return order, None


def _payu_payment_fields(request, order, frontend_url=None):
    if not settings.PAYU_KEY or not settings.PAYU_SALT:
        return None
    callback_url = request.build_absolute_uri("/api/payments/payu/callback/")
    frontend_target = frontend_url or settings.FRONTEND_URL
    return_param = f"&return_to={quote_plus(frontend_target)}" if frontend_target else ""
    fields = {
        "key": settings.PAYU_KEY,
        "txnid": order.payment_transaction_id,
        "amount": f"{order.total_amount:.2f}",
        "productinfo": f"Shopzone order #{order.id}",
        "firstname": order.user.name or "Customer",
        "email": order.user.email,
        "phone": order.user.phone or "",
        "surl": f"{callback_url}?result=success{return_param}",
        "furl": f"{callback_url}?result=failure{return_param}",
        "udf1": "", "udf2": "", "udf3": "", "udf4": "", "udf5": "",
    }
    fields["hash"] = _payu_hash([
        fields["key"], fields["txnid"], fields["amount"], fields["productinfo"],
        # PayU v1 requires udf1..udf5 followed by five reserved empty fields.
        fields["firstname"], fields["email"], "", "", "", "", "", *("" for _ in range(5)), settings.PAYU_SALT,
    ])
    return fields


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
        # Retain the old URL while ensuring it cannot bypass payment.
        return PayUInitiateView().post(request)


class PayUInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order, error = _create_pending_order(request)
        if error:
            return error

        # Determine frontend origin dynamically to prevent origin mismatch on callback
        raw_frontend = (
            request.data.get("frontend_url", "").strip()
            or request.headers.get("Origin", "").strip()
            or request.headers.get("Referer", "").strip()
            or settings.FRONTEND_URL
        ).rstrip("/")

        if raw_frontend and "://" in raw_frontend:
            split = urlsplit(raw_frontend)
            frontend_url = f"{split.scheme}://{split.netloc}"
        else:
            frontend_url = settings.FRONTEND_URL

        fields = _payu_payment_fields(request, order, frontend_url)
        if not fields:
            # Do not leave an unusable order around when credentials were omitted.
            order.delete()
            return Response(
                {"detail": "PayU test credentials are not configured. Set PAYU_KEY and PAYU_SALT in the backend .env."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({
            "order": OrderSummarySerializer(order).data,
            "payment_url": settings.PAYU_PAYMENT_URL,
            "payment_fields": fields,
        }, status=status.HTTP_201_CREATED)


class PayUCallbackView(APIView):
    """PayU posts here after checkout; trust only a callback with a valid reverse hash."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        txnid = request.data.get("txnid", "")
        order = Order.objects.filter(payment_transaction_id=txnid).select_related("user").first()
        successful = False
        if order and settings.PAYU_SALT:
            received_hash = request.data.get("hash", "")
            expected_hash = _payu_hash([
                # PayU's reverse hash contains udf5..udf1 plus five reserved empty fields.
                settings.PAYU_SALT, request.data.get("status", ""), *("" for _ in range(10)),
                request.data.get("email", ""), request.data.get("firstname", ""), request.data.get("productinfo", ""),
                request.data.get("amount", ""), txnid, request.data.get("key", ""),
            ])
            expected_amount = f"{order.total_amount:.2f}"
            valid = (
                constant_time_compare(received_hash, expected_hash)
                and request.data.get("key") == settings.PAYU_KEY
                and request.data.get("amount") == expected_amount
            )
            successful = valid and request.data.get("status") == "success"
            if valid:
                if successful:
                    order.payment_status = "SUCCESS"
                    order.status = "PROCESSING"
                    if not order.paid_at:
                        order.paid_at = timezone.now()
                        # Clear the current cart only after PayU confirms payment.
                        CartItem.objects.filter(cart__user=order.user, product_id__in=order.items.values("product_id")).delete()
                else:
                    order.payment_status = "FAILED"
                    order.status = "CANCELLED"
                order.payu_payment_id = request.data.get("mihpayid", "")
                order.save()

        return_to = request.query_params.get("return_to", "").strip() or settings.FRONTEND_URL
        result = "success" if successful else "failure"

        query_params = {
            "payment": result,
            "order": str(order.id) if order else "",
        }

        # Provide tokens for order.user to preserve the logged-in session even across origins
        if order and order.user:
            try:
                refresh = RefreshToken.for_user(order.user)
                query_params["token"] = str(refresh.access_token)
                query_params["refresh"] = str(refresh)
            except Exception:
                pass

        target = f"{return_to.rstrip('/')}/orders?{urlencode(query_params)}"
        html = (
            f'<!doctype html><html><head>'
            f'<meta http-equiv="refresh" content="0; url={escape(target)}">'
            f'<script>window.location.replace({json.dumps(target)});</script>'
            f'</head>'
            f'<body><p>Payment {result}. Redirecting to Shopzone...</p>'
            f'<p><a href="{escape(target)}">Click here if you are not automatically redirected</a>.</p></body></html>'
        )
        return HttpResponse(html)


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


def generate_invoice_pdf(order):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        "BrandHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        textColor=colors.HexColor("#4F46E5"),
        spaceAfter=2,
    )
    tagline_style = ParagraphStyle(
        "Tagline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
    )
    invoice_title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#0F172A"),
        alignment=2,
    )
    meta_right_style = ParagraphStyle(
        "MetaRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        alignment=2,
        leading=13,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#4F46E5"),
        spaceAfter=4,
    )
    body_text = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1E293B"),
        leading=13,
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
        alignment=1,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#1E293B"),
        leading=12,
    )
    table_cell_right = ParagraphStyle(
        "TableCellRight",
        parent=table_cell_style,
        alignment=2,
    )
    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell_style,
        alignment=1,
    )

    elements = []

    paid_date_str = order.paid_at.strftime("%d %b %Y, %I:%M %p") if order.paid_at else "N/A"
    header_data = [
        [
            Paragraph("<b>SHOPZONE</b>", brand_style),
            Paragraph("<b>TAX INVOICE</b>", invoice_title_style),
        ],
        [
            Paragraph("Your Premium Shopping Destination · www.shopzone.com", tagline_style),
            Paragraph(
                f"<b>Invoice #:</b> INV-{order.id:06d}<br/>"
                f"<b>Order Date:</b> {order.created_at.strftime('%d %b %Y')}<br/>"
                f"<b>Payment Date:</b> {paid_date_str}",
                meta_right_style,
            ),
        ],
    ]
    header_table = Table(header_data, colWidths=[100 * mm, 82 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=8))

    user_name = order.user.name or "Customer"
    user_email = order.user.email
    user_phone = order.user.phone or "N/A"
    clean_address = "<br/>".join(line.strip() for line in order.shipping_address.splitlines() if line.strip()) or "Standard Delivery"

    bill_to_content = (
        f"<b>Customer Name:</b> {user_name}<br/>"
        f"<b>Email:</b> {user_email}<br/>"
        f"<b>Phone:</b> {user_phone}<br/>"
        f"<b>Shipping Address:</b><br/>{clean_address}"
    )

    pay_status_color = "#059669" if order.payment_status == "SUCCESS" else "#DC2626"
    payment_content = (
        f"<b>Order ID:</b> #{order.id}<br/>"
        f"<b>Order Status:</b> {order.status}<br/>"
        f"<b>Payment Status:</b> <font color='{pay_status_color}'><b>{order.payment_status}</b></font><br/>"
        f"<b>Payment Gateway:</b> PayU Hosted Checkout<br/>"
        f"<b>Transaction Ref:</b> {order.payment_transaction_id or 'N/A'}<br/>"
        f"<b>PayU Payment ID:</b> {order.payu_payment_id or 'N/A'}"
    )

    info_data = [
        [
            Paragraph("<b>BILLED & SHIPPED TO</b>", section_heading),
            Paragraph("<b>ORDER & PAYMENT DETAILS</b>", section_heading),
        ],
        [
            Paragraph(bill_to_content, body_text),
            Paragraph(payment_content, body_text),
        ],
    ]
    info_table = Table(info_data, colWidths=[91 * mm, 91 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5 * mm))

    items_data = [
        [
            Paragraph("#", table_header_style),
            Paragraph("Item Description", table_header_style),
            Paragraph("Status", table_header_style),
            Paragraph("Unit Price", table_header_style),
            Paragraph("Qty", table_header_style),
            Paragraph("Total Amount", table_header_style),
        ]
    ]

    for idx, item in enumerate(order.items.all(), start=1):
        item_status_text = item.status.replace("_", " ").title()
        status_color = "#059669" if item.status == "ACTIVE" else "#DC2626" if item.status == "CANCELLED" else "#D97706"
        items_data.append([
            Paragraph(str(idx), table_cell_center),
            Paragraph(f"<b>{item.product_name}</b>", table_cell_style),
            Paragraph(f"<font color='{status_color}'><b>{item_status_text}</b></font>", table_cell_center),
            Paragraph(f"Rs. {item.unit_price:.2f}", table_cell_right),
            Paragraph(str(item.quantity), table_cell_center),
            Paragraph(f"Rs. {item.line_total():.2f}", table_cell_right),
        ])

    items_table = Table(
        items_data,
        colWidths=[10 * mm, 77 * mm, 25 * mm, 25 * mm, 15 * mm, 30 * mm],
    )
    items_table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for row_idx in range(1, len(items_data)):
        if row_idx % 2 == 0:
            items_table_style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#F8FAFC")))
    items_table.setStyle(TableStyle(items_table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))

    discount_label = f"Discount ({order.coupon.code}):" if order.coupon else "Discount:"
    summary_data = [
        [Paragraph("Subtotal:", table_cell_right), Paragraph(f"Rs. {order.subtotal:.2f}", table_cell_right)],
        [Paragraph(discount_label, table_cell_right), Paragraph(f"- Rs. {order.discount_amount:.2f}", table_cell_right)],
        [Paragraph("Shipping:", table_cell_right), Paragraph("<font color='#059669'><b>FREE</b></font>", table_cell_right)],
        [Paragraph("<b>TOTAL PAID:</b>", table_cell_right), Paragraph(f"<b>Rs. {order.total_amount:.2f}</b>", table_cell_right)],
    ]
    summary_table = Table(summary_data, colWidths=[142 * mm, 40 * mm])
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEABOVE", (0, 3), (-1, 3), 1, colors.HexColor("#4F46E5")),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#EEF2FF")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
    footer_text = Paragraph(
        "<font color='#64748B' size='8'>Thank you for shopping with <b>Shopzone</b>! "
        "For any queries regarding this order, please contact support@shopzone.com.<br/>"
        "This is a computer-generated tax invoice and requires no physical signature.</font>",
        ParagraphStyle("Footer", parent=styles["Normal"], alignment=1, leading=11),
    )
    elements.append(footer_text)

    doc.build(elements)
    return buffer.getvalue()


class InvoiceView(APIView):
    """Download a paid order's invoice as a PDF.  Unpaid orders have no invoice."""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(
            Order.objects.prefetch_related("items"), id=order_id, user=request.user
        )
        if order.payment_status != "SUCCESS":
            return Response({"detail": "The invoice is available after successful payment."}, status=status.HTTP_409_CONFLICT)

        pdf_bytes = generate_invoice_pdf(order)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="shopzone-invoice-{order.id}.pdf"'
        return response


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
        valid_statuses = [
            "PENDING",
            "PROCESSING",
            "SHIPPED",
            "DELIVERED",
            "CANCELLED",
            "RETURN_REQUESTED",
            "RETURNED",
        ]

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


class CancelOrderView(APIView):
    """
    Cancel an entire order before it has shipped (status in PENDING, PROCESSING).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to cancel this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status not in ["PENDING", "PROCESSING"]:
            return Response(
                {"detail": f"Cannot cancel an order with status '{order.status}'. Orders can only be cancelled before they are shipped."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip() or "Cancelled by customer"
        order.status = "CANCELLED"
        order.cancellation_reason = reason
        order.save()

        order.items.filter(status="ACTIVE").update(status="CANCELLED", cancellation_reason=reason)

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelOrderItemView(APIView):
    """
    Cancel a specific item in an order before it has shipped.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id, item_id):
        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to modify this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status not in ["PENDING", "PROCESSING"]:
            return Response(
                {"detail": f"Cannot cancel items in an order with status '{order.status}'. Items can only be cancelled before the order is shipped."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(OrderItem, id=item_id, order=order)
        if item.status == "CANCELLED":
            return Response(
                {"detail": "This item is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip() or "Item cancelled by customer"
        item.status = "CANCELLED"
        item.cancellation_reason = reason
        item.save()

        # If all items are now cancelled, mark the entire order cancelled
        active_items_count = order.items.exclude(status="CANCELLED").count()
        if active_items_count == 0:
            order.status = "CANCELLED"
            order.cancellation_reason = "All ordered items were cancelled"
            order.save()

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReturnOrderView(APIView):
    """
    Request a return for an order after it has been delivered.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to return this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status != "DELIVERED":
            return Response(
                {"detail": "Returns can only be requested for delivered orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip() or "Return requested by customer"
        order.status = "RETURN_REQUESTED"
        order.return_reason = reason
        order.save()

        order.items.filter(status="ACTIVE").update(status="RETURN_REQUESTED", return_reason=reason)

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReturnOrderItemView(APIView):
    """
    Request a return for a specific item after delivery.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id, item_id):
        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to return this item."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status != "DELIVERED":
            return Response(
                {"detail": "Returns can only be requested for delivered orders."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(OrderItem, id=item_id, order=order)
        if item.status in ["RETURN_REQUESTED", "RETURNED"]:
            return Response(
                {"detail": f"Item return has already been requested ({item.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip() or "Return requested by customer"
        item.status = "RETURN_REQUESTED"
        item.return_reason = reason
        item.save()

        if order.status != "RETURN_REQUESTED":
            order.status = "RETURN_REQUESTED"
            order.return_reason = "Return requested for one or more items"
            order.save()

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AcceptReturnView(APIView):
    """
    Endpoint for Delivery Staff or Admin to process and accept a returned order.
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
                {"detail": "Only delivery staff or admins can accept returns."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = get_object_or_404(Order, id=order_id)
        order.status = "RETURNED"
        order.save()
        order.items.filter(status="RETURN_REQUESTED").update(status="RETURNED")

        serializer = OrderSummarySerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
