from django.db import models
from django.contrib.auth.models import User
from products.models import Product


class UserProfile(models.Model):
    """Extended profile for a registered user — saved shipping details."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    pincode = models.CharField(max_length=6, blank=True)

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
