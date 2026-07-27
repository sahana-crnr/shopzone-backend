import decimal

from django.core.management.base import BaseCommand

from catalog.models import Product


class Command(BaseCommand):
    help = "Seeds the database with an initial set of products."

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.SUCCESS("Products already seeded. Skipping."))
            return

        products_to_create = [
            {
                "name": "Classic Leather Jacket",
                "description": "A timeless leather jacket for any occasion.",
                "price": decimal.Decimal("199.99"),
                "image": "images/products/leather_jacket.jpg",
            },
            {
                "name": "Wireless Bluetooth Headphones",
                "description": "High-fidelity sound with a 20-hour battery life.",
                "price": decimal.Decimal("89.99"),
                "image": "images/products/headphones.jpg",
            },
            {
                "name": "Modern Minimalist Watch",
                "description": "A sleek and stylish watch that complements any outfit.",
                "price": decimal.Decimal("149.50"),
                "image": "images/products/watch.jpg",
            },
            # Add more products here if you wish
        ]

        for product_data in products_to_create:
            Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "description": product_data["description"],
                    "price": product_data["price"],
                    "image": product_data["image"],
                    # Ensure all rating and review counts start at 0
                    "rating": 0,
                    "ratings_count": 0,
                    "reviews_count": 0,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(products_to_create)} products."
            )
        )