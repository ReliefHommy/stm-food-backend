from rest_framework import serializers

from .models import Subscription


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


class SubscriptionStartSerializer(serializers.Serializer):
    frequency = serializers.ChoiceField(choices=Subscription.FREQUENCY_CHOICES)
    items = SubscriptionItemInputSerializer(many=True)

    def validate_items(self, items):
        return _reject_empty_or_duplicate_items(items)


class SubscriptionItemsUpdateSerializer(serializers.Serializer):
    items = SubscriptionItemInputSerializer(many=True)

    def validate_items(self, items):
        return _reject_empty_or_duplicate_items(items)
