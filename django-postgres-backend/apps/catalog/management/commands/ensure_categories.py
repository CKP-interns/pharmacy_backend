"""
Management command to ensure all required medicine categories exist in the database.
This command is idempotent - it will create missing categories but won't duplicate existing ones.
"""
from django.core.management.base import BaseCommand
from apps.catalog.models import ProductCategory


class Command(BaseCommand):
    help = 'Ensure all required medicine categories exist in the database'

    def handle(self, *args, **options):
        # List of category names (frontend maps these via string IDs)
        CATEGORIES = [
            'Tablet',
            'Capsule',
            'Syrup/Suspension',
            'Injection/Vial',
            'Ointment/Cream',
            'Drops (Eye/Ear/Nasal)',
            'Inhaler',
            'Powder/Sachet',
            'Gel',
            'Spray',
            'Lotion/Solution',
            'Shampoo',
            'Soap/Bar',
            'Bandage/Dressing',
            'Mask (Surgical/N95)',
            'Gloves',
            'Cotton/Gauze',
            'Hand Sanitizer',
            'Thermometer',
            'Supplement/Vitamin',
            'Other/Miscellaneous',
        ]
        
        created_count = 0
        existing_count = 0
        
        for category_name in CATEGORIES:
            category, created = ProductCategory.objects.get_or_create(
                name=category_name,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created category: {category_name}')
                )
            else:
                existing_count += 1
                # Ensure it's active
                if not category.is_active:
                    category.is_active = True
                    category.save()
                    self.stdout.write(
                        self.style.WARNING(f'✓ Activated existing category: {category_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Category already exists: {category_name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} new categories, '
                f'{existing_count} categories already existed.'
            )
        )

