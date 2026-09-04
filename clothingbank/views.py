"""
JSON API for the admin dashboard's Donor / Inventory / Issue / Enquiry data
— replaces the localStorage data layer that used to live entirely in
admin.js. Plain JsonResponse views (no DRF needed).

Every view here requires a logged-in session (same as the dashboard page
itself) EXCEPT contact_submit, which backs the public /contact.html form
and must stay reachable by anonymous visitors.
"""
import json
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
from PIL import Image, UnidentifiedImageError

from core.ratelimit import rate_limited

from .forms import ContactEnquiryForm, DonorForm, InventoryShelfForm, IssueRecordForm
from .models import ContactEnquiry, Donor, InventoryShelf, IssueRecord, SiteImage

DUPLICATE_SUBMISSION_WINDOW = timedelta(minutes=5)

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
# Extension is derived from Pillow's verified format, never from the
# client's filename — closes off the classic "photo.jpg.php" style attack.
IMAGE_FORMAT_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif"}


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except ValueError:
        return {}


def _serialize_donor(d):
    return {
        "id": d.id,
        "name": d.name,
        "mobile": d.mobile,
        "whatsapp": d.whatsapp,
        "address": d.address,
        "date": d.date.isoformat(),
        "category": d.category,
        "count": d.count,
        "remarks": d.remarks,
    }


def _serialize_inventory(i):
    return {
        "id": i.id,
        "shelf": i.shelf,
        "category": i.category,
        "size": i.size,
        "qty": i.qty,
        "status": i.status,
    }


def _serialize_issue(i):
    return {
        "id": i.id,
        "name": i.name,
        "mobile": i.mobile,
        "address": i.address,
        "category": i.category,
        "count": i.count,
        "date": i.date.isoformat(),
    }


def _serialize_enquiry(e):
    return {
        "id": e.id,
        "name": e.name,
        "mobile": e.mobile,
        "subject": e.subject,
        "message": e.message,
        "submitted_at": e.submitted_at.isoformat(),
        "status": e.status,
        "handled_by": e.handled_by.get_username() if e.handled_by_id else None,
        "handled_at": e.handled_at.isoformat() if e.handled_at else None,
    }


@login_required
@require_GET
def api_data(request):
    donors_qs = Donor.objects.order_by("-created_at")
    issues_qs = IssueRecord.objects.order_by("-created_at")

    # Optional server-side date-range filter for the Reports section.
    # Only donors/issues are date-filterable — inventory has no date field,
    # and this is additive: with no from/to, behaviour is unchanged.
    date_from = _parse_date(request.GET.get("from"))
    date_to = _parse_date(request.GET.get("to"))
    if date_from:
        donors_qs = donors_qs.filter(date__gte=date_from)
        issues_qs = issues_qs.filter(date__gte=date_from)
    if date_to:
        donors_qs = donors_qs.filter(date__lte=date_to)
        issues_qs = issues_qs.filter(date__lte=date_to)

    donors = [_serialize_donor(d) for d in donors_qs]
    inventory = [_serialize_inventory(i) for i in InventoryShelf.objects.order_by("-updated_at")]
    issues = [_serialize_issue(i) for i in issues_qs]
    enquiries = [_serialize_enquiry(e) for e in ContactEnquiry.objects.order_by("-submitted_at")]
    return JsonResponse({"donors": donors, "inventory": inventory, "issues": issues, "enquiries": enquiries})


@login_required
@require_http_methods(["POST"])
def api_donors_create(request):
    form = DonorForm(_json_body(request))
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    donor = form.save(commit=False)
    donor.created_by = request.user
    donor.save()
    return JsonResponse(_serialize_donor(donor), status=201)


@login_required
@require_http_methods(["POST"])
def api_inventory_upsert(request):
    data = _json_body(request)
    shelf_code = (data.get("shelf") or "").strip().upper()
    if not shelf_code:
        return JsonResponse({"errors": {"shelf": ["This field is required."]}}, status=400)

    instance = InventoryShelf.objects.filter(shelf__iexact=shelf_code).first()
    form = InventoryShelfForm(data, instance=instance)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    shelf = form.save(commit=False)
    shelf.shelf = shelf_code
    shelf.save()
    return JsonResponse(_serialize_inventory(shelf), status=200)


@login_required
@require_http_methods(["POST"])
def api_issues_create(request):
    form = IssueRecordForm(_json_body(request))
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    category = form.cleaned_data["category"]
    count = form.cleaned_data["count"]

    with transaction.atomic():
        shelves = list(
            InventoryShelf.objects.select_for_update()
            .filter(category=category, status="Available", qty__gt=0)
            .order_by("shelf")
        )
        total_available = sum(s.qty for s in shelves)
        if total_available < count:
            return JsonResponse(
                {"error": f'Not enough stock available in "{category}" category. Please check Inventory.'},
                status=400,
            )

        remaining = count
        for shelf in shelves:
            if remaining <= 0:
                break
            take = min(shelf.qty, remaining)
            shelf.qty -= take
            remaining -= take
            shelf.save(update_fields=["qty", "updated_at"])

        issue = form.save(commit=False)
        issue.issued_by = request.user
        issue.save()

    return JsonResponse(_serialize_issue(issue), status=201)


@rate_limited("contact_submit", limit=5, window_seconds=600)
@require_http_methods(["POST"])
def contact_submit(request):
    """Public endpoint (no login required) backing the /contact.html form."""
    form = ContactEnquiryForm(_json_body(request))
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    name = form.cleaned_data["name"]
    mobile = form.cleaned_data["mobile"]
    message = form.cleaned_data["message"]

    cutoff = timezone.now() - DUPLICATE_SUBMISSION_WINDOW
    duplicate = ContactEnquiry.objects.filter(
        name=name, mobile=mobile, message=message, submitted_at__gte=cutoff
    ).exists()
    if duplicate:
        return JsonResponse(
            {"error": "This message was already sent a few minutes ago. Please wait before sending it again."},
            status=429,
        )

    enquiry = form.save()
    return JsonResponse({"success": True, "id": enquiry.id}, status=201)


@login_required
@require_http_methods(["POST"])
def api_enquiry_handle(request, pk):
    try:
        enquiry = ContactEnquiry.objects.get(pk=pk)
    except ContactEnquiry.DoesNotExist:
        return JsonResponse({"error": "Enquiry not found."}, status=404)

    enquiry.status = "Handled"
    enquiry.handled_by = request.user
    enquiry.handled_at = timezone.now()
    enquiry.save(update_fields=["status", "handled_by", "handled_at"])
    return JsonResponse(_serialize_enquiry(enquiry))


def _serialize_site_image(s):
    return {
        "key": s.key,
        "label": s.label,
        "alt_text": s.alt_text,
        "image_url": s.image.url if s.image else None,
        "has_custom_image": bool(s.image),
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "updated_by": s.updated_by.get_username() if s.updated_by_id else None,
    }


@login_required
@require_GET
def api_site_images_list(request):
    # Super Admin only — Site Content is a separate tier from the Admin/
    # Volunteer groups, gated on Django's own is_superuser flag.
    if not request.user.is_superuser:
        return JsonResponse({"error": "Superuser access required."}, status=403)

    images = [_serialize_site_image(s) for s in SiteImage.objects.order_by("key")]
    return JsonResponse({"site_images": images})


@login_required
@require_http_methods(["POST"])
def api_site_image_upload(request, key):
    if not request.user.is_superuser:
        return JsonResponse({"error": "Superuser access required."}, status=403)

    uploaded = request.FILES.get("image")
    if not uploaded:
        return JsonResponse({"error": "No image file was uploaded."}, status=400)

    if uploaded.size > MAX_IMAGE_UPLOAD_BYTES:
        return JsonResponse({"error": "Image must be 5MB or smaller."}, status=400)

    # Fast pre-filter on the client-declared content-type (easily spoofed —
    # the Pillow round-trip below is the real check).
    if uploaded.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        return JsonResponse({"error": "Unsupported file type."}, status=400)

    # Authoritative check: does this actually decode as an image? Rejects a
    # renamed .php/.svg/whatever even if its content-type header lied.
    try:
        uploaded.seek(0)
        probe = Image.open(uploaded)
        probe.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return JsonResponse({"error": "This file is not a valid image."}, status=400)

    # verify() leaves the file object unusable for further reads — reopen
    # to get a usable image and to confirm the format again post-verify.
    uploaded.seek(0)
    try:
        reopened = Image.open(uploaded)
        reopened.load()
        image_format = reopened.format
    except (UnidentifiedImageError, OSError, ValueError):
        return JsonResponse({"error": "This file is not a valid image."}, status=400)

    ext = IMAGE_FORMAT_EXTENSIONS.get(image_format)
    if not ext:
        return JsonResponse({"error": "Unsupported image format."}, status=400)

    site_image, _ = SiteImage.objects.get_or_create(
        key=key, defaults={"label": key.replace("_", " ").title()}
    )

    # Never trust the client's filename — generate our own storage name.
    uploaded.seek(0)
    site_image.image.save(f"{uuid.uuid4().hex}{ext}", uploaded, save=False)
    site_image.updated_by = request.user
    site_image.save()

    return JsonResponse(_serialize_site_image(site_image), status=200)
