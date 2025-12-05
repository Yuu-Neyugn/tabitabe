"""
Restaurant API views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
# from django.contrib.gis.geos import Point  # Requires GDAL
# from django.contrib.gis.measure import D
from django_filters.rest_framework import DjangoFilterBackend
import math

from apps.restaurants.models import Restaurant, Product, RestaurantStatus
from apps.media_manager.models import MediaFile
from apps.core.permissions import IsRestaurantOwner
from .serializers import (
    RestaurantListSerializer,
    RestaurantDetailSerializer,
    RestaurantUpdateSerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
    MediaFileSerializer,
    MediaFileUploadSerializer,
)


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    Restaurant API ViewSet
    
    Public endpoints:
    - list: GET /api/v1/restaurants/
    - retrieve: GET /api/v1/restaurants/{id}/
    - nearby: GET /api/v1/restaurants/nearby/?lat=35.6762&lng=139.6503&radius=5
    
    Owner endpoints (requires authentication):
    - my_restaurant: GET /api/v1/restaurants/my-restaurant/
    - update: PATCH /api/v1/restaurants/my-restaurant/
    """
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'address_line']
    ordering_fields = ['created_at', 'name']
    filterset_fields = ['prefecture', 'city', 'status']
    
    def get_queryset(self):
        """Get queryset with annotations"""
        queryset = Restaurant.objects.select_related('user').prefetch_related(
            'products', 'campaigns'
        ).annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        
        # Public endpoints: only show approved restaurants
        if self.action in ['list', 'retrieve', 'nearby']:
            queryset = queryset.filter(status=RestaurantStatus.APPROVED)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'list':
            return RestaurantListSerializer
        elif self.action in ['update', 'partial_update', 'my_restaurant']:
            return RestaurantUpdateSerializer
        return RestaurantDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['update', 'partial_update', 'my_restaurant']:
            return [IsAuthenticated(), IsRestaurantOwner()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """
        List approved restaurants with filters
        
        Query params:
        - prefecture: Filter by prefecture
        - city: Filter by city
        - cuisine_types: Filter by cuisine type
        - search: Search in name, description
        - ordering: Sort by field (created_at, average_rating, name)
        - campaign: Filter restaurants with active campaigns
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter by active campaigns
        if request.query_params.get('campaign'):
            queryset = queryset.filter(
                campaigns__is_active=True,
                campaigns__start_date__lte=timezone.now(),
                campaigns__end_date__gte=timezone.now()
            ).distinct()
        
        # Filter by rating
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=float(min_rating))
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get nearby restaurants using simple distance calculation
        
        Query params:
        - lat: Latitude (required)
        - lng: Longitude (required)
        - radius: Search radius in km (default: 5km)
        
        Note: Uses Haversine formula for distance calculation.
        For production with large datasets, consider PostGIS.
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 5))
        
        if not lat or not lng:
            return Response(
                {'error': 'lat and lng parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_lat = float(lat)
            user_lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Invalid lat/lng values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all restaurants with coordinates
        queryset = self.get_queryset().filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Calculate distance using Haversine formula
        restaurants_with_distance = []
        for restaurant in queryset:
            distance = self._calculate_distance(
                user_lat, user_lng,
                float(restaurant.latitude), float(restaurant.longitude)
            )
            if distance <= radius:
                restaurant.distance = round(distance, 2)
                restaurants_with_distance.append(restaurant)
        
        # Sort by distance
        restaurants_with_distance.sort(key=lambda x: x.distance)
        
        # Paginate
        page = self.paginate_queryset(restaurants_with_distance)
        if page is not None:
            serializer = RestaurantListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RestaurantListSerializer(restaurants_with_distance, many=True)
        return Response(serializer.data)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def my_restaurant(self, request):
        """
        Get or update authenticated user's restaurant
        
        GET: Retrieve own restaurant
        PATCH: Update own restaurant
        """
        try:
            restaurant = Restaurant.objects.select_related('user').prefetch_related(
                'products', 'campaigns'
            ).annotate(
                average_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).get(user=request.user)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            serializer = RestaurantDetailSerializer(restaurant, context={'request': request})
            return Response(serializer.data)
        
        # PATCH - Update
        serializer = RestaurantUpdateSerializer(
            restaurant, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product (Menu Item) API ViewSet
    
    Owner endpoints only (requires authentication + owner permission)
    """
    
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        """Get products for authenticated user's restaurant"""
        restaurant_id = self.kwargs.get('restaurant_pk')
        return Product.objects.filter(restaurant_id=restaurant_id).order_by('category', 'display_order')
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        """Create product for restaurant"""
        restaurant_id = self.kwargs.get('restaurant_pk')
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, user=self.request.user)
            serializer.save(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Restaurant not found or you are not the owner')


class MediaFileViewSet(viewsets.ModelViewSet):
    """
    Media File API ViewSet for restaurant images
    
    Owner endpoints only (requires authentication + owner permission)
    """
    
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    serializer_class = MediaFileSerializer
    
    def get_queryset(self):
        """Get media files for authenticated user's restaurant"""
        # TODO: Add proper filtering based on restaurant relationship
        return MediaFile.objects.filter(
            uploader=self.request.user,
            media_type=MediaFile.MediaType.IMAGE
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action in ['create', 'update', 'partial_update']:
            return MediaFileUploadSerializer
        return MediaFileSerializer
    
    def perform_create(self, serializer):
        """Create media file"""
        serializer.save(context={'request': self.request})
