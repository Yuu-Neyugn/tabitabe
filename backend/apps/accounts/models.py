"""
Custom User Model with OIDC Integration
Supports 3 user types: Customer, Restaurant, Admin
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', UserType.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class UserType(models.IntegerChoices):
    """User type choices"""
    CUSTOMER = 1, 'Customer'
    RESTAURANT = 2, 'Restaurant'
    ADMIN = 3, 'Admin'


class CustomUser(AbstractUser):
    """
    Custom User Model
    - Email-based authentication (no username)
    - Integrates with Keycloak OIDC
    - Supports multiple user types
    """
    
    # Remove username field
    username = None
    
    # Primary identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Email Address', unique=True, db_index=True)
    
    # User type
    user_type = models.IntegerField(
        'User Type',
        choices=UserType.choices,
        default=UserType.CUSTOMER,
        db_index=True
    )
    
    # OIDC fields
    oidc_subject = models.CharField(
        'OIDC Subject (sub)',
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text='Keycloak user ID'
    )
    
    # Timestamps
    password_changed_at = models.DateTimeField(
        'Password Changed At',
        null=True,
        blank=True
    )
    
    # Metadata
    is_email_verified = models.BooleanField('Email Verified', default=False)
    last_login_ip = models.GenericIPAddressField('Last Login IP', null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['oidc_subject']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def is_customer(self):
        """Check if user is a customer"""
        return self.user_type == UserType.CUSTOMER
    
    @property
    def is_restaurant(self):
        """Check if user is a restaurant"""
        return self.user_type == UserType.RESTAURANT
    
    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.user_type == UserType.ADMIN
    
    def get_full_name(self):
        """Return full name or email"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def get_short_name(self):
        """Return short name"""
        return self.first_name or self.email.split('@')[0]


def generate_customer_number():
    """Generate unique 12-digit customer number"""
    import random
    return f"{random.randint(100000000000, 999999999999)}"


class CustomerProfile(models.Model):
    """
    Customer Profile - Extended information for customer users
    One-to-One with CustomUser
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        primary_key=True
    )
    
    customer_number = models.CharField(
        'Customer Number',
        max_length=12,
        unique=True,
        default=generate_customer_number,
        db_index=True
    )
    
    # Personal Information
    phone_number = PhoneNumberField(
        'Phone Number',
        unique=True,
        region='JP',
        help_text='Japanese phone number format'
    )
    
    birth_date = models.DateField(
        'Birth Date',
        null=True,
        blank=True
    )
    
    # Address
    postal_code = models.CharField(
        'Postal Code',
        max_length=8,
        validators=[
            RegexValidator(
                regex=r'^\d{3}-?\d{4}$',
                message='Enter a valid postal code (e.g., 123-4567)'
            )
        ],
        null=True,
        blank=True
    )
    
    prefecture = models.CharField(
        'Prefecture',
        max_length=20,
        null=True,
        blank=True
    )
    
    city = models.CharField(
        'City',
        max_length=100,
        null=True,
        blank=True
    )
    
    address_line = models.CharField(
        'Address Line',
        max_length=200,
        null=True,
        blank=True
    )
    
    # Profile
    avatar = models.ImageField(
        'Avatar',
        upload_to='avatars/customers/',
        null=True,
        blank=True
    )
    
    bio = models.TextField(
        'Bio',
        max_length=500,
        null=True,
        blank=True
    )
    
    # Preferences
    language = models.CharField(
        'Preferred Language',
        max_length=5,
        choices=[('ja', 'Japanese'), ('en', 'English')],
        default='ja'
    )
    
    receive_newsletter = models.BooleanField(
        'Receive Newsletter',
        default=True
    )
    
    receive_push_notifications = models.BooleanField(
        'Receive Push Notifications',
        default=True
    )
    
    # Status
    is_active = models.BooleanField(
        'Active',
        default=True,
        help_text='Account active status'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    
    class Meta:
        db_table = 'customer_profiles'
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_number']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return f"{self.user.email} ({self.customer_number})"
    
    @property
    def full_address(self):
        """Return full formatted address"""
        parts = [
            self.postal_code,
            self.prefecture,
            self.city,
            self.address_line
        ]
        return ' '.join(filter(None, parts))
    
    def deactivate(self):
        """Deactivate customer account"""
        self.is_active = False
        self.user.is_active = False
        self.save()
        self.user.save()
    
    def activate(self):
        """Activate customer account"""
        self.is_active = True
        self.user.is_active = True
        self.save()
        self.user.save()
