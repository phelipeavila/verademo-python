from django.test import TestCase, Client
from django.urls import reverse
from django.db import connection
from django.db.utils import DatabaseError
from django.http import HttpResponse
from unittest.mock import patch, Mock
from app.views.userController import login, showPasswordHint, processRegister, processRegisterFinish
import hashlib
import logging


logger = logging.getLogger("VeraDemo:Tests")

# Testing Login
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.register_url = reverse('registerFinish')
        self.client.post(self.register_url, {
            'username': 'clyde',
            'password': 'clyde',
            'cpassword': 'clyde',
            'realName': 'clyde',
            'blabName': 'clyde',
        })

    def testDatabase(self):
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
        response = self.client.post(self.login_url, {
            'user': 'clyde',
            'password': 'clyde',
            'target': 'feed'
        }, HTTP_USER_AGENT='UA=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0 U=clyde')
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
        self.client.post(self.register_url, {
            'username': 'clyde',
            'password': 'clyde',
            'cpassword': 'clyde',
            'realName': 'clyde',
            'blabName': 'clyde',
        })

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

    def testNoUsername(self):
        response = processRegister(self.createRegisterRequest(username=''))
        self.assertIsInstance(response, str)
        self.assertEqual(response, "No username provided, please type in your username first")

    def testDatabase(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = DatabaseError('Database error')
            response = processRegister(self.createRegisterRequest(username='newuser'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Database error')
            self.assertRedirects(response, 'register')
            self.assertRedirects(response, 'register-finish')

    def testUnexpectedError(self):
        with patch('app.views.userController') as mock_cursor:
            mock_cursor.side_effect = Exception('Unexpected error')
            response = processRegister(self.createRegisterRequest(username='newuser'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Unexpected error')
            self.assertRedirects(response, 'register')
            self.assertRedirects(response, 'register-finish')

    def createRegisterRequest(self, username):
        return self.client.post(reverse('register'), {'username': username})
    
        
class ProcessRegisterFinishTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.register_url = reverse('register')
       # self.logger = logging.getLogger('django')
        self.client.post(self.register_url, {
            'username': 'newuser',
            'password': 'newuser',
            'cpassword': 'newuser',
            'realName': 'newuser',
            'blabName': 'newuser',
        })
    # TEST FAILS 302 != 200
    def testValidRegistration(self):
        response = self.client.get(self.register_url, {
            'user': 'newuser',
            'password': 'newuser',
            'cpassword': 'newuser',
            'realName': 'newuser',
            'blabName': 'newuser',
            'target': 'feed'
        },HTTP_USER_AGENT='UA=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0 U=newuser')

        response = self.client.post(self.register_url)
        self.assertRedirects(response, '/feed')

        # self.assertRedirects(response, '/login')

        
    # TEST FAILS 302 != 200
    def testInvalidRegistration(self):
        data = {
            'username': 'testuser',
            'password': '123',
            'cpassword': '123',
           'realName': 'Test User',
            'blabName': 'testblab'
        }
        response = self.client.post(self.register_finish_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, 'login')

        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', [data['username']])
            result = cursor.fetchone()
            self.assertIsNone(result)
    
    def testPasswordsDontMatch(self):
        data = {
            'username': 'testuser',
            'password': '123',
            'cpassword': '321',
           'realName': 'Test User',
            'blabName': 'testblab'
        }
        response = self.client.post(self.register_finish_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, 'login')
        self.assertIn('The password and Confirm Password values do not match. Please try again.', response.context['request'].error)
    
    def testDatabase(self):
        data = {
            'username': 'testuser',
            'password': '123',
            'cpassword': '123',
            'realName': 'Test User',
            'blabName': 'testblab'
        }

        connection.close()

        response = self.client.post(self.register_finish_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,'register-finish.html')

        with self.assertLogs(self.logger, level='ERROR') as cm:
            self.assertIn('Database error', cm.output[0])

    def testValue(self):
        data = {
            'username': 'testuser',
            'password': '123',
            'cpassword': '123',
           'realName': 'Test User',
            'blabName': 'testblab'
        }

        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = ValueError('Integrity error')
            response = self.client.post(self.register_finish_url, data)

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response,'app/register-finish.html')
            self.assertIn('Invalid Data', response.context['request'].error)

    def testSQLite(self):
        data = {
            'username': 'testuser',
            'password': '123',
            'cpassword': '123',
           'realName': 'Test User',
            'blabName': 'testblab'
        }

        connection.close()

        response = self.client.post(self.register_finish_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response,'app/register-finish.html')

        with self.assertLogs(self.logger, level='ERROR') as cm:
            self.assertIn('Database error', cm.output[0])
        
    



            


    
    



    



            

