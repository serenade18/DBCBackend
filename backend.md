# Digital Business Card SaaS — Backend Specification (Django REST Framework)

> Companion document: `frontend-spec.md` (React/TypeScript dashboard + public marketing site). This file is the source of truth for the API, data model, and infrastructure. The frontend consumes everything under `/api/v1/`; the public card renderer, `.vcf` export, QR/NFC endpoints, and directory search are server-rendered by this backend and are not part of the React app.

## 1. Product Overview

Build a production-grade digital business card and NFC identity platform inspired by digitalbusinesscard.app.

The platform allows individuals and organizations to create professional digital business cards accessible through a unique public URL, QR codes, NFC cards/tags, a searchable public directory, and social sharing links.

Each digital card is a personal or business landing page containing contact information, social profiles, services, products, testimonials, galleries, booking options, and custom content.

The platform also provides organization/team management, card assignment, analytics, subscription billing, feature/usage limits, NFC physical card ordering, QR generation, contact export, enquiry management, appointment booking, a public directory, and administrative management.

Design this as a multi-tenant SaaS platform capable of supporting thousands of organizations and individual users.

## 2. Technology Stack (Backend)

- Python 3.12+
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Django Channels where real-time functionality is required
- JWT authentication
- S3-compatible object storage for media
- Python `qrcode` for QR generation
- WeasyPrint/reportlab where document generation is required

**Payments**

International: Stripe
Kenya / Africa: M-Pesa, SasaPay

Payment architecture must use a provider abstraction so additional providers can be introduced later.

**Infrastructure**
- Ubuntu, DigitalOcean
- Nginx, Gunicorn, Supervisor/systemd
- PostgreSQL, Redis
- Cloudflare
- S3-compatible object storage
- GitHub Actions for CI/CD

## 3. High-Level Architecture

```text
                         INTERNET
                            |
                       Cloudflare
                            |
              +-------------+-------------+
              |                           |
        Public Card URLs             Application API
              |                           |
          Nginx/CDN                    Nginx
              |                           |
       Django Public Renderer       Gunicorn
                                          |
                    +---------------------+--------------------+
                    |                     |                    |
                PostgreSQL              Redis                Storage
                    |                     |                    |
                 Database              Celery              S3/Object
                                      Workers               Storage
                    |
              Analytics / Billing
                    |
        +-----------+-----------+
        |                       |
      Stripe                M-Pesa/SasaPay
```

## 4. Multi-Tenant Architecture

Use a shared PostgreSQL database with organization-level row scoping.
Do not use separate databases or PostgreSQL schemas for each organization at the initial stage.

```text
Platform
   |
   +── Organization
          |
          +── Users
          |
          +── VCards
          |
          +── Subscription
          |
          +── Orders
          |
          +── Analytics
```

Individual users can own cards without belonging to a formal organization.

Every organization-owned resource must contain an organization reference where appropriate:

```python
organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    related_name="vcards"
)
```

API querysets must always be tenant-scoped. Never rely on frontend filtering for tenant isolation.

## 5. User Roles

**Platform roles**: `super_admin`, `admin`, `support`, `finance`

**Organization roles**: `owner`, `admin`, `member`

**Permissions**

Owner: manage organization, manage subscription, create/delete cards, assign cards, manage team, view analytics, manage billing, place physical card orders

Admin: create/manage cards, manage members, view analytics, manage card content

Member: manage assigned card, view permitted analytics, manage personal profile

## 6. Django Application Structure

Every app owns its own `urls.py`, and `config/urls.py` aggregates them under `/api/v1/`. `cards` also exposes a separate, unauthenticated router for the public-facing card renderer and `.vcf`/QR endpoints (see §6.1 and §16).

```text
backend/
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py                # root URLConf — includes every app's urls.py
│   ├── celery.py
│   └── wsgi.py
│
├── apps/
│   │
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py            # /api/v1/auth/
│   │
│   ├── organizations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py            # /api/v1/organizations/
│   │
│   ├── cards/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── urls.py            # /api/v1/vcards/  +  public /@<slug>/ renderer routes
│   │
│   ├── profile_blocks/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/vcards/<id>/blocks/, /api/v1/blocks/<id>/
│   │
│   ├── templates/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/templates/
│   │
│   ├── appointments/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/appointments/
│   │
│   ├── analytics/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/analytics/
│   │
│   ├── billing/
│   │   ├── models.py
│   │   ├── providers/
│   │   │   ├── stripe.py
│   │   │   ├── mpesa.py
│   │   │   └── sasapay.py
│   │   ├── services.py
│   │   ├── webhooks.py
│   │   └── urls.py            # /api/v1/billing/  +  /api/v1/webhooks/{provider}/
│   │
│   ├── directory/
│   │   ├── models.py
│   │   ├── search.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/directory/  +  public /directory/
│   │
│   ├── orders/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/orders/
│   │
│   ├── nfc_qr/
│   │   ├── qr.py
│   │   ├── nfc.py
│   │   ├── vcard.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/vcards/<id>/qr/, /api/v1/nfc/
│   │
│   ├── enquiries/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py            # /api/v1/enquiries/  +  public submit endpoint
│   │
│   ├── notifications/
│   │   ├── email.py
│   │   ├── sms.py
│   │   ├── tasks.py
│   │   └── urls.py            # /api/v1/notifications/ (in-app feed, mark-read)
│   │
│   └── core/
│       ├── models.py
│       ├── permissions.py
│       ├── pagination.py
│       ├── exceptions.py
│       ├── utils.py
│       └── urls.py            # /health/, /health/db/, /health/redis/
│
├── manage.py
└── requirements.txt
```

### 6.1 Root URL Configuration (`config/urls.py`)

Each app's `urls.py` is self-contained and mounted with `include()` from the root URLConf. Authenticated/API routes live under `/api/v1/`; public, unauthenticated routes (the card renderer, directory, health checks, webhooks) are mounted at the root so they never depend on the dashboard SPA.

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health checks (unauthenticated)
    path("health/", include("apps.core.urls")),

    # Versioned API — dashboard/authenticated surface
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/organizations/", include("apps.organizations.urls")),
    path("api/v1/vcards/", include("apps.cards.urls")),
    path("api/v1/", include("apps.profile_blocks.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/appointments/", include("apps.appointments.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/nfc/", include("apps.nfc_qr.urls")),
    path("api/v1/enquiries/", include("apps.enquiries.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/directory/", include("apps.directory.urls")),

    # Payment provider webhooks (unauthenticated, signature-verified)
    path("api/v1/webhooks/", include("apps.billing.webhook_urls")),

    # Public, unauthenticated surfaces
    path("directory/", include("apps.directory.public_urls")),
    path("", include("apps.cards.public_urls")),  # /@<slug>/, /c/<slug>/, .vcf, QR
]
```

Notes:
- `apps.cards.urls` holds the **authenticated** `/api/v1/vcards/` CRUD; `apps.cards.public_urls` holds the **public** `/@<slug>/` renderer, `.vcf` export, and OpenGraph/SEO routes — kept as separate URLConfs so the public path never imports dashboard-only permission classes.
- `apps.billing.webhooks` (handler functions) are wired up in `apps.billing.webhook_urls`, mounted outside `/api/v1/` auth middleware since providers call these unauthenticated and instead verify via signature.
- `apps.directory.public_urls` serves the public `/directory/` search page; `apps.directory.urls` under `/api/v1/directory/` serves authenticated management endpoints (visibility toggle, category assignment).

## 7. Core Data Model — User

```text
User
- id UUID
- email
- phone
- first_name
- last_name
- password
- avatar
- is_active
- is_staff
- date_joined
- last_login
```

Use UUID primary keys.

## 8. Organization

```text
Organization
- id UUID
- name
- slug
- logo
- description
- website
- email
- phone
- country
- timezone
- created_at
- updated_at
```

## 9. Organization Membership

```text
OrganizationMember
- id UUID
- organization
- user
- role
- status
- invited_at
- joined_at
```

Unique constraint: `organization + user`

## 10. VCard

The VCard is the central entity.

```text
VCard
- id UUID
- organization
- owner
- assigned_user
- slug
- display_name
- job_title
- company_name
- bio
- profile_photo
- cover_photo
- email
- phone
- whatsapp
- website
- address
- location
- template
- theme_config JSON
- visibility
- status
- is_featured
- is_directory_visible
- created_at
- updated_at
```

Statuses: `draft`, `published`, `suspended`, `archived`

Public URL: `https://domain.com/@username` or `https://domain.com/c/slug`

The slug must be unique.

## 11. Profile Content System

```text
ProfileBlock
- id
- vcard
- type
- title
- content JSON
- position
- is_visible
- created_at
- updated_at
```

Supported types: `social`, `link`, `service`, `product`, `testimonial`, `gallery`, `video`, `contact`, `location`, `appointment`, `custom`

This allows new block types to be introduced without redesigning the VCard database schema.

## 12. Profile Links

```text
ProfileLink
- id
- vcard
- title
- url
- icon
- position
- is_visible
```

Examples: LinkedIn, Instagram, TikTok, Facebook, X, YouTube, WhatsApp, Website, Portfolio

## 13. Services

```text
Service
- id
- vcard
- name
- description
- price
- currency
- image
- booking_enabled
- position
- is_visible
```

## 14. Products

```text
Product
- id
- vcard
- name
- description
- price
- currency
- image
- external_url
- position
- is_visible
```

## 15. Testimonials

```text
Testimonial
- id
- vcard
- customer_name
- customer_title
- customer_photo
- content
- rating
- position
- is_visible
```

## 16. Gallery

```text
GalleryItem
- id
- vcard
- image
- title
- description
- position
- is_visible
```

Images must be stored in object storage rather than the application server filesystem.

## 17. Appointment System

```text
AppointmentService
- id
- vcard
- name
- description
- duration_minutes
- price
- currency
- is_active
```

```text
AvailabilityRule
- id
- vcard
- weekday
- start_time
- end_time
- timezone
```

```text
Appointment
- id
- vcard
- service
- customer_name
- customer_email
- customer_phone
- date
- start_time
- end_time
- status
- notes
- created_at
```

Statuses: `pending`, `confirmed`, `cancelled`, `completed`, `no_show`

## 18. Enquiries

```text
Enquiry
- id
- vcard
- name
- email
- phone
- message
- status
- created_at
```

Statuses: `new`, `read`, `replied`, `archived`

Notifications are sent asynchronously.

## 19. Contact Export

The system generates a standards-compliant `.vcf` file.

Endpoint: `GET /api/vcards/{slug}/contact/`

Contains: name, organization, job title, phone, email, website, address, social links.

The endpoint must work without JavaScript.

## 20. QR Code System

Each published VCard receives a QR code pointing to its public URL, e.g. `https://domain.com/@john-doe`

QR formats: PNG, SVG, PDF. QR generation should happen server-side.

## 21. NFC System

NFC tags should store the public VCard URL only, e.g. `https://domain.com/@john-doe`

The platform should support: NFC tag registration, assignment, reassignment, status, write instructions.

NFC lifecycle:

```text
Unassigned → Assigned → Activated → Suspended → Reassigned
```

Do not store the entire profile inside the NFC chip — store only the URL, so the user can change their profile without rewriting the physical card.

## 22. Public Card Rendering

The public VCard page is the highest-performance part of the system, and is server-rendered by Django (not the React dashboard).

Requirements: server-side rendering, SEO metadata, OpenGraph metadata, Twitter/X metadata, JSON-LD, fast first contentful paint, mobile-first, no authentication required, no dashboard JavaScript dependency, responsive, accessible markup.

Example: `GET /@john-doe` — HTML must contain the core profile content before any JavaScript executes.

## 23. Template System

```text
CardTemplate
- id
- name
- slug
- preview_image
- category
- configuration
- is_active
- is_premium
```

Initial templates: Minimal, Professional, Corporate, Creative, Executive, Dark, Elegant, Modern, Personal, Business

## 24. Theme Engine

Store theme configuration as JSON, not hardcoded per-template properties.

```json
{
  "primaryColor": "#111827",
  "secondaryColor": "#6B7280",
  "backgroundColor": "#FFFFFF",
  "textColor": "#111827",
  "buttonStyle": "rounded",
  "cardStyle": "glass",
  "fontFamily": "Inter",
  "borderRadius": "lg"
}
```

Controls: colors, typography, buttons, background, cards, borders, shadows, spacing, avatar shape, link styles.

Templates control structure. Themes control appearance.

## 25. Analytics — Data Model

```text
CardView
- id, vcard, timestamp, referrer, source, device_type, browser, country, city, ip_hash, user_agent_hash
```

```text
LinkClick
- id, vcard, link, timestamp, source, device_type, country, ip_hash
```

Never expose raw IP addresses to organization users.

## 26. Analytics — API Contract

Expose: Total Views, Unique Visitors, Link Clicks, Contact Downloads, Enquiries, Appointments, Top Links, Traffic Sources, Countries, Devices — plus time-series for Views/Clicks/Engagement rate/Traffic sources/Device distribution.

Time filters: Today, 7 days, 30 days, 90 days, 12 months, Custom.

Analytics aggregation should use daily/hourly aggregate tables rather than querying raw events per dashboard request.

## 27. Subscription System

```text
Plan
- id, name, slug, description, monthly_price, annual_price, currency
- max_vcards, max_storage_mb, max_team_members, max_gallery_items, max_products, max_services
- analytics_enabled, appointments_enabled, custom_domain_enabled, directory_enabled
- remove_branding, priority_support, is_active
```

Example tiers: Free, Starter, Professional, Business, Enterprise. Do not hardcode plan IDs in the frontend.

## 28. Subscription

```text
Subscription
- id, organization, plan, provider, provider_subscription_id, status
- trial_start, trial_end, current_period_start, current_period_end
- cancel_at_period_end, created_at, updated_at
```

Statuses: `trialing`, `active`, `past_due`, `cancelled`, `expired`, `paused`

## 29. Feature Gating

Central entitlement service:

```python
subscription.can("analytics")
subscription.can("appointments")
subscription.can("custom_domain")
subscription.can_create_vcard()
subscription.can_upload(size)
```

The frontend displays limits; the backend must enforce them.

## 30. Payment Architecture

```python
class PaymentProvider:
    def create_customer(self, user): ...
    def create_subscription(self, subscription): ...
    def cancel_subscription(self, subscription): ...
    def verify_payment(self, payload): ...
    def handle_webhook(self, payload): ...
```

Providers: `StripeProvider`, `MpesaProvider`, `SasaPayProvider` — keeps payment logic out of the rest of the application.

## 31. Payment Records

```text
Payment
- id, organization, subscription, provider, provider_reference
- amount, currency, status, payment_method, metadata JSON
- paid_at, created_at
```

Statuses: `pending`, `processing`, `successful`, `failed`, `refunded`. All provider callbacks must be idempotent.

## 32. Physical NFC Card Ordering

Materials: PET Plastic, Wood, Metal

```text
PhysicalCardProduct
- id, name, material, description, price, currency, image, is_active
```

```text
Order
- id, organization, customer, order_number, status
- subtotal, shipping_fee, tax, total, currency, payment_status
- shipping_address, created_at, updated_at
```

Statuses: `pending_payment`, `paid`, `processing`, `printing`, `shipped`, `delivered`, `cancelled`, `refunded`

## 33. NFC Card Inventory

```text
NfcCard
- id, uid, serial_number, material, vcard, order, status, activated_at
```

Statuses: `inventory`, `reserved`, `assigned`, `active`, `blocked`, `retired`

## 34. Shipping

```text
ShippingAddress
- full_name, company, phone, address_line_1, address_line_2, city, county/state, postal_code, country
```

```text
ShippingEvent
- order, status, description, tracking_number, timestamp
```

## 35. Public Directory

Directory URL: `/directory` — search, category, industry, location, profession, company.

Examples: `/directory?category=software-engineer`, `/directory?location=nairobi`

Directory listing must only expose fields explicitly marked public.

## 36. Directory Profile

Public listing: profile photo, name, job title, company, location, short bio, verified status.

Never expose: private email, private phone, internal organization information, analytics, billing information.

## 37. Search

Initial implementation: PostgreSQL full-text search over name, company, job_title, bio, location, industry.

For larger scale, introduce Elasticsearch or OpenSearch without changing the public API.

## 38. Authentication API

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
POST /api/auth/forgot-password/
POST /api/auth/reset-password/
GET  /api/auth/me/
```

Support: email/password, email verification, forgot/reset password, logout, refresh token, session management. Optional later: Google, Apple, Microsoft OAuth.

## 39. VCard API

```text
GET    /api/vcards/
POST   /api/vcards/
GET    /api/vcards/{id}/
PATCH  /api/vcards/{id}/
DELETE /api/vcards/{id}/

POST   /api/vcards/{id}/publish/
POST   /api/vcards/{id}/unpublish/

GET    /api/vcards/{id}/qr/
GET    /api/vcards/{id}/contact/
```

Public:

```text
GET /api/public/cards/{slug}/
GET /api/public/cards/{slug}/analytics/
```

The public analytics endpoint must not expose private analytics.

## 40. Content, Team, Billing APIs

**Content**

```text
GET    /api/vcards/{id}/blocks/
POST   /api/vcards/{id}/blocks/
PATCH  /api/blocks/{id}/
DELETE /api/blocks/{id}/
POST   /api/vcards/{id}/blocks/reorder/
```

**Team**

```text
GET    /api/organizations/
GET    /api/organizations/{id}/
PATCH  /api/organizations/{id}/

GET    /api/organizations/{id}/members/
POST   /api/organizations/{id}/members/invite/
PATCH  /api/organizations/{id}/members/{member}/
DELETE /api/organizations/{id}/members/{member}/

POST /api/vcards/{id}/assign/
POST /api/vcards/{id}/unassign/
```

**Billing**

```text
GET  /api/billing/plans/
GET  /api/billing/subscription/
POST /api/billing/checkout/
POST /api/billing/cancel/
POST /api/billing/reactivate/
GET  /api/billing/invoices/

POST /api/webhooks/stripe/
POST /api/webhooks/mpesa/
POST /api/webhooks/sasapay/
```

## 41. Security Requirements

Mandatory: HTTPS everywhere, secure HTTP headers, CSRF protection where applicable, CORS whitelist in production, JWT rotation, password hashing, rate limiting, API throttling, object-level permissions, tenant isolation, signed upload URLs, file validation, image size limits, MIME validation, webhook signature verification, idempotency keys, audit logging.

Never trust `organization_id`, `user_id`, `vcard_id`, `role`, `plan`, `price`, `permissions` when received from the frontend. Derive them from authenticated server-side context.

## 42. Audit Logging

```text
AuditLog
- id, actor, organization, action, resource_type, resource_id, metadata JSON, ip_hash, created_at
```

Track: login, logout, card created/deleted/published/assigned, member invited/removed, subscription changed, payment, order, profile changes.

## 43. Notifications (Backend)

Channels: Email, SMS, In-app.

Events: welcome, email verification, password reset, new enquiry, new appointment, appointment reminder, payment successful/failed, subscription expiring, order received/shipped/delivered, team invitation.

Use Celery for asynchronous delivery.

## 44. Media Management

Supported: JPEG, PNG, WEBP, SVG where safe. Generate original/thumbnail/medium/large variants, e.g. `profile-original.webp`, `profile-400.webp`, `profile-800.webp`, `profile-1200.webp`. Optimize automatically; deliver via CDN.

## 45. Public Page SEO

```html
<title>
<meta name="description">
<meta property="og:title">
<meta property="og:description">
<meta property="og:image">
<meta property="og:url">
<meta name="twitter:card">
```

Structured data: `{"@context": "https://schema.org", "@type": "Person"}` or `"Organization"` depending on card type.

## 46. Performance Requirements

Public VCard pages: TTFB < 500ms, LCP < 2.5s.

Use CDN, HTTP caching, database indexes, Redis caching, optimized images, lazy loading, minimal JavaScript, server-side rendering. Cache public card responses where safe; invalidate on update.

## 47. Database Indexes

```text
VCard.slug, VCard.owner, VCard.organization, VCard.status
Organization.slug
ProfileBlock.vcard + position
CardView.vcard + timestamp
LinkClick.vcard + timestamp
Appointment.vcard + date, Appointment.status
Order.order_number, Order.organization, Order.status
```

Add composite indexes based on actual query patterns.

## 48. Background Jobs (Celery)

Tasks: analytics aggregation, email sending, SMS sending, appointment reminders, subscription checks, payment reconciliation, image processing, QR generation, order notifications, cleanup jobs.

Scheduled: hourly analytics aggregation, daily subscription checks, daily abandoned-order checks, appointment reminders, expired trial processing.

## 49. Admin Panel

Users: search, filter, suspend, activate, view activity
Organizations: search, view members/cards/subscription, suspend
Plans: create, edit, deactivate, configure limits
Templates: create, edit, preview, activate/deactivate, mark premium
Orders: view, filter, update status, add tracking
Payments: search, filter, refund status, provider reference

## 50. System Settings

Admin-configurable: platform name, logo, default currency, supported countries, default plan, trial duration, email settings, SMS settings, Stripe settings, M-Pesa settings, SasaPay settings, storage settings, directory settings, maintenance mode.

Secrets must never be stored in normal database settings — use environment variables / secret management.

## 51. Internationalization (Data Model)

Design the backend for English, Swahili, French, Arabic at minimum — the data model should not assume a single language.

Currency support: KES, USD, EUR, GBP

## 52. Observability

Monitor: application logs, Nginx logs, Celery logs, database monitoring, error tracking, performance monitoring, uptime monitoring.

Track: API response time, 5xx rate, authentication failures, payment failures, Celery failures, database connections, storage usage.

## 53. Backup Strategy

PostgreSQL: daily full backup, point-in-time recovery where supported.
Object storage: versioning, lifecycle policies.
Configuration: env vars backed up securely; infra config stored in Git.

## 54. Testing Strategy (Backend)

Test: authentication, permissions, tenant isolation, VCard CRUD, public pages, content blocks, analytics, billing, webhooks, orders, appointments.

Critical test: *User A must never retrieve Organization B data.*

Integration tests: Stripe webhook, M-Pesa callback, SasaPay callback, email, SMS, file uploads, QR generation, VCF generation.

## 55. API Versioning

Start with `/api/v1/`, e.g. `/api/v1/auth/login/`, `/api/v1/vcards/`, `/api/v1/organizations/` — allows future API versions without breaking mobile clients or integrations.

## 56. Deployment Architecture

```text
Cloudflare
     |
     +---------------------+
     |                     |
Frontend CDN          API Server
                          |
                       Nginx
                          |
                      Gunicorn
                          |
                      Django
                    /    |    \
                   /     |     \
            PostgreSQL Redis  Storage
                         |
                       Celery
```

Separate workers: `web`, `celery-worker`, `celery-beat`

## 57. Environment Variables

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=

DATABASE_URL=

REDIS_URL=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=

SASAPAY_CLIENT_ID=
SASAPAY_CLIENT_SECRET=

EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

SMS_API_KEY=
```

Never commit secrets to Git.

## 58. CI/CD (Backend)

```text
Push → Install dependencies → Lint → Type check → Backend tests →
Build deployment artifact → Deploy → Run migrations → Collect static →
Restart services → Health check
```

Production deployment should fail if migrations or health checks fail.

## 59. Health Checks

```text
GET /health/
GET /health/db/
GET /health/redis/
```

```json
{ "status": "healthy", "database": "healthy", "redis": "healthy" }
```

## 60. MVP Scope (Backend)

**Phase 1**: auth (register/login/logout/password reset/email verification); VCard CRUD, publish/unpublish, unique slug, profile photo, bio, contact info; public card endpoint + `.vcf` + QR; basic card list/editor persistence.

**Phase 2**: templates, theme engine, services, products, gallery, testimonials, custom links, enquiries.

**Phase 3**: analytics (views/clicks), appointments, notifications (email/SMS).

**Phase 4**: subscriptions, Stripe, M-Pesa, SasaPay, plan limits, trials, invoices, payment history.

**Phase 5**: organizations, team members, roles, card assignment.

**Phase 6**: public directory, search, categories, locations, featured profiles, verification.

**Phase 7**: physical NFC cards — inventory, ordering, shipping, NFC assignment, fulfillment.

**Phase 8**: custom domains, advanced analytics, white-labeling, enterprise plans, public API access, webhooks.

## 61. Important Architectural Decisions

**Multi-tenancy** — Shared PostgreSQL database + organization foreign keys + server-side tenant scoping. Easier deployment/backups/analytics, lower infra cost, scales sufficiently for initial SaaS growth.

**Public Rendering** — Django-rendered public card pages (not the React SPA). Django renders public card, VCF download, SEO metadata, social previews — avoids loading the dashboard SPA just to view a business card.

**Template Architecture** — Separate template (layout), theme (appearance), content blocks (data): 10 templates × 100 themes × thousands of cards without duplicating profile data.

**Payments** — Provider abstraction from day one (`PaymentService` → Stripe, M-Pesa, SasaPay). Never couple subscriptions directly to Stripe-specific models.

## 62. MVP Success Criteria

A new user can: register → create card → upload photo → add contact details → choose template → publish → receive unique URL → download QR code → scan QR → open public card → save contact → share card.

An organization can subsequently: create organization → invite employees → create multiple cards → assign cards → manage employees → view analytics → manage subscription.

## 63. Backend Development Order

```text
STEP 01  Project foundation — Django + PostgreSQL + Redis
STEP 02  Authentication
STEP 03  Organizations + users
STEP 04  VCard CRUD
STEP 05  Public VCard renderer
STEP 06  VCF export
STEP 07  QR generation
STEP 08  Template system
STEP 09  Profile blocks
STEP 10  Media storage
STEP 11  Analytics
STEP 12  Appointments + enquiries
STEP 13  Subscription engine
STEP 14  Stripe
STEP 15  M-Pesa/SasaPay
STEP 16  Team management
STEP 17  Directory
STEP 18  NFC inventory
STEP 19  Physical card orders
STEP 20  Admin
STEP 21  Monitoring + CI/CD
STEP 22  Security audit
STEP 23  Performance optimization
STEP 24  Production launch
```

## 64. Core Principle

The platform should be built as a data-driven SaaS, not a collection of hardcoded profile pages.

```text
USER → ORGANIZATION → VCARD → CONTENT BLOCKS → TEMPLATE → THEME → PUBLIC URL → QR / NFC
```

This lets the same underlying profile power the web card, QR code, NFC card, directory listing, contact export, analytics, and future mobile applications without duplicating business logic.