from django.db import models, transaction
from django.contrib.auth.models import User
from products.models import Product


class Cart(models.Model):
    """
    Shopping cart tied to either an authenticated user or an anonymous session.
    A user should have at most one cart at a time; the merge logic enforces this.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart',
    )
    session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text='Anonymous session identifier for guest carts.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, session_id__isnull=True)
                    | models.Q(user__isnull=True, session_id__isnull=False)
                    | models.Q(user__isnull=True, session_id__isnull=True)
                ),
                name='cart_exclusive_owner',
            ),
        ]

    def __str__(self):
        if self.user_id:
            return f'Cart #{self.id} — {self.user.username}'
        return f'Guest Cart #{self.id} — {self.session_id}'

    @classmethod
    def get_or_create_for_request(cls, user, session_id):
        """
        Return the cart for an authenticated user (by user) or for a guest
        (by session_id).  Creates one if it doesn't exist.
        """
        if user and user.is_authenticated:
            cart, _ = cls.objects.get_or_create(user=user, defaults={'session_id': None})
            return cart

        if session_id:
            cart, _ = cls.objects.get_or_create(
                session_id=session_id,
                defaults={'user': None},
            )
            return cart

        return None

    @classmethod
    def merge_guest_into_user(cls, user, session_id):
        """
        Merge items from the guest cart (session_id) into the user's cart.
        - If the same product exists in both carts, quantities are summed.
        - The guest cart is deleted after merging.
        - Returns the user's merged cart.
        """
        if not user or not user.is_authenticated or not session_id:
            return cls.get_or_create_for_request(user, None)

        try:
            guest_cart = cls.objects.get(session_id=session_id, user__isnull=True)
        except cls.DoesNotExist:
            return cls.get_or_create_for_request(user, None)

        user_cart, _ = cls.objects.get_or_create(user=user, defaults={'session_id': None})

        with transaction.atomic():
            for guest_item in guest_cart.items.select_related('product').all():
                if guest_item.product is None or not guest_item.product.is_available:
                    guest_item.delete()
                    continue

                try:
                    existing = user_cart.items.get(product=guest_item.product)
                    existing.quantity += guest_item.quantity
                    existing.save(update_fields=['quantity'])
                    guest_item.delete()
                except CartItem.DoesNotExist:
                    # Reassign the item to the user's cart
                    guest_item.cart = user_cart
                    guest_item.save(update_fields=['cart'])

            guest_cart.delete()

        return user_cart


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['added_at']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'