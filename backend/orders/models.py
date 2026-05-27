from django.db import models, transaction
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from products.models import Product

PHONE_VALIDATOR = RegexValidator(
    regex=r'^\d{10}$',
    message='Enter a valid 10-digit phone number.',
)


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Card'
        UPI = 'upi', 'UPI'
        COD = 'cod', 'Cash on Delivery'

    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    # Link to authenticated user (optional — guests can also place orders)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    contact_email = models.EmailField(db_index=True)
    contact_phone = models.CharField(max_length=10, validators=[PHONE_VALIDATOR])
    shipping_first_name = models.CharField(max_length=120)
    shipping_last_name = models.CharField(max_length=120)
    shipping_address_line_1 = models.CharField(max_length=255)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=120)
    shipping_state = models.CharField(max_length=120)
    shipping_pincode = models.CharField(max_length=6)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.contact_email}'

    def save(self, *args, **kwargs):
        """Override to restore product stock when order is cancelled."""
        restoring = False
        if self.pk is not None:
            try:
                old = Order.objects.get(pk=self.pk)
                if old.status != self.OrderStatus.CANCELLED and self.status == self.OrderStatus.CANCELLED:
                    restoring = True
            except Order.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if restoring:
            with transaction.atomic():
                for item in self.items.all():
                    if item.product is not None:
                        item.product.stock += item.quantity
                        item.product.save(update_fields=['stock'])


class ShippingZone(models.Model):
    """Delivery zone with estimated transit times from the Delhi studio."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True)
    is_serviceable = models.BooleanField(default=True)
    min_delivery_days = models.PositiveSmallIntegerField(default=5)
    max_delivery_days = models.PositiveSmallIntegerField(default=8)
    region_digit = models.CharField(
        max_length=1,
        blank=True,
        help_text='Fallback when no prefix rule matches (India pincode first digit 1-9).',
    )
    is_default_region = models.BooleanField(
        default=False,
        help_text='Use as fallback for pincodes in this postal region.',
    )
    sort_order = models.IntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class PincodeRule(models.Model):
    """Maps a pincode prefix or full pincode to a shipping zone."""

    class RuleType(models.TextChoices):
        PREFIX = 'prefix', 'Prefix'
        EXACT = 'exact', 'Exact pincode'

    rule_type = models.CharField(max_length=10, choices=RuleType.choices)
    value = models.CharField(max_length=6, db_index=True)
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, related_name='rules')
    priority = models.PositiveSmallIntegerField(
        default=100,
        help_text='Lower number wins when multiple rules match.',
    )

    class Meta:
        ordering = ['priority', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['rule_type', 'value'],
                name='orders_pincode_rule_unique',
            ),
        ]

    def __str__(self):
        return f'{self.rule_type}:{self.value} → {self.zone.name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    purchase_option = models.CharField(
        max_length=20,
        default='individual',
        choices=[('individual', 'Individual'), ('set', 'Set')],
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'
