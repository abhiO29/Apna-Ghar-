from django import forms

from .models import ContactEnquiry, Donor, InventoryShelf, IssueRecord


class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = ["name", "mobile", "whatsapp", "address", "date", "category", "count", "remarks"]


class InventoryShelfForm(forms.ModelForm):
    class Meta:
        model = InventoryShelf
        fields = ["category", "size", "qty", "status"]


class IssueRecordForm(forms.ModelForm):
    class Meta:
        model = IssueRecord
        fields = ["name", "mobile", "address", "category", "count", "date"]


class ContactEnquiryForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ["name", "mobile", "subject", "message"]
