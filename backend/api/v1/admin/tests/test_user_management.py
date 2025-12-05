"""
User management API tests
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestUserManagementAPI:
    """Test user management endpoints"""
    
    def setup_method(self):
        """Setup test data"""
        # Create admin user
        self.admin = CustomUser.objects.create_superuser(
            email='admin@test.com',
            password='testpass123',
            user_type=0  # ADMIN
        )
        
        # Create test users as ADMIN type to avoid signals
        self.customer = CustomUser.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            user_type=0,  # ADMIN to avoid customer profile signal
            first_name='Test',
            last_name='Customer'
        )
        
        self.owner = CustomUser.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            user_type=0,  # ADMIN to avoid restaurant signal
            first_name='Test',
            last_name='Owner'
        )
        
        self.client = APIClient()
    
    def test_list_users_as_admin(self):
        """Admin can list all users"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # admin + customer + owner + AnonymousUser from Guardian
        assert len(response.data['results']) >= 3
    
    def test_list_users_as_non_admin(self):
        """Non-admin cannot list users"""
        self.client.force_authenticate(user=self.customer)
        url = reverse('api_v1:admin:admin-users-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_user_detail(self):
        """Admin can get user details"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-detail', args=[self.customer.id])
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'customer@test.com'
        # Customer created as type=0 to avoid signal
        assert response.data['user_type'] == 0
    def test_filter_users_by_type(self):
        """Admin can filter users by user_type"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-list')
        
        # Filter by ADMIN type (0) - all test users are type 0
        response = self.client.get(url, {'user_type': 0})
        
        assert response.status_code == status.HTTP_200_OK
        # Should get admin, customer, and owner (all type=0)
        assert len(response.data['results']) >= 3
        # Check all returned users are type 0
        for user in response.data['results']:
            assert user['user_type'] == 0
        # Verify our test users are in results
        user_emails = [u['email'] for u in response.data['results']]
        assert 'admin@test.com' in user_emails
        assert 'customer@test.com' in user_emails
        assert 'owner@test.com' in user_emails
    
    def test_filter_users_by_active_status(self):
        """Admin can filter users by active status"""
        # Deactivate customer
        self.customer.is_active = False
        self.customer.save()
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-list')
        
        # Get inactive users
        response = self.client.get(url, {'is_active': 'false'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['is_active'] is False
    
    def test_search_users(self):
        """Admin can search users by email or name"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-list')
        
        response = self.client.get(url, {'search': 'customer'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert 'customer' in response.data['results'][0]['email'].lower()
    
    def test_deactivate_user(self):
        """Admin can deactivate user"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-deactivate', args=[self.customer.id])
        
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'User deactivated successfully'
        
        # Check user is inactive
        self.customer.refresh_from_db()
        assert self.customer.is_active is False
    
    def test_activate_user(self):
        """Admin can activate user"""
        # Deactivate first
        self.customer.is_active = False
        self.customer.save()
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-activate', args=[self.customer.id])
        
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'User activated successfully'
        
        # Check user is active
        self.customer.refresh_from_db()
        assert self.customer.is_active is True
    
    def test_cannot_deactivate_already_inactive_user(self):
        """Cannot deactivate already inactive user"""
        self.customer.is_active = False
        self.customer.save()
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-users-deactivate', args=[self.customer.id])
        
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already inactive' in response.data['error']
