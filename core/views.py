"""
Milestone 2: real Django authentication replaces the fake JS-based admin
login/logout. Donor/Inventory/Issue models are still Milestone 3.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/index.html"


class AboutView(TemplateView):
    template_name = "core/about.html"


class GalleryView(TemplateView):
    template_name = "core/gallery.html"


class DonateView(TemplateView):
    template_name = "core/donate.html"


class ClothingBankView(TemplateView):
    template_name = "core/clothing-bank.html"


class ContactView(TemplateView):
    template_name = "core/contact.html"


class AdminLoginView(LoginView):
    template_name = "admin_panel/login.html"
    redirect_authenticated_user = True


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin_panel/dashboard.html"


class AdminLogoutView(LogoutView):
    """POST-only logout (Django 5+ no longer allows GET). Redirects to
    LOGOUT_REDIRECT_URL (admin_login) per settings.py."""
