from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    image2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image3 = models.ImageField(upload_to='products/', null=True, blank=True)
    video = models.FileField(upload_to='products/videos/', null=True, blank=True)
    
    # Set vs. Individual options
    has_set_option = models.BooleanField(default=False, help_text="Allow buying as a set")
    set_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price for the set option")
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    is_new = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:245]
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug[:240]}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        from django.db.models import Avg

        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] is not None else None

    @property
    def reviews_total(self):
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
        from orders.models import Order

        return Order.objects.filter(
            user=self.user,
            status__in=['confirmed', 'shipped', 'delivered'],
            items__product_id=self.product_id,
        ).exists()

    def __str__(self):
        return f'{self.user.username} - {self.product.name}: {self.rating} stars'


class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_questions',
    )
    asker_name = models.CharField(max_length=120)
    question = models.TextField()
    answer_text = models.TextField(blank=True)
    answered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_product_questions',
    )
    answered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_answered(self):
        return bool(self.answer_text.strip())

    def __str__(self):
        return f'Q by {self.asker_name} on {self.product.name}'
