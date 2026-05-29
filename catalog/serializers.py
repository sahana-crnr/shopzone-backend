from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    originalPrice = serializers.IntegerField(
        source="original_price", required=False, allow_null=True
    )
    ratingsCount = serializers.IntegerField(source="ratings_count", read_only=True)
    reviewsCount = serializers.IntegerField(source="reviews_count", read_only=True)
    tags = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "size",
            "color",
            "description",
            "price",
            "image",
            "images",
            "originalPrice",
            "rating",
            "ratingsCount",
            "reviewsCount",
            "tags",
        ]
        read_only_fields = ["id"]

    def get_images(self, product):
        images = product.images if isinstance(product.images, list) else []
        images = [image for image in images if image]

        if images:
            return images
        if product.image:
            return [product.image]
        return []


class ProductQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True)
    min_price = serializers.IntegerField(required=False, min_value=0)
    max_price = serializers.IntegerField(required=False, min_value=0)
    min_rating = serializers.FloatField(required=False, min_value=0, max_value=5)
    min_reviews = serializers.IntegerField(required=False, min_value=0)
    category = serializers.CharField(required=False, allow_blank=True)
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
