from django.test import TestCase, Client
from django.urls import reverse
from django.db.utils import DatabaseError
from unittest.mock import patch, Mock
from app.views.userController import login
from .models import User
import hashlib

# Testing UserController
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')

    def testDatabase(self):
        # Simulate a DatabaseError during login
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = DatabaseError('Database error')

            response = self.client.post(self.login_url, {
                'user': 'testuser',
                'password': 'testpass',
                'target': 'feed'
            })

            self.assertEqual(response.status_code, 200) 
            self.assertContains(response, 'Login failed') 

    def testGeneral(self):
        # Simulate a general exception during login
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = Exception('General error')

            response = self.client.post(self.login_url, {
                'user': 'testuser',
                'password': 'testpass',
                'target': 'feed'
            })

            self.assertEqual(response.status_code, 200)  # or the appropriate status code
            self.assertContains(response, 'Login failed')  # Customize based on your template

    def testLogin(self):
        # Mock the successful login case
        with patch('app.views.userController') as mock_cursor:
            # Simulate the database returning a valid user row
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                'testuser', hashlib.md5('testpass'.encode('utf-8')).hexdigest(),
                'hint', '2022-01-01', '2022-01-01', 'Real Name', 'Blab Name'
            )

            response = self.client.post(self.login_url, {
                'user': 'testuser',
                'password': 'testpass',
                'target': 'feed'
            })

            self.assertRedirects(response, '/feed')

    def testLoginInvalid(self):
        # Mock the case where no user is found
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None

            response = self.client.post(self.login_url, {
                'user': 'invaliduser',
                'password': 'invalidpass',
                'target': 'feed'
            })

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Login failed') 
