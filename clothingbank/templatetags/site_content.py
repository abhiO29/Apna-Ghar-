"""
{% site_image "hero_building" "images/building.svg" %}

Looks up the SiteImage row for `key` and renders its uploaded image URL;
falls back to the given static path if the row has no image uploaded yet
(or doesn't exist at all, e.g. before migrations run). This is what lets
Super Admins replace public-site photos without touching templates or
static files.
"""
from django import template
from django.templatetags.static import static as static_url

from clothingbank.models import SiteImage

register = template.Library()


@register.simple_tag
def site_image(key, fallback):
    try:
        obj = SiteImage.objects.get(key=key)
    except SiteImage.DoesNotExist:
        return static_url(fallback)

    if obj.image:
        return obj.image.url
    return static_url(fallback)
