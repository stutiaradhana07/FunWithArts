from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from django.core.validators import RegexValidator
from products.models import Product
from .delivery import lookup_pincode
from .models import Order, OrderItem, ExchangeRequest

PHONE_VALIDATOR = RegexValidator(
    regex=r'^\d{10}$',
    message='Enter a valid 10-digit phone number.',
)


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    purchase_option = serializers.ChoiceField(choices=['individual', 'set'], default='individual')


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'purchase_option',
            'unit_price',
            'quantity',
            'line_total',
        ]


class GuestOrderLookupSerializer(serializers.Serializer):
    contact_email = serializers.EmailField()
    order_id = serializers.IntegerField()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'contact_email',
            'contact_phone',
            'shipping_first_name',
            'shipping_last_name',
            'shipping_address_line_1',
            'shipping_address_line_2',
            'shipping_city',
            'shipping_state',
            'shipping_pincode',
            'payment_method',
            'subtotal',
            'shipping_fee',
            'total_amount',
            'status',
            'created_at',
            'items',
        ]


class OrderCreateSerializer(serializers.Serializer):
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=10, validators=[PHONE_VALIDATOR])
    shipping_first_name = serializers.CharField(max_length=120)
    shipping_last_name = serializers.CharField(max_length=120)
    shipping_address_line_1 = serializers.CharField(max_length=255)
    shipping_address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    shipping_city = serializers.CharField(max_length=120)
    shipping_state = serializers.CharField(max_length=120)
    shipping_pincode = serializers.RegexField(r'^\d{6}$')
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    items = OrderItemCreateSerializer(many=True, allow_empty=False)

    def validate_shipping_pincode(self, value):
        delivery = lookup_pincode(value)
        if not delivery.is_serviceable:
            raise serializers.ValidationError(delivery.message)
        return value

    def create(self, validated_data):
        item_payloads = validated_data.pop('items')
        shipping_address_line_2 = validated_data.pop('shipping_address_line_2', '')
        # user is passed via save(user=...) from the view
        user = validated_data.pop('user', None)

        product_ids = [item['product_id'] for item in item_payloads]

        with transaction.atomic():
            products = list(
                Product.objects.select_for_update()
                .filter(id__in=product_ids, is_available=True)
                .order_by('id')
            )
            product_map = {product.id: product for product in products}

            subtotal = Decimal('0.00')
            order_items = []

            for item in item_payloads:
                product = product_map.get(item['product_id'])
                if product is None:
                    raise serializers.ValidationError(
                        {'items': [f"Product {item['product_id']} is invalid or unavailable."]}
                    )

                qty = item['quantity']
                if product.stock < qty:
                    raise serializers.ValidationError(
                        {'items': [f"Only {product.stock} units available for '{product.name}'."]}
                    )

                purchase_option = item.get('purchase_option', 'individual')
                if purchase_option == 'set':
                    if not product.has_set_option:
                        raise serializers.ValidationError(
                            {'items': [f"Product '{product.name}' does not have a set buying option."]}
                        )
                    unit_price = product.set_price if product.set_price is not None else product.price
                    product_name = f"{product.name} (Set)"
                else:
                    unit_price = product.price
                    product_name = product.name

                line_total = unit_price * qty
                subtotal += line_total
                order_items.append((product, qty, line_total, unit_price, product_name, purchase_option))

            shipping_fee = Decimal('99.00')
            total_amount = subtotal + shipping_fee

            # Set initial order status based on payment method
            payment_method = validated_data.get('payment_method')
            if payment_method == 'cod':
                initial_status = Order.OrderStatus.CONFIRMED
            else:
                initial_status = Order.OrderStatus.PENDING
            
            order = Order.objects.create(
                **validated_data,
                user=user,
                shipping_address_line_2=shipping_address_line_2,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                status=initial_status,
            )

            for product, qty, line_total, unit_price, product_name, purchase_option in order_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product_name,
                    purchase_option=purchase_option,
                    unit_price=unit_price,
                    quantity=qty,
                    line_total=line_total,
                )
                product.stock -= qty
                product.save(update_fields=['stock'])

            # For COD (immediately confirmed), dispatch confirmation after items are committed to DB
            if initial_status == Order.OrderStatus.CONFIRMED:
                from notifications.signals import _send_order_confirmation, _send_order_confirmed_whatsapp
                transaction.on_commit(lambda: _send_order_confirmation(order))
                transaction.on_commit(lambda: _send_order_confirmed_whatsapp(order))

        return order


# ──────────────────────────────────────────────────────────────────────────────
# Exchange Request Serializers
# ──────────────────────────────────────────────────────────────────────────────

EXCHANGE_WINDOW_HOURS = 48
MAX_VIDEO_SIZE_MB = 500
ACCEPTED_VIDEO_MIMES = {'video/mp4', 'video/quicktime', 'video/webm'}


class ExchangeRequestSerializer(serializers.ModelSerializer):
    """Read-only serializer for returning exchange request data to the customer."""
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_item_name = serializers.CharField(source='order_item.product_name', read_only=True, default=None)
    alt_product_name = serializers.CharField(source='alt_product.name', read_only=True, default=None)
    unboxing_video_url = serializers.SerializerMethodField()

    class Meta:
        model = ExchangeRequest
        fields = [
            'id',
            'reference_id',
            'order_id',
            'order_item_name',
            'exchange_type',
            'alt_product_name',
            'reason',
            'unboxing_video_url',
            'status',
            'created_at',
            'updated_at',
        ]

    def get_unboxing_video_url(self, obj):
        request = self.context.get('request')
        if obj.unboxing_video and request:
            return request.build_absolute_uri(obj.unboxing_video.url)
        return None


class ExchangeRequestCreateSerializer(serializers.Serializer):
    """
    Validates and creates an ExchangeRequest.

    Business rules enforced here (not in model so that clear API error messages are returned):
    - Order must belong to the authenticated user.
    - Order must have been placed within the last 48 hours.
    - One active exchange per order_item (pending/approved/completed).
    - Video is required; must be MP4/MOV/WEBM and ≤ 500 MB.
    - If exchange_type == 'other', alt_product_id is required and product must be available.
    - Reason must be at least 20 characters.
    """

    order_id = serializers.IntegerField()
    order_item_id = serializers.IntegerField(required=False, allow_null=True)
    exchange_type = serializers.ChoiceField(choices=ExchangeRequest.ExchangeType.choices)
    alt_product_id = serializers.IntegerField(required=False, allow_null=True)
    reason = serializers.CharField(min_length=20, max_length=2000, trim_whitespace=True)
    unboxing_video = serializers.FileField()

    # Agreement checkboxes — frontend sends these; we store them in the audit log
    confirm_authentic = serializers.BooleanField()
    confirm_review = serializers.BooleanField()
    confirm_policy = serializers.BooleanField()

    def _get_order(self, order_id, user):
        try:
            return Order.objects.prefetch_related('items').get(pk=order_id, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                {'order_id': 'Order not found or does not belong to your account.'}
            )

    def validate_unboxing_video(self, video):
        content_type = getattr(video, 'content_type', '') or ''
        if content_type not in ACCEPTED_VIDEO_MIMES:
            raise serializers.ValidationError(
                'Invalid video format. Please upload an MP4, MOV, or WEBM file.'
            )
        max_bytes = MAX_VIDEO_SIZE_MB * 1024 * 1024
        if video.size > max_bytes:
            raise serializers.ValidationError(
                f'Video file is too large. Maximum allowed size is {MAX_VIDEO_SIZE_MB} MB.'
            )
        return video

    def validate_confirm_authentic(self, value):
        if not value:
            raise serializers.ValidationError('You must confirm the video is authentic and unedited.')
        return value

    def validate_confirm_review(self, value):
        if not value:
            raise serializers.ValidationError('You must acknowledge that the decision is subject to manual review.')
        return value

    def validate_confirm_policy(self, value):
        if not value:
            raise serializers.ValidationError('You must acknowledge the policy on false claims.')
        return value

    def validate(self, data):
        user = self.context['request'].user
        order = self._get_order(data['order_id'], user)

        # 1. 48-hour eligibility window
        cutoff = order.created_at + timedelta(hours=EXCHANGE_WINDOW_HOURS)
        if timezone.now() > cutoff:
            raise serializers.ValidationError(
                {'order_id': (
                    f'The {EXCHANGE_WINDOW_HOURS}-hour exchange window for this order has expired. '
                    'Exchange requests must be submitted within 48 hours of purchase.'
                )}
            )

        # 2. Resolve the order item (optional but encouraged)
        order_item = None
        order_item_id = data.get('order_item_id')
        if order_item_id:
            try:
                order_item = order.items.get(pk=order_item_id)
            except OrderItem.DoesNotExist:
                raise serializers.ValidationError(
                    {'order_item_id': 'Order item not found in this order.'}
                )

            # 3. Prevent duplicate exchange for this item
            already_exists = ExchangeRequest.objects.filter(
                order_item=order_item,
                status__in=[
                    ExchangeRequest.ExchangeStatus.PENDING_REVIEW,
                    ExchangeRequest.ExchangeStatus.APPROVED,
                    ExchangeRequest.ExchangeStatus.COMPLETED,
                ],
            ).exists()
            if already_exists:
                raise serializers.ValidationError(
                    {'order_item_id': (
                        'An active exchange request already exists for this item. '
                        'Only one exchange per item is allowed.'
                    )}
                )

        # 4. Validate alt_product if type == 'other'
        alt_product = None
        if data['exchange_type'] == ExchangeRequest.ExchangeType.OTHER:
            alt_product_id = data.get('alt_product_id')
            if not alt_product_id:
                raise serializers.ValidationError(
                    {'alt_product_id': 'Please select a replacement product when choosing "Another Item".'}
                )
            try:
                from products.models import Product
                alt_product = Product.objects.get(pk=alt_product_id, is_available=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    {'alt_product_id': 'Selected replacement product is unavailable or does not exist.'}
                )

        data['_order'] = order
        data['_order_item'] = order_item
        data['_alt_product'] = alt_product
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        order = validated_data.pop('_order')
        order_item = validated_data.pop('_order_item')
        alt_product = validated_data.pop('_alt_product')

        # Strip agreement booleans (not stored on model)
        validated_data.pop('confirm_authentic')
        validated_data.pop('confirm_review')
        validated_data.pop('confirm_policy')
        validated_data.pop('order_id')
        validated_data.pop('order_item_id', None)
        validated_data.pop('alt_product_id', None)

        return ExchangeRequest.objects.create(
            order=order,
            order_item=order_item,
            user=user,
            alt_product=alt_product,
            exchange_type=validated_data['exchange_type'],
            reason=validated_data['reason'],
            unboxing_video=validated_data['unboxing_video'],
        )
