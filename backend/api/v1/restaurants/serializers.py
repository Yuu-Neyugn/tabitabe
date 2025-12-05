"""
Restaurant API serializers
"""
from rest_framework import serializers
from apps.restaurants.models import Restaurant, Product, RestaurantStatus
from apps.media_manager.models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    """Media file serializer for restaurant images"""
    
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFile
        fields = ['id', 'file_url', 'title', 'alt_text', 'width', 'height', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_file_url(self, obj):
        """Get file URL"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Product (menu item) serializer"""
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 
            'category', 'is_available', 'image_url',
            'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RestaurantListSerializer(serializers.ModelSerializer):
    """Restaurant list serializer (compact view)"""
    
    primary_image = serializers.SerializerMethodField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    distance = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True, required=False)
    active_campaigns = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description',
            'prefecture', 'city', 'address_line',
            'primary_image', 'average_rating', 'review_count',
            'distance', 'active_campaigns', 'opening_time', 'closing_time'
        ]
    
    def get_primary_image(self, obj):
        """Get primary restaurant image from related media files"""
        # TODO: Implement after establishing media relationship
        return None
    
    def get_active_campaigns(self, obj):
        """Get active campaigns for this restaurant"""
        from django.utils import timezone
        campaigns = obj.campaigns.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).values('id', 'name', 'discount_percentage')
        return list(campaigns)


class RestaurantDetailSerializer(serializers.ModelSerializer):
    """Restaurant detail serializer (full view)"""
    
    products = serializers.SerializerMethodField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    active_campaigns = serializers.SerializerMethodField()
    owner_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description',
            'phone_number', 'email', 'website',
            'postal_code', 'prefecture', 'city', 'address_line',
            'latitude', 'longitude',
            'opening_time', 'closing_time', 'regular_holiday',
            'capacity', 'parking_info', 'access_info',
            'payment_methods', 'features',
            'average_rating', 'review_count',
            'products', 'active_campaigns',
            'owner_info', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
    
    def get_products(self, obj):
        """Get available products grouped by category"""
        products = obj.products.filter(is_available=True).order_by('category', 'display_order')
        return ProductSerializer(products, many=True).data
    
    def get_active_campaigns(self, obj):
        """Get detailed active campaigns"""
        from django.utils import timezone
        campaigns = obj.campaigns.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        return [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'discount_percentage': c.discount_percentage,
            'start_date': c.start_date,
            'end_date': c.end_date,
        } for c in campaigns]
    
    def get_owner_info(self, obj):
        """Get basic owner info (only if user is owner or admin)"""
        request = self.context.get('request')
        if request and (request.user == obj.user or request.user.is_staff):
            return {
                'name': f"{obj.user.first_name} {obj.user.last_name}".strip(),
                'email': obj.user.email,
                'phone': obj.user.phone_number,
            }
        return None


class RestaurantUpdateSerializer(serializers.ModelSerializer):
    """Restaurant update serializer (for owners)"""
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description',
            'phone_number', 'email', 'website',
            'postal_code', 'prefecture', 'city', 'address_line',
            'latitude', 'longitude',
            'opening_time', 'closing_time', 'regular_holiday',
            'capacity', 'parking_info', 'access_info',
            'payment_methods', 'features'
        ]
    
    def validate(self, attrs):
        """Validate restaurant data"""
        # Ensure restaurant is not suspended
        if self.instance and self.instance.status == RestaurantStatus.SUSPENDED:
            raise serializers.ValidationError(
                "Cannot update suspended restaurant. Please contact admin."
            )
        return attrs


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Product create/update serializer"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category',
            'is_available', 'image_url', 'display_order'
        ]
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class MediaFileUploadSerializer(serializers.ModelSerializer):
    """Media file upload serializer for restaurant images"""
    
    class Meta:
        model = MediaFile
        fields = ['file', 'title', 'alt_text']
    
    def create(self, validated_data):
        """Create media file with auto-filled metadata"""
        file = validated_data.get('file')
        validated_data['file_name'] = file.name
        validated_data['file_size'] = file.size
        validated_data['mime_type'] = file.content_type or 'application/octet-stream'
        validated_data['media_type'] = MediaFile.MediaType.IMAGE
        validated_data['uploader'] = self.context['request'].user
        return super().create(validated_data)
