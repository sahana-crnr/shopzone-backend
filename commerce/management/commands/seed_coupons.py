from django.core.management.base import BaseCommand
from django.db import transaction

from commerce.models import Coupon


class Command(BaseCommand):
    help = "Seed default discount coupons for local development."

    def handle(self, *args, **options):
        coupons = [
            {"code": "SAVE10", "discount_percent": 10, "min_order_amount": 0},
            {"code": "SAVE20", "discount_percent": 20, "min_order_amount": 0},
        ]

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for coupon_data in coupons:
                _, created = Coupon.objects.update_or_create(
                    code=coupon_data["code"],
                    defaults={
                        "discount_percent": coupon_data["discount_percent"],
                        "min_order_amount": coupon_data["min_order_amount"],
                        "is_active": True,
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded coupons successfully. Created: {created_count}, updated: {updated_count}."
            )
        )
