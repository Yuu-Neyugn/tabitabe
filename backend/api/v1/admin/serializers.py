"""
Admin API Serializers
"""
from rest_framework import serializers
from apps.accounts.models import CustomUser, CustomerProfile
from apps.restaurants.models import Restaurant, Product
from apps.reviews.models import Review
from apps.campaigns.models import GiftCard, Stamprally


class UserListSerializer(serializers.ModelSerializer):
    """User list serializer for admin"""
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'user_type', 'user_type_display',
            'first_name', 'last_name', 'is_active', 
            'is_email_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined']


class UserDetailSerializer(serializers.ModelSerializer):
    """User detail serializer for admin"""
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    customer_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'user_type', 'user_type_display',
            'first_name', 'last_name', 'is_active', 'is_staff',
            'is_superuser', 'is_email_verified', 'oidc_subject',
            'date_joined', 'last_login', 'last_login_ip',
            'customer_profile'
        ]
        read_only_fields = ['id', 'date_joined', 'oidc_subject']
    
    def get_customer_profile(self, obj):
        if obj.user_type == 1 and hasattr(obj, 'customer_profile'):
            return {
                'customer_number': obj.customer_profile.customer_number,
                'phone_number': str(obj.customer_profile.phone_number) if obj.customer_profile.phone_number else None,
                'prefecture': obj.customer_profile.prefecture,
                'city': obj.customer_profile.city,
            }
        return None


class RestaurantApprovalSerializer(serializers.ModelSerializer):
    """Restaurant approval serializer"""
    owner_email = serializers.EmailField(source='user.email', read_only=True)
    owner_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'user', 'owner_email', 'owner_name',
            'status', 'status_display', 'phone_number', 'email',
            'prefecture', 'city', 'address_line', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_owner_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class RestaurantApprovalActionSerializer(serializers.Serializer):
    """Restaurant approval action serializer"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a restaurant.'
            })
        return data


class AnalyticsSummarySerializer(serializers.Serializer):
    """Analytics summary serializer"""
    total_users = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_restaurants = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    pending_restaurants = serializers.IntegerField()
    active_gift_cards = serializers.IntegerField()
    active_stamp_rallies = serializers.IntegerField()
    avg_restaurant_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
