from django.db import models
from django.contrib.auth.models import User


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=255)
    title_is_bold = models.BooleanField(default=False)
    title_is_italic = models.BooleanField(default=False)
    title_font_size = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='CSS font size for the title, e.g. 32px or 2rem',
    )
    title_color = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='CSS color code or name for the title',
    )
    slug = models.SlugField(max_length=255, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_image = models.ImageField(upload_to='blogs/covers/')
    cover_image_position = models.CharField(
        max_length=30,
        blank=True,
        default='center center',
        help_text='CSS object-position for the cover image, e.g. "top center" or "50% 25%". Controls which part of the image is visible.',
    )
    excerpt = models.TextField(max_length=500)
    content = models.TextField(help_text='Rich HTML content is allowed. Use paragraphs to structure your story.')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
