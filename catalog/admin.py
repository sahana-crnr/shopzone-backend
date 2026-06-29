from django.contrib import admin

from .models import Product, ProductReview, ProductTag


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "rating",
        "ratings_count",
        "reviews_count",
    )
    search_fields = ("name", "description", "color", "size", "category", "tags__name")
    list_filter = ("rating", "category", "tags")
    filter_horizontal = ("tags",)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "user", "rating", "created_at")
    search_fields = ("product__name", "user__name", "user__email", "comment")
    list_filter = ("rating", "created_at")
