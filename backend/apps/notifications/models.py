"""
Notification Models
Email and push notifications system
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, TimestampedModel
from apps.accounts.models import CustomUser


class EmailTemplate(BaseModel):
    """
    Email templates for different notification types
    """
    
    class TemplateType(models.TextChoices):
        WELCOME = 'welcome', _('Welcome Email')
        RESTAURANT_APPROVED = 'restaurant_approved', _('Restaurant Approved')
        RESTAURANT_REJECTED = 'restaurant_rejected', _('Restaurant Rejected')
        REVIEW_MODERATED = 'review_moderated', _('Review Moderated')
        GIFTCARD_PURCHASED = 'giftcard_purchased', _('Gift Card Purchased')
        STAMPRALLY_COMPLETED = 'stamprally_completed', _('Stamp Rally Completed')
        PRIZE_WON = 'prize_won', _('Prize Won')
        NEWSLETTER = 'newsletter', _('Newsletter')
    
    name = models.CharField('Template Name', max_length=100, unique=True)
    template_type = models.CharField(
        'Template Type',
        max_length=30,
        choices=TemplateType.choices,
        unique=True
    )
    
    subject = models.CharField('Email Subject', max_length=200)
    
    # Email body (HTML)
    html_body = models.TextField('HTML Body')
    
    # Plain text fallback
    text_body = models.TextField('Text Body', blank=True)
    
    # Template variables documentation
    variables_help = models.TextField(
        'Available Variables',
        help_text='Document template variables like {{user_name}}, {{restaurant_name}}',
        blank=True
    )
    
    is_active = models.BooleanField('Active', default=True)
    
    class Meta:
        db_table = 'email_templates'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['template_type']
    
    def __str__(self):
        return self.name


class EmailLog(TimestampedModel):
    """
    Log of all sent emails
    """
    
    class EmailStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SENT = 'sent', _('Sent')
        FAILED = 'failed', _('Failed')
        BOUNCED = 'bounced', _('Bounced')
    
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_emails'
    )
    
    recipient_email = models.EmailField('Recipient Email')
    
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    
    subject = models.CharField('Subject', max_length=200)
    body = models.TextField('Body')
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        db_index=True
    )
    
    sent_at = models.DateTimeField('Sent At', null=True, blank=True)
    
    error_message = models.TextField('Error Message', blank=True)
    
    # Tracking
    opened = models.BooleanField('Opened', default=False)
    opened_at = models.DateTimeField('Opened At', null=True, blank=True)
    
    clicked = models.BooleanField('Clicked', default=False)
    clicked_at = models.DateTimeField('Clicked At', null=True, blank=True)
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.recipient_email} - {self.subject}"


class PushNotification(BaseModel):
    """
    Push notifications for mobile apps
    """
    
    class NotificationType(models.TextChoices):
        GENERAL = 'general', _('General')
        REVIEW_REPLY = 'review_reply', _('Review Reply')
        STAMPRALLY = 'stamprally', _('Stamp Rally')
        GIFTCARD = 'giftcard', _('Gift Card')
        PROMOTION = 'promotion', _('Promotion')
    
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='push_notifications'
    )
    
    notification_type = models.CharField(
        'Type',
        max_length=20,
        choices=NotificationType.choices
    )
    
    title = models.CharField('Title', max_length=100)
    message = models.TextField('Message', max_length=500)
    
    # Deep link for navigation
    action_url = models.CharField('Action URL', max_length=500, blank=True)
    
    # Metadata
    data = models.JSONField('Additional Data', default=dict, blank=True)
    
    # Status
    sent = models.BooleanField('Sent', default=False)
    sent_at = models.DateTimeField('Sent At', null=True, blank=True)
    
    read = models.BooleanField('Read', default=False)
    read_at = models.DateTimeField('Read At', null=True, blank=True)
    
    class Meta:
        db_table = 'push_notifications'
        verbose_name = 'Push Notification'
        verbose_name_plural = 'Push Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.read:
            from django.utils import timezone
            self.read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """
    User notification preferences
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_reviews = models.BooleanField('Email - Reviews', default=True)
    email_campaigns = models.BooleanField('Email - Campaigns', default=True)
    email_system = models.BooleanField('Email - System', default=True)
    
    # Push notifications
    push_reviews = models.BooleanField('Push - Reviews', default=True)
    push_campaigns = models.BooleanField('Push - Campaigns', default=True)
    push_system = models.BooleanField('Push - System', default=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
