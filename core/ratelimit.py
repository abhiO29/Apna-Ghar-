"""
Minimal per-IP rate limiting on top of Django's cache framework — no new
dependency (no django-ratelimit, no Redis requirement; LocMemCache is fine
for this). Used on /admin/login.html (POST) and /contact/submit/, the two
public-facing endpoints an attacker could hammer (credential stuffing /
enquiry spam) without ever needing to authenticate first.
"""
from django.core.cache import cache
from django.http import HttpResponse


def _client_ip(request):
    return request.META.get("REMOTE_ADDR") or "unknown"


def rate_limited(key_prefix, limit, window_seconds, methods=("POST",)):
    """Allow at most `limit` requests per client IP per `window_seconds`,
    counting only the given HTTP methods (default: POST only — GETting a
    login page shouldn't burn down the same budget as submitting it)."""

    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return view_func(request, *args, **kwargs)

            cache_key = f"ratelimit:{key_prefix}:{_client_ip(request)}"
            # cache.add() only succeeds if the key doesn't exist yet, so it
            # atomically starts a fresh fixed window; every request after
            # that within the window just increments the same counter
            # without resetting its expiry.
            if cache.add(cache_key, 1, timeout=window_seconds):
                count = 1
            else:
                try:
                    count = cache.incr(cache_key)
                except ValueError:
                    # Key expired between the add() check and incr() —
                    # treat this request as the start of a new window.
                    cache.set(cache_key, 1, timeout=window_seconds)
                    count = 1

            if count > limit:
                return HttpResponse(
                    "Too many requests. Please wait a few minutes and try again.",
                    status=429,
                    content_type="text/plain",
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
