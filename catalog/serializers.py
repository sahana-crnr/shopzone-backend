from urllib.parse import quote_plus

from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    carousel_image_count = 6
    blank_image_start = 4
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

        if product.image and product.image not in images:
            images.insert(0, product.image)

        label = quote_plus(product.name or "Product")
        while len(images) < 3:
            view_number = len(images) + 1
            images.append(
                f"https://placehold.co/400x400?text={label}+View+{view_number}"
            )

        images = images[:3]
        images.extend(
            f"https://placehold.co/400x400/ffffff/ffffff.png?blank={slot}"
            for slot in range(self.blank_image_start, self.carousel_image_count + 1)
        )

        return images[: self.carousel_image_count]


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
