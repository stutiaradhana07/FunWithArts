from django.contrib import admin
from .models import Workshop, Booking


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'instructor', 'date', 'time', 'price', 'available_slots', 'total_slots')
    list_filter = ('date', 'instructor')
    search_fields = ('title', 'instructor', 'description')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'workshop', 'seats', 'booking_date')
    list_filter = ('booking_date',)
    search_fields = ('user__username', 'workshop__title')
