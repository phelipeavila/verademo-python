from django.test import TestCase, Client
from django.urls import reverse
from django.db.utils import DatabaseError
from unittest.mock import patch, Mock
from app.views.userController import login, showPasswordHint, processRegister
import hashlib

# Testing Login
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

            self.assertEqual(response.status_code, 200) 
            self.assertContains(response, 'Login failed')

    def testLogin(self):
        # Mock the successful login case
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (
                'testuser', hashlib.md5('testpass'.encode('utf-8')).hexdigest(),
                'hint', '2022-01-01', '2022-01-01', 'Real Name', 'Blab Name'
            )

            response = self.client.post(self.login_url, {
                'user': 'testuser',
                'password': 'testpass',
                'target': 'feed'
            })
            self.assertRedirects(response, 'feed')

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


class PasswordHintTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hint_url = reverse('passwordHint')

    def validUser(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ('passwordhint', 'hint')
            response = showPasswordHint(self.createRequest(username='testuser'))
            self.assertEqual(response.content.decode(), "Username 'testuser' has password: pa***wordhint")

    def invalidUser(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
            response = showPasswordHint(self.createRequest(username='invaliduser'))
            self.assertEqual(response.content.decode(), "No username provided, please type in your username first") 

    def noUsername(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
            response = showPasswordHint(self.createRequest(username=''))
            self.assertEqual(response.content.decode(), "No username provided, please type in your username first")

    def testDatabaseUser(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = DatabaseError('Database error')
            response = showPasswordHint(self.createRequest(username='testuser'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Database error')
    
    def testUnexpectedError(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = Exception('Unexpected error')
            response = showPasswordHint(self.createRequest(username='testuser'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Unexpected error')

    def createRequest(self, username):
        request = self.client.get(reverse('passwordHint'))
        if username is not None:
            request.GET['username'] = username
        return request
    
class ProcessRegisterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def testUniqueUsername(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = None
            response = processRegister(self.createRegisterRequest(username='newuser'))
            self.assertRedirects(response, 'register-finish')

    def testExistingUsername(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.return_value._enter_.return_value.fetchone.return_value = ('existinguser',)
            response = processRegister(self.createRegisterRequest(username='existinguser'))
            self.assertRedirects(response, 'register')
            self.assertIn('Username \'existinguser\' already exists!', response.context['error'])



            

