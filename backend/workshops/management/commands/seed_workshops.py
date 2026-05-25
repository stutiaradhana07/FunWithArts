"""
Management command to seed the 5 core workshops displayed on the studio page.

Usage:
    python manage.py seed_workshops

This command is idempotent — running it multiple times will not create duplicates.
"""

from datetime import date, time
from django.core.management.base import BaseCommand
from workshops.models import Workshop


SEED_WORKSHOPS = [
    {
        'title': 'Beginner Pottery Course',
        'description': (
            'Start your pottery journey with foundational techniques in handbuilding '
            'and wheel work. Includes a certificate upon completion.'
        ),
        'instructor': 'Studio Team',
        'date': date(2027, 1, 15),
        'time': time(10, 0),
        'duration': 8 * 120,  # 8 classes × 2 hours
        'price': 7000,
        'total_slots': 12,
        'available_slots': 12,
        'category': Workshop.Category.PROGRAM,
        'icon': '🌱',
        'schedule_text': '1 Month • 8 Classes',
        'is_highlighted': True,
    },
    {
        'title': 'Intermediate Pottery Course',
        'description': (
            'Refine your skills with advanced wheel throwing, surface detailing, '
            'and glazing. Includes a completion certificate.'
        ),
        'instructor': 'Studio Team',
        'date': date(2027, 2, 1),
        'time': time(10, 0),
        'duration': 16 * 120,  # 16 classes × 2 hours
        'price': 15000,
        'total_slots': 10,
        'available_slots': 10,
        'category': Workshop.Category.PROGRAM,
        'icon': '✨',
        'schedule_text': '2 Months • 16 Classes',
        'is_highlighted': True,
    },
    {
        'title': 'Advanced Ceramic Program',
        'description': (
            'An intensive studio program to master professional ceramic finishing '
            'and sculptural forms. Certificate included.'
        ),
        'instructor': 'Studio Team',
        'date': date(2027, 3, 1),
        'time': time(10, 0),
        'duration': 25 * 120,  # 25 classes × 2 hours
        'price': 24000,
        'total_slots': 8,
        'available_slots': 8,
        'category': Workshop.Category.PROGRAM,
        'icon': '🔥',
        'schedule_text': '3 Months • 25 Classes',
        'is_highlighted': True,
    },
    {
        'title': 'One Day Pottery Workshop',
        'description': (
            'Explore clay and learn basic shaping techniques to create your own piece. '
            'Perfect for a quick creative escape.'
        ),
        'instructor': 'Studio Team',
        'date': date(2027, 1, 20),
        'time': time(14, 0),
        'duration': 120,  # 2 hours
        'price': 1200,
        'total_slots': 15,
        'available_slots': 15,
        'category': Workshop.Category.EXPERIENCE,
        'icon': '🏺',
        'schedule_text': '1 Day • 2 Hours',
        'is_highlighted': False,
    },
    {
        'title': 'The Clay Date',
        'description': (
            'A private, guided session for two. Bring a partner, enjoy some chai, '
            'and learn how to throw together.'
        ),
        'instructor': 'Studio Team',
        'date': date(2027, 2, 14),  # Valentine's 😊
        'time': time(16, 0),
        'duration': 120,  # 2 hours
        'price': 3500,
        'total_slots': 6,  # 6 pairs
        'available_slots': 6,
        'category': Workshop.Category.EXPERIENCE,
        'icon': '✨',
        'schedule_text': '2 Hours • For Two',
        'is_highlighted': False,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with the 5 core studio workshops.'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for data in SEED_WORKSHOPS:
            title = data.pop('title')
            workshop, was_created = Workshop.objects.get_or_create(
                title=title,
                defaults=data,
            )
            if was_created:
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [OK] Created: {title}')
                )
            else:
                skipped += 1
                self.stdout.write(
                    f'  [--] Skipped (already exists): {title}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created} created, {skipped} already existed.'
            )
        )