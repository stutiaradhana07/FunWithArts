"""
Management command to release expired PENDING workshop bookings.

Run manually:
    python manage.py release_expired_bookings

For cron (every 5 minutes):
    */5 * * * * cd /path/to/backend && python manage.py release_expired_bookings
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from workshops.models import Workshop
from workshops.views import _release_expired_pending_bookings


class Command(BaseCommand):
    help = (
        'Release workshop slots held by PENDING bookings older than '
        'PENDING_BOOKING_EXPIRY_MINUTES. Safe to run from cron every few minutes.'
    )

    def handle(self, *args, **options):
        # Only iterate workshops that could have pending bookings:
        # active + future-dated (past workshops are irrelevant)
        workshops = Workshop.objects.filter(is_active=True)

        total_released_bookings = 0
        total_released_seats = 0

        for workshop in workshops:
            with transaction.atomic():
                # Lock the row to avoid races with initiate-payment
                workshop = Workshop.objects.select_for_update().get(pk=workshop.pk)
                count = _release_expired_pending_bookings(workshop)
                if count:
                    total_released_bookings += count

        if total_released_bookings:
            self.stdout.write(
                self.style.WARNING(
                    f'Released {total_released_bookings} expired PENDING booking(s).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No expired PENDING bookings found.')
            )