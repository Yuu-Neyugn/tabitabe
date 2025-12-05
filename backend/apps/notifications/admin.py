"""
Notification Admin Configuration
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import EmailTemplate, EmailLog, PushNotification, NotificationPreference


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
    
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'name',
                'template_type',
                'is_active'
            )
        }),
        ('Email Content', {
            'fields': (
                'subject',
                'html_body',
                'text_body'
            )
        }),
        ('Documentation', {
            'fields': ('variables_help',)
        })
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_email',
        'subject',
        'status_badge',
        'opened',
        'clicked',
        'sent_at',
        'created_at'
    ]
    
    list_filter = ['status', 'opened', 'clicked', 'created_at', 'sent_at']
    search_fields = ['recipient_email', 'subject']
    
    readonly_fields = [
        'recipient',
        'recipient_email',
        'template',
        'subject',
        'body',
        'status',
        'sent_at',
        'error_message',
        'opened',
        'opened_at',
        'clicked',
        'clicked_at',
        'created_at',
        'updated_at'
    ]
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'sent': 'green',
            'failed': 'red',
            'bounced': 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_email',
        'notification_type',
        'title',
        'sent',
        'read',
        'created_at'
    ]
    
    list_filter = ['notification_type', 'sent', 'read', 'created_at']
    search_fields = ['recipient__email', 'title', 'message']
    
    readonly_fields = [
        'recipient',
        'sent_at',
        'read_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient',)
        }),
        ('Content', {
            'fields': (
                'notification_type',
                'title',
                'message',
                'action_url',
                'data'
            )
        }),
        ('Status', {
            'fields': (
                'sent',
                'sent_at',
                'read',
                'read_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def recipient_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.recipient.id])
        return format_html('<a href="{}">{}</a>', url, obj.recipient.email)
    recipient_email.short_description = 'Recipient'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'email_reviews',
        'email_campaigns',
        'push_reviews',
        'push_campaigns'
    ]
    
    list_filter = [
        'email_reviews',
        'email_campaigns',
        'push_reviews',
        'push_campaigns'
    ]
    
    search_fields = ['user__email']
    
    def user_email(self, obj):
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
