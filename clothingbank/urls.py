from django.urls import path

from . import views

urlpatterns = [
    path("data/", views.api_data, name="api_data"),
    path("donors/", views.api_donors_create, name="api_donors_create"),
    path("inventory/", views.api_inventory_upsert, name="api_inventory_upsert"),
    path("issues/", views.api_issues_create, name="api_issues_create"),
    path("enquiries/<int:pk>/handle/", views.api_enquiry_handle, name="api_enquiry_handle"),
    path("site-images/", views.api_site_images_list, name="api_site_images_list"),
    path("site-images/<slug:key>/", views.api_site_image_upload, name="api_site_image_upload"),
]
