from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from django.core.validators import RegexValidator
from products.models import Product
from .delivery import lookup_pincode
from .models import Order, OrderItem

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

            shipping_fee = Decimal('0.00') if subtotal >= Decimal('10000.00') else Decimal('500.00')
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

        return order
