from django.contrib import admin
from .models import Workshop, Booking


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'instructor', 'date', 'time', 'price', 'available_slots', 'total_slots', 'is_highlighted', 'is_active')
    list_filter = ('category', 'is_highlighted', 'date', 'instructor', 'is_active')
    search_fields = ('title', 'instructor', 'description')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'workshop', 'seats', 'payment_status', 'booking_date')
    list_filter = ('payment_status', 'booking_date')
    search_fields = ('user__username', 'workshop__title')
