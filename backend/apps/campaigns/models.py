"""
Campaign Models
Gift Cards and Stamp Rally campaigns for customer engagement
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from apps.core.models import BaseModel
from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant


# ===== GIFT CARD MODELS =====

class GiftCard(BaseModel):
    """
    Gift Card Templates created by admin
    """
    
    class GiftCardType(models.TextChoices):
        DISCOUNT_PERCENT = 'discount_percent', _('Discount Percentage')
        DISCOUNT_AMOUNT = 'discount_amount', _('Discount Amount')
        FREE_ITEM = 'free_item', _('Free Item')
    
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', max_length=1000)
    
    card_type = models.CharField(
        'Card Type',
        max_length=20,
        choices=GiftCardType.choices
    )
    
    # Discount values
    discount_percentage = models.DecimalField(
        'Discount Percentage',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    
    discount_amount = models.DecimalField(
        'Discount Amount',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Price
    price = models.DecimalField(
        'Price',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Validity
    valid_from = models.DateTimeField('Valid From')
    valid_until = models.DateTimeField('Valid Until')
    
    # Usage restrictions
    min_purchase_amount = models.DecimalField(
        'Minimum Purchase Amount',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    max_uses_per_customer = models.PositiveIntegerField(
        'Max Uses Per Customer',
        default=1
    )
    
    total_available = models.PositiveIntegerField(
        'Total Available',
        help_text='Total number of gift cards available for purchase'
    )
    
    # Applicable restaurants (empty = all restaurants)
    applicable_restaurants = models.ManyToManyField(
        Restaurant,
        blank=True,
        related_name='applicable_giftcards'
    )
    
    # Media
    image = models.ImageField('Card Image', upload_to='giftcards/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'giftcards'
        verbose_name = 'Gift Card'
        verbose_name_plural = 'Gift Cards'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_valid(self):
        """Check if gift card is currently valid"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
    
    @property
    def purchased_count(self):
        """Count how many have been purchased"""
        return self.my_giftcards.count()
    
    @property
    def remaining_count(self):
        """Calculate remaining available"""
        return max(0, self.total_available - self.purchased_count)


class MyGiftCard(BaseModel):
    """
    Customer-owned gift cards
    """
    
    class UsageStatus(models.TextChoices):
        UNUSED = 'unused', _('Unused')
        USED = 'used', _('Used')
        EXPIRED = 'expired', _('Expired')
    
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='my_giftcards'
    )
    
    giftcard = models.ForeignKey(
        GiftCard,
        on_delete=models.CASCADE,
        related_name='my_giftcards'
    )
    
    # Unique code for this customer's gift card
    code = models.CharField('Gift Card Code', max_length=20, unique=True, db_index=True)
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=UsageStatus.choices,
        default=UsageStatus.UNUSED
    )
    
    # Purchase info
    purchased_at = models.DateTimeField('Purchased At', auto_now_add=True)
    purchase_price = models.DecimalField(
        'Purchase Price',
        max_digits=10,
        decimal_places=2
    )
    
    # Usage info
    used_at = models.DateTimeField('Used At', null=True, blank=True)
    used_at_restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_giftcards'
    )
    
    # QR code for verification
    qr_code = models.ImageField('QR Code', upload_to='giftcards/qr/', null=True, blank=True)
    
    class Meta:
        db_table = 'my_giftcards'
        verbose_name = 'My Gift Card'
        verbose_name_plural = 'My Gift Cards'
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.customer.email} - {self.giftcard.title}"
    
    def use(self, restaurant):
        """Mark gift card as used"""
        if self.status == self.UsageStatus.UNUSED and self.is_valid():
            self.status = self.UsageStatus.USED
            self.used_at = timezone.now()
            self.used_at_restaurant = restaurant
            self.save()
            return True
        return False
    
    def is_valid(self):
        """Check if gift card is valid for use"""
        if self.status != self.UsageStatus.UNUSED:
            return False
        
        now = timezone.now()
        if not (self.giftcard.valid_from <= now <= self.giftcard.valid_until):
            self.status = self.UsageStatus.EXPIRED
            self.save()
            return False
        
        return True


# ===== STAMP RALLY MODELS =====

class Stamprally(BaseModel):
    """
    Stamp Rally Campaigns
    """
    
    class StamprallyStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', max_length=2000)
    
    # Duration
    start_date = models.DateTimeField('Start Date')
    end_date = models.DateTimeField('End Date')
    
    # Requirements
    required_stamps = models.PositiveIntegerField(
        'Required Stamps',
        validators=[MinValueValidator(2)]
    )
    
    # Prize
    prize_description = models.TextField('Prize Description', max_length=1000)
    prize_image = models.ImageField('Prize Image', upload_to='stampralley/prizes/', null=True, blank=True)
    
    # Campaign image
    banner_image = models.ImageField('Banner Image', upload_to='stampralley/banners/', null=True, blank=True)
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StamprallyStatus.choices,
        default=StamprallyStatus.DRAFT
    )
    
    # Max participants (null = unlimited)
    max_participants = models.PositiveIntegerField(
        'Max Participants',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'stampralley'
        verbose_name = 'Stamp Rally'
        verbose_name_plural = 'Stamp Rallies'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        """Check if stamp rally is currently active"""
        now = timezone.now()
        return (
            self.status == self.StamprallyStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )
    
    @property
    def participants_count(self):
        """Count total participants"""
        return self.participants.count()


class JoinShops(models.Model):
    """
    Participating restaurants in stamp rally
    """
    stamprally = models.ForeignKey(
        Stamprally,
        on_delete=models.CASCADE,
        related_name='join_shops'
    )
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='joined_stampralley'
    )
    
    display_order = models.PositiveIntegerField('Display Order', default=0)
    
    class Meta:
        db_table = 'stamprally_join_shops'
        unique_together = ['stamprally', 'restaurant']
        ordering = ['display_order', 'id']
    
    def __str__(self):
        return f"{self.stamprally.title} - {self.restaurant.name}"


class CustomerStamprally(models.Model):
    """
    Customer participation in stamp rally
    """
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='stamprally_participations'
    )
    
    stamprally = models.ForeignKey(
        Stamprally,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    
    joined_at = models.DateTimeField('Joined At', auto_now_add=True)
    
    completed = models.BooleanField('Completed', default=False)
    completed_at = models.DateTimeField('Completed At', null=True, blank=True)
    
    prize_received = models.BooleanField('Prize Received', default=False)
    prize_received_at = models.DateTimeField('Prize Received At', null=True, blank=True)
    
    class Meta:
        db_table = 'customer_stamprally'
        unique_together = ['customer', 'stamprally']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.customer.email} - {self.stamprally.title}"
    
    @property
    def stamps_collected(self):
        """Count collected stamps"""
        return self.stamps.count()
    
    def check_completion(self):
        """Check if customer has collected enough stamps"""
        if not self.completed and self.stamps_collected >= self.stamprally.required_stamps:
            self.completed = True
            self.completed_at = timezone.now()
            self.save()


class Stamped(models.Model):
    """
    Individual stamps collected by customers
    """
    customer_stamprally = models.ForeignKey(
        CustomerStamprally,
        on_delete=models.CASCADE,
        related_name='stamps'
    )
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='given_stamps'
    )
    
    stamped_at = models.DateTimeField('Stamped At', auto_now_add=True)
    
    # Verification
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_stamps'
    )
    
    class Meta:
        db_table = 'stamped'
        unique_together = ['customer_stamprally', 'restaurant']
        ordering = ['stamped_at']
    
    def __str__(self):
        return f"Stamp from {self.restaurant.name} for {self.customer_stamprally.customer.email}"


class WinPrize(BaseModel):
    """
    Prize winners record
    """
    customer_stamprally = models.OneToOneField(
        CustomerStamprally,
        on_delete=models.CASCADE,
        related_name='prize'
    )
    
    prize_description = models.TextField('Prize Description')
    
    awarded_at = models.DateTimeField('Awarded At', auto_now_add=True)
    
    delivered = models.BooleanField('Delivered', default=False)
    delivered_at = models.DateTimeField('Delivered At', null=True, blank=True)
    
    tracking_number = models.CharField('Tracking Number', max_length=100, blank=True)
    
    class Meta:
        db_table = 'win_prizes'
        verbose_name = 'Win Prize'
        verbose_name_plural = 'Win Prizes'
        ordering = ['-awarded_at']
    
    def __str__(self):
        return f"Prize for {self.customer_stamprally.customer.email}"
