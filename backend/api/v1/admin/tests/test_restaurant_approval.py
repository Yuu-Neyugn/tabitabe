"""
Restaurant approval API tests
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import time

from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant, RestaurantStatus


@pytest.mark.django_db
class TestRestaurantApprovalAPI:
    """Test restaurant approval endpoints"""
    
    def setup_method(self):
        """Setup test data"""
        self.admin = CustomUser.objects.create_superuser(
            email='admin@test.com',
            password='testpass123',
            user_type=0
        )
        
        self.owner = CustomUser.objects.create_user(
            email='owner@test.com',
            password='testpass123',
            user_type=0,
            first_name='Test',
            last_name='Owner'
        )
        
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            user=self.owner,
            status=RestaurantStatus.PENDING,
            phone_number='0312345678',
            email='restaurant@test.com',
            prefecture='東京都',
            city='渋谷区',
            address_line='道玄坂1-1-1',
            description='Test restaurant description',
            opening_time=time(9, 0),
            closing_time=time(22, 0),
            postal_code='150-0043'
        )
        
        self.client = APIClient()
    
    def test_list_restaurants_as_admin(self):
        """Admin can list all restaurants"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Restaurant'
    
    def test_list_restaurants_as_non_admin(self):
        """Non-admin cannot list restaurants"""
        self.client.force_authenticate(user=self.owner)
        url = reverse('api_v1:admin:admin-restaurants-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_pending_restaurants(self):
        """Admin can list pending restaurants"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-pending')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == RestaurantStatus.PENDING
    
    def test_approve_restaurant(self):
        """Admin can approve pending restaurant"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-approve', args=[self.restaurant.id])
        
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Restaurant approved successfully'
        
        self.restaurant.refresh_from_db()
        assert self.restaurant.status == RestaurantStatus.APPROVED
    
    def test_approve_already_approved_restaurant(self):
        """Cannot approve already approved restaurant"""
        self.restaurant.status = RestaurantStatus.APPROVED
        self.restaurant.save()
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-approve', args=[self.restaurant.id])
        
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only pending restaurants' in response.data['error']
    
    def test_reject_restaurant(self):
        """Admin can reject pending restaurant"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-reject', args=[self.restaurant.id])
        
        data = {
            'action': 'reject',
            'rejection_reason': '情報が不足しています'
        }
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Restaurant rejected successfully'
        
        self.restaurant.refresh_from_db()
        assert self.restaurant.status == RestaurantStatus.REJECTED
    
    def test_reject_without_reason(self):
        """Cannot reject without reason"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-reject', args=[self.restaurant.id])
        
        data = {'action': 'reject'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'rejection_reason' in response.data
    
    def test_filter_restaurants_by_status(self):
        """Admin can filter restaurants by status"""
        another_owner = CustomUser.objects.create_user(
            email='another@test.com',
            password='testpass123',
            user_type=0
        )
        
        Restaurant.objects.create(
            name='Approved Restaurant',
            user=another_owner,
            status=RestaurantStatus.APPROVED,
            phone_number='0387654321',
            email='approved@test.com',
            prefecture='大阪府',
            city='大阪市',
            address_line='梅田1-1-1',
            opening_time=time(10, 0),
            closing_time=time(23, 0),
            postal_code='530-0001'
        )
        
        self.client.force_authenticate(user=self.admin)
        url = reverse('api_v1:admin:admin-restaurants-list')
        
        response = self.client.get(url, {'status': RestaurantStatus.APPROVED})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Approved Restaurant'
