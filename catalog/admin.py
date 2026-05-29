from django.contrib import admin

from .models import Product, ProductTag


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
