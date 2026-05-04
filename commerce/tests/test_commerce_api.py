from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import Product
from commerce.models import Cart
from commerce.models import CartItem, Coupon, Order, WishlistItem


User = get_user_model()


class CommerceApiTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            name="User A",
            email="a@example.com",
            password="password123",
        )
        self.user_b = User.objects.create_user(
            name="User B",
            email="b@example.com",
            password="password123",
        )
        self.product_1 = Product.objects.create(
            name="Alpha Shoes",
            price=1000,
            rating=4.1,
            ratings_count=100,
            reviews_count=10,
        )
        self.product_2 = Product.objects.create(
            name="Beta Headphones",
            price=2000,
            rating=4.8,
            ratings_count=200,
            reviews_count=40,
        )
        self.cart_url = reverse("cart")
        self.wishlist_url = reverse("wishlist")
        self.coupons_url = reverse("coupon-list")
        self.coupon_validate_url = reverse("coupon-validate")
        self.checkout_url = reverse("checkout")
        self.orders_url = reverse("orders")

    def authenticate(self, user):
        access = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_cart_requires_authentication(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wishlist_requires_authentication(self):
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_coupon_list_requires_authentication(self):
        response = self.client.get(self.coupons_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkout_requires_authentication(self):
        response = self.client.post(self.checkout_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cart_is_scoped_to_authenticated_user(self):
        self.authenticate(self.user_a)
        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])

    def test_user_a_cannot_touch_user_b_cart_items(self):
        cart_b = Cart.objects.create(user=self.user_b)
        item = CartItem.objects.create(cart=cart_b, product=self.product_1, quantity=2)

        self.authenticate(self.user_a)
        response = self.client.patch(
            reverse("cart-item-detail", kwargs={"pk": item.pk}),
            {"quantity": 5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_touch_user_b_wishlist_items(self):
        item = WishlistItem.objects.create(user=self.user_b, product=self.product_1)

        self.authenticate(self.user_a)
        response = self.client.delete(reverse("wishlist-item-detail", kwargs={"pk": item.pk}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cart_add_update_and_delete_item(self):
        self.authenticate(self.user_a)

        add_response = self.client.post(
            self.cart_url,
            {"product_id": self.product_1.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_response.data["totalItems"], 2)

        cart_item = CartItem.objects.get(cart=self.user_a.cart, product=self.product_1)
        patch_response = self.client.patch(
            reverse("cart-item-detail", kwargs={"pk": cart_item.pk}),
            {"quantity": 5},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

        delete_response = self.client.delete(
            reverse("cart-item-detail", kwargs={"pk": cart_item.pk})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(pk=cart_item.pk).exists())

    def test_wishlist_add_list_and_delete_item(self):
        self.authenticate(self.user_a)

        add_response = self.client.post(
            self.wishlist_url,
            {"product_id": self.product_2.pk},
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_201_CREATED)

        list_response = self.client.get(self.wishlist_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["product"]["name"], "Beta Headphones")

        wishlist_item = WishlistItem.objects.get(user=self.user_a, product=self.product_2)
        delete_response = self.client.delete(
            reverse("wishlist-item-detail", kwargs={"pk": wishlist_item.pk})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WishlistItem.objects.filter(pk=wishlist_item.pk).exists())

    def test_coupon_list_and_validate(self):
        Coupon.objects.create(code="SAVE10", discount_percent=10, min_order_amount=1000)
        Coupon.objects.create(
            code="SAVE20",
            discount_percent=20,
            min_order_amount=2000,
            is_active=False,
        )

        self.authenticate(self.user_a)

        list_response = self.client.get(self.coupons_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["code"], "SAVE10")

        validate_response = self.client.post(
            self.coupon_validate_url,
            {"code": "SAVE10"},
            format="json",
        )
        self.assertEqual(validate_response.status_code, status.HTTP_200_OK)
        self.assertEqual(validate_response.data["code"], "SAVE10")

        invalid_response = self.client.post(
            self.coupon_validate_url,
            {"code": "DOES-NOT-EXIST"},
            format="json",
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_creates_order_uses_coupon_and_clears_cart(self):
        Coupon.objects.create(code="SAVE10", discount_percent=10, min_order_amount=0)
        self.authenticate(self.user_a)

        self.client.post(
            self.cart_url,
            {"product_id": self.product_1.pk, "quantity": 2},
            format="json",
        )

        response = self.client.post(
            self.checkout_url,
            {"coupon_code": "SAVE10"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal"], 2000)
        self.assertEqual(response.data["discountAmount"], 200)
        self.assertEqual(response.data["totalAmount"], 1800)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["name"], "Alpha Shoes")

        self.assertEqual(Order.objects.filter(user=self.user_a).count(), 1)
        self.assertEqual(CartItem.objects.filter(cart=self.user_a.cart).count(), 0)

    def test_user_a_cannot_access_user_b_orders(self):
        order = Order.objects.create(
            user=self.user_b,
            subtotal=1000,
            discount_amount=0,
            total_amount=1000,
        )

        self.authenticate(self.user_a)
        response = self.client.get(reverse("order-detail", kwargs={"pk": order.pk}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
