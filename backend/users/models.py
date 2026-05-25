from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from products.models import Product

PHONE_VALIDATOR = RegexValidator(
    regex=r'^\d{10}$',
    message='Enter a valid 10-digit phone number.',
)


class UserProfile(models.Model):
    """Extended profile for a registered user — saved shipping details."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(
        max_length=10,
        blank=True,
        validators=[PHONE_VALIDATOR],
        help_text='10-digit phone number',
    )
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    pincode = models.CharField(
        max_length=6,
        blank=True,
        validators=[RegexValidator(r'^\d{6}$', 'Enter a valid 6-digit pincode.')],
        help_text='6-digit Indian postal code',
    )

    def __str__(self):
        return f'Profile — {self.user.username}'


class WishlistItem(models.Model):
    """A product saved to a user's wishlist."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user.username} ♥ {self.product.name}'
