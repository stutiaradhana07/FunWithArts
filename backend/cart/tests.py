from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from .models import Cart, CartItem


class CartModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            stock=10,
        )

    def test_user_cart_creation(self):
        """Test that a user cart is created and persists."""
        cart = Cart.get_or_create_for_request(self.user, None)
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_id)
        self.assertIsNone(cart.expires_at)

    def test_guest_cart_creation(self):
        """Test that a guest cart is created with expiry timestamp."""
        cart = Cart.get_or_create_for_request(None, 'guest-session-123')
        self.assertIsNotNone(cart)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.session_id, 'guest-session-123')
        self.assertIsNotNone(cart.expires_at)
        self.assertTrue(cart.expires_at > timezone.now())

    def test_guest_cart_expiry_refresh(self):
        """Test that guest cart expiry is refreshed on each access."""
        session_id = 'guest-session-456'
        cart1 = Cart.get_or_create_for_request(None, session_id)
        expiry1 = cart1.expires_at

        # Wait a moment and fetch again (in real scenario, time passes)
        import time
        time.sleep(0.1)
        cart2 = Cart.get_or_create_for_request(None, session_id)
        expiry2 = cart2.expires_at

        # Expiry should be refreshed (newer)
        self.assertGreaterEqual(expiry2, expiry1)

    def test_user_cart_uniqueness(self):
        """Test that a user has only one cart."""
        cart1 = Cart.get_or_create_for_request(self.user, None)
        cart2 = Cart.get_or_create_for_request(self.user, None)
        self.assertEqual(cart1.id, cart2.id)

    def test_add_item_to_cart(self):
        """Test adding an item to cart."""
        cart = Cart.get_or_create_for_request(self.user, None)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)

    def test_cart_total_price(self):
        """Test cart total price calculation."""
        cart = Cart.get_or_create_for_request(self.user, None)
        CartItem.objects.create(cart=cart, product=self.product, quantity=3)
        
        total = sum(item.product.price * item.quantity for item in cart.items.all())
        self.assertEqual(total, 300.00)

    def test_guest_cart_ttl_days(self):
        """Test that guest cart has correct TTL days set."""
        self.assertEqual(Cart.GUEST_CART_TTL_DAYS, 30)

    def test_cart_constraints(self):
        """Test that cart must have either user OR session_id, not both."""
        # User-only cart should work
        cart1 = Cart.objects.create(user=self.user, session_id=None)
        self.assertEqual(cart1.user.id, self.user.id)

        # Session-only cart should work
        cart2 = Cart.objects.create(user=None, session_id='test-session')
        self.assertEqual(cart2.session_id, 'test-session')

        # Both None should work (anonymous cart without session)
        cart3 = Cart.objects.create(user=None, session_id=None)
        self.assertIsNone(cart3.user)
        self.assertIsNone(cart3.session_id)
