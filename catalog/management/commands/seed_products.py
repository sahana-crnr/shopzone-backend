import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Product


class Command(BaseCommand):
    help = "Seed the product catalog from catalog/data/products.json."

    def handle(self, *args, **options):
        source_file = Path(__file__).resolve().parents[2] / "data" / "products.json"

        if not source_file.exists():
            raise CommandError(f"Could not find source products file: {source_file}")

        with source_file.open("r", encoding="utf-8") as file:
            raw_products = json.load(file)

        if not isinstance(raw_products, list):
            raise CommandError("products.json must contain a JSON array.")

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for item in raw_products:
                if not isinstance(item, dict) or "id" not in item or "name" not in item:
                    continue

                defaults = {
                    "name": item.get("name", ""),
                    "size": item.get("size", ""),
                    "color": item.get("color", ""),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "image": item.get("image", ""),
                    "original_price": item.get("originalPrice"),
                    "rating": item.get("rating", 0),
                    "ratings_count": item.get("ratingsCount", 0),
                    "reviews_count": item.get("reviewsCount", 0),
                }

                _, created = Product.objects.update_or_create(
                    id=item["id"],
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded products successfully. Created: {created_count}, updated: {updated_count}."
            )
        )
