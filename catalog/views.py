from django.core.paginator import EmptyPage, Paginator
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Product, ProductReview
from .serializers import (
    ProductQuerySerializer,
    ProductReviewCreateSerializer,
    ProductReviewSerializer,
    ProductSerializer,
)
from .search_terms import expand_search_terms


ORDERING_MAP = {
    "default": "id",
    "price-asc": "price",
    "price-desc": "-price",
    "rating-desc": "-rating",
    "name-asc": "name",
    "name-desc": "-name",
    "price": "price",
    "-price": "-price",
    "rating": "rating",
    "-rating": "-rating",
    "reviews": "reviews_count",
    "-reviews": "-reviews_count",
    "name": "name",
    "-name": "-name",
}


def _normalize_query_params(query_params):
    mapping = {
        "search": query_params.get("search") or query_params.get("searchTerm") or "",
        "min_price": query_params.get("min_price") or query_params.get("minPrice"),
        "max_price": query_params.get("max_price") or query_params.get("maxPrice"),
        "min_rating": query_params.get("min_rating") or query_params.get("minRating"),
        "min_reviews": query_params.get("min_reviews") or query_params.get("minReviews"),
        "category": query_params.get("category") or query_params.get("categoryName"),
        "sort": query_params.get("sort") or query_params.get("sortBy") or "default",
        "page": query_params.get("page") or query_params.get("pageNumber"),
        "page_size": query_params.get("page_size") or query_params.get("pageSize"),
    }
    return {key: value for key, value in mapping.items() if value not in (None, "")}


class ProductListView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get(self, request):
        query_serializer = ProductQuerySerializer(
            data=_normalize_query_params(request.query_params)
        )
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        queryset = Product.objects.all()

        search = filters.get("search", "").strip()
        if search:
            for term in search.split():
                expanded_terms = expand_search_terms(term)
                queryset = queryset.filter(
                    Q(name__icontains=term)
                    | Q(description__icontains=term)
                    | Q(color__icontains=term)
                    | Q(size__icontains=term)
                    | Q(category__icontains=term)
                    | Q(tags__name__in=expanded_terms)
                )
            queryset = queryset.distinct()

        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        min_rating = filters.get("min_rating")
        min_reviews = filters.get("min_reviews")
        category = filters.get("category", "").strip()

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)
        if min_reviews is not None:
            queryset = queryset.filter(reviews_count__gte=min_reviews)
        if category:
            queryset = queryset.filter(category__iexact=category)

        sort_key = filters.get("sort", "default")
        queryset = queryset.order_by(ORDERING_MAP.get(sort_key, "id"))

        page = filters.get("page", 1)
        page_size = filters.get("page_size", 12)
        paginator = Paginator(queryset, page_size)

        try:
            page_obj = paginator.page(page)
        except EmptyPage as exc:
            raise NotFound("Page not found.") from exc

        products = ProductSerializer(page_obj.object_list, many=True).data

        return Response(
            {
                "count": paginator.count,
                "page": page_obj.number,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "has_more": page_obj.has_next(),
                "results": products,
                "products": products,
                "totalCount": paginator.count,
            }
        )


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


def _refresh_product_review_totals(product):
    summary = product.customer_reviews.aggregate(
        average_rating=Avg("rating"),
    )
    product.reviews_count = product.customer_reviews.count()
    product.ratings_count = product.reviews_count
    product.rating = round(summary["average_rating"] or 0, 1)
    product.save(update_fields=["reviews_count", "ratings_count", "rating", "updated_at"])


class ProductReviewListCreateView(generics.GenericAPIView):
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs["pk"])

    def get_queryset(self):
        return ProductReview.objects.filter(product_id=self.kwargs["pk"]).select_related(
            "user",
            "product",
        )

    def get(self, request, *args, **kwargs):
        reviews = self.get_queryset()
        return Response(ProductReviewSerializer(reviews, many=True).data)

    def post(self, request, *args, **kwargs):
        product = self.get_product()
        serializer = ProductReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(product=product, user=request.user)
        _refresh_product_review_totals(product)
        return Response(ProductReviewSerializer(review).data, status=status.HTTP_201_CREATED)
