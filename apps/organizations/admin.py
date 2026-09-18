from django.contrib import admin

from apps.organizations.models import Organization, OrganizationMember


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "country", "created_at"]
    search_fields = ["name", "slug", "email"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [OrganizationMemberInline]


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "role", "status", "joined_at"]
    list_filter = ["role", "status"]
    search_fields = ["organization__name", "user__email"]
    autocomplete_fields = ["organization", "user"]
