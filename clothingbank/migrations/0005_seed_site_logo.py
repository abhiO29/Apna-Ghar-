import os

from django.conf import settings
from django.core.files import File
from django.db import migrations

LOGO_SOURCE = os.path.join(settings.BASE_DIR, "core", "static", "images", "logo", "logo_master.png")


def seed_site_logo(apps, schema_editor):
    SiteImage = apps.get_model("clothingbank", "SiteImage")
    obj, _ = SiteImage.objects.get_or_create(
        key="site_logo",
        defaults={"label": "Site Logo", "alt_text": "अपना घर वृद्ध आश्रम logo"},
    )
    # Unlike the other seeded slots, this one ships with a real image from
    # day one — nav/footer/login/sidebar all read the same key, so a
    # superuser can replace the logo everywhere from the dashboard without
    # a code change.
    if not obj.image and os.path.exists(LOGO_SOURCE):
        with open(LOGO_SOURCE, "rb") as f:
            obj.image.save("site_logo.png", File(f), save=False)
        obj.save()


def remove_site_logo(apps, schema_editor):
    SiteImage = apps.get_model("clothingbank", "SiteImage")
    SiteImage.objects.filter(key="site_logo").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clothingbank", "0004_seed_site_images"),
    ]

    operations = [
        migrations.RunPython(seed_site_logo, remove_site_logo),
    ]
