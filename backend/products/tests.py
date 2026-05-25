from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from products.models import Category, Product, ProductQuestion


class ProductAPITests(TestCase):
    def setUp(self):
        self.decor = Category.objects.create(name='Decor', slug='decor')
        self.tableware = Category.objects.create(name='Tableware', slug='tableware')
        self.p1 = Product.objects.create(
            name='The Guardians',
            slug='the-guardians',
            description='Handmade decor',
            price=Decimal('7800.00'),
            stock=10,
            category=self.decor,
            is_available=True,
            is_new=True,
        )
        self.p2 = Product.objects.create(
            name='Artisan Bowl',
            slug='artisan-bowl',
            description='Textured bowl',
            price=Decimal('3200.00'),
            stock=5,
            category=self.tableware,
            is_available=True,
            is_new=False,
        )

    def test_product_list(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_product_detail(self):
        response = self.client.get(f'/api/products/{self.p1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.p1.id)
        self.assertTrue(response.json()['isNew'])

    def test_product_filter_by_category(self):
        response = self.client.get('/api/products/?category=Decor')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'The Guardians')

    def test_product_filter_category_case_insensitive(self):
        response = self.client.get('/api/products/?category=tableware')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_product_search(self):
        response = self.client.get('/api/products/?search=bowl')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Artisan Bowl')

    def test_product_filter_is_new(self):
        response = self.client.get('/api/products/?is_new=true')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'The Guardians')

    def test_category_list(self):
        response = self.client.get('/api/products/categories/')
        self.assertEqual(response.status_code, 200)
        categories = response.json()
        self.assertIn('Decor', categories)
        self.assertIn('Tableware', categories)
        self.assertEqual(len(categories), 2)

    def test_product_detail_404(self):
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, 404)


class ProductQuestionsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Decor', slug='decor')
        self.product = Product.objects.create(
            name='Wall Vase',
            slug='wall-vase',
            description='Clay wall vase',
            price=Decimal('2200.00'),
            stock=8,
            category=self.category,
            is_available=True,
        )
        self.staff = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='secret123',
            is_staff=True,
        )
        self.staff_token = Token.objects.create(user=self.staff)

    def test_anyone_can_post_product_question(self):
        response = self.client.post(
            f'/api/products/{self.product.id}/questions/',
            {
                'asker_name': 'Riya',
                'question': 'Is this suitable for fresh flowers?',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ProductQuestion.objects.count(), 1)
        self.assertEqual(ProductQuestion.objects.first().asker_name, 'Riya')

    def test_product_questions_list_returns_created_question(self):
        ProductQuestion.objects.create(
            product=self.product,
            asker_name='Aman',
            question='How heavy is it?',
        )
        response = self.client.get(f'/api/products/{self.product.id}/questions/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['asker_name'], 'Aman')
        self.assertEqual(data[0]['question'], 'How heavy is it?')

    def test_staff_can_answer_question(self):
        question = ProductQuestion.objects.create(
            product=self.product,
            asker_name='Aman',
            question='How heavy is it?',
        )
        response = self.client.patch(
            f'/api/products/{self.product.id}/questions/{question.id}/answer/',
            {'answer_text': 'It is light enough for wall hooks and comes ready to hang.'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {self.staff_token.key}',
        )
        self.assertEqual(response.status_code, 200)
        question.refresh_from_db()
        self.assertTrue(question.answer_text.startswith('It is light enough'))
        self.assertEqual(question.answered_by, self.staff)

    def test_non_staff_cannot_answer_question(self):
        user = User.objects.create_user(username='buyer', email='buyer@example.com', password='secret123')
        token = Token.objects.create(user=user)
        question = ProductQuestion.objects.create(
            product=self.product,
            asker_name='Aman',
            question='How heavy is it?',
        )
        response = self.client.patch(
            f'/api/products/{self.product.id}/questions/{question.id}/answer/',
            {'answer_text': 'Trying to answer'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_can_delete_question(self):
        question = ProductQuestion.objects.create(
            product=self.product,
            asker_name='Aman',
            question='How heavy is it?',
        )
        response = self.client.delete(
            f'/api/products/{self.product.id}/questions/{question.id}/answer/',
            HTTP_AUTHORIZATION=f'Token {self.staff_token.key}',
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProductQuestion.objects.filter(id=question.id).exists())

    def test_non_staff_cannot_delete_question(self):
        user = User.objects.create_user(username='buyer2', email='buyer2@example.com', password='secret123')
        token = Token.objects.create(user=user)
        question = ProductQuestion.objects.create(
            product=self.product,
            asker_name='Aman',
            question='How heavy is it?',
        )
        response = self.client.delete(
            f'/api/products/{self.product.id}/questions/{question.id}/answer/',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ProductQuestion.objects.filter(id=question.id).exists())
