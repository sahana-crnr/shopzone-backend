from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product


class ProductApiTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("product-list")

        self.product_1 = Product.objects.create(
            name="Alpha Shoes",
            size="EU42",
            color="Black",
            description="Running shoes",
            price=1000,
            image="/images/alpha.png",
            original_price=1500,
            rating=4.1,
            ratings_count=100,
            reviews_count=10,
        )
        self.product_2 = Product.objects.create(
            name="Beta Headphones",
            size="Standard",
            color="White",
            description="Wireless audio",
            price=2000,
            image="/images/beta.png",
            original_price=2500,
            rating=4.8,
            ratings_count=200,
            reviews_count=40,
        )
        self.product_3 = Product.objects.create(
            name="Gamma Lamp",
            size="Standard",
            color="Blue",
            description="Desk light",
            price=3000,
            image="/images/gamma.png",
            original_price=3500,
            rating=3.9,
            ratings_count=300,
            reviews_count=70,
        )

    def test_list_supports_filters_sort_and_pagination(self):
        response = self.client.get(
            self.list_url,
            {
                "search": "Headphones",
                "min_price": 1500,
                "max_price": 2500,
                "min_rating": 4.5,
                "min_reviews": 20,
                "sort": "price-desc",
                "page": 1,
                "page_size": 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Beta Headphones")
        self.assertEqual(response.data["totalCount"], 1)
        self.assertFalse(response.data["has_more"])

    def test_detail_returns_single_product(self):
        response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.product_2.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Beta Headphones")

    def test_detail_unknown_product_returns_404(self):
        response = self.client.get(reverse("product-detail", kwargs={"pk": 9999}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

