from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import Product
from commerce.models import Cart
from commerce.models import CartItem, WishlistItem


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

    def authenticate(self, user):
        access = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_cart_requires_authentication(self):
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wishlist_requires_authentication(self):
        response = self.client.get(self.wishlist_url)
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
