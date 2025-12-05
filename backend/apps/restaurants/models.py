"""
Restaurant Models
Complete restaurant management with onboarding workflow
"""
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from apps.core.models import BaseModel, TimestampedModel
from apps.accounts.models import CustomUser
from decimal import Decimal


class RestaurantStatus(models.TextChoices):
    """Restaurant onboarding status"""
    DRAFT = 'draft', _('Draft')
    PENDING = 'pending', _('Pending Approval')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')
    SUSPENDED = 'suspended', _('Suspended')


class DayOfWeek(models.TextChoices):
    """Days of the week"""
    MONDAY = 'mon', _('Monday')
    TUESDAY = 'tue', _('Tuesday')
    WEDNESDAY = 'wed', _('Wednesday')
    THURSDAY = 'thu', _('Thursday')
    FRIDAY = 'fri', _('Friday')
    SATURDAY = 'sat', _('Saturday')
    SUNDAY = 'sun', _('Sunday')
    HOLIDAY = 'holiday', _('Holiday')


class Restaurant(BaseModel):
    """
    Restaurant Model
    Core restaurant information and settings
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='restaurant'
    )
    
    # Basic Information
    name = models.CharField('Restaurant Name', max_length=200, db_index=True)
    name_en = models.CharField('Restaurant Name (English)', max_length=200, blank=True)
    
    description = models.TextField('Description', max_length=2000, blank=True)
    description_en = models.TextField('Description (English)', max_length=2000, blank=True)
    
    # Contact
    phone_number = PhoneNumberField('Phone Number', unique=True, region='JP')
    email = models.EmailField('Restaurant Email', blank=True)
    website = models.URLField('Website', blank=True)
    
    # Social Media
    facebook_url = models.URLField('Facebook', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    twitter_url = models.URLField('Twitter/X', blank=True)
    line_id = models.CharField('LINE ID', max_length=100, blank=True)
    
    # Location
    postal_code = models.CharField(
        'Postal Code',
        max_length=8,
        validators=[RegexValidator(r'^\d{3}-?\d{4}$')]
    )
    prefecture = models.CharField('Prefecture', max_length=20)
    city = models.CharField('City', max_length=100)
    address_line = models.CharField('Address Line', max_length=200)
    building = models.CharField('Building', max_length=100, blank=True)
    
    # Geolocation
    latitude = models.DecimalField(
        'Latitude',
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))]
    )
    longitude = models.DecimalField(
        'Longitude',
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))]
    )
    
    # Operating Hours
    opening_time = models.TimeField('Opening Time')
    closing_time = models.TimeField('Closing Time')
    
    # Closed Days (Many-to-Many through intermediate model)
    # Will be handled by ClosedDay model below
    
    # Capacity & Features
    seating_capacity = models.PositiveIntegerField('Seating Capacity', null=True, blank=True)
    has_parking = models.BooleanField('Parking Available', default=False)
    has_wifi = models.BooleanField('WiFi Available', default=False)
    is_smoking_allowed = models.BooleanField('Smoking Allowed', default=False)
    accepts_reservations = models.BooleanField('Accepts Reservations', default=True)
    
    # Media
    logo = models.ImageField('Logo', upload_to='restaurants/logos/', null=True, blank=True)
    cover_image = models.ImageField('Cover Image', upload_to='restaurants/covers/', null=True, blank=True)
    interior_image1 = models.ImageField('Interior Image 1', upload_to='restaurants/interiors/', null=True, blank=True)
    interior_image2 = models.ImageField('Interior Image 2', upload_to='restaurants/interiors/', null=True, blank=True)
    interior_image3 = models.ImageField('Interior Image 3', upload_to='restaurants/interiors/', null=True, blank=True)
    
    # Status & Approval
    status = models.CharField(
        'Status',
        max_length=20,
        choices=RestaurantStatus.choices,
        default=RestaurantStatus.DRAFT,
        db_index=True
    )
    
    is_visible = models.BooleanField(
        'Visible to Public',
        default=False,
        help_text='Show restaurant on map and search'
    )
    
    is_active = models.BooleanField('Active', default=True)
    
    # Approval Info
    approved_at = models.DateTimeField('Approved At', null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_restaurants'
    )
    rejection_reason = models.TextField('Rejection Reason', blank=True)
    
    # Admin Notes
    admin_notes = models.TextField('Admin Notes', blank=True)
    
    # Statistics (cached)
    total_reviews = models.PositiveIntegerField('Total Reviews', default=0)
    average_rating = models.DecimalField(
        'Average Rating',
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))]
    )
    total_views = models.PositiveIntegerField('Total Views', default=0)
    
    class Meta:
        db_table = 'restaurants'
        verbose_name = 'Restaurant'
        verbose_name_plural = 'Restaurants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['prefecture', 'city']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [
            self.postal_code,
            self.prefecture,
            self.city,
            self.address_line
        ]
        if self.building:
            parts.append(self.building)
        return ' '.join(parts)
    
    def can_be_approved(self):
        """Check if restaurant can be approved"""
        return self.status == RestaurantStatus.PENDING
    
    def approve(self, admin_user):
        """Approve restaurant"""
        from django.utils import timezone
        self.status = RestaurantStatus.APPROVED
        self.approved_at = timezone.now()
        self.approved_by = admin_user
        self.is_visible = True
        self.save()
    
    def reject(self, reason, admin_user):
        """Reject restaurant"""
        self.status = RestaurantStatus.REJECTED
        self.rejection_reason = reason
        self.approved_by = admin_user
        self.is_visible = False
        self.save()
    
    def suspend(self, reason):
        """Suspend restaurant"""
        self.status = RestaurantStatus.SUSPENDED
        self.admin_notes = f"Suspended: {reason}"
        self.is_visible = False
        self.is_active = False
        self.save()


class ClosedDay(models.Model):
    """
    Restaurant closed days
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='closed_days'
    )
    day_of_week = models.CharField(
        'Day of Week',
        max_length=10,
        choices=DayOfWeek.choices
    )
    
    class Meta:
        db_table = 'restaurant_closed_days'
        verbose_name = 'Closed Day'
        verbose_name_plural = 'Closed Days'
        unique_together = ['restaurant', 'day_of_week']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_of_week_display()}"


class Cuisine(models.Model):
    """
    Cuisine types (Japanese, Italian, French, etc.)
    """
    name = models.CharField('Cuisine Type', max_length=50, unique=True)
    name_en = models.CharField('Cuisine Type (English)', max_length=50, blank=True)
    slug = models.SlugField('Slug', unique=True)
    icon = models.ImageField('Icon', upload_to='cuisines/', null=True, blank=True)
    display_order = models.PositiveIntegerField('Display Order', default=0)
    
    class Meta:
        db_table = 'cuisines'
        verbose_name = 'Cuisine'
        verbose_name_plural = 'Cuisines'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class RestaurantCuisine(models.Model):
    """
    Many-to-Many relationship between Restaurant and Cuisine
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='restaurant_cuisines'
    )
    cuisine = models.ForeignKey(
        Cuisine,
        on_delete=models.CASCADE,
        related_name='restaurant_cuisines'
    )
    is_primary = models.BooleanField('Primary Cuisine', default=False)
    
    class Meta:
        db_table = 'restaurant_cuisines'
        unique_together = ['restaurant', 'cuisine']
    
    def __str__(self):
        primary = ' (Primary)' if self.is_primary else ''
        return f"{self.restaurant.name} - {self.cuisine.name}{primary}"


class Product(BaseModel):
    """
    Restaurant Menu Items/Products
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    name = models.CharField('Product Name', max_length=200)
    name_en = models.CharField('Product Name (English)', max_length=200, blank=True)
    
    description = models.TextField('Description', max_length=1000, blank=True)
    description_en = models.TextField('Description (English)', max_length=1000, blank=True)
    
    price = models.DecimalField(
        'Price',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    image = models.ImageField('Product Image', upload_to='products/', null=True, blank=True)
    
    is_available = models.BooleanField('Available', default=True)
    is_featured = models.BooleanField('Featured', default=False)
    
    display_order = models.PositiveIntegerField('Display Order', default=0)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['restaurant', 'display_order', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class RestaurantView(TimestampedModel):
    """
    Track restaurant page views
    """
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_views'
    )
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    class Meta:
        db_table = 'restaurant_views'
        verbose_name = 'Restaurant View'
        verbose_name_plural = 'Restaurant Views'
        unique_together = ['restaurant', 'user']  # One view per user
    
    def __str__(self):
        user_info = self.user.email if self.user else self.ip_address
        return f"{self.restaurant.name} - {user_info}"
