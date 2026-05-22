from django.test import TestCase


class AccountsAPITests(TestCase):
    def test_register_login_and_me(self):
        register_payload = {
            'username': 'stuti',
            'email': 'stuti@example.com',
            'password': 'strongpass123',
        }
        reg_response = self.client.post('/api/auth/register/', register_payload, content_type='application/json')
        self.assertEqual(reg_response.status_code, 201)
        self.assertIn('token', reg_response.json())

        login_payload = {'username': 'stuti', 'password': 'strongpass123'}
        login_response = self.client.post('/api/auth/login/', login_payload, content_type='application/json')
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()['token']

        me_response = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()['username'], 'stuti')

    def test_logout_invalidates_token(self):
        # Register and get token
        self.client.post(
            '/api/auth/register/',
            {'username': 'logoutuser', 'email': 'lo@lo.com', 'password': 'pass1234!'},
            content_type='application/json',
        )
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'logoutuser', 'password': 'pass1234!'},
            content_type='application/json',
        )
        token = login_resp.json()['token']
        auth = {'HTTP_AUTHORIZATION': f'Token {token}'}

        # Logout
        logout_resp = self.client.post('/api/auth/logout/', **auth)
        self.assertEqual(logout_resp.status_code, 200)

        # Token should no longer work
        me_resp = self.client.get('/api/auth/me/', **auth)
        self.assertEqual(me_resp.status_code, 401)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'nobody', 'password': 'wrong'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
