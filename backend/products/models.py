from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.CharField(max_length=100)
    is_new = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] is not None else None

    @property
    def review_count(self):
        return self.reviews.count()


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_product_review'),
        ]
        ordering = ['-created_at']

    @property
    def is_verified_buyer(self):
        """Returns True if the user has purchased this product."""
        from orders.models import Order
        return Order.objects.filter(
            user=self.user,
            status__in=['confirmed', 'shipped', 'delivered'],
            items__product_id=self.product_id,
        ).exists()

    def __str__(self):
        return f'{self.user.username} — {self.product.name}: {self.rating}★'
