from django.contrib import admin

from .models import ContactEnquiry, Donor, InventoryShelf, IssueRecord, SiteImage


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "category", "count", "date", "created_by")
    list_filter = ("category", "date")
    search_fields = ("name", "mobile", "whatsapp")
    date_hierarchy = "date"


@admin.register(InventoryShelf)
class InventoryShelfAdmin(admin.ModelAdmin):
    list_display = ("shelf", "category", "size", "qty", "status", "updated_at")
    list_filter = ("category", "status")
    search_fields = ("shelf",)


@admin.register(IssueRecord)
class IssueRecordAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "category", "count", "date", "issued_by")
    list_filter = ("category", "date")
    search_fields = ("name", "mobile")
    date_hierarchy = "date"


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "subject", "status", "submitted_at", "handled_by")
    list_filter = ("status", "subject")
    search_fields = ("name", "mobile", "message")
    date_hierarchy = "submitted_at"


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "image", "updated_at", "updated_by")
    search_fields = ("key", "label")
    readonly_fields = ("updated_at", "updated_by")
