from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from .models import Product, ProductReview, Banner
from .serializers import ProductSerializer, ProductReviewSerializer, BannerSerializer


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        total_pages = self.page.paginator.num_pages
        current_page = self.page.number
        return Response({
            'count': self.page.paginator.count,
            'page': current_page,
            'page_size': self.get_page_size(self.request),
            'total_pages': total_pages,
            'has_more': current_page < total_pages,
            'results': data
        })


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = Product.objects.all()
        params = self.request.query_params

        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )

        category = params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        min_price = params.get('min_price')
        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        max_price = params.get('max_price')
        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        min_rating = params.get('min_rating')
        if min_rating is not None:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass

        sort = params.get('sort')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset

    @action(detail=True, methods=['get', 'post'], permission_classes=[AllowAny])
    def reviews(self, request, pk=None):
        product = self.get_object()

        if request.method == 'GET':
            reviews_qs = product.customer_reviews.all()
            serializer = ProductReviewSerializer(reviews_qs, many=True)
            return Response(serializer.data)

        if request.method == 'POST':
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            rating_val = request.data.get('rating')
            comment = request.data.get('comment', '').strip()
            image = request.data.get('image', '')

            if rating_val is None or not comment:
                return Response(
                    {'detail': 'Rating and comment are required.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                rating_int = int(rating_val)
                if not (1 <= rating_int <= 5):
                    raise ValueError()
            except ValueError:
                return Response(
                    {'detail': 'Rating must be an integer between 1 and 5.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review = ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=rating_int,
                comment=comment,
                image=image,
            )

            reviews_qs = product.customer_reviews.all()
            count = reviews_qs.count()
            avg = sum(r.rating for r in reviews_qs) / count if count > 0 else 0.0

            product.reviews_count = count
            product.ratings_count = count
            product.rating = round(avg, 1)
            product.save()

            serializer = ProductReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        featured_products = list(Product.objects.filter(is_featured=True)[:8])
        if len(featured_products) < 4:
            existing_ids = {p.id for p in featured_products}
            needed = 8 - len(featured_products)
            fallback = Product.objects.exclude(id__in=existing_ids).order_by('-rating', '-ratings_count')[:needed]
            featured_products.extend(list(fallback))

        serializer = ProductSerializer(featured_products, many=True)
        return Response(serializer.data)


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Banner.objects.filter(is_active=True).order_by('order', '-id')
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    pagination_class = None