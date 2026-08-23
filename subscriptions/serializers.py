import re

from rest_framework import serializers

from .models import Subscription

_ISO_ALPHA2_RE = re.compile(r'^[A-Za-z]{2}$')


class SubscriptionItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


def _reject_empty_or_duplicate_items(items):
    if not items:
        raise serializers.ValidationError("At least one item is required.")
    product_ids = [item['product_id'] for item in items]
    duplicates = {pid for pid in product_ids if product_ids.count(pid) > 1}
    if duplicates:
        raise serializers.ValidationError(
            f"Duplicate product_id(s) in items: {sorted(duplicates)}"
        )
    return items


class DeliveryAddressSerializer(serializers.Serializer):
    """A customer's delivery address, collected inline on /start/ when they
    don't already have a Customer row -- see Task 6.5-C. `country` is
    restricted to a 2-letter ISO 3166-1 alpha-2 code (not free text) since
    Stripe Tax silently fails automatic_tax on anything else (e.g. the
    literal string "Sweden") -- the bug fixed in PR #12 for existing rows.
    """
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    shipping_address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, min_length=2)

    def validate_country(self, value):
        if not _ISO_ALPHA2_RE.match(value):
            raise serializers.ValidationError(
                "country must be a 2-letter ISO 3166-1 alpha-2 code (e.g. 'SE')."
            )
        return value.upper()


class SubscriptionStartSerializer(serializers.Serializer):
    frequency = serializers.ChoiceField(choices=Subscription.FREQUENCY_CHOICES)
    items = SubscriptionItemInputSerializer(many=True)
    delivery_address = DeliveryAddressSerializer(required=False)

    def validate_items(self, items):
        return _reject_empty_or_duplicate_items(items)


class SubscriptionItemsUpdateSerializer(serializers.Serializer):
    items = SubscriptionItemInputSerializer(many=True)

    def validate_items(self, items):
        return _reject_empty_or_duplicate_items(items)
