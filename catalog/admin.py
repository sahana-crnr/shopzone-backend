from django.contrib import admin

from .models import Product, ProductReview, ProductTag


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "reviews_count")
    list_filter = ("category", "rating")
    search_fields = ("name", "description")
    readonly_fields = ("rating", "ratings_count", "reviews_count", "created_at", "updated_at")


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("comment", "product__name", "user__name")
    readonly_fields = ("created_at",)