
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import PartnerStore

User = get_user_model()

@receiver(post_save, sender=User)
def setup_partner_user(sender, instance, created, **kwargs):
    if created and instance.is_partner:
        # Create PartnerStore if it doesn't exist
        PartnerStore.objects.get_or_create(
            user=instance,
            defaults={
                'store_name': f"{instance.username}'s Store",
                'contact_email': instance.email,
                'description': 'Auto-generated partner store.'
            }
        )

        # Make sure partner is treated as admin of their content
        if not instance.is_staff:
            instance.is_staff = True
            instance.save()

        # Assign basic permissions to partner user
        allowed_models = ['product', 'recipe']
        allowed_perms = ['add', 'view', 'change']
        for model in allowed_models:
            try:
                content_type = ContentType.objects.get(app_label='thefood', model=model)
                for action in allowed_perms:
                    perm = Permission.objects.get(content_type=content_type, codename=f"{action}_{model}")
                    instance.user_permissions.add(perm)
            except ContentType.DoesNotExist:
                continue  # Model hasn't been migrated yet, skip