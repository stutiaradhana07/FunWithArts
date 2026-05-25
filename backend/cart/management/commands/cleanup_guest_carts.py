from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cart.models import Cart


class Command(BaseCommand):
    help = 'Remove abandoned guest carts older than the specified number of days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than-days',
            type=int,
            default=30,
            help='Delete guest carts whose expires_at is older than this many days (default: 30).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting.',
        )

    def handle(self, *args, **options):
        days = options['older_than_days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        # Guest carts: expired AND no expires_at but older than cutoff by updated_at
        expired_qs = Cart.objects.filter(
            user__isnull=True,
            expires_at__isnull=False,
            expires_at__lt=cutoff,
        )
        # Also catch legacy guest carts without an expires_at (created before this field was added)
        legacy_qs = Cart.objects.filter(
            user__isnull=True,
            expires_at__isnull=True,
            updated_at__lt=cutoff,
        )

        expired_count = expired_qs.count()
        legacy_count = legacy_qs.count()
        total = expired_count + legacy_count

        self.stdout.write(f'Expired guest carts (with expires_at):  {expired_count}')
        self.stdout.write(f'Legacy guest carts (no expires_at):    {legacy_count}')
        self.stdout.write(f'Total to delete:                       {total}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no carts deleted.'))
            return

        # Delete items first (CASCADE should handle this, but be explicit)
        expired_qs.delete()
        legacy_qs.delete()

        self.stdout.write(self.style.SUCCESS(f'Deleted {total} abandoned guest cart(s).'))