"""
Management command to process the email retry queue.
Run periodically (e.g., every 5 minutes via cron or APScheduler):
    python manage.py process_email_retries

Or add to Celery beat schedule for periodic execution.
"""

from django.core.management.base import BaseCommand
from notifications.emails import process_email_retry_queue
import logging

logger = logging.getLogger('notifications')


class Command(BaseCommand):
    help = 'Process queued emails that are ready for retry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        self.stdout.write(self.style.SUCCESS('Starting email retry queue processing...'))
        
        try:
            process_email_retry_queue()
            self.stdout.write(self.style.SUCCESS('Email retry queue processed successfully'))
        except Exception as e:
            logger.exception('Error processing email retry queue')
            self.stdout.write(
                self.style.ERROR(f'Error processing email retry queue: {str(e)}')
            )
