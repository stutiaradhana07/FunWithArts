# 🔍 Backend Deep Audit — Udaan Studio / FunWithArts
**Scope:** Every Python file in all 9 apps was read line-by-line.
**Apps audited:** `products`, `orders`, `accounts`, `payments`, `cart`, `users`, `blogs`, `workshops`, `notifications` + main `backend/` config.

---

## ✅ What Is Solid and Complete

| App | What's done |
|---|---|
| **products** | `product_list` (with search/filter/is_new), `product_detail`, `product_search`, `category_list`, `product_reviews` (paginated GET + authenticated POST), `product_review_summary` with rating breakdown. All seeded with real data. Tests cover list, detail, filter, search, 404. |
| **orders** | `order_list_create` (paginated, filterable by status, orderable), `order_detail` (staff vs own), `guest_order_lookup` (email + order_id), `delivery_check` with real ShippingZone DB rules. Pincode logic handles exact match → prefix → region digit fallback. Stock decremented atomically. COD auto-confirms. Tests cover create, stock fail, delivery check, auth guard, cross-user 403. |
| **accounts** | Register, login, logout (token delete), `/me`, password reset (email with one-time token link), password reset confirm (uid+token validate, set password). Anti-enumeration on reset. |
| **cart** | Get, add item (stock check), update qty (qty=0 removes), remove item, clear, guest↔user merge (sums quantities, deletes guest cart). Guest carts via `session_id`. DB constraint prevents a cart having both user and session_id. |
| **users** | Profile GET/PUT/PATCH, wishlist GET/POST/DELETE. `get_or_create` for profile ensures lazy creation. Wishlist prevents duplicates (200 on duplicate add). Tests cover all CRUD paths. |
| **payments** | Razorpay create-order, signature verify, payment detail (ownership check), refund (Razorpay API + local record), webhook (payment.captured, payment.failed, refund.processed). `mark_captured()` atomically updates payment + order status. |
| **workshops** | List, detail, create booking (slot check, seat decrement). Email confirmation fires via signal. |
| **blogs** | Newsletter subscribe (idempotent — reactivates inactive subscribers), blog post list (published only), post detail by slug. |
| **notifications** | Order confirmation, order shipped, workshop booked, password reset emails — all fire async via daemon thread. HTML + plain text templates for all 4 triggers. Signals wired in `apps.py ready()`. |
| **Admin** | All models registered with `list_display`, `search_fields`, `list_filter`. Order has inline items. Payment has inline refunds. ShippingZone has inline pincode rules. Blog auto-assigns author. |
| **Config** | Custom CORS middleware (no extra package needed), `.env` + `.env.example`, seed commands for products+workshops+shipping zones, `manage.py check` passes 0 issues. |

---

## 🐛 Bugs (Will Break Things Right Now)

---

### Bug 1 — Newsletter URL Mismatch 🔴 Critical
**File:** [`backend/urls.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/backend/urls.py) · [`blogs/urls.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/blogs/urls.py)

**Root cause:** The newsletter endpoint lives inside the `blogs` app and is routed at `/api/blogs/subscribe/`. But the frontend, API contract, and `BACKEND_SETUP.md` all document it as `/api/newsletter/subscribe/`.

```python
# backend/urls.py — what it IS
path('api/blogs/', include('blogs.urls')),   # → /api/blogs/subscribe/

# What the frontend EXPECTS
POST /api/newsletter/subscribe/             # → 404 currently
```

**Impact:** Every newsletter subscription from the frontend fails with 404. The footer's "Join Us" form will silently never work.

**Fix:** Add an alias directly in `backend/urls.py`:
```python
from blogs.views import newsletter_subscribe
path('api/newsletter/subscribe/', newsletter_subscribe),
```

---

### Bug 2 — Guest Users Cannot Pay with Card/UPI 🔴 Critical
**File:** [`payments/views.py` L34–36](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/payments/views.py#L34-L36)

**Root cause:** `create_payment_order` is gated with `@permission_classes([IsAuthenticated])`. But `POST /api/orders/` allows guest checkout (`user=None`). A guest who places a card/UPI order is then completely stuck — they cannot call the payment endpoint to initiate Razorpay.

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])   # ← blocks all unauthenticated users
def create_payment_order(request):
    order = Order.objects.get(id=order_id)
    if order.user and order.user != request.user:  # ← only checks linked orders
        return Response({'error': '...'}, 403)
```

**Impact:** Only logged-in users can pay with card or UPI. Guest checkout is effectively limited to COD — which is not communicated anywhere.

**Fix:** Remove `IsAuthenticated` and instead verify ownership by checking `order.contact_email` against a request body field (e.g. `guest_email`) for guest orders:
```python
@api_view(['POST'])
@permission_classes([AllowAny])
def create_payment_order(request):
    order = get_object_or_404(Order, id=order_id)
    if order.user:
        # Authenticated order — must match token
        if not request.user.is_authenticated or order.user != request.user:
            return Response({'error': '...'}, 403)
    else:
        # Guest order — verify by email
        guest_email = request.data.get('contact_email', '')
        if order.contact_email.lower() != guest_email.lower():
            return Response({'error': 'Email does not match order.'}, 403)
```

---

### Bug 3 — Duplicate Payment Record Crashes with IntegrityError 🔴 Critical
**File:** [`payments/views.py` L64–71](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/payments/views.py#L64-L71)

**Root cause:** Every call to `create_payment_order` runs `Payment.objects.create(order=order, ...)`. Since `Payment` has `OneToOneField(Order, ...)`, a second call for the same order raises `django.db.utils.IntegrityError: UNIQUE constraint failed`. This is not caught.

```python
# Called every time — no duplicate check
payment = Payment.objects.create(
    order=order,
    razorpay_order_id=razorpay_order['id'],
    ...
)
```

**Impact:** If a user's payment fails and they retry (very common), the second attempt crashes with a 500. The retry flow is completely broken.

**Fix:** Use `get_or_create` or check first:
```python
existing = Payment.objects.filter(order=order, status=Payment.PaymentStatus.CREATED).first()
if existing:
    payment = existing
else:
    payment = Payment.objects.create(order=order, ...)
```

---

### Bug 4 — `Order.DoesNotExist` Not Caught → 500 Error 🟠 High
**File:** [`payments/views.py` L44–45](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/payments/views.py#L44-L45)

**Root cause:** `order = Order.objects.get(id=order_id)` raises `Order.DoesNotExist` if the order ID doesn't exist. The outer `except Exception` block catches it but returns a generic 500 message instead of a proper 404.

```python
order = Order.objects.get(id=order_id)   # raises DoesNotExist → 500
```

**Fix:**
```python
order = get_object_or_404(Order, id=order_id)
```

---

## ⚠️ Missing Features (Not Yet Built)

---

### Feature 1 — No Google (OAuth) Login 🔴 Critical for UX
**Files:** [`accounts/views.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/views.py), [`accounts/urls.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/urls.py)

**What's missing:** The entire auth system uses only username+password (DRF Token Auth). There is no OAuth2 / social login flow. For a modern e-commerce site aimed at Indian consumers, Google login is essentially expected.

**What's needed:**
- Install `social-auth-app-django` or `dj-rest-auth` with `allauth`
- Add `INSTALLED_APPS`: `social_django`, `allauth`, `allauth.socialaccount.providers.google`
- Configure Google OAuth2 credentials in `.env`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- New endpoint: `POST /api/auth/google/` — accepts the `id_token` from the frontend Google Sign-In button, verifies it, and returns a DRF Token
- The frontend needs the Google Sign-In JS SDK loaded + a button that triggers the flow

**Package to add to `requirements.txt`:**
```
social-auth-app-django>=4.0,<5
```

---

### Feature 2 — Email Login Not Supported 🟠 High
**File:** [`accounts/views.py` L57](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/views.py#L57), [`accounts/serializers.py` L21–23](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/serializers.py#L21-L23)

**Root cause:** The `LoginSerializer` accepts a field called `username`. Django's `authenticate()` matches only the `username` column, not `email`. A user who registered with `stuti@example.com` and tries to log in with their email will always get "Invalid credentials."

```python
# LoginSerializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()    # ← field label is "username"
    password = serializers.CharField()

# views.py
user = authenticate(username=username, password=password)  # ← never checks email
```

**Impact:** All users who attempt to log in with their email address (the majority) are locked out.

**Fix in `accounts/views.py`:**
```python
from django.contrib.auth.models import User

# In login_user view, before authenticate():
identifier = serializer.validated_data['username']
try:
    matched = User.objects.get(email__iexact=identifier)
    username = matched.username
except User.DoesNotExist:
    username = identifier  # try as-is (actual username)

user = authenticate(username=username, password=password)
```

---

### Feature 3 — No Email Uniqueness Validation on Registration 🟠 High
**File:** [`accounts/serializers.py` L8–18](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/serializers.py#L8-L18)

**Root cause:** Django's `User` model does NOT enforce email uniqueness at the DB level. `RegisterSerializer` marks email as `required=True` but adds no uniqueness constraint.

```python
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'email': {'required': True}}
        # ← No UniqueValidator on email!
```

**Impact:** Two users can register with the same email. When either one triggers password reset, `User.objects.get(email__iexact=email)` raises `MultipleObjectsReturned` → 500 crash. Also causes confusing duplicate accounts.

**Fix:**
```python
from rest_framework.validators import UniqueValidator

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='An account with this email already exists.'
        )]
    )
```

---

### Feature 4 — No Double-Booking Guard on Workshops 🟠 High
**File:** [`workshops/models.py` L21–28](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/workshops/models.py#L21-L28), [`workshops/views.py` L23–43](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/workshops/views.py#L23-L43)

**Root cause:** The `Booking` model has no `unique_together` on `(user, workshop)`. A user can call `POST /api/workshops/book/` multiple times for the same workshop and get multiple bookings — each one decrementing `available_slots`.

```python
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)
    seats = models.IntegerField(default=1)
    # ← No unique_together = ('user', 'workshop')
```

**Impact:** A user could drain all workshop slots by themselves. Available slots can reach negative values.

**Fix — two-step:**

Step 1: Add to `Booking.Meta`:
```python
class Meta:
    unique_together = ('user', 'workshop')
```
Step 2: In `create_booking` view, handle the error:
```python
from django.db import IntegrityError
try:
    booking = serializer.save(user=request.user)
except IntegrityError:
    return Response({'error': 'You have already booked this workshop.'}, status=400)
```

---

### Feature 5 — Workshops Show Expired/Past Dates and Allow Booking Them 🟡 Medium
**File:** [`workshops/views.py` L10–13](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/workshops/views.py#L10-L13), [`workshops/models.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/workshops/models.py)

**Root cause:** `workshop_list` returns all workshops ordered by date with no date filter. `create_booking` has no check that the workshop date is in the future. Additionally, `Workshop` has no `is_active` or `is_cancelled` flag.

```python
def workshop_list(request):
    workshops = Workshop.objects.all().order_by('date', 'time')
    # ← includes past workshops, cancelled workshops
```

**Impact:** The frontend will display workshops from the past. Users can book workshops with dates that have already passed.

**Fix:**
```python
from datetime import date

# In workshop_list:
workshops = Workshop.objects.filter(
    is_active=True, date__gte=date.today()
).order_by('date', 'time')

# In create_booking:
if workshop.date < date.today():
    return Response({'error': 'This workshop has already passed.'}, status=400)
```

And add `is_active = models.BooleanField(default=True)` to `Workshop`.

---

### Feature 6 — `BookingSerializer` Returns Minimal Data 🟡 Medium
**File:** [`workshops/serializers.py` L35–38](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/workshops/serializers.py#L35-L38)

**Root cause:** `BookingSerializer` only returns `['id', 'workshop', 'seats']` — just a foreign key integer for `workshop`, and no user info, no booking date.

```python
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'workshop', 'seats']   # ← workshop is just an ID integer
```

**Impact:** After a successful booking, the frontend gets back `{"id": 1, "workshop": 2, "seats": 1}` with no workshop title, date, time, or price — making it impossible to show a meaningful booking confirmation.

**Fix:** Nest the full workshop data:
```python
class BookingSerializer(serializers.ModelSerializer):
    workshop = WorkshopSerializer(read_only=True)
    workshop_id = serializers.PrimaryKeyRelatedField(
        queryset=Workshop.objects.all(), source='workshop', write_only=True
    )
    booking_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'workshop', 'workshop_id', 'seats', 'booking_date']
```

---

### Feature 7 — No `published_at` Field on Blog Posts 🟢 Low
**File:** [`blogs/models.py` L14–34](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/blogs/models.py#L14-L34)

**Root cause:** `Post` has `created_at` (when the row was created) and `updated_at` (last edit), but no `published_at`. Changing status from `draft` to `published` does not record when that happened.

**Impact:** Cannot show "Published on May 20th" vs "Updated 2 days ago." Cannot schedule future posts.

**Fix:** Add a nullable field:
```python
published_at = models.DateTimeField(null=True, blank=True)
```
Set it in `PostAdmin.save_model()` when `status` flips to `published`.

---

### Feature 8 — Blog Author Returns Empty String If No Full Name Set 🟢 Low
**File:** [`blogs/serializers.py` L17](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/blogs/serializers.py#L17), [`blogs/serializers.py` L29](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/blogs/serializers.py#L29)

**Root cause:** Both `PostListSerializer` and `PostDetailSerializer` use `source='author.get_full_name'`. If the author's `first_name` and `last_name` are blank (common for programmatically created users), `get_full_name()` returns an empty string.

```python
author_name = serializers.CharField(source='author.get_full_name', read_only=True)
```

**Impact:** Blog posts show a blank author name in the frontend.

**Fix:**
```python
def get_author_name(self, obj):
    return obj.author.get_full_name() or obj.author.username
```

---

### Feature 9 — Guest Cart Rows Are Never Cleaned Up 🟢 Low
**File:** [`cart/models.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/cart/models.py)

**Root cause:** `Cart` rows for guest sessions have no `expires_at` field and no cleanup mechanism. A new guest cart is created for every new `session_id`. Over time, the `cart` table will accumulate thousands of abandoned guest rows.

**Impact:** DB bloat. No immediate breakage.

**Fix (future):** Add `expires_at = models.DateTimeField()` and a management command:
```bash
python manage.py cleanup_guest_carts --older-than-days=30
```

---

### Feature 10 — ShippingZone Seed Not in `BACKEND_SETUP.md` 🟡 Medium
**File:** [`BACKEND_SETUP.md`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/BACKEND_SETUP.md), [`orders/management/commands/seed_shipping_zones.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/orders/management/commands/seed_shipping_zones.py)

**Root cause:** `BACKEND_SETUP.md` says to run `python manage.py seed_store_data` but **does not mention** `seed_shipping_zones`. If only `seed_store_data` is run, the `ShippingZone` and `PincodeRule` tables are empty.

**Impact (critical path):** Every `POST /api/orders/` call validates the pincode via `validate_shipping_pincode()` → `lookup_pincode()` → queries `PincodeRule`. With no rules seeded, `_zone_for_pincode()` returns `None` → `DeliveryLookupResult(is_serviceable=False)` → `OrderCreateSerializer.validate_shipping_pincode()` raises a `ValidationError`. **No orders can be placed at all.**

**Fix:** Update `BACKEND_SETUP.md`:
```bash
python manage.py seed_store_data
python manage.py seed_shipping_zones   # ← add this line
```

---

## 🔐 Security Issues

---

### Security 1 — No Rate Limiting on Auth Endpoints 🟠 High
**File:** [`accounts/views.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/views.py), [`accounts/urls.py`](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/accounts/urls.py)

**Root cause:** `POST /api/auth/login/`, `/register/`, and `/password_reset/` have no throttling. An attacker can attempt unlimited passwords or trigger unlimited password reset emails.

**Fix:** Add DRF throttling in `settings.py`:
```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
    }
}
```
Apply stricter throttle class specifically to login/register using `throttle_classes` on the view.

---

### Security 2 — `DEBUG=true` in `.env.example` 🟡 Medium
**File:** [`.env.example` L2](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/.env.example#L2)

The example file ships with `DJANGO_DEBUG=true`. A developer who copies it without editing will run in debug mode, which exposes stack traces and database queries in error responses.

**Fix:** Change to `DJANGO_DEBUG=false` in `.env.example` and add a comment.

---

### Security 3 — Email Fails Silently in Production If SMTP Not Configured 🟡 Medium
**File:** [`backend/settings.py` L169–172](file:///c:/Users/stuti/OneDrive/Desktop/FunWithArts/backend/backend/settings.py#L169-L172)

**Root cause:** When `DEBUG=false`, Django uses `smtp.EmailBackend`. If `EMAIL_HOST` is blank (production without SMTP configured), sending raises a `socket.gaierror` inside the background thread. The thread catches it and logs it — but the HTTP response still returns 200/201. Order confirmation emails are silently dropped.

**Fix:** Add a startup check in `settings.py` for production:
```python
if not DEBUG and not EMAIL_HOST:
    import warnings
    warnings.warn("EMAIL_HOST is not set — emails will fail silently in production.")
```

---

## 📊 Test Coverage Summary

| App | Test file | What's tested | What's missing |
|---|---|---|---|
| `products` | `tests.py` — 8 tests | list, detail, filter by category (case-insensitive), search, is_new filter, category list, 404 | Review POST, review summary, product search endpoint (`/api/search/`), unavailable product filter |
| `orders` | `tests.py` — 9 tests | create (guest + auth), invalid product, out-of-stock, delivery check, history auth guard, history list, detail, cross-user 403 | Guest order lookup, order status filter, ordering param, free shipping threshold (≥10k) |
| `accounts` | `tests.py` — 3 tests | register+login+me flow, logout invalidates token, invalid credentials | Password reset flow, duplicate email, email login (not tested because it's broken) |
| `users` | `tests.py` — 5 tests | Profile GET/PATCH, profile requires auth, wishlist add/list, duplicate add, remove | Profile PUT (full replace), wishlist product unavailable |
| `cart` | No test file | — | Everything — add, update qty, remove, clear, merge, guest flow |
| `payments` | `tests.py` — 0 tests | — | Everything — create-order, verify, webhook, refund |
| `workshops` | `tests.py` — 0 tests | — | Everything — list, detail, booking, double-booking, past workshops |
| `blogs` | No test file | — | Newsletter subscribe, blog list/detail, duplicate subscribe |
| `notifications` | No test file | — | Email signal firing, async thread behaviour |

---

## 📋 Complete Issue Priority Table

| # | Severity | Issue | File |
|---|---|---|---|
| 1 | 🔴 Critical | Newsletter URL mismatch → 404 on frontend | `backend/urls.py` |
| 2 | 🔴 Critical | Guest users cannot pay with card/UPI (auth required) | `payments/views.py` L35 |
| 3 | 🔴 Critical | Retry payment → IntegrityError (duplicate Payment record) | `payments/views.py` L65 |
| 4 | 🔴 Critical | No Google OAuth login | `accounts/` — missing entirely |
| 5 | 🔴 Critical | ShippingZone seed not documented → all orders fail pincode check | `BACKEND_SETUP.md` |
| 6 | 🟠 High | `Order.DoesNotExist` not caught → 500 instead of 404 | `payments/views.py` L45 |
| 7 | 🟠 High | Email login not supported (only username works) | `accounts/views.py` L57 |
| 8 | 🟠 High | No email uniqueness → duplicate accounts → password reset crash | `accounts/serializers.py` L13 |
| 9 | 🟠 High | No double-booking guard on workshops → slot drain possible | `workshops/models.py`, `views.py` |
| 10 | 🟠 High | No rate limiting on auth endpoints | `accounts/views.py` |
| 11 | 🟡 Medium | Past workshops still shown and bookable | `workshops/views.py` L11 |
| 12 | 🟡 Medium | `BookingSerializer` returns only IDs — no workshop details | `workshops/serializers.py` |
| 13 | 🟡 Medium | `DEBUG=true` in `.env.example` | `.env.example` L2 |
| 14 | 🟡 Medium | Email fails silently in production if SMTP not configured | `backend/settings.py` L169 |
| 15 | 🟡 Medium | Zero tests for `cart` app | `cart/` (no tests.py) |
| 16 | 🟡 Medium | Zero tests for `payments` app | `payments/tests.py` |
| 17 | 🟡 Medium | Zero tests for `workshops` app | `workshops/tests.py` |
| 18 | 🟡 Medium | Zero tests for `blogs` app | `blogs/` (no tests.py) |
| 19 | 🟢 Low | No `published_at` field on `Post` | `blogs/models.py` |
| 20 | 🟢 Low | Blog `author_name` returns empty string if no full name | `blogs/serializers.py` L17, L29 |
| 21 | 🟢 Low | Guest cart rows never expire/cleaned up | `cart/models.py` |
| 22 | 🟢 Low | `order_detail` auth requirement not documented for guest use case | `orders/views.py` L70 |

---

## 🛠️ Recommended Fix Order

```
Phase 1 — Fix before any frontend integration:
  ✅ Fix #5 (seed_shipping_zones docs) → run it
  🔧 Fix #1 (newsletter URL alias)
  🔧 Fix #3 (duplicate payment record)
  🔧 Fix #6 (Order.DoesNotExist → get_object_or_404)
  🔧 Fix #8 (email uniqueness on registration)

Phase 2 — Fix for a working auth flow:
  🔧 Fix #7 (email login support)
  🔧 Fix #4 (Google OAuth — install social-auth-app-django)

Phase 3 — Fix for a correct payment flow:
  🔧 Fix #2 (guest card/UPI payments)

Phase 4 — Fix for data integrity:
  🔧 Fix #9 (workshop double-booking guard)
  🔧 Fix #11 (past workshops filter)
  🔧 Fix #12 (BookingSerializer with full data)

Phase 5 — Security hardening:
  🔧 Fix #10 (rate limiting on auth)
  🔧 Fix #13 (DEBUG=false in .env.example)
  🔧 Fix #14 (email silent failure warning)

Phase 6 — Polish:
  🔧 Fix #19 (published_at field)
  🔧 Fix #20 (author_name fallback to username)
  🔧 Fix #21 (guest cart cleanup command)
```
