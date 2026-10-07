from datetime import date

from rest_framework import serializers
from .models import Workshop, Booking


class WorkshopSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Workshop
        fields = [
            'id',
            'title',
            'description',
            'instructor',
            'date',
            'time',
            'duration',
            'price',
            'total_slots',
            'available_slots',
            'image',
            'image_url',
            'is_active',
            'created_at',
            'category',
            'icon',
            'schedule_text',
            'is_highlighted',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return None
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)


class BookingSerializer(serializers.ModelSerializer):
    workshop = WorkshopSerializer(read_only=True)
    workshop_id = serializers.PrimaryKeyRelatedField(
        queryset=Workshop.objects.all(), source='workshop', write_only=True,
        required=False, allow_null=True,
    )
    booking_date = serializers.DateTimeField(read_only=True)
    payment_status = serializers.CharField(read_only=True)
    payment_status_display = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_type', 'workshop', 'workshop_id', 'seats', 'sessions',
            'amount', 'customer_name', 'customer_phone', 'customer_email',
            'booking_date', 'payment_status', 'payment_status_display',
            'razorpay_order_id', 'razorpay_payment_id',
        ]

    def get_payment_status_display(self, obj):
        return obj.get_payment_status_display()


class InitiateWorkshopPaymentSerializer(serializers.Serializer):
    booking_type = serializers.ChoiceField(
        choices=Booking.BookingType.choices,
        required=False,
        default=Booking.BookingType.WORKSHOP,
    )
    workshop_id = serializers.IntegerField(required=False)
    seats = serializers.IntegerField(min_value=1, max_value=10, required=False, default=1)
    sessions = serializers.IntegerField(min_value=1, required=False)
    customer_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    customer_email = serializers.EmailField(required=False, allow_blank=True)

    def validate_workshop_id(self, value):
        try:
            workshop = Workshop.objects.get(pk=value)
        except Workshop.DoesNotExist:
            raise serializers.ValidationError('Workshop not found.')
        if not workshop.is_active or workshop.date < date.today():
            raise serializers.ValidationError('This workshop is no longer available.')
        self._workshop = workshop
        return value

    def validate_seats(self, value):
        workshop = getattr(self, '_workshop', None)
        if workshop and value > workshop.available_slots:
            raise serializers.ValidationError(
                f'Only {workshop.available_slots} seat(s) remaining.'
            )
        return value

    def validate(self, attrs):
        booking_type = attrs['booking_type']
        if booking_type == Booking.BookingType.WORKSHOP:
            if 'workshop_id' not in attrs:
                raise serializers.ValidationError({'workshop_id': 'Select a workshop.'})
            return attrs

        if 'workshop_id' in attrs:
            raise serializers.ValidationError({'workshop_id': 'Home Tuition does not use a workshop.'})
        if 'sessions' not in attrs:
            raise serializers.ValidationError({'sessions': 'Select the number of sessions.'})

        for field in ('customer_name', 'customer_phone', 'customer_email'):
            if not attrs.get(field):
                raise serializers.ValidationError({field: 'This field is required for Home Tuition.'})
        return attrs

    @property
    def workshop(self):
        return getattr(self, '_workshop', None)


class VerifyWorkshopPaymentSerializer(serializers.Serializer):
    razorpay_order_id   = serializers.CharField(max_length=255)
    razorpay_payment_id = serializers.CharField(max_length=255)
    razorpay_signature  = serializers.CharField(max_length=512)
