from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Product, ProductTag


class ProductApiTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("product-list")

        self.product_1 = Product.objects.create(
            name="Alpha Shoes",
            category="Fashion & Apparel",
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
            category="Electronics",
            size="Standard",
            color="White",
            description="Wireless audio",
            price=2000,
            image="/images/beta.png",
            images=[
                "/images/beta.png",
                "/images/beta-side.png",
            ],
            original_price=2500,
            rating=4.8,
            ratings_count=200,
            reviews_count=40,
        )
        self.product_3 = Product.objects.create(
            name="Gamma Lamp",
            category="Home & Furniture",
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

    def test_list_can_filter_by_category(self):
        response = self.client.get(self.list_url, {"category": "Electronics"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Beta Headphones")

    def test_list_expands_search_terms_using_tags(self):
        shoes_tag = ProductTag.objects.create(name="shoes")
        sneaker_product = Product.objects.create(
            name="Runner Pro",
            category="Fashion & Apparel",
            size="EU43",
            color="White",
            description="Lightweight performance sneaker",
            price=1800,
            image="/images/runner.png",
            original_price=2200,
            rating=4.6,
            ratings_count=150,
            reviews_count=30,
        )
        sneaker_product.tags.add(shoes_tag)

        response = self.client.get(self.list_url, {"search": "sneakers"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(item["name"] == "Runner Pro" for item in response.data["results"])
        )

    def test_laptop_search_does_not_match_unrelated_electronics(self):
        laptop_product = Product.objects.create(
            name="UltraBook X",
            category="Electronics",
            size="13 inch",
            color="Silver",
            description="Portable notebook computer",
            price=65000,
            image="/images/laptop.png",
            original_price=72000,
            rating=4.7,
            ratings_count=250,
            reviews_count=80,
        )
        laptop_product.tags.add(ProductTag.objects.create(name="laptop"))

        headphones_product = Product.objects.create(
            name="Studio Headphones",
            category="Electronics",
            size="Standard",
            color="Black",
            description="Wireless audio device",
            price=3500,
            image="/images/headphones.png",
            original_price=4000,
            rating=4.2,
            ratings_count=180,
            reviews_count=45,
        )
        headphones_product.tags.add(ProductTag.objects.create(name="headphones"))

        response = self.client.get(self.list_url, {"search": "laptop"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_names = {item["name"] for item in response.data["results"]}
        self.assertIn("UltraBook X", returned_names)
        self.assertNotIn("Studio Headphones", returned_names)

    def test_detail_returns_single_product(self):
        response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.product_2.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Beta Headphones")
        self.assertEqual(
            response.data["images"],
            [
                "/images/beta.png",
                "/images/beta-side.png",
            ],
        )

    def test_detail_returns_image_fallback_when_images_are_empty(self):
        response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.product_1.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["images"], ["/images/alpha.png"])

    def test_detail_unknown_product_returns_404(self):
        response = self.client.get(reverse("product-detail", kwargs={"pk": 9999}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
