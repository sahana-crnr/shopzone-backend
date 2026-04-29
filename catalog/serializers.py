from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    originalPrice = serializers.IntegerField(
        source="original_price", required=False, allow_null=True
    )
    ratingsCount = serializers.IntegerField(source="ratings_count", read_only=True)
    reviewsCount = serializers.IntegerField(source="reviews_count", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "size",
            "color",
            "description",
            "price",
            "image",
            "originalPrice",
            "rating",
            "ratingsCount",
            "reviewsCount",
        ]
        read_only_fields = ["id"]


class ProductQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.IntegerField(required=False, min_value=0)
    max_price = serializers.IntegerField(required=False, min_value=0)
    min_rating = serializers.FloatField(required=False, min_value=0, max_value=5)
    min_reviews = serializers.IntegerField(required=False, min_value=0)
    sort = serializers.ChoiceField(
        required=False,
        choices=[
            "default",
            "price-asc",
            "price-desc",
            "rating-desc",
            "name-asc",
            "name-desc",
            "price",
            "-price",
            "rating",
            "-rating",
            "reviews",
            "-reviews",
            "name",
            "-name",
        ],
        default="default",
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=12)

