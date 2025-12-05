"""
Restaurant notification tasks
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from apps.restaurants.models import Restaurant
from apps.notifications.models import EmailTemplate, EmailLog


@shared_task(bind=True, max_retries=3)
def send_restaurant_approval_email(self, restaurant_id):
    """
    Send restaurant approval email
    
    Args:
        restaurant_id: Restaurant ID
    """
    try:
        restaurant = Restaurant.objects.select_related('user').get(id=restaurant_id)
        
        # Get email template
        try:
            template = EmailTemplate.objects.get(
                template_type=1,  # RESTAURANT_APPROVAL
                is_active=True
            )
            subject = template.subject
            html_content = template.html_content.format(
                restaurant_name=restaurant.name,
                owner_name=f"{restaurant.user.first_name} {restaurant.user.last_name}".strip() or restaurant.user.email
            )
        except EmailTemplate.DoesNotExist:
            # Default template if not found
            subject = f"【Tabitabe】レストラン「{restaurant.name}」が承認されました"
            html_content = render_to_string('emails/restaurant_approval.html', {
                'restaurant': restaurant,
                'owner': restaurant.user,
            })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[restaurant.user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Log email
        EmailLog.objects.create(
            recipient_email=restaurant.user.email,
            subject=subject,
            template=template if 'template' in locals() else None,
            status=1,  # SENT
            sent_at=None  # Will be auto-set by model
        )
        
        return f"Approval email sent to {restaurant.user.email}"
    
    except Restaurant.DoesNotExist:
        return f"Restaurant {restaurant_id} not found"
    
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_restaurant_rejection_email(self, restaurant_id, rejection_reason):
    """
    Send restaurant rejection email
    
    Args:
        restaurant_id: Restaurant ID
        rejection_reason: Reason for rejection
    """
    try:
        restaurant = Restaurant.objects.select_related('user').get(id=restaurant_id)
        
        # Get email template
        try:
            template = EmailTemplate.objects.get(
                template_type=2,  # RESTAURANT_REJECTION
                is_active=True
            )
            subject = template.subject
            html_content = template.html_content.format(
                restaurant_name=restaurant.name,
                owner_name=f"{restaurant.user.first_name} {restaurant.user.last_name}".strip() or restaurant.user.email,
                rejection_reason=rejection_reason
            )
        except EmailTemplate.DoesNotExist:
            # Default template if not found
            subject = f"【Tabitabe】レストラン「{restaurant.name}」の審査結果について"
            html_content = render_to_string('emails/restaurant_rejection.html', {
                'restaurant': restaurant,
                'owner': restaurant.user,
                'rejection_reason': rejection_reason,
            })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[restaurant.user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Log email
        EmailLog.objects.create(
            recipient_email=restaurant.user.email,
            subject=subject,
            template=template if 'template' in locals() else None,
            status=1,  # SENT
            sent_at=None
        )
        
        return f"Rejection email sent to {restaurant.user.email}"
    
    except Restaurant.DoesNotExist:
        return f"Restaurant {restaurant_id} not found"
    
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def send_restaurant_created_notification(self, restaurant_id):
    """
    Send notification to admin when new restaurant is created
    
    Args:
        restaurant_id: Restaurant ID
    """
    try:
        restaurant = Restaurant.objects.select_related('user').get(id=restaurant_id)
        
        subject = f"【Tabitabe Admin】新しいレストランが登録されました: {restaurant.name}"
        html_content = render_to_string('emails/admin_new_restaurant.html', {
            'restaurant': restaurant,
            'owner': restaurant.user,
            'admin_url': f"{settings.FRONTEND_URL}/admin/restaurants/{restaurant.id}"
        })
        
        text_content = strip_tags(html_content)
        
        # Send to admin emails
        admin_emails = settings.ADMIN_NOTIFICATION_EMAILS
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_content,
            fail_silently=False,
        )
        
        # Log emails
        for email in admin_emails:
            EmailLog.objects.create(
                recipient_email=email,
                subject=subject,
                status=1,  # SENT
            )
        
        return f"Admin notification sent for restaurant {restaurant.name}"
    
    except Restaurant.DoesNotExist:
        return f"Restaurant {restaurant_id} not found"
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
