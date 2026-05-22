"""
Pincode serviceability and delivery estimates for Fun With Art (Delhi studio).

Lookup order:
  1. Exact pincode rules (highest priority)
  2. Longest matching prefix rules
  3. Default zone by India postal region (first digit)
"""
from dataclasses import dataclass

from .models import PincodeRule, ShippingZone


@dataclass(frozen=True)
class DeliveryLookupResult:
    pincode: str
    is_serviceable: bool
    zone_name: str
    zone_slug: str
    min_delivery_days: int
    max_delivery_days: int
    estimated_delivery: str
    message: str

    def as_dict(self):
        return {
            'pincode': self.pincode,
            'is_serviceable': self.is_serviceable,
            'zone': self.zone_name,
            'zone_slug': self.zone_slug,
            'min_delivery_days': self.min_delivery_days,
            'max_delivery_days': self.max_delivery_days,
            'estimated_delivery': self.estimated_delivery,
            'message': self.message,
        }


def format_delivery_window(min_days: int, max_days: int) -> str:
    if min_days == max_days:
        return f'{min_days} business day{"s" if min_days != 1 else ""}'
    return f'{min_days}-{max_days} business days'


def _result_from_zone(pincode: str, zone: ShippingZone) -> DeliveryLookupResult:
    estimated = format_delivery_window(zone.min_delivery_days, zone.max_delivery_days)
    if zone.is_serviceable:
        message = f'We deliver to {zone.name}. Estimated delivery: {estimated}.'
    else:
        message = (
            f'Sorry, we do not ship to {zone.name} yet. '
            'Contact us at support@funwithart.com for special arrangements.'
        )
    return DeliveryLookupResult(
        pincode=pincode,
        is_serviceable=zone.is_serviceable,
        zone_name=zone.name,
        zone_slug=zone.slug,
        min_delivery_days=zone.min_delivery_days,
        max_delivery_days=zone.max_delivery_days,
        estimated_delivery=estimated,
        message=message,
    )


def _zone_for_pincode(pincode: str) -> ShippingZone | None:
    exact = (
        PincodeRule.objects.filter(rule_type=PincodeRule.RuleType.EXACT, value=pincode)
        .select_related('zone')
        .order_by('priority', 'id')
        .first()
    )
    if exact:
        return exact.zone

    prefix_rules = list(
        PincodeRule.objects.filter(rule_type=PincodeRule.RuleType.PREFIX)
        .select_related('zone')
        .order_by('priority', 'id')
    )
    matching = [rule for rule in prefix_rules if pincode.startswith(rule.value)]
    if matching:
        matching.sort(key=lambda rule: (-len(rule.value), rule.priority, rule.id))
        return matching[0].zone

    region_digit = pincode[0]
    return (
        ShippingZone.objects.filter(region_digit=region_digit, is_default_region=True)
        .order_by('sort_order')
        .first()
    )


def lookup_pincode(pincode: str) -> DeliveryLookupResult:
    """
    Resolve delivery options for a 6-digit Indian pincode.
    Caller must validate pincode format before calling.
    """
    zone = _zone_for_pincode(pincode)
    if zone is None:
        return DeliveryLookupResult(
            pincode=pincode,
            is_serviceable=False,
            zone_name='Unknown',
            zone_slug='unknown',
            min_delivery_days=0,
            max_delivery_days=0,
            estimated_delivery='Not available',
            message='Delivery is not available for this pincode.',
        )
    return _result_from_zone(pincode, zone)


def validate_pincode_serviceable(pincode: str) -> None:
    """Raise ValueError if pincode cannot receive orders."""
    result = lookup_pincode(pincode)
    if not result.is_serviceable:
        raise ValueError(result.message)
