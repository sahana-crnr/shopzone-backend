from django.conf import settings
from django.db import models


class ProductTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    image = models.CharField(max_length=500, blank=True)
    images = models.JSONField(default=list, blank=True)
    original_price = models.PositiveIntegerField(null=True, blank=True)
    rating = models.FloatField(default=0)
    ratings_count = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(
        ProductTag,
        related_name="products",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="customer_reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews",
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    image = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.product} review by {self.user}"
