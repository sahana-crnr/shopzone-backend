import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Product


def _infer_category(item):
    name = f"{item.get('name', '')} {item.get('description', '')}".lower()

    electronics_terms = [
        "headphone",
        "smartwatch",
        "speaker",
        "mouse",
        "keyboard",
        "camera",
        "drone",
        "webcam",
        "monitor",
        "hub",
        "powerbank",
        "power bank",
        "usb",
        "harddrive",
        "hard drive",
        "earbud",
        "laptop",
    ]
    fashion_terms = [
        "shoe",
        "sneaker",
        "backpack",
        "wallet",
        "tape",
        "trimmer",
        "shaver",
        "groomer",
        "hair",
        "bag",
        "watch",
    ]
    home_terms = [
        "lamp",
        "kettle",
        "toaster",
        "microwave",
        "airfryer",
        "air fryer",
        "blender",
        "coffee",
        "cooker",
        "iron",
        "heater",
        "fan",
        "purifier",
        "dehumidifier",
        "humidifier",
        "lamp",
        "massager",
        "lamp",
    ]
    sports_terms = ["yoga", "mat", "sports", "outdoor", "fitness"]
    books_terms = ["book", "magazine", "media"]

    if any(term in name for term in electronics_terms):
        return "Electronics"
    if any(term in name for term in fashion_terms):
        return "Fashion & Apparel"
    if any(term in name for term in home_terms):
        return "Home & Furniture"
    if any(term in name for term in sports_terms):
        return "Sports & Outdoors"
    if any(term in name for term in books_terms):
        return "Books & Media"
    return ""


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
                    "category": _infer_category(item),
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
