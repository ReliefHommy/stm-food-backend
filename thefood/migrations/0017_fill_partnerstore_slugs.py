

from django.db import migrations
from django.utils.text import slugify

def fill_slugs(apps, schema_editor):
    PartnerStore = apps.get_model('thefood', 'PartnerStore')
    
    existing = set(
        PartnerStore.objects.exclude(slug__isnull=True)
        .exclude(slug="")
        .values_list("slug", flat=True)
    )

    

    for store in PartnerStore.objects.all().only("id", "store_name", "slug").iterator():
        if store.slug and store.slug.strip():
            continue

        base = slugify(store.store_name or "")
        if not base:
            base = f"partnerstore-{store.id}"

        slug = base
        i = 2
        while slug in existing or PartnerStore.objects.filter(slug=slug).exclude(id=store.id).exists():
            slug = f"{base}-{i}"
            i += 1

        store.slug = slug
        store.save(update_fields=["slug"])
        existing.add(slug)

def reverse_noop(apps, schema_editor):
    
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('thefood', '0016_alter_partnerstore_slug'),
    ]

    operations = [
        migrations.RunPython(fill_slugs, reverse_noop),
    ]
