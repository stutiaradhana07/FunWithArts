from datetime import date, timedelta, time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from workshops.models import Workshop


class Command(BaseCommand):
    help = 'Seed products and workshops for local frontend integration'

    def handle(self, *args, **options):
        products = [
            ('The Guardians',    'Decor',     Decimal('7800.00'),  12, True,  'Handmade wall decor inspired by studio expressions.', 'products/wall-faces.jpg'),
            ('Emerald Duo',      'Pots',      Decimal('4500.00'),  15, False, 'A clean two-piece pot pairing in rich green glaze.', 'products/wall-green-pots.jpg'),
            ('Artisan Bowl',     'Tableware', Decimal('3200.00'),  20, True,  'Textured serving bowl crafted in natural clay tones.', 'products/rosee.jpg'),
            ('Terracotta Holder','Office',    Decimal('2800.00'),  25, False, 'Desk accessory holder for everyday studio utility.', 'products/wall-pen-holder.png'),
            ('Earth Vessel',     'Vase',      Decimal('8900.00'),   8, False, 'Statement vase with earthy glaze and organic silhouette.', 'products/tall-vases.jpg'),
            ('Geometric Trio',   'Sets',      Decimal('12500.00'),  6, True,  'Three-piece geometric decor set for premium interiors.', 'products/geometric-trio.jpg'),
        ]

        for name, category_name, price, stock, is_new, description, image_path in products:
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'slug': slugify(category_name)}
            )
            Product.objects.update_or_create(
                name=name,
                defaults={
                    'category': category,
                    'price': price,
                    'stock': stock,
                    'is_new': is_new,
                    'description': description,
                    'image': image_path,
                    'is_available': True,
                },
            )

        self.stdout.write(f'  Seeded {len(products)} products')

        today = date.today()
        workshops = [
            (
                'Wheel Basics',
                'Foundational wheel-throwing workshop for beginners.',
                'Studio Mentor',
                today + timedelta(days=7),
                time(11, 0),
                120,
                Decimal('2200.00'),
                20,
            ),
            (
                'Handbuilding Textures',
                'Explore slab and coil techniques with decorative surface textures.',
                'Craft Lead',
                today + timedelta(days=14),
                time(15, 0),
                150,
                Decimal('2500.00'),
                16,
            ),
            (
                'Glaze & Fire',
                'Learn glazing techniques and understand kiln firing processes.',
                'Studio Mentor',
                today + timedelta(days=21),
                time(10, 0),
                180,
                Decimal('3000.00'),
                12,
            ),
        ]

        for title, description, instructor, workshop_date, workshop_time, duration, price, total_slots in workshops:
            Workshop.objects.update_or_create(
                title=title,
                defaults={
                    'description': description,
                    'instructor': instructor,
                    'date': workshop_date,
                    'time': workshop_time,
                    'duration': duration,
                    'price': price,
                    'total_slots': total_slots,
                    'available_slots': total_slots,
                },
            )

        self.stdout.write(f'  Seeded {len(workshops)} workshops (always upcoming)')
        self.stdout.write(self.style.SUCCESS('Seeded store data successfully.'))
