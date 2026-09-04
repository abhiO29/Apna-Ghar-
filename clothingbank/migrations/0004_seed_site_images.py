from django.db import migrations

# One row per current image placement on the public site. `image` is left
# blank for all of them — templates fall back to the original static SVG
# via {% site_image key fallback %} until a superuser uploads a real photo.
SITE_IMAGES = [
    {
        "key": "hero_building",
        "label": "Homepage Hero — Building",
        "alt_text": "अपना घर वृद्ध आश्रम building, Ranaji Enclave, Najafgarh Road, New Delhi",
    },
    {
        "key": "about_building",
        "label": "About Page — Building Photo",
        "alt_text": "अपना घर building exterior",
    },
    {
        "key": "gallery_1",
        "label": "Gallery Photo 1",
        "alt_text": "अपना घर वृद्ध आश्रम building front view",
    },
    {
        "key": "gallery_2",
        "label": "Gallery Photo 2",
        "alt_text": "Community outreach poster showing meal service to elderly",
    },
    {
        "key": "gallery_3",
        "label": "Gallery Photo 3",
        "alt_text": "Community Clothing Bank showroom with racks of donated clothes",
    },
    {
        "key": "gallery_4",
        "label": "Gallery Photo 4",
        "alt_text": "Community Clothing Bank showroom, another view of the racks",
    },
    {
        "key": "clothing_bank_1",
        "label": "Clothing Bank Photo 1",
        "alt_text": "Community Clothing Bank showroom",
    },
    {
        "key": "clothing_bank_2",
        "label": "Clothing Bank Photo 2",
        "alt_text": "Racks of donated clothes organised by colour and category",
    },
    {
        "key": "donate_qr",
        "label": "Donate Page — UPI QR Code",
        "alt_text": "Placeholder — the organisation's official UPI QR code will be shown here",
    },
]


def seed_site_images(apps, schema_editor):
    SiteImage = apps.get_model("clothingbank", "SiteImage")
    for entry in SITE_IMAGES:
        SiteImage.objects.get_or_create(
            key=entry["key"],
            defaults={"label": entry["label"], "alt_text": entry["alt_text"]},
        )


def remove_site_images(apps, schema_editor):
    SiteImage = apps.get_model("clothingbank", "SiteImage")
    SiteImage.objects.filter(key__in=[e["key"] for e in SITE_IMAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clothingbank", "0003_siteimage"),
    ]

    operations = [
        migrations.RunPython(seed_site_images, remove_site_images),
    ]
