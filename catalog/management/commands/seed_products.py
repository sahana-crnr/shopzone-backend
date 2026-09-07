import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product


class Command(BaseCommand):
    help = "Synchronize the product catalog with catalog/data/products.json."

    def handle(self, *args, **options):
        data_file = Path(__file__).resolve().parents[2] / "data" / "products.json"
        with data_file.open(encoding="utf-8") as file:
            products = json.load(file)

        product_ids = [product["id"] for product in products]
        with transaction.atomic():
            # Keep database IDs equal to the IDs used by the frontend data file.
            for item in products:
                Product.objects.update_or_create(
                    id=item["id"],
                    defaults={
                        "name": item["name"],
                        "category": item.get("category", ""),
                        "size": item.get("size", ""),
                        "color": item.get("color", ""),
                        "description": item.get("description", ""),
                        "price": item["price"],
                        "image": item.get("image", ""),
                        "images": item.get("images", []),
                        "original_price": item.get("originalPrice"),
                        "rating": item.get("rating", 0),
                        "ratings_count": item.get("ratingsCount", 0),
                        "reviews_count": item.get("reviewsCount", 0),
                    },
                )

            # Keep only products explicitly supplied by products.json.
            deleted, _ = Product.objects.exclude(id__in=product_ids).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Catalog synchronized: {len(products)} JSON products loaded; {deleted} old records removed."
        ))
