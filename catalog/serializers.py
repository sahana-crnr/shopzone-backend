from rest_framework import serializers
from .models import Product, ProductReview, ProductTag


class ProductTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ['id', 'name']


class ProductReviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'author', 'rating', 'comment', 'image', 'createdAt']

    def get_author(self, obj):
        return obj.user.name or obj.user.email.split('@')[0]


class ProductSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_rating(self, obj):
        reviews = obj.customer_reviews.all()
        if not reviews.exists():
            return 0.0
        avg = sum(r.rating for r in reviews) / len(reviews)
        return round(avg, 1)

    def get_ratings_count(self, obj):
        return obj.customer_reviews.count()

    def get_reviews_count(self, obj):
        return obj.customer_reviews.count()

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]