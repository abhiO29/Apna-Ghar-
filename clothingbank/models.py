from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

CATEGORY_CHOICES = [("Men", "Men"), ("Women", "Women"), ("Kids", "Kids")]
MOBILE_VALIDATOR = RegexValidator(r'^[0-9]{10}$', "Enter a valid 10-digit mobile number.")


class Donor(models.Model):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10, validators=[MOBILE_VALIDATOR])
    whatsapp = models.CharField(max_length=10, blank=True, validators=[MOBILE_VALIDATOR])
    address = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    count = models.PositiveIntegerField()
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.category}, {self.count})"


class InventoryShelf(models.Model):
    STATUS_CHOICES = [("Available", "Available"), ("Given", "Given"), ("Damaged", "Damaged")]

    shelf = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    size = models.CharField(max_length=30)
    qty = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Available")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.shelf} ({self.category}, {self.qty})"


class IssueRecord(models.Model):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10, validators=[MOBILE_VALIDATOR])
    address = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    count = models.PositiveIntegerField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} ({self.category}, {self.count})"


class ContactEnquiry(models.Model):
    STATUS_CHOICES = [("New", "New"), ("Handled", "Handled")]

    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10, validators=[MOBILE_VALIDATOR])
    subject = models.CharField(max_length=100)  # matches the <select> options in contact.html
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="New")
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    handled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} — {self.subject} ({self.status})"


class SiteImage(models.Model):
    """A superuser-replaceable photo slot on the public site. `key` is the
    stable identifier templates look up via {% site_image "key" "fallback.svg" %};
    an empty `image` means "not uploaded yet" and the template falls back to
    the original static SVG."""

    key = models.SlugField(unique=True)
    label = models.CharField(max_length=100)
    image = models.ImageField(upload_to="site_images/", blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.label
