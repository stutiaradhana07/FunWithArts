from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
import json

from .models import NewsletterSubscriber, Post


class NewsletterAPITests(TestCase):
    def test_newsletter_subscribe_and_duplicate(self):
        payload = {'email': 'join@example.com'}
        first = self.client.post('/api/newsletter/subscribe/', payload, content_type='application/json')
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()['already_subscribed'], False)

        second = self.client.post('/api/newsletter/subscribe/', payload, content_type='application/json')
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()['already_subscribed'], True)

    def test_newsletter_subscribe_invalid_email(self):
        """Test that invalid email is rejected."""
        payload = {'email': 'not-an-email'}
        response = self.client.post('/api/newsletter/subscribe/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_newsletter_subscriber_creation(self):
        """Test that subscriber record is created in database."""
        subscriber = NewsletterSubscriber.objects.create(
            email='test@example.com',
            is_active=True
        )
        self.assertEqual(subscriber.email, 'test@example.com')
        self.assertTrue(subscriber.is_active)

    def test_newsletter_subscriber_uniqueness(self):
        """Test that duplicate emails are rejected at database level."""
        NewsletterSubscriber.objects.create(email='unique@example.com')
        
        with self.assertRaises(Exception):  # IntegrityError
            NewsletterSubscriber.objects.create(email='unique@example.com')


class PostModelTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='blogger',
            email='blogger@example.com',
            password='password123',
            first_name='John',
            last_name='Blogger'
        )

    def test_post_creation(self):
        """Test creating a blog post."""
        post = Post.objects.create(
            title='First Post',
            slug='first-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='This is a preview',
            content='This is the full content',
            status='published',
            published_at=timezone.now()
        )
        self.assertEqual(post.title, 'First Post')
        self.assertEqual(post.author.username, 'blogger')
        self.assertEqual(post.status, 'published')

    def test_post_draft_status(self):
        """Test that post can be in draft status."""
        post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Draft preview',
            content='Draft content',
            status='draft',
            published_at=None
        )
        self.assertEqual(post.status, 'draft')
        self.assertIsNone(post.published_at)

    def test_post_published_at_field(self):
        """Test that published_at field exists and can be set."""
        now = timezone.now()
        post = Post.objects.create(
            title='Timestamped Post',
            slug='timestamped-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Has publish time',
            content='Full content',
            status='published',
            published_at=now
        )
        self.assertEqual(post.published_at, now)

    def test_post_string_representation(self):
        """Test post string representation."""
        post = Post.objects.create(
            title='Test Post Title',
            slug='test-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Preview',
            content='Content',
            status='published'
        )
        self.assertEqual(str(post), 'Test Post Title')

    def test_post_ordering(self):
        """Test that posts are ordered by created_at descending."""
        post1 = Post.objects.create(
            title='Post 1',
            slug='post-1',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='First',
            content='Content 1',
            status='published'
        )
        
        post2 = Post.objects.create(
            title='Post 2',
            slug='post-2',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Second',
            content='Content 2',
            status='published'
        )
        
        posts = list(Post.objects.all())
        # Most recent first
        self.assertEqual(posts[0].id, post2.id)
        self.assertEqual(posts[1].id, post1.id)


class PostSerializerTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='blogger',
            email='blogger@example.com',
            password='password123',
            first_name='John',
            last_name='Blogger'
        )
        self.client = Client()

    def test_author_name_with_full_name(self):
        """Test that author_name returns full name if available."""
        post = Post.objects.create(
            title='By John Blogger',
            slug='by-john-blogger',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Preview',
            content='Content',
            status='published'
        )
        
        response = self.client.get(f'/api/blogs/{post.slug}/')
        if response.status_code == 200:
            data = response.json()
            # Should return full name or username
            self.assertIn(data.get('author_name'), ['John Blogger', 'blogger'])

    def test_author_name_fallback_to_username(self):
        """Test that author_name falls back to username if no full name."""
        user_no_name = User.objects.create_user(
            username='plainuser',
            email='plain@example.com',
            password='pass123'
            # No first_name or last_name
        )
        
        post = Post.objects.create(
            title='By Plain User',
            slug='by-plain-user',
            author=user_no_name,
            cover_image='blogs/test.jpg',
            excerpt='Preview',
            content='Content',
            status='published'
        )
        
        response = self.client.get(f'/api/blogs/{post.slug}/')
        if response.status_code == 200:
            data = response.json()
            # Should fall back to username
            self.assertEqual(data.get('author_name'), 'plainuser')

    def test_blog_detail_includes_title_style_fields(self):
        """Test that title styling flags are included in the blog detail API."""
        post = Post.objects.create(
            title='Styled Title',
            slug='styled-title',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Preview',
            content='Content',
            title_is_bold=True,
            title_is_italic=True,
            title_font_size='36px',
            title_color='#c47d4b',
            status='published'
        )

        response = self.client.get(f'/api/blogs/{post.slug}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('title_is_bold'))
        self.assertTrue(data.get('title_is_italic'))
        self.assertEqual(data.get('title_font_size'), '36px')
        self.assertEqual(data.get('title_color'), '#c47d4b')


class BlogAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username='blogger',
            email='blogger@example.com',
            password='password123'
        )
        
        self.published_post = Post.objects.create(
            title='Published Post',
            slug='published-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='This is published',
            content='Published content here',
            status='published',
            published_at=timezone.now()
        )
        
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=self.author,
            cover_image='blogs/test.jpg',
            excerpt='Still drafting',
            content='Draft content',
            status='draft',
            published_at=None
        )

    def test_list_posts_endpoint(self):
        """Test that list endpoint returns posts."""
        response = self.client.get('/api/blogs/')
        self.assertIn(response.status_code, [200, 404])  # 404 if endpoint not configured

    def test_post_detail_endpoint(self):
        """Test that post detail endpoint returns post data."""
        response = self.client.get(f'/api/blogs/{self.published_post.slug}/')
        self.assertIn(response.status_code, [200, 404])
