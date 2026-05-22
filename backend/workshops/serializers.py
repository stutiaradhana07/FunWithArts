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
            'created_at',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return None
        if request is None:
            return obj.image.url
        return request.build_absolute_uri(obj.image.url)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'workshop', 'seats']
