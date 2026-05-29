"""
migrate_images_to_cloudinary.py

Management command to upload local product images to Cloudinary and update
the Product model image fields so they point to Cloudinary public IDs.

Usage:
    python manage.py migrate_images_to_cloudinary [--dry-run]

Run this once after setting up Cloudinary to migrate any locally-stored
images to the persistent Cloudinary CDN.
"""
import os

import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = 'Upload locally-stored product images to Cloudinary and update DB records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be uploaded without making any changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = str(settings.MEDIA_ROOT)

        self.stdout.write(self.style.NOTICE(
            f'Media root: {media_root}\nDry run: {dry_run}\n'
        ))

        products = Product.objects.all()
        migrated = 0
        skipped = 0
        errors = 0

        for product in products:
            product_changed = False
            for field_name in ('image', 'image2', 'image3'):
                field = getattr(product, field_name)
                if not field:
                    continue

                name = field.name  # e.g. 'products/Picture1.jpg'

                # cloudinary_storage prepends 'media/' when building Cloudinary URLs.
                # So the real Cloudinary public_id must be 'media/products/picturename'.
                # We check if the local file exists to see if it needs uploading.
                local_path = os.path.join(media_root, name)
                if not os.path.isfile(local_path):
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [{product.id}] {field_name}: local file not found: {local_path}'
                        )
                    )
                    skipped += 1
                    continue

                # Build the Cloudinary public_id with the 'media/' prefix that
                # cloudinary_storage expects when generating URLs.
                basename_no_ext = os.path.splitext(os.path.basename(name))[0].lower().replace(' ', '_')
                cloudinary_public_id = 'media/products/' + basename_no_ext
                # The name stored in Django's ImageField (without 'media/' prefix)
                new_field_name = 'products/' + basename_no_ext + os.path.splitext(os.path.basename(name))[1].lower()

                self.stdout.write(f'  [{product.id}] {field_name}: {name} -> Cloudinary:{cloudinary_public_id}')

                if dry_run:
                    skipped += 1
                    continue

                try:
                    result = cloudinary.uploader.upload(
                        local_path,
                        public_id=cloudinary_public_id,
                        overwrite=True,
                        resource_type='image',
                    )
                    # Store the relative path (without 'media/') in the DB field.
                    # cloudinary_storage will prepend 'media/' when generating URLs.
                    setattr(product, field_name, new_field_name)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'    OK Uploaded: {result["secure_url"]}'
                        )
                    )
                    migrated += 1
                    product_changed = True
                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(f'    FAILED: {exc}')
                    )
                    errors += 1

            if not dry_run and product_changed:
                product.save()

        self.stdout.write('\n' + self.style.SUCCESS(
            f'Done. Migrated: {migrated}, Skipped/Dry: {skipped}, Errors: {errors}'
        ))
