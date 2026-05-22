from django.core.management.base import BaseCommand
from orders.models import PincodeRule, ShippingZone


class Command(BaseCommand):
    help = 'Seed shipping zones and pincode rules for delivery checks'

    def handle(self, *args, **options):
        zones_spec = [
            {
                'slug': 'delhi-ncr',
                'name': 'Delhi NCR',
                'is_serviceable': True,
                'min_delivery_days': 2,
                'max_delivery_days': 4,
                'description': 'Delhi, Gurugram, Noida, Faridabad & nearby',
                'sort_order': 10,
                'prefixes': ['110', '121', '122', '201'],
            },
            {
                'slug': 'metro',
                'name': 'Metro cities',
                'is_serviceable': True,
                'min_delivery_days': 4,
                'max_delivery_days': 6,
                'description': 'Major metros across India',
                'sort_order': 20,
                'prefixes': [
                    '400', '401', '410', '411',  # Mumbai / Pune
                    '560', '561',  # Bengaluru
                    '600', '601', '602',  # Chennai
                    '700', '701', '711',  # Kolkata
                    '500', '501', '502',  # Hyderabad
                    '380', '390',  # Ahmedabad
                    '302', '303',  # Jaipur
                    '226', '227',  # Lucknow
                    '160', '140',  # Chandigarh / Mohali
                ],
            },
            {
                'slug': 'north-india',
                'name': 'North India',
                'is_serviceable': True,
                'min_delivery_days': 5,
                'max_delivery_days': 7,
                'region_digit': '1',
                'is_default_region': True,
                'sort_order': 30,
                'prefixes': [],
            },
            {
                'slug': 'west-india',
                'name': 'West & Central India',
                'is_serviceable': True,
                'min_delivery_days': 5,
                'max_delivery_days': 8,
                'region_digit': '3',
                'is_default_region': True,
                'sort_order': 40,
                'prefixes': [],
            },
            {
                'slug': 'east-india',
                'name': 'East India',
                'is_serviceable': True,
                'min_delivery_days': 6,
                'max_delivery_days': 9,
                'region_digit': '5',
                'is_default_region': True,
                'sort_order': 50,
                'prefixes': [],
            },
            {
                'slug': 'south-india',
                'name': 'South India',
                'is_serviceable': True,
                'min_delivery_days': 6,
                'max_delivery_days': 9,
                'region_digit': '8',
                'is_default_region': True,
                'sort_order': 60,
                'prefixes': [],
            },
            {
                'slug': 'central-east',
                'name': 'Central & East (MP, Odisha, AP)',
                'is_serviceable': True,
                'min_delivery_days': 6,
                'max_delivery_days': 9,
                'region_digit': '4',
                'is_default_region': True,
                'sort_order': 70,
                'prefixes': [],
            },
            {
                'slug': 'maharashtra-goa',
                'name': 'Maharashtra & Goa',
                'is_serviceable': True,
                'min_delivery_days': 5,
                'max_delivery_days': 8,
                'region_digit': '9',
                'is_default_region': True,
                'sort_order': 80,
                'prefixes': [],
            },
            {
                'slug': 'up-uk',
                'name': 'Uttar Pradesh & Uttarakhand',
                'is_serviceable': True,
                'min_delivery_days': 5,
                'max_delivery_days': 8,
                'region_digit': '2',
                'is_default_region': True,
                'sort_order': 90,
                'prefixes': [],
            },
            {
                'slug': 'east-south-mixed',
                'name': 'Odisha, Telangana & neighbouring',
                'is_serviceable': True,
                'min_delivery_days': 6,
                'max_delivery_days': 9,
                'region_digit': '7',
                'is_default_region': True,
                'sort_order': 100,
                'prefixes': [],
            },
            {
                'slug': 'north-east',
                'name': 'North East & hills',
                'is_serviceable': True,
                'min_delivery_days': 7,
                'max_delivery_days': 12,
                'region_digit': '6',
                'is_default_region': True,
                'sort_order': 110,
                'prefixes': [],
            },
            {
                'slug': 'remote-islands',
                'name': 'Islands & remote areas',
                'is_serviceable': False,
                'min_delivery_days': 0,
                'max_delivery_days': 0,
                'description': 'Andaman, Lakshadweep & selected remote pincodes',
                'sort_order': 200,
                'prefixes': ['744', '682', '737'],
                'exact': [],
            },
            {
                'slug': 'ne-restricted',
                'name': 'Restricted North East',
                'is_serviceable': False,
                'min_delivery_days': 0,
                'max_delivery_days': 0,
                'description': 'Selected NE pincode ranges — contact support',
                'sort_order': 210,
                'prefixes': ['790', '791', '792', '793', '794', '795', '796', '797', '798', '799'],
                'exact': [],
            },
        ]

        PincodeRule.objects.all().delete()
        ShippingZone.objects.all().delete()

        for spec in zones_spec:
            prefixes = spec.pop('prefixes', [])
            exact = spec.pop('exact', [])
            zone, _ = ShippingZone.objects.update_or_create(
                slug=spec['slug'],
                defaults={k: v for k, v in spec.items() if k != 'slug'},
            )
            for prefix in prefixes:
                PincodeRule.objects.create(
                    rule_type=PincodeRule.RuleType.PREFIX,
                    value=prefix,
                    zone=zone,
                    priority=10,
                )
            for pin in exact:
                PincodeRule.objects.create(
                    rule_type=PincodeRule.RuleType.EXACT,
                    value=pin,
                    zone=zone,
                    priority=5,
                )

        self.stdout.write(self.style.SUCCESS(
            f'  Seeded {ShippingZone.objects.count()} zones and '
            f'{PincodeRule.objects.count()} pincode rules'
        ))
