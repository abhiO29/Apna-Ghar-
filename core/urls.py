from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Alias: every page's nav/footer links to "index.html" as a relative
    # href, which browsers resolve to /index.html from any top-level page.
    path("index.html", views.HomeView.as_view(), name="home_index"),
    path("about.html", views.AboutView.as_view(), name="about"),
    path("gallery.html", views.GalleryView.as_view(), name="gallery"),
    path("donate.html", views.DonateView.as_view(), name="donate"),
    path("clothing-bank.html", views.ClothingBankView.as_view(), name="clothing_bank"),
    path("contact.html", views.ContactView.as_view(), name="contact"),
    path("admin/login.html", views.AdminLoginView.as_view(), name="admin_login"),
    path("admin/dashboard.html", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("admin/logout", views.AdminLogoutView.as_view(), name="admin_logout"),
]
