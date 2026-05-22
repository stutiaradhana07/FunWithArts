from django.test import TestCase


class NewsletterAPITests(TestCase):
    def test_newsletter_subscribe_and_duplicate(self):
        payload = {'email': 'join@example.com'}
        first = self.client.post('/api/newsletter/subscribe/', payload, content_type='application/json')
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()['already_subscribed'], False)

        second = self.client.post('/api/newsletter/subscribe/', payload, content_type='application/json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()['already_subscribed'], True)
