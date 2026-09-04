"""
URL configuration for the अपना घर वृद्ध आश्रम project.

NOTE: Django's built-in admin site lives at /django-admin/ rather than the
usual /admin/ — our own "Admin / Volunteer Login" panel already owns the
/admin/login.html and /admin/dashboard.html paths (kept identical to the
original static site), so we moved Django's site to avoid a collision.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from clothingbank import views as clothingbank_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/api/", include("clothingbank.urls")),
    path("contact/submit/", clothingbank_views.contact_submit, name="contact_submit"),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
