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
        queryset=Workshop.objects.all(), source='workshop', write_only=True
    )
    booking_date = serializers.DateTimeField(read_only=True)
    payment_status = serializers.CharField(read_only=True)
    payment_status_display = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'workshop', 'workshop_id', 'seats', 'booking_date',
            'payment_status', 'payment_status_display',
        ]

    def get_payment_status_display(self, obj):
        return obj.get_payment_status_display()


class InitiateWorkshopPaymentSerializer(serializers.Serializer):
    workshop_id = serializers.IntegerField()
    seats = serializers.IntegerField(min_value=1, max_value=10)

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

    @property
    def workshop(self):
        return self._workshop


class VerifyWorkshopPaymentSerializer(serializers.Serializer):
    razorpay_order_id   = serializers.CharField(max_length=255)
    razorpay_payment_id = serializers.CharField(max_length=255)
    razorpay_signature  = serializers.CharField(max_length=512)
