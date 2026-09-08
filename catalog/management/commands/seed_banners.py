from django.core.management.base import BaseCommand
from catalog.models import Banner, Product


class Command(BaseCommand):
    help = "Seed promotional banners, assign clean categories to products, and flag featured items."

    def handle(self, *args, **options):
        banners_data = [
            {
                "order": 1,
                "title": "Mega Tech & Audio Fest",
                "subtitle": "Immerse in sound & power. Up to 50% off on premium wireless audio, smartwatches & accessories.",
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1200&auto=format&fit=crop&q=80",
                "target_category": "Electronics",
                "button_text": "Shop Gadgets",
                "badge": "⚡ Limited Time Deal",
                "bg_gradient": "from-slate-950 via-indigo-950 to-blue-900",
                "is_active": True,
            },
            {
                "order": 2,
                "title": "Step Up Your Game",
                "subtitle": "Discover performance running shoes & streetwear sneakers engineered for style and endurance.",
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1200&auto=format&fit=crop&q=80",
                "target_category": "Footwear",
                "button_text": "Explore Footwear",
                "badge": "🔥 New Arrivals",
                "bg_gradient": "from-stone-950 via-rose-950 to-neutral-900",
                "is_active": True,
            },
            {
                "order": 3,
                "title": "Modern Home & Kitchen",
                "subtitle": "Upgrade your lifestyle with energy-efficient air purifiers, coffee makers, smart hubs & fryers.",
                "image_url": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=1200&auto=format&fit=crop&q=80",
                "target_category": "Home & Kitchen",
                "button_text": "Upgrade Home",
                "badge": "✨ Up to 40% Off",
                "bg_gradient": "from-zinc-950 via-emerald-950 to-teal-950",
                "is_active": True,
            },
            {
                "order": 4,
                "title": "Daily Wellness & Grooming",
                "subtitle": "Elevate your self-care routine with precision trimmers, massagers, styling tools & more.",
                "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&auto=format&fit=crop&q=80",
                "target_category": "Personal Care",
                "button_text": "Discover Wellness",
                "badge": "⭐ Customer Favorites",
                "bg_gradient": "from-neutral-950 via-purple-950 to-slate-900",
                "is_active": True,
            },
        ]

        Banner.objects.all().delete()
        for b in banners_data:
            Banner.objects.create(**b)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(banners_data)} promotional banners."))

        category_rules = [
            ("Footwear", ["shoe", "sneaker", "air max", "boot", "sandal", "footwear"]),
            (
                "Electronics",
                [
                    "headphone", "earbud", "speaker", "mouse", "keyboard", "smartwatch",
                    "smart watch", "power bank", "charging pad", "hard drive", "webcam",
                    "usb-c hub", "gaming console", "vr headset", "drone", "television",
                    "home theater", "smart home hub",
                ],
            ),
            (
                "Home & Kitchen",
                [
                    "kettle", "coffee maker", "blender", "air fryer", "pressure cooker",
                    "toaster", "iron", "air purifier", "purifier", "humidifier",
                    "dehumidifier", "fan", "heater", "microwave", "refrigerator",
                    "washing machine", "air conditioner", "photo frame", "desk lamp",
                ],
            ),
            (
                "Personal Care",
                [
                    "toothbrush", "hair dryer", "straightener", "curling iron",
                    "shaver", "trimmer", "groomer", "massager", "yoga mat",
                ],
            ),
            (
                "Accessories",
                ["backpack", "wallet", "laptop sleeve", "travel mug", "monitor stand"],
            ),
        ]

        updated_count = 0
        for p in Product.objects.all():
            lower_name = p.name.lower()
            matched = False
            for cat_name, keywords in category_rules:
                if any(kw in lower_name for kw in keywords):
                    p.category = cat_name
                    matched = True
                    break
            if not matched:
                p.category = "Accessories"
            p.save(update_fields=["category"])
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated categories for {updated_count} products."))

        featured_ids = [1, 3, 4, 6, 8, 19, 32, 56, 57]
        Product.objects.filter(id__in=featured_ids).update(is_featured=True)
        self.stdout.write(self.style.SUCCESS(f"Flagged {len(featured_ids)} products as featured!"))
