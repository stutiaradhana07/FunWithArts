from django.db import models


class Workshop(models.Model):
    class Category(models.TextChoices):
        PROGRAM = 'program', 'Professional Program'
        EXPERIENCE = 'experience', 'Studio Experience'

    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    total_slots = models.IntegerField()
    available_slots = models.IntegerField()
    image = models.ImageField(upload_to='workshops/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ── New fields for studio page rendering ──
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.EXPERIENCE,
        help_text='Determines which grid section the workshop appears in on the studio page.',
    )
    icon = models.CharField(
        max_length=2,
        blank=True,
        default='🏺',
        help_text='Single emoji displayed on the card and in the dropdown (e.g. 🌱, ✨, 🔥).',
    )
    schedule_text = models.CharField(
        max_length=100,
        blank=True,
        help_text='Human-friendly duration label shown on cards (e.g. "1 Month • 8 Classes", "2 Hours • For Two").',
    )
    is_highlighted = models.BooleanField(
        default=False,
        help_text='If true, the card gets the highlighted-card CSS class for extra visual emphasis.',
    )

    def __str__(self):
        return self.title

from django.contrib.auth.models import User

class Booking(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING   = 'pending',   'Awaiting Payment'
        CONFIRMED = 'confirmed', 'Payment Confirmed'
        FAILED    = 'failed',    'Payment Failed'
        CANCELLED = 'cancelled', 'Cancelled / Refunded'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    seats = models.IntegerField(default=1)

    # ── Payment tracking ──
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    razorpay_order_id = models.CharField(max_length=255, blank=True, default='')
    razorpay_payment_id = models.CharField(max_length=255, blank=True, default='')
    razorpay_signature = models.CharField(max_length=512, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Removed unique_together — users can retry failed payments.
        # Application-level check prevents duplicate CONFIRMED bookings.
        ordering = ['-booking_date']

    def __str__(self):
        return f"{self.user.username} - {self.workshop.title} ({self.get_payment_status_display()})"
