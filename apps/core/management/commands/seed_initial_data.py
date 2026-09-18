from django.core.management.base import BaseCommand

from apps.billing.models import Plan
from apps.templates.models import CardTemplate

TEMPLATES = [
    ("Minimal", "minimal", "general"),
    ("Professional", "professional", "business"),
    ("Corporate", "corporate", "business"),
    ("Creative", "creative", "creative"),
    ("Executive", "executive", "business"),
    ("Dark", "dark", "general"),
    ("Elegant", "elegant", "general"),
    ("Modern", "modern", "general"),
    ("Personal", "personal", "individual"),
    ("Business", "business", "business"),
]

PLANS = [
    dict(name="Free", slug="free", monthly_price=0, annual_price=0, max_vcards=1, max_storage_mb=100,
         max_team_members=1, max_gallery_items=5, max_products=5, max_services=5,
         analytics_enabled=False, appointments_enabled=False, custom_domain_enabled=False,
         directory_enabled=True, remove_branding=False, priority_support=False),
    dict(name="Starter", slug="starter", monthly_price=9, annual_price=90, max_vcards=3, max_storage_mb=500,
         max_team_members=1, max_gallery_items=20, max_products=20, max_services=20,
         analytics_enabled=True, appointments_enabled=False, custom_domain_enabled=False,
         directory_enabled=True, remove_branding=False, priority_support=False),
    dict(name="Professional", slug="professional", monthly_price=29, annual_price=290, max_vcards=10, max_storage_mb=2000,
         max_team_members=5, max_gallery_items=50, max_products=50, max_services=50,
         analytics_enabled=True, appointments_enabled=True, custom_domain_enabled=False,
         directory_enabled=True, remove_branding=True, priority_support=False),
    dict(name="Business", slug="business", monthly_price=79, annual_price=790, max_vcards=50, max_storage_mb=10000,
         max_team_members=25, max_gallery_items=200, max_products=200, max_services=200,
         analytics_enabled=True, appointments_enabled=True, custom_domain_enabled=True,
         directory_enabled=True, remove_branding=True, priority_support=True),
    dict(name="Enterprise", slug="enterprise", monthly_price=249, annual_price=2490, max_vcards=1000, max_storage_mb=100000,
         max_team_members=500, max_gallery_items=1000, max_products=1000, max_services=1000,
         analytics_enabled=True, appointments_enabled=True, custom_domain_enabled=True,
         directory_enabled=True, remove_branding=True, priority_support=True),
]


class Command(BaseCommand):
    help = "Seeds initial CardTemplates and subscription Plans (§23, §27, §60 Phase 1/4)."

    def handle(self, *args, **options):
        created_templates = 0
        for name, slug, category in TEMPLATES:
            _, created = CardTemplate.objects.get_or_create(
                slug=slug, defaults={"name": name, "category": category, "configuration": {}},
            )
            created_templates += int(created)

        created_plans = 0
        for plan_data in PLANS:
            _, created = Plan.objects.get_or_create(slug=plan_data["slug"], defaults=plan_data)
            created_plans += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created_templates} new template(s), {created_plans} new plan(s)."
        ))
