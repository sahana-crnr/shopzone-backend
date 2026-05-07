from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    image = models.CharField(max_length=500, blank=True)
    original_price = models.PositiveIntegerField(null=True, blank=True)
    rating = models.FloatField(default=0)
    ratings_count = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name
